import subprocess
import sys
import os

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from utils import network_stats

def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]

def add_subnet_to_loopback(ips):
    print("here")
    cmd = "\n".join(f"sudo ifconfig lo0 alias {ip} 255.255.255.255" for ip in ips)
    subprocess.run(cmd, shell=True, executable="/bin/bash")
    ip_list_str = "{" + ", ".join(ips) + "}"
    pf_rule = f"nat on lo0 from any to {ip_list_str} -> 127.0.0.1"
    
    # We pipe the rule directly into pfctl using a specific 'anchor' 
    # so we don't interfere with the main system firewall.
    pf_cmd = (
        f'echo "{pf_rule}" | sudo pfctl -a "com.user.anycast" -f - && '
        f'sudo pfctl -e'
    )
    
    subprocess.run(pf_cmd, shell=True, executable="/bin/bash")

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
    netstats = network_stats.NetworkStats.get_stats()
    ips = [real_ip_to_local(str(ip)) for ip in netstats.network]
    add_subnet_to_loopback(ips)
    subnet_str = f"{real_ip_to_local(netstats.get_base_addr())}/{netstats.network.prefixlen}"
    disable_rst(subnet_str)