import sys
import os
import argparse
from scapy.all import sniff, send, Raw
from scapy.layers.inet import IP, TCP
from sniff_constants import PAYLOAD_MAGIC 

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]


class Sniffer:
    def __init__(self, our_ip, default_gateway, sniff_iface, lo_iface):
        self.our_ip = our_ip
        self.default_gateway = default_gateway
        self.sniff_iface = sniff_iface
        self.lo_iface = lo_iface
        self.bpf_filter = (f"dst host {our_ip} "
                  f"and src {default_gateway} ")
    
    def start_sniff(self):
        sniff(filter=self.bpf_filter, iface=self.sniff_iface, prn=self.decapsulate_and_inject, store=0)

    def decapsulate_and_inject(self,pkt):
        """
        Takes an ICMP echo packet, checks that the magic is there,
        and injects the "raw" part into loopback.
        """
        try:
            #make sure its our magic
            if pkt[Raw].load[:len(PAYLOAD_MAGIC)] != PAYLOAD_MAGIC:
                return
            #get the raw, without magic (og packet)
            encapsulated = IP(pkt[Raw].load[len(PAYLOAD_MAGIC):])
            #change src and dst to allow sending in lo
            encapsulated[IP].src = real_ip_to_local(encapsulated[IP].src)
            encapsulated[IP].dst = "127.0.0.1" #real_ip_to_local(encapsulated[IP].dst)
            #delete checksums to force recalculation, and send :-)
            del encapsulated[IP].chksum
            del encapsulated[TCP].chksum
            send(encapsulated, verbose=0, iface=self.lo_iface)

        except Exception as e:
            pass

def main():
    parser = argparse.ArgumentParser(description="Sniffs for ICMP, if its correct magic, injects into lo")
    parser.add_argument("--our_ip", dest="our_ip", required=True,
                        help="our IP address to filter")
    parser.add_argument("--default_gateway", dest="default_gateway", required=True,
                        help="Expected source of captured packets")
    parser.add_argument("--main_iface", dest="main_iface", required=True,
                        help="Network interface to sniff/send packets on")
    parser.add_argument("--lo_iface", dest="lo_iface", required=True,
                        help="Network interface to send on (loopback)")
    parser.add_argument("--subnet", dest="subnet", required=True,
                        help="subnet like 172.16.164.0")
    parser.add_argument("--subnet_mask", dest="subnet_mask", required=True,
                        help="subnet mask like 255.255.255.0")
    args = parser.parse_args()
    in_sniffer = Sniffer(args.our_ip, args.default_gateway, args.main_iface, args.lo_iface)
    in_sniffer.start_sniff()
    
if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
