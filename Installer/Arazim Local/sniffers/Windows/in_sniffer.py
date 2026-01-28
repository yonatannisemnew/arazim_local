import sys
from scapy.all import IP, Raw, conf
import pydivert
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from utils.network_stats import *
from sniffers.constants import *
from sniffers.sniffers_utils import sniff_assembeld


def get_interface_index():
    try:
        default_interface = conf.route.route("8.8.8.8")[0]
        return conf.ifaces[default_interface].index
    except:
        return None


def send_packet_pydivert(
    scapy_ip_packet, div_handle: pydivert.WinDivert = None, interface_index: int = 5
):
    if scapy_ip_packet.haslayer("Ether"):
        scapy_ip_packet = scapy_ip_packet["IP"]
    packet_bytes = bytes(scapy_ip_packet)
    packet = pydivert.Packet(
        raw=packet_bytes,  # Starting from scratch
        interface=(interface_index, 0),
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
    try:
        icmp_payload = packet[Raw].load
        magic_len = len(PAYLOAD_MAGIC)
        if icmp_payload[0:magic_len] != PAYLOAD_MAGIC:
            return
        payload = icmp_payload[magic_len:]
        ip_packet = IP(payload)
        if valid_packet_to_send(ip_packet, network_stats):
            interface_index = get_interface_index()
            send_packet_pydivert(ip_packet, div_handle, interface_index)
    except:
        print("an error while handeling the packet")


def sniffer(network_stats):
    with pydivert.WinDivert("false") as w:
        bpf = bpf_filter(network_stats)
        print(f"Scapy filter: {bpf}")
        print("STARTED IN SNIFFER")
        """
        sniff(
            filter=bpf,
            prn=lambda pack: handle_packet(pack, network_stats, w),
            store=False,
        )
        """
        def_iface = conf.route.route("8.8.8.8")[0]
        sniff_assembeld(
            filter=bpf,
            iface=def_iface,
            prn=lambda pack: handle_packet(pack, network_stats, w),
        )


def main():
    network_stats = NetworkStats()
    if network_stats is None:
        print("network stats is not initialized!")
        exit(1)
    sniffer(network_stats)


if __name__ == "__main__":
    main()
