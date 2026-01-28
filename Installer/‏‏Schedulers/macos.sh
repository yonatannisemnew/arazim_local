#!/bin/bash

# ===============================
# Require root
# ===============================
if [[ "$EUID" -ne 0 ]]; then
    echo "[ERROR] This script must be run as root (sudo)."
    exit 1
fi

# ===============================
# Validate arguments
# ===============================
if [[ -z "$1" || -z "$2" ]]; then
    echo "[ERROR] Missing arguments"
    echo "Usage: $0 <script.py> <interval_minutes>"
    exit 1
fi

PY_FILE="$(realpath "$1")"
INTERVAL="$2"

if [[ ! -f "$PY_FILE" ]]; then
    echo "[ERROR] Python file not found: $PY_FILE"
    exit 1
fi

if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
    echo "[ERROR] Interval must be a number (minutes)"
    exit 1
fi

# ===============================
# Detect python / python3
# ===============================
if command -v python >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python)"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD="$(command -v python3)"
else
    echo "[ERROR] python or python3 not found"
    exit 1
fi

# ===============================
# LaunchDaemon identifiers
# ===============================
SCRIPT_NAME="$(basename "$PY_FILE" .py)"
LABEL="com.autorun.${SCRIPT_NAME}.${INTERVAL}min"
PLIST="/Library/LaunchDaemons/${LABEL}.plist"

# ===============================
# Unload existing job (if any)
# ===============================
launchctl unload "$PLIST" 2>/dev/null

# ===============================
# Create plist
# ===============================
cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>${LABEL}</string>

    <key>ProgramArguments</key>
    <array>
        <string>${PYTHON_CMD}</string>
        <string>${PY_FILE}</string>
    </array>

    <key>StartInterval</key>
    <integer>$((INTERVAL * 60))</integer>

    <key>RunAtLoad</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/var/log/${LABEL}.out.log</string>

    <key>StandardErrorPath</key>
    <string>/var/log/${LABEL}.err.log</string>
</dict>
</plist>
EOF

# ===============================
# Permissions (REQUIRED by launchd)
# ===============================
chmod 644 "$PLIST"
chown root:wheel "$PLIST"

# ===============================
# Load daemon
# ===============================
launchctl load "$PLIST"
if [[ $? -ne 0 ]]; then
    echo "[ERROR] Failed to load LaunchDaemon"
    exit 1
fi

echo "[SUCCESS] LaunchDaemon installed"
echo "  Label    : $LABEL"
echo "  Python   : $PYTHON_CMD"
echo "  Script   : $PY_FILE"
echo "  Interval : Every $INTERVAL minutes"
echo "  Logs     : /var/log/${LABEL}.out.log"

exit 0
