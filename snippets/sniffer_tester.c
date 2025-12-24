// sniffer_tester.c
// Simple tester that starts two sniffers:
//  - sniffer 1: BPF "tcp", prints "sniffer 1 captured tcp from g2"
//  - sniffer 2: BPF "udp", prints "sniffer 2 captured udp from g2"
// Runs until SIGINT/SIGTERM, then stops sniffers.

#include "sniff.h"

#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

static volatile sig_atomic_t running = 1;

static void on_signal(int sig) {
    (void)sig;
    running = 0;
}

static const char *pick_device(void) {
    const char *env = getenv("SNIFFER_DEV");
    if (env && *env) {
        return env;
    }
    return "wlo1"; // default; override with SNIFFER_DEV if needed
}

static int handler_tcp(const struct pcap_pkthdr *hdr, const u_char *bytes) {
    (void)hdr;
    (void)bytes;
    puts("sniffer 1 captured tcp from g2");
    return 0;
}

static int handler_udp(const struct pcap_pkthdr *hdr, const u_char *bytes) {
    (void)hdr;
    (void)bytes;
    puts("sniffer 2 captured udp from g2");
    return 0;
}

int main(void) {
    const char *device = pick_device();

    signal(SIGINT, on_signal);
    signal(SIGTERM, on_signal);

    printf("Starting sniffer 1 on %s with BPF 'tcp'\n", device);
    int rc = start_sniffer(device, handler_tcp, "tcp");
    if (rc != 0) {
        fprintf(stderr, "Failed to start sniffer 1 on %s: %s\n", device, strerror(rc));
        return 1;
    }

    printf("Starting sniffer 2 on %s with BPF 'udp'\n", device);
    rc = start_sniffer(device, handler_udp, "udp");
    if (rc != 0) {
        fprintf(stderr, "Failed to start sniffer 2 on %s: %s\n", device, strerror(rc));
        stop_sniffer();
        return 1;
    }

    printf("Sniffers armed. Waiting for SSID 'Building_G2'...\n");
    printf("Override device with env var SNIFFER_DEV (default: wlo0)\n");
    while (running) {
        sleep(1);
    }

    printf("\nStopping sniffers...\n");
    stop_sniffer();
    printf("Stopped. Goodbye.\n");
    return 0;
}


