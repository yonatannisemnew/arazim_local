import ipaddress
class NetworkStats:

    def __init__(self, my_ip, router_ip, subnet_mask, interface_index):
        self.my_ip = my_ip
        self.router_ip = router_ip
        self.subnet_mask = subnet_mask
        self.network = ipaddress.IPv4Network(f"{my_ip}/{subnet_mask}", strict=False)
        self.interface_index = interface_index
    def in_subnet(self, ip_addr):
        return ipaddress.IPv4Address(ip_addr) in self.network
    
    def base_addr(self):
        """Returns the mathematically correct network address (e.g., 172.16.158.0)"""
        return str(self.network.network_address)

