import os

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMenu, QMainWindow, QAction

icon_path = os.path.join('GUI\\icons')


def icon(icon_name):
    return QIcon(os.path.join(icon_path, icon_name))


class RemoteMenu(QMenu):
    def __init__(self, parent):
        super(RemoteMenu, self).__init__()

        self.actionAddDir = QAction(parent)
        self.actionAddDir.setObjectName("actionAddDir")
        self.actionAddDir.setText("&Add new directory")
        self.actionAddDir.setIcon(icon("icons8-add-folder-96.png"))

        self.actionDelete = QAction(parent)
        self.actionDelete.setObjectName("actionDelete")
        self.actionDelete.setText("&Delete")
        self.actionDelete.setIcon(icon("icons8-delete-240.png"))

        self.actionRename = QAction(parent)
        self.actionRename.setObjectName("actionRename")
        self.actionRename.setText("&Rename")
        self.actionRename.setIcon(icon("icons8-rename-96.png"))

        self.addAction(self.actionAddDir)
        self.addAction(self.actionRename)
        self.addAction(self.actionDelete)
