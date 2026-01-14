import sys
import os
import argparse
from scapy.all import sniff, send, Raw
from scapy.layers.inet import IP, TCP
from manager.constants import PAYLOAD_MAGIC


def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

def decapsulate_and_inject(pkt):
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
        encapsulated[IP].dst = "127.0.0.1"
        #delete checksums to force recalculation, and send :-)
        del encapsulated[IP].chksum
        del encapsulated[TCP].chksum
        send(encapsulated, verbose=0, iface="lo")

    except Exception as e:
        pass

def main():
    parser = argparse.ArgumentParser(description="Sniffs for ICMP, if its correct magic, injects into lo")
    parser.add_argument("--our-ip", dest="our_ip", required=True,
                        help="our IP address to filter")
    parser.add_argument("--tunnel-dst-ip", dest="tunnel_dst_ip", required=True,
                        help="Expected source of captured packets")
    parser.add_argument("--netiface", dest="netiface", required=True,
                        help="Network interface to sniff on")

    args = parser.parse_args()
    our_ip = args.our_ip
    tunnel_dst_ip = args.tunnel_dst_ip
    netiface = args.netiface

    bpf_filter = (f"dst host {our_ip} "
                  f"and src host {tunnel_dst_ip} "
                  "and icmp")
    
    sniff(filter=bpf_filter, iface=netiface, prn=decapsulate_and_inject, store=0)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
