# Logitech Channel Switcher

This script allows you to switch channels of your Logitech keyboard and mouse automatically whenever the mouse goes over a specific part of the screen, which is configurable.
## Running Application
### Linux 
Linux needs sudo priveledges to run application. you can run with `sudo ./linux_channel_switcher` 
### MacOSx 
MacOSx needs input tracking privileges whenever you activate from system tray icon and go to edge of screen which is set at settings it needs to ask automatically
### Windows
Windows can run exe file directly
## Creating distribution

### Linux and MacOSx
```
pyinstaller --onefile --windowed --add-data "icon.png:." --add-data "icon.ico:." --add-data "icon.icns:." --add-data "hidapitester-windows-x86_64.exe:." --add-data "hidapitester-linux-x86_64:." --add-data "hidapitester-linux-armv7l:." --add-data "hidapitester-macos-arm64:." --add-data "hidapitester-macos-x86_64:." --add-data "config.json:."--icon=icon.icns --name logitech_channel_switcher main.py
```

### Windows
```
python -m PyInstaller --onefile --windowed --add-data "icon.png;." --add-data "icon.ico;." --add-data "icon.icns;." --add-data "hidapitester-windows-x86_64.exe;." --add-data "hidapitester-linux-x86_64;." --add-data "hidapitester-linux-armv7l;." --add-data "hidapitester-macos-arm64;." --add-data "hidapitester-macos-x86_64;." --add-data "config.json;." --icon icon.ico --name logitech_channel_switcher main.py
```
## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
