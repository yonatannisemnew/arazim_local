from scapy.all import *
import socket
import struct
import array

TARGET_PAYLOAD = b"nif_local_salta_8223"
CONFIRMATION = b"NOT_EZ_GIMEL_SHTAIM"
MY_IP = get_if_addr(conf.iface)
DEFAULT_GATEWAY = "172.16.164.254"
XOR_KEY = "222.222.222.222"

def checksum(packet):
    """
    Calculate the IP checksum of the given packet.
    """
    if len(packet) % 2 != 0:
        packet += b'\x00'
    words = array.array("H", packet)
    chk = sum(words)
    chk = (chk >> 16) + (chk & 0xffff)
    chk += chk >> 16
    return (~chk) & 0xffff

def extract_ip(payload):
    """
    Slices the payload after the signature and XORs it against the key
    to recover the IP address string.
    """
    encrypted_data = payload[len(TARGET_PAYLOAD):]

    decrypted_chars = []
    key_len = len(XOR_KEY)

    # 2. Perform XOR decryption
    for i in range(len(encrypted_data)):
        key_char = XOR_KEY[i % key_len]
        decrypted_byte = encrypted_data[i] ^ ord(key_char)
        decrypted_chars.append(chr(decrypted_byte))

    extracted_ip_str = "".join(decrypted_chars)
    return extracted_ip_str.strip('\x00')

def create_ip_header(source_ip, dest_ip, data_length):
    """
    Create an ICMP header with the given source and destination IPs.
    """
    # IPv4 Header Fields
    version_ihl = (4 << 4) + 5
    tos = 0
    total_len = 20 + data_length
    ip_id = 8223
    frag_off = 0
    ttl = 64
    protocol = socket.IPPROTO_ICMP
    check = 0

    src_addr = socket.inet_aton(source_ip)
    dst_addr = socket.inet_aton(dest_ip)

    header = struct.pack('!BBHHHBBH4s4s',
                         version_ihl, tos, total_len, ip_id, frag_off,
                         ttl, protocol, check, src_addr, dst_addr)
    return header

def start_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
    sock.bind(('', 0))
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1) #Allows custom IP header

    print(f"LISTENING!!!: {MY_IP}")
    try:
        while True:
            raw_data, addr = sock.recvfrom(65535)

            # Parse IP Header
            ip_header_len = (raw_data[0] & 0xF) * 4
            icmp_packet = raw_data[ip_header_len:]

            icmp_header = icmp_packet[:8]
            ic_type, _, _, p_id, seq = struct.unpack('!BBHHH', icmp_header)

            if ic_type == 8:
                payload = icmp_packet[8:]

                if TARGET_PAYLOAD in payload:
                    print("[*] Target payload received.")

                    try:
                        extracted_source_ip = extract_ip(payload)
                        print(f"    Extracted IP to spoof: {extracted_source_ip}")
                        icmp_data = CONFIRMATION + MY_IP.encode()
                        dummy_icmp = struct.pack('!BBHHH', 0, 0, 0, p_id, seq)
                        icmp_chk = checksum(dummy_icmp + icmp_data)
                        real_icmp_header = struct.pack('!BBHHH', 0, 0, socket.htons(icmp_chk), p_id, seq)
                        full_icmp_part = real_icmp_header + icmp_data
                        ip_header = create_ip_header(MY_IP,extracted_source_ip, len(full_icmp_part))
                        final_packet = ip_header + full_icmp_part   
                        sock.sendto(final_packet, (extracted_source_ip, 0))
                        print(f"sent spoofed packet to {extracted_source_ip} from {MY_IP}")

                    except Exception as e:
                        print(f"PARSING ERROR: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    try:
        start_server()
    except Exception as e:
        print("ERROR: ", e)
