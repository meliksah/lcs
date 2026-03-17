# Mac Testing Guide

## What is this project?

**auto-lcs** (Logitech Channel Switcher) is a system tray app that acts as a software KVM switch for Logitech multi-device keyboards and mice. When your cursor hits a screen edge, it sends HID packets to the Logitech receiver to switch the keyboard and mouse to a different channel — letting you control multiple machines with one set of peripherals.

### Features to test

| Feature | Description |
|---------|-------------|
| **Flow** | Cursor hits a screen edge → keyboard + mouse switch to configured channel |
| **Keep Me Awake** | Anti-sleep: moves mouse after 45s inactivity, presses F15 every 30s |
| **Uniclip** | Shared clipboard between machines over LAN (server/client) |
| **Settings** | GUI dialog for configuring HID device IDs, trigger edges, zones, protocol |

## Setup

### Prerequisites

- Python 3.9+
- macOS (Apple Silicon or Intel)
- Logitech Bolt or Unifying receiver plugged in
- Paired keyboard and mouse (multi-channel capable, e.g. MX Keys / MX Master)

### Install

```bash
cd auto-lcs
pip install -r requirements.txt
```

No extra packages needed on Mac (no `pypiwin32`).

### Run

```bash
python src/main.py
```

The app appears as a system tray icon (menu bar, top-right).

### Find your device IDs

Before testing Flow, you need your receiver's device slot and ID values. Use the probe tool:

```bash
# Bolt receiver (default VID:PID 046D:C548)
python tools/probe_devices.py

# Unifying receiver
python tools/probe_devices.py 046D:C52B
```

Note the `Slot` and `Device ID` values for your keyboard and mouse — enter these in Settings.

## Test plan

### 1. App launch and tray icon

- [ ] App starts without errors in terminal
- [ ] Icon appears in macOS menu bar
- [ ] Right-click (or click) on icon shows context menu with: Flow, Keep Me Awake, Start Clipboard Server, Connect Clipboard Server, Settings, Quit

### 2. Settings dialog

- [ ] Settings opens and shows current config values
- [ ] Protocol dropdown works (bolt / unifying)
- [ ] Hex fields (Vendor ID, Product ID, Keyboard/Mouse IDs) accept valid hex, reject invalid
- [ ] Target position dropdowns work (top/bottom/left/right/none)
- [ ] Zone mode fields enable/disable correctly when switching full ↔ zone
- [ ] Save persists to `~/.lcs_config/config.json`
- [ ] File permissions are `0o600` (`-rw-------`): `ls -la ~/.lcs_config/config.json`
- [ ] Cancel reverts changes (does not save partial edits)

### 3. Flow (channel switching)

**Setup:** Configure Settings with your device IDs from `probe_devices.py`. Set Target 1 position to a screen edge (e.g. `right`).

- [ ] Enable Flow from tray menu (checkbox becomes checked)
- [ ] Move cursor to the configured edge → keyboard and mouse switch to channel 1
- [ ] Cursor nudges 1px away from the edge after successful switch
- [ ] Disable Flow → cursor at edge no longer triggers switch
- [ ] Test with `Require Ctrl` enabled: only switches when holding Ctrl

**Zone mode:**
- [ ] Set Target 1 mode to `zone`, size to e.g. 200px, anchor `start`
- [ ] Only the top 200px (or left 200px) of the edge triggers a switch
- [ ] Rest of the edge does not trigger

**Multi-monitor (if available):**
- [ ] Edge detection works correctly across multiple displays
- [ ] Screen boundaries are computed from all connected monitors

### 4. Keep Me Awake (mouse emulation)

- [ ] Enable from tray menu
- [ ] After ~45s of no mouse movement, cursor moves automatically (smooth B-spline path)
- [ ] F15 keypress fires every 30s (check with key event viewer or `Key Codes.app`)
- [ ] Disable from tray menu → emulation stops, cursor no longer moves automatically
- [ ] Moving the mouse resets the inactivity timer

### 5. Uniclip (shared clipboard)

**Server:**
- [ ] Click "Start Clipboard Server" → notification shows IP:port
- [ ] Menu shows green dot with IP:port info
- [ ] Stop server → green dot disappears

**Client (requires second machine running uniclip server):**
- [ ] Click "Connect Clipboard Server" → input dialog appears
- [ ] Enter valid IP:port → client connects
- [ ] Copy text on one machine, paste on the other
- [ ] Invalid IP:port format shows warning
- [ ] Disconnect client → checkbox unchecks

### 6. Quit

- [ ] Quit from tray menu stops all services (Flow, emulation, uniclip) cleanly
- [ ] No orphan processes remain: `ps aux | grep -E 'hidapitester|uniclip'`

## macOS-specific things to watch for

| Area | What to check |
|------|---------------|
| **HID access** | macOS may prompt for Input Monitoring permission (System Settings → Privacy & Security → Input Monitoring). Grant it to Terminal / Python. |
| **Accessibility** | Cursor movement via `QCursor.setPos` may require Accessibility permission. |
| **Gatekeeper** | hidapitester / uniclip binaries may be blocked. Right-click → Open, or: `xattr -d com.apple.quarantine static/hidapitester/*` and same for `static/uniclip/*`. |
| **System tray** | macOS menu bar icons are monochrome by default. Check if the icon renders correctly. |
| **Architecture** | On Apple Silicon, verify the correct binary is selected (arm64). Check with: `python -c "import platform; print(platform.machine())"` |

## Troubleshooting

**"hidapitester: Operation not permitted"**
→ Grant Input Monitoring permission, or run with `sudo` as a last resort.

**Icon doesn't appear in menu bar**
→ macOS may hide tray icons if the menu bar is full. Try with fewer menu bar apps.

**Binary blocked by Gatekeeper**
```bash
xattr -d com.apple.quarantine static/hidapitester/hidapitester-macos-*
xattr -d com.apple.quarantine static/uniclip/uniclip-macos-*
chmod +x static/hidapitester/hidapitester-macos-*
chmod +x static/uniclip/uniclip-macos-*
```

**Flow triggers but devices don't switch**
→ Double-check Vendor ID, Product ID, Receiver Slots and Device IDs in Settings. Re-run `probe_devices.py` to verify.

**"No module named PyQt6"**
→ `pip install PyQt6` (native arm64 wheels available, no build required).
