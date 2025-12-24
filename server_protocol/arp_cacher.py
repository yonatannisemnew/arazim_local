import json
import sys, subprocess


def insert_to_arp_cache(ip, mac, device=""):
    # --- Linux Logic ---
    if sys.platform.startswith("linux"):
        result = subprocess.run(["ip", "-j", "n"], capture_output=True, text=True)
        neighbors = json.loads(result.stdout)
        for n in neighbors:
            if (n.get("ip") == ip and (n.get("dev") == device or device == "")):
                print("need to delete existing arp entry, sudo required")
                subprocess.run(["sudo", "ip", "n", "del", n.get("ip"), "dev", n.get("dev")], capture_output=True,
                               text=True)

        if device == "":
            cmd = "ip route get " + ip + " | grep -Po '(?<=dev )(\\S+)'"
            device = subprocess.check_output(cmd, shell=True, text=True).strip()

        print("need to add arp entry, sudo required")
        subprocess.run(["sudo", "-S", "ip", "n", "add", ip, "lladdr", mac, "dev", device],
                       capture_output=True, text=True)

    # --- Windows Logic ---
    elif sys.platform == "win32":
        # 1. Check if the entry exists
        # 'arp -a' lists all entries
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True)

        if ip in result.stdout:
            print(f"Existing entry for {ip} found. Attempting to delete (requires Admin)...")
            # 'arp -d' deletes the entry for the specific IP
            subprocess.run(["arp", "-d", ip], capture_output=True)

        # 2. Format MAC for Windows (it prefers 00-00-00-00-00-00 format)
        win_mac = mac.replace(":", "-")

        print(f"Adding static ARP entry for {ip} (requires Admin)...")
        # 'arp -s' adds a static entry
        # Note: If multiple interfaces exist, Windows may require an interface IP,
        # but 'arp -s <ip> <mac>' usually defaults to the primary interface.
        add_res = subprocess.run(["arp", "-s", ip, win_mac], capture_output=True, text=True)

        if add_res.returncode != 0:
            print("Error: Could not add ARP entry. Please run this script as Administrator.")
        else:
            print("Successfully updated ARP cache.")

    # --- macOS Logic ---
    elif sys.platform.startswith("darwin"):
        pass


if __name__ == '__main__':
    # Ensure you run the terminal/IDE as Administrator on Windows
    insert_to_arp_cache("12.14.12.14", "12:12:12:12:12:12")

# def insert_to_arp_cache(ip, mac, device=""):
#     if sys.platform.startswith("linux"): #linux
#         result = subprocess.run(["ip", "-j", "n"], capture_output=True, text=True)
#         neighbors = json.loads(result.stdout)
#         for n in neighbors:
#             if (n.get("ip") == ip and (n.get("dev") == device or device == "")):
#                 print("need to delete existing arp entry, sudo required")
#                 del_res = subprocess.run(["sudo", "ip", "n", "del", n.get("ip"), "dev", n.get("dev")], capture_output=True, text=True)
#                 # print("out:", del_res.stdout, "err:", del_res.stderr)
#         if device == "":
#             cmd = "ip route get " + ip + " | grep -Po '(?<=dev )(\\S+)'"
#             device = subprocess.check_output(cmd, shell=True, text=True).strip()
#         print("need to add arp entry, sudo required")
#         add_res = subprocess.run(["sudo", "-S", "ip", "n", "add", ip, "lladdr", mac, "dev", device, "nud", "permanent"], capture_output=True, text=True)
#         # print("out:", add_res.stdout, "err:", add_res.stderr)
#     if sys.platform.startswith("darwin"):  # mac
#         pass
#     if sys.platform == "win32":  # windows
#         pass
#
#
# if __name__ == '__main__':
#     insert_to_arp_cache("12.14.12.14", "12:12:12:12:12:12")