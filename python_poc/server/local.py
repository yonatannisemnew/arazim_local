from scapy.all import *
import random

# --- FIX 1: FORCE RAW SOCKET ---
# This forces Scapy to calculate checksums in a way the Loopback interface accepts.
# Without this, the OS Kernel often silently drops the packet before 'nc' sees it.
conf.L3socket = L3RawSocket

# Configuration
target_ip = "127.0.0.1"
target_port = 8889
# Use a random source port so you don't get stuck in TCP wait states if you run it twice
src_port = random.randint(1025, 65535)

# 1. Create the Packet
ip_layer = IP(dst=target_ip)
tcp_layer = TCP(sport=src_port, dport=target_port, flags="S")
packet = ip_layer / tcp_layer

print(f"[*] Sending SYN to {target_ip}:{target_port} from port {src_port}...")

# --- FIX 2: USE sr1() INSTEAD OF send() ---
# send() = Send only (Fire and forget)
# sr1()  = Send and Receive 1 packet (Waits for the reply)
response = sr1(packet, iface="lo", timeout=1, verbose=0)

# 3. Check the Response
if response:
    # Check if the response has a TCP layer
    if response.haslayer(TCP):
        flags = response[TCP].flags
        print(f"[+] Received packet with flags: {flags}")
        
        # Check for SYN-ACK (Flags can be 'SA' or 0x12)
        if "SA" in str(flags): 
            print("[SUCCESS] NC returned a SYN-ACK!")
        elif "R" in str(flags):
            print("[FAIL] Connection Reset (RST). Is the port closed or firewall active?")
else:
    print("[FAIL] No response received. (Packet likely dropped by Kernel checksum offloading)")