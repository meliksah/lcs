"""
Probe Logitech Bolt/Unifying receiver to discover paired devices
and their Change Host feature index.

Step 1: Ping device indices 1-6 to find paired devices.
Step 2: Query each device for the Change Host (0x1814) feature index.

Run from project root:

    python tools/probe_devices.py [--protocol bolt|unifying] [VID:PID]

Default: Bolt protocol with VID:PID 046D:C548.
For Unifying: python tools/probe_devices.py --protocol unifying 046D:C52B
"""

import subprocess
import sys
import os

VERSION = '0.5'

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
from utils import get_absolute_file_data_path, creation_flags


def get_hidapitester():
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


def hid_send_receive(exec_path, vidpid, protocol, msg, force_short=False):
    """Send a HID++ message and return (success, raw_output, response_bytes).

    force_short: use short endpoint (usage 1, 7 bytes) even for Bolt.
    """
    if force_short or protocol != 'bolt':
        if len(msg) < 7:
            msg = msg + [0x00] * (7 - len(msg))
        length = '7'
        usage = '1'
    else:
        if len(msg) < 20:
            msg = msg + [0x00] * (20 - len(msg))
        length = '20'
        usage = '2'

    hex_string = ','.join(f'0x{b:02X}' for b in msg)
    cmd = [
        exec_path, '--vidpid', vidpid,
        '--usage', usage, '--usagePage', '0xFF00', '--open',
        '--length', length, '--send-output', hex_string,
        '--length', length, '--send-output', hex_string,
        '--timeout', '2000',
        '--length', length, '--read-input',
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True,
                                timeout=3, creationflags=creation_flags)
        output = result.stdout + result.stderr
        # Parse response bytes from output
        response = parse_response_bytes(output)
        if response:
            return True, output, response
        # Fallback: check if hidapitester read any bytes (even if not printed)
        if 'read 7 bytes' in output or 'read 20 bytes' in output:
            return True, output, None
        return False, output, None
    except subprocess.TimeoutExpired:
        return False, 'timeout', None
    except Exception as e:
        return False, str(e), None


def parse_response_bytes(output):
    """Extract response bytes from hidapitester read output.

    hidapitester format:
        Reading N-byte input report ...read N bytes:
         AA BB CC DD ...
    Hex bytes are on the NEXT line after 'read N bytes:'.
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
    """HID++ 2.0 ping: IRoot (feature 0x00), function 1 (ping), swID=0x0F.

    Tries short endpoint first. For Bolt, also tries long endpoint if short
    returns no data (Bolt devices may only respond on the long endpoint).
    """
    # Try short ping first
    msg_short = [0x10, device_index, 0x00, 0x1F, 0x00, 0x00, 0xAA]
    ok, output, response = hid_send_receive(exec_path, vidpid, protocol, msg_short, force_short=True)
    if ok:
        # Check if it's an error response (0x8F = HID++ error, not a real device)
        if response and len(response) >= 3 and response[2] == 0x8F:
            return False, output, response
        return True, output, response

    # For Bolt, try long endpoint if short didn't work
    if protocol == 'bolt':
        msg_long = [0x11, device_index, 0x00, 0x1F] + [0x00] * 15 + [0xAA]
        ok, output, response = hid_send_receive(exec_path, vidpid, protocol, msg_long)
        if ok:
            if response and len(response) >= 3 and response[2] == 0x8F:
                return False, output, response
            return True, output, response

    return False, output, response


def query_feature_index(exec_path, vidpid, protocol, device_index, feature_id):
    """Query IRoot.getFeature(featureID) to find a feature's index.

    IRoot is always at feature index 0x00, function 0 = getFeature.
    Sends [report_id, device_index, 0x00, 0x0F, feat_hi, feat_lo, ...]
    Response byte 4 contains the feature index (0 = not found).
    """
    feat_hi = (feature_id >> 8) & 0xFF
    feat_lo = feature_id & 0xFF
    if protocol == 'bolt':
        msg = [0x11, device_index, 0x00, 0x0F, feat_hi, feat_lo]
    else:
        msg = [0x10, device_index, 0x00, 0x0F, feat_hi, feat_lo]

    ok, output, response = hid_send_receive(exec_path, vidpid, protocol, msg)
    if ok and response and len(response) > 4:
        return response[4], output  # feature index
    return None, output


def main():
    protocol = 'bolt'
    vidpid = '046D:C548'

    debug = False
    args = sys.argv[1:]
    if '--debug' in args:
        debug = True
        args.remove('--debug')
    if '--protocol' in args:
        idx = args.index('--protocol')
        protocol = args[idx + 1]
        args = args[:idx] + args[idx + 2:]

    if args:
        vidpid = args[0]

    if protocol == 'unifying' and vidpid == '046D:C548':
        vidpid = '046D:C52B'

    exec_path = get_hidapitester()
    print(f'Probe v{VERSION} — Probing receiver {vidpid} (protocol: {protocol})')
    print(f'Using: {exec_path}')

    # Step 1: Ping device indices 0-8
    print(f'\n--- Step 1: Pinging device indices 0-8 ---\n')
    devices = []
    for dev_idx in range(0, 9):
        sys.stdout.write(f'\r  Pinging device index {dev_idx}...')
        sys.stdout.flush()
        ok, output, response = ping_device(exec_path, vidpid, protocol, dev_idx)
        if ok:
            sys.stdout.write(f'\r  Device index {dev_idx}: FOUND   \n')
            if debug:
                print(f'    Raw: {output.strip()}')
            devices.append(dev_idx)
        else:
            sys.stdout.write(f'\r  Device index {dev_idx}: -       \n')
            if debug:
                print(f'    Raw: {output.strip()}')

    if not devices:
        print('\nNo devices found. Check that:')
        print('  - Receiver is plugged in')
        print('  - Keyboard/mouse are on and paired')
        print(f'  - VID:PID {vidpid} is correct')
        print(f'  - Protocol "{protocol}" matches your receiver')
        return

    # Step 2: Query Change Host (0x1814) feature index for each device
    CHANGE_HOST = 0x1814
    print(f'\n--- Step 2: Querying Change Host (0x1814) feature index ---\n')
    results = []
    for dev_idx in devices:
        sys.stdout.write(f'  Device index {dev_idx}: ')
        sys.stdout.flush()
        feat_idx, query_output = query_feature_index(exec_path, vidpid, protocol, dev_idx, CHANGE_HOST)
        if feat_idx and feat_idx > 0:
            print(f'Change Host feature at index {feat_idx} (0x{feat_idx:02X})')
            results.append((dev_idx, feat_idx))
        else:
            print('Change Host feature not found')
        if debug and query_output:
            print(f'    Raw: {query_output.strip()}')

    # Summary
    print(f'\n--- Summary ---\n')
    print(f'  Protocol:   {protocol}')
    print(f'  VID:PID:    {vidpid}')
    print()
    if results:
        for dev_idx, feat_idx in results:
            print(f'  Device index (RECEIVER_SLOT): {dev_idx}')
            print(f'  Change Host feature index (DEVICE_ID): {feat_idx} (0x{feat_idx:02X})')
            print()
        print('Use these values in config.json:')
        if len(results) >= 2:
            print(f'  KB_RECEIVER_SLOT: {results[0][0]}, KEYBOARD_ID: {results[0][1]}')
            print(f'  MS_RECEIVER_SLOT: {results[1][0]}, MOUSE_ID: {results[1][1]}')
        elif len(results) == 1:
            print(f'  RECEIVER_SLOT: {results[0][0]}, DEVICE_ID: {results[0][1]}')
    else:
        print('  No devices with Change Host support found.')


if __name__ == '__main__':
    main()
