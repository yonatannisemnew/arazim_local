import sys
import ipaddress

def is_valid_ip(ip_str: str) -> bool:
    try:
        ipaddress.IPv4Address(ip_str)
        return True
    except ipaddress.AddressValueError:
        return False



def sniffer_parse_args(args: list[str]) -> tuple[str, str, str, int]:
    if len(args) != 5:
        print("Usage: in_sniffer_windows.py <router_ip> <subnet_mask> <my_ip> <interface_index>")
        sys.exit(1)
    for i in range(1,4):
        if not is_valid_ip(args[i]):
            print(f"Invalid IP address: {args[i]}")
            sys.exit(1)

    router_ip = args[1]
    subnet_mask = args[2]
    my_ip = args[3]
    interface_index = int(args[4])
    return my_ip, router_ip, subnet_mask, interface_index

