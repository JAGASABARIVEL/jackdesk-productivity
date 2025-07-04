
import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon

from registration import register_device_with_server
from util import get_hostname


class GoogleSignInThread(QThread):
    success = pyqtSignal(str, str)  # email, token
    error = pyqtSignal(str)

    def run(self):
        try:
            from google_signin import login_and_get_app_token
            email, token = login_and_get_app_token()
            self.success.emit(email, token)
        except Exception as e:
            self.error.emit(str(e))


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.thread = None
        self.init_ui()

    def init_ui(self):
        icon_path = os.path.join(os.path.dirname(__file__), "logo.png")
        self.setWindowTitle('Jackdesk Productivity')
        self.setWindowIcon(QIcon(icon_path))

        # Ensure the window stays on top and gains focus
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        #self.setWindowFlags(
        #    Qt.Window |
        #    Qt.WindowStaysOnTopHint |
        #    Qt.CustomizeWindowHint |
        #    Qt.WindowTitleHint |
        #    Qt.FramelessWindowHint
        #)

        # Only close button and stays on top
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowCloseButtonHint |
            Qt.WindowStaysOnTopHint
        )
        # Set fixed medium size
        self.resize(600, 300)

        self.label = QLabel('Click below to sign in with Google:')
        self.label.setAlignment(Qt.AlignCenter)

        self.button = QPushButton('Sign in with Google')
        self.button.clicked.connect(self.login)
        self.button.setFixedWidth(350)
        self.button.setFixedHeight(60)

        layout = QVBoxLayout()
        layout.addStretch(2)
        layout.addWidget(self.label, alignment=Qt.AlignCenter)
        layout.addSpacing(10)
        layout.addWidget(self.button, alignment=Qt.AlignCenter)
        layout.addStretch(3)
        self.setLayout(layout)

        #self.showNormal()
        self.raise_()
        self.activateWindow()

    def login(self):
        self.button.setText("Signing in...")
        self.button.setEnabled(False)

        self.thread = GoogleSignInThread()
        self.thread.success.connect(self.on_login_success)
        self.thread.error.connect(self.on_login_error)
        self.thread.start()

    def on_login_success(self, email, token):
        success = register_device_with_server(email, token, get_hostname())
        if not success:
            QMessageBox.critical(self, 'Error', 'Registration failed on central server.')
        else:
            QMessageBox.information(self, 'Success', f'Signed in as: {email}')
            self.close()

        self.button.setText("Sign in with Google")
        self.button.setEnabled(True)

    def on_login_error(self, message):
        QMessageBox.critical(self, 'Error', message)
        self.button.setText("Sign in with Google")
        self.button.setEnabled(True)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self.drag_position)
            event.accept()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
