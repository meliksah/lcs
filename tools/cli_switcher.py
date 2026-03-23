#!/usr/bin/env python3
"""
Logitech Channel Switcher CLI

Stateless command-line tool for switching Logitech Bolt/Unifying keyboard
and mouse channels without requiring background processes.

Usage:
    python cli_switcher.py --channel 1|2|3 [--quiet]

Exit codes:
    0 = Success
    1 = Configuration error (missing/invalid config)
    2 = HID communication failure
    3 = Invalid arguments

First-run behavior:
    Interactive mode: Launches interactive device discovery
    Quiet mode: Auto-configures using first two devices found
                (first device = keyboard, second = mouse)
                Tries Bolt protocol first, falls back to Unifying
"""

import argparse
import subprocess
import sys
import os
import time
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from utils import get_absolute_file_data_path, creation_flags

# Minimal imports from settings (avoid PyQt6 dependencies)
try:
    from settings import Config, SettingsManager
except ImportError:
    # Fallback if PyQt6 not installed - define minimal config classes
    import json
    import platform
    
    class Config:
        def __init__(self, PROTOCOL="unifying", VENDOR_ID=0x046D, PRODUCT_ID=0xC52B,
                     KB_RECEIVER_SLOT=0x01, MS_RECEIVER_SLOT=0x02,
                     KEYBOARD_ID=0x09, MOUSE_ID=0x0a, **kwargs):
            self.PROTOCOL = PROTOCOL
            self.VENDOR_ID = VENDOR_ID
            self.PRODUCT_ID = PRODUCT_ID
            self.KB_RECEIVER_SLOT = KB_RECEIVER_SLOT
            self.MS_RECEIVER_SLOT = MS_RECEIVER_SLOT
            self.KEYBOARD_ID = KEYBOARD_ID
            self.MOUSE_ID = MOUSE_ID
            # Store any extra kwargs for compatibility
            self.__dict__.update(kwargs)
        
        def to_dict(self):
            return self.__dict__
        
        @classmethod
        def from_dict(cls, data):
            return cls(**data)
    
    class SettingsManager:
        def __init__(self):
            self.CONFIG_FOLDER_NAME = '.lcs_config'
            self.CONFIG_FILE_NAME = 'config.json'
            self.config_path = self.get_config_path()
        
        def get_config_path(self):
            config_folder = Path.home().joinpath(self.CONFIG_FOLDER_NAME)
            config_folder.mkdir(parents=True, exist_ok=True)
            return config_folder.joinpath(self.CONFIG_FILE_NAME)
        
        def load_config(self):
            if not self.config_path.is_file():
                return None
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                return Config.from_dict(config_data)
            except (FileNotFoundError, json.JSONDecodeError):
                return None
        
        def save_config(self, config):
            with open(self.config_path, 'w') as f:
                json.dump(config.to_dict(), f, indent=2)
            # Restrict file permissions on non-Windows
            if platform.system().lower() != 'windows':
                os.chmod(self.config_path, 0o600)


def log(message, quiet=False):
    """Print message unless quiet mode is enabled."""
    if not quiet:
        print(message)


def log_error(message):
    """Always print errors to stderr."""
    print(f"ERROR: {message}", file=sys.stderr)


def get_hidapi_executable():
    """Get platform-specific hidapitester binary path."""
    import platform
    system = platform.system().lower()
    arch = platform.machine()
    
    if system == 'windows':
        return get_absolute_file_data_path('hidapitester', 'hidapitester-windows-x86_64.exe')
    elif system == 'darwin':
        name = 'hidapitester-macos-arm64' if arch == 'arm64' else 'hidapitester-macos-x86_64'
        return get_absolute_file_data_path('hidapitester', name)
    else:
        name = 'hidapitester-linux-armv7l' if arch == 'armv7l' else 'hidapitester-linux-x86_64'
        return get_absolute_file_data_path('hidapitester', name)


def build_hidapi_command(config, msg_bytes):
    """Build hidapitester command for sending HID++ packet.
    
    Args:
        config: Config object with VENDOR_ID, PRODUCT_ID, PROTOCOL
        msg_bytes: list of bytes to send
    
    Returns:
        List of command arguments for subprocess
    """
    exec_path = get_hidapi_executable()
    hex_string = ','.join(f'0x{byte:02X}' for byte in msg_bytes)
    length = str(len(msg_bytes))
    usage = '2' if config.PROTOCOL == 'bolt' else '1'
    
    cmd = [
        exec_path,
        '--vidpid', f'{config.VENDOR_ID:04X}:{config.PRODUCT_ID:04X}',
        '--usage', usage,
        '--usagePage', '0xFF00',
        '--open',
        '--length', length,
        '--send-output', hex_string,
        '--length', length,
        '--send-output', hex_string,  # Send twice for device wake
    ]
    return cmd


def send_hid_command(config, msg_bytes, max_retries=3, quiet=False):
    """Send HID command with retries.
    
    Args:
        config: Config object
        msg_bytes: list of bytes to send
        max_retries: maximum number of retry attempts
        quiet: suppress output if True
    
    Returns:
        True if successful, False otherwise
    """
    cmd = build_hidapi_command(config, msg_bytes)
    success_msg = f"wrote {len(msg_bytes)} bytes"
    
    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=creation_flags
            )
            
            if success_msg in result.stdout:
                return True
            
            # Retry with delay if not last attempt
            if attempt < max_retries:
                time.sleep(0.1)
                
        except subprocess.TimeoutExpired:
            log(f"  Timeout on attempt {attempt}/{max_retries}", quiet)
            if attempt < max_retries:
                time.sleep(0.1)
        except Exception as e:
            log(f"  Error on attempt {attempt}/{max_retries}: {e}", quiet)
            if attempt < max_retries:
                time.sleep(0.1)
    
    return False


def build_channel_switch_packet(config, device_type, channel):
    """Build HID++ packet for switching channels.
    
    Args:
        config: Config object with protocol and device settings
        device_type: 'keyboard' or 'mouse'
        channel: target channel (1, 2, or 3)
    
    Returns:
        List of bytes representing the HID++ packet
    """
    # Get device-specific slot and feature index
    if device_type == 'keyboard':
        receiver_slot = config.KB_RECEIVER_SLOT
        feature_index = config.KEYBOARD_ID
    else:  # mouse
        receiver_slot = config.MS_RECEIVER_SLOT
        feature_index = config.MOUSE_ID
    
    # Convert channel to zero-indexed (1→0, 2→1, 3→2)
    channel_byte = channel - 1
    
    # Build packet based on protocol
    if config.PROTOCOL == 'bolt':
        # Bolt: 20 bytes, report ID 0x11, function 0x1E
        packet = [0x11, receiver_slot, feature_index, 0x1E, channel_byte] + [0x00] * 15
    else:
        # Unifying: 7 bytes, report ID 0x10, function 0x1C
        packet = [0x10, receiver_slot, feature_index, 0x1C, channel_byte, 0x00, 0x00]
    
    return packet


def switch_channel(config, channel, quiet=False):
    """Switch both keyboard and mouse to target channel.
    
    Args:
        config: Config object with device settings
        channel: target channel (1, 2, or 3)
        quiet: suppress output if True
    
    Returns:
        True if both devices switched successfully, False otherwise
    """
    log(f"Switching to channel {channel}...", quiet)
    
    # Switch keyboard
    log("  Switching keyboard...", quiet)
    kb_packet = build_channel_switch_packet(config, 'keyboard', channel)
    kb_success = send_hid_command(config, kb_packet, max_retries=3, quiet=quiet)
    
    if not kb_success:
        log_error("Failed to switch keyboard")
        return False
    
    log("  Keyboard switched", quiet)
    
    # Switch mouse
    log("  Switching mouse...", quiet)
    ms_packet = build_channel_switch_packet(config, 'mouse', channel)
    ms_success = send_hid_command(config, ms_packet, max_retries=3, quiet=quiet)
    
    if not ms_success:
        log_error("Failed to switch mouse")
        return False
    
    log("  Mouse switched", quiet)
    log(f"Successfully switched to channel {channel}", quiet)
    return True


def validate_config(config):
    """Validate that config has all required fields.
    
    Args:
        config: Config object to validate
    
    Returns:
        (valid: bool, error_message: str or None)
    """
    required_fields = [
        'PROTOCOL', 'VENDOR_ID', 'PRODUCT_ID',
        'KB_RECEIVER_SLOT', 'MS_RECEIVER_SLOT',
        'KEYBOARD_ID', 'MOUSE_ID'
    ]
    
    for field in required_fields:
        if not hasattr(config, field):
            return False, f"Missing required field: {field}"
        if getattr(config, field) is None:
            return False, f"Field {field} is None"
    
    # Validate protocol value
    if config.PROTOCOL not in ['bolt', 'unifying']:
        return False, f"Invalid PROTOCOL: {config.PROTOCOL} (must be 'bolt' or 'unifying')"
    
    return True, None


def run_device_discovery(quiet=False):
    """Run interactive device discovery to generate config.
    
    Args:
        quiet: If True, auto-configure using first two devices found
    
    Returns:
        Config object if successful, None otherwise
    """
    if not quiet:
        print("\n" + "="*70)
        print("FIRST RUN: Device Discovery")
        print("="*70)
        print("\nNo configuration found. Starting device discovery...")
        print("This will scan your Logitech receiver for paired devices.\n")
    
    # Import probe_devices functions
    sys.path.insert(0, os.path.dirname(__file__))
    try:
        from probe_devices import (
            get_hidapitester, ping_device, query_feature_index
        )
    except ImportError as e:
        if not quiet:
            log_error(f"Failed to import probe_devices: {e}")
        return None
    
    # Auto-detect protocol and VID:PID in quiet mode, or prompt in interactive mode
    if quiet:
        # Try Bolt first (more common on newer receivers)
        protocol = "bolt"
        vidpid_input = "046D:C548"
        vendor_id = 0x046D
        product_id = 0xC548
    else:
        # Prompt for protocol
        print("Select receiver protocol:")
        print("  1 = Bolt (default, newer receivers)")
        print("  2 = Unifying (older receivers)")
        protocol_choice = input("Enter choice [1]: ").strip() or "1"
        
        if protocol_choice == "2":
            protocol = "unifying"
            default_vidpid = "046D:C52B"
        else:
            protocol = "bolt"
            default_vidpid = "046D:C548"
        
        print(f"\nUsing protocol: {protocol}")
        
        # Prompt for VID:PID (allow override)
        vidpid_input = input(f"Enter VID:PID [{default_vidpid}]: ").strip() or default_vidpid
        
        # Parse VID:PID
        try:
            vid_str, pid_str = vidpid_input.split(':')
            vendor_id = int(vid_str, 16)
            product_id = int(pid_str, 16)
        except:
            log_error(f"Invalid VID:PID format: {vidpid_input}")
            return None
        
        print(f"\nScanning receiver {vidpid_input}...")
    
    # Get hidapitester path
    exec_path = get_hidapitester()
    
    # Step 1: Ping device indices 0-8
    if not quiet:
        print("\nStep 1: Discovering paired devices...")
        print("(This scans receiver slots 0-8 for active devices)")
    
    devices = []
    for dev_idx in range(0, 9):
        if not quiet:
            sys.stdout.write(f'\r  Checking slot {dev_idx}...')
            sys.stdout.flush()
        ok, output, response = ping_device(exec_path, vidpid_input, protocol, dev_idx)
        if ok:
            if not quiet:
                sys.stdout.write(f'\r  Slot {dev_idx}: ✅ DEVICE FOUND   \n')
            devices.append(dev_idx)
        else:
            if not quiet:
                sys.stdout.write(f'\r  Slot {dev_idx}: -              \n')
    
    if not devices:
        if not quiet:
            log_error("\n⚠️  No devices found. Please check:")
            log_error("  - Receiver is plugged in and recognized by your computer")
            log_error("  - Keyboard/mouse are turned ON and paired to this receiver")
            log_error(f"  - VID:PID {vidpid_input} matches your receiver")
            log_error(f"  - Protocol '{protocol}' matches your receiver type")
            log_error("\n💡 TIP: Try running 'python probe_devices.py' for more details")
        return None
    
    # In quiet mode, try Unifying if Bolt didn't find devices
    if quiet and not devices and protocol == "bolt":
        protocol = "unifying"
        vidpid_input = "046D:C52B"
        vendor_id = 0x046D
        product_id = 0xC52B
        
        # Retry with Unifying protocol
        devices = []
        for dev_idx in range(0, 9):
            ok, output, response = ping_device(exec_path, vidpid_input, protocol, dev_idx)
            if ok:
                devices.append(dev_idx)
        
        if not devices:
            return None
    
    if not quiet:
        print(f"\n✅ Found {len(devices)} device(s) at slot(s): {', '.join(map(str, devices))}")
    
    # Step 2: Query Change Host feature for each device
    CHANGE_HOST = 0x1814
    if not quiet:
        print("\nStep 2: Querying Change Host feature...")
    
    results = []
    for dev_idx in devices:
        if not quiet:
            sys.stdout.write(f'  Device slot {dev_idx}: ')
            sys.stdout.flush()
        feat_idx, _ = query_feature_index(exec_path, vidpid_input, protocol, dev_idx, CHANGE_HOST)
        if feat_idx and feat_idx > 0:
            if not quiet:
                print(f'✅ Change Host found at feature index {feat_idx} (0x{feat_idx:02X})')
            results.append((dev_idx, feat_idx))
        else:
            if not quiet:
                print('❌ Change Host not found (device does not support channel switching)')
    
    if not results:
        if not quiet:
            log_error("\n⚠️  No devices with Change Host support found.")
            log_error("Your devices may not support channel switching.")
            log_error("Ensure your keyboard/mouse have multi-device/multi-channel capability.")
        return None
    
    if len(results) < 2:
        if not quiet:
            log_error(f"\n⚠️  Only found {len(results)} device with Change Host support.")
            log_error("You need both a keyboard AND mouse paired to the receiver.")
            log_error("\nPossible solutions:")
            log_error("  1. Pair your second device to the receiver")
            log_error("  2. Turn on the device if it's off")
            log_error("  3. Check if both devices support multi-device switching")
        return None
    
    # Auto-configure in quiet mode: first device = keyboard, second = mouse
    if quiet:
        kb_receiver_slot, kb_feature_idx = results[0]
        ms_receiver_slot, ms_feature_idx = results[1]
        
        # Create config directly without user interaction
        config = Config(
            PROTOCOL=protocol,
            VENDOR_ID=vendor_id,
            PRODUCT_ID=product_id,
            KB_RECEIVER_SLOT=kb_receiver_slot,
            MS_RECEIVER_SLOT=ms_receiver_slot,
            KEYBOARD_ID=kb_feature_idx,
            MOUSE_ID=ms_feature_idx
        )
        return config
    
    # Step 3: Interactive device assignment (only in non-quiet mode)
    print("\n" + "="*70)
    print("Step 3: Device Assignment")
    print("="*70)
    print("\n📋 DEVICES FOUND:")
    for i, (dev_idx, feat_idx) in enumerate(results, 1):
        print(f"  {i}. Device at receiver slot {dev_idx} | Change Host feature index: {feat_idx} (0x{feat_idx:02X})")
    
    print("\n💡 NOTE: It's normal for devices to have the same feature index.")
    print("   What matters is the SLOT number (1 vs 2), which identifies each device.")
    print("\n💡 TIP: It doesn't actually matter which device you call 'keyboard' or 'mouse'.")
    print("   Both receive the same channel-switch command. The labels are just for clarity.")
    
    print("\n🔍 HELP: Not sure which device is which?")
    print("   Option 1: Usually, the first device paired (lower slot) is the keyboard")
    print("   Option 2: Test each device individually below (sends command to see which responds)")
    print("   Option 3: Just pick any assignment - it will still work! 😊")
    
    test_choice = input("\n🧪 Would you like to test each device before choosing? [y/N]: ").strip().lower()
    
    kb_from_test = None
    ms_from_test = None
    
    if test_choice in ['y', 'yes']:
        print("\n" + "="*70)
        print("🧪 DEVICE TESTING MODE")
        print("="*70)
        print("\nWe'll send a channel switch command to each device.")
        print("Watch your keyboard and mouse to see which one responds.\n")
        
        # Ask what channel devices are currently on
        print("💡 TIP: For the test to work, we need to switch to a DIFFERENT channel")
        print("        than the one your devices are currently on.\n")
        
        while True:
            current_channel = input("What channel are your devices currently on? [1/2/3]: ").strip()
            if current_channel in ['1', '2', '3']:
                current_channel = int(current_channel)
                break
            else:
                print("❌ Please enter 1, 2, or 3")
        
        # Choose a different channel for testing
        test_channel = 2 if current_channel == 1 else 1
        print(f"\n✅ Current channel: {current_channel}")
        print(f"✅ Test will switch devices to channel {test_channel} (so you can see the change)\n")
        
        device_labels = {}  # Store what each device is: {dev_idx: 'keyboard'/'mouse'/None}
        
        for i, (dev_idx, feat_idx) in enumerate(results, 1):
            print(f"\n--- Testing Device {i} (Slot {dev_idx}, Feature Index {feat_idx}) ---")
            input("Press ENTER to send test command to this device...")
            
            # Create temporary config for this device
            test_config = Config(
                PROTOCOL=protocol,
                VENDOR_ID=vendor_id,
                PRODUCT_ID=product_id,
                KB_RECEIVER_SLOT=dev_idx,
                MS_RECEIVER_SLOT=dev_idx,
                KEYBOARD_ID=feat_idx,
                MOUSE_ID=feat_idx
            )
            
            # Try to switch to test channel (different from current)
            print(f"  📡 Sending switch to channel {test_channel}...")
            packet = build_channel_switch_packet(test_config, 'keyboard', test_channel)
            success = send_hid_command(test_config, packet, max_retries=2, quiet=True)
            
            if success:
                print(f"  ✅ Command sent successfully")
                print(f"  👀 Did your keyboard or mouse switch to channel {test_channel}?")
                device_type = input(f"     What device is this? [k=keyboard, m=mouse, s=skip]: ").strip().lower()
                
                if device_type == 'k':
                    device_labels[dev_idx] = 'keyboard'
                    print(f"  ✅ Marked as KEYBOARD")
                elif device_type == 'm':
                    device_labels[dev_idx] = 'mouse'
                    print(f"  ✅ Marked as MOUSE")
                else:
                    device_labels[dev_idx] = None
                    print(f"  ⏭️  Skipped")
            else:
                print(f"  ❌ Command failed (device may be off or not responding)")
                device_labels[dev_idx] = None
        
        # Check if user identified both devices during testing
        for dev_idx, feat_idx in results:
            if device_labels.get(dev_idx) == 'keyboard':
                kb_from_test = (dev_idx, feat_idx)
            elif device_labels.get(dev_idx) == 'mouse':
                ms_from_test = (dev_idx, feat_idx)
        
        if kb_from_test is not None and ms_from_test is not None:
            kb_receiver_slot, kb_feature_idx = kb_from_test
            ms_receiver_slot, ms_feature_idx = ms_from_test
            
            print("\n" + "="*70)
            print("✅ Devices identified from testing:")
            print(f"   Keyboard: Slot {kb_receiver_slot}, Feature Index {kb_feature_idx}")
            print(f"   Mouse:    Slot {ms_receiver_slot}, Feature Index {ms_feature_idx}")
            
            confirm = input("\nUse these settings? [Y/n]: ").strip().lower()
            if confirm in ['n', 'no']:
                kb_from_test = None
                ms_from_test = None
    
    # Manual selection if test was skipped or user rejected test results
    if kb_from_test is None or ms_from_test is None:
        print("\n" + "-"*70)
        print("Which device is your KEYBOARD?")
        for i, (dev_idx, feat_idx) in enumerate(results, 1):
            print(f"  {i} = Slot {dev_idx} (feature index {feat_idx})")
        
        while True:
            kb_choice = input(f"\nEnter number [1-{len(results)}]: ").strip()
            try:
                kb_idx = int(kb_choice) - 1
                if 0 <= kb_idx < len(results):
                    kb_receiver_slot, kb_feature_idx = results[kb_idx]
                    break
                else:
                    print(f"❌ Invalid choice. Enter a number between 1 and {len(results)}")
            except ValueError:
                print("❌ Invalid input. Enter a number.")
        
        print(f"✅ Keyboard set to: Slot {kb_receiver_slot}, Feature Index {kb_feature_idx}")
        
        print("\n" + "-"*70)
        print("Which device is your MOUSE?")
        for i, (dev_idx, feat_idx) in enumerate(results, 1):
            if i == kb_idx + 1:
                print(f"  {i} = Slot {dev_idx} (feature index {feat_idx}) [ALREADY USED AS KEYBOARD]")
            else:
                print(f"  {i} = Slot {dev_idx} (feature index {feat_idx})")
        
        while True:
            ms_choice = input(f"\nEnter number [1-{len(results)}]: ").strip()
            try:
                ms_idx = int(ms_choice) - 1
                if 0 <= ms_idx < len(results):
                    ms_receiver_slot, ms_feature_idx = results[ms_idx]
                    if ms_receiver_slot == kb_receiver_slot:
                        print("❌ Cannot use the same device for both keyboard and mouse!")
                        print(f"   You already selected slot {kb_receiver_slot} as the keyboard.")
                        print("   Please choose a different device.")
                        continue
                    break
                else:
                    print(f"❌ Invalid choice. Enter a number between 1 and {len(results)}")
            except ValueError:
                print("❌ Invalid input. Enter a number.")
        
        print(f"✅ Mouse set to: Slot {ms_receiver_slot}, Feature Index {ms_feature_idx}")
    else:
        # Use settings from test
        kb_receiver_slot, kb_feature_idx = kb_from_test
        ms_receiver_slot, ms_feature_idx = ms_from_test
        print("\n✅ Using settings from device testing")
    
    # Create config
    print("\n" + "="*70)
    print("Configuration Summary")
    print("="*70)
    print(f"  Protocol:     {protocol}")
    print(f"  VID:PID:      {vidpid_input}")
    print(f"  Keyboard:     Slot {kb_receiver_slot}, Feature Index {kb_feature_idx} (0x{kb_feature_idx:02X})")
    print(f"  Mouse:        Slot {ms_receiver_slot}, Feature Index {ms_feature_idx} (0x{ms_feature_idx:02X})")
    
    # Note about same feature index
    if kb_feature_idx == ms_feature_idx:
        print(f"\n  ℹ️  Note: Both devices use feature index {kb_feature_idx}. This is normal!")
        print(f"      The SLOT number ({kb_receiver_slot} vs {ms_receiver_slot}) identifies each device.")
    
    # Critical validation: same slot means same device!
    if kb_receiver_slot == ms_receiver_slot:
        log_error("\n❌ ERROR: Keyboard and mouse are assigned to the SAME SLOT!")
        log_error(f"   Both are using slot {kb_receiver_slot}.")
        log_error("   This means you selected the same device twice.")
        log_error("\n   The configuration will NOT work correctly.")
        log_error("   Please run the configuration again and select DIFFERENT devices.")
        return None
    
    print("="*70)
    
    # Offer quick test before saving
    print("\n💡 Would you like to test the configuration before saving?")
    print("   This will switch both devices to verify they respond correctly.")
    test_choice = input("Test now? [y/N]: ").strip().lower()
    
    if test_choice in ['y', 'yes']:
        print("\n🧪 Testing configuration...")
        
        # Ask current channel
        while True:
            current_ch = input("What channel are your devices currently on? [1/2/3]: ").strip()
            if current_ch in ['1', '2', '3']:
                current_ch = int(current_ch)
                break
            else:
                print("❌ Please enter 1, 2, or 3")
        
        # Choose different channel for test
        test_ch = 2 if current_ch == 1 else 1
        print(f"\n✅ Will test by switching to channel {test_ch} (different from current {current_ch})")
        
        test_config = Config(
            PROTOCOL=protocol,
            VENDOR_ID=vendor_id,
            PRODUCT_ID=product_id,
            KB_RECEIVER_SLOT=kb_receiver_slot,
            MS_RECEIVER_SLOT=ms_receiver_slot,
            KEYBOARD_ID=kb_feature_idx,
            MOUSE_ID=ms_feature_idx
        )
        
        print(f"\n  📡 Sending switch to channel {test_ch} for keyboard...")
        kb_packet = build_channel_switch_packet(test_config, 'keyboard', test_ch)
        kb_success = send_hid_command(test_config, kb_packet, max_retries=3, quiet=True)
        
        print(f"  📡 Sending switch to channel {test_ch} for mouse...")
        ms_packet = build_channel_switch_packet(test_config, 'mouse', test_ch)
        ms_success = send_hid_command(test_config, ms_packet, max_retries=3, quiet=True)
        
        if kb_success and ms_success:
            print(f"\n✅ Test successful! Both devices should now be on channel {test_ch}.")
            print("   If your keyboard/mouse switched channels, the configuration is correct.")
            print(f"\n💡 Note: Devices are now on channel {test_ch}. You can switch them back manually")
            print(f"   or save this config and use it to switch to any channel.")
        else:
            print("\n⚠️  Test failed!")
            if not kb_success:
                print("   - Keyboard switch command failed")
            if not ms_success:
                print("   - Mouse switch command failed")
            confirm = input("\nDo you want to save this configuration anyway? [y/N]: ").strip().lower()
            if confirm not in ['y', 'yes']:
                log_error("Configuration cancelled.")
                return None
    
    config = Config(
        PROTOCOL=protocol,
        VENDOR_ID=vendor_id,
        PRODUCT_ID=product_id,
        KB_RECEIVER_SLOT=kb_receiver_slot,
        MS_RECEIVER_SLOT=ms_receiver_slot,
        KEYBOARD_ID=kb_feature_idx,
        MOUSE_ID=ms_feature_idx
    )
    
    return config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Logitech Channel Switcher CLI - Switch keyboard/mouse channels',
        epilog='For first-run setup, run without --quiet to configure devices.'
    )
    parser.add_argument(
        '--channel',
        type=int,
        required=True,
        choices=[1, 2, 3],
        help='Target channel (1, 2, or 3)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress output (for use in shortcuts)'
    )
    
    args = parser.parse_args()
    
    # Load or create configuration
    settings_manager = SettingsManager()
    config = settings_manager.load_config()
    
    if config is None:
        # No config exists - run device discovery
        config = run_device_discovery(quiet=args.quiet)
        if config is None:
            # Discovery failed
            sys.exit(1)
        
        # Save the new config
        try:
            settings_manager.save_config(config)
            log(f"\nConfiguration saved to: {settings_manager.config_path}", args.quiet)
        except Exception as e:
            log_error(f"Failed to save configuration: {e}")
            sys.exit(1)
    
    # Validate configuration
    valid, error_msg = validate_config(config)
    if not valid:
        log_error(f"Invalid configuration: {error_msg}")
        log_error(f"Please check: {settings_manager.config_path}")
        sys.exit(1)
    
    # Switch channels
    success = switch_channel(config, args.channel, quiet=args.quiet)
    
    if success:
        sys.exit(0)
    else:
        sys.exit(2)


if __name__ == '__main__':
    main()
