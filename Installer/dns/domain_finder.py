import ipaddress
import os
from scapy.layers.inet import IP, ICMP
from typing import Iterable
from constants import *

# path setup
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from utils.network_stats import NetworkStats


def get_subnet_ips(ip: str, mask: int) -> Iterable[str]:
    # Returns a generator yielding IPs as strings
    return (str(ip) for ip in ipaddress.IPv4Network(f"{ip}/{mask}", strict=False))


def filter_packet(packet):
    if packet.haslayer(ICMP):
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            if payload.startswith(RESPONSE_IDENTIFIER):
                return True
    return False


def send_queries(network_stats):
    ips_to_query = [str(ip) for ip in network_stats.network.hosts()]
    icmp_core = ICMP() / Raw(QUERY_IDENTIFIER)
    packets = []

    for dst_ip in ips_to_query:
        packet = IP(src=network_stats.my_ip, dst=dst_ip) / icmp_core
        packets.append(packet)
    send(packets, verbose=False)


def find_server(network_stats, timeout: float = 15):
    sniffer = AsyncSniffer(
        iface=conf.iface, lfilter=filter_packet, count=1, timeout=timeout
    )
    sniffer.start()

    send_queries(network_stats)
    sniffer.join()
    captured_packets = sniffer.results
    if len(captured_packets) == 0:
        return None
    return captured_packets[0][IP].src


if __name__ == "__main__":
    network_stats = NetworkStats()
    if network_stats is None:
        exit(1)
    try:
        result = find_server(network_stats, 24)
        print(f"Discovered IP: {result}")
    except:
        exit(1)
