import os 
import logging
from ftp_server_handler import FtpServerHandler
import socket
from threading import Thread
from settings import *


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

    while(True):
        client_socket, address = s.accept()
        handler = FtpServerHandler(address=address, socket = client_socket)
        handler.start()
        print("[SERVER] New connection from {}".format(address))

if __name__ == "__main__":
    listener = Thread(target=server_listener)
    listener.start()
