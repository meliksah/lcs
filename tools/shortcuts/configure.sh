#!/bin/bash
# Logitech Channel Switcher - Configure Devices
# Run this script to set up your keyboard and mouse assignment

echo "======================================================================"
echo " Logitech Channel Switcher - CONFIGURATION"
echo "======================================================================"
echo

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if config already exists
CONFIG_FILE="$HOME/.lcs_config/config.json"

if [ -f "$CONFIG_FILE" ]; then
    echo "Configuration already exists at:"
    echo "$CONFIG_FILE"
    echo
    read -p "Do you want to reconfigure? (y/n): " RECONFIGURE
    
    if [[ ! "$RECONFIGURE" =~ ^[Yy]$ ]]; then
        echo
        echo "Configuration unchanged. Exiting."
        exit 0
    fi
    
    echo
    rm "$CONFIG_FILE"
    echo "Old configuration deleted."
    echo
fi

# Run configuration (interactive mode)
python3 "$SCRIPT_DIR/../cli_switcher.py" --channel 1

echo
echo "======================================================================"
if [ $? -eq 0 ]; then
    echo "Configuration saved successfully!"
    echo
    echo "You can now use the channel switcher shortcuts:"
    echo "  - switch-channel-1.sh"
    echo "  - switch-channel-2.sh"
    echo "  - switch-channel-3.sh"
else
    echo "Configuration failed!"
    echo "Please check error messages above."
fi
echo "======================================================================"
