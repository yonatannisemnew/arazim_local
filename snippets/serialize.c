#include "serialize.h"

#include <errno.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>

// Windows equivalents for Ethernet constants
#define ETHERTYPE_IP 0x0800
#ifndef IPPROTO_ICMP
#define IPPROTO_ICMP 1
#endif

// Ethernet header for Windows
struct ether_header {
    uint8_t  ether_dhost[6];
    uint8_t  ether_shost[6];
    uint16_t ether_type;
};

// IP header for Windows (from RFC 791)
struct iphdr {
    uint8_t  ihl:4;
    uint8_t  version:4;
    uint8_t  tos;
    uint16_t tot_len;
    uint16_t id;
    uint16_t frag_off;
    uint8_t  ttl;
    uint8_t  protocol;
    uint16_t check;
    uint32_t saddr;
    uint32_t daddr;
};

// ICMP header for Windows
struct icmphdr {
    uint8_t  type;
    uint8_t  code;
    uint16_t checksum;
    union {
        struct {
            uint16_t id;
            uint16_t sequence;
        } echo;
    } un;
};

#define ICMP_ECHO 8
#define ICMP_ECHOREPLY 0

#else
#include <arpa/inet.h>
#ifdef __APPLE__
#include <net/if.h>
#include <net/ethernet.h>
#define iphdr ip
#define ihl ip_hl
#define version ip_v
#define tos ip_tos
#define tot_len ip_len
#define id ip_id
#define frag_off ip_off
#define ttl ip_ttl
#define protocol ip_p
#define check ip_sum
#define saddr ip_src.s_addr
#define daddr ip_dst.s_addr
#else
#include <net/ethernet.h>
#endif
#include <netinet/ip.h>
#include <netinet/ip_icmp.h>
#endif

// Compute Internet checksum (RFC 1071) over a buffer
static uint16_t checksum16(const void *data, size_t len) {
	uint32_t sum = 0;
	const uint16_t *ptr = (const uint16_t *)data;

	while (len > 1) {
		sum += *ptr++;
		len -= 2;
	}
	if (len == 1) {
		uint16_t last = 0;
		*(uint8_t *)&last = *(const uint8_t *)ptr;
		sum += last;
	}

	// Fold 32-bit sum to 16 bits
	while (sum >> 16) {
		sum = (sum & 0xFFFF) + (sum >> 16);
	}
	return (uint16_t)(~sum);
}

// Locate IPv4 header inside a packet. Supports:
// - Ethernet II frames (with up to two VLAN tags)
// - Raw IPv4 packets (no L2 header)
// On success returns pointer to IPv4 header and sets *ip_len with remaining bytes.
static const struct iphdr *locate_ipv4(const uint8_t *packet, size_t caplen, size_t *ip_len) {
	if (!packet || caplen == 0) return NULL;

	// If the first nibble is 4, treat as IPv4 without L2
	if (caplen >= 1 && ((packet[0] >> 4) == 4)) {
		if (ip_len) *ip_len = caplen;
		return (const struct iphdr *)packet;
	}

	// Must have Ethernet header
	if (caplen < sizeof(struct ether_header)) return NULL;

	size_t offset = 0;
	const struct ether_header *eth = (const struct ether_header *)packet;
	uint16_t eth_type = ntohs(eth->ether_type);
	offset += sizeof(struct ether_header);

	// Handle up to two VLAN tags (802.1Q 0x8100, 0x88a8)
	for (int i = 0; i < 2; ++i) {
		if (eth_type == 0x8100 || eth_type == 0x88A8) {
			if (caplen < offset + 4) return NULL; // VLAN tag present but truncated
			// VLAN tag is 4 bytes, next two bytes are encapsulated EtherType
			eth_type = ntohs(*(const uint16_t *)(packet + offset + 2));
			offset += 4;
		} else {
			break;
		}
	}

	if (eth_type != ETHERTYPE_IP) return NULL; // Not IPv4
	if (caplen < offset + sizeof(struct iphdr)) return NULL;

	const struct iphdr *ip4 = (const struct iphdr *)(packet + offset);
	if (ip_len) *ip_len = caplen - offset;
	return ip4;
}

int extract_ipv4_addrs(const uint8_t *packet, size_t caplen,
					   struct in_addr *src, struct in_addr *dst) {
	if (!packet || !src || !dst) return -1;
	size_t ip_avail = 0;
	const struct iphdr *ip4 = locate_ipv4(packet, caplen, &ip_avail);
	if (!ip4) return -1;

	// Ensure we have full IP header according to IHL
	size_t ihl = (size_t)ip4->ihl * 4u;
	if (ihl < sizeof(struct iphdr) || ip_avail < ihl) return -1;
	src->s_addr = ip4->saddr;
	dst->s_addr = ip4->daddr;
	return 0;
}

int extract_icmp_payload(const uint8_t *packet, size_t caplen,
						 const uint8_t **payload, size_t *payload_len) {
	if (!packet || !payload || !payload_len) return -1;
	size_t ip_avail = 0;
	const struct iphdr *ip4 = locate_ipv4(packet, caplen, &ip_avail);
	if (!ip4) return -1;

	size_t ihl = (size_t)ip4->ihl * 4u;
	if (ihl < sizeof(struct iphdr) || ip_avail < ihl) return -1;

	if (ip4->protocol != IPPROTO_ICMP) return -1;

	const uint8_t *l4 = (const uint8_t *)ip4 + ihl;
	size_t l4_len = ip_avail - ihl;
	if (l4_len < sizeof(struct icmphdr)) return -1;

	const struct icmphdr *icmp = (const struct icmphdr *)l4;
	if (!(icmp->type == ICMP_ECHO || icmp->type == ICMP_ECHOREPLY)) return -1;

	size_t hdr_len = sizeof(struct icmphdr);
	if (l4_len < hdr_len) return -1;
	*payload = l4 + hdr_len;
	*payload_len = l4_len - hdr_len;
	return 0;
}

ssize_t build_icmp_echo_ipv4(uint8_t *out_buf, size_t out_buf_len,
							 struct in_addr src, struct in_addr dst,
							 uint16_t id, uint16_t seq,
							 const uint8_t *data, size_t data_len) {
	if (!out_buf) return -1;
	if (data_len > 0 && !data) return -1;

	const size_t ip_hdr_len = sizeof(struct iphdr);
	const size_t icmp_hdr_len = sizeof(struct icmphdr);
	const size_t total_len = ip_hdr_len + icmp_hdr_len + data_len;
	if (out_buf_len < total_len) return -1;

	// Zero the buffer to have predictable content
	memset(out_buf, 0, total_len);

	// Build IP header
	struct iphdr *ip4 = (struct iphdr *)out_buf;
	ip4->version = 4;
	ip4->ihl = (uint8_t)(ip_hdr_len / 4);
	ip4->tos = 0;
	ip4->tot_len = htons((uint16_t)total_len);
	ip4->id = htons(0);
	ip4->frag_off = htons(0);
	ip4->ttl = 64;
	ip4->protocol = IPPROTO_ICMP;
	ip4->saddr = src.s_addr;
	ip4->daddr = dst.s_addr;
	ip4->check = 0;
	ip4->check = checksum16(ip4, ip_hdr_len);

	// Build ICMP header + payload
	struct icmphdr *icmp = (struct icmphdr *)(out_buf + ip_hdr_len);
	icmp->type = ICMP_ECHO;
	icmp->code = 0;
	icmp->un.echo.id = htons(id);
	icmp->un.echo.sequence = htons(seq);
	icmp->checksum = 0;

	if (data_len > 0) memcpy((uint8_t *)icmp + icmp_hdr_len, data, data_len);

	icmp->checksum = checksum16(icmp, icmp_hdr_len + data_len);

	return (ssize_t)total_len;
}

ssize_t build_icmp_echo_ipv4_str(uint8_t *out_buf, size_t out_buf_len,
								 const char *src_ip_str, const char *dst_ip_str,
								 uint16_t id, uint16_t seq,
								 const uint8_t *data, size_t data_len) {
	if (!src_ip_str || !dst_ip_str) return -1;
	struct in_addr src = {0}, dst = {0};
	if (inet_pton(AF_INET, src_ip_str, &src) != 1) return -1;
	if (inet_pton(AF_INET, dst_ip_str, &dst) != 1) return -1;
	return build_icmp_echo_ipv4(out_buf, out_buf_len, src, dst, id, seq, data, data_len);
}

