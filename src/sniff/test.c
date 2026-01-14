#include "test.h"
// desirilzies ping packets and fake sends them
int handler(const struct pcap_pkthdr *hdr, const u_char *bytes, pcap_if_t *device)
{
    printf("\nhandler: captured packet len=%u caplen=%u", hdr->len, hdr->caplen);
}

// creates a bpf filter for the "recivier" sniffer - allows only ICMP packets with dst of our ip
void create_bpf(char *subnet, char *router_ip, char *our_ip, char *bpf)
{
    snprintf(bpf, 256, "icmp");
}
