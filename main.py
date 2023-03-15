from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QPushButton, QVBoxLayout, QSystemTrayIcon, QMenu, QMessageBox, QComboBox, QDesktopWidget
from PyQt5.QtGui import QIcon, QKeySequence, QCursor
from PyQt5.QtCore import Qt, QTimer
import sys
import os
import json
import platform
import subprocess

def getAbsoluteFileDataPath(fileName):
    return os.path.join(os.path.dirname(__file__), fileName)

VENDOR_ID = 0x046D
PRODUCT_ID = 0xC52B
KB_RECEIVER_SLOT = 0x01  # Change to your desired value
MS_RECEIVER_SLOT = 0x02  # Change to your desired value

KEYBOARD_ID = 0x09  # Change to your desired value
MOUSE_ID = 0x0a  # Change to your desired value
TARGET_CHANNEL = 0x00  # Change to your desired value
TARGET1_POS="right"
TARGET2_POS="none"
TARGET3_POS="none"
CONFIG_FILE_NAME = 'config.json'
CONFIG_FILE = getAbsoluteFileDataPath(CONFIG_FILE_NAME)

app = QApplication(sys.argv)
desktop = QDesktopWidget()
screen_count = desktop.screenCount()
rightmost_screen = desktop.screen(screen_count - 1)
leftmost_screen = desktop.screen(0)

rightmost_edge = rightmost_screen.geometry().right()
leftmost_edge = leftmost_screen.geometry().left()

topmost_screen = desktop.screen(0)
topmost_edge = topmost_screen.geometry().top()

bottommost_screen = desktop.screen(screen_count - 1)
bottommost_edge = bottommost_screen.geometry().bottom()

def getKbCmd(target_channel):
    return [0x10, KB_RECEIVER_SLOT, KEYBOARD_ID, 0x1c, target_channel - 1, 0x00, 0x00]

def getMsCmd(target_channel):
    return [0x10, MS_RECEIVER_SLOT, MOUSE_ID, 0x1c, target_channel - 1, 0x00, 0x00]

def save_config():
    config = {
        'VENDOR_ID': VENDOR_ID,
        'PRODUCT_ID': PRODUCT_ID,
        'KB_RECEIVER_SLOT': KB_RECEIVER_SLOT,
        'MS_RECEIVER_SLOT': MS_RECEIVER_SLOT,
        'KEYBOARD_ID': KEYBOARD_ID,
        'MOUSE_ID': MOUSE_ID,
        'TARGET1_POS': TARGET1_POS,
        'TARGET2_POS': TARGET2_POS,
        'TARGET3_POS': TARGET3_POS,
    }
    print(config)
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
    global KB_CMD, MOUSE_CMD
    KB_CMD = [0x10, KB_RECEIVER_SLOT, KEYBOARD_ID, 0x1c, TARGET_CHANNEL, 0x00, 0x00]
    MOUSE_CMD = [0x10, MS_RECEIVER_SLOT, MOUSE_ID, 0x1c, TARGET_CHANNEL, 0x00, 0x00]

def load_config():
    print("load_config started")
    if not os.path.isfile(CONFIG_FILE):
        return

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        save_config()
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)

    global VENDOR_ID, PRODUCT_ID, KB_RECEIVER_SLOT, MS_RECEIVER_SLOT, KEYBOARD_ID, MOUSE_ID, TARGET1_POS, TARGET2_POS, TARGET3_POS
    VENDOR_ID = config.get('VENDOR_ID', VENDOR_ID)
    PRODUCT_ID = config.get('PRODUCT_ID', PRODUCT_ID)
    KB_RECEIVER_SLOT = config.get('KB_RECEIVER_SLOT', KB_RECEIVER_SLOT)
    MS_RECEIVER_SLOT = config.get('MS_RECEIVER_SLOT', MS_RECEIVER_SLOT)
    KEYBOARD_ID = config.get('KEYBOARD_ID', KEYBOARD_ID)
    MOUSE_ID = config.get('MOUSE_ID', MOUSE_ID)
    TARGET1_POS = config.get('TARGET1_POS', MS_RECEIVER_SLOT)
    TARGET2_POS = config.get('TARGET2_POS', KEYBOARD_ID)
    TARGET3_POS = config.get('TARGET3_POS', MOUSE_ID)
    print("load_config finished")

load_config()

KB_CMD = [0x10, KB_RECEIVER_SLOT, KEYBOARD_ID, 0x1c, TARGET_CHANNEL, 0x00, 0x00]
MOUSE_CMD = [0x10, MS_RECEIVER_SLOT, MOUSE_ID, 0x1c, TARGET_CHANNEL, 0x00, 0x00]

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        print("SettingsDialog init")
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon(getAbsoluteFileDataPath('icon.png')))
        self.setWindowFlags(Qt.WindowCloseButtonHint)

        self.vendor_id_edit = QLineEdit(f'{VENDOR_ID:04X}')
        self.product_id_edit = QLineEdit(f'{PRODUCT_ID:04X}')
        self.kb_receiver_slot_edit = QLineEdit(f'{KB_RECEIVER_SLOT:02X}')
        self.ms_receiver_slot_edit = QLineEdit(f'{MS_RECEIVER_SLOT:02X}')
        self.keyboard_id_edit = QLineEdit(f'{KEYBOARD_ID:02X}')
        self.mouse_id_edit = QLineEdit(f'{MOUSE_ID:02X}')

        self.target1_combo = QComboBox()
        self.target1_combo.addItems(['top', 'bottom', 'right', 'left', 'none'])
        target1_index = self.target1_combo.findText(TARGET1_POS)
        self.target1_combo.setCurrentIndex(target1_index)
        self.target2_combo = QComboBox()
        self.target2_combo.addItems(['top', 'bottom', 'right', 'left', 'none'])
        target2_index = self.target2_combo.findText(TARGET2_POS)
        self.target2_combo.setCurrentIndex(target2_index)
        self.target3_combo = QComboBox()
        self.target3_combo.addItems(['top', 'bottom', 'right', 'left', 'none'])
        target3_index = self.target3_combo.findText(TARGET3_POS)
        self.target3_combo.setCurrentIndex(target3_index)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_config)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Vendor ID'))
        layout.addWidget(self.vendor_id_edit)
        layout.addWidget(QLabel('Product ID'))
        layout.addWidget(self.product_id_edit)
        layout.addWidget(QLabel('Keyboard Receiver Slot'))
        layout.addWidget(self.kb_receiver_slot_edit)
        layout.addWidget(QLabel('Mouse Receiver Slot'))
        layout.addWidget(self.ms_receiver_slot_edit)
        layout.addWidget(QLabel('Keyboard ID'))
        layout.addWidget(self.keyboard_id_edit)
        layout.addWidget(QLabel('Mouse ID'))
        layout.addWidget(self.mouse_id_edit)
        layout.addWidget(QLabel('Target 1'))
        layout.addWidget(self.target1_combo)
        layout.addWidget(QLabel('Target 2'))
        layout.addWidget(self.target2_combo)
        layout.addWidget(QLabel('Target 3'))
        layout.addWidget(self.target3_combo)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.setGeometry(350, 350, 300, 450)



    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message', 'Do you want to save the changes?', QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            save_config()
            load_config()
        else:
            load_config()
        event.ignore()
        self.hide()

    def save_config(self):
        global VENDOR_ID, PRODUCT_ID, KB_RECEIVER_SLOT, MS_RECEIVER_SLOT, KEYBOARD_ID, MOUSE_ID, TARGET1_POS, TARGET2_POS, TARGET3_POS

        VENDOR_ID = int(self.vendor_id_edit.text(), 16)
        PRODUCT_ID = int(self.product_id_edit.text(), 16)
        KB_RECEIVER_SLOT = int(self.kb_receiver_slot_edit.text(), 16)
        MS_RECEIVER_SLOT = int(self.ms_receiver_slot_edit.text(), 16)
        KEYBOARD_ID = int(self.keyboard_id_edit.text(), 16)
        MOUSE_ID = int(self.mouse_id_edit.text(), 16)
        TARGET1_POS = self.target1_combo.currentText()
        TARGET2_POS = self.target2_combo.currentText()
        TARGET3_POS = self.target3_combo.currentText()

def write_to_adu(msg_str):

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

    # Build the command string
    exec_path = os.path.join(os.path.dirname(__file__), executable)
    cmd = [exec_path, '--vidpid', f'{VENDOR_ID:04X}:{PRODUCT_ID:04X}', '--open', '--length', '7', '--send-output']
    hex_string = ','.join(f'0x{byte:02X}' for byte in msg_str)
    cmd.append(hex_string)

    print('Writing command: {}'.format(' '.join(cmd)))
    max_retries = 10
    success_msg = "wrote 7 bytes"

    for attempt in range(1, max_retries + 1):
        try:
            # Run the executable with the command string as arguments
            result = subprocess.run(cmd, capture_output=True, text=True)
        except Exception as e:
            print('Error writing command: {}'.format(e))
            continue

        if success_msg in result.stdout:
            return True
        else:
            print(f'Attempt {attempt}: Failed to write command')

    return False

class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        print("SystemTrayIcon init")
        self.menu = QMenu(parent)
        self.activate_action = self.menu.addAction('Activate')
        self.activate_action.setCheckable(True)
        self.activate_action.setChecked(False)
        self.activate_action.triggered.connect(self.icon_activated)
        self.settings_action = self.menu.addAction('Settings')
        self.settings_action.triggered.connect(self.show_settings_dialog)
        self.menu.addAction('Quit', self.quit)
        self.setContextMenu(self.menu)
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_mouse_position)
        



    def icon_activated(self, checked):
        if checked:
            self.timer.start(300)  # Check mouse position every 1 second
        else:
            self.timer.stop()

            # Check if mouse position falls under target positions
    def check_mouse_position(self):
        mouse_pos = QCursor.pos()
        successKb = False
        successMs = False
        if TARGET1_POS == 'left' and mouse_pos.x() <= leftmost_edge:
            successMs = write_to_adu( getMsCmd(1))
            successKb = write_to_adu( getKbCmd(1))

        elif TARGET1_POS == 'right' and mouse_pos.x() >= rightmost_edge:
            successMs = write_to_adu( getMsCmd(1))
            successKb = write_to_adu( getKbCmd(1))

        elif TARGET1_POS == 'top' and mouse_pos.y() <= topmost_edge:
            successMs = write_to_adu( getMsCmd(1))
            successKb = write_to_adu( getKbCmd(1))

        elif TARGET1_POS == 'bottom' and mouse_pos.y() >= bottommost_edge:
            successMs = write_to_adu( getMsCmd(1))
            successKb = write_to_adu( getKbCmd(1))

        elif TARGET2_POS == 'left' and mouse_pos.x() <= leftmost_edge:
            successMs = write_to_adu( getMsCmd(2))
            successKb = write_to_adu( getKbCmd(2))

        elif TARGET2_POS == 'right' and mouse_pos.x() >= rightmost_edge:
            successMs = write_to_adu( getMsCmd(2))
            successKb = write_to_adu( getKbCmd(2))

        elif TARGET2_POS == 'top' and mouse_pos.y() <= topmost_edge:
            successMs = write_to_adu( getMsCmd(2))
            successKb = write_to_adu( getKbCmd(2))

        elif TARGET2_POS == 'bottom' and mouse_pos.y() >= bottommost_edge:
            successMs = write_to_adu( getMsCmd(2))
            successKb = write_to_adu( getKbCmd(2))

        elif TARGET3_POS == 'left' and mouse_pos.x() <= leftmost_edge:
            successMs = write_to_adu( getMsCmd(3))
            successKb = write_to_adu( getKbCmd(3))

        elif TARGET3_POS == 'right' and mouse_pos.x() >= rightmost_edge:
            successMs = write_to_adu( getMsCmd(3))
            successKb = write_to_adu( getKbCmd(3))

        elif TARGET3_POS == 'top' and mouse_pos.y() <= topmost_edge:
            successMs = write_to_adu( getMsCmd(3))
            successKb = write_to_adu( getKbCmd(3))

        elif TARGET3_POS == 'bottom' and mouse_pos.y() >= bottommost_edge:
            successMs = write_to_adu( getMsCmd(3))
            successKb = write_to_adu( getKbCmd(3))

        if successKb and successMs:
            QCursor.setPos(rightmost_screen.geometry().center())
    def show_settings_dialog(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def quit(self):
        app.quit()
try:
    tray_icon = SystemTrayIcon(QIcon(getAbsoluteFileDataPath('icon.png')))
    tray_icon.show()
    sys.exit(app.exec_())
except BaseException as e:
    print("ERROR")
    print(e)
