# Logitech Channel Switcher
## Flow
This script allows you to switch channels of your Logitech keyboard and mouse automatically whenever the mouse goes over a specific part of the screen, which is configurable.

<img width="100" alt="image" src="https://user-images.githubusercontent.com/9367348/225811049-dd1e2950-fe20-44ce-98fc-4b6675b76e02.png">
<img width="300" alt="image" src="https://user-images.githubusercontent.com/9367348/225811535-97c6bf67-befe-42d8-ab6d-956b3ef1824f.png">

You need to change Receiver Slot and ID accordingly in above settings. 0x10 at header, const/magic number and paddings are constant. Target channel is calculating according to if mouse go Target 1 region it is passing 0 and switching to 1. if mouse go Target 2 region it is passing 1 and switching to channel 2. If mouse go Target 3 region it is passing 2 and switching to 3rd channel.

| Device   | Header | Receiver Slot | ID | Const/Magic Number | Target Channel | Padding | Padding |
|----------|--------|---------------|----|-------------------|----------------|---------|---------|
| Keyboard | 0x10   | 0x01          | 0x09 | 0x1c              | 0x00           | 0x00    | 0x00    |
| Mouse    | 0x10   | 0x02          | 0x0c | 0x1c              | 0x00           | 0x00    | 0x00    |

For running application in linux you need to grant execution permission and run with sudo. Otherwise application cannot connect to hidapi

```
chmod +x logitech_channel_switcher-linux
```

For running application
```
sudo ./logitech_channel_switcher-linux
```
## Mouse Emulation
For preventing sleep of computer whenever you are focused another computer it can move your mouse in every 10 second. If it detect user movement it will give up moving until user is not moving for 10 second.

## Uniclip

For linux users they need to install xclip, xsel, wayland or termux. [Details can be found here](https://github.com/quackduck/uniclip/blob/master/uniclip.go#L323)

```
sudo apt-get install xclip
```

Whenever you enabled server in one computer it will create server you can check ip and port from there and from another computer you can click connect server and enter ip and port in this format `192.168.50.50:55555`.

## Running Application
### From Source Code
For running the code from source code follow below commands.
```
pip install -r requirements.txt
python3.9 src/main.py
```
### Linux 
Linux needs sudo priveledges to run application. you can run with `sudo ./linux_channel_switcher` 
### MacOSx 
MacOSx needs input tracking privileges whenever you activate from system tray icon and go to edge of screen which is set at settings it needs to ask automatically
### Windows
Windows can run exe file directly
## Creating distribution

### Linux and MacOSx
```
pyinstaller --onefile --windowed --add-data "static/icon:static/icon" --add-data "static/hidapitester:static/hidapitester" --add-data "static/uniclip:static/uniclip" --icon static/icon/icon.icns --name logitech_channel_switcher src/main.py
```

### Windows
```
python -m PyInstaller --onefile --windowed --add-data "static/icon;static/icon" --add-data "static/hidapitester;static/hidapitester" --add-data "static/uniclip;static/uniclip" --icon static/icon/icon.ico --name logitech_channel_switcher src/main.py
```
## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
