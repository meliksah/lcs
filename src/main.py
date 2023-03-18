from PyQt5.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QDesktopWidget, QLineEdit, QInputDialog
from PyQt5.QtGui import QIcon, QPainter, QPixmap, QBrush, QPainter
from PyQt5.QtCore import Qt, QRectF

import sys

from mouse_emulation import MouseEmulation
from flow import Flow
from utils import get_absolute_file_data_path
from settings import SettingsDialog, config, trigger_config_save
from uniclip import Uniclip

app = QApplication(sys.argv)
desktop = QDesktopWidget()


class SystemTrayIcon(QSystemTrayIcon):
    def __init__(self, icon, parent=None):
        super().__init__(icon, parent)
        print("SystemTrayIcon init")
        self.green_circle_icon = self.create_green_circle_pixmap()
        self.menu = QMenu(parent)
        self.flow = Flow(desktop)
        self.flow_action = self.menu.addAction('Flow')
        self.flow_action.setCheckable(True)
        self.flow_action.setChecked(False)
        self.flow_action.triggered.connect(self.toggle_flow)
        self.menu.addSeparator()

        self.mouse_emulation = MouseEmulation()
        self.mouse_emulation_action = self.menu.addAction('Mouse Emulation')
        self.mouse_emulation_action.setCheckable(True)
        self.mouse_emulation_action.setChecked(False)
        self.mouse_emulation_action.triggered.connect(self.toggle_mouse_emulation)

        # Add the "Start Clipboard Server" button to the "Uniclip" section
        self.menu.addSeparator()
        self.uniclip = Uniclip()
        self.start_server_action = self.menu.addAction('Start Clipboard Server')
        self.start_server_action.setCheckable(True)
        self.start_server_action.setChecked(False)
        self.start_server_action.triggered.connect(self.toggle_uniclip_server)

        # Add server info action below the "Start Clipboard Server" button
        self.server_info_action = self.menu.addAction('')
        self.server_info_action.setEnabled(False)
        self.server_info_action.setVisible(False)

        # Add the "Connect Clipboard Server" button to the "Uniclip" section
        self.connect_client_action = self.menu.addAction('Connect Clipboard Server')
        self.connect_client_action.setCheckable(True)
        self.connect_client_action.setChecked(False)
        self.connect_client_action.triggered.connect(self.toggle_uniclip_client)
        self.menu.addSeparator()

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
            # Get the IP and port from the user
            text, ok_pressed = QInputDialog.getText(self.menu.parent(), "Connect to Clipboard Server", "Enter IP and Port in the format 'IP:port':", QLineEdit.Normal, config.UNICLIP_SERVER_IP)
            if ok_pressed and text.strip():
                ip_port = text.strip()
                ip, port = ip_port.split(':')
                config.UNICLIP_SERVER_IP = f'{ip}:{port}'
                trigger_config_save()
                # Start the client
                try:
                    self.uniclip.start_client(ip_port)
                    # self.connect_client_action.setChecked(True)
                except Exception as e:
                    print(f"An error occurred while starting the Uniclip client: {str(e)}")
                    self.connect_client_action.setChecked(False)
            else:
                # If the user cancels or enters an invalid value, uncheck the "Connect Clipboard Server" button
                self.connect_client_action.setChecked(False)
        else:
            self.uniclip.stop_client()
            self.connect_client_action.setChecked(False)

    def show_settings_dialog(self):
        dialog = SettingsDialog()
        dialog.exec_()

    def quit(self):
        app.quit()
        sys.exit(app.exec_())
    def create_green_circle_pixmap(self):
        # Define the circle diameter
        circle_diameter = 12

        # Create a 16x16 base pixmap
        pixmap = QPixmap(16, 16)
        pixmap.fill(Qt.transparent)

        # Draw a green circle on the pixmap
        painter = QPainter(pixmap)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(Qt.green))
        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.drawEllipse(QRectF((16 - circle_diameter) / 2, (16 - circle_diameter) / 2, circle_diameter, circle_diameter))
        painter.end()
        painter = QPainter(pixmap)
        painter.setCompositionMode(QPainter.CompositionMode_SourceIn)
        painter.fillRect(pixmap.rect(), Qt.green)
        painter.end()
        return QIcon(pixmap)


tray_icon = SystemTrayIcon(
    QIcon(get_absolute_file_data_path('icon', 'icon.png')))
while True:
    try:

        tray_icon.show()
        app.exec_()
    except BaseException as e:
        print("ERROR")
        print(e)
