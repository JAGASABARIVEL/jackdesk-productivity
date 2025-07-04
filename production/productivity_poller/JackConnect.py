import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QLineEdit, QStackedLayout, QFileDialog
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

from util import get_hostname, update_central_server_ip, get_credentials_from_server
from registration import register_device_with_server, unregister_device_from_server
from google_signin import login_and_get_app_token
from PyQt5.QtCore import QThread, pyqtSignal


CONFIG_PATH_FILE = "config_path.txt"


class LoginWorker(QThread):
    login_success = pyqtSignal(str, str)
    login_failed = pyqtSignal(str)

    def __init__(self, config_path, *args, **kwargs):
        self.config_path = config_path
        super().__init__(*args, **kwargs)

    def run(self):
        try:
            email, token = login_and_get_app_token()
            if not register_device_with_server(email, token, get_hostname(), self.config_path):
                raise Exception("Registration failed")
            self.login_success.emit(email, token)
        except Exception as e:
            self.login_failed.emit(str(e))


class CentralControlUI(QWidget):
    def __init__(self):
        super().__init__()
        self.email = None
        self.token = None
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Jackconnect")
        icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
        self.setWindowIcon(QIcon(icon_path))
        self.setFixedSize(500, 350)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)

        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.clicked.connect(self.toggle_controls)
        self.menu_btn.setStyleSheet("font-size: 18px; border: none;")

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(self.menu_btn)

        self.status_label = QLabel("Status: Not signed in")
        self.status_label.setAlignment(Qt.AlignCenter)

        # --- Config path input ---
        self.config_path_input = QLineEdit()
        self.config_path_input.setPlaceholderText("Path to app.config")
        self.config_path_input.setFixedHeight(28)

        self.browse_config_btn = QPushButton("Browse")
        self.browse_config_btn.setFixedHeight(28)
        self.browse_config_btn.clicked.connect(self.browse_config_file)

        config_path_layout = QHBoxLayout()
        config_path_layout.addWidget(self.config_path_input)
        config_path_layout.addWidget(self.browse_config_btn)

        self.server_ip_input = QLineEdit()
        self.server_ip_input.setPlaceholderText("Enter Central Server IP")
        self.server_ip_input.setFixedHeight(30)

        self.save_ip_btn = QPushButton("Save Server IP")
        self.save_ip_btn.clicked.connect(self.save_ip)

        self.signin_btn = QPushButton("Sign in")
        self.signin_btn.clicked.connect(self.login)

        self.validate_btn = QPushButton("Validate Registration")
        self.validate_btn.clicked.connect(self.validate_registration)

        self.connected_label = QLabel("Connected")
        self.connected_label.setAlignment(Qt.AlignCenter)
        self.connected_label.setStyleSheet("font-weight: bold; font-size: 18px;")
        
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_label.setPixmap(QPixmap(icon_path).scaled(100, 100, Qt.KeepAspectRatio))
        
        self.logo_container = QVBoxLayout()
        self.logo_container.addStretch(1)
        self.logo_container.addWidget(self.connected_label)
        self.logo_container.addWidget(self.logo_label)
        self.logo_container.addStretch(1)

        self.logo_widget = QWidget()
        self.logo_widget.setLayout(self.logo_container)

        self.settings_layout = QVBoxLayout()
        self.settings_layout.addWidget(self.status_label)
        self.settings_layout.addSpacing(10)
        self.settings_layout.addLayout(config_path_layout)
        self.settings_layout.addWidget(self.server_ip_input)
        self.settings_layout.addWidget(self.save_ip_btn)
        self.settings_layout.addWidget(self.signin_btn)
        self.settings_layout.addWidget(self.validate_btn)

        self.settings_widget = QWidget()
        self.settings_widget.setLayout(self.settings_layout)

        self.main_stack = QStackedLayout()
        self.main_stack.addWidget(self.logo_widget)
        self.main_stack.addWidget(self.settings_widget)

        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addLayout(self.main_stack)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.main_stack.setCurrentIndex(0)
        self.load_saved_config_path()
        self.refresh_status()

    def toggle_controls(self):
        self.main_stack.setCurrentIndex(1 if self.main_stack.currentIndex() == 0 else 0)

    def browse_config_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select app.config", filter="Config Files (*.config)")
        if path:
            self.config_path_input.setText(path)
            self.save_config_path(path)

    def save_config_path(self, path):
        try:
            with open(CONFIG_PATH_FILE, "w") as f:
                f.write(path)
        except Exception as e:
            print(f"Failed to save config path: {e}")

    def load_saved_config_path(self):
        try:
            if os.path.exists(CONFIG_PATH_FILE):
                with open(CONFIG_PATH_FILE, "r") as f:
                    path = f.read().strip()
                    self.config_path_input.setText(path)
        except Exception as e:
            print(f"Failed to load saved config path: {e}")

    def save_ip(self):
        ip = self.server_ip_input.text().strip()
        config_path = self.config_path_input.text().strip()

        if not ip:
            QMessageBox.warning(self, "Error", "Enter a valid IP address")
            return

        if not config_path or not os.path.exists(config_path):
            QMessageBox.warning(self, "Error", "Please provide a valid app.config path")
            return

        try:
            update_central_server_ip(ip, config_path)
            self.save_config_path(config_path)
            QMessageBox.information(self, "Success", f"Central server set to {ip}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update config: {e}")

    def login(self):
        self.signin_btn.setEnabled(False)
        self.signin_btn.setText("Signing in...")
        self.worker = LoginWorker(self.config_path_input.text().strip())
        self.worker.login_success.connect(self.on_login_success)
        self.worker.login_failed.connect(self.on_login_failed)
        self.worker.start()

    def on_login_success(self, email, token):
        self.email = email
        self.token = token
        QMessageBox.information(self, "Signed in", f"Logged in as {email}")
        self.refresh_status()
        self.signin_btn.setEnabled(True)
        self.signin_btn.setText("Sign in")

    def on_login_failed(self, message):
        QMessageBox.critical(self, "Login failed", message)
        self.refresh_status()
        self.signin_btn.setEnabled(True)
        self.signin_btn.setText("Sign in")

    def refresh_status(self):
        config_path = self.config_path_input.text().strip()
        creds = get_credentials_from_server(config_path)
        icon_path = os.path.dirname(__file__)
    
        if creds and creds.get("email"):
            self.email = creds["email"]
            self.token = creds["token"]
            self.status_label.setText(f"Signed in as: {self.email}")
            self.connected_label.setText("Connected")
            self.connected_label.setStyleSheet("color: green; font-weight: bold; font-size: 18px;")
            self.setWindowIcon(QIcon(os.path.join(icon_path, "logo.png")))
            self.logo_label.setPixmap(QPixmap(os.path.join(icon_path, "logo.png")).scaled(100, 100, Qt.KeepAspectRatio))
            self.validate_btn.setEnabled(True)
            self.signin_btn.hide()
            self.main_stack.setCurrentIndex(0)
        else:
            self.email = None
            self.token = None
            self.status_label.setText("Status: Not signed in")
            self.connected_label.setText("Disconnected")
            self.connected_label.setStyleSheet("color: red; font-weight: bold; font-size: 18px;")
            self.setWindowIcon(QIcon(os.path.join(icon_path, "disconnect.png")))
            self.logo_label.setPixmap(QPixmap(os.path.join(icon_path, "disconnect.png")).scaled(100, 100, Qt.KeepAspectRatio))
            self.validate_btn.setEnabled(False)
            self.signin_btn.show()
            self.main_stack.setCurrentIndex(1)

    def validate_registration(self):
        reply = QMessageBox.question(
            self,
            "Are you the current user?",
            f"You are signed in as {self.email}. Do you want to unregister this device?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            confirm = QMessageBox.question(
                self,
                "Confirm Unregistration",
                "This will remove device registration and require login again. Proceed?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                try:
                    resp = unregister_device_from_server(self.email, self.token, get_hostname(), self.config_path_input.text().strip())
                    if resp:
                        QMessageBox.information(self, "Unregistered", "Device has been unregistered.")
                    else:
                        QMessageBox.warning(self, "Failed", f"Failed to unregister: {resp.text}")
                except Exception as e:
                    QMessageBox.critical(self, "Error", str(e))
                self.refresh_status()


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    window = CentralControlUI()
    window.show()
    sys.exit(app.exec_())
