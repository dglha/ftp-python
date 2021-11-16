import sys
from threading import Thread

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ftplib import FTP
from urllib.parse import urlparse

from GUI.GuiWidget import LocalWidget, RemoteWidget
from BaseWindow import Ui_MainWindow
from utils import parse_file_info

RED_COLOR = QColor(255, 0, 0)
GREEN_COLOR = QColor(0, 255, 0)


class ClientGUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.ftp = FTP()
        self.hostname = ""
        self.username = ""
        self.password = ""

        self.setupWidget()

    #     Add slot to signal

        self.connectButton.clicked.connect(lambda: Thread(target=self.create_connect).start())

    def appendToStatus(self, log: str, color):
        self.statusTextEdit.append(log)
        self.statusTextEdit.setTextColor(color)

    def setupWidget(self):
        self.local = LocalWidget()
        self.remote = RemoteWidget()

        self.mainLayout.addWidget(self.local)
        self.mainLayout.addWidget(self.remote)
        self.mainLayout.setSpacing(0)

    def create_connect(self):
        # if not self.hostname:
        self.hostname = self.hostLineEdit.text()
        self.username = self.userLineEdit.text()
        self.password = self.passLineEdit.text()

        self.connectButton.setEnabled(False)
        self.connectButton.setText("Connecting...")
        # result = QInputDialog.getText(self, 'Connect to Host', 'Host Address', QLineEdit.Normal)

        try:
            response = self.ftp.connect(self.hostname, port=21, timeout=2)
            self.appendToStatus(response, GREEN_COLOR)
        except Exception as err:
            self.statusTextEdit.append(str(err))
            # msg = QMessageBox()
            # msg.setIcon(QMessageBox.Warning)
            # msg.setText("Error when connect to host!")
        response = self.ftp.login(user=self.username, passwd=self.password)
        self.statusTextEdit.append(response)

        self.connectButton.setEnabled(True)
        self.connectButton.setText("Connect")
        self.getRemoteFiles()

    def disconnect(self):
        try:
            response = self.ftp.quit()
            self.appendToStatus(response)
        except Exception as e:
            self.appendToStatus(str(e), RED_COLOR)

    def getRemoteFiles(self):
        self.remoteWordList = []
        self.remoteDir = {}
        self.ftp.dir('.', self.addItemToRemoteFiles)
        self.remote.completerModel.setStringList(self.remoteWordList)
        # self.remote.fileList.sortByColumn(0)


    def addItemToRemoteFiles(self, content):
        a = parse_file_info(content)
        print(a)

app = QtWidgets.QApplication(sys.argv)

window = ClientGUI()
window.show()
app.exec()
