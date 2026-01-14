#pragma once
#include "sniff.h"
// Handles (after filtering) ICMP packets sent to this PC, if has magic it sends into this pc the packet.
int handler(const struct pcap_pkthdr *hdr, const u_char *bytes, pcap_if_t *device);
// creates a bpf filter for the "recivier" sniffer - allows only ICMP packets with dst of our ip
void create_bpf(char *subnet, char *router_ip, char *our_ip, char *bpf);