import sys
from constants import *
from scapy.all import *
from scapy.all import IP, ICMP, Raw, send
from networkstats import NetworkStats
from sniffer_utils import sniffer_parse_args


def bpf_filter(network_stats: NetworkStats) -> str:
    # Logic:
    # 1. Source must be my_ip
    # 2. Destination must be within the subnet/mask
    # 3. Destination must NOT be the router_ip
    my_ip = network_stats.my_ip
    base_addr = network_stats.base_addr()
    subnet_mask = network_stats.subnet_mask
    router_ip = network_stats.router_ip
    return f"src host {my_ip} and dst net {base_addr} mask {subnet_mask} and not dst host {router_ip}"


def sniffer(network_stats):
    bpf = bpf_filter(network_stats)
    print(f"Scapy filter: {bpf}")
    print("STARTED OUT SNIFFER")
    sniff(filter=bpf, prn=lambda pack: handle_packet(pack, network_stats), store=False)


def handle_packet(packet, network_stats):
    if IP not in packet:
        return
    dst_ip = packet[IP].dst
    icmp_payload = PAYLOAD_MAGIC + bytes(packet[IP])
    icmp_packet = (
        IP(src=dst_ip, dst=network_stats.router_ip) / ICMP(type=8, code=0) / Raw(load=icmp_payload)
    )
    send(icmp_packet, verbose=True)


def main(my_ip: str, router_ip: str, subnet_mask: str, interface_index: int):
    network_stats = NetworkStats(my_ip, router_ip, subnet_mask, interface_index)
    sniffer(network_stats)


if __name__ == "__main__":
    my_ip, router_ip, subnet_mask, interface_index = sniffer_parse_args(sys.argv)
    main(my_ip, router_ip, subnet_mask, interface_index)