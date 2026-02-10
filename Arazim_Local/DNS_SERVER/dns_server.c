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
#include <sys/socket.h>
#include <unistd.h>

#define SNAP_LEN 1518

pcap_t *handle_global = NULL;
int raw_sock;

/* ---------------- Checksum ---------------- */

unsigned short calculate_checksum(unsigned short *p, int len)
{
    unsigned int sum = 0;

    while (len > 1) {
        sum += *p++;
        len -= 2;
    }

    if (len == 1)
        sum += *(unsigned char *)p;

    sum = (sum >> 16) + (sum & 0xffff);
    sum += (sum >> 16);

    return (unsigned short)(~sum);
}

/* ---------------- Start Server ---------------- */

int start_dns_server(const char *interface)
{
    char errbuf[PCAP_ERRBUF_SIZE];
    struct bpf_program fp;

    /* RAW SOCKET FOR SENDING */
    raw_sock = socket(AF_INET, SOCK_RAW, IPPROTO_ICMP);
    if (raw_sock < 0) {
        perror("raw socket");
        return 1;
    }

    handle_global = pcap_open_live(
        interface,
        SNAP_LEN,
        1,
        1000,
        errbuf
    );

    if (!handle_global) {
        fprintf(stderr, "pcap_open_live: %s\n", errbuf);
        return 1;
    }

    if (pcap_compile(handle_global, &fp, "icmp", 0, 0) == -1 ||
        pcap_setfilter(handle_global, &fp) == -1) {
        fprintf(stderr, "pcap filter error\n");
        return 1;
    }

    printf("Server started on %s\n", interface);
    printf("Waiting for payload \"%s\"\n", PAYLOAD);

    pcap_loop(handle_global, -1,
              (pcap_handler)handle_packet, NULL);

    return 0;
}

/* ---------------- Packet Handler ---------------- */

int handle_packet(u_char *args,
                  const struct pcap_pkthdr *header,
                  const u_char *packet)
{
    (void)args;

    struct ether_header *eth = (struct ether_header *)packet;
    struct ip *ip = (struct ip *)(packet + ETHER_HDR_LEN);

    int ip_len = ip->ip_hl * 4;
    if (ip_len < 20)
        return 0;

    if (ip->ip_p != IPPROTO_ICMP)
        return 0;

    struct icmp *icmp =
        (struct icmp *)(packet + ETHER_HDR_LEN + ip_len);

    u_char *payload = (u_char *)icmp + 8;
    int payload_len =
        ntohs(ip->ip_len) - ip_len - 8;

    if (payload_len < (int)strlen(PAYLOAD))
        return 0;

    if (memcmp(payload, PAYLOAD, strlen(PAYLOAD)) != 0)
        return 0;

    printf("\n--- PACKET MATCH ---\n");
    printf("From %s\n", inet_ntoa(ip->ip_src));

    u_char response[1024];
    int response_len = 0;

    if (create_dns_response(packet, response, &response_len) == 0) {

        struct sockaddr_in dst;
        memset(&dst, 0, sizeof(dst));
        dst.sin_family = AF_INET;
        dst.sin_addr = ip->ip_src;

        if (sendto(raw_sock,
                   response,
                   response_len,
                   0,
                   (struct sockaddr *)&dst,
                   sizeof(dst)) < 0) {
            perror("sendto");
        } else {
            printf("Response sent (%d bytes)\n",
                   response_len);
        }
    }

    return 0;
}

/* ---------------- Build ICMP Response ---------------- */

int create_dns_response(const u_char *request,
                        u_char *response,
                        int *response_size)
{
    struct ip *req_ip =
        (struct ip *)(request + ETHER_HDR_LEN);
    struct icmp *req_icmp =
        (struct icmp *)(request +
                        ETHER_HDR_LEN +
                        req_ip->ip_hl * 4);

    struct icmp *icmp = (struct icmp *)response;

    int data_len = strlen(RESPONSE_PAYLOAD);

    icmp->icmp_type = ICMP_ECHO;     /* REQUEST */
    icmp->icmp_code = 0;
    icmp->icmp_id   = req_icmp->icmp_id;
    icmp->icmp_seq  = req_icmp->icmp_seq;

    memcpy(response + 8,
           RESPONSE_PAYLOAD,
           data_len);

    icmp->icmp_cksum = 0;
    icmp->icmp_cksum =
        calculate_checksum(
            (unsigned short *)icmp,
            8 + data_len);

    *response_size = 8 + data_len;
    return 0;
}

/* ---------------- Main ---------------- */

int main(int argc, char **argv)
{
    printf("Starting DNS-over-ICMP server\n");
    start_dns_server(INTERFACE);
    return 0;
}
