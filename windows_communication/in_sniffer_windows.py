import ipaddress
import sys
from constants import *
from scapy.all import *
from scapy.all import IP, Raw
import pydivert
from networkstats import NetworkStats
from sniffer_utils import sniffer_parse_args


def send_packet_pydivert(scapy_ip_packet, div_handle: pydivert.WinDivert = None):
    if scapy_ip_packet.haslayer("Ether"):
        scapy_ip_packet = scapy_ip_packet["IP"]
    packet_bytes = bytes(scapy_ip_packet)
    packet = pydivert.Packet(
        raw=packet_bytes,  # Starting from scratch
        interface=(5, 0),
        direction=pydivert.Direction.INBOUND,
    )
    div_handle.send(packet, recalculate_checksum=True)

    print("sent 1 packet via pydivert")


def bpf_filter(network_stats) -> str:
    router_ip = network_stats.router_ip
    return f"ip and icmp and src host {router_ip}"


def valid_packet_to_send(packet, network_stats):
    to_my_ip = network_stats.my_ip == packet[IP].dst
    in_subnet = network_stats.in_subnet(packet[IP].src)
    not_from_router = network_stats.router_ip != packet[IP].src
    return to_my_ip and in_subnet and not_from_router


def handle_packet(packet, network_stats, div_handle: pydivert.WinDivert = None):
    icmp_payload = packet[Raw].load
    magic_len = len(PAYLOAD_MAGIC)
    # check payload starts with magic
    if icmp_payload[0:magic_len] != PAYLOAD_MAGIC:
        return
    payload = icmp_payload[magic_len:]
    ###sending is from the IP layer
    ip_packet = IP(payload)
    if valid_packet_to_send(ip_packet, network_stats):
        # sends and than pydivert retransmits
        # send(ip_packet) # TODO: change to pydivert
        send_packet_pydivert(ip_packet, div_handle)


def sniffer(network_stats):

    with pydivert.WinDivert("false") as w:
        bpf = bpf_filter(network_stats)
        print(f"Scapy filter: {bpf}")
        print("STARTED IN SNIFFER")
        sniff(
            filter=bpf,
            prn=lambda pack: handle_packet(pack, network_stats, w),
            store=False,
        )


def main(my_ip: str, router_ip: str, subnet_mask: str):
    network_stats = NetworkStats(my_ip, router_ip, subnet_mask)
    sniffer(network_stats)


if __name__ == "__main__":
    my_ip, router_ip, subnet_mask = sniffer_parse_args(sys.argv)
    main(my_ip, router_ip, subnet_mask)
