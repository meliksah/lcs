#!/bin/bash
set -e

echo "Uninstalling Logitech Channel Switcher..."
sudo rm -rf /opt/logitech-channel-switcher
rm -f "$HOME/.local/share/applications/logitech-channel-switcher.desktop"
echo "Uninstalled successfully."
