# Logitech Channel Switcher

This script allows you to switch channels of your Logitech keyboard and mouse automatically whenever the mouse goes over a specific part of the screen, which is configurable.

<img width="100" alt="image" src="https://user-images.githubusercontent.com/9367348/225811049-dd1e2950-fe20-44ce-98fc-4b6675b76e02.png">
<img width="300" alt="image" src="https://user-images.githubusercontent.com/9367348/225811535-97c6bf67-befe-42d8-ab6d-956b3ef1824f.png">

You need to change Receiver Slot and ID accordingly in above settings. 0x10 at header, const/magic number and paddings are constant. Target channel is calculating according to if mouse go Target 1 region it is passing 0 and switching to 1. if mouse go Target 2 region it is passing 1 and switching to channel 2. If mouse go Target 3 region it is passing 2 and switching to 3rd channel.

| Device   | Header | Receiver Slot | ID | Const/Magic Number | Target Channel | Padding | Padding |
|----------|--------|---------------|----|-------------------|----------------|---------|---------|
| Keyboard | 0x10   | 0x01          | 0x09 | 0x1c              | 0x00           | 0x00    | 0x00    |
| Mouse    | 0x10   | 0x02          | 0x0c | 0x1c              | 0x00           | 0x00    | 0x00    |

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
