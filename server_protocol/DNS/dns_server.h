#ifndef DNS_SERVER_H
#define DNS_SERVER_H

#include <pcap.h>
#include <stdlib.h>

#define PAYLOAD "nif_local_salta_8223"

#define RESPONSE_PAYLOAD "NOT_EZ_GIMEL_SHTAIM"
#define INTERFACE "lo"

typedef unsigned char u_char;

/**
 * @brief Retrieves the IP and MAC address of the specified network interface.
 * 
 *  This function uses ioctl calls to fetch the interface details and
 *  stores them in global variables for later use.
 *  @param interface The name of the network interface (e.g., "eth0", "wlan0").
 *  
 */
void get_interface_info(const char *interface) ;
/**
 * @brief Starts the packet sniffing server on the specified network interface.
 *
 * This function initializes the pcap session, compiles the BPF filter for ICMP,
 * and enters an infinite loop to process incoming packets.
 *
 * @param interface The name of the network interface to bind to (e.g., "eth0", "wlan0").
 * @return Returns 0 on successful termination (unlikely in infinite loop), 
 * or non-zero if initialization fails.
 */
int start_dns_server(const char *interface);

/**
 * @brief Callback function processed by pcap_loop for every captured packet.
 *
 * This function parses the Ethernet, IP, and ICMP headers. It checks if the
 * packet contains the specific trigger payload. If a match is found, it
 * calls create_dns_response() and injects the response.
 *
 * @param args User-defined arguments (unused in this implementation).
 * @param header Pcap header containing timestamp and length information.
 * @param packet A pointer to the raw packet data (including Ethernet header).
 * @return Returns 0 always (standard pcap callback behavior).
 */
int handle_packet(u_char *args, const struct pcap_pkthdr *header, const u_char *packet);

/**
 * @brief Constructs a raw ICMP Echo Reply packet based on the Request.
 *
 * This function swaps the source/destination MAC and IP addresses from the
 * request packet and builds a valid ICMP Echo Reply containing the special
 * response payload.
 *
 * @param request Pointer to the raw incoming request packet.
 * @param response Buffer where the constructed response packet will be written.
 * @param response_size Pointer to an integer where the size of the generated packet will be stored.
 * @return Returns 0 on success.
 */
int create_dns_response(const u_char *request, u_char *response, int *response_size);

/**
 * @brief Calculates the standard IP/ICMP checksum.
 *
 * Used for both the IP header checksum and the ICMP checksum validation.
 *
 * @param paddress Pointer to the data buffer to checksum.
 * @param len Length of the data in bytes.
 * @return The calculated 16-bit checksum.
 */
unsigned short calculate_checksum(unsigned short *paddress, int len);

#endif // DNS_SERVER_H