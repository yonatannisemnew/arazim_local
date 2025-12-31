from arp_cacher import insert_to_arp_cache
from edit_hosts_file import insert_to_hosts
from DNS.client import protocol


def setup_server_conn():
    protocol()
    insert_to_arp_cache()
    insert_to_hosts()


if __name__ == '__main__':
    setup_server_conn()