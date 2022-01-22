import os
import sys

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
from .Menu.RemoteMenu import RemoteMenu


class BaseWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(700, 700)

        self.create_file_list()
        self.create_group_box()

        for pos, width in enumerate((150, 70, 70, 70, 90, 90)):
            self.fileList.setColumnWidth(pos, width)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.addWidget(self.groupBox)
        self.mainLayout.addWidget(self.fileList)
        # self.mainLayout.setMargin(5)
        self.setLayout(self.mainLayout)

        completer = QCompleter()
        self.completerModel = QStringListModel()
        completer.setModel(self.completerModel)
        self.pathEdit.setCompleter(completer)
        # Custom context menu
        self.fileList.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        # self.fileList.customContextMenuRequested.connect(self.menu_context_tree)

        # Menu
        self.menu = QMenu()

    def create_group_box(self):
        self.pathEdit = QLineEdit()
        self.homeButton = QPushButton()
        self.backButton = QPushButton()
        self.nextButton = QPushButton()

        self.homeButton.setText("Home")
        self.backButton.setText("Back")
        self.nextButton.setText("Next")

        self.homeButton.setEnabled(False)
        self.backButton.setEnabled(False)
        self.nextButton.setEnabled(False)

        self.hBox1 = QHBoxLayout()
        self.hBox2 = QHBoxLayout()

        self.hBox1.addWidget(self.homeButton)
        self.hBox1.addWidget(self.pathEdit)
        self.hBox2.addWidget(self.backButton)
        # self.hBox2.addWidget(self.nextButton)
        self.hBox2.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

        self.gLayout = QVBoxLayout()
        self.gLayout.addLayout(self.hBox1)
        self.gLayout.addLayout(self.hBox2)
        self.gLayout.setSpacing(5)
        # self.gLayout.setMargin(5)
        self.groupBox = QGroupBox('Widgets')
        self.groupBox.setLayout(self.gLayout)

    def create_file_list(self):
        self.fileList = QTreeWidget()
        self.fileList.setStyleSheet("""
            QTreeView::item {
                  padding: 5px;
                  
            }
        """)
        self.fileList.setIconSize(QSize(25, 25))
        self.fileList.setRootIsDecorated(False)
        # self.fileList.setHeaderLabels(('Name', 'Size', 'Owner', 'Group', 'Time', 'Mode'))
        self.fileList.setHeaderLabels(('Name', 'Size', 'Time', 'Mode'))
        self.fileList.header().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.fileList.header().setSectionResizeMode(0, QtWidgets.QHeaderView.Stretch)
        self.fileList.header().setStretchLastSection(False)
        self.fileList.setSortingEnabled(True)
        # self.fileList.setModel(self.fileModel)

    def menu_context_tree(self, point):
        index = self.fileList.indexAt(point)

        if not index.isValid():
            return

        item = self.fileList.itemAt(point)
        name = item.text(0)  # The text of the node.

        # We build the menu.
        # self.menu = QMenu()
        # action = menu.addAction(name)
        # self.menu.addSeparator()
        # action_1 = menu.addAction("Change Permissions")
        # action_2 = menu.addAction("File information")
        # action_3 = menu.addAction("Copy File Path")

        self.menu.exec(self.fileList.mapToGlobal(point))


class RemoteWidget(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.downloadButton = QPushButton()
        self.downloadButton.setText("Download")

        self.createDirButton = QPushButton()

        self.homeButton.setText("Home")
        self.hBox2.addWidget(self.downloadButton)
        self.hBox2.addWidget(self.createDirButton)
        self.groupBox.setTitle('Remote')

        self.menu = RemoteMenu(self)


class LocalWidget(BaseWidget):
    def __init__(self):
        BaseWidget.__init__(self)
        self.uploadButton = QPushButton()
        self.connectButton = QPushButton()
        self.uploadButton.setText("Upload")
        self.connectButton.setText("Connect")
        self.hBox2.addWidget(self.uploadButton)
        # self.hBox2.addWidget(self.connectButton)
        self.groupBox.setTitle('Local')

        # New pick location button
        self.pickDirButton = QPushButton()
        self.pickDirButton.setIcon(QFileIconProvider.icon(QFileIconProvider(), QFileIconProvider.Folder))
        self.hBox1.addWidget(self.pickDirButton)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ui = LocalWidget()
    ui.show()
    sys.exit(app.exec_())
