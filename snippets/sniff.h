// sniff.h
// Background sniffer that only activates when connected to the
// Wi‑Fi network "Building_G2". Uses libpcap to apply the provided BPF.

#ifndef SNIFF_H
#define SNIFF_H

#if defined(_WIN32)
#include <pcap.h>
#else
#include <pcap/pcap.h>
#endif

#ifdef __cplusplus
extern "C" {
#endif

// Signature for user-provided packet handlers.
// Return 0 on success; non-zero signals an error but does not stop capture.
typedef int (*packet_handler)(const struct pcap_pkthdr *hdr, const u_char *bytes);

// Start the background sniffer.
// device  : network interface name (e.g., "wlan0")
// handler : callback invoked for every packet that matches the BPF
// bpf     : tcpdump-style filter string
// Returns 0 on success, non-zero on setup error.
// Non-blocking: spawns internal threads and returns immediately.
int start_sniffer(const char *device, packet_handler handler, const char *bpf);

// Stop the sniffer and release resources. Safe to call more than once.
void stop_sniffer(void);

#ifdef __cplusplus
}
#endif
#endif // SNIFF_H
