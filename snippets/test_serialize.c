#ifndef _WIN32
#define _DEFAULT_SOURCE 1
#define _POSIX_C_SOURCE 200809L
#endif

#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#pragma comment(lib, "ws2_32.lib")
#pragma comment(lib, "wpcap.lib")
#define getpid GetCurrentProcessId
typedef DWORD pid_t;
#else
#define _DEFAULT_SOURCE 1
#define _POSIX_C_SOURCE 200809L
#include <arpa/inet.h>
#include <sys/types.h>
#include <netinet/in.h>
#include <netinet/ip.h>
#ifdef __APPLE__
#include <netinet/in_systm.h>
#include <netinet/ip_icmp.h>
#else
#include <netinet/ip_icmp.h>
#endif
#include <sys/socket.h>
#include <sys/time.h>
#include <time.h>
#include <unistd.h>
#endif

#include <pcap.h>
#include "serialize.h"

static volatile sig_atomic_t stop_flag = 0;

static void on_sigint(int sig) {
    (void)sig;
    stop_flag = 1;
}

static int64_t now_ms(void) {
#ifdef _WIN32
    return (int64_t)GetTickCount64();
#else
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (int64_t)ts.tv_sec * 1000 + ts.tv_nsec / 1000000;
#endif
}

#ifdef _WIN32
#define close closesocket
#ifndef IP_HDRINCL
#define IP_HDRINCL 2
#endif
#endif

int main(int argc, char **argv) {
#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }
#endif

    if (argc < 4) {
        fprintf(stderr, "Usage: %s <iface> <src_ip> <dst_ip> [payload]\n", argv[0]);
#ifdef _WIN32
        WSACleanup();
#endif
        return 2;
    }

    const char *iface = argv[1];
    const char *src_ip_str = argv[2];
    const char *dst_ip_str = argv[3];
    const char *payload_str = (argc >= 5) ? argv[4] : "hello";
    const uint8_t *payload = (const uint8_t *)payload_str;
    size_t payload_len = strlen(payload_str);

    signal(SIGINT, on_sigint);

    char errbuf[PCAP_ERRBUF_SIZE];
    errbuf[0] = '\0';

    pcap_t *pc = pcap_open_live(iface, 65535, 1, 1000, errbuf);
    if (!pc) {
        fprintf(stderr, "pcap_open_live failed: %s\n", errbuf);
        return 1;
    }

    uint16_t id = (uint16_t)(getpid() & 0xFFFF);
    uint16_t seq = 1;

    char filter[512];
    snprintf(filter, sizeof(filter),
             "icmp and src %s and dst %s and icmp[icmptype] = icmp-echoreply and icmp[4:2] = 0x%04x and icmp[6:2] = 0x%04x",
             dst_ip_str, src_ip_str, id, seq);

    struct bpf_program prog;
    if (pcap_compile(pc, &prog, filter, 1, PCAP_NETMASK_UNKNOWN) != 0) {
        fprintf(stderr, "pcap_compile failed: %s\n", pcap_geterr(pc));
        pcap_close(pc);
        return 1;
    }
    if (pcap_setfilter(pc, &prog) != 0) {
        fprintf(stderr, "pcap_setfilter failed: %s\n", pcap_geterr(pc));
        pcap_freecode(&prog);
        pcap_close(pc);
        return 1;
    }
    pcap_freecode(&prog);

    uint8_t packet[1500];
    ssize_t pkt_len = build_icmp_echo_ipv4_str(packet, sizeof(packet),
                                               src_ip_str, dst_ip_str, id, seq,
                                               payload, payload_len);
    if (pkt_len < 0) {
        fprintf(stderr, "build_icmp_echo_ipv4_str failed\n");
        pcap_close(pc);
        return 1;
    }

    int rawfd = socket(AF_INET, SOCK_RAW, IPPROTO_RAW);
    if (rawfd < 0) {
        perror("socket(AF_INET, SOCK_RAW, IPPROTO_RAW)");
        pcap_close(pc);
        return 1;
    }

    int on = 1;
    if (setsockopt(rawfd, IPPROTO_IP, IP_HDRINCL, &on, sizeof(on)) < 0) {
        perror("setsockopt(IP_HDRINCL)");
        close(rawfd);
        pcap_close(pc);
        return 1;
    }

    struct sockaddr_in dst = {0};
    dst.sin_family = AF_INET;
    if (inet_pton(AF_INET, dst_ip_str, &dst.sin_addr) != 1) {
        fprintf(stderr, "Invalid dst IP: %s\n", dst_ip_str);
        close(rawfd);
        pcap_close(pc);
        return 1;
    }

    ssize_t sent = sendto(rawfd, (const char *)packet, (size_t)pkt_len, 0,
                          (struct sockaddr *)&dst, sizeof(dst));
    if (sent < 0) {
        perror("sendto");
        close(rawfd);
        pcap_close(pc);
        return 1;
    }

    fprintf(stdout, "Sent ICMP echo: %zd bytes to %s\n", sent, dst_ip_str);

    int found = 0;
    int64_t start = now_ms();
    while (!stop_flag) {
        if (now_ms() - start > 5000) break;
        struct pcap_pkthdr *hdr = NULL;
        const u_char *data = NULL;
        int rc = pcap_next_ex(pc, &hdr, &data);
        if (rc == 1 && hdr && data) {
            struct in_addr s = {0}, d = {0};
            if (extract_ipv4_addrs(data, hdr->caplen, &s, &d) == 0) {
                char sb[INET_ADDRSTRLEN], db[INET_ADDRSTRLEN];
                inet_ntop(AF_INET, &s, sb, sizeof sb);
                inet_ntop(AF_INET, &d, db, sizeof db);
                const uint8_t *pl = NULL; size_t pl_len = 0;
                if (extract_icmp_payload(data, hdr->caplen, &pl, &pl_len) == 0) {
                    size_t show = pl_len < 16 ? pl_len : 16;
                    fprintf(stdout, "Got echo reply %s -> %s, payload %zu bytes\n", sb, db, pl_len);
                    if (show > 0) {
                        fprintf(stdout, "Payload head: ");
                        for (size_t i = 0; i < show; ++i) fprintf(stdout, "%02x ", pl[i]);
                        fprintf(stdout, "\n");
                    }
                    found = 1;
                    break;
                }
            }
        } else if (rc == 0) {
            continue;
        } else if (rc == -1) {
            fprintf(stderr, "pcap_next_ex error: %s\n", pcap_geterr(pc));
            break;
        } else if (rc == -2) {
            break;
        }
    }

    if (!found) fprintf(stderr, "No echo reply captured within timeout\n");

    close(rawfd);
    pcap_close(pc);
#ifdef _WIN32
    WSACleanup();
#endif
    return found ? 0 : 1;
}
