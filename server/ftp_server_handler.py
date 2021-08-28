from ftplib import error_perm
import os
import socket
from threading import Thread
import threading
from settings import *


class FtpServerHandler(Thread):
    def __init__(self, address, socket: socket.socket) -> None:
        Thread.__init__(self)
        self.cwd = SERVER_DATA_PATH
        self.client_address = address
        self.client_socket = socket
        self.client_data_socket = None
        self.mode = None

    def run(self):
        self.send_message("220")
        while True:
            try:
                data = self.client_socket.recv(SIZE).rstrip()

                try:
                    command = data.decode("utf-8")
                except AttributeError as err:
                    command = data

                if not command:
                    break

                print(f"[COMMAND {self.client_address}] {command}")

            except Exception as e:
                print("Error: " + str(e))
                break

            try:
                command, args = (
                    command[:4].upper().rstrip(),
                    command[4:].strip() or None,
                )
                func = getattr(self, command)
                func(args)
            except Exception as e:
                self.send_message('500 Syntax error, command unrecognized. '
                    'This may include errors such as command line too long.\r\n')

    def send_message(self, message: str):
        self.client_socket.send(message.encode("utf-8"))

    def create_data_socket(self):
        print("[DATA SOCKET {}] Create Data connection...".format(self.client_address))
        try:
            self.client_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_data_socket.connect((self.client_address, DATA_PORT))
        except Exception as e:
            print(
                "[DATA SOCKET {}] Start data connection error: ".format(
                    self.client_address
                )
                + str(e)
            )

    def stop_data_socket(self):
        print("[DATA SOCKET {}] Stoping data connection...".format(self.client_address))
        try:
            self.client_data_socket.close()
        except Exception as e:
            print(
                "[DATA SOCKET {}] Stop data connection error: "
                + str(e).format(self.client_address)
            )

    def send_data(self, data):
        self.client_data_socket.send(data.encode("utf-8"))

    def TYPE(self, type):
        self.mode = type
        if self.mode == 'I':
            self.send_message('200 binary mode. \r\n')
        elif self.mode == 'A':
            self.send_message('200 ASCII mode. \r\n')

    def LIST(self, dir_path):

        if not dir_path:
            path_name = os.path.abspath(os.path.join(self.cwd, "."))
            print(path_name)
        else:
            path_name = os.path.abspath(os.path.join(self.cwd, dir_path))
            print(path_name)

        if not os.path.exists(path_name):
            self.send_message(
                "550 Requested action not taken. File unavailable (e.g., file not found, no access)."
            )
            return

        self.create_data_socket()
        for file in os.listdir(path_name):
            file_info = os.path.basename(file)
            self.send_message(file_info + "\r\n")

        self.stop_data_socket()
        self.send_message("226 Closing data connection.")
