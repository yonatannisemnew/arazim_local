import subprocess
import platform
import psutil
from scapy.all import *
from constants import *
from snippets.DNS.client import MY_IP


def get_current_network_name():
    try:
        os_name = platform.system()

        if os_name == WINDOWS:
            # Query Windows netsh
            output = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"]
            ).decode(DECODE_FORMAT, errors="ignore")
            for line in output.split("\n"):
                if "SSID" in line and "BSSID" not in line:
                    return line.split(":")[1].strip()

        elif os_name == MACOS:  # macOS
            # Query macOS airport utility
            cmd = "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I"
            output = subprocess.check_output(cmd, shell=True).decode(
                DECODE_FORMAT, errors="ignore"
            )
            for line in output.split("\n"):
                if " SSID" in line:
                    return line.split(":")[1].strip()

        elif os_name == LINUX:
            # Query Linux nmcli
            output = subprocess.check_output(
                ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"]
            ).decode(DECODE_FORMAT, errors="ignore")
            for line in output.split("\n"):
                if line.startswith("yes"):
                    return line.split(":")[1]

    except Exception as ex:
        return f"Error retrieving network name: {ex}"

    return NETWORK_NOT_FOUND


def get_ip_and_def_device():
    # find default gateway and my ip
    dst, my_ip, router_ip = conf.route.route(DEFAULT_GATEWAY)
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
    return SUBNET_NOT_FOUND


def get_network_properties():
    ip = get_if_addr(conf.iface)
    if ip == DEFAULT_GATEWAY or ip == LOOPBACK_IP:
        return {
            NETWORK_NAME_KEY: NOT_CONNECTED_MESSAGE,
            MY_IP_KEY: None,
            ROUTER_IP_KEY: None,
            DEFAULT_DEVICE_KEY: None,
            SUBNET_MASK_KEY: None,
        }
    network_name = get_current_network_name()
    my_ip, router_ip, default_device = get_ip_and_def_device()
    subnet_mask = get_subnet_mask(router_ip)

    return {
        NETWORK_NAME_KEY: network_name,
        MY_IP_KEY: my_ip,
        ROUTER_IP_KEY: router_ip,
        DEFAULT_DEVICE_KEY: default_device,
        SUBNET_MASK_KEY: subnet_mask,
    }


if __name__ == "__main__":
    print(get_network_properties())  # Example usage
