import sys
import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QDialog, QMessageBox

from .BaseDialog import Ui_Dialog
from Worker.UserWorker import create_user, get_user, update_user

icon_path = os.path.join(os.path.dirname(__file__), 'icons')


def icon(icon_name):
    return QIcon(os.path.join(icon_path, icon_name))


class CreateUserDialog(QDialog, Ui_Dialog):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Adding new user")
        self.setWindowIcon(icon("icons8-folder-240.png"))

        self.buttonBox.accepted.connect(self.createUser)

    def createUser(self):
        print("Create user")
        username = self.usernameLineEdit.text()
        passwd = self.passTextEdit.text()
        is_write = self.writeCheckbox.isChecked()
        is_delete = self.deleleCheckbox.isChecked()

        result = create_user(username, passwd, is_write, is_delete)
        if result:
            dialog = QMessageBox.information(self, "Adding new user", "Successfully!", QMessageBox.Ok)
        else:
            dialog = QMessageBox.information(self, "Adding new user", "Failed!", QMessageBox.Ok)


class UpdateUserDialog(QDialog, Ui_Dialog):
    def __init__(self, userId: int):
        super().__init__()
        self.setupUi(self)
        self.userId = userId
        self.setWindowTitle("Update new user")
        self.setWindowIcon(icon("icons8-folder-240.png"))
        self.getUserInformation()

        self.buttonBox.accepted.connect(self.updateUser)

    def getUserInformation(self):
        result, user = get_user(self.userId)
        self.usernameLineEdit.setText(user.username)
        self.usernameLineEdit.setEnabled(False)
        self.passTextEdit.setEnabled(False)

        if user.is_write:
            self.writeCheckbox.setChecked(True)
        if user.is_delete:
            self.deleleCheckbox.setChecked(True)

    def updateUser(self):
        username = self.usernameLineEdit.text()
        is_write = self.writeCheckbox.isChecked()
        is_delete = self.deleleCheckbox.isChecked()

        result = update_user(self.userId, is_write, is_delete)
        if result:
            dialog = QMessageBox.information(self, "Update new user", "Successfully!", QMessageBox.Ok)
        else:
            dialog = QMessageBox.information(self, "Update new user", "Failed!", QMessageBox.Ok)