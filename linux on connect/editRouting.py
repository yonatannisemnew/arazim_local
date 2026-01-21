import subprocess
import sys
import ipaddress

# routing table editing support, darwin and windows are untested

def get_windows_mask(subnet_cidr):
    """
    Converts CIDR notation (e.g., '192.168.1.0/24')
    to a Windows-style subnet mask (e.g., '255.255.255.0').
    """
    try:
        # Create an IPv4Network object; strict=False allows host bits to be set
        network = ipaddress.IPv4Network(subnet_cidr, strict=False)
        return str(network.netmask)
    except ValueError as e:
        return f"Invalid subnet format: {e}"

def configure_linux_routing(subnet):
    """
    Configures Linux routing table:
    1. Adds a subnet route via the loopback (lo) interface.
    """
    try:
        # 1. Add subnet via loopback with a LOWER priority (higher metric)
        # Metric 200 is used here.
        print(f"Routing subnet {subnet} to loopback (lo) with metric 200...")
        subprocess.run(
            ["sudo", "ip", "route", "add", subnet, "dev", "lo", "metric", "200"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error updating routing table: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)



def remove_linux_routing(subnet):
    """
    removes custom configuration Linux routing table:
    1. removes a subnet route via the loopback (lo) interface.
    """
    try:
        # 1. del subnet
        print(f"unRouting subnet {subnet}...")
        subprocess.run(
            ["sudo", "ip", "route", "del", subnet],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error updating routing table: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)

def configure_windows_routing(subnet):
    """
    Adds a subnet route via the loopback interface on Windows.
    """
    try:
        mask = get_windows_mask(subnet)
        # Windows 'route' uses 'mask' keyword and 127.0.0.1 for loopback
        # Example: route add 192.168.10.0 mask 255.255.255.0 127.0.0.1 metric 200
        dest_ip = subnet.split('/')[0] if '/' in subnet else subnet
        subprocess.run(
            ["route", "ADD", dest_ip, "MASK", mask, "127.0.0.1", "METRIC", "200"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error adding route: {e}", file=sys.stderr)


def remove_windows_routing(subnet):
    """
    Removes the custom subnet route on windows.
    """
    try:
        dest_ip = subnet.split('/')[0] if '/' in subnet else subnet
        subprocess.run(["route", "DELETE", dest_ip], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error removing route: {e}", file=sys.stderr)


def configure_darwin_routing(subnet):
    """
    Configures macOS (Darwin) routing table:
    Adds a subnet route via the loopback (lo0) interface.
    """
    try:
        # In macOS, the loopback interface is typically lo0
        # The 'route' command uses the -interface flag to direct traffic to a device
        # macOS route command format: route add -net <network> -interface lo0
        # Note: macOS doesn't use 'metrics' in the same way as Linux;
        # priority is handled by the order of specific routes vs. defaults.
        subprocess.run(
            ["sudo", "route", "-n", "add", "-net", subnet, "-interface", "lo0"],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print(f"Error updating macOS routing table: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


def remove_darwin_routing(subnet):
    """
    Removes custom configuration from macOS (Darwin) routing table.
    """
    try:
        # macOS delete command format: route delete -net <network>
        subprocess.run(
            ["sudo", "route", "-n", "delete", "-net", subnet],
            check=True
        )

    except subprocess.CalledProcessError as e:
        print(f"Error removing macOS route: {e}", file=sys.stderr)
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)


def configure_routing(subnet):
    os_type = sys.platform
    if os_type.startswith("linux"):
        configure_linux_routing(subnet)
    elif os_type.startswith("darwin"):
        configure_darwin_routing(subnet)
    elif os_type.startswith("win32"):
        configure_windows_routing(subnet)


def remove_routing(subnet):
    os_type = sys.platform
    if os_type.startswith("linux"):
        remove_linux_routing(subnet)
    elif os_type.startswith("darwin"):
        remove_darwin_routing(subnet)
    elif os_type.startswith("win32"):
        remove_windows_routing(subnet)


if __name__ == "__main__":
    remove_linux_routing("172.16.164.0/23")
    configure_linux_routing("172.16.164.0/23")