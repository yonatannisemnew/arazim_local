import time
from scapy.all import *
import ipaddress
from scapy.layers.inet import IP, ICMP
from typing import Iterable

from scapy.layers.l2 import Ether

MY_IP = get_if_addr(conf.iface)
DEFAULT_GATEWAY = conf.route.route("0.0.0.0")[2]
QUERY_IDENTIFIER = b"nif_local_salta_8223"
RESPONSE_IDENTIFIER = b"NOT_EZ_GIMEL_SHTAIM"
def xor(data, key):
    return bytes([a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1))])
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


def send_queries(src_ip: str, ips: Iterable):
    icmp_core = ICMP() / Raw(QUERY_IDENTIFIER)
    packets = []
    for ip in ips:
        packet = IP(src=src_ip, dst=ip) / icmp_core
        packets.append(packet)
    send(packets, verbose=False)

def protocol(subnet: str, mask: int, timeout: float=5):
    # 1. Define the sniffer object
    # 'prn' is a callback function for each packet, 'filter' uses BPF syntax
    sniffer = AsyncSniffer(iface=conf.iface, lfilter=filter_packet, count=1, timeout=timeout)
    # 2. Start sniffing (non-blocking)
    sniffer.start()
    
    send_queries(MY_IP, get_subnet_ips(subnet, mask))

    sniffer.join() # Wait for responses to be captured
    # 3. Stop sniffing when you're done
    captured_packets = sniffer.results
    if len(captured_packets) == 0:
        return None
    if len(captured_packets) == 1:
        return captured_packets[0][IP].src
    if len(captured_packets) > 1:
        for packet in captured_packets: # remove this debug print later
            packet.summary()
        return captured_packets[0][IP].src

# if __name__ == "__main__":
#     result = protocol("10.233.219.84", 24, 1)
#     print(f"Discovered IP: {result}")
