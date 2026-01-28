import ipaddress
import platform
from scapy.all import IP, ICMP, Raw, send, AsyncSniffer, conf, Ether
from typing import Iterable
from constants import *
import sys
import os
from python_hosts import Hosts, HostsEntry
# path setup
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from utils.network_stats import NetworkStats

def add_to_hosts_file(ip, hostname):
    hosts = Hosts()
    new_entry = HostsEntry(entry_type='ipv4', address=ip, names=[hostname])
    hosts.add([new_entry])
    try:
        hosts.write()
        print(f"[+] {hostname} pointed to {ip}")
    except PermissionError:
        print("[!] Run as sudo to modify hosts.")

def filter_packet(packet):
    if packet.haslayer(ICMP):
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            if payload.startswith(RESPONSE_IDENTIFIER):
                return True
    return False

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

def send_queries(ips):
    ips = [str(ip) for ip in ips]
    if platform.system() != "Windows":
        ips = list(map(real_ip_to_local, ips))
    packets = [IP(dst=ip)/ICMP()/Raw(load=QUERY_IDENTIFIER) for ip in ips]
    send(packets, verbose=False)

def get_cached_ip():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            return f.read().strip()
    return None

def save_cached_ip(ip):
    with open(CACHE_FILE, "w") as f:
        f.write(ip)

def find_server(interface, ips_to_check, timeout: float = 15):
    sniffer = AsyncSniffer(
        iface=interface, lfilter=filter_packet, count=1, timeout=timeout
    )
    sniffer.start()

    send_queries(ips_to_check)
    sniffer.join()
    captured_packets = sniffer.results
    if len(captured_packets) == 0:
        return None
    return captured_packets[0][IP].src

def main():
    network_stats = NetworkStats()
    if network_stats is None:
        print("error in netstats")
        exit(1)
    try:
        cached_ip = get_cached_ip()
        result = None
        try:
            if cached_ip is not None:
                result = find_server(network_stats.loopback_device, [cached_ip])
        finally:
            if result is None:
                result = find_server(network_stats.loopback_device, network_stats.network.hosts())
        if result is not None:
            print(f"server is at: {result}")
            add_to_hosts_file(result, DOMAIN)
            save_cached_ip(result)
        else:
            print("Server not found")
    except Exception as e:
        print(e)
        exit(1)

if __name__ == "__main__":
    main()