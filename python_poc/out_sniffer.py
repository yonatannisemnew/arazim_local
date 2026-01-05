from scapy.all import *
import sys

# --- Configuration ---
TARGET_SUBNET = "172.16.164.0/23"

# The specific address where the tunneled pings will be sent
TUNNEL_DEST_IP = "172.16.164.254"
MY_IP = "172.16.164.165"


# Interface to sniff on (e.g., 'eth0', 'wlan0')
IFACE = "wlp0s20f3"


def encapsulate_and_send(pkt):
    """
    Takes the WHOLE packet (headers + data), converts to bytes,
    and puts it inside an ICMP Echo Request.
    """
    try:
        if IP not in pkt:
            return
        # Convert the entire original packet object to raw bytes
        # This includes IP headers, TCP/UDP headers, and data
        full_packet_bytes = bytes(pkt[IP])
        payload = b"sacha" + full_packet_bytes
        # Create the tunnel packet
        # Layer 3: IP (Source=spoofed, Dest=Tunnel Endpoint)
        # Layer 4: ICMP (Type 8 = Echo Request)
        # Payload: The raw bytes of the original packet
        original_dst = pkt[IP].dst
        tunnel_pkt = IP(dst=TUNNEL_DEST_IP, src=original_dst) / ICMP(type=8) / payload

        # Send without verbose output
        send(tunnel_pkt, verbose=0, iface=IFACE)

        # Optional: Print summary
        print(
            f"[*] Tunneled {len(full_packet_bytes)} bytes intended for {original_dst}")

    except Exception as e:
        print(f"[!] Error processing packet: {e}")

def main():
    print(f"[*] Starting Sniffer...")
    print(f"[*] Targeting Subnet: {TARGET_SUBNET}")
    print(f"[*] Tunneling to: {TUNNEL_DEST_IP}")

    # --- The BPF Filter ---
    # 1. 'dst net TARGET_SUBNET': Only capture packets going TO the target subnet
    # 2. 'and not dst host TUNNEL_DEST_IP': Safety check to prevent loops
    # 3. 'and not icmp': Optional, to avoid tunneling existing pings (prevents ping loops)
    bpf_filter = (f"dst net {TARGET_SUBNET} "
                  f"and src host {MY_IP} "
                  f"and not dst host {TUNNEL_DEST_IP} "
                  f"and not dst host {MY_IP}")
    # Start sniffing
    # store=0: Do not keep packets in memory (saves RAM)
    # prn: The callback function to run on every packet
    sniff(filter=bpf_filter, iface="lo", prn=encapsulate_and_send, store=0)


if __name__ == "__main__":
    # Scapy requires root privileges to sniff and craft packets
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()