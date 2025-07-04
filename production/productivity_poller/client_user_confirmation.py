import sys
import os
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from util import get_hostname, get_credentials_from_server
from registration import unregister_device_from_server


class ConfirmUserWindow(QWidget):
    def __init__(self, email, token):
        super().__init__()
        self.email = email
        self.token = token
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Confirm Current User")
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "logo.png")))
        self.setFixedSize(500, 200)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.WindowCloseButtonHint |
            Qt.MSWindowsFixedSizeDialogHint
        )

        message = QLabel(f"Are you the current user with email:\n\n<b>{self.email}</b>?")
        message.setAlignment(Qt.AlignCenter)

        yes_btn = QPushButton("Yes")
        yes_btn.setFixedSize(100, 40)
        yes_btn.clicked.connect(self.accept_user)

        no_btn = QPushButton("No")
        no_btn.setFixedSize(100, 40)
        no_btn.clicked.connect(self.confirm_unregistration)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(yes_btn)
        button_layout.addSpacing(20)
        button_layout.addWidget(no_btn)
        button_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.addStretch(1)
        layout.addWidget(message)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        layout.addStretch(2)

        self.setLayout(layout)

    def accept_user(self):
        self.close()

    def get_user_details(self):
        creds = get_credentials_from_server()
        if not creds or not creds.get("token") or not creds.get("email"):
            return None
        return {'email': creds["email"], 'token': creds["token"]}

    def confirm_unregistration(self):
        reply = QMessageBox.question(
            self,
            "Unregister Confirmation",
            "This will unregister this device and require login again.\nAre you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.unregister_user()

    def unregister_user(self):
        try:
            r = unregister_device_from_server(self.email, self.token, get_hostname())
            if r.status_code == 200:
                QMessageBox.information(self, "Unregistered", "Device has been unregistered.")
            else:
                QMessageBox.warning(self, "Failed", f"Failed to unregister: {r.text}")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Fetch user details first
    user_details = get_credentials_from_server()
    if not user_details or not user_details.get("token") or not user_details.get("email"):
        print("No valid user credentials found. Exiting.")
        sys.exit(0)  # Exit before showing window
    
    window = ConfirmUserWindow(user_details.get("email"), user_details.get("token"))
    window.show()
    sys.exit(app.exec_())
