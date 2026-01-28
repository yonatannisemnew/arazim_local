import sys
import os

# Your path setup
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from utils.network_stats import NetworkStats
from utils.Windows.arp_table_stats import WindowsArpManager


def add_subnet_to_arp_table(network_stats):
    """
    Fills the Windows ARP table with every IP in the current subnet,
    mapping them to the router's MAC address to ensure local traffic
    is routed through the gateway.
    """
    print(f"[*] Target Subnet: {network_stats.network}")
    print(f"[*] Mapping to Router MAC: {network_stats.router_mac}")

    # 1. Fetch existing entries to avoid unnecessary command calls
    current_entries = WindowsArpManager.get_table()
    # We create a set of IPs for O(1) lookup speed
    existing_ips = {entry["ip"] for entry in current_entries}

    # 2. Iterate through the subnet hosts
    added_count = 0
    skipped_count = 0

    # .hosts() provides all valid IPs excluding network/broadcast
    for ip_obj in network_stats.network.hosts():
        ip_str = str(ip_obj)

        if ip_str in existing_ips:
            skipped_count += 1
            continue

        # 3. Add the entry
        # We pass network_stats.my_ip as the 'interface_ip' so Windows
        # knows exactly which network card to apply this static route to.
        success = WindowsArpManager.add_static_entry(
            ip=ip_str, mac=network_stats.router_mac, interface_ip=network_stats.my_ip
        )

        if success:
            added_count += 1

    print(f"\n--- Process Complete ---")
    print(f"Added: {added_count}")
    print(f"Already Existed: {skipped_count}")


def main():
    # Make sure to run as Admin!
    try:
        stats = NetworkStats()
        if not stats.router_mac:
            print("[-] Could not resolve Router MAC. Exiting.")
            return

        add_subnet_to_arp_table(stats)

    except PermissionError:
        print("[-] Permission Denied: Please run this script as Administrator.")
    except Exception as e:
        print(f"[-] An unexpected error occurred: {e}")


if __name__ == "__main__":
    main()
