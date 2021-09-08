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
        self.client_address_ip = address[0]
        self.client_address_port = address[1]
        self.client_socket = socket
        # Auth
        self.username = None
        self.is_authorization = False
        self.client_data_socket = None
        self.mode = None

    def run(self):
        self.send_message("220")
        while True:
            try:
                data = self.client_socket.recv(SIZE).rstrip()

                command = data.decode("utf-8")

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
                self.send_message(
                    "500 Syntax error, command unrecognized. "
                    "This may include errors such as command line too long.\r\n"
                )

    def send_message(self, message: str):
        self.client_socket.send(message.encode("utf-8"))

    def create_data_socket(self):
        print("[DATA SOCKET {}] Create Data connection...".format(self.client_address))
        try:
            self.client_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.client_data_socket.connect((self.client_address_ip, DATA_PORT))
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

    """
        FUNCS
    """

    def TYPE(self, type):
        self.mode = type
        if self.mode == "I":
            self.send_message("200 binary mode. \r\n")
        elif self.mode == "A":
            self.send_message("200 ASCII mode. \r\n")

    def LIST(self, dir_path):

        if not dir_path:
            print("NONE")
            path_name = os.path.abspath(os.path.join(self.cwd, "."))
            # print(path_name)
        else:
            path_name = os.path.abspath(os.path.join(self.cwd, dir_path))
            # print(path_name)

        if not self.is_authorization:
            self.send_message("530 User not logged in!")
            return

        if not os.path.exists(path_name):
            self.send_message(
                "550 Requested action not taken. File unavailable (e.g., file not found, no access)."
            )
            return
        
        self.create_data_socket()
        
        if os.path.isdir(path_name):
            # If path_name is dir
            print("LIST dir")
            self.send_message("150 dir info\n")
            for file in os.listdir(path_name):
                file_info = os.path.basename(file)
                self.send_data(file_info + "\n")

        else: # path_name is path of file
            print("LIST file")
            self.send_message("150 File info\n")
            file_info = os.path.basename(path_name)
            self.send_data(file_info + "\n")
            print("send")

        self.stop_data_socket()
        self.send_message("226 Closing data connection.")

    def PWD(self, command):
        self.send_message(f"{self.cwd}. \r\n")

    def CWD(self, dir_path):
        dir_path = os.path.join(self.cwd, dir_path)
        if not os.path.exists(dir_path) and not os.path.isdir(dir_path):
            self.send_message("CWD false, directory not exists. \r\n")
            return
        self.cwd = dir_path
        self.send_message("500 CWD Successfully!")

    def NLIST(self):
        pass

    def CDUP(self, command):
        path = os.path.join(self.cwd, '..')
        print(path)
        self.cwd = os.path.abspath(path)
        self.send_message("500 CDUP Successfully!")

        


    """
        AUTH FUNCS
    """

    def USER(self, user):
        if user:
            print("USER: " + user)
            # Need verification here
            self.username = user
            self.send_message("200 OK - Need password")
        else:
            self.send_message("404 OK - Sytax error")

    def PASS(self, password):
        if password:
            print("PASS :" + password)
            # Need verification here
            self.is_authorization = True
            self.send_message("200 OK - Login successfully!")
        else:
            self.send_message("404 OK - Sytax error")

    def HELP(self, *args):
        self.send_message('Ngu')

    
