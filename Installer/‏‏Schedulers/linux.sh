#!/bin/bash

# ===============================
# Require root (admin)
# ===============================
if [[ "$EUID" -ne 0 ]]; then
    echo "[ERROR] This script must be run as root."
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
# Cron identifier
# ===============================
CRON_TAG="# RUN_PYTHON_$(basename "$PY_FILE")_${INTERVAL}MIN"

# ===============================
# Remove existing job (idempotent)
# ===============================
crontab -l 2>/dev/null | grep -v "$CRON_TAG" | crontab -

# ===============================
# Create cron job
# ===============================
(
    crontab -l 2>/dev/null
    echo "*/$INTERVAL * * * * $PYTHON_CMD $PY_FILE $CRON_TAG"
) | crontab -

if [[ $? -ne 0 ]]; then
    echo "[ERROR] Failed to install cron job"
    exit 1
fi

echo "[SUCCESS] Cron job installed"
echo "  Python   : $PYTHON_CMD"
echo "  Script   : $PY_FILE"
echo "  Interval : Every $INTERVAL minutes"

exit 0
