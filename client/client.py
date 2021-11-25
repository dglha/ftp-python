import socket

from PyQt5 import QtWidgets
import sys
from Worker.CommandLineWorker import CommandLineWorker
from GUI.ClientGUI import ClientGUI


def command_line():
    server_ip = input("Server ip: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 21))
    print("Connect successfully!")

    handler = CommandLineWorker(client)
    handler.start()


def gui():
    app = QtWidgets.QApplication(sys.argv)

    window = ClientGUI()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    gui()
