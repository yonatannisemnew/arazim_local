import subprocess
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from utils import network_stats


def add_subnet_to_loopback(ips):
    cmd = "\n".join(f"sudo ifconfig lo0 alias {ip}; netmask 0xffffffff anycast" for ip in ips)
    """cmd = (
        "for i in {1..254}; do "
        "sudo ifconfig lo0 alias 127.16.164.$i; netmask 0xffffffff anycast"
        "sudo ifconfig lo0 alias 127.16.165.$i; netmask 0xffffffff anycast"
        "done"
    )"""
    subprocess.run(cmd, shell=True, executable="/bin/bash")

def disable_rst(subnet):
    rules = (
        f"block drop out proto tcp from any to {subnet} flags R/R\n"
        f"block drop out proto tcp from {subnet} to any flags R/R\n"
    )

    try:
        subprocess.run(f"echo '{rules}' | sudo pfctl -f -", shell=True, check=True)
        subprocess.run("sudo pfctl -e", shell=True, stderr=subprocess.DEVNULL)
        print("[-] Firewall rules loaded and PF enabled.")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to load firewall rules: {e}")

if __name__ == "__main__":
    netstats = network_stats.NetworkStats()
    ips = [str(ip) for ip in netstats.network]
    add_subnet_to_loopback(ips)
    subnet_str = f"{netstats.get_base_addr()}/{netstats.network.prefixlen}"
    disable_rst(subnet_str)