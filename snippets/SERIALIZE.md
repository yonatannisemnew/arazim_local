# Cross-Platform Build Instructions

The code is cross-platform compatible and can be built on **Linux**, **macOS**, and **Windows**.

---

## macOS

### Prerequisites
- Xcode Command Line Tools: `xcode-select --install`
- libpcap (included with macOS)

### Building
```bash
clang -Wall -Wextra -std=c11 test_ping.c serialize.c -lpcap -o test_ping
# or
gcc -Wall -Wextra -std=c11 test_ping.c serialize.c -lpcap -o test_ping
```

### Running
```bash
# Requires root for raw sockets
sudo ./test_ping en0 192.168.1.100 8.8.8.8 "hello"
```

Use `ifconfig` to find your network interface name (usually `en0` for Wi-Fi).

---

## Linux

### Prerequisites
```bash
sudo apt install libpcap-dev  # Debian/Ubuntu
sudo yum install libpcap-devel  # RHEL/CentOS
```

### Building
```bash
gcc -Wall -Wextra -std=c11 test_ping.c serialize.c -lpcap -o test_ping
```

### Running
```bash
sudo ./test_ping eth0 192.168.1.100 8.8.8.8 "hello"
```

---

## Windows

1. **WinPcap or Npcap**: Install [Npcap](https://npcap.com/) (recommended) or WinPcap
2. **Compiler**: Visual Studio (MSVC) or MinGW-w64 with GCC
3. **WinPcap SDK**: Download the [WinPcap Developer's Pack](https://www.winpcap.org/devel.htm) or use Npcap SDK

## Building with MSVC

```cmd
cl /W4 /std:c11 serialize.c test_ping.c /I"C:\path\to\WpdPack\Include" ^
   /link /LIBPATH:"C:\path\to\WpdPack\Lib\x64" wpcap.lib ws2_32.lib
```

## Building with MinGW

```bash
gcc -Wall -Wextra -std=c11 test_ping.c serialize.c -lpcap -lws2_32 -o test_ping.exe
```

## Platform Differences

### macOS (BSD-based):
- Uses BSD `struct ip` instead of Linux `struct iphdr`
- Field names mapped via macros (e.g., `ihl` → `ip_hl`, `saddr` → `ip_src.s_addr`)
- Requires `netinet/in_systm.h` before `netinet/ip_icmp.h`
- libpcap included with system
- Raw sockets require root privileges

### Linux:
- Uses `struct iphdr` from `netinet/ip.h`
- Standard POSIX socket headers
- Uses `clock_gettime(CLOCK_MONOTONIC)` for timing
- Requires `CAP_NET_RAW` capability or root

### Windows-specific:
- Uses `Winsock2` (`winsock2.h`, `ws2tcpip.h`)
- Requires `WSAStartup()` / `WSACleanup()`
- Uses `closesocket()` instead of `close()`
- Uses `GetTickCount64()` for timing
- Raw sockets require Administrator privileges
- IP header structures defined manually

### Linux/POSIX:
- Uses standard POSIX socket headers
- Uses `clock_gettime(CLOCK_MONOTONIC)` for timing
- Requires `CAP_NET_RAW` capability or root

## Running on Windows

```cmd
# Run as Administrator
test_ping.exe \Device\NPF_{GUID} 192.168.1.100 8.8.8.8 "hello"
```

Use `getmac /v` or WinPcap/Npcap tools to find the correct device name.

## Cross-Platform Code

All platform-specific code is wrapped in `#ifdef` blocks:
- `#ifdef _WIN32` for Windows-specific code
- `#ifdef __APPLE__` for macOS-specific code
- Linux is the default fallback

The same source files compile on **Linux**, **macOS**, and **Windows** without modification.
