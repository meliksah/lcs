# Logitech Channel Switcher - Tools

Command-line utilities for device discovery and channel switching.

## Contents

- [CLI Switcher](#cli-switcher) - Stateless channel switching with keyboard shortcut support
- [Probe Devices](#probe-devices) - Discover paired devices and their configuration values

---

## CLI Switcher

Lightweight command-line tool for channel switching via keyboard shortcuts or scripts, without requiring the main GUI application.

### Features

- ✅ **Stateless execution** - No background processes required
- ✅ **Silent operation** - No console windows (when using shortcuts)
- ✅ **Global keyboard shortcuts** - Works system-wide
- ✅ **Zero-touch auto-configuration** - First-run automatic device detection
- ✅ **Interactive configuration** - Manual device identification if needed
- ✅ **Cross-platform** - Windows, Linux, macOS

### Quick Start

```bash
# First-run: Auto-configure (silent)
python tools/cli_switcher.py --channel 1 --quiet
# Detects receiver, assigns first device=keyboard, second=mouse

# Or: Interactive configuration (prompts for device selection)
python tools/cli_switcher.py --channel 1

# Switch to channel 2 silently
python tools/cli_switcher.py --channel 2 --quiet
```

### Usage

```bash
python tools/cli_switcher.py --channel <1|2|3> [--quiet]

Arguments:
  --channel <1|2|3>   Target channel to switch to (required)
  --quiet             Silent mode, no output (auto-configures on first run)
```

### Auto-Configuration (Quiet Mode)

On first run, the CLI automatically detects your Logitech receiver and paired devices:

- Tries **Bolt** protocol first (`046D:C548`), falls back to **Unifying** (`046D:C52B`)
- First device found is assigned as **keyboard**
- Second device found is assigned as **mouse**
- Configuration saved to `~/.lcs_config/config.json`
- No user interaction required (perfect for enterprise deployment)

**Why it works:** The first paired device is typically the keyboard, and the second is the mouse. Even if they're swapped, both devices receive the same channel-switch command, so functionality is identical.

### Interactive Configuration

If you prefer to manually identify your devices:

```bash
python tools/cli_switcher.py --channel 1
```

The interactive mode will:
1. Detect available receivers (Bolt/Unifying)
2. Discover paired devices
3. Let you test each device by sending a switch command
4. Observe which physical device responds (LED blinks or channel switches)
5. Save your selections to config

### Configuration File

Settings are stored in `~/.lcs_config/config.json`:

```json
{
  "PROTOCOL": "bolt",
  "VENDOR_ID": "046D",
  "PRODUCT_ID": "C548",
  "KB_RECEIVER_SLOT": 1,
  "MS_RECEIVER_SLOT": 2,
  "KEYBOARD_ID": 10,
  "MOUSE_ID": 10
}
```

**Field Descriptions:**
- `PROTOCOL`: `"bolt"` (HID++ 2.0) or `"unifying"` (HID++ 1.0)
- `VENDOR_ID`/`PRODUCT_ID`: USB identifiers (hex without `0x` prefix)
- `KB_RECEIVER_SLOT`/`MS_RECEIVER_SLOT`: Device slot on receiver (1-6, typically 1 and 2)
- `KEYBOARD_ID`/`MOUSE_ID`: Change Host feature index (use [probe_devices.py](#probe-devices) to discover)

**Note:** Both devices can have the same feature index - the `RECEIVER_SLOT` differentiates them, not the feature index. See [DEVICE_CONFIG_EXPLAINED.md](DEVICE_CONFIG_EXPLAINED.md) for details.

### Keyboard Shortcuts

Pre-configured shortcut scripts are available in `tools/shortcuts/`:

- **Windows:** `.bat` files using `pythonw.exe` (no console flash)
- **Linux/macOS:** `.sh` shell scripts

**Setup:**
1. Run `configure.bat` (Windows) or `configure.sh` (Linux/macOS) to set up your devices
2. Create keyboard shortcuts pointing to the channel switcher scripts:
   - `switch-channel-1.bat` / `switch-channel-1.sh`
   - `switch-channel-2.bat` / `switch-channel-2.sh`
   - `switch-channel-3.bat` / `switch-channel-3.sh`

See [shortcuts/README.md](shortcuts/README.md) for detailed platform-specific setup instructions.

### Exit Codes

- `0` - Success
- `1` - Configuration error (missing config, invalid values)
- `2` - HID communication failure (device not found, command failed)
- `3` - Invalid arguments

### Enterprise Deployment

For IT teams deploying to multiple machines:

**Zero-Touch Setup:**
```powershell
# Deploy script + create shortcut with --quiet flag
python tools/cli_switcher.py --channel 1 --quiet
```

The `--quiet` flag enables fully automated configuration on first run. No user prompts, ideal for:
- Group Policy Object (GPO) deployments
- Configuration management tools (Ansible, Puppet, etc.)
- DLP-compliant environments
- Zero-trust security policies

**Pre-Configuration:**

Alternatively, deploy a pre-configured `config.json` to `%USERPROFILE%\.lcs_config\` (Windows) or `~/.lcs_config/` (Unix) to skip auto-detection entirely.

### Troubleshooting

**"No receiver found"**
- Verify receiver is plugged in
- Check devices are on and paired
- Try running `probe_devices.py` to confirm detection
- On Linux, may need `sudo` for HID access

**"Channel switch command failed"**
- Ensure devices are awake (move mouse, press key)
- Verify `RECEIVER_SLOT` values are different (1 vs 2, not both 1)
- Check feature indices with `probe_devices.py`

**Configuration issues**
- Delete `~/.lcs_config/config.json` and run again
- Use `configure.bat`/`configure.sh` for interactive setup
- See [DEVICE_CONFIG_EXPLAINED.md](DEVICE_CONFIG_EXPLAINED.md) for slot vs feature index explanation

---

## Probe Devices

Utility to discover Logitech Bolt/Unifying receivers and query paired devices for their configuration values.

### Purpose

Finds the `RECEIVER_SLOT` and `DEVICE_ID` (Change Host feature index) values needed for `config.json`.

### Usage

```bash
python tools/probe_devices.py [--protocol bolt|unifying] [VID:PID] [--debug]

Arguments:
  --protocol   bolt or unifying (default: bolt)
  VID:PID      Vendor:Product ID in hex (default: 046D:C548 for Bolt)
  --debug      Show detailed HID communication logs

Examples:
  python tools/probe_devices.py
  python tools/probe_devices.py --protocol unifying 046D:C52B
  python tools/probe_devices.py --debug
```

### What It Does

**Step 1: Device Discovery**
- Pings device indices 0-8 using HID++ 2.0 ping command (IRoot feature)
- Reports which slots have paired devices

**Step 2: Feature Query**
- Queries each discovered device for the **Change Host (0x1814)** feature
- Returns the feature index for each device

### Example Output

```
Probe v0.5 — Probing receiver 046D:C548 (protocol: bolt)
Using: C:\...\hidapitester-windows-x86_64.exe

--- Step 1: Pinging device indices 0-8 ---

  Device index 0: -       
  Device index 1: FOUND   
  Device index 2: FOUND   
  Device index 3: -       
  ...

--- Step 2: Querying Change Host (0x1814) feature index ---

  Device index 1: Change Host feature at index 10 (0x0A)
  Device index 2: Change Host feature at index 10 (0x0A)

--- Summary ---

  Protocol:   bolt
  VID:PID:    046D:C548

  Device index (RECEIVER_SLOT): 1
  Change Host feature index (DEVICE_ID): 10 (0x0A)

  Device index (RECEIVER_SLOT): 2
  Change Host feature index (DEVICE_ID): 10 (0x0A)

Use these values in config.json:
  KB_RECEIVER_SLOT: 1, KEYBOARD_ID: 10
  MS_RECEIVER_SLOT: 2, MOUSE_ID: 10
```

### Understanding the Output

- **RECEIVER_SLOT** - The slot number where your device is paired (1-6)
- **DEVICE_ID** - Change Host feature index (varies by device model)
- Both devices can have the **same feature index** - this is normal!
  - The RECEIVER_SLOT differentiates them
  - Both receive identical channel-switch commands

### Protocol Detection

**Default Bolt VID:PID:** `046D:C548`
- Bolt receivers (newer, uses HID++ 2.0)
- 20-byte packets, report ID `0x11`

**Unifying VID:PID:** `046D:C52B`
- Unifying receivers (older, uses HID++ 1.0)
- 7-byte packets, report ID `0x10`

If your receiver isn't detected, check Windows Device Manager or `lsusb` on Linux to find the correct VID:PID.

### Wake-Up Behavior

The tool sends commands **twice with a 2-second timeout** to wake sleeping devices. However, it's unverified whether this alone is sufficient - user activity during testing (moving mouse, pressing keys) may be required to wake devices.

If devices aren't detected, try:
1. Moving your mouse or pressing a key
2. Running the probe again immediately after
3. Ensuring devices are on and within range

### Technical Details

Uses `hidapitester` binary (located in `static/hidapitester/`) to communicate with HID devices across platforms:

- **Windows:** `hidapitester-windows-x86_64.exe`
- **macOS:** `hidapitester-macos-arm64` / `hidapitester-macos-x86_64`
- **Linux:** `hidapitester-linux-x86_64` / `hidapitester-linux-armv7l`

**HID++ Commands:**
- Ping: `[report_id, device_index, 0x00, 0x1F, 0x00, 0x00, 0xAA, ...]`
- Get Feature: `[report_id, device_index, 0x00, 0x0F, feat_hi, feat_lo, ...]`

See [Logitech HID++ specification](https://lekensteyn.nl/logitech-unifying.html) for protocol details.

### Permissions

- **Linux:** Requires `sudo` for HID access
- **macOS:** May need Input Monitoring permission
- **Windows:** No special permissions required

---

## See Also

- [shortcuts/README.md](shortcuts/README.md) - Keyboard shortcut setup guide
- [DEVICE_CONFIG_EXPLAINED.md](DEVICE_CONFIG_EXPLAINED.md) - Technical explanation of slots vs feature indices
- [../BOLT_SETUP.md](../BOLT_SETUP.md) - Bolt protocol configuration guide
- [../README.md](../README.md) - Main project documentation
