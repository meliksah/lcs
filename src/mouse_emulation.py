import sys
import random
import time
import math
import logging
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import QTimer, QThread, pyqtSignal, Qt
from PyQt5.QtGui import QCursor
from PyQt5.QtTest import QTest
from scipy import interpolate
import numpy as np

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def point_dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

class MoveMouseThread(QThread):
    def __init__(self):
        super().__init__()

    def run(self):
        logger.debug("Starting mouse movement.")
        cp = random.randint(3, 5)
        x1, y1 = QCursor.pos().x(), QCursor.pos().y()
        screen_width, screen_height = QApplication.desktop().screenGeometry().width(), QApplication.desktop().screenGeometry().height()
        x2 = random.randint(0, screen_width)
        y2 = random.randint(0, screen_height)
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
            QCursor.setPos(*point)
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
        self.keypress_timer.setInterval(30000)  # 30 seconds
        self.keypress_timer.timeout.connect(self.simulate_keypress)

    def start(self):
        logger.debug("Starting MouseEmulation.")
        self.last_mouse_position = QCursor.pos()
        self.user_inactive_time = 0
        self.mouse_activity_timer.start()  # Check for user activity every 10 seconds
        self.keypress_timer.start()  # Start the keypress simulation

    def stop(self):
        logger.debug("Stopping MouseEmulation.")
        self.mouse_activity_timer.stop()
        self.keypress_timer.stop()
        if self.move_mouse_thread and self.move_mouse_thread.isRunning():
            self.move_mouse_thread.terminate()
            self.move_mouse_thread = None

    def check_user_activity(self):
        current_mouse_position = QCursor.pos()
        if self.last_mouse_position != current_mouse_position:
            logger.debug("User activity detected. Resetting inactivity timer.")
            self.user_inactive_time = 0
        else:
            self.user_inactive_time += 10  # Increment by 10 seconds
            if self.user_inactive_time >= 45:  # 45 seconds
                self.start_mouse_movement()
        self.last_mouse_position = current_mouse_position

    def start_mouse_movement(self):
        if not self.move_mouse_thread or not self.move_mouse_thread.isRunning():
            logger.debug("Starting mouse movement.")
            self.move_mouse_thread = MoveMouseThread()  # Create a new thread
            self.move_mouse_thread.start()
            self.user_inactive_time = 0

    def simulate_keypress(self):
        logger.debug("Simulating F15 keypress.")
        QTest.keyPress(QWidget(), Qt.Key_F15)
