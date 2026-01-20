#!/bin/bash

# ==========================================
# Linux Installer for Arazim Local
# ==========================================

# 1. Get absolute path
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 2. Define paths
SOURCE_DIR="$SCRIPT_DIR/../Arazim Local"
TARGET_DIR="/opt/Arazim_Local"

echo "Starting installation of Arazim Local..."

# 3. Check Source
if [ ! -d "$SOURCE_DIR" ]; then
    echo "Error: Source directory not found at: $SOURCE_DIR"
    exit 1
fi

# 4. Create target
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory at $TARGET_DIR"
    sudo mkdir -p "$TARGET_DIR"
fi

# 5. Copy files
echo "Copying files..."
sudo cp -a "$SOURCE_DIR/." "$TARGET_DIR/"

if [ $? -ne 0 ]; then
    echo "Error: Failed to copy files."
    exit 1
fi

# 6. Set executable permissions
echo "Setting executable permissions..."

# Use sudo for chmod as files are now in /opt (owned by root)
if [ -f "$TARGET_DIR/Arazim Local.sh" ]; then
    sudo chmod +x "$TARGET_DIR/Arazim Local.sh"
fi

if [ -f "$TARGET_DIR/Uninstall Arazim Local.sh" ]; then
    sudo chmod +x "$TARGET_DIR/Uninstall Arazim Local.sh"
fi

echo "Installation complete."