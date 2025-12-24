// Helpers for parsing and building IPv4/ICMP (ping) packets
#ifndef SERIALIZE_H
#define SERIALIZE_H

#include <stddef.h>
#include <stdint.h>

#ifdef _WIN32
#include <winsock2.h>
#include <ws2tcpip.h>
#ifndef ssize_t
typedef intptr_t ssize_t;
#endif
#else
#include <sys/types.h>
#include <arpa/inet.h>
#include <netinet/in.h>
#endif

// Extract source and destination IPv4 addresses from a raw packet buffer.
// Supports Ethernet frames (with optional 802.1Q VLAN) and raw IPv4 packets.
// Returns 0 on success and fills src/dst. Returns -1 on failure.
int extract_ipv4_addrs(const uint8_t *packet, size_t caplen,
					   struct in_addr *src, struct in_addr *dst);

// For an IPv4 ICMP Echo (ping) packet, extract a pointer and length to the
// data/payload that follows the ICMP header. Returns 0 on success,
// and sets *payload/*payload_len. Returns -1 on failure or non-ICMP-Echo.
int extract_icmp_payload(const uint8_t *packet, size_t caplen,
						 const uint8_t **payload, size_t *payload_len);

// Build a minimal IPv4 ICMP Echo Request packet into out_buf.
// - src, dst: IPv4 addresses (network byte order inside struct in_addr)
// - id, seq: ICMP Echo identifier and sequence
// - data/data_len: payload to include after the ICMP header
// Returns the total number of bytes written on success, or -1 on error.
// The produced packet contains only IPv4+ICMP, no Ethernet header.
ssize_t build_icmp_echo_ipv4(uint8_t *out_buf, size_t out_buf_len,
							 struct in_addr src, struct in_addr dst,
							 uint16_t id, uint16_t seq,
							 const uint8_t *data, size_t data_len);

// Convenience wrapper taking dotted-quad IPv4 strings for src/dst.
// Returns bytes written on success, -1 on error (e.g., bad IP string).
ssize_t build_icmp_echo_ipv4_str(uint8_t *out_buf, size_t out_buf_len,
								 const char *src_ip_str, const char *dst_ip_str,
								 uint16_t id, uint16_t seq,
								 const uint8_t *data, size_t data_len);

#endif // SERIALIZE_H

