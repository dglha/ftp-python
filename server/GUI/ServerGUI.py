import sys
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import os
from color import BLACK_COLOR, GREEN_COLOR
from .BaseGUI import Ui_MainWindow
from .Dialog import CreateUserDialog, UpdateUserDialog
from Worker.ServerWorker import ServerWorker
from Worker.UserWorker import get_all_user, delete_user
from Worker.UserWorker import create_user, update_user, check_user
import socket
from settings import PORT
from functools import partial
import datetime

__version__ = "0.1"
__author__ = "dlha_ndphuc"

icon_path = os.path.join(os.path.dirname(__file__), 'icons')


def icon(icon_name):
    return QIcon(os.path.join(icon_path, icon_name))


class ServerGUI(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("FileSent Server")
        self.setWindowIcon(icon("icons8-folder-240.png"))
        self.host = socket.gethostbyname(socket.gethostname())
        # self.mainWorker = GuiWorker(self, self.host, PORT)
        self.threadpool = QThreadPool()

        # Create runner
        self.guiRunner = GuiRunner(self, self.host, PORT)

        self.setupTable()

        self.logTextEdit.setStyleSheet("""
            QTextEdit {
                background-color: rgb(0, 0, 127)
            }
        """)
        self.logTextEdit.setFontPointSize(11)

        # self.startButton.clicked.connect(self.startServer)
        # self.stopButton.clicked.connect(self.stopServer)

        self.startButton.clicked.connect(self.startServer)
        # self.stopButton.clicked.connect(self.guiRunner.stop)
        self.stopButton.setEnabled(False)
        self.stopButton.setToolTip("Duo to technical problem, this button disabled for now ☹")

        self.createButton.clicked.connect(self.createUser)
        self.deleteButton.clicked.connect(self.deleteUser)
        self.editButton.clicked.connect(self.updateUser)

    def appendToStatus(self, log: str, color=GREEN_COLOR):
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M:%S")
        self.logTextEdit.setTextColor(color)
        self.logTextEdit.append(f"[{current_time}] {log}")

    def setupTable(self):
        self.tableWidget.setEnabled(True)
        self.tableWidget.setColumnCount(4)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setHorizontalHeaderLabels(['ID', 'Username', 'Write', 'Delete'])

        self.tableWidget.setColumnWidth(0, 70)
        self.tableWidget.setColumnWidth(1, 250)
        self.tableWidget.setColumnWidth(2, 250)
        self.tableWidget.setColumnWidth(3, 250)

        self.loadData()

    def loadData(self):
        self.tableWidget.clearContents()
        users = get_all_user()
        for i, user in enumerate(users):
            # item = QTableWidgetItem(user)
            self.tableWidget.insertRow(i)
            self.tableWidget.setItem(i, 0, QTableWidgetItem(str(user.id)))
            self.tableWidget.setItem(i, 1, QTableWidgetItem(user.username))
            self.tableWidget.setItem(i, 2, QTableWidgetItem("True" if user.is_write else "False"))
            self.tableWidget.setItem(i, 3, QTableWidgetItem("True" if user.is_delete else "False"))

    def showWarningDialog(self, title, message):
        dialog = QMessageBox.warning(self, title, message, QMessageBox.Ok, QMessageBox.Cancel)
        return dialog

    def showReloadRequiredDialog(self):
        QMessageBox.information(self, "Reload", "After your previous action, you must reopen server to work correctly!")

    @QtCore.pyqtSlot()
    def createUser(self):
        dialog = CreateUserDialog()
        dialog.exec_()
        self.loadData()

    @QtCore.pyqtSlot()
    def deleteUser(self):
        currentRow = self.tableWidget.currentIndex()
        index = self.tableWidget.model().index(currentRow.row(), 0)  # get id
        user_id = self.tableWidget.model().data(index)
        if not user_id:
            return
        is_accept = self.showWarningDialog("Delete", f"Are you sure to delete user had id {user_id}?")
        if is_accept == QMessageBox.Ok:
            result = delete_user(user_id)
            if result:
                QMessageBox.information(self, "Delete", "Delete successfully!", QMessageBox.Ok)
                self.loadData()
                self.showReloadRequiredDialog()
            else:
                QMessageBox.critical(self, "Delete", "An error occurred, try again!", QMessageBox.Ok)

    @QtCore.pyqtSlot()
    def updateUser(self):
        currentRow = self.tableWidget.currentIndex()
        index = self.tableWidget.model().index(currentRow.row(), 0)  # get id
        userId = self.tableWidget.model().data(index)
        if not userId:
            return
        dialog = UpdateUserDialog(int(userId))
        dialog.exec_()
        self.loadData()
        self.showReloadRequiredDialog()

    @QtCore.pyqtSlot()
    def startServer(self):
        self.threadpool.start(self.guiRunner)
        self.startButton.setEnabled(False)

    @QtCore.pyqtSlot()
    def stopServer(self):
        pass


class GuiRunner(QRunnable):
    """
    Start server worker thread
    """
    clients = []
    is_kill = False

    def __init__(self, gui: ServerGUI, host, port):
        super().__init__()
        self.host = host
        self.port = port
        self.gui = gui
        self.socket = None


    def run(self):
        while not self.is_kill:
            self.gui.appendToStatus("[SERVER] Starting...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.gui.appendToStatus("[SERVER] Server started, listening on {}".format(self.socket.getsockname()))
            self.socket.listen(5)
            while not self.is_kill:
                try:
                    client_socket, address = self.socket.accept()
                except OSError:
                    break
                # print("Accept")
                handler = ServerWorker(address=address, socket=client_socket, host=self.host)
                handler.start()

                self.clients.append(handler)
                # print("[SERVER] New connection from {}".format(address))
                self.gui.appendToStatus("[SERVER] New connection from {}".format(address))
                if self.is_kill:
                    break

    def stop(self):
        self.is_kill = True
        self.socket.close()
        # self.requestInterruption()
        for client in self.clients:
            client.terminate()
        self.gui.appendToStatus("[SERVER] Server stopped!")
        # self.terminate()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    server_gui = ServerGUI()
    server_gui.show()
    sys.exit(app.exec_())
