import sys
import os
import cv2
import numpy as np
from PIL import Image

from threading import Thread

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ftplib import FTP
from urllib.parse import urlparse

from GUI.Dialogs.dialogs import ProgressDialog
from GUI.GuiWidget import LocalWidget, RemoteWidget
from BaseWindow import Ui_MainWindow
from Worker.ThreadWorker import ThreadWorker, DownloadWorker, UploadWorker
from utils import parse_file_info, get_file_properties, path_parser
from queue import LifoQueue as stack
from constant import *

icon_path = os.path.join(os.path.dirname(__file__), 'icons')
icon = lambda icon_name: QIcon(os.path.join(icon_path, icon_name))

fontface = cv2.FONT_HERSHEY_SIMPLEX
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read("E://DoAn4//ftp-python//server//recoginzer//trainingData.yml")


class ClientGUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("FileSent")
        self.setWindowIcon(icon("icons8-folder-240.png"))

        self.ftp = FTP()
        self.hostname = ""
        self.username = ""
        self.password = ""

        # Dialog
        self.downloadProgressDialog = ProgressDialog("Download", icon("icons8-download-96.png"))
        self.uploadProgressDialog = ProgressDialog("Upload", icon("icons8-upload-96.png"))

        # Progress dict
        self.downloadProgress = {}
        self.uploadProgress = {}

        # pwd
        self.local_pwd = "E:\DoAn4\\demo\\"
        self.pwd = ""  # Remote dir

        # Current working dir
        self.cwd = ""  # Remote dir
        self.local_cwd = ""  # Local dir

        # GUI Widget
        self.setupWidget()

        # Path edit
        self.local.pathEdit.setText(self.local_pwd)
        self.localOriginPath = self.local_pwd
        self.getLocalFile()

        self.thread = QThread()
        self.threadpool = QThreadPool()
        print("Multithreading with maximum %d threads" % self.threadpool.maxThreadCount())

        self.remoteOriginPath = ""

        # Path history
        self.remoteHistory = stack(maxsize=20)
        self.localHistory = stack(maxsize=20)

        #     Add slot to signal

        self.connectButton.clicked.connect(lambda: Thread(target=self.createConnect).start())

        self.remote.pathEdit.returnPressed.connect(self.cdRemotePath)
        self.remote.fileList.itemDoubleClicked.connect(self.cdToRemoteDir)
        self.remote.homeButton.clicked.connect(self.cdToOriginRemoteDir)
        self.remote.backButton.clicked.connect(self.cdBackHistoryRemoteDir)
        self.remote.downloadButton.clicked.connect(self.downloadFile)
        # self.thread.finished.connect(self.progressDialog.show)

        self.local.pathEdit.returnPressed.connect(self.cdLocalPath)
        self.local.fileList.itemDoubleClicked.connect(self.cdToLocalDir)
        self.local.homeButton.clicked.connect(self.cdToOriginLocalDir)
        self.local.backButton.clicked.connect(self.cdBackHistoryLocalDir)
        self.local.pickDirButton.clicked.connect(self.pickLocalDir)
        self.local.uploadButton.clicked.connect(self.uploadFile)

    def initRemoteWidget(self):
        self.pwd = self.ftp.pwd()
        self.remoteOriginPath = self.pwd
        self.remote.pathEdit.setText(self.pwd)
        self.getRemoteFiles()

    def appendToStatus(self, log: str, color=BLACK_COLOR):
        self.statusTextEdit.append(log)
        self.statusTextEdit.setTextColor(color)

    def setupWidget(self):
        self.local = LocalWidget()
        self.remote = RemoteWidget()

        self.mainLayout.addWidget(self.local)
        self.mainLayout.addWidget(self.remote)
        self.mainLayout.setSpacing(0)

        # TextEdit Status
        self.statusTextEdit.setReadOnly(True)
        sb = self.statusTextEdit.verticalScrollBar()
        sb.setValue(sb.maximum())

        # Menu bar
        self.actionDownload.setIcon(icon("icons8-download-96.png"))
        self.actionDownload.triggered.connect(self.downloadProgressDialog.show)
        self.actionUpload.setIcon(icon("icons8-upload-96.png"))
        self.actionUpload.triggered.connect(self.uploadProgressDialog.show)
        self.actionExit.setIcon(icon("icons8-cancel-96.png"))

    def createConnect(self):
        # if not self.hostname:
        self.hostname = self.hostLineEdit.text()
        self.username = self.userLineEdit.text()
        self.password = self.passLineEdit.text()

        self.connectButton.setEnabled(False)
        self.connectButton.setText("Connecting...")
        # result = QInputDialog.getText(self, 'Connect to Host', 'Host Address', QLineEdit.Normal)

        try:
            response = self.ftp.connect(self.hostname, port=21, timeout=2)
            self.appendToStatus(response, BLUE_COLOR)
        except Exception as err:
            self.statusTextEdit.append(str(err))
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Error when connect to host!")
        finally:
            self.connectButton.setEnabled(True)
            self.connectButton.setText("Connect")

        response = self.ftp.login(user=self.username, passwd=self.password)
        self.statusTextEdit.append(response)

        self.openCV(response.split("-")[1], response.split("-")[2])

        self.connectButton.setEnabled(True)
        self.connectButton.setText("Connect")

    def clearInputInfo(self):
        self.hostLineEdit.setText("")
        self.userLineEdit.setText("")
        self.passLineEdit.setText("")

    def disconnect(self):
        try:
            response = self.ftp.quit()
            self.appendToStatus(response)
        except Exception as e:
            self.appendToStatus(str(e), RED_COLOR)

    def getRemoteFiles(self):
        self.remoteWordList = []
        self.remoteDir = {}
        self.remote.fileList.clear()
        self.ftp.dir('.', self.addItemToRemoteFiles)
        self.remote.completerModel.setStringList(self.remoteWordList)
        self.remote.fileList.sortByColumn(0, Qt.AscendingOrder)

    def addItemToRemoteFiles(self, content: str):
        # If file info is folder
        mode, size, time, fileName = parse_file_info(content)
        if content.startswith("d"):
            # fileIcon = QFileIconProvider.icon(QFileIconProvider(), QFileIconProvider.Folder)

            # Use custom icon
            fileIcon = icon("icons8-folder-240.png")
            self.remoteWordList.append(fileName)
            path = os.path.join(self.pwd, fileName)
            self.remoteDir[path] = True
        else:
            # fileIcon = QFileIconProvider.icon(QFileIconProvider(), QFileIconProvider.File)
            fileIcon = icon("icons8-document-240.png")

        item = QTreeWidgetItem()
        item.setIcon(0, fileIcon)

        for n, i in enumerate((fileName, size, time, mode)):
            item.setText(n, i)
        # item.setText(2, fileName)
        # item.setText(2, size)
        # item.setText(3, time)

        self.remote.fileList.addTopLevelItem(item)
        # Set cursor to first item on list files/folders
        if not self.remote.fileList.currentItem():
            self.remote.fileList.setCurrentItem(self.remote.fileList.topLevelItem(0))
            self.remote.fileList.setEnabled(True)

    def getLocalFile(self):
        self.localWordList = []
        self.localDir = {}
        self.local.fileList.clear()

        for file in os.listdir(self.local_pwd):
            pathname = os.path.join(self.local_pwd, file)
            self.addItemtoLocalFiles(get_file_properties(pathname))

        self.local.completerModel.setStringList(self.localWordList)
        self.local.fileList.sortByColumn(0, Qt.AscendingOrder)

    def addItemtoLocalFiles(self, content: str):
        mode, size, time, fileName = parse_file_info(content)
        if content.startswith("d"):
            fileIcon = QFileIconProvider.icon(QFileIconProvider(), QFileIconProvider.Folder)

            # Use custom icon
            # fileIcon = icon("icons8-folder-240.png")
            self.localWordList.append(fileName)
            path = os.path.join(self.local_pwd, fileName)
            self.localDir[path] = True

        else:
            fileIcon = QFileIconProvider.icon(QFileIconProvider(), QFileInfo(fileName))
            # fileIcon = icon("icons8-document-240.png")

        item = QTreeWidgetItem()
        item.setIcon(0, fileIcon)

        for n, i in enumerate((fileName, size, time, mode)):
            item.setText(n, i)
        # item.setText(2, fileName)
        # item.setText(2, size)
        # item.setText(3, time)

        self.local.fileList.addTopLevelItem(item)
        # Set cursor to first item on list files/folders
        # if not self.remote.fileList.currentItem():
        #     self.remote.fileList.setCurrentItem(self.remote.fileList.topLevelItem(0))
        #     self.remote.fileList.setEnabled(True)

    """
        REMOTE FUNCS
    """

    def isRemoteDir(self, dirname):
        return self.remoteDir.get(dirname, None)

    def cdRemotePath(self):
        pathname = path_parser(self.remote.pathEdit.text())
        try:
            # Add history
            self.remoteHistory.put(path_parser(self.pwd))
            self.ftp.cwd(pathname)
        except Exception as e:
            self.appendToStatus(str(e), RED_COLOR)
            self.remoteHistory.get()
            return

        # self.cwd = pathname.startswith(os.path.sep) and pathname or os.path.join(self.pwd, pathname)
        self.pwd = self.ftp.pwd()
        self.cwd = self.pwd

        self.getRemoteFiles()
        self.remote.pathEdit.setText(self.cwd)
        self.remote.backButton.setEnabled(True)
        if os.path.abspath(pathname) != self.remoteOriginPath:
            self.remote.homeButton.setEnabled(True)
        else:
            self.remote.homeButton.setEnabled(False)

    def cdToRemoteDir(self, item: QTreeWidgetItem, column):
        pathname = os.path.join(self.pwd, str(item.text(0)))

        if not self.isRemoteDir(pathname):
            self.appendToStatus("Dir not exits!", RED_COLOR)
            return

        try:
            self.ftp.cwd(path_parser(pathname))
            self.remoteHistory.put(path_parser(self.pwd))
        except Exception as e:
            self.appendToStatus(str(e), RED_COLOR)
            self.remoteHistory.get()

        self.pwd = self.ftp.pwd()

        self.remote.pathEdit.setText(self.pwd)
        self.getRemoteFiles()
        self.remote.backButton.setEnabled(True)
        if pathname != self.remoteOriginPath:
            self.remote.homeButton.setEnabled(True)

        self.appendToStatus(f"Cd to remote: {self.pwd}")

    def cdToOriginRemoteDir(self):
        try:
            self.ftp.cwd(self.remoteOriginPath + os.path.sep)
        except Exception as e:
            print(e)

        self.pwd = self.ftp.pwd()
        self.getRemoteFiles()
        self.remote.pathEdit.setText(self.pwd)
        self.remote.homeButton.setEnabled(False)

        self.appendToStatus("Cd to remote HOME")

    def cdBackHistoryRemoteDir(self):
        if self.remoteHistory.empty():
            self.remote.backButton.setEnabled(False)
            return

        pathname = self.remoteHistory.get()
        print(pathname)
        if pathname != self.remoteOriginPath:
            self.remote.homeButton.setEnabled(True)
        else:
            self.remote.homeButton.setEnabled(False)

        self.remote.backButton.setEnabled(True)
        self.pwd = pathname
        self.ftp.cwd(pathname)
        self.getRemoteFiles()
        self.remote.pathEdit.setText(pathname)

        self.appendToStatus(f"Cd to remote: {self.pwd}")

    """
        LOCAL FUNCS
    """

    def isLocalDir(self, dirname):
        return self.localDir.get(dirname, None)

    def cdLocalPath(self):
        pathname = path_parser(self.local.pathEdit.text())

        # Add history
        self.localHistory.put(self.local_pwd)

        if not os.path.exists(pathname) and not os.path.isdir(pathname):
            self.appendToStatus("Local dir does not exists or not a dir!", RED_COLOR)
            self.localHistory.get()
            return

        # self.cwd = pathname.startswith(os.path.sep) and pathname or os.path.join(self.pwd, pathname)
        self.local_pwd = pathname
        self.local_cwd = self.local_pwd

        self.getLocalFile()
        self.local.pathEdit.setText(self.local_cwd)
        self.local.backButton.setEnabled(True)
        if os.path.abspath(pathname) != self.localOriginPath:
            self.local.homeButton.setEnabled(True)
        else:
            self.local.homeButton.setEnabled(False)

        self.appendToStatus(f"Cd to local: {self.local_pwd}")

    def cdToLocalDir(self, item: QTreeWidgetItem, column):
        pathname = os.path.join(self.local_pwd, str(item.text(0)))

        self.localHistory.put(self.local_pwd)

        if not self.isLocalDir(pathname):
            print(pathname)
            self.appendToStatus("Local dir does not exists or not a dir!", RED_COLOR)
            self.localHistory.get()
            return

        self.local_pwd = pathname

        self.local.pathEdit.setText(self.local_pwd)
        self.getLocalFile()
        self.local.backButton.setEnabled(True)
        if pathname != self.localOriginPath:
            self.local.homeButton.setEnabled(True)

        self.appendToStatus(f"Cd to local: {self.local_pwd}")

    def cdToOriginLocalDir(self):
        self.local_pwd = self.localOriginPath
        self.getLocalFile()
        self.local.pathEdit.setText(self.local_pwd)
        self.local.homeButton.setEnabled(False)

    def cdBackHistoryLocalDir(self):
        if self.localHistory.empty():
            self.local.backButton.setEnabled(False)
            return

        pathname = self.localHistory.get()

        self.local.backButton.setEnabled(True)
        self.local_pwd = pathname
        self.getLocalFile()
        self.local.pathEdit.setText(pathname)

        self.appendToStatus(f"Cd to local: {self.local_pwd}")

    def pickLocalDir(self):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.DirectoryOnly)

        if dialog.exec():
            pathname = dialog.selectedFiles()
            self.local_pwd = os.path.abspath(pathname[0])
            self.local.pathEdit.setText(self.local_pwd)
            self.getLocalFile()
            self.appendToStatus(f"Cd to local: {self.local_pwd}")

    """
        UPLOAD - DOWNLOAD FUNCS
    """

    def downloadFile(self):
        # self.thread = QThread()
        # self.thread.started.connect(self.handleDownload)
        # self.thread.start()
        fileItem = self.remote.fileList.currentItem()
        sourceFile = os.path.join(self.pwd, fileItem.text(0))
        destinationFile = os.path.join(self.local_pwd, fileItem.text(0))

        fileSize = self.ftp.size(fileItem.text(0))

        temp = FTP()
        temp.connect(self.hostname, port=21, timeout=5)
        temp.login(self.username, self.password)
        temp.cwd(path_parser(self.pwd))

        worker = DownloadWorker(file_name=fileItem.text(0), file_size=fileSize, source_file=sourceFile,
                                destination_file=destinationFile, ftp=temp)

        worker.signals.progress.connect(self.setDownloadProgressDialogProcess)
        worker.signals.finished.connect(self.getLocalFile)

        self.downloadProgress[sourceFile] = self.downloadProgressDialog.addProgress(
            "Download", fileItem.text(0), fileSize
        )

        self.downloadProgressDialog.show()

        self.threadpool.start(worker)

    def uploadFile(self):
        fileItem = self.local.fileList.currentItem()
        sourceFile = os.path.join(self.local_pwd, fileItem.text(0))
        destinationFile = os.path.join(self.pwd, fileItem.text(0))

        print(sourceFile)

        fileSize = os.path.getsize(sourceFile)
        print(fileSize)

        temp = FTP()
        temp.connect(self.hostname, port=21, timeout=5)
        temp.login(self.username, self.password)
        temp.cwd(path_parser(self.pwd))

        uploadWorker = UploadWorker(file_name=fileItem.text(0), file_size=fileSize, source_file=sourceFile,
                                    destination_file=destinationFile, ftp=temp)

        uploadWorker.signals.progress.connect(self.setUploadProgressDialogProcess)
        uploadWorker.signals.finished.connect(self.getRemoteFiles)

        self.uploadProgress[sourceFile] = self.uploadProgressDialog.addProgress(
            "Upload", fileItem.text(0), fileSize
        )

        self.uploadProgressDialog.show()

        self.threadpool.start(uploadWorker)

    def setDownloadProgressDialogProcess(self, n, file_name):
        self.downloadProgress[file_name].set_value(n)

    def setUploadProgressDialogProcess(self, n, file_name):
        self.uploadProgress[file_name].set_value(n)

    def openCV(self, id_response, name_response):
        cap = cv2.VideoCapture(0)
        isPass = False

        while True:
            ret, frame = cap.read()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray)

            check = False

            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

                roi_gray = gray[y:y + h, x:x + w]
                id_roi, confidence = recognizer.predict(roi_gray)

                if confidence < 40:
                    if id_roi is not None:
                        if id_roi == int(id_response):
                            cv2.putText(frame, "" + str(name_response), (x + 10, y + h + 30), fontface, 1, (0, 255, 0),
                                        2)
                            isPass = True

                        else:
                            cv2.putText(frame, "Unknown", (x + 10, y + h + 30), fontface, 1, (0, 255, 0), 2)
                            isPass = False

            cv2.imshow('FACE RECOGNITION', frame)
            if cv2.waitKey(1) == ord('q') and isPass:
                self.setWindowTitle(f"FileSend - {self.username} - {self.hostname}")
                self.initRemoteWidget()
                break
        cap.release()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    window = ClientGUI()
    window.show()
    sys.exit(app.exec())
