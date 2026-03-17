# Logitech Channel Switcher (auto-lcs)

Desktop app (Python/PyQt6) running in system tray that automatically switches Logitech Unifying keyboard and mouse channels when the cursor hits a screen edge.

## Architecture

```
src/
  main.py              - Entry point, system tray icon + menu
  flow.py              - Core logic: mouse position polling + HID++ channel switching
  mouse_emulation.py   - Anti-sleep: mouse movement (scipy B-spline) + F15 keypress
  uniclip.py           - Shared clipboard via external uniclip binary (server/client)
  settings.py          - Config persistence (~/.lcs_config/config.json) + settings dialog
  utils.py             - Path helpers, OS-specific flags
tools/
  probe_devices.py     - Discover paired devices + Change Host feature indices
static/
  hidapitester/        - HID API binaries (linux/macos/windows)
  uniclip/             - Uniclip binaries (linux/macos/windows)
  icon/                - App icons
```

## Key concepts

- **Flow**: Every 300ms checks cursor position. If at a configured screen edge (top/bottom/left/right), sends HID++ packets via `hidapitester` to switch keyboard + mouse to the target channel.
- **Bolt HID++ packet**: `[0x11, RECEIVER_SLOT, FEATURE_INDEX, 0x1E, CHANNEL, 0x00 x15]` (20 bytes, usage 2)
- **Unifying HID packet**: `[0x10, RECEIVER_SLOT, DEVICE_ID, 0x1C, CHANNEL, 0x00, 0x00]` (7 bytes, usage 1)
- **FEATURE_INDEX**: Change Host (0x1814) feature index, varies per device. Discovered via `tools/probe_devices.py`. Note: probe sends messages twice with 2s timeout to wake sleeping devices, but it's unverified whether this alone is sufficient — user activity during testing may have been the actual wake factor.
- **Keep Me Awake**: Moves mouse after 45s inactivity, presses F15 every 30s.
- **Uniclip**: Launches uniclip subprocess for cross-machine clipboard sharing over LAN.

## Build & run

```bash
pip install -r requirements.txt
python3.9 src/main.py
```

Windows additionally needs `pypiwin32`. Linux needs `sudo` for HID access. CI builds via PyInstaller on tag push (`v*`).

## Design notes

- **Threading**: HID commands (flow.py) and mouse movement (mouse_emulation.py) run in QThread workers to avoid blocking the GUI. Cursor operations use pyqtSignal to marshal back to the main thread.
- **Config**: Stored in `~/.lcs_config/config.json` with 0o600 permissions on non-Windows. Settings dialog is created once and reused.
- **Uniclip**: Server and client use separate subprocess handles. Password is configurable via settings (UNICLIP_PASSWORD).
