import sys
import ipaddress

def is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        return False



def sniffer_parse_args(args: list[str]) -> tuple[str, str, str]:
    if len(args) != 4:
        print("Usage: in_sniffer_windows.py <router_ip> <subnet_mask> <my_ip>")
        sys.exit(1)
    for i in range(1,4):
        if not is_valid_ip(args[i]):
            print(f"Invalid IP address: {args[i]}")
            sys.exit(1)

    router_ip = args[1]
    subnet_mask = args[2]
    my_ip = args[3]
    return my_ip, router_ip, subnet_mask

