from scapy.config import conf
from arp_cacher import insert_to_arp_cache
from edit_hosts_file import insert_to_hosts
from DNS.client import protocol
import json


server_ip_address_json_path = "server_ip_address.json"
MASK_SIZE = 24

def find_server_ip_address(DEFAULT_GATEWAY: str):
    try:
        with open(server_ip_address_json_path, 'r') as file:
            data = json.load(file)
            ip = protocol(data["server_ip_address"], 32, 0.1)
            if ip != None:
                return ip
            else:
                found_ip = protocol(DEFAULT_GATEWAY, MASK_SIZE, 10)
                return found_ip
    except FileNotFoundError:
        found_ip = protocol(DEFAULT_GATEWAY, MASK_SIZE, 10)
        return found_ip


def setup_server_conn():
    DEFAULT_GATEWAY = conf.route.route("0.0.0.0")[2]

    insert_to_arp_cache()
    insert_to_hosts()


if __name__ == '__main__':
    setup_server_conn()