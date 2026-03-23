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
from hid_protocol import (
    get_hidapi_executable,
    ping_device,
    query_feature_index,
    FEATURE_CHANGE_HOST
)


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

    exec_path = get_hidapi_executable()
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
    print(f'\n--- Step 2: Querying Change Host (0x1814) feature index ---\n')
    results = []
    for dev_idx in devices:
        sys.stdout.write(f'  Device index {dev_idx}: ')
        sys.stdout.flush()
        feat_idx, query_output = query_feature_index(exec_path, vidpid, protocol, dev_idx, FEATURE_CHANGE_HOST)
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
