#!/bin/bash
set -e

INSTALL_DIR="/opt/logitech-channel-switcher"
DESKTOP_FILE="$HOME/.local/share/applications/logitech-channel-switcher.desktop"

echo "Installing Logitech Channel Switcher..."

sudo mkdir -p "$INSTALL_DIR"
sudo cp -r "Logitech Channel Switcher"/* "$INSTALL_DIR/"
sudo chmod +x "$INSTALL_DIR/Logitech Channel Switcher"

mkdir -p "$(dirname "$DESKTOP_FILE")"
cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Name=Logitech Channel Switcher
Comment=Switch Logitech device channels across computers
Exec="$INSTALL_DIR/Logitech Channel Switcher"
Icon=$INSTALL_DIR/static/icon/split-screen.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=false
EOF

chmod +x "$DESKTOP_FILE"
echo "Installation complete. You may need to log out and back in for the desktop entry to appear."
