import subprocess
import platform
import psutil
from scapy.all import *
import ipaddress


class NetworkStats:
    def __init__(self):
        self.my_ip, self.router_ip, self.default_device = self._get_ips_and_def_device()
        self.subnet_mask = self._get_subnet_mask(self.router_ip)
        self.network = ipaddress.IPv4Network(
            f"{self.my_ip}/{self.subnet_mask}", strict=False
        )
        self.my_mac = self.get_my_mac(self.default_device)
        self.router_mac = self.get_router_mac(self.router_ip)
        self.loopback_device = self.get_loopback_device()

    def in_subnet(self, ip_addr):
        return ipaddress.IPv4Address(ip_addr) in self.network

    def get_base_addr(self):
        """Returns the mathematically correct network address (e.g., 172.16.158.0)"""
        return str(self.network.network_address)

    def get_router_mac(self, router_ip):
        # Create an Ethernet frame directed to the broadcast MAC (ff:ff:ff:ff:ff:ff)
        eth = Ether(dst="ff:ff:ff:ff:ff:ff")
        # Create an ARP request for the router's IP
        arp = ARP(pdst=self.router_ip)

        # Stack them and send/receive (srp)
        ans, unans = srp(eth / arp, timeout=2, verbose=False)

        for sent, received in ans:
            return received.hwsrc  # This is the router's MAC

        return None

    def get_my_mac(self, interface):
        addrs = psutil.net_if_addrs()
        if interface in addrs:
            for addr in addrs[interface]:
                if addr.family == psutil.AF_LINK:
                    return addr.address
        return None

    def _get_ips_and_def_device(self):
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

    def _get_subnet_mask(self, router_ip):
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
        return None

    def get_loopback_device(self):
        interfaces = psutil.net_if_addrs()
        # iterate through devices, check what has 127 and guess its the loopback
        for iface, addrs in interfaces.items():
            for addr in addrs:
                if addr.family == socket.AF_INET and addr.address.startswith("127."):
                    return iface
        return None


if __name__ == "__main__":
    stats = NetworkStats()
    print(f"My IP: {stats.my_ip}")
    print(f"Router IP: {stats.router_ip}")
    print(f"Default Device: {stats.default_device}")
    print(f"Subnet Mask: {stats.subnet_mask}")
    print(f"My MAC: {stats.my_mac}")
    print(f"Router MAC: {stats.router_mac}")
    print(f"Network Base Address: {stats.get_base_addr()}")
