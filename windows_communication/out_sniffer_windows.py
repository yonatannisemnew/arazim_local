import os
import sys 
import time
import pydivert
from pydivert import windivert_dll
import constants
from scapy.all import IP, ICMP
def windivert_filter(src_ip: str, router_ip: str, subnet: str, mask: str) -> str:
    return f"(ip.DstAddr != {router_ip} and (ip.DstAddr & {mask}) == {subnet}) and ip.SrcAddr == {src_ip}"


def create_icmp_echo(src_ip: str, dst_ip: str, payload_bytes: bytes):
    """
    Creates a pydivert packet object containing an ICMP Echo Request.
    """
    scapy_pkt = IP(src=src_ip, dst=dst_ip) / ICMP(type=constants.ICMP_REQUEST_TYPE, code=0) / (constants.PAYLOAD_MAGIC + payload_bytes)

    raw_bytes = bytes(scapy_pkt)

    # Create the WinDivert address structure
    # This tells the driver the packet is Outbound (leaving your computer)
    addr = windivert_dll.WINDIVERT_ADDRESS()
    addr.Outbound = 1   
    addr.Loopback = 0
    addr.Impostor = 1
    
    return pydivert.Packet(raw_bytes, addr)

def sniffer(subnet: str, mask: str, router_ip: str, our_ip: str): 
    wind_filter = windivert_filter(our_ip, router_ip, subnet, mask)
    with pydivert.WinDivert(wind_filter) as w:
        print("STARTED OUT SNIFFER")
        for packet in w:
            #bytes to send in icmp 
            packet_bytes = packet.raw
            #spoofed ip to send to
            src_ip__icmp = packet.dst_addr
            new_icmp_packet = create_icmp_echo(src_ip__icmp, router_ip, packet_bytes)
            w.send(new_icmp_packet)
            w.send(packet)





def main(argc, argv):
    subnet = argv[1]
    mask = argv[2]
    router_ip = argv[3]
    our_ip = argv[4]
    sniffer(subnet, mask, router_ip, our_ip)

if __name__ == "__main__":
    argc = len(sys.argv)
    argv = sys.argv
    main(len(sys.argv), sys.argv)