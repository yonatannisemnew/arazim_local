from networkstats import NetworkStats
import pydivert
import ipaddress
from constants import *

def windivert_filter() -> str:
    return "ip"


def to_intercept(packet, network_stats) -> bool:
    """
    returns True if ip_dst == MY_IP and
    ip_src in subnet and ip_src is not the ROUTER_IP
    """
    # Ensure the packet has an IPv4 layer to avoid errors
    if not packet.ipv4:
        return False

    src_ip = packet.ipv4.src_addr
    dst_ip = packet.ipv4.dst_addr

    # 1. Check if destination is MY_IP
    is_to_me = (dst_ip == MY_IP)

    # 2. Check if source is NOT the ROUTER_IP
    is_not_from_router = (src_ip != ROUTER_IP)

    # 3. Check if source IP is within the subnet
    # We create a network object from the subnet and mask
    network = ipaddress.IPv4Network(f"{MY_IP}/{SUBNET_MASK}", strict=False)
    is_from_subnet = ipaddress.IPv4Address(src_ip) in network

    return is_to_me and is_not_from_router and is_from_subnet

def sniffer(network_stats):
    wind_filter = windivert_filter()
    with pydivert.WinDivert(wind_filter, layer=pydivert.Layer.NETWORK) as w:
        print("STARTED IN SNIFFER")
        for packet in w:
            if to_intercept(packet, network_stats):
                #change packet direction from going out to going in
                packet.direction = pydivert.Direction.INBOUND
                print("intercepted packet!")
            w.send(packet)


def main(my_ip, router_ip, subnet_mask):
    network_stats = NetworkStats(my_ip, router_ip, subnet_mask)
    sniffer(network_stats)


if __name__ == "__main__":
    main(MY_IP, ROUTER_IP, SUBNET_MASK)