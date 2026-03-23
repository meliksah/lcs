import time
from PyQt6.QtCore import Qt, QTimer, QPoint, QThread, pyqtSignal
from PyQt6.QtGui import QCursor
from PyQt6.QtWidgets import QApplication

from settings import config
from hid_protocol import (
    get_hidapi_executable,
    build_channel_switch_packet,
    build_hidapi_command,
    send_hid_command
)


class ChannelSwitchThread(QThread):
    """Run HID commands in a background thread to avoid blocking the GUI."""
    finished = pyqtSignal(bool, bool, str)  # success_ms, success_kb, position

    def __init__(self, ms_cmd, kb_cmd, position):
        super().__init__()
        self._ms_cmd = ms_cmd
        self._kb_cmd = kb_cmd
        self._position = position

    def run(self):
        success_ms = _send_hid_packet(self._ms_cmd)
        success_kb = _send_hid_packet(self._kb_cmd)
        self.finished.emit(success_ms, success_kb, self._position)


def _send_hid_packet(msg_bytes):
    """Send HID packet with retries using consolidated protocol functions."""
    cmd = build_hidapi_command(
        config.VENDOR_ID,
        config.PRODUCT_ID,
        config.PROTOCOL,
        msg_bytes
    )
    print('Writing command: {}'.format(' '.join(cmd)))
    return send_hid_command(cmd, success_indicator='wrote', max_retries=10)


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
# Build channel switch packets using protocol functions
            ms_cmd = build_channel_switch_packet(
                config.PROTOCOL,
                config.MS_RECEIVER_SLOT,
                config.MOUSE_ID,
                channel
            )
            kb_cmd = build_channel_switch_packet(
                config.PROTOCOL,
                config.KB_RECEIVER_SLOT,
                config.KEYBOARD_ID,
                channel
            )
            