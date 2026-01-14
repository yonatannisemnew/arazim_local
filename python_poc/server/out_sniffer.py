import os
import sys
import argparse

from scapy.all import  sniff, send
from scapy.layers.inet import IP, TCP, ICMP

from in_sniffer import real_ip_to_local
from sniff_constants import PAYLOAD_MAGIC


def local_ip_to_real(self, ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return self.my_ip[:self.my_ip.find(".")] + ip[ind:]

def real_ip_to_local(self, ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

class OutSniffer:
    def __init__(self, target_subnet, my_ip, network_interface, default_gateway, lo_iface):
        self.target_subnet = target_subnet
        self.my_ip = my_ip
        self.network_interface = network_interface
        self.default_gateway = default_gateway
        self.lo_iface = lo_iface
        self.bpf_filter = f"dst net {real_ip_to_local(target_subnet)} and tcp"
    
    def start_sniff(self):
        sniff(filter=self.bpf_filter, iface=self.lo_iface, prn=self.encapsulate_and_send, store=0)
    
    def encapsulate_and_send(self, pkt):
        try:
            if IP not in pkt:
                return
            pkt[IP].dst = local_ip_to_real(pkt[IP].dst)
            print(f"IP is {pkt[IP].dst}")
            pkt[IP].src = self.my_ip
            #deleting the checksum to force recalculation
            del pkt[IP].chksum
            del pkt[TCP].chksum
            #adding into icmp payload, with magic
            full_packet_bytes = bytes(pkt[IP])
            payload = PAYLOAD_MAGIC + full_packet_bytes
            original_dst = pkt[IP].dst
            tunnel_pkt = IP(dst=self.default_gateway, src=original_dst) / ICMP(type=8) / payload

            send(tunnel_pkt, verbose=0, iface=self.network_interface)

        except Exception as e:
            pass

def main():
    parser = argparse.ArgumentParser(description="Sniffs for packets in subnet from lo and injects into normal iface")
    parser.add_argument("--our_ip", dest="our_ip", required=True,
                        help="our IP address to filter")
    parser.add_argument("--default_gateway", dest="default_gateway", required=True,
                        help="Expected source of captured packets")
    parser.add_argument("--send_iface", dest="send_iface", required=True,
                        help="Network interface to sniff on")
    parser.add_argument("--lo_iface", dest="lo_iface", required=True,
                        help="Network interface to send on (loopback)")
    parser.add_argument("--subnet", dest="subnet", required=True,
                        help="subnet like 172.16.164.0/23")
    args = parser.parse_args()
    sniffer = OutSniffer(args.subnet, args.our_ip, args.send_iface, args.default_gateway,  args.lo_iface)
    sniffer.start_sniff()


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
