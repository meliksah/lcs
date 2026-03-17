#!/bin/bash
set -e

INSTALL_DIR="/opt/logitech_channel_switcher"
DESKTOP_FILE="$HOME/.local/share/applications/logitech_channel_switcher.desktop"

echo "Installing Logitech Channel Switcher..."

sudo mkdir -p "$INSTALL_DIR"
sudo cp -r logitech_channel_switcher/* "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/logitech_channel_switcher"

mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Logitech Channel Switcher
Comment=Switch Logitech device channels across computers
Exec=$INSTALL_DIR/logitech_channel_switcher
Icon=$INSTALL_DIR/static/icon/icon.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"
echo "Installation complete. You may need to log out and back in for the desktop entry to appear."
