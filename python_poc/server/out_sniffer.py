import os

from scapy.all import  sniff, send
import sys

from scapy.layers.inet import IP, TCP, ICMP

from python_poc.server.sniff_constants import PAYLOAD_MAGIC


class OutSniffer:

    def __init__(self, target_subnet, destination_ip, my_ip, network_interface):
        self.target_subnet = target_subnet
        self.destination_ip = destination_ip
        self.my_ip = my_ip
        self.network_interface = network_interface

    TARGET_SUBNET = "127.16.164.0/24"

    # router
    TUNNEL_DEST_IP = "172.16.164.254"
    MY_IP = "172.16.164.94"

    def local_ip_to_real(self, ip):
        ind = ip.find(".")
        if ind == -1:
            raise ValueError("Invalid IP")
        return self.my_ip[:self.my_ip.find(".")] + ip[ind:]


    # Wi-Fi interface
    # IFACE = "wlp8s0"


    def encapsulate_and_send(self, pkt):
        try:
            if IP not in pkt:
                return

            pkt[IP].dst = self.local_ip_to_real(pkt[IP].dst)
            print(f"IP is {pkt[IP].dst}")
            pkt[IP].src = self.my_ip
            del pkt[IP].chksum
            del pkt[TCP].chksum
            full_packet_bytes = bytes(pkt[IP])
            payload = PAYLOAD_MAGIC + full_packet_bytes
            original_dst = pkt[IP].dst
            tunnel_pkt = IP(dst=self.destination_ip, src=original_dst) / ICMP(type=8) / payload

            send(tunnel_pkt, verbose=0, iface=self.network_interface)

            print(
                f"[*] Tunneled {len(full_packet_bytes)} bytes intended for {original_dst}")

        except Exception as e:
            print(f"[!] Error processing packet: {e}")

def main(TUNNEL_DEST_IP, TARGET_SUBNET, my_ip, network_interface, lo_interface):
    print(f"[*] Starting Sniffer...")
    print(f"[*] Targeting Subnet: {TARGET_SUBNET}")
    print(f"[*] Tunneling to: {TUNNEL_DEST_IP}")
    sniffer = OutSniffer(TARGET_SUBNET, TUNNEL_DEST_IP, my_ip, network_interface)
    bpf_filter = (f"dst host 127.16.164.165 "
                  f"and src host 127.0.0.1 "
                  f"and tcp")
    sniff(filter=bpf_filter, iface=lo_interface, prn=sniffer.encapsulate_and_send, store=0)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    # main()
