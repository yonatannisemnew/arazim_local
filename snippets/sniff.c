// sniff.c
// Background sniffer that only activates when connected to "Building_G2".
// Requires libpcap and pthreads.

#include "sniff.h"

#include <errno.h>
#include <signal.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#if defined(_WIN32)
#include <windows.h>
#include <process.h>
#define SNIFF_THREAD HANDLE
#define SNIFF_THREAD_RET unsigned __stdcall
#define SNIFF_THREAD_CALL __stdcall
#define SNIFF_THREAD_CREATE(thr, fn, arg) \
    ((*(thr) = (HANDLE)_beginthreadex(NULL, 0, fn, arg, 0, NULL)) ? 0 : errno)
#define SNIFF_THREAD_JOIN(thr)              \
    do                                      \
    {                                       \
        WaitForSingleObject(thr, INFINITE); \
        CloseHandle(thr);                   \
    } while (0)
#define SNIFF_THREAD_DETACH(thr) CloseHandle(thr)
#define SNIFF_MUTEX CRITICAL_SECTION
#define SNIFF_MUTEX_INIT(m) InitializeCriticalSection(m)
#define SNIFF_MUTEX_LOCK(m) EnterCriticalSection(m)
#define SNIFF_MUTEX_UNLOCK(m) LeaveCriticalSection(m)
#define SNIFF_MUTEX_DESTROY(m) DeleteCriticalSection(m)
static void sleep_seconds(int s) { Sleep(s * 1000); }
#define popen _popen
#define pclose _pclose
#else
#include <pthread.h>
#include <unistd.h>
#define SNIFF_THREAD pthread_t
#define SNIFF_THREAD_RET void *
#define SNIFF_THREAD_CALL
#define SNIFF_THREAD_CREATE(thr, fn, arg) pthread_create(thr, NULL, fn, arg)
#define SNIFF_THREAD_JOIN(thr) pthread_join(thr, NULL)
#define SNIFF_THREAD_DETACH(thr) pthread_detach(thr)
#define SNIFF_MUTEX pthread_mutex_t
#define SNIFF_MUTEX_INIT(m) pthread_mutex_init(m, NULL)
#define SNIFF_MUTEX_LOCK(m) pthread_mutex_lock(m)
#define SNIFF_MUTEX_UNLOCK(m) pthread_mutex_unlock(m)
#define SNIFF_MUTEX_DESTROY(m) pthread_mutex_destroy(m)
static void sleep_seconds(int s) { sleep((unsigned int)s); }
#endif

#define TARGET_SSID "Building_G2"
#define SSID_CHECK_INTERVAL_SEC 5
#define PCAP_SNAPLEN 65535
#define PCAP_TIMEOUT_MS 1000

typedef struct
{
    char device[128];
    char bpf[256];
    packet_handler handler;
} sniffer_config;

typedef struct sniffer_state
{
    sniffer_config cfg;
    SNIFF_THREAD monitor_thread;
    SNIFF_THREAD capture_thread;
    bool monitor_running;
    bool capture_running;
    pcap_t *handle;
    SNIFF_MUTEX lock;
    struct sniffer_state *next;
} sniffer_state;

static sniffer_state *g_head = NULL;
static SNIFF_MUTEX g_list_lock;
static bool g_list_lock_inited = false;

static void ensure_list_lock(void)
{
    if (!g_list_lock_inited)
    {
        SNIFF_MUTEX_INIT(&g_list_lock);
        g_list_lock_inited = true;
    }
}

static bool read_first_line(const char *cmd, char *out, size_t len)
{
    FILE *fp = popen(cmd, "r");
    if (!fp)
    {
        return false;
    }
    if (!fgets(out, (int)len, fp))
    {
        pclose(fp);
        return false;
    }
    pclose(fp);
    out[strcspn(out, "\r\n")] = '\0';
    return out[0] != '\0';
}

static bool get_current_ssid(char *ssid_out, size_t len)
{
#ifdef __APPLE__
    const char *cmds[] = {
        "networksetup -getairportnetwork en0 2>/dev/null | sed 's/^Current Wi-Fi Network: //'",
        "/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport -I 2>/dev/null | awk -F': ' '/ SSID/ {print $2; exit}'",
    };
    for (size_t i = 0; i < sizeof(cmds) / sizeof(cmds[0]); ++i)
    {
        if (read_first_line(cmds[i], ssid_out, len))
        {
            return true;
        }
    }
#else
    const char *env_cmd = getenv("SNIFFER_SSID_CMD");
    if (env_cmd && read_first_line(env_cmd, ssid_out, len))
    {
        return true;
    }
    // Try iwgetid -r first.
    if (read_first_line("iwgetid -r 2>/dev/null", ssid_out, len))
    {
        return true;
    }
    // Fallback to nmcli if available.
    if (read_first_line("nmcli -t -f ACTIVE,SSID dev wifi 2>/dev/null | grep '^yes' | cut -d: -f2", ssid_out, len))
    {
        return true;
    }
#endif
    return false;
}

static bool on_target_network(void)
{
    char ssid[128] = {0};
    if (!get_current_ssid(ssid, sizeof(ssid)))
    {
        return false;
    }
    return strcmp(ssid, TARGET_SSID) == 0;
}

static void packet_trampoline(u_char *user, const struct pcap_pkthdr *hdr, const u_char *bytes)
{
    sniffer_state *state = (sniffer_state *)user;
    if (state->cfg.handler)
    {
        state->cfg.handler(hdr, bytes);
    }
}

static void stop_capture_locked(sniffer_state *state)
{
    if (!state->capture_running)
    {
        return;
    }
    if (state->handle)
    {
        pcap_breakloop(state->handle);
    }
}

static SNIFF_THREAD_RET SNIFF_THREAD_CALL capture_thread_fn(void *arg)
{
    sniffer_state *state = (sniffer_state *)arg;

    char errbuf[PCAP_ERRBUF_SIZE];
    state->handle = pcap_open_live(state->cfg.device, PCAP_SNAPLEN, 1, PCAP_TIMEOUT_MS, errbuf);
    if (!state->handle)
    {
        fprintf(stderr, "pcap_open_live failed: %s\n", errbuf);
        goto done;
    }

    struct bpf_program fp;
    if (pcap_compile(state->handle, &fp, state->cfg.bpf, 1, PCAP_NETMASK_UNKNOWN) == -1)
    {
        fprintf(stderr, "pcap_compile failed: %s\n", pcap_geterr(state->handle));
        goto done;
    }

    if (pcap_setfilter(state->handle, &fp) == -1)
    {
        fprintf(stderr, "pcap_setfilter failed: %s\n", pcap_geterr(state->handle));
        pcap_freecode(&fp);
        goto done;
    }
    pcap_freecode(&fp);

    state->capture_running = true;
    pcap_loop(state->handle, -1, packet_trampoline, (u_char *)state);

done:
    if (state->handle)
    {
        pcap_close(state->handle);
        state->handle = NULL;
    }
    state->capture_running = false;
    return 0;
}

static SNIFF_THREAD_RET SNIFF_THREAD_CALL monitor_thread_fn(void *arg)
{
    sniffer_state *state = (sniffer_state *)arg;
    while (state->monitor_running)
    {
        bool on_target = on_target_network();

        pthread_mutex_lock(&state->lock);
        bool already_running = state->capture_running;
        pthread_mutex_unlock(&state->lock);

        if (on_target && !already_running)
        {
            SNIFF_MUTEX_LOCK(&state->lock);
            if (!state->capture_running)
            {
                if (SNIFF_THREAD_CREATE(&state->capture_thread, capture_thread_fn, state) != 0)
                {
                    fprintf(stderr, "Failed to start capture thread\n");
                }
            }
            SNIFF_MUTEX_UNLOCK(&state->lock);
        }
        else if (!on_target && already_running)
        {
            SNIFF_MUTEX_LOCK(&state->lock);
            stop_capture_locked(state);
            SNIFF_MUTEX_UNLOCK(&state->lock);
        }

        sleep_seconds(SSID_CHECK_INTERVAL_SEC);
    }
    return 0;
}

int start_sniffer(const char *device, packet_handler handler, const char *bpf)
{
    if (!device || !handler || !bpf)
    {
        return EINVAL;
    }

    ensure_list_lock();

    sniffer_state *state = calloc(1, sizeof(sniffer_state));
    if (!state)
    {
        return ENOMEM;
    }
    SNIFF_MUTEX_INIT(&state->lock);

    snprintf(state->cfg.device, sizeof(state->cfg.device), "%s", device);
    snprintf(state->cfg.bpf, sizeof(state->cfg.bpf), "%s", bpf);
    state->cfg.handler = handler;
    state->monitor_running = true;

    int rc = SNIFF_THREAD_CREATE(&state->monitor_thread, monitor_thread_fn, state);
    if (rc != 0)
    {
        state->monitor_running = false;
        free(state);
        return rc;
    }

    // Add to global list.
    SNIFF_MUTEX_LOCK(&g_list_lock);
    state->next = g_head;
    g_head = state;
    SNIFF_MUTEX_UNLOCK(&g_list_lock);

    return 0;
}

void stop_sniffer(void)
{
    ensure_list_lock();
    SNIFF_MUTEX_LOCK(&g_list_lock);
    sniffer_state *state = g_head;
    g_head = NULL;
    SNIFF_MUTEX_UNLOCK(&g_list_lock);

    while (state)
    {
        sniffer_state *next = state->next;
        state->monitor_running = false;

        SNIFF_MUTEX_LOCK(&state->lock);
        stop_capture_locked(state);
        SNIFF_MUTEX_UNLOCK(&state->lock);

        if (state->capture_running)
        {
            SNIFF_THREAD_JOIN(state->capture_thread);
        }
        SNIFF_THREAD_JOIN(state->monitor_thread);

        SNIFF_MUTEX_DESTROY(&state->lock);
        free(state);
        state = next;
    }
}

// Example handler: prints packet length. Replace or remove as needed.
static int default_handler(const struct pcap_pkthdr *hdr, const u_char *bytes)
{
    (void)bytes;
    printf("Packet captured: %u bytes\n", hdr->caplen);
    return 0;
}

// Optional demo main for manual testing.
#ifdef SNIFF_STANDALONE
int main(int argc, char **argv)
{
    if (argc != 4)
    {
        fprintf(stderr, "Usage: %s <device> <dummy_handler> <bpf>\n", argv[0]);
        fprintf(stderr, "Example: %s wlan0 print \"tcp port 80\"\n", argv[0]);
        return 1;
    }

    const char *device = argv[1];
    (void)argv[2]; // Placeholder; using default_handler in this demo.
    const char *bpf = argv[3];

    int rc = start_sniffer(device, default_handler, bpf);
    if (rc != 0)
    {
        fprintf(stderr, "Failed to start sniffer: %s\n", strerror(rc));
        return 1;
    }

    // Keep process alive.
    while (1)
    {
        sleep(60);
    }
    return 0;
}
#endif
