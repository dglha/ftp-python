import os
import logging
import socket
import sys
from threading import Thread

from PyQt5.QtWidgets import QApplication

from GUI.ServerGUI import ServerGUI
from settings import *
from Worker.ServerWorker import ServerWorker

# Generate host
HOST = socket.gethostbyname(socket.gethostname())


# Start socket server
def server_listener():
    print('[SERVER] Starting...')
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    print("[SERVER] Server started, listening on {}".format(s.getsockname()))
    s.listen(5)
    print('[SERVER] Server is listening')

    while True:
        client_socket, address = s.accept()
        print("Accept")
        handler = ServerWorker(address=address, socket=client_socket, host=HOST)
        handler.start()
        print("[SERVER] New connection from {}".format(address))


def gui():
    app = QApplication(sys.argv)
    ui = ServerGUI()
    ui.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    # listener = Thread(target=server_listener)
    # listener.start()

    gui()
