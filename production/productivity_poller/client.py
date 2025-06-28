from PyQt5.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel,
    QVBoxLayout, QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtCore import Qt
from google_signin import login_and_get_app_token
from register_with_server import register_device_with_server
import sys

from util import get_hostname



class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Jackdesk Productivity')

        # Ensure the window stays on top and gains focus
        #self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.CustomizeWindowHint |
            Qt.WindowTitleHint |
            Qt.FramelessWindowHint
        )

        
        self.showNormal()
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

        self.raise_()
        self.activateWindow()

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

    def login(self):
        try:
            email, token = login_and_get_app_token()
            success = register_device_with_server(email, token, get_hostname())
            if not success:
                raise Exception("Registration failed on central server.")
            QMessageBox.information(self, 'Success', f'Signed in as: {email}')
            self.close()
        except Exception as e:
            QMessageBox.critical(self, 'Error', str(e))

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LoginWindow()
    window.show()
    sys.exit(app.exec_())
