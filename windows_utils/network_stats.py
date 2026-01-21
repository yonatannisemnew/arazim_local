import os
import json
import subprocess
import tempfile
import ipaddress

def get_network_stats():
    result_file = os.path.join(tempfile.gettempdir(), "sniffer_result.json")
    if os.path.exists(result_file):
        os.remove(result_file)
    subprocess.run(["sniffer_start.bat"], capture_output=False)
    my_ip = None
    router_ip = None
    subnet_mask = None
    network = None

    # Run the batch script
    with open(result_file, "r") as f:
        network_info = json.load(f)
        my_ip = network_info[0]
        router_ip = network_info[1]
        subnet_mask = network_info[2]
        network = ipaddress.IPv4Network(f"{my_ip}/{subnet_mask}", strict=False)
    return {
        "my_ip": my_ip,
        "router_ip": router_ip,
        "subnet_mask": subnet_mask,
        "network": network,
    }

def get_interface_index():
    result_file = os.path.join(tempfile.gettempdir(), "sniffer_result.json")
    if os.path.exists(result_file):
        os.remove(result_file)
    subprocess.run(["sniffer_start.bat"], capture_output=False)
    with open(result_file, "r") as f:
        network_info = json.load(f)
        interface_index = network_info[3]
    return interface_index

def poison_arp_cache(target_ip: str, target_mac: str):
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    if target_ip in result.stdout:
        print(f"Existing entry for {target_ip} found. Attempting to delete (requires Admin)...")
        subprocess.run(["arp", "-d", target_ip], capture_output=True)

    win_mac = target_mac.replace(":", "-")

    print(f"Adding static ARP entry for {target_ip} (requires Admin)...")

    add_res = subprocess.run(["arp", "-s", target_ip, win_mac], capture_output=True, text=True)
    if add_res.returncode != 0:
        print("Error: Could not add ARP entry. Please run this script as Administrator.")
    else:
        print("Successfully updated ARP cache.")
