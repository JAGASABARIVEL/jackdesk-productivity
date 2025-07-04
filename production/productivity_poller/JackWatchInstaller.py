
import os
import sys
import shutil
import zipfile
import subprocess
import requests
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QPushButton,
    QFileDialog, QProgressBar, QMessageBox, QStackedLayout,
    QHBoxLayout, QLineEdit, QSizePolicy, QSpacerItem
)
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5 import QtCore

GITHUB_ZIP_URL = "https://github.com/JAGASABARIVEL/jackdesk-productivity/archive/refs/heads/main.zip"
REQUIREMENTS_REL_PATH = "jackdesk-productivity-main/production/productivity_poller/requirements.txt"
CLIENT_SECRET_DEST_REL_PATH = "jackdesk-productivity-main/production/productivity_poller/client_secret.json"


class InstallerWorker(QThread):
    progress = pyqtSignal(str)
    finished = pyqtSignal(bool, str)

    def __init__(self, install_path):
        super().__init__()
        self.install_path = install_path

    def run(self):
        try:
            zip_path = os.path.join(self.install_path, "jackdesk.zip")
            self.progress.emit("Downloading project zip...")
            with requests.get(GITHUB_ZIP_URL, stream=True) as r:
                r.raise_for_status()
                with open(zip_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        f.write(chunk)

            self.progress.emit("Extracting zip...")
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.install_path)

            os.remove(zip_path)

            req_path = os.path.join(self.install_path, REQUIREMENTS_REL_PATH)
            self.progress.emit("Installing dependencies...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", req_path])

            self.progress.emit("Installation complete.")
            self.finished.emit(True, "Installation completed successfully.")
        except Exception as e:
            self.finished.emit(False, f"Installation failed: {str(e)}")


class StepperInstaller(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("JackWatch Installer")
        self.setFixedSize(600, 400)
        self.setWindowIcon(QIcon(os.path.join(os.path.dirname(__file__), "logo.png")))

        self.install_path = ""
        self.worker = None

        self.setStyleSheet("""
            QWidget {
        font-family: 'Segoe UI';
        background-color: #e0f2f1;  /* Light teal */
    }
    QPushButton {
        background-color: #009688;
        color: white;
        border-radius: 5px;
        padding: 8px 16px;
    }
    QPushButton:hover {
        background-color: #00796b;
    }
    QLabel {
        font-size: 14px;
    }
    QLineEdit {
        background-color: white;
        border: 1px solid #ccc;
        padding: 5px;
        border-radius: 4px;
    }
    QProgressBar {
        height: 20px;
        border: 1px solid #aaa;
        border-radius: 5px;
        text-align: center;
    }
    QProgressBar::chunk {
        background-color: #009688;
        width: 20px;
    }
        """)

        self.stack = QStackedLayout()
        self.stack.addWidget(self.page1_select_folder())
        self.stack.addWidget(self.page2_confirm())
        self.stack.addWidget(self.page3_install())
        self.stack.addWidget(self.page4_add_secret())
        self.stack.addWidget(self.page5_finish())

        layout = QVBoxLayout()
        layout.addLayout(self.stack)
        self.setLayout(layout)

    def page1_select_folder(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Step 1: Select Installation Folder")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.folder_path = QLineEdit()
        self.folder_path.setReadOnly(True)
        self.folder_path.setPlaceholderText("No folder selected")
        self.folder_path.setToolTip("Installation folder path")
        self.folder_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        browse_btn = QPushButton("Browse")
        browse_btn.clicked.connect(self.select_folder)

        self.page1_next_btn = QPushButton("Next")
        self.page1_next_btn.setEnabled(False)
        self.page1_next_btn.clicked.connect(lambda: self.stack.setCurrentIndex(1))

        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.folder_path)
        folder_layout.addWidget(browse_btn)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(20)
        layout.addLayout(folder_layout)
        layout.addStretch()
        layout.addWidget(self.page1_next_btn, alignment=Qt.AlignRight)

        page.setLayout(layout)
        return page

    def page2_confirm(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Step 2: Confirm Installation Path")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        self.confirm_label = QLabel("")
        self.confirm_label.setAlignment(Qt.AlignCenter)
        self.confirm_label.setWordWrap(True)

        back_btn = QPushButton("Back")
        back_btn.clicked.connect(lambda: self.stack.setCurrentIndex(0))

        next_btn = QPushButton("Install")
        next_btn.clicked.connect(self.start_installation)

        nav = QHBoxLayout()
        nav.addWidget(back_btn)
        nav.addStretch()
        nav.addWidget(next_btn)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(20)
        layout.addWidget(self.confirm_label)
        layout.addStretch()
        layout.addLayout(nav)
        page.setLayout(layout)
        return page

    def page3_install(self):
        page = QWidget()
        layout = QVBoxLayout()

        self.progress_label = QLabel("Installing...")
        self.progress_label.setAlignment(Qt.AlignCenter)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(0)
        self.progress_bar.hide()

        layout.addStretch()
        layout.addWidget(self.progress_label)
        layout.addSpacing(10)
        layout.addWidget(self.progress_bar)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def page4_add_secret(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("Step 4: Add `client_secret.json`")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        add_btn = QPushButton("Add File")
        add_btn.clicked.connect(self.add_secret)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(20)
        layout.addWidget(add_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def page5_finish(self):
        page = QWidget()
        layout = QVBoxLayout()

        label = QLabel("🎉 Installation Completed")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))

        finish_btn = QPushButton("Finish")
        finish_btn.clicked.connect(self.close)

        layout.addStretch()
        layout.addWidget(label)
        layout.addSpacing(30)
        layout.addWidget(finish_btn, alignment=Qt.AlignCenter)
        layout.addStretch()
        page.setLayout(layout)
        return page

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose Installation Directory")
        if folder:
            self.install_path = folder
            self.folder_path.setText(folder)
            self.confirm_label.setText(f"Selected Path:\n{folder}")
            self.page1_next_btn.setEnabled(True)

    def start_installation(self):
        self.stack.setCurrentIndex(2)
        self.progress_bar.show()
        self.worker = InstallerWorker(self.install_path)
        self.worker.progress.connect(self.progress_label.setText)
        self.worker.finished.connect(self.installation_done)
        self.worker.start()

    def installation_done(self, success, message):
        self.progress_bar.hide()
        QMessageBox.information(self, "Installer", message)
        if success:
            self.stack.setCurrentIndex(3)
        else:
            self.stack.setCurrentIndex(1)

    def add_secret(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select client_secret.json", filter="JSON Files (*.json)")
        if file_path:
            try:
                dest = os.path.join(self.install_path, CLIENT_SECRET_DEST_REL_PATH)
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                shutil.copy(file_path, dest)
                QMessageBox.information(self, "Success", "client_secret.json added successfully.")
                self.stack.setCurrentIndex(4)
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QtCore.QCoreApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app = QApplication(sys.argv)
    window = StepperInstaller()
    window.show()
    sys.exit(app.exec_())
