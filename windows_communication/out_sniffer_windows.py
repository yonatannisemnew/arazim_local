
from constants import *
from scapy.all import *
from scapy.all import IP, ICMP, Raw, send
from networkstats import NetworkStats


# def windivert_filter(src_ip: str, router_ip: str, subnet: str, mask: str) -> str:
#     return f"(ip.DstAddr != {router_ip} and (ip.DstAddr & {mask}) == {subnet}) and ip.SrcAddr == {src_ip}"


# def create_icmp_echo(src_ip: str, dst_ip: str, payload_bytes: bytes):
#     """
#     Creates a pydivert packet object containing an ICMP Echo Request.
#     """
#     scapy_pkt = IP(src=src_ip, dst=dst_ip) / ICMP(type=ICMP_REQUEST_TYPE, code=0) / (PAYLOAD_MAGIC + payload_bytes)

#     raw_bytes = bytes(scapy_pkt)

#     # Create the WinDivert address structure
#     # This tells the driver the packet is Outbound (leaving your computer)
#     addr = windivert_dll.WINDIVERT_ADDRESS()
#     addr.Outbound = 1   
#     addr.Loopback = 0
#     addr.Impostor = 1
    
#     return pydivert.Packet(raw_bytes, addr)

# def sniffer(subnet: str, mask: str, router_ip: str, our_ip: str): 
#     wind_filter = windivert_filter(our_ip, router_ip, subnet, mask)
#     with pydivert.WinDivert(wind_filter) as w:
#         print("STARTED OUT SNIFFER")
#         for packet in w:
#             #bytes to send in icmp 
#             packet_bytes = packet.raw
#             #spoofed ip to send to
#             src_ip__icmp = packet.dst_addr
#             new_icmp_packet = create_icmp_echo(src_ip__icmp, router_ip, packet_bytes)
#             w.send(new_icmp_packet)
#             w.send(packet)
# def main(argc, argv):
#     subnet = argv[1]
#     mask = argv[2]
#     router_ip = argv[3]
#     our_ip = argv[4]
#     sniffer(subnet, mask, router_ip, our_ip)

# if __name__ == "__main__":
#     argc = len(sys.argv)
#     argv = sys.argv
#     main(len(sys.argv), sys.argv)


def bpf_filter(networks_stats: NetworkStats) -> str:
    # Logic:
    # 1. Source must be my_ip
    # 2. Destination must be within the subnet/mask
    # 3. Destination must NOT be the router_ip
    my_ip = networks_stats.my_ip
    base_addr = networks_stats.base_addr()
    subnet_mask = networks_stats.subnet_mask
    router_ip = networks_stats.router_ip
    return f"src host {my_ip} and dst net {base_addr} mask {subnet_mask} and not dst host {router_ip}"

def sniffer(network_stats):
    bpf = bpf_filter(network_stats)
    print(f"Scapy filter: {bpf}")
    print("STARTED OUT SNIFFER")
    sniff(filter=bpf, prn=lambda pack: handle_packet(pack, network_stats), store=False)




def handle_packet(packet, network_stats):
    # Ensure the packet has an IP layer to avoid AttributeErrors
    if IP not in packet:
        return

    # Extract the destination IP from the intercepted packet
    dst_ip = packet[IP].dst

    # Create the payload: Your MAGIC identifier + the original IP packet bytes
    # This encapsulates the original packet inside the ICMP data field
    icmp_payload = PAYLOAD_MAGIC + bytes(packet[IP])

    # Construct the ICMP packet
    # type=8 is an Echo Request (ping)
    icmp_packet = IP(src = dst_ip, dst=ROUTER_IP) / ICMP(type=8, code=0) / Raw(load=icmp_payload)

    send(icmp_packet, verbose=True)



def main():
    network_stats = NetworkStats(MY_IP, ROUTER_IP, SUBNET_MASK)
    sniffer(network_stats)


if __name__ == "__main__":
    main()
