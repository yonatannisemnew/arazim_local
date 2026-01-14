import os

from scapy.all import  sniff, send
import sys

from scapy.layers.inet import IP, TCP, ICMP

from python_poc.server.in_sniffer import real_ip_to_local
from sniff_constants import PAYLOAD_MAGIC


class OutSniffer:

    def __init__(self, target_subnet, my_ip, network_interface, default_gateway):
        self.target_subnet = target_subnet
        self.my_ip = my_ip
        self.network_interface = network_interface
        self.default_gateway = default_gateway

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


    def encapsulate_and_send(self, pkt):
        try:
            if IP not in pkt:
                return

            pkt[IP].dst = self.local_ip_to_real(pkt[IP].dst)
            print(f"IP is {pkt[IP].dst}")
            pkt[IP].src = self.my_ip
            del pkt[IP].chksum
            del pkt[TCP].chksum
            full_packet_bytes = bytes(pkt[IP])
            payload = PAYLOAD_MAGIC + full_packet_bytes
            original_dst = pkt[IP].dst
            tunnel_pkt = IP(dst=self.default_gateway, src=original_dst) / ICMP(type=8) / payload

            send(tunnel_pkt, verbose=0, iface=self.network_interface)

            print(
                f"[*] Tunneled {len(full_packet_bytes)} bytes intended for {original_dst}")

        except Exception as e:
            print(f"[!] Error processing packet: {e}")

def main(target_subnet, my_ip, network_interface, lo_interface, default_gateway):
    print(f"[*] Starting Sniffer...")
    print(f"[*] Targeting Subnet: {target_subnet}")
    sniffer = OutSniffer(target_subnet, my_ip, network_interface)
    bpf_filter = (f"dst net {target_subnet} and not dst host {default_gateway} and src net 127.16.164.0/23 and tcp")
    sniff(filter=bpf_filter, iface=lo_interface, prn=sniffer.encapsulate_and_send, store=0)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    args = sys.argv[1:]
    main(args[0], args[1], args[2], args[3], args[4])
