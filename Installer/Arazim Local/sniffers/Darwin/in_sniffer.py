import sys
import os
from scapy.all import sniff, send, Raw
from scapy.layers.inet import IP, TCP, defragment

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
from sniffers.constants import PAYLOAD_MAGIC
from sniffers.sniffers_utils import sniff_assembeld
from utils import network_stats


def real_ip_to_local(ip):
    ind = ip.find(".")
    if ind == -1:
        raise ValueError("Invalid IP")
    return "127" + ip[ind:]


fragment_cache = dict()


def is_fragmented(pkt):
    return pkt[IP].flags == 1 or pkt[IP].frag > 0


class Sniffer:
    def __init__(self, our_ip, default_gateway, sniff_iface, lo_iface):
        self.our_ip = our_ip
        self.default_gateway = default_gateway
        self.sniff_iface = sniff_iface
        self.lo_iface = lo_iface
        self.bpf_filter = f"dst host {our_ip} and src {default_gateway} and ip"

    def start_sniff(self):
        """
        sniff(
            filter=self.bpf_filter,
            iface=self.sniff_iface,
            prn=self.handle_packet,
            store=0,
        )
        """
        sniff_assembeld(
            filter=self.bpf_filter, iface=self.sniff_iface, prn=self.handle_packet
        )

    def handle_packet(self, pkt):
        if is_fragmented(pkt):
            if pkt[IP].id not in fragment_cache.keys():
                fragment_cache[pkt[IP].id] = [pkt]
            else:
                fragment_cache[pkt[IP].id].append(pkt)
                reassembled = defragment(fragment_cache[pkt[IP].id])
                if len(reassembled) == 1 and not is_fragmented(reassembled[0]):
                    self.decapsulate_and_inject(reassembled[0])
        else:
            self.decapsulate_and_inject(pkt)

    def decapsulate_and_inject(self, pkt):
        """
        Takes an ICMP echo packet, checks that the magic is there,
        and injects the "raw" part into loopback.
        """
        try:
            # make sure its our magic
            if pkt[Raw].load[: len(PAYLOAD_MAGIC)] != PAYLOAD_MAGIC:
                return
            # get the raw, without magic (og packet)
            decapsulated = IP(pkt[Raw].load[len(PAYLOAD_MAGIC) :])
            # change src and dst to allow sending in lo
            decapsulated[IP].src = real_ip_to_local(decapsulated[IP].src)

            decapsulated[IP].dst = "127.0.0.1"
            # delete checksums to force recalculation, and send :-)
            del decapsulated[IP].chksum
            del decapsulated[IP].len
            if TCP in decapsulated:
                del decapsulated[TCP].chksum
            send(decapsulated, verbose=0, iface=self.lo_iface)
        except Exception as e:
            print(e)


def main():
    stats = network_stats.NetworkStats()
    if stats is None:
        print("Networks stats failed, closing sniffer")
        exit(0)
    in_sniffer = Sniffer(
        stats.my_ip, stats.router_ip, stats.default_device, stats.loopback_device
    )
    in_sniffer.start_sniff()


if __name__ == "__main__":
    if os.geteuid() != 0:
        sys.exit("Please run as root/sudo.")
    main()
