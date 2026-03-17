from PyQt6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QLineEdit, QInputDialog, QMessageBox
from PyQt6.QtGui import QIcon, QPainter, QPixmap, QBrush
from PyQt6.QtCore import Qt, QRectF

import sys

from mouse_emulation import MouseEmulation
from flow import Flow
from utils import get_absolute_file_data_path
from settings import SettingsDialog, config, trigger_config_save
from uniclip import Uniclip

app = QApplication(sys.argv)


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        self.green_circle_icon = self.create_green_circle_pixmap()
        self.menu = QMenu(parent)
        self.flow = Flow(QApplication.screens())
        self.flow_action = self.menu.addAction('Flow')
        self.flow_action.setCheckable(True)
        self.flow_action.setChecked(False)
        self.flow_action.triggered.connect(self.toggle_flow)
        self.menu.addSeparator()

        self.mouse_emulation = MouseEmulation()
        self.mouse_emulation_action = self.menu.addAction('Keep Me Awake')
        self.mouse_emulation_action.setCheckable(True)
        self.mouse_emulation_action.setChecked(False)
        self.mouse_emulation_action.triggered.connect(self.toggle_mouse_emulation)

        self.menu.addSeparator()
        self.uniclip = Uniclip()
        self.start_server_action = self.menu.addAction('Start Clipboard Server')
        self.start_server_action.setCheckable(True)
        self.start_server_action.setChecked(False)
        self.start_server_action.triggered.connect(self.toggle_uniclip_server)

        self.server_info_action = self.menu.addAction('')
        self.server_info_action.setEnabled(False)
        self.server_info_action.setVisible(False)

        self.connect_client_action = self.menu.addAction('Connect Clipboard Server')
        self.connect_client_action.setCheckable(True)
        self.connect_client_action.setChecked(False)
        self.connect_client_action.triggered.connect(self.toggle_uniclip_client)
        self.menu.addSeparator()

        # Create settings dialog once, reuse it
        self.settings_dialog = SettingsDialog()

        self.settings_action = self.menu.addAction('Settings')
        self.settings_action.triggered.connect(self.show_settings_dialog)

        self.menu.addAction('Quit', self.quit)
        self.setContextMenu(self.menu)

    def toggle_mouse_emulation(self, checked):
        if checked:
            self.mouse_emulation.start()
            self.mouse_emulation_action.setChecked(True)
        else:
            self.mouse_emulation.stop()
            self.mouse_emulation_action.setChecked(False)

    def toggle_flow(self, checked):
        if checked:
            self.flow.start()
            self.flow_action.setChecked(True)
        else:
            self.flow.stop()
            self.flow_action.setChecked(False)

    def toggle_uniclip_server(self, checked):
        if checked:
            ip_port = self.uniclip.start_server()
            self.start_server_action.setChecked(True)
            self.update_server_info_action(ip_port, True)
            self.showMessage("Uniclip", f"Server started. IP and port: {ip_port}")
        else:
            self.uniclip.stop_server()
            self.start_server_action.setChecked(False)
            self.update_server_info_action("", False)

    def update_server_info_action(self, ip_port, visible):
        if visible:
            self.server_info_action.setIcon(self.green_circle_icon)
            self.server_info_action.setText(f"{ip_port}")
        else:
            self.server_info_action.setIcon(QIcon())
            self.server_info_action.setText("")
        self.server_info_action.setVisible(visible)

    def toggle_uniclip_client(self, checked):
        if checked:
            text, ok_pressed = QInputDialog.getText(
                self.menu.parent(), "Connect to Clipboard Server",
                "Enter IP and Port in the format 'IP:port':",
                QLineEdit.EchoMode.Normal, config.UNICLIP_SERVER_IP
            )
            if ok_pressed and text.strip():
                ip_port = text.strip()
                # Validate IP:port format
                try:
                    ip, port = ip_port.split(':')
                    int(port)  # validate port is numeric
                except ValueError:
                    QMessageBox.warning(
                        None, 'Invalid Input',
                        "Please enter address in the format 'IP:port' (e.g. 192.168.1.1:55555)."
                    )
                    self.connect_client_action.setChecked(False)
                    return
                config.UNICLIP_SERVER_IP = f'{ip}:{port}'
                trigger_config_save()
                try:
                    self.uniclip.start_client(ip_port)
                except Exception as e:
                    print(f"An error occurred while starting the Uniclip client: {str(e)}")
                    self.connect_client_action.setChecked(False)
            else:
                self.connect_client_action.setChecked(False)
        else:
            self.uniclip.stop_client()
            self.connect_client_action.setChecked(False)

    def show_settings_dialog(self):
        self.settings_dialog.load_values()
        self.settings_dialog.show()
        self.settings_dialog.raise_()

    def quit(self):
        self.flow.stop()
        self.mouse_emulation.stop()
        self.uniclip.stop_all()
        app.quit()

    def create_green_circle_pixmap(self):
        circle_diameter = 12
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(Qt.GlobalColor.green))
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.drawEllipse(QRectF(
            (16 - circle_diameter) / 2, (16 - circle_diameter) / 2,
            circle_diameter, circle_diameter
        ))
        painter.end()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), Qt.GlobalColor.green)
        painter.end()
        return QIcon(pixmap)


tray_icon = SystemTrayIcon(
    QIcon(get_absolute_file_data_path('icon', 'split-screen.png')))

tray_icon.show()
sys.exit(app.exec())
