#!/bin/bash

# ==============================================================================
# Script Name: schedule_macos.sh
# Description: Adds a Python script to the user's crontab to run every T minutes.
# Usage: ./schedule_macos.sh
# ==============================================================================


SCRIPT_PATH="/Library/Application Support/Arazim Local/manager/manager.py"
INTERVAL="15"

# Check if the Python file exists
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Error: File '$SCRIPT_PATH' not found."
    exit 1
fi

# Check if interval is a number
if ! [[ "$INTERVAL" =~ ^[0-9]+$ ]]; then
    echo "Error: Interval must be an integer (e.g., 15)."
    exit 1
fi

# Prepare Paths
# Cron requires absolute paths. We use 'realpath' to resolve the full location.
FULL_SCRIPT_PATH=$(realpath "$SCRIPT_PATH")
SCRIPT_DIR=$(dirname "$FULL_SCRIPT_PATH")
SCRIPT_NAME=$(basename "$FULL_SCRIPT_PATH")
LOG_FILE="${SCRIPT_DIR}/${SCRIPT_NAME%.*}.log"
PYTHON_BIN=$(which python3)

if [ -z "$PYTHON_BIN" ]; then
    echo "Error: Could not find 'python3'. Is it installed?"
    exit 1
fi

# Construct the Cron Command
CRON_CMD="*/$INTERVAL * * * * cd $SCRIPT_DIR && $PYTHON_BIN $FULL_SCRIPT_PATH >> $LOG_FILE 2>&1"

# Add to Crontab safely
# We first list existing cron jobs. If the command is already there, we skip it.
CURRENT_CRON=$(crontab -l 2>/dev/null)

if echo "$CURRENT_CRON" | grep -Fq "$FULL_SCRIPT_PATH"; then
    echo "Notice: This script is already scheduled in crontab. Skipping."
else
    # Append the new job to the existing list and save it
    (echo "$CURRENT_CRON"; echo "$CRON_CMD") | crontab -
    
    echo "Success! Added the following job to crontab:"
    echo "---------------------------------------------------"
    echo "$CRON_CMD"
    echo "---------------------------------------------------"
    echo "Logs will be saved to: $LOG_FILE"
fi