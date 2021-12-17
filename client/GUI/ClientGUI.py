import sys
import os
from threading import Thread

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from ftplib import FTP
from urllib.parse import urlparse

from GUI.Dialogs.dialogs import ProgressDialog
from GUI.GuiWidget import LocalWidget, RemoteWidget
from GUI.BaseWindow import Ui_MainWindow
from Worker.ThreadWorker import ThreadWorker, DownloadWorker, UploadWorker
from utils import parse_file_info, get_file_properties, path_parser, clearQTreeWidget
from queue import LifoQueue as stack
from constant import *
from pathlib import Path

icon_path = os.path.join(os.path.dirname(__file__), 'icons')


def icon(icon_name):
    return QIcon(os.path.join(icon_path, icon_name))


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
        self.local_pwd = str(Path.home())
        self.pwd = ""  # Remote dir

        # Current working dir
        self.cwd = ""  # Remote dir
        self.local_cwd = ""  # Local dir

        # GUI Widget
        self.setupWidget()
        self.remoteWordList = []
        self.remoteDir = {}
        self.localWordList = []
        self.localDir = {}

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

        # self.connectButton.clicked.connect(lambda: Thread(target=self.createConnect).start())
        self.connectButton.clicked.connect(self.createConnect)

        # Remote menu
        self.remote.fileList.customContextMenuRequested.connect(self.remote_menu_context_tree)

        # Remote signal
        self.remote.pathEdit.returnPressed.connect(self.cdRemotePath)
        self.remote.fileList.itemDoubleClicked.connect(self.cdToRemoteDir)
        self.remote.homeButton.clicked.connect(self.cdToOriginRemoteDir)
        self.remote.backButton.clicked.connect(self.cdBackHistoryRemoteDir)
        self.remote.downloadButton.clicked.connect(self.downloadFile)
        # self.thread.finished.connect(self.progressDialog.show)
        self.remote.createDirButton.clicked.connect(self.createRemoteDir)
        self.remote.menu.actionAddDir.triggered.connect(self.createRemoteDir)
        self.remote.menu.actionDelete.triggered.connect(self.deleteRemoteFile)
        self.remote.menu.actionRename.triggered.connect(self.renameRemoteFile)

        self.local.pathEdit.returnPressed.connect(self.cdLocalPath)
        self.local.fileList.itemDoubleClicked.connect(self.cdToLocalDir)
        self.local.homeButton.clicked.connect(self.cdToOriginLocalDir)
        self.local.backButton.clicked.connect(self.cdBackHistoryLocalDir)
        self.local.pickDirButton.clicked.connect(self.pickLocalDir)
        self.local.uploadButton.clicked.connect(self.uploadFile)

    def initRemoteWidget(self):
        self.setRemoteBool(True)
        self.pwd = self.ftp.pwd()
        self.remoteOriginPath = self.pwd
        self.remote.pathEdit.setText(self.pwd)
        self.getRemoteFiles()

    def appendToStatus(self, log: str, color=BLACK_COLOR):
        self.statusTextEdit.setTextColor(color)
        self.statusTextEdit.append(log)

    def remote_menu_context_tree(self, point):
        index = self.remote.fileList.indexAt(point)

        if not index.isValid():
            return

        # item = self.remote.fileList.itemAt(point)
        # self.remote.menu.actionDelete.triggered.connect(partial(self.deleteRemoteFile, point))

        self.remote.menu.exec(self.remote.fileList.mapToGlobal(point))

    def setupWidget(self):
        self.local = LocalWidget()
        self.remote = RemoteWidget()

        # Disable remote
        self.setRemoteBool(False)

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
        self.actionExit.triggered.connect(self.disconnect)
        self.actionAbout.triggered.connect(self.showAboutAction)

        # Set remote widget icon
        self.remote.createDirButton.setIcon(icon("icons8-add-folder-96.png"))

    def createConnect(self):
        # if not self.hostname:
        self.hostname = self.hostLineEdit.text()
        self.username = self.userLineEdit.text()
        self.password = self.passLineEdit.text()

        self.connectButton.setEnabled(False)
        self.connectButton.setText("Connecting...")

        try:
            response = self.ftp.connect(self.hostname, port=21, timeout=2)
            self.appendToStatus(response, BLUE_COLOR)
        except Exception as err:
            self.statusTextEdit.append(str(err))
            self.showErrorMsg(str(err))
            return
        finally:
            self.connectButton.setEnabled(True)
            self.connectButton.setText("Connect")

        try:
            response = self.ftp.login(user=self.username, passwd=self.password)
        except Exception as e:
            self.ftp.quit()
            self.appendToStatus(str(e), RED_COLOR)
            self.showErrorMsg(str(e))
            return

        self.connectButton.setEnabled(True)
        self.connectButton.setText("Connect")

        # Reset windows title
        self.setWindowTitle(f"FileSend - {self.username} - {self.hostname}")

        self.showSuccessMsg("Login", "Login successfully!")
        self.clearInputInfo()
        self.initRemoteWidget()

    def disconnect(self):
        try:
            response = self.ftp.quit()
            self.setRemoteBool(False)
            self.clearRemoteWidget()
            self.appendToStatus(response)
        except Exception as e:
            self.showErrorMsg(str(e))
            self.appendToStatus(str(e), RED_COLOR)

    def getRemoteFiles(self):
        self.remoteWordList = []
        self.remoteDir = {}
        # self.remote.fileList.clear()
        if self.remote.fileList.topLevelItemCount() > 0:
            clearQTreeWidget(self.remote.fileList)
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

    def cdToRemoteDir(self, item: QTreeWidgetItem):
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

    @QtCore.pyqtSlot()
    def createRemoteDir(self, *args):
        dir_name, confirm = QInputDialog.getText(self, "New dir", "Name", QLineEdit.Normal)
        if confirm:
            try:
                status = self.ftp.mkd(dir_name)
            except Exception as e:
                self.appendToStatus(str(e), RED_COLOR)
                return
            self.appendToStatus(status, BLUE_COLOR)
            QMessageBox.about(self, "New dir", f"{dir_name} created successfully!")
            self.getRemoteFiles()

    @QtCore.pyqtSlot()
    def deleteRemoteFile(self):
        items = self.remote.fileList.selectedItems()
        if len(items) < 0:
            return

        name = items[0].text(0)
        path = os.path.join(self.pwd, name)

        dialog = QMessageBox()
        dialog.setIcon(QMessageBox.Warning)
        dialog.setWindowTitle("Confirm")
        dialog.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)

        if path in self.remoteDir and self.remoteDir[path]:

            dialog.setText(f"Do you want to delete \"{name}\" directory?")
            confirm = dialog.exec()
            print("confirm", confirm)

        else:
            dialog.setText(f"Do you want to delete \"{name}\" file?")
            confirm = dialog.exec()
            print("confirm", confirm)

        if confirm == QMessageBox.Ok:
            try:
                if path in self.remoteDir:
                    self.ftp.rmd(name)
                else:
                    self.ftp.delete(name)
                self.getRemoteFiles()
            except Exception as e:
                self.appendToStatus(str(e), RED_COLOR)

    @QtCore.pyqtSlot()
    def renameRemoteFile(self):
        items = self.remote.fileList.selectedItems()
        old_name = items[0].text(0)
        if not items:
            return
        new_name, confirm = QInputDialog.getText(self, "Rename", "Name", QLineEdit.Normal, text=items[0].text(0))
        if confirm:
            try:
                status = self.ftp.rename(old_name, new_name)
            except Exception as e:
                self.appendToStatus(str(e), RED_COLOR)
                return

            self.appendToStatus(status, BLUE_COLOR)
            QMessageBox.about(self, "Rename", "Rename successfully!")
            self.getRemoteFiles()

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

    def checkIsDir(self, file_name: str, file_dict: dict):
        return file_name in file_dict and file_dict[file_name] == True

    def downloadFile(self):
        # self.thread = QThread()
        # self.thread.started.connect(self.handleDownload)
        # self.thread.start()
        fileItem = self.remote.fileList.currentItem()
        if not fileItem:
            self.showErrorMsg("Please choose a file to download!")
            return
        if not self.checkIsDir(fileItem.text(0), self.remoteDir):
            self.showErrorMsg("Cannot download directory!")
            return
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
        if not fileItem:
            self.showErrorMsg("Please choose a file to upload!")
            return
        if self.checkIsDir(fileItem.text(0), self.localDir):
            self.showErrorMsg("Cannot upload directory!")
            return
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

    """
        CLIENT FUNCS
    """

    def showErrorMsg(self, msg: str):
        e = QErrorMessage(self)
        e.setWindowTitle("Error")
        e.showMessage(msg)

    def showSuccessMsg(self, title: str, msg: str):
        e = QMessageBox.information(self, title, msg)

    def setRemoteBool(self, b: bool):
        self.remote.setEnabled(b)
        self.local.uploadButton.setEnabled(b)

    def clearRemoteWidget(self):
        self.remote.pathEdit.setText("")
        self.local.uploadButton.setEnabled(False)
        clearQTreeWidget(self.remote.fileList)

    def clearInputInfo(self):
        self.hostLineEdit.setText("")
        self.userLineEdit.setText("")
        self.passLineEdit.setText("")

    def showAboutAction(self):
        QMessageBox.about(self, "FileSend", "FTP Implement application\r\nBy dlha & ndphuc.")

    def setDownloadProgressDialogProcess(self, n, file_name):
        self.downloadProgress[file_name].set_value(n)

    def setUploadProgressDialogProcess(self, n, file_name):
        self.uploadProgress[file_name].set_value(n)
