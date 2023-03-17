# Logitech Channel Switcher

This script allows you to switch channels of your Logitech keyboard and mouse automatically whenever the mouse goes over a specific part of the screen, which is configurable.

## Creating distribution

### Linux and MacOSx
```
pyinstaller --onefile --windowed --add-data "icon.png:." --add-data "icon.ico:." --add-data "icon.icns:." --add-data "hidapitester-windows-x86_64.exe:." --add-data "hidapitester-linux-x86_64:." --add-data "hidapitester-linux-armv7l:." --add-data "hidapitester-macos-arm64:." --add-data "hidapitester-macos-x86_64:." --add-data "config.json:."--icon=icon.icns --name logitech_channel_switcher main.py
```

### Windows
```
python -m PyInstaller --onefile --windowed --add-data "icon.png;." --add-data "icon.ico;." --add-data "icon.icns;." --add-data "hidapitester-windows-x86_64.exe;." --add-data "hidapitester-linux-x86_64;." --add-data "hidapitester-linux-armv7l;." --add-data "hidapitester-macos-arm64;." --add-data "hidapitester-macos-x86_64;." --add-data "config.json;." --icon icon.ico --name logitech_channel_switcher main.py
```
