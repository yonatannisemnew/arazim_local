from scapy.all import *
import sys

from scapy.layers.inet import IP, TCP, ICMP

TARGET_SUBNET = "127.16.164.0/24"

# router
TUNNEL_DEST_IP = "172.16.164.254"
MY_IP = "172.16.164.94"

def local_ip_to_real(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return MY_IP[:MY_IP.find(".")] + ip[ind:]


# wifi interface
IFACE = "wlp8s0"


def encapsulate_and_send(pkt):
    try:
        if IP not in pkt:
            return

        pkt[IP].dst = local_ip_to_real(pkt[IP].dst)
        print(f"IP is {pkt[IP].dst}")
        pkt[IP].src = MY_IP
        del pkt[IP].chksum
        del pkt[TCP].chksum
        full_packet_bytes = bytes(pkt[IP])
        payload = b"sacha" + full_packet_bytes
        original_dst = pkt[IP].dst
        tunnel_pkt = IP(dst=TUNNEL_DEST_IP, src=original_dst) / ICMP(type=8) / payload

        send(tunnel_pkt, verbose=0, iface=IFACE)

        print(
            f"[*] Tunneled {len(full_packet_bytes)} bytes intended for {original_dst}")

    except Exception as e:
        print(f"[!] Error processing packet: {e}")

def main():
    print(f"[*] Starting Sniffer...")
    print(f"[*] Targeting Subnet: {TARGET_SUBNET}")
    print(f"[*] Tunneling to: {TUNNEL_DEST_IP}")

    bpf_filter = (f"dst host 127.16.164.165 "
                  f"and src host 127.0.0.1 "
                  f"and tcp")
    sniff(filter=bpf_filter, iface="lo", prn=encapsulate_and_send, store=0)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
