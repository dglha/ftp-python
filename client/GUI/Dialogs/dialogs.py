import os

from PyQt5 import QtCore
from PyQt5.QtWidgets import *


class BaseProgressWidget(QWidget):
    updateProgress = QtCore.pyqtSignal(str)

    def __init__(self, text='', parent=None):
        super(BaseProgressWidget, self).__init__(parent)
        self.setFixedHeight(100)
        self.text = text
        self.progressbar = QProgressBar()
        self.progressbar.setTextVisible(True)
        self.progressbar.setFixedHeight(30)
        self.updateProgress.connect(self.set_value)

        self.bottomBorder = QWidget()
        self.bottomBorder.setStyleSheet("""
                    background: palette(shadow);
                """)
        self.bottomBorder.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed))
        self.bottomBorder.setMinimumHeight(1)

        self.label = QLabel(self.text)
        self.label.setStyleSheet("""
                    font-weight: bold;
                """)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(10, 10, 10, 30)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.progressbar)

        self.mainLayout = QVBoxLayout()
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.addLayout(self.layout)
        self.mainLayout.addWidget(self.bottomBorder)
        self.setLayout(self.mainLayout)
        self.totalValue = 0

    def set_value(self, value):
        self.totalValue += value
        self.progressbar.setValue(self.totalValue)

    def set_max(self, value):
        self.progressbar.setMaximum(value)


class DownloadProgressWidget(BaseProgressWidget):
    def __init__(self, text='Downloading', parent=None):
        super(self.__class__, self).__init__(text, parent)
        style = """
        QProgressBar {
            border: 1px solid grey;
            border-radius: 5px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #37DA7E;
            width: 20px;
        }"""
        self.progressbar.setStyleSheet(style)


class UploadProgressWidget(BaseProgressWidget):
    def __init__(self, text='Uploading', parent=None):
        super(self.__class__, self).__init__(text, parent)
        style = """
        QProgressBar {
            border: 1px solid grey;
            border-radius: 5px;
            text-align: center;
        }

        QProgressBar::chunk {
            background-color: #88B0EB;
            width: 20px;
        }"""
        self.progressbar.setStyleSheet(style)


class ProgressDialog(QMainWindow):
    def __init__(self, title, icon):
        super().__init__()
        self.setWindowTitle(title)
        self.setWindowIcon(icon)
        self.resize(500, 110)
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)
        self.setCentralWidget(self.scrollArea)

        self.centralWidget = QWidget()
        self.scrollArea.setWidget(self.centralWidget)

        self.layout = QVBoxLayout()
        self.layout.setAlignment(QtCore.Qt.AlignTop)
        self.layout.setContentsMargins(0, 10, 0, 0)
        self.centralWidget.setLayout(self.layout)

        self.setStyleSheet("background-color: white")

    def addProgressbar(self, progressbar):
        self.layout.insertWidget(0, progressbar)

    def addProgress(self, type, title, size):
        if type not in ['Download', 'Upload']:
            raise str("type must 'Download' or 'Upload'")

        if type == 'Download':
            pb = DownloadProgressWidget(text=title)
        else:
            pb = UploadProgressWidget(text=title)
        pb.set_max(size)
        self.addProgressbar(pb)
        return pb


if __name__ == '__main__':
    def testProgressDialog():
        import random
        number = [x for x in range(1, 101)]
        progresses = []
        while len(progresses) <= 20: progresses.append(random.choice(number))
        print(progresses)
        app = QApplication([])
        pbs = ProgressDialog()
        for i in progresses:
            pb = pbs.addProgress(type='Download', title='download', size=100)
            pb.set_value(len(' ' * i))

        for i in progresses:
            pb = pbs.addProgress(type='Upload', title='upload', size=100)
            pb.set_value(len(' ' * i))
        # pb = pbs.addProgress(type='Download', title='download', size=100)
        # for i in range(0, 101):
        #     pb.set_value(' '*i)
        pbs.show()
        app.exec_()


    testProgressDialog()
