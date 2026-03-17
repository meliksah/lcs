#!/bin/bash
set -e

echo "Uninstalling Logitech Channel Switcher..."
sudo rm -rf /opt/logitech_channel_switcher
rm -f "$HOME/.local/share/applications/logitech_channel_switcher.desktop"
echo "Uninstalled successfully."
