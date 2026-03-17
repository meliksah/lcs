# Bolt HID++ 2.0 Support

## Overview

Added support for Logitech Bolt receivers (HID++ 2.0 protocol) alongside existing Unifying (HID++ 1.0) support.

## Protocol Differences

| | Unifying (HID++ 1.0) | Bolt (HID++ 2.0) |
|---|---|---|
| Report ID | `0x10` (short, 7 bytes) | `0x11` (long, 20 bytes) |
| HID usage | `1` | `2` |
| Usage page | `0xFF00` | `0xFF00` |
| Byte 3 (function) | `0x1C` | `0x1E` (functionId=1 \| swId=0xE) |
| Device ID field | Fixed per device type | Feature index for CHANGE_HOST (varies per device) |
| Receiver PID | `0xC52B` | `0xC548` |

## Packet Format

### Bolt channel switch command
```
[0x11, RECEIVER_SLOT, FEATURE_INDEX, 0x1E, CHANNEL, 0x00 x15]
```
- `RECEIVER_SLOT`: device index on receiver (e.g. 0x01, 0x02)
- `FEATURE_INDEX`: CHANGE_HOST feature index (discovered via IRoot query)
- `CHANNEL`: 0-based (0 = channel 1, 1 = channel 2, 2 = channel 3)

### Unifying channel switch command
```
[0x10, RECEIVER_SLOT, DEVICE_ID, 0x1C, CHANNEL, 0x00, 0x00]
```

## Discovering Feature Index (CHANGE_HOST)

Feature index for CHANGE_HOST (0x1814) varies per device and must be discovered via IRoot query.

### Query command
```bash
hidapitester --vidpid 046D:C548 --usage 2 --usagePage 0xFF00 --open \
  --length 20 \
  --send-output 0x11,<DEVICE_INDEX>,0x00,0x0F,0x18,0x14,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00 \
  --send-output 0x11,<DEVICE_INDEX>,0x00,0x0F,0x18,0x14,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00,0x00 \
  --timeout 2000 --length 20 --read-input
```
Note: send twice to wake sleeping devices, use 2000ms timeout.

### Response format
```
11 <DEVICE_INDEX> 00 0F <FEATURE_INDEX> 00 XX 00 00 ...
```
Byte 4 of the response = feature index to use in channel switch commands.

### Probe tool

Run `tools/probe_devices.py` to discover device indices and feature indices automatically:

```bash
python tools/probe_devices.py              # Bolt (default)
python tools/probe_devices.py --debug      # with raw HID++ output
python tools/probe_devices.py --protocol unifying 046D:C52B  # Unifying
```

### Tested hardware values (Windows receiver)

| Device | Receiver Slot | CHANGE_HOST Feature Index |
|---|---|---|
| Keyboard (MX Keys Mini) | `0x01` | `0x09` |
| Mouse | `0x02` | `0x0E` |

## Settings

New `Protocol` field in Settings UI (combo box: `bolt` / `unifying`). Stored in config as `PROTOCOL`.

### Recommended Settings (Bolt)
```
Protocol:          bolt
Vendor ID:         046D
Product ID:        C548
KB Receiver Slot:  01
MS Receiver Slot:  02
Keyboard ID:       09  (feature index, not device type — MX Keys Mini)
Mouse ID:          0E  (feature index, not device type)
```

## Files Modified

- `src/settings.py` — Added `PROTOCOL` config field (default: `"bolt"`), changed `PRODUCT_ID` default to `0xC548`, added protocol combo to Settings UI
- `src/flow.py` — Packet construction branches on protocol, `_build_hidapi_command()` uses dynamic usage/length, `_write_to_adu()` uses dynamic success message

## Running on Windows

```powershell
$env:QT_QPA_PLATFORM_PLUGIN_PATH="<python-path>\Lib\site-packages\PyQt6\Qt6\plugins\platforms"
py src/main.py
```

## Notes

- On Windows, `hidapitester` does not require admin privileges
- On Linux/macOS, `sudo` is required for HID access
- The `--timeout 5000` flag is needed for IRoot queries (default 250ms is too short)
- Feature indices may differ per device model — always discover via IRoot query when setting up new hardware
