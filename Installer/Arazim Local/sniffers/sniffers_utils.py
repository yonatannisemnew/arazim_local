import sys
import os
from scapy.all import *
from scapy.layers.inet import IP, TCP


fragment_cache = dict()


def is_fragmented(pkt):
    return pkt[IP].flags == 1 or pkt[IP].frag > 0


def handle_fragmented(prn, pkt):
    global fragment_cache
    if is_fragmented(pkt):
        if pkt[IP].id not in fragment_cache.keys():
            fragment_cache[pkt[IP].id] = [pkt]
        else:
            fragment_cache[pkt[IP].id].append(pkt)
        reassembled = defragment(fragment_cache[pkt[IP].id])
        if len(reassembled) == 1 and not is_fragmented(reassembled[0]):
            del fragment_cache[pkt[IP].id]
            prn(reassembled[0])
    else:
        prn(pkt)


def sniff_assembeld(filter, iface, prn):
    sniff(
        filter=filter, iface=iface, prn=lambda pkt: handle_fragmented(prn, pkt), store=0
    )
