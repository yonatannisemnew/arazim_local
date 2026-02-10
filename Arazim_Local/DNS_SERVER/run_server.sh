#!/bin/bash

# 1. Check for admin privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: This script must be run as root."
  exit 1
fi

# Get the directory where this script is actually saved
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use quotes around paths to handle spaces (e.g., "Arazim Local")
SERVER_C_PATH="$SCRIPT_DIR/dns_server.c"
SERVER_BINARY_PATH="$SCRIPT_DIR/dns_server"

# 2. Compile dns_server
echo "Compiling dns_server..."
# Quotes added here:
gcc "$SERVER_C_PATH" -o "$SERVER_BINARY_PATH" -lpcap

# 3. Check for errors
if [ $? -ne 0 ]; then
    echo "Error: Compilation failed. Exiting."
    exit 1
fi

# 4. Execute
echo "Starting server..."
# Added "$" to use the variable, and quotes for safety
"$SERVER_BINARY_PATH"