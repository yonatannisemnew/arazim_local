import subprocess
import psutil
from scapy.all import *


def get_current_network_name():
    try:
        # Query Linux nmcli
        output = subprocess.check_output(
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]
        ).decode("utf-8")
        for line in output.split("\n"):
            if line.startswith("yes"):
                return line.split(":")[1]

    except Exception as ex:
        return f"Error retrieving network name: {ex}"

    return "Network name not found (or not on Wi-Fi)"


def get_ip_and_def_device():
    # find default gateway and my ip
    dst, my_ip, router_ip = conf.route.route("0.0.0.0")
    if isinstance(router_ip, int):
        router_ip = socket.if_indextoname(router_ip)

    # find default device
    default_device = None
    for iface, addrs in psutil.net_if_addrs().items():
        if any(a.address == my_ip for a in addrs):
            default_device = iface
            break
    return (my_ip, router_ip, default_device)


def get_subnet_mask(router_ip):
    # get subnet mask
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((router_ip, 1))
        local_ip = s.getsockname()[0]
    except Exception as e:
        return f"Error connecting to router: {e}"
    finally:
        s.close()

    interfaces = psutil.net_if_addrs()
    for _, addresses in interfaces.items():
        for addr in addresses:
            if addr.address == local_ip:
                return addr.netmask
    return "Subnet mask not found for that interface."

def get_loopback_device():
    interfaces = psutil.net_if_addrs()
    # iterate through devices, check what has 127 and guess its the loopback
    for iface, addrs in interfaces.items():
        for addr in addrs:
            if addr.family == socket.AF_INET and addr.address.startswith("127."):
                return iface
    return None

def get_network_properties():
    network_name = get_current_network_name()
    my_ip, router_ip, default_device = get_ip_and_def_device()
    subnet_mask = get_subnet_mask(router_ip)
    loopback_device = get_loopback_device()

    return {
        "network_name": network_name,
        "my_ip": my_ip,
        "router_ip": router_ip,
        "subnet_mask": subnet_mask,
        "loopback_device": loopback_device,
    }


if __name__ == "__main__":
    print(get_network_properties())  # Example usage