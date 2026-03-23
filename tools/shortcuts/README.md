# Keyboard Shortcuts for LCS CLI

This directory contains helper scripts for creating global keyboard shortcuts to switch Logitech channels instantly.

## ⚠️ IMPORTANT: First-Time Setup

**The silent shortcuts will auto-configure on first run!**

When you run a shortcut for the first time without configuration, it will:
1. **Automatically detect** your Logitech receiver (tries Bolt, then Unifying)
2. **Auto-assign** first device found as keyboard, second as mouse
3. **Save configuration** to `%USERPROFILE%\.lcs_config\config.json`
4. **Switch channels** immediately

### If You Want Manual Control

If you prefer to choose which device is keyboard/mouse (though it doesn't functionally matter):

### Windows
1. Double-click **`configure.bat`** in this directory
2. Follow the interactive prompts to select your protocol and identify your devices
3. Configuration will be saved to `%USERPROFILE%\.lcs_config\config.json`

### Linux/macOS
```bash
cd tools/shortcuts
./configure.sh
# Or: chmod +x configure.sh && ./configure.sh
```

**Why auto-config works:** The first device paired is usually the keyboard, second is the mouse. And even if they're swapped, both receive the same channel-switch command, so it works either way!

---

## Overview

The scripts in this directory provide silent, background execution of the CLI switcher without console windows. Each script switches to a specific channel (1, 2, or 3).

**Available Scripts:**
- **`configure.bat` / `configure.sh`** — **Run this FIRST** (setup/reconfiguration)
- `switch-channel-1.bat` / `switch-channel-1.sh` — Switch to Channel 1
- `switch-channel-2.bat` / `switch-channel-2.sh` — Switch to Channel 2
- `switch-channel-3.bat` / `switch-channel-3.sh` — Switch to Channel 3

---

## Windows Setup

### Method 1: Create Desktop Shortcuts (Recommended)

1. **Right-click** on the desired `.bat` file (e.g., `switch-channel-1.bat`)
2. Select **"Create shortcut"**
3. **Drag the shortcut** to your Desktop or Start Menu
4. **Right-click the shortcut** > **Properties**
5. Click in the **"Shortcut key"** field
6. **Press your desired key combination** (e.g., `Ctrl+Alt+1`)
   - Windows will automatically prefix it (e.g., shows as `Ctrl + Alt + 1`)
7. Click **OK**

**Repeat for channels 2 and 3** with different key combinations (e.g., `Ctrl+Alt+2`, `Ctrl+Alt+3`).

### Method 2: Pin to Taskbar

1. **Right-click** the `.bat` file > **"Create shortcut"**
2. **Right-click the shortcut** > **"Pin to taskbar"**
3. Once pinned, press **Win + [Number]** to trigger (Win+1 for first icon, etc.)

### Troubleshooting Windows

- **First run takes longer:** Auto-detection scans for devices (5-10 seconds). Subsequent runs are instant.
- **Exit code 1 without doing anything:** Auto-detection failed. Run `configure.bat` (Windows) or `configure.sh` (Linux/macOS) to see error messages.
- **Console window flashes:** Ensure you're using `pythonw.exe` (not `python.exe`). The provided `.bat` files already use `pythonw.exe`.
- **Shortcut doesn't work:** 
  - Verify Python is installed and in PATH
  - Try running the `.bat` file directly first (double-click)
  - Check that the configuration file exists: `%USERPROFILE%\.lcs_config\config.json`
  - Try running `configure.bat` (Windows) or `configure.sh` (Linux/macOS) to see detailed error messages
- **"pythonw.exe not found":**
  - Add Python to your PATH, or
  - Edit the `.bat` file to use the full path: `C:\Python39\pythonw.exe`
---

## Linux Setup

### GNOME (Ubuntu, Fedora, etc.)

1. Open **Settings** > **Keyboard** > **Keyboard Shortcuts** (or **Custom Shortcuts**)
2. Click **"+"** or **"Add Custom Shortcut"**
3. **Name:** `Switch to Channel 1`
4. **Command:** `/path/to/lcs/tools/shortcuts/switch-channel-1.sh`
   - Replace `/path/to/lcs` with your actual repository path
5. **Shortcut:** Click "Set Shortcut" and press your key combo (e.g., `Ctrl+Alt+1`)
6. Click **Add**

**Repeat for channels 2 and 3.**

### KDE Plasma

1. Open **System Settings** > **Shortcuts** > **Custom Shortcuts**
2. Right-click > **New** > **Global Shortcut** > **Command/URL**
3. **Trigger tab:** Set your key combination (e.g., `Ctrl+Alt+1`)
4. **Action tab:** Enter `/path/to/lcs/tools/shortcuts/switch-channel-1.sh`
5. Click **Apply**

**Repeat for channels 2 and 3.**

### Make Scripts Executable

Before using the shell scripts on Linux/macOS, make them executable:

```bash
cd tools/shortcuts
chmod +x switch-channel-1.sh
chmod +x switch-channel-2.sh
chmod +x switch-channel-3.sh
```

### Using xbindkeys (Alternative)

If your desktop environment doesn't support custom shortcuts, use `xbindkeys`:

1. Install xbindkeys:
   ```bash
   sudo apt install xbindkeys  # Debian/Ubuntu
   sudo dnf install xbindkeys  # Fedora
   ```

2. Create config file:
   ```bash
   xbindkeys --defaults > ~/.xbindkeysrc
   ```

3. Edit `~/.xbindkeysrc` and add:
   ```
   "/path/to/lcs/tools/shortcuts/switch-channel-1.sh"
       Control+Alt + 1
   
   "/path/to/lcs/tools/shortcuts/switch-channel-2.sh"
       Control+Alt + 2
   
   "/path/to/lcs/tools/shortcuts/switch-channel-3.sh"
       Control+Alt + 3
   ```

4. Restart xbindkeys:
   ```bash
   killall xbindkeys
   xbindkeys
   ```

5. Add xbindkeys to startup applications

### Troubleshooting Linux

- **"Permission denied":** Run `chmod +x switch-channel-*.sh`
- **"python3: command not found":** Install Python 3 or edit scripts to use full path
- **HID access denied:** 
  - On Linux, you may need `sudo` for HID access
  - Add udev rules to allow non-root access (see main README)
  - Or run: `sudo python3 cli_switcher.py --channel 1` (not recommended long-term)

---

## macOS Setup

### Method 1: System Preferences (Monterey and later)

1. Open **System Preferences** > **Keyboard** > **Shortcuts**
2. Select **App Shortcuts** or **Services** (left sidebar)
3. Click **"+"** to add a shortcut
4. **Application:** All Applications
5. **Command:** Enter the full path to the script:
   ```
   /Users/yourusername/path/to/lcs/tools/shortcuts/switch-channel-1.sh
   ```
6. **Keyboard Shortcut:** Press your key combo (e.g., `⌃⌥1` = Ctrl+Option+1)
7. Click **Add**

**Repeat for channels 2 and 3.**

### Method 2: Automator + Keyboard Maestro (Advanced)

For more advanced hotkey management, use [Keyboard Maestro](https://www.keyboardmaestro.com/) or [BetterTouchTool](https://folivora.ai/).

### Make Scripts Executable (macOS)

```bash
cd tools/shortcuts
chmod +x switch-channel-1.sh
chmod +x switch-channel-2.sh
chmod +x switch-channel-3.sh
```

### Troubleshooting macOS

- **"Operation not permitted":** 
  - Grant Terminal (or your script runner) **Accessibility** permissions
  - System Preferences > Security & Privacy > Privacy > Accessibility
- **"python3: command not found":** 
  - Install Python 3 via Homebrew: `brew install python3`
  - Or use full path in script: `/usr/local/bin/python3`

---

## Advanced Usage

### Custom Key Combinations

You can modify the scripts or create new ones for different workflows:

**Example: Switch channel only if Ctrl is held**
```batch
REM Windows: Add timeout check
if not "%CTRL_KEY_PRESSED%"=="1" exit
pythonw.exe "%~dp0..\cli_switcher.py" --channel 1 --quiet
```

### Running Without Shortcuts

You can also run the CLI directly from terminal:

```bash
# Switch to channel 2
python cli_switcher.py --channel 2

# Switch silently (no output)
python cli_switcher.py --channel 1 --quiet
```

### Exit Codes

The CLI returns specific exit codes for automation:
- `0` = Success
- `1` = Configuration error (missing/invalid config)
- `2` = HID communication failure
- `3` = Invalid arguments

**Example: Check if switching succeeded**
```bash
#!/bin/bash
python3 cli_switcher.py --channel 2 --quiet
if [ $? -eq 0 ]; then
    notify-send "Switched to Channel 2"
else
    notify-send "Failed to switch channel"
fi
```

---

## First-Run Configuration (Optional)

The shortcuts will **auto-configure on first run**, but if you want manual control:

### Windows
**Option 1: Using the helper script (Recommended)**
1. Navigate to `tools\shortcuts\`
2. Double-click **`configure.bat`**
3. Follow the interactive prompts

**Option 2: Manual command**
```powershell
cd tools
python cli_switcher.py --channel 1
```

### Linux/macOS
**Option 1: Using the helper script (Recommended)**
```bash
cd tools/shortcuts
chmod +x configure.sh
./configure.sh
```

**Option 2: Manual command**
```bash
cd tools
python3 cli_switcher.py --channel 1
```

### Linux/macOS
```bash
cd tools
python3 cli_switcher.py --channel 1
```

This will launch an interactive setup that:
1. Lets you choose protocol (Bolt or Unifying)
2. Scans for paired devices
3. **Optionally test devices** to identify which is keyboard/mouse
4. Prompts you to confirm which is your keyboard and which is your mouse
5. Saves configuration to `~/.lcs_config/config.json`

**Note:** Manual configuration is only needed if:
- Auto-detection fails (wrong protocol, unusual VID:PID)
- You want to ensure specific device assignments
- You want to test devices before saving config

For most users, **just use the shortcuts** - they'll configure automatically!

---

## Security Considerations

### Enterprise/DLP Environments

The CLI switcher is designed for strict enterprise environments:

- ✅ **No background processes** — Runs stateless, exits immediately after switching
- ✅ **No network communication** — USB/HID access only
- ✅ **No clipboard sync** — Unlike the GUI app, CLI doesn't use Uniclip
- ✅ **User-space only** — No admin/sudo required (after udev rules on Linux)
- ✅ **No persistent memory** — Only reads config file, no telemetry

### Config File Permissions

The configuration file is stored at:
- **Windows:** `C:\Users\<username>\.lcs_config\config.json`
- **Linux/macOS:** `~/.lcs_config/config.json` (chmod 600)

The file contains only device hardware identifiers (VID, PID, receiver slots, feature indices). No passwords or sensitive data.

---

## Uninstallation

To remove keyboard shortcuts:

**Windows:**
1. Delete the shortcut files you created
2. Or right-click shortcut > Properties > Clear "Shortcut key" field

**Linux (GNOME/KDE):**
1. Open Settings > Keyboard > Custom Shortcuts
2. Select and delete the LCS shortcuts

**macOS:**
1. System Preferences > Keyboard > Shortcuts
2. Select and delete the LCS shortcuts

To remove the CLI config file:
```bash
rm -rf ~/.lcs_config
```