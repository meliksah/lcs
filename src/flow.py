import os
import platform
import subprocess
from PyQt5.QtCore import QTimer, QPoint
from PyQt5.QtGui import QCursor

from settings import config
from utils import get_absolute_file_data_path, creation_flags
class Flow:
    def __init__(self, desktop):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_position)
        screen_count = desktop.screenCount()
        screen_geometries = [desktop.screen(i).geometry() for i in range(screen_count)]
        self.rightmost_edge = max([geometry.x() + geometry.width() for geometry in screen_geometries])-1
        self.leftmost_edge = min([geometry.x() for geometry in screen_geometries])
        self.topmost_edge = min([geometry.y() for geometry in screen_geometries])
        self.bottommost_edge = max([geometry.y() + geometry.height() for geometry in screen_geometries])-1
        self.offsets = {
            'left': QPoint(1, 0),
            'right': QPoint(-1, 0),
            'top': QPoint(0, 1),
            'bottom': QPoint(0, -1)
        }

    def start(self):
        self.timer.start(300)

    def stop(self):
        self.timer.stop()
    def get_hidapi_executable_full_path(self):
        # Determine the system's architecture and platform
        arch = platform.machine()
        system = platform.system().lower()

        # Select the appropriate executable
        if system == 'windows':
            executable = 'hidapitester-windows-x86_64.exe'
        elif system == 'linux':
            if arch == 'x86_64':
                executable = 'hidapitester-linux-x86_64'
            elif arch == 'armv7l':
                executable = 'hidapitester-linux-armv7l'
        elif system == 'darwin':  # macOS
            if arch == 'arm64':
                executable = 'hidapitester-macos-arm64'
            elif arch == 'x86_64':
                executable = 'hidapitester-macos-x86_64'

        return get_absolute_file_data_path('hidapitester', executable)
    def build_hidapi_command(self, msg_str): 
        exec_path = self.get_hidapi_executable_full_path()
        cmd = [exec_path, '--vidpid', f'{config.VENDOR_ID:04X}:{config.PRODUCT_ID:04X}','--usage','1','--usagePage','0xFF00','--open', '--length', '7', '--send-output']
        hex_string = ','.join(f'0x{byte:02X}' for byte in msg_str)
        cmd.append(hex_string)
        cmd.append('--length')
        cmd.append('7')
        cmd.append('--send-output')
        cmd.append(hex_string)
        return cmd

    def write_to_adu(self, msg_str):
        cmd = self.build_hidapi_command(msg_str)
        print('Writing command: {}'.format(' '.join(cmd)))
        max_retries = 10
        success_msg = "wrote 7 bytes"

        for attempt in range(1, max_retries + 1):
            try:
                # Run the executable with the command string as arguments
                result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)
            except Exception as e:
                print('Error writing command: {}'.format(e))
                continue

            if success_msg in result.stdout:
                return True
            else:
                print(f'Attempt {attempt}: Failed to write command')

        return False
    def get_kb_cmd(self, target_channel):
        return [0x10, config.KB_RECEIVER_SLOT, config.KEYBOARD_ID, 0x1c, target_channel - 1, 0x00, 0x00]

    def get_ms_cmd(self, target_channel):
        return [0x10, config.MS_RECEIVER_SLOT, config.MOUSE_ID, 0x1c, target_channel - 1, 0x00, 0x00]

    def check_mouse_position(self):
        mouse_pos = QCursor.pos()
        targets = [
            {'position': config.TARGET1_POS, 'channel': 1},
            {'position': config.TARGET2_POS, 'channel': 2},
            {'position': config.TARGET3_POS, 'channel': 3},
        ]
        for target in targets:
            position, channel = target['position'], target['channel']
            if (
                (position == 'left' and mouse_pos.x() <= self.leftmost_edge)
                or (position == 'right' and mouse_pos.x() >= self.rightmost_edge)
                or (position == 'top' and mouse_pos.y() <= self.topmost_edge)
                or (position == 'bottom' and mouse_pos.y() >= self.bottommost_edge)
            ):
                success_ms = self.write_to_adu(self.get_ms_cmd(channel))
                success_kb = self.write_to_adu(self.get_kb_cmd(channel))
                if success_ms and success_kb:
                    QCursor.setPos(QCursor.pos() + self.offsets[position])
                    break

