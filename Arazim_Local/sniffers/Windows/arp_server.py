import sys
import random
from scapy.all import *
import os

# Adjust path to find the utils package
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

# Assuming utils.network_stats is available in your environment based on the prompt
# If running this as a single file for testing, ensure NetworkStats class is included or imported correctly.
from utils.network_stats import *


def generate_random_mac():
    """
    Generates a random Unicast, Locally Administered MAC address.
    Format: x2:xx:xx:xx:xx:xx (where x is random).
    This ensures Windows/Linux accept it as a valid neighbor.
    """
    # 0x02 ensures the Local bit is set and Multicast bit is OFF.
    first_byte = 0x02
    rest = [random.randint(0x00, 0xFF) for _ in range(5)]
    return ":".join(f"{b:02x}" for b in [first_byte] + rest)


def responder(network_stats):
    """
    Will respond to arp 'who-has' requests relevant to the subnet with
    a random mac (which is a correct mac that windows allows).
    """
    print(f"[*] Starting ARP Server on interface: {network_stats.default_device}")
    print(f"[*] Responding for subnet: {network_stats.network}")
    print(f"[*] Ignoring own IP: {network_stats.my_ip}")

    def handle_packet(packet):

        if ARP in packet and packet[ARP].op == 1:
            target_ip = packet[ARP].pdst
            sender_ip = packet[ARP].psrc

            if network_stats.in_subnet(target_ip):
                if (
                    target_ip == network_stats.my_ip
                    or target_ip == network_stats.router_ip
                ):
                    return
                random_mac = generate_random_mac()

                print(
                    f"[+] Request: Who has {target_ip}? -> Tell {sender_ip} it is at {random_mac}"
                )

                reply = Ether(dst=packet[ARP].hwsrc, src=random_mac) / ARP(
                    op=2,  # 2 = ARP Reply
                    hwsrc=random_mac,  # The fake MAC we just invented
                    psrc=target_ip,  # The IP they were looking for
                    hwdst=packet[ARP].hwsrc,  # The requester's MAC
                    pdst=sender_ip,  # The requester's IP
                )

                # Send the packet out
                sendp(reply, iface=network_stats.default_device, verbose=False)

    # Sniff for ARP packets on the default device
    # store=0 prevents Scapy from eating up RAM by saving packets
    sniff(filter="arp", prn=handle_packet, store=0, iface=network_stats.default_device)


def main():
    network_stats = NetworkStats.get_stats()
    if network_stats is None:
        print("network stats is not initialized!")
        exit(1)
    responder(network_stats)


if __name__ == "__main__":
    main()
