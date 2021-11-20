import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QLabel
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtWidgets import QVBoxLayout
from PyQt5.QtWidgets import QWidget

__version__ = "0.1"
__author__ = "dlha_ndphuc"

from PyQt5.uic import pyuic


class Server(QApplication):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # pyuic.loadUi("mainwindow.ui")


cal = QApplication(sys.argv)
view = pyuic.loadUi("mainwindow.ui")
view.show()
sys.exit(cal.exec())

