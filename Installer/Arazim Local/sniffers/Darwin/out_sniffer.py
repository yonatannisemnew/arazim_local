import os
import sys
import ipaddress
from scapy.all import  sniff, send
from scapy.layers.inet import IP, ICMP, fragment
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from sniffers.constants import PAYLOAD_MAGIC
from utils import network_stats

def real_subnet_to_our(ip, subnet_mask):
    # Split the strings into lists of octets
    ip_parts = ip.split('.')
    mask_parts = subnet_mask.split('.')

    if len(ip_parts) != 4 or len(mask_parts) != 4:
        raise ValueError("Invalid IP or Subnet Mask format")

    # Perform bitwise AND on each octet
    # int(a) & int(b) calculates the network portion
    network_parts = [
        str(int(ip_parts[i]) & int(mask_parts[i]))
        for i in range(4)
    ]

    # Join them back into a standard IP string
    res =  ".".join(network_parts[1:])
    res = "127." + res
    return res


def local_ip_to_real(ip, my_ip): # make it work for other subnet values
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return my_ip[:my_ip.find(".")] + ip[ind:]

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

class OutSniffer:
    def __init__(self, target_subnet,target_subnet_mask, my_ip, network_interface, default_gateway, lo_iface):
        self.target_subnet = target_subnet
        self.target_subnet_mask = target_subnet_mask
        self.my_ip = my_ip
        self.network_interface = network_interface
        self.default_gateway = default_gateway
        self.lo_iface = lo_iface
        fake_subnet = real_subnet_to_our(target_subnet, self.target_subnet_mask)
        self.target_network = ipaddress.ip_network(f"{fake_subnet}/{self.target_subnet_mask}", strict=False)


    def start_sniff(self):
        sniff(iface=self.lo_iface, prn=self.encapsulate_and_send, store=0)


    def encapsulate_and_send(self, pkt):
        try:
            if IP not in pkt:
                return
            if pkt[IP].src != "127.0.0.1":
                return
            if ipaddress.ip_address(pkt[IP].dst) not in self.target_network:
                return
            #adding into icmp payload, with magic
            pkt[IP].src = self.my_ip
            pkt[IP].dst = local_ip_to_real(pkt[IP].dst, self.my_ip)
            full_packet_bytes = bytes(pkt[IP])
            payload = PAYLOAD_MAGIC + full_packet_bytes
            wrapper_pkt = IP(dst=self.default_gateway, src=pkt[IP].dst) / ICMP(type=8) / payload
            for f in fragment(wrapper_pkt):
                send(f, verbose=0, iface=self.network_interface)

        except Exception as e:
            print("Error in encapsulate_and_send:", e)

def main():
    stats = network_stats.NetworkStats()
    if stats is None:
        print("Networks stats failed, closing sniffer")
        exit(0)
    sniffer = OutSniffer(stats.my_ip, stats.subnet_mask, stats.my_ip, stats.default_device, stats.router_ip, stats.loopback_device)
    sniffer.start_sniff()


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
