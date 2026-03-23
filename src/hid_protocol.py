"""HID++ protocol definitions and utilities for Logitech devices.

Consolidates HID communication logic previously duplicated across
flow.py, cli_switcher.py, and probe_devices.py.
"""

import subprocess
import time
import platform
from utils import get_absolute_file_data_path, creation_flags

# Protocol constants
BOLT_REPORT_ID = 0x11
UNIFYING_REPORT_ID = 0x10
BOLT_CHANGE_HOST_FUNC = 0x1E
UNIFYING_CHANGE_HOST_FUNC = 0x1C
BOLT_PACKET_LENGTH = 20
UNIFYING_PACKET_LENGTH = 7

# Feature IDs
FEATURE_CHANGE_HOST = 0x1814
FEATURE_IROOT = 0x00

# HID++ functions
FUNC_GET_FEATURE = 0x0F
FUNC_PING = 0x1F

# Default VID:PIDs
DEFAULT_BOLT_VIDPID = ('046D', 'C548')
DEFAULT_UNIFYING_VIDPID = ('046D', 'C52B')


def get_hidapi_executable():
    """Get platform-specific hidapitester binary path.
    
    Consolidates implementations from flow.py, cli_switcher.py, and probe_devices.py.
    """
    system = platform.system().lower()
    arch = platform.machine()
    
    if system == 'windows':
        return get_absolute_file_data_path('hidapitester', 'hidapitester-windows-x86_64.exe')
    elif system == 'darwin':
        name = 'hidapitester-macos-arm64' if arch == 'arm64' else 'hidapitester-macos-x86_64'
        return get_absolute_file_data_path('hidapitester', name)
    else:  # linux
        name = 'hidapitester-linux-armv7l' if arch == 'armv7l' else 'hidapitester-linux-x86_64'
        return get_absolute_file_data_path('hidapitester', name)


def format_vidpid(vendor_id, product_id):
    """Format VID:PID as hex string (e.g., '046D:C548')."""
    return f'{int(vendor_id, 16) if isinstance(vendor_id, str) else vendor_id:04X}:{int(product_id, 16) if isinstance(product_id, str) else product_id:04X}'


def build_channel_switch_packet(protocol, receiver_slot, feature_index, channel):
    """Build HID++ packet for channel switching.
    
    Args:
        protocol: 'bolt' or 'unifying'
        receiver_slot: Device slot on receiver (1-6)
        feature_index: Change Host feature index
        channel: Target channel (1-3)
        
    Returns:
        List of bytes representing the HID++ packet
    """
    channel_byte = channel - 1  # Channels are 0-indexed in protocol
    
    if protocol == 'bolt':
        # Bolt: 20-byte packet
        packet = [BOLT_REPORT_ID, receiver_slot, feature_index, BOLT_CHANGE_HOST_FUNC, channel_byte] + [0x00] * 15
    else:  # unifying
        # Unifying: 7-byte packet
        packet = [UNIFYING_REPORT_ID, receiver_slot, feature_index, UNIFYING_CHANGE_HOST_FUNC, channel_byte, 0x00, 0x00]
    
    return packet


def build_hidapi_command(vendor_id, product_id, protocol, msg_bytes, exec_path=None):
    """Build hidapitester command array.
    
    Consolidates command building from flow.py and cli_switcher.py.
    
    Args:
        vendor_id: Vendor ID (string like '046D' or int)
        product_id: Product ID (string like 'C548' or int)
        protocol: 'bolt' or 'unifying'
        msg_bytes: Message bytes to send
        exec_path: Path to hidapitester (optional, auto-detected if None)
        
    Returns:
        List of command arguments for subprocess
    """
    if exec_path is None:
        exec_path = get_hidapi_executable()
    
    vidpid = format_vidpid(vendor_id, product_id)
    hex_string = ','.join(f'0x{byte:02X}' for byte in msg_bytes)
    length = str(len(msg_bytes))
    usage = '2' if protocol == 'bolt' else '1'
    
    return [
        exec_path, '--vidpid', vidpid,
        '--usage', usage, '--usagePage', '0xFF00', '--open',
        '--length', length, '--send-output', hex_string,
        '--length', length, '--send-output', hex_string,  # Send twice for device wake
    ]


def send_hid_command(cmd, success_indicator='wrote', max_retries=3, timeout=5, quiet=False):
    """Send HID command with retries.
    
    Consolidates execution logic from flow.py and cli_switcher.py.
    
    Args:
        cmd: Command array for subprocess
        success_indicator: String to look for in output to indicate success
        max_retries: Maximum retry attempts
        timeout: Timeout in seconds per attempt
        quiet: Suppress error output
        
    Returns:
        True on success, False on failure
    """
    for attempt in range(max_retries):
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                creationflags=creation_flags
            )
            
            output = result.stdout + result.stderr
            
            # Check for success indicator
            if success_indicator in output.lower():
                return True
                
        except subprocess.TimeoutExpired:
            if not quiet:
                print(f'  Attempt {attempt + 1}/{max_retries} timed out')
        except Exception as e:
            if not quiet:
                print(f'  Attempt {attempt + 1}/{max_retries} failed: {e}')
        
        if attempt < max_retries - 1:
            time.sleep(0.5)  # Brief delay between retries
    
    return False


def send_hid_receive(exec_path, vidpid, protocol, msg_bytes, force_short=False, timeout=2):
    """Send HID command and parse response.
    
    From probe_devices.py with enhancements.
    
    Args:
        exec_path: Path to hidapitester executable
        vidpid: VID:PID string (e.g., '046D:C548')
        protocol: 'bolt' or 'unifying'
        msg_bytes: Message bytes to send (list of ints)
        force_short: Force short endpoint (7 bytes, usage 1) even for Bolt
        timeout: Timeout in milliseconds
        
    Returns:
        Tuple of (success, raw_output, response_bytes)
    """
    # Determine packet length and usage
    if force_short or protocol != 'bolt':
        if len(msg_bytes) < UNIFYING_PACKET_LENGTH:
            msg_bytes = msg_bytes + [0x00] * (UNIFYING_PACKET_LENGTH - len(msg_bytes))
        length = str(UNIFYING_PACKET_LENGTH)
        usage = '1'
    else:
        if len(msg_bytes) < BOLT_PACKET_LENGTH:
            msg_bytes = msg_bytes + [0x00] * (BOLT_PACKET_LENGTH - len(msg_bytes))
        length = str(BOLT_PACKET_LENGTH)
        usage = '2'
    
    hex_string = ','.join(f'0x{b:02X}' for b in msg_bytes)
    cmd = [
        exec_path, '--vidpid', vidpid,
        '--usage', usage, '--usagePage', '0xFF00', '--open',
        '--length', length, '--send-output', hex_string,
        '--length', length, '--send-output', hex_string,  # Send twice
        '--timeout', str(timeout),
        '--length', length, '--read-input',
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout / 1000 + 1,  # Convert ms to seconds + buffer
            creationflags=creation_flags
        )
        output = result.stdout + result.stderr
        
        # Parse response bytes from output
        response = parse_response_bytes(output)
        if response:
            return True, output, response
        
        # Fallback: check if hidapitester read any bytes
        if 'read 7 bytes' in output or 'read 20 bytes' in output:
            return True, output, None
        
        return False, output, None
        
    except subprocess.TimeoutExpired:
        return False, 'timeout', None
    except Exception as e:
        return False, str(e), None


def parse_response_bytes(output):
    """Extract response bytes from hidapitester read output.
    
    From probe_devices.py.
    
    hidapitester format:
        Reading N-byte input report ...read N bytes:
         AA BB CC DD ...
    Hex bytes are on the NEXT line after 'read N bytes:'.
    
    Args:
        output: stdout/stderr text from hidapitester
        
    Returns:
        List of response bytes (ints), or None if not found
    """
    lines = output.split('\n')
    for i, line in enumerate(lines):
        if 'read' in line and 'bytes' in line and 'read 0 bytes' not in line:
            # Check same line after colon
            parts = line.split(':')
            if len(parts) > 1:
                hex_part = parts[-1].strip()
                if hex_part:
                    try:
                        return [int(b, 16) for b in hex_part.split()]
                    except ValueError:
                        pass
            
            # Check next line for hex bytes
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line:
                    try:
                        return [int(b, 16) for b in next_line.split()]
                    except ValueError:
                        pass
    
    return None


def ping_device(exec_path, vidpid, protocol, device_index):
    """HID++ 2.0 ping to check if device exists.
    
    From probe_devices.py.
    
    Sends IRoot (feature 0x00) ping (function 0x1F) with swID=0x0F.
    Tries short endpoint first. For Bolt, also tries long endpoint if short fails.
    
    Args:
        exec_path: Path to hidapitester
        vidpid: VID:PID string
        protocol: 'bolt' or 'unifying'
        device_index: Device slot to ping (0-8)
        
    Returns:
        Tuple of (success, raw_output, response_bytes)
    """
    # Try short ping first
    msg_short = [UNIFYING_REPORT_ID, device_index, FEATURE_IROOT, FUNC_PING, 0x00, 0x00, 0xAA]
    ok, output, response = send_hid_receive(exec_path, vidpid, protocol, msg_short, force_short=True)
    
    if ok:
        # Check if it's an error response (0x8F = HID++ error)
        if response and len(response) >= 3 and response[2] == 0x8F:
            return False, output, response
        return True, output, response
    
    # For Bolt, try long endpoint if short didn't work
    if protocol == 'bolt':
        msg_long = [BOLT_REPORT_ID, device_index, FEATURE_IROOT, FUNC_PING] + [0x00] * 15 + [0xAA]
        ok, output, response = send_hid_receive(exec_path, vidpid, protocol, msg_long)
        
        if ok:
            if response and len(response) >= 3 and response[2] == 0x8F:
                return False, output, response
            return True, output, response
    
    return False, output, response


def query_feature_index(exec_path, vidpid, protocol, device_index, feature_id):
    """Query IRoot.getFeature to find a feature's index.
    
    From probe_devices.py.
    
    IRoot is always at feature index 0x00, function 0 = getFeature.
    
    Args:
        exec_path: Path to hidapitester
        vidpid: VID:PID string
        protocol: 'bolt' or 'unifying'
        device_index: Device slot
        feature_id: Feature ID to query (e.g., 0x1814 for Change Host)
        
    Returns:
        Tuple of (feature_index, raw_output). feature_index is None if not found.
    """
    feat_hi = (feature_id >> 8) & 0xFF
    feat_lo = feature_id & 0xFF
    
    if protocol == 'bolt':
        msg = [BOLT_REPORT_ID, device_index, FEATURE_IROOT, FUNC_GET_FEATURE, feat_hi, feat_lo]
    else:
        msg = [UNIFYING_REPORT_ID, device_index, FEATURE_IROOT, FUNC_GET_FEATURE, feat_hi, feat_lo]
    
    ok, output, response = send_hid_receive(exec_path, vidpid, protocol, msg)
    
    if ok and response and len(response) > 4:
        return response[4], output  # Feature index is in byte 4
    
    return None, output
