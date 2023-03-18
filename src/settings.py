from pathlib import Path
import json
from PyQt5.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QComboBox, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt
from utils import get_absolute_file_data_path

class Config:
    def __init__(
        self,
        VENDOR_ID=0x046D,
        PRODUCT_ID=0xC52B,
        KB_RECEIVER_SLOT=0x01,
        MS_RECEIVER_SLOT=0x02,
        KEYBOARD_ID=0x09,
        MOUSE_ID=0x0a,
        UNICLIP_SERVER_IP="192.168.50.50",
        TARGET1_POS="right",
        TARGET2_POS="none",
        TARGET3_POS="none",
    ):
        self.VENDOR_ID = VENDOR_ID
        self.PRODUCT_ID = PRODUCT_ID
        self.KB_RECEIVER_SLOT = KB_RECEIVER_SLOT
        self.MS_RECEIVER_SLOT = MS_RECEIVER_SLOT
        self.KEYBOARD_ID = KEYBOARD_ID
        self.MOUSE_ID = MOUSE_ID
        self.UNICLIP_SERVER_IP = UNICLIP_SERVER_IP
        self.TARGET1_POS = TARGET1_POS
        self.TARGET2_POS = TARGET2_POS
        self.TARGET3_POS = TARGET3_POS

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
        except (FileNotFoundError, json.JSONDecodeError):
            return None

        return Config.from_dict(config_data)

    def save_config(self, config):
        with open(self.config_path, 'w') as f:
            json.dump(config.to_dict(), f)

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        print("SettingsDialog init")
        screen_locations = ['top', 'bottom', 'right', 'left', 'none']
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon(get_absolute_file_data_path('icon', 'icon.png')))
        self.setWindowFlags(Qt.WindowCloseButtonHint)

        self.vendor_id_edit = QLineEdit(f'{config.VENDOR_ID:04X}')
        self.product_id_edit = QLineEdit(f'{config.PRODUCT_ID:04X}')
        self.kb_receiver_slot_edit = QLineEdit(f'{config.KB_RECEIVER_SLOT:02X}')
        self.ms_receiver_slot_edit = QLineEdit(f'{config.MS_RECEIVER_SLOT:02X}')
        self.keyboard_id_edit = QLineEdit(f'{config.KEYBOARD_ID:02X}')
        self.mouse_id_edit = QLineEdit(f'{config.MOUSE_ID:02X}')

        self.target1_combo = QComboBox()
        self.target1_combo.addItems(screen_locations)
        target1_index = self.target1_combo.findText(config.TARGET1_POS)
        self.target1_combo.setCurrentIndex(target1_index)
        self.target2_combo = QComboBox()
        self.target2_combo.addItems(screen_locations)
        target2_index = self.target2_combo.findText(config.TARGET2_POS)
        self.target2_combo.setCurrentIndex(target2_index)
        self.target3_combo = QComboBox()
        self.target3_combo.addItems(screen_locations)
        target3_index = self.target3_combo.findText(config.TARGET3_POS)
        self.target3_combo.setCurrentIndex(target3_index)

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.close)

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
        self.hide()
        event.ignore()
    def close(self):
        reply = QMessageBox.question(
            self, 'Message', 'Do you want to save the changes?',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            config.VENDOR_ID = int(self.vendor_id_edit.text(), 16)
            config.PRODUCT_ID = int(self.product_id_edit.text(), 16)
            config.KB_RECEIVER_SLOT = int(self.kb_receiver_slot_edit.text(), 16)
            config.MS_RECEIVER_SLOT = int(self.ms_receiver_slot_edit.text(), 16)
            config.KEYBOARD_ID = int(self.keyboard_id_edit.text(), 16)
            config.MOUSE_ID = int(self.mouse_id_edit.text(), 16)
            config.TARGET1_POS = self.target1_combo.currentText()
            config.TARGET2_POS = self.target2_combo.currentText()
            config.TARGET3_POS = self.target3_combo.currentText()
            settings_manager.save_config(config)

        settings_manager.load_config()
        self.hide()

settings_manager = SettingsManager()

config = settings_manager.load_config()
if config is None:
    config = Config()
    settings_manager.save_config(config)
def trigger_config_save(): 
    settings_manager.save_config(config)
