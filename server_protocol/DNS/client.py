from scapy.all import *
from scapy.layers.inet import IP, ICMP

XOR_KEY = "222.222.222.222"
MY_IP = get_if_addr(conf.iface)
DEFAULT_GATEWAY = conf.route.route("0.0.0.0")[2]
DNS_IP = "172.16.164.6"
QUERY_IDENTIFIER = b"nif_local_salta_8223"
RESPONSE_IDENTIFIER = b"NOT_EZ_GIMEL_SHTAIM"
def xor(data, key):
    return bytes([a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1))])

xor_data = xor(MY_IP.encode(), XOR_KEY.encode())

# Send
res = sr1(IP(src=DNS_IP,dst=DEFAULT_GATEWAY)/ICMP()/(QUERY_IDENTIFIER + xor_data))