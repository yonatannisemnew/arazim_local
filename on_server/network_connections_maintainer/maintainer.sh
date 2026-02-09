#!/bin/bash

# Variables
BUILT_IN_NIC="wlp0s20f3"
TP_LINK_NIC="wlx14cc201b8fcb"

G2_SSID="Building_G2"
G2_PASS="123456789"

PRINTER_SSID="DIRECT-D7-HP DeskJet 5200 series"
PRINTER_PASS="12345678"

SLEEP_TIME=3

echo "Monitoring connections... (Press Ctrl+C to stop)"

while true; do
    # 1. Global Wi-Fi Check: Force radio on if GUI turned it off
    if [ "$(nmcli radio wifi)" = "disabled" ]; then
        echo "$(date): WiFi radio was OFF. Enabling..."
        nmcli radio wifi on
        sleep 2
    fi

    # 2. Check Built-in NIC (G2 Network)
    # We fetch the current connection name associated with the device
    CURRENT_G2=$(nmcli -t -f DEVICE,CONNECTION device | grep "^$BUILT_IN_NIC:" | cut -d: -f2)
    
    # Fuzzy match: If the current connection name does NOT contain our target SSID
    if [[ "$CURRENT_G2" != *"$G2_SSID"* ]]; then
        echo "$(date): $BUILT_IN_NIC is not on $G2_SSID (Current: $CURRENT_G2). Connecting..."
        nmcli device wifi connect "$G2_SSID" password "$G2_PASS" ifname "$BUILT_IN_NIC"
        nmcli connection modify "$G2_SSID" ipv4.route-metric 50
    fi

    # 3. Check TP-Link NIC (Printer)
    CURRENT_PRINTER=$(nmcli -t -f DEVICE,CONNECTION device | grep "^$TP_LINK_NIC:" | cut -d: -f2)

    # Fuzzy match for the printer
    if [[ "$CURRENT_PRINTER" != *"$PRINTER_SSID"* ]]; then
        echo "$(date): $TP_LINK_NIC is not on $PRINTER_SSID (Current: $CURRENT_PRINTER). Connecting..."
        # We attempt connection. If it fails due to existing profiles, we try to force 'up'
        nmcli device wifi connect "$PRINTER_SSID" password "$PRINTER_PASS" ifname "$TP_LINK_NIC" || nmcli connection up "$PRINTER_SSID"
        
        # Ensure printer doesn't steal the internet gateway
        nmcli connection modify "$PRINTER_SSID" ipv4.route-metric 500
    fi

    sleep $SLEEP_TIME
done