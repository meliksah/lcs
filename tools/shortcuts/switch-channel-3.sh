#!/bin/bash
# Logitech Channel Switcher - Switch to Channel 3
# This script runs the CLI switcher in quiet mode
# 
# To create a keyboard shortcut:
# - GNOME: Settings > Keyboard > Custom Shortcuts
# - KDE: System Settings > Shortcuts > Custom Shortcuts
# - macOS: System Preferences > Keyboard > Shortcuts > App Shortcuts

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run the CLI switcher
python3 "$SCRIPT_DIR/../cli_switcher.py" --channel 3 --quiet
