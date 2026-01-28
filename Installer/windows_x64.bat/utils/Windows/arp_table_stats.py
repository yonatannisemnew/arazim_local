import subprocess
import re
from scapy.all import ARP, Ether, srp  # Optional, for "active" discovery


class WindowsArpManager:
    @staticmethod
    def get_table():
        """
        Parses 'arp -a' into a list of dictionaries.
        Returns: [{'ip': '192.168.1.1', 'mac': 'aa:bb:cc...', 'type': 'dynamic'}, ...]
        """
        entries = []
        try:
            # Run 'arp -a' and capture output
            output = subprocess.check_output("arp -a", shell=True).decode()

            # Regex to find IP, MAC, and Type (Dynamic/Static)
            # Example line:  192.168.1.1       00-11-22-33-44-55     dynamic
            regex = r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F-]{17})\s+(\w+)"

            for line in output.splitlines():
                match = re.search(regex, line)
                if match:
                    entries.append(
                        {
                            "ip": match.group(1),
                            "mac": match.group(2).replace(
                                "-", ":"
                            ),  # Standardize MAC format
                            "type": match.group(3),
                        }
                    )
        except Exception as e:
            print(f"Error reading ARP table: {e}")
        return entries

    @staticmethod
    def add_static_entry(ip, mac, interface_ip=None):
        """
        Adds a static ARP entry.
        cmd: arp -s <IP> <MAC> [InterfaceIP]
        """
        cmd = f"arp -s {ip} {mac.replace(':', '-')}"
        if interface_ip:
            # On Windows with multiple NICs, specifying the Interface IP is often safer
            cmd += f" {interface_ip}"

        return WindowsArpManager._run_cmd(cmd)

    @staticmethod
    def delete_entry(ip, interface_ip=None):
        """
        Deletes an entry for a specific IP.
        cmd: arp -d <IP>
        """
        cmd = f"arp -d {ip}"
        if interface_ip:
            cmd += f" {interface_ip}"

        return WindowsArpManager._run_cmd(cmd)

    @staticmethod
    def clear_cache():
        """
        Clears the entire ARP cache (dangerous if you are remote!).
        cmd: arp -d *
        """
        return WindowsArpManager._run_cmd("arp -d *")

    @staticmethod
    def _run_cmd(cmd):
        print(f"Running: {cmd}")
        try:
            # shell=True is required for arp commands on Windows
            subprocess.check_call(cmd, shell=True)
            print("[+] Success")
            return True
        except subprocess.CalledProcessError:
            print("[-] Failed (Did you run as Admin?)")
            return False


# --- Usage ---
if __name__ == "__main__":
    manager = WindowsArpManager()

    # 1. VIEW Table
    print("\n--- Current ARP Table ---")
    for entry in manager.get_table():
        print(entry)

    # 2. ADD Static Entry (requires Admin)
    # Be careful! This prevents your PC from asking "Who is 192.168.1.55?"
    # It will blindly send packets to this MAC.
    # manager.add_static_entry("192.168.1.55", "aa:bb:cc:dd:ee:ff")

    # 3. DELETE Entry (requires Admin)
    # manager.delete_entry("192.168.1.55")
