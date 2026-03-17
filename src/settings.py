import logging
import os
import platform
from pathlib import Path
import json
from PyQt6.QtWidgets import QDialog, QLabel, QLineEdit, QVBoxLayout, QMessageBox, QComboBox, QPushButton, QCheckBox
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
from utils import get_absolute_file_data_path

logger = logging.getLogger(__name__)

class Config:
    def __init__(
        self,
        PROTOCOL="unifying",
        VENDOR_ID=0x046D,
        PRODUCT_ID=0xC52B,
        KB_RECEIVER_SLOT=0x01,
        MS_RECEIVER_SLOT=0x02,
        KEYBOARD_ID=0x09,
        MOUSE_ID=0x0a,
        UNICLIP_SERVER_IP="192.168.50.50",
        UNICLIP_PASSWORD="lcs1234",
        TARGET1_POS="right",
        TARGET2_POS="none",
        TARGET3_POS="none",
        TARGET1_MODE="full",
        TARGET1_ZONE_SIZE=200,
        TARGET1_ZONE_ANCHOR="start",
        TARGET2_MODE="full",
        TARGET2_ZONE_SIZE=200,
        TARGET2_ZONE_ANCHOR="start",
        TARGET3_MODE="full",
        TARGET3_ZONE_SIZE=200,
        TARGET3_ZONE_ANCHOR="start",
        REQUIRE_CTRL=False,
    ):
        self.PROTOCOL = PROTOCOL
        self.VENDOR_ID = VENDOR_ID
        self.PRODUCT_ID = PRODUCT_ID
        self.KB_RECEIVER_SLOT = KB_RECEIVER_SLOT
        self.MS_RECEIVER_SLOT = MS_RECEIVER_SLOT
        self.KEYBOARD_ID = KEYBOARD_ID
        self.MOUSE_ID = MOUSE_ID
        self.UNICLIP_SERVER_IP = UNICLIP_SERVER_IP
        self.UNICLIP_PASSWORD = UNICLIP_PASSWORD
        self.TARGET1_POS = TARGET1_POS
        self.TARGET2_POS = TARGET2_POS
        self.TARGET3_POS = TARGET3_POS
        self.TARGET1_MODE = TARGET1_MODE
        self.TARGET1_ZONE_SIZE = TARGET1_ZONE_SIZE
        self.TARGET1_ZONE_ANCHOR = TARGET1_ZONE_ANCHOR
        self.TARGET2_MODE = TARGET2_MODE
        self.TARGET2_ZONE_SIZE = TARGET2_ZONE_SIZE
        self.TARGET2_ZONE_ANCHOR = TARGET2_ZONE_ANCHOR
        self.TARGET3_MODE = TARGET3_MODE
        self.TARGET3_ZONE_SIZE = TARGET3_ZONE_SIZE
        self.TARGET3_ZONE_ANCHOR = TARGET3_ZONE_ANCHOR
        self.REQUIRE_CTRL = REQUIRE_CTRL

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        known_keys = set(cls.__init__.__code__.co_varnames) - {'self'}
        unknown_keys = set(data.keys()) - known_keys
        if unknown_keys:
            logger.warning(f"Ignoring unknown config keys: {unknown_keys}")
        return cls(**{k: v for k, v in data.items() if k in known_keys})

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
        # Restrict file permissions on non-Windows
        if platform.system().lower() != 'windows':
            os.chmod(self.config_path, 0o600)

class SettingsDialog(QDialog):
    def __init__(self):
        super().__init__()
        screen_locations = ['top', 'bottom', 'right', 'left', 'none']
        self.setWindowTitle('Settings')
        self.setWindowIcon(QIcon(get_absolute_file_data_path('icon', 'split-screen.png')))
        self.setWindowFlags(Qt.WindowType.WindowCloseButtonHint)

        self.protocol_combo = QComboBox()
        self.protocol_combo.addItems(['unifying', 'bolt'])

        self.vendor_id_edit = QLineEdit()
        self.product_id_edit = QLineEdit()
        self.kb_receiver_slot_edit = QLineEdit()
        self.ms_receiver_slot_edit = QLineEdit()
        self.keyboard_id_edit = QLineEdit()
        self.mouse_id_edit = QLineEdit()
        self.uniclip_password_edit = QLineEdit()

        self.target1_combo = QComboBox()
        self.target1_combo.addItems(screen_locations)
        self.target2_combo = QComboBox()
        self.target2_combo.addItems(screen_locations)
        self.target3_combo = QComboBox()
        self.target3_combo.addItems(screen_locations)

        trigger_modes = ['full', 'zone']
        zone_anchors = ['start', 'end']

        self.target1_mode_combo = QComboBox()
        self.target1_mode_combo.addItems(trigger_modes)
        self.target1_zone_size_edit = QLineEdit()
        self.target1_zone_anchor_combo = QComboBox()
        self.target1_zone_anchor_combo.addItems(zone_anchors)
        self.target1_mode_combo.currentTextChanged.connect(
            lambda mode: self._toggle_zone_fields(mode, self.target1_zone_size_edit, self.target1_zone_anchor_combo))

        self.target2_mode_combo = QComboBox()
        self.target2_mode_combo.addItems(trigger_modes)
        self.target2_zone_size_edit = QLineEdit()
        self.target2_zone_anchor_combo = QComboBox()
        self.target2_zone_anchor_combo.addItems(zone_anchors)
        self.target2_mode_combo.currentTextChanged.connect(
            lambda mode: self._toggle_zone_fields(mode, self.target2_zone_size_edit, self.target2_zone_anchor_combo))

        self.target3_mode_combo = QComboBox()
        self.target3_mode_combo.addItems(trigger_modes)
        self.target3_zone_size_edit = QLineEdit()
        self.target3_zone_anchor_combo = QComboBox()
        self.target3_zone_anchor_combo.addItems(zone_anchors)
        self.target3_mode_combo.currentTextChanged.connect(
            lambda mode: self._toggle_zone_fields(mode, self.target3_zone_size_edit, self.target3_zone_anchor_combo))

        self.require_ctrl_checkbox = QCheckBox('Require Ctrl held to switch')

        self.save_button = QPushButton('Save')
        self.save_button.clicked.connect(self.save_and_close)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Protocol'))
        layout.addWidget(self.protocol_combo)
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
        layout.addWidget(QLabel('Target 1 Mode'))
        layout.addWidget(self.target1_mode_combo)
        layout.addWidget(QLabel('Target 1 Zone Size (px)'))
        layout.addWidget(self.target1_zone_size_edit)
        layout.addWidget(QLabel('Target 1 Zone Anchor'))
        layout.addWidget(self.target1_zone_anchor_combo)
        layout.addWidget(QLabel('Target 2'))
        layout.addWidget(self.target2_combo)
        layout.addWidget(QLabel('Target 2 Mode'))
        layout.addWidget(self.target2_mode_combo)
        layout.addWidget(QLabel('Target 2 Zone Size (px)'))
        layout.addWidget(self.target2_zone_size_edit)
        layout.addWidget(QLabel('Target 2 Zone Anchor'))
        layout.addWidget(self.target2_zone_anchor_combo)
        layout.addWidget(QLabel('Target 3'))
        layout.addWidget(self.target3_combo)
        layout.addWidget(QLabel('Target 3 Mode'))
        layout.addWidget(self.target3_mode_combo)
        layout.addWidget(QLabel('Target 3 Zone Size (px)'))
        layout.addWidget(self.target3_zone_size_edit)
        layout.addWidget(QLabel('Target 3 Zone Anchor'))
        layout.addWidget(self.target3_zone_anchor_combo)
        layout.addWidget(self.require_ctrl_checkbox)
        layout.addWidget(QLabel('Uniclip Password'))
        layout.addWidget(self.uniclip_password_edit)
        layout.addWidget(self.save_button)
        self.setLayout(layout)

        self.setGeometry(350, 350, 300, 800)

    @staticmethod
    def _toggle_zone_fields(mode, size_edit, anchor_combo):
        enabled = mode == 'zone'
        size_edit.setEnabled(enabled)
        anchor_combo.setEnabled(enabled)

    def load_values(self):
        self.protocol_combo.setCurrentIndex(self.protocol_combo.findText(config.PROTOCOL))
        self.vendor_id_edit.setText(f'{config.VENDOR_ID:04X}')
        self.product_id_edit.setText(f'{config.PRODUCT_ID:04X}')
        self.kb_receiver_slot_edit.setText(f'{config.KB_RECEIVER_SLOT:02X}')
        self.ms_receiver_slot_edit.setText(f'{config.MS_RECEIVER_SLOT:02X}')
        self.keyboard_id_edit.setText(f'{config.KEYBOARD_ID:02X}')
        self.mouse_id_edit.setText(f'{config.MOUSE_ID:02X}')
        self.uniclip_password_edit.setText(config.UNICLIP_PASSWORD)
        self.target1_combo.setCurrentIndex(self.target1_combo.findText(config.TARGET1_POS))
        self.target2_combo.setCurrentIndex(self.target2_combo.findText(config.TARGET2_POS))
        self.target3_combo.setCurrentIndex(self.target3_combo.findText(config.TARGET3_POS))

        self.target1_mode_combo.setCurrentIndex(self.target1_mode_combo.findText(config.TARGET1_MODE))
        self.target1_zone_size_edit.setText(str(config.TARGET1_ZONE_SIZE))
        self.target1_zone_anchor_combo.setCurrentIndex(self.target1_zone_anchor_combo.findText(config.TARGET1_ZONE_ANCHOR))
        self._toggle_zone_fields(config.TARGET1_MODE, self.target1_zone_size_edit, self.target1_zone_anchor_combo)

        self.target2_mode_combo.setCurrentIndex(self.target2_mode_combo.findText(config.TARGET2_MODE))
        self.target2_zone_size_edit.setText(str(config.TARGET2_ZONE_SIZE))
        self.target2_zone_anchor_combo.setCurrentIndex(self.target2_zone_anchor_combo.findText(config.TARGET2_ZONE_ANCHOR))
        self._toggle_zone_fields(config.TARGET2_MODE, self.target2_zone_size_edit, self.target2_zone_anchor_combo)

        self.target3_mode_combo.setCurrentIndex(self.target3_mode_combo.findText(config.TARGET3_MODE))
        self.target3_zone_size_edit.setText(str(config.TARGET3_ZONE_SIZE))
        self.target3_zone_anchor_combo.setCurrentIndex(self.target3_zone_anchor_combo.findText(config.TARGET3_ZONE_ANCHOR))
        self._toggle_zone_fields(config.TARGET3_MODE, self.target3_zone_size_edit, self.target3_zone_anchor_combo)

        self.require_ctrl_checkbox.setChecked(config.REQUIRE_CTRL)

    def closeEvent(self, event):
        self.hide()
        event.accept()

    def save_and_close(self):
        reply = QMessageBox.question(
            self, 'Message', 'Do you want to save the changes?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Validate hex inputs before saving
            hex_fields = [
                ('Vendor ID', self.vendor_id_edit),
                ('Product ID', self.product_id_edit),
                ('Keyboard Receiver Slot', self.kb_receiver_slot_edit),
                ('Mouse Receiver Slot', self.ms_receiver_slot_edit),
                ('Keyboard ID', self.keyboard_id_edit),
                ('Mouse ID', self.mouse_id_edit),
            ]
            for name, field in hex_fields:
                try:
                    int(field.text(), 16)
                except ValueError:
                    QMessageBox.warning(self, 'Invalid Input', f'{name} must be a valid hex value.')
                    return

            # Validate zone size fields for targets in "zone" mode
            zone_fields = [
                ('Target 1 Zone Size', self.target1_mode_combo, self.target1_zone_size_edit),
                ('Target 2 Zone Size', self.target2_mode_combo, self.target2_zone_size_edit),
                ('Target 3 Zone Size', self.target3_mode_combo, self.target3_zone_size_edit),
            ]
            for name, mode_combo, size_edit in zone_fields:
                if mode_combo.currentText() == 'zone':
                    try:
                        val = int(size_edit.text())
                        if val <= 0:
                            raise ValueError
                    except ValueError:
                        QMessageBox.warning(self, 'Invalid Input', f'{name} must be a positive integer.')
                        return

            config.PROTOCOL = self.protocol_combo.currentText()
            config.VENDOR_ID = int(self.vendor_id_edit.text(), 16)
            config.PRODUCT_ID = int(self.product_id_edit.text(), 16)
            config.KB_RECEIVER_SLOT = int(self.kb_receiver_slot_edit.text(), 16)
            config.MS_RECEIVER_SLOT = int(self.ms_receiver_slot_edit.text(), 16)
            config.KEYBOARD_ID = int(self.keyboard_id_edit.text(), 16)
            config.MOUSE_ID = int(self.mouse_id_edit.text(), 16)
            config.TARGET1_POS = self.target1_combo.currentText()
            config.TARGET2_POS = self.target2_combo.currentText()
            config.TARGET3_POS = self.target3_combo.currentText()
            config.TARGET1_MODE = self.target1_mode_combo.currentText()
            config.TARGET1_ZONE_SIZE = int(self.target1_zone_size_edit.text())
            config.TARGET1_ZONE_ANCHOR = self.target1_zone_anchor_combo.currentText()
            config.TARGET2_MODE = self.target2_mode_combo.currentText()
            config.TARGET2_ZONE_SIZE = int(self.target2_zone_size_edit.text())
            config.TARGET2_ZONE_ANCHOR = self.target2_zone_anchor_combo.currentText()
            config.TARGET3_MODE = self.target3_mode_combo.currentText()
            config.TARGET3_ZONE_SIZE = int(self.target3_zone_size_edit.text())
            config.TARGET3_ZONE_ANCHOR = self.target3_zone_anchor_combo.currentText()
            config.REQUIRE_CTRL = self.require_ctrl_checkbox.isChecked()
            config.UNICLIP_PASSWORD = self.uniclip_password_edit.text()
            settings_manager.save_config(config)
        else:
            # Reload config from file and apply to the global config object
            saved = settings_manager.load_config()
            if saved:
                config.__dict__.update(saved.__dict__)

        self.hide()

settings_manager = SettingsManager()

config = settings_manager.load_config()
if config is None:
    config = Config()
    settings_manager.save_config(config)

def trigger_config_save():
    settings_manager.save_config(config)
