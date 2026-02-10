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
from sniffers.constants import PAYLOAD_MAGIC


def add_to_hosts_file(ip, hostname):
    hosts = Hosts()
    new_entry = HostsEntry(entry_type="ipv4", address=ip, names=[hostname])
    hosts.add([new_entry])
    try:
        hosts.write()
        print(f"[+] {hostname} pointed to {ip}")
    except PermissionError:
        print("[!] Run as sudo to modify hosts.")


def filter_packet(packet):
    ##for windows version:
    if packet.haslayer(ICMP):
        if packet.haslayer(Raw):
            payload = packet[Raw].load
            if payload.startswith(PAYLOAD_MAGIC) and (RESPONSE_IDENTIFIER in payload):
                print("DNS FINDER: got packet!")
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
    packets = [IP(dst=ip) / ICMP() / Raw(load=QUERY_IDENTIFIER) for ip in ips]
    print("DNS: STARTS SENDING QUERIES")
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
    try:
        sniffer = AsyncSniffer(
            iface=interface, lfilter=filter_packet, count=1, timeout=timeout
        )
        sniffer.start()

        send_queries(ips_to_check)
        sniffer.join()
        captured_packets = sniffer.results
        if len(captured_packets) == 0:
            return None
        captured_packet = captured_packets[0]
        captured_packet_load = captured_packet[Raw].load
        packet_paylod = IP(captured_packet_load[len(PAYLOAD_MAGIC) :])
        ip = packet_paylod.src
        if sys.platform.startswith("linux"):
            ##to be sure with linux
            parts = ip.split(".")
            parts[0] = "127"
            return ".".join(parts)
        return ip
    except:
        return None


def main():
    network_stats = NetworkStats.get_stats()
    if network_stats is None:
        print("error in netstats")
        exit(1)
    try:
        cached_ip = get_cached_ip()
        result = None
        try:
            if cached_ip is not None:
                result = find_server(network_stats.default_device, [cached_ip])
        finally:
            if result is None:
                result = find_server(
                    network_stats.default_device, network_stats.network.hosts()
                )
        if result is not None:
            print(f"DNS: server is at: {result}")
            print(f"{result}*100")
            add_to_hosts_file(result, DOMAIN)
            save_cached_ip(result)
        else:
            print("Server not found")
    except Exception as e:
        print(e)
        exit(1)


if __name__ == "__main__":
    main()
