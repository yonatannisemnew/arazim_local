#define _DEFAULT_SOURCE
#include "dns_server.h"
#include <pcap.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <arpa/inet.h>
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#include <netinet/if_ether.h>
#include <ctype.h>
#include <sys/ioctl.h>
#include <net/if.h>
#include <unistd.h>

#define SNAP_LEN 1518 // 1500 bytes + Ethernet header

pcap_t *handle_global = NULL;

    // Globals to store my own Interface details
struct in_addr my_ip;
unsigned char my_mac[6];

    // Helper to get local IP and MAC
void get_interface_info(const char *interface) 
{
    int fd;
    struct ifreq ifr;

    fd = socket(AF_INET, SOCK_DGRAM, 0);
    if (fd == -1) {
        perror("socket");
        exit(1);
    }

    // Get IP Address
    ifr.ifr_addr.sa_family = AF_INET;
    strncpy(ifr.ifr_name, interface, IFNAMSIZ - 1);
    if (ioctl(fd, SIOCGIFADDR, &ifr) == -1) {
        perror("ioctl IP");
        close(fd);
        exit(1);
    }
    my_ip = ((struct sockaddr_in *)&ifr.ifr_addr)->sin_addr;

    // Get MAC Address
    if (ioctl(fd, SIOCGIFHWADDR, &ifr) == -1) {
        perror("ioctl MAC");
        close(fd);
        exit(1);
    }
    memcpy(my_mac, ifr.ifr_hwaddr.sa_data, 6);

    close(fd);

    printf("Initialized. My IP: %s\n", inet_ntoa(my_ip));
    printf("Initialized. My MAC: %02x:%02x:%02x:%02x:%02x:%02x\n",
           my_mac[0], my_mac[1], my_mac[2], my_mac[3], my_mac[4], my_mac[5]);
}

// Checksum calculation for IP/ICMP
unsigned short calculate_checksum(unsigned short *paddress, int len) {
    int nleft = len;
    int sum = 0;
    unsigned short *w = paddress;
    unsigned short answer = 0;

    while (nleft > 1) {
        sum += *w++;
        nleft -= 2;
    }

    if (nleft == 1) {
        *(unsigned char *)&answer = *(unsigned char *)w;
        sum += answer;
    }

    sum = (sum >> 16) + (sum & 0xFFFF);
    sum += (sum >> 16);
    answer = ~sum;
    return answer;
}

int start_dns_server(const char *interface) {
    char errbuf[PCAP_ERRBUF_SIZE];
    struct bpf_program fp;
    bpf_u_int32 mask;
    bpf_u_int32 net;

    // 1. Get local Interface details first
    get_interface_info(interface);

    // Get network number and mask
    if (pcap_lookupnet(interface, &net, &mask, errbuf) == -1) {
        fprintf(stderr, "Can't get netmask for device %s\n", interface);
        net = 0;
        mask = 0;
    }

    // Open session (0 = non-promiscuous, though we filter in software anyway)
    handle_global = pcap_open_live(interface, SNAP_LEN, 1, 1000, errbuf);
    if (handle_global == NULL) {
        fprintf(stderr, "Couldn't open device %s: %s\n", interface, errbuf);
        return 2;
    }

    // Compile and apply filter for ICMP only
    if (pcap_compile(handle_global, &fp, "icmp", 0, net) == -1) {
        fprintf(stderr, "Couldn't parse filter: %s\n", pcap_geterr(handle_global));
        return 2;
    }
    if (pcap_setfilter(handle_global, &fp) == -1) {
        fprintf(stderr, "Couldn't install filter: %s\n", pcap_geterr(handle_global));
        return 2;
    }

    printf("Server started on %s. Waiting for payload: %s\n", interface, PAYLOAD);

    // Loop forever
    pcap_loop(handle_global, -1, (pcap_handler)handle_packet, NULL);

    pcap_freecode(&fp);
    pcap_close(handle_global);
    return 0;
}

int handle_packet(u_char *args, const struct pcap_pkthdr *header, const u_char *packet) {
    struct ether_header *eth_header;
    struct ip *ip_header;
    struct icmp *icmp_header;
    
    // Parse Ethernet
    eth_header = (struct ether_header *)packet;
    
    // Parse IP (assume Ethernet header is 14 bytes)
    ip_header = (struct ip *)(packet + ETHER_HDR_LEN);
    int ip_header_len = ip_header->ip_hl * 4;

    // --- NEW CHECK: Only respond if Destination IP matches My IP ---
    if (ip_header->ip_dst.s_addr != my_ip.s_addr) {
        return 0; // Ignore packet
    }

    // Parse ICMP
    icmp_header = (struct icmp *)(packet + ETHER_HDR_LEN + ip_header_len);
    
    // Calculate payload location and size
    u_char *payload = (u_char *)((u_char *)icmp_header + 8); // ICMP header is 8 bytes
    int payload_len = ntohs(ip_header->ip_len) - ip_header_len - 8;

    if (payload_len < strlen(PAYLOAD)) return 0;

    // Check for specific payload
    if (memcmp(payload, PAYLOAD, strlen(PAYLOAD)) == 0) {
        printf("Packet Detected! Sending response...\n");

        u_char response_packet[1024];
        int response_size = 0;

        if (create_dns_response(packet, response_packet, &response_size) == 0) {
            if (pcap_sendpacket(handle_global, response_packet, response_size) != 0) {
                fprintf(stderr, "Error sending packet: %s\n", pcap_geterr(handle_global));
                return 1;
            }
            printf("Response sent.\n");
        }
    }
    return 0;
}

int create_dns_response(const u_char *request, u_char *response, int *response_size) {
    struct ether_header *req_eth = (struct ether_header *)request;
    struct ip *req_ip = (struct ip *)(request + ETHER_HDR_LEN);
    
    struct ether_header *resp_eth = (struct ether_header *)response;
    struct ip *resp_ip = (struct ip *)(response + ETHER_HDR_LEN);
    struct icmp *resp_icmp = (struct icmp *)(response + ETHER_HDR_LEN + sizeof(struct ip));
    
    int data_len = strlen(RESPONSE_PAYLOAD);

    // 1. Ethernet Header
    // Dest MAC = Request Source MAC
    memcpy(resp_eth->ether_dhost, req_eth->ether_shost, ETHER_ADDR_LEN);
    // Source MAC = My Own MAC (Explicitly)
    memcpy(resp_eth->ether_shost, my_mac, ETHER_ADDR_LEN);
    resp_eth->ether_type = req_eth->ether_type;

    // 2. IP Header
    resp_ip->ip_hl = 5;
    resp_ip->ip_v = 4;
    resp_ip->ip_tos = 0;
    resp_ip->ip_len = htons(sizeof(struct ip) + sizeof(struct icmp) + data_len);
    resp_ip->ip_id = htons(54321);
    resp_ip->ip_off = 0;
    resp_ip->ip_ttl = 64;
    resp_ip->ip_p = IPPROTO_ICMP;
    
    // Dest IP = Request Source IP
    resp_ip->ip_dst = req_ip->ip_src;
    // Source IP = My Own IP (Explicitly)
    resp_ip->ip_src = my_ip;
    
    resp_ip->ip_sum = 0;
    resp_ip->ip_sum = calculate_checksum((unsigned short *)resp_ip, sizeof(struct ip));

    // 3. ICMP Header (Type 0 = Echo Reply)
    resp_icmp->icmp_type = ICMP_ECHOREPLY;
    resp_icmp->icmp_code = 0;
    resp_icmp->icmp_id = ((struct icmp *)(request + ETHER_HDR_LEN + (req_ip->ip_hl * 4)))->icmp_id;
    resp_icmp->icmp_seq = ((struct icmp *)(request + ETHER_HDR_LEN + (req_ip->ip_hl * 4)))->icmp_seq;
    
    // 4. Payload
    char *data_ptr = (char *)resp_icmp + 8;
    memcpy(data_ptr, RESPONSE_PAYLOAD, data_len);

    // 5. ICMP Checksum
    resp_icmp->icmp_cksum = 0;
    resp_icmp->icmp_cksum = calculate_checksum((unsigned short *)resp_icmp, 8 + data_len);

    *response_size = ETHER_HDR_LEN + sizeof(struct ip) + 8 + data_len;
    return 0;
}

int main(int argc, char **argv) {
    printf("starting dns server!\n");
    start_dns_server(INTERFACE);
    return 0;
}