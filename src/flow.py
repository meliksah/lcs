import platform
import subprocess
import time
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

from settings import config
from utils import get_absolute_file_data_path, creation_flags


class ChannelSwitchThread(QThread):
    """Run HID commands in a background thread to avoid blocking the GUI."""
    finished = pyqtSignal(bool, bool, str)  # success_ms, success_kb, position

    def __init__(self, ms_cmd, kb_cmd, position):
        super().__init__()
        self._ms_cmd = ms_cmd
        self._kb_cmd = kb_cmd
        self._position = position

    def run(self):
        success_ms = _write_to_adu(self._ms_cmd)
        success_kb = _write_to_adu(self._kb_cmd)
        self.finished.emit(success_ms, success_kb, self._position)


def _get_hidapi_executable_full_path():
    arch = platform.machine()
    system = platform.system().lower()
    executable = None

    if system == 'windows':
        if arch in ('x86_64', 'AMD64'):
            executable = 'hidapitester-windows-x86_64.exe'
    elif system == 'linux':
        if arch == 'x86_64':
            executable = 'hidapitester-linux-x86_64'
        elif arch == 'armv7l':
            executable = 'hidapitester-linux-armv7l'
    elif system == 'darwin':
        if arch == 'arm64':
            executable = 'hidapitester-macos-arm64'
        elif arch == 'x86_64':
            executable = 'hidapitester-macos-x86_64'

    if executable is None:
        raise RuntimeError(f"Unsupported platform: {system} {arch}")

    return get_absolute_file_data_path('hidapitester', executable)


def _build_hidapi_command(msg_str):
    exec_path = _get_hidapi_executable_full_path()
    hex_string = ','.join(f'0x{byte:02X}' for byte in msg_str)
    length = str(len(msg_str))
    usage = '2' if config.PROTOCOL == 'bolt' else '1'
    cmd = [
        exec_path, '--vidpid', f'{config.VENDOR_ID:04X}:{config.PRODUCT_ID:04X}',
        '--usage', usage, '--usagePage', '0xFF00', '--open',
        '--length', length, '--send-output', hex_string,
        '--length', length, '--send-output', hex_string,
    ]
    return cmd


def _write_to_adu(msg_str):
    cmd = _build_hidapi_command(msg_str)
    print('Writing command: {}'.format(' '.join(cmd)))
    max_retries = 10
    success_msg = f"wrote {len(msg_str)} bytes"

    for attempt in range(1, max_retries + 1):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, creationflags=creation_flags)
        except Exception as e:
            print('Error writing command: {}'.format(e))
            if attempt < max_retries:
                time.sleep(0.1)
            continue

        if success_msg in result.stdout:
            return True
        else:
            print(f'Attempt {attempt}: Failed to write command')
            if attempt < max_retries:
                time.sleep(0.1)

    return False


class Flow:
    def __init__(self, screens):
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_position)
        screen_geometries = [s.geometry() for s in screens]
        self.rightmost_edge = max([geometry.x() + geometry.width() for geometry in screen_geometries])
        self.leftmost_edge = min([geometry.x() for geometry in screen_geometries])
        self.topmost_edge = min([geometry.y() for geometry in screen_geometries])
        self.bottommost_edge = max([geometry.y() + geometry.height() for geometry in screen_geometries])
        self.offsets = {
            'left': QPoint(1, 0),
            'right': QPoint(-1, 0),
            'top': QPoint(0, 1),
            'bottom': QPoint(0, -1)
        }
        self._switch_thread = None

    def start(self):
        self.timer.start(300)

    def stop(self):
        self.timer.stop()
        if self._switch_thread and self._switch_thread.isRunning():
            self._switch_thread.wait(3000)

    def _on_switch_finished(self, success_ms, success_kb, position):
        if success_ms and success_kb:
            QCursor.setPos(QCursor.pos() + self.offsets[position])

    def check_mouse_position(self):
        # Don't start a new switch if one is already running
        if self._switch_thread and self._switch_thread.isRunning():
            return

        if config.REQUIRE_CTRL and not (QApplication.keyboardModifiers() & Qt.KeyboardModifier.ControlModifier):
            return

        mouse_pos = QCursor.pos()
        targets = [
            {'position': config.TARGET1_POS, 'channel': 1,
             'mode': config.TARGET1_MODE, 'zone_size': config.TARGET1_ZONE_SIZE, 'zone_anchor': config.TARGET1_ZONE_ANCHOR},
            {'position': config.TARGET2_POS, 'channel': 2,
             'mode': config.TARGET2_MODE, 'zone_size': config.TARGET2_ZONE_SIZE, 'zone_anchor': config.TARGET2_ZONE_ANCHOR},
            {'position': config.TARGET3_POS, 'channel': 3,
             'mode': config.TARGET3_MODE, 'zone_size': config.TARGET3_ZONE_SIZE, 'zone_anchor': config.TARGET3_ZONE_ANCHOR},
        ]
        for target in targets:
            position, channel = target['position'], target['channel']
            # Use -1/+1 margin so edge conditions can actually trigger
            if not (
                (position == 'left' and mouse_pos.x() <= self.leftmost_edge + 1)
                or (position == 'right' and mouse_pos.x() >= self.rightmost_edge - 1)
                or (position == 'top' and mouse_pos.y() <= self.topmost_edge + 1)
                or (position == 'bottom' and mouse_pos.y() >= self.bottommost_edge - 1)
            ):
                continue

            # Zone trigger filtering
            if target['mode'] == 'zone':
                zone_size = target['zone_size']
                anchor = target['zone_anchor']
                if position in ('left', 'right'):
                    if anchor == 'start':
                        in_zone = mouse_pos.y() <= self.topmost_edge + zone_size
                    else:
                        in_zone = mouse_pos.y() >= self.bottommost_edge - zone_size
                else:  # top/bottom
                    if anchor == 'start':
                        in_zone = mouse_pos.x() <= self.leftmost_edge + zone_size
                    else:
                        in_zone = mouse_pos.x() >= self.rightmost_edge - zone_size
                if not in_zone:
                    continue

            if config.PROTOCOL == 'bolt':
                ms_cmd = [0x11, config.MS_RECEIVER_SLOT, config.MOUSE_ID, 0x1E, channel - 1] + [0x00] * 15
                kb_cmd = [0x11, config.KB_RECEIVER_SLOT, config.KEYBOARD_ID, 0x1E, channel - 1] + [0x00] * 15
            else:  # unifying
                ms_cmd = [0x10, config.MS_RECEIVER_SLOT, config.MOUSE_ID, 0x1C, channel - 1, 0x00, 0x00]
                kb_cmd = [0x10, config.KB_RECEIVER_SLOT, config.KEYBOARD_ID, 0x1C, channel - 1, 0x00, 0x00]
            # Run HID commands in a thread
            self._switch_thread = ChannelSwitchThread(ms_cmd, kb_cmd, position)
            self._switch_thread.finished.connect(self._on_switch_finished)
            self._switch_thread.start()
            break
