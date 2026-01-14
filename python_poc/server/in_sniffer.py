import sys
from scapy.all import sniff, send, Raw
from scapy.layers.inet import IP, TCP
from sniff_constants import PAYLOAD_MAGIC

TARGET_SUBNET_remove = "172.16.164.0/23"

# router
TUNNEL_DEST_IP_remove = "172.16.164.254"
MY_IP_remove = "172.16.164.94"



# wifi interface
IFACE_remove = "wlp8s0"

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

def encapsulate_and_send(pkt):
    """
    Takes the WHOLE packet (headers + data), converts to bytes,
    and puts it inside an ICMP Echo Request, with a magic
    """
    try:
        if pkt[Raw].load[:len(PAYLOAD_MAGIC)] != PAYLOAD_MAGIC:
            return

        real_packet = IP(pkt[Raw].load[len(PAYLOAD_MAGIC):])
        real_packet[IP].src = real_ip_to_local(real_packet[IP].src)
        real_packet[IP].dst = "127.0.0.1"
        real_packet.show()
        del real_packet[IP].chksum
        del real_packet[TCP].chksum
        send(real_packet, verbose=0, iface="lo")

        print(
            f"injected packet from {real_packet[IP].src}")

    except Exception as e:
        print(f"[!] Error processing packet: {e}")

def main():
    print(f"[*] Starting Sniffer...")
    print(f"[*] Targeting Subnet: {TARGET_SUBNET}")
    print(f"[*] Tunneling to: {TUNNEL_DEST_IP}")

    bpf_filter = (f"dst host {MY_IP} "
                  f"and src host {TUNNEL_DEST_IP} "
                  "and icmp")
    sniff(filter=bpf_filter, iface=IFACE, prn=encapsulate_and_send, store=0)


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
