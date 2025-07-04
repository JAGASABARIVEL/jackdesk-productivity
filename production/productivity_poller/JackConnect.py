import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QVBoxLayout,
    QHBoxLayout, QMessageBox, QLineEdit, QStackedLayout
)
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtCore import Qt
from PyQt5 import QtCore

from util import get_hostname, update_central_server_ip, get_credentials_from_server
from registration import register_device_with_server, unregister_device_from_server
from google_signin import login_and_get_app_token


from PyQt5.QtCore import QThread, pyqtSignal

class LoginWorker(QThread):
    login_success = pyqtSignal(str, str)  # email, token
    login_failed = pyqtSignal(str)        # error message

    def run(self):
        from google_signin import login_and_get_app_token
        from registration import register_device_with_server
        from util import get_hostname

        try:
            email, token = login_and_get_app_token()
            if not register_device_with_server(email, token, get_hostname()):
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
        self.setFixedSize(450, 320)
        self.setWindowFlags(Qt.Window | Qt.WindowCloseButtonHint | Qt.MSWindowsFixedSizeDialogHint)

        # --- Top bar with hamburger menu ---
        self.menu_btn = QPushButton("☰")
        self.menu_btn.setFixedSize(30, 30)
        self.menu_btn.clicked.connect(self.toggle_controls)
        self.menu_btn.setStyleSheet("font-size: 18px; border: none;")

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        top_bar.addWidget(self.menu_btn)

        self.status_label = QLabel("Status: Not signed in")
        self.status_label.setAlignment(Qt.AlignCenter)

        # --- Settings panel ---
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
        self.settings_layout.addWidget(self.server_ip_input)
        self.settings_layout.addWidget(self.save_ip_btn)
        self.settings_layout.addWidget(self.signin_btn)
        self.settings_layout.addWidget(self.validate_btn)

        self.settings_widget = QWidget()
        self.settings_widget.setLayout(self.settings_layout)

        self.main_stack = QStackedLayout()
        self.main_stack.addWidget(self.logo_widget)      # index 0 - shows Connected + logo
        self.main_stack.addWidget(self.settings_widget)  # index 1 - settings panel


        main_layout = QVBoxLayout()
        main_layout.addLayout(top_bar)
        main_layout.addLayout(self.main_stack)
        main_layout.addStretch()

        self.setLayout(main_layout)
        self.main_stack.setCurrentIndex(0)
        self.refresh_status()

    def toggle_controls(self):
        current_index = self.main_stack.currentIndex()
        self.main_stack.setCurrentIndex(1 if current_index == 0 else 0)

    def refresh_status(self):
        creds = get_credentials_from_server()
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




    def save_ip(self):
        ip = self.server_ip_input.text().strip()
        if ip:
            update_central_server_ip(ip)
            QMessageBox.information(self, "Success", f"Central server set to {ip}")
        else:
            QMessageBox.warning(self, "Error", "Enter a valid IP address")

    def login(self):
        self.signin_btn.setEnabled(False)
        self.signin_btn.setText("Signing in...")
        self.worker = LoginWorker()
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
                    resp = unregister_device_from_server(self.email, self.token, get_hostname())
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
