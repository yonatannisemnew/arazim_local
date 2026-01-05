from scapy.all import *
import sys

# --- Configuration ---
TARGET_SUBNET = "172.16.164.0/23"

# The specific address where the tunneled pings will be sent
TUNNEL_DEST_IP = "172.16.164.254"
MY_IP = "172.16.164.94"



# Interface to sniff on (e.g., 'eth0', 'wlan0')
IFACE = "wlp8s0"

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

def encapsulate_and_send(pkt):
    """
    Takes the WHOLE packet (headers + data), converts to bytes,
    and puts it inside an ICMP Echo Request.
    """
    try:
        if pkt[Raw].load[:len("sacha")] != b"sacha":
            return
        # Convert the entire original packet object to raw bytes
        # This includes IP headers, TCP/UDP headers, and data
        real_packet = IP(pkt[Raw].load[len("sacha"):])
        real_packet[IP].src = real_ip_to_local(real_packet[IP].src)
        real_packet[IP].dst = "127.0.0.1"
        real_packet.show()
        del real_packet[IP].chksum
        del real_packet[TCP].chksum
        # Create the tunnel packet
        # Layer 3: IP (Source=spoofed, Dest=Tunnel Endpoint)
        # Layer 4: ICMP (Type 8 = Echo Request)
        # Payload: The raw bytes of the original packet
        # Send without verbose output
        send(real_packet, verbose=0, iface="lo")

        # Optional: Print summary
        print(
            f"injected packet from {real_packet[IP].src}")

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
    bpf_filter = (f"dst host {MY_IP} "
                  f"and src host {TUNNEL_DEST_IP} "
                  "and icmp")
    # Start sniffing
    # store=0: Do not keep packets in memory (saves RAM)
    # prn: The callback function to run on every packet
    sniff(filter=bpf_filter, iface=IFACE, prn=encapsulate_and_send, store=0)


if __name__ == "__main__":
    # Scapy requires root privileges to sniff and craft packets
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()