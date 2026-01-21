import subprocess
import sys


def configure_routing(subnet):
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



def remove_routing(subnet):
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