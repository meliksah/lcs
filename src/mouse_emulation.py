import sys
import random
import time
import math
import logging
import platform

from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QPoint
from PyQt6.QtGui import QCursor
from PyQt6.QtTest import QTest
from scipy import interpolate
import numpy as np

if platform.system() == 'Windows':
    import win32com.client

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def point_dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

class MoveMouseThread(QThread):
    # Use signal to move cursor from the GUI thread
    move_cursor = pyqtSignal(int, int)

    def __init__(self, start_pos, screen_rect):
        super().__init__()
        self._running = True
        self._start_pos = start_pos
        self._screen_rect = screen_rect

    def stop(self):
        self._running = False

    def run(self):
        logger.debug("Starting mouse movement.")
        cp = random.randint(3, 5)
        x1, y1 = self._start_pos.x(), self._start_pos.y()
        # Use provided full virtual desktop geometry
        screen_width = self._screen_rect.width()
        screen_height = self._screen_rect.height()
        x2 = random.randint(self._screen_rect.x(), self._screen_rect.x() + screen_width)
        y2 = random.randint(self._screen_rect.y(), self._screen_rect.y() + screen_height)
        x = np.linspace(x1, x2, num=cp, dtype='int')
        y = np.linspace(y1, y2, num=cp, dtype='int')

        RND = 10
        xr = [random.randint(-RND, RND) for k in range(cp)]
        yr = [random.randint(-RND, RND) for k in range(cp)]
        xr[0] = yr[0] = xr[-1] = yr[-1] = 0
        x += xr
        y += yr

        degree = 3 if cp > 3 else cp - 1
        tck, u = interpolate.splprep([x, y], k=degree)
        u = np.linspace(0, 1, num=2+int(point_dist(x1, y1, x2, y2) / 50.0))
        points = interpolate.splev(u, tck)

        duration = 0.1
        timeout = duration / len(points[0])
        point_list = zip(*(i.astype(int) for i in points))

        for point in point_list:
            if not self._running:
                break
            self.move_cursor.emit(int(point[0]), int(point[1]))
            time.sleep(timeout)
        logger.debug("Mouse movement completed.")

class MouseEmulation:
    def __init__(self):
        self.mouse_activity_timer = QTimer()
        self.mouse_activity_timer.timeout.connect(self.check_user_activity)
        self.mouse_activity_timer.setInterval(10000)
        self.move_mouse_thread = None
        self.last_mouse_position = None
        self.user_inactive_time = 0

        self.keypress_timer = QTimer()
        self.keypress_timer.setInterval(30000)
        self.keypress_timer.timeout.connect(self.simulate_keypress)

        self.is_windows = platform.system() == 'Windows'

    def start(self):
        logger.debug("Starting MouseEmulation.")
        self.last_mouse_position = QCursor.pos()
        self.user_inactive_time = 0
        self.mouse_activity_timer.start()
        self.keypress_timer.start()

    def stop(self):
        logger.debug("Stopping MouseEmulation.")
        self.mouse_activity_timer.stop()
        self.keypress_timer.stop()
        # Graceful thread stop instead of terminate()
        if self.move_mouse_thread and self.move_mouse_thread.isRunning():
            self.move_mouse_thread.stop()
            self.move_mouse_thread.wait(2000)
            self.move_mouse_thread = None

    def check_user_activity(self):
        current_mouse_position = QCursor.pos()
        if self.last_mouse_position != current_mouse_position:
            logger.debug("User activity detected. Resetting inactivity timer.")
            self.user_inactive_time = 0
        else:
            self.user_inactive_time += 10
            if self.user_inactive_time >= 45:
                self.start_mouse_movement()
        self.last_mouse_position = current_mouse_position

    def _on_move_cursor(self, x, y):
        QCursor.setPos(x, y)

    def start_mouse_movement(self):
        if not self.move_mouse_thread or not self.move_mouse_thread.isRunning():
            logger.debug("Starting mouse movement.")
            # Use virtual desktop geometry (all monitors combined)
            screen_rect = QApplication.primaryScreen().virtualGeometry()
            self.move_mouse_thread = MoveMouseThread(QCursor.pos(), screen_rect)
            # Connect signal so cursor is moved from the GUI thread
            self.move_mouse_thread.move_cursor.connect(self._on_move_cursor)
            self.move_mouse_thread.start()
            self.user_inactive_time = 0

    def simulate_keypress(self):
        if self.is_windows:
            logger.debug("Simulating F15 keypress on Windows.")
            shell = win32com.client.Dispatch("WScript.Shell")
            shell.SendKeys('{F15}')
        else:
            logger.debug("Simulating F15 keypress.")
            QTest.keyPress(QWidget(), Qt.Key.Key_F15)
