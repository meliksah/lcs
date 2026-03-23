# Logitech Channel Switcher

## Flow
This script allows you to switch channels of your Logitech keyboard and mouse automatically whenever the mouse goes over a specific part of the screen, which is configurable.

<img width="100" alt="image" src="https://user-images.githubusercontent.com/9367348/225811049-dd1e2950-fe20-44ce-98fc-4b6675b76e02.png">
<img width="300" alt="image" src="https://user-images.githubusercontent.com/9367348/225811535-97c6bf67-befe-42d8-ab6d-956b3ef1824f.png">

You need to change Receiver Slot and ID accordingly in above settings. Target channel is calculated according to the configured screen edge — Target 1 switches to channel 1, Target 2 to channel 2, Target 3 to channel 3.

Supports both **Unifying** (HID++ 1.0) and **Bolt** (HID++ 2.0) protocols. See [BOLT_SETUP.md](BOLT_SETUP.md) for Bolt configuration details.

| Protocol | Device   | Header | Receiver Slot | ID   | Const | Target Channel | Padding |
|----------|----------|--------|---------------|------|-------|----------------|---------|
| Unifying | Keyboard | 0x10   | 0x01          | 0x09 | 0x1c  | 0x00           | 0x00 0x00 |
| Unifying | Mouse    | 0x10   | 0x02          | 0x0c | 0x1c  | 0x00           | 0x00 0x00 |
| Bolt     | Keyboard | 0x11   | 0x01          | 0x09 | 0x1E  | 0x00           | 0x00 x15  |
| Bolt     | Mouse    | 0x11   | 0x02          | 0x0E | 0x1E  | 0x00           | 0x00 x15  |

Use `python tools/probe_devices.py` to discover your device's Receiver Slot and ID values.

## Command-Line Tools

For keyboard shortcut-based channel switching or device discovery, see the [tools/](tools/) directory:

- **[CLI Switcher](tools/README.md#cli-switcher)** - Stateless channel switching with zero-touch auto-configuration
- **[Probe Devices](tools/README.md#probe-devices)** - Discover receiver and device configuration values
- **[Keyboard Shortcuts](tools/shortcuts/README.md)** - Ready-to-use scripts for Windows, Linux, and macOS

Perfect for:
- Users who prefer keyboard shortcuts over automatic edge-switching
- Enterprise deployments with DLP/zero-trust policies (no clipboard-sharing)
- Environments where background processes are restricted

## Mouse Emulation
Prevents computer sleep when you're focused on another machine. Moves the mouse after 45 seconds of inactivity and simulates F15 keypress every 30 seconds. Resets when user activity is detected.

## Uniclip

Clipboard sharing between machines over LAN.

For Linux users, install xclip: `sudo apt-get install xclip`. [Details here](https://github.com/quackduck/uniclip/blob/master/uniclip.go#L323)

Start the server on one computer, note the IP:port shown, then connect from the other computer using that address (e.g. `192.168.50.50:55555`).

## Running Application

### From Source Code
```bash
pip install -r requirements.txt
python src/main.py
```

#### Windows
Install `pypiwin32` before running:
```bash
pip install pypiwin32
```

### Linux
Linux needs sudo privileges for HID access:
```bash
sudo ./Logitech\ Channel\ Switcher
```

### macOS
macOS needs Input Monitoring permission (System Settings → Privacy & Security → Input Monitoring). Grant it to Terminal or Python.

### Windows
Run the exe file directly or use the installer.

## Creating Distribution

CI/CD builds automatically on tag push (`v*`) using `--onedir` mode for faster startup.

### Linux and macOS
```bash
pyinstaller --onedir --windowed --add-data "static/icon:static/icon" --add-data "static/hidapitester:static/hidapitester" --add-data "static/uniclip:static/uniclip" --icon static/icon/icon.icns --name "Logitech Channel Switcher" src/main.py
```

### Windows
```bash
python -m PyInstaller --onedir --windowed --add-data "static/icon;static/icon" --add-data "static/hidapitester;static/hidapitester" --add-data "static/uniclip;static/uniclip" --icon static/icon/icon.ico --name "Logitech Channel Switcher" src/main.py
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.
