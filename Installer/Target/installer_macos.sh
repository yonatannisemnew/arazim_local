#!/bin/bash

# ==========================================
# macOS Installer for Arazim Local
# ==========================================

# 1. Get the absolute path of the directory where this script is located
#    Uses -P to resolve symlinks to the physical directory
SCRIPT_DIR="$( cd -P "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# 2. Define paths
#    Assumes script is in a subfolder (e.g. installers/). 
#    If script is in root, remove "/.."
SOURCE_DIR="$SCRIPT_DIR/../Arazim Local"
TARGET_DIR="/Library/Application Support/Arazim Local"

echo "Starting installation of Arazim Local for macOS..."

# 3. Check if source actually exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo "❌ Error: Source directory not found at:"
    echo "   $SOURCE_DIR"
    exit 1
fi

# 4. Create target directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "Creating target directory..."
    sudo mkdir -p "$TARGET_DIR"
fi

# 5. Copy files
echo "Copying files..."
# Using trailing /. ensures we copy contents, not the folder itself
sudo cp -a "$SOURCE_DIR/." "$TARGET_DIR/"

if [ $? -ne 0 ]; then
    echo "❌ Error: Failed to copy files."
    exit 1
fi

# 6. Set Executable Permissions
echo "Setting executable permissions..."
MAIN_SCRIPT="$TARGET_DIR/Arazim Local.sh"
UNINSTALL_SCRIPT="$TARGET_DIR/Uninstall Arazim Local.sh"

if [ -f "$MAIN_SCRIPT" ]; then
    sudo chmod +x "$MAIN_SCRIPT"
    # Remove Quarantine attribute, silence error if attribute missing
    sudo xattr -d com.apple.quarantine "$MAIN_SCRIPT" 2>/dev/null || true
fi

if [ -f "$UNINSTALL_SCRIPT" ]; then
    sudo chmod +x "$UNINSTALL_SCRIPT"
    sudo xattr -d com.apple.quarantine "$UNINSTALL_SCRIPT" 2>/dev/null || true
fi

echo "✅ Installation complete."
echo "Files located in: $TARGET_DIR"