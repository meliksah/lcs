

## Creating distribution


```
pyinstaller --onefile --windowed --add-data "icon.png:." --add-data "hidapitester-windows-x86_64.exe:." --add-data "hidapitester-linux-x86_64:." --add-data "hidapitester-linux-armv7l:." --add-data "hidapitester-macos-arm64:." --add-data "hidapitester-macos-x86_64:." --icon=icon.icns --name logitech_channel_changer main.py
```