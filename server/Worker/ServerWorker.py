import os
import socket
from threading import Thread

from sqlalchemy.orm import sessionmaker

# from Model.User import User
from Model.User import User
from utils import get_file_properties
from settings import *
import re
import shutil
import sqlalchemy as db

engine = db.create_engine("sqlite:///fpt_implement.sqlite", connect_args={'check_same_thread': False})
connection = engine.connect()
DBSession = sessionmaker(bind=engine)
session = DBSession()

ALLOW_DELETE = False


class ServerWorker(Thread):
    def __init__(self, address, socket: socket.socket, host) -> None:
        Thread.__init__(self)
        self.cwd = SERVER_DATA_PATH
        self.client_address = address
        self.client_address_ip = address[0]
        self.client_address_port = address[1]
        self.client_socket = socket
        self.server_socket = None
        self.pasv_mode = False
        self.HOST = host
        self.rest = False
        self.pos = 0
        # Auth
        self.username = None
        self.is_authorization = False
        self.client_data_socket = None
        self.mode = None

        print("started")

    def run(self):
        self.send_message("220 Welcome.\r\n")
        while True:
            try:
                data = self.client_socket.recv(SIZE).rstrip()

                command = data.decode("utf-8")

                if not command:
                    break

                print(f"[COMMAND {self.client_address}] {command}")

            except socket.error as e:
                print("Error: ", e)
                break

            try:
                command, args = (
                    command[:4].upper().rstrip(),
                    command[4:].strip() or None,
                )
                func = getattr(self, command)
                func(args)
            except Exception as e:
                print(e)
                self.send_message(
                    "500 Syntax error, command unrecognized. "
                    "This may include errors such as command line too long.\r\n"
                )

    def send_message(self, message: str):
        self.client_socket.send(message.encode("utf-8"))

    # def create_data_socket(self):
    #     print("[DATA SOCKET {}] Create Data connection...".format(self.client_address))
    #     try:
    #         self.client_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #         self.client_data_socket.connect((self.client_address_ip, DATA_PORT))
    #     except Exception as e:
    #         print(
    #             "[DATA SOCKET {}] Start data connection error: ".format(
    #                 self.client_address
    #             )
    #             + str(e)
    #         )

    def create_data_socket(self):
        self.send_message("150 Opening data connection.\r\n")
        try:
            self.client_data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.pasv_mode:
                self.client_data_socket, self.client_address = self.server_socket.accept()
            else:
                self.client_data_socket.connect((self.client_address_ip, DATA_PORT))

            print("[DATA SOCKET {}] Create Data connection...".format(self.client_address))
        except socket.error as error:
            print("[SERVER ERROR]: ", error)

    def stop_data_socket(self):
        print("[DATA SOCKET {}] Stopping data connection...".format(self.client_address))
        try:
            if self.pasv_mode:
                self.server_socket.close()
            self.client_data_socket.close()
        except Exception as e:
            print(
                "[DATA SOCKET {}] Stop data connection error: "
                + str(e).format(self.client_address)
            )

    def send_data(self, data):
        self.client_data_socket.send(data)

    def recv_data(self):
        return self.client_data_socket.recv(SIZE)

    """
        FUNCS
    """

    def TYPE(self, type):
        self.mode = type
        if self.mode == "I":
            self.send_message("200 binary mode. \r\n")
        elif self.mode == "A":
            self.send_message("200 ASCII mode. \r\n")

    def PASV(self, command):
        print("PASV: ", command)
        self.pasv_mode = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.HOST, 0))
        self.server_socket.listen(5)
        address, port = self.server_socket.getsockname()
        print(address, port)
        text = f"227 Entering Passive Mode ({','.join(address.split('.'))},{port >> 8 & 0xFF},{port & 0xFF}).\r\n"
        # text = f"227 Entering Passive Mode ({','.join(address.split('.'))},{port}).\r\n"

        print(text)
        self.send_message(
            text
        )

    def PORT(self, command):
        print("[SERVER] PORT" + command)

    def LIST(self, dir_path):

        if not dir_path:
            print("NONE")
            path_name = os.path.abspath(os.path.join(self.cwd, "."))
            print("PATH 1 : ", path_name)
        else:
            path_name = os.path.abspath(os.path.join(self.cwd, dir_path))
            print("PATH 2 : ", path_name)

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
            # self.send_message("150 dir info.\r\n")
            for file in os.listdir(path_name):
                print(file)
                file_info = get_file_properties(os.path.join(path_name, file))
                self.send_data(file_info.encode())

        else:  # path_name is path of file
            print("LIST file")
            self.send_message("150 File info\n")
            file_info = os.path.basename(path_name)
            self.send_data(file_info + "\n")
            print("send")

        self.stop_data_socket()
        self.send_message("226 Closing data connection. \r\n")

    def PWD(self, command):
        self.send_message(f"{self.cwd}. \r\n")

    def CWD(self, dir_path):
        dir_path = os.path.join(self.cwd, dir_path)
        if not os.path.exists(dir_path) and not os.path.isdir(dir_path):
            self.send_message("CWD false, directory not exists. \r\n")
            return
        self.cwd = dir_path
        self.send_message("500 CWD Successfully!\r\n")

    def NLIST(self):
        pass

    def CDUP(self, command):
        path = os.path.join(self.cwd, "../..")
        self.cwd = os.path.abspath(path)
        self.send_message("500 CDUP Successfully!\r\n")

    def CAT(self, file_path):
        # ^READ content of one file
        path = os.path.join(self.cwd, file_path)

        if not os.path.exists(path) and os.path.isfile(path):
            self.send_message("CAT false, file not exists. \r\n")
            return

        # * Only accept txt and md file
        file_ext = re.search(REGEX_FILE_EXTENSION, path).group()
        if file_ext not in ACCEPT_CAT_FILE_TYPES:
            self.send_message("CAT false, only support *.txt or *.md file. \r\n")
            return

        self.send_message("200. Here file contents. \r\n")
        self.create_data_socket()

        with open(path, "rb") as file:
            file_contents = (
                file.read()
            )  # Read all content of file into a string variable
        self.send_data(file_contents)

        self.stop_data_socket()

    def MKD(self, dir_name):
        if not dir_name:
            self.send_message(f"MKD Failed - No directory name was provided!\r\n")
        path = os.path.join(self.cwd, dir_name)
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")

        else:
            # ^Create new dir with dir_)name provided
            try:
                os.mkdir(path)
                self.send_message(f"257 MKD Directory created - {dir_name}.\r\n")
            except OSError:
                self.send_message(
                    f"550 MKD failed - Directory {dir_name} already exists.\r\n"
                )

    def RMD(self, dir_name):
        if not dir_name:
            self.send_message(f"MKD Failed - No directory name was provided!\r\n")
        path = os.path.join(self.cwd, dir_name)

        # ^Check if user is authenticated
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")

        elif not ALLOW_DELETE:
            self.send_message(
                f"450 RMD failed - Detele operation not allow on this server! \r\n"
            )

        # ^If dir is not exists
        elif not os.path.exists(path):
            self.send_message(f"550 RMD failed - Directory {dir_name} not exists!\r\n")

        else:
            shutil.rmtree(path=path)
            self.send_message(f"250 RMD Directory deteled!\r\n")

    def DELE(self, file_name):
        path = os.path.join(self.cwd, file_name)

        # ^Check if user is authenticated
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")

        # ^If file or dir is not exists
        elif not os.path.exists(path):
            self.send_message(f"550 DELE failed File {file_name} not exists.\r\n")

        elif not ALLOW_DELETE:
            self.send_message(
                f"450 DELE failed - Detele operation not allow on this server! \r\n"
            )

        else:
            # ^Delete file
            os.remove(path)
            self.send_message("250 DELE File deleted.\r\n")

    """ Recive file from client """

    def PUT(self, file_name):
        # ^Check if user is authenticated
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")
            return

        self.send_message("200. Created data connection.\r\n")
        self.create_data_socket()

        # ^Open in write Binary mode
        with open(file_name, "wb") as file:
            data = self.recv_data()
            while data:
                file.write(data)
                data = self.recv_data()
            self.send_message("200. File recived.\r\n")

        self.stop_data_socket()

    def STOR(self, file_name):
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")
            return

        path = os.path.join(self.cwd, file_name)

        file_write_type = "wb" if self.mode == "I" else "w"

        self.create_data_socket()

        with open(path, file_write_type) as file:
            print("asdf")
            print(self.client_data_socket)
            data = self.client_data_socket.recv(SIZE)
            print("DATA: ", data)
            while data:
                print("DATA: ", data)
                file.write(data)
                data = self.client_data_socket.recv(SIZE)

        self.send_message("226 Transfer completed.\r\n")
        self.stop_data_socket()

    """ Send file to client """

    def GET(self, file_name):
        # ^Check if user is authenticated
        if not self.is_authorization:
            self.send_message("530 User not logged in!\r\n")
            return

        path = os.path.join(self.cwd, file_name)
        if not file_name:
            self.send_message(f"GET Failed - No file name was provided!\r\n")

        elif not os.path.exists(path):
            self.send_message(f"GET Failed - File {file_name} doesn't exist!\r\n")

        elif not os.path.isfile(path):
            self.send_message(f"GET Failed - {file_name} is not file!\r\n")

        else:
            self.create_data_socket()
            try:
                with open(path, "rb") as file:
                    data = file.read(SIZE)
                    while data:
                        self.send_data(data)
                        data = file.read(SIZE)
                    self.send_message("200. File sent.\r\n")
            except OSError as e:
                self.send_message(f"GET error - Please try again - {e}.\r\n")
                self.stop_data_socket()

            self.stop_data_socket()

    def REST(self, position):
        self.pos = position
        self.rest = True
        self.send_message("250 File position reseted.\r\n")

    def RETR(self, file_name):
        path = os.path.join(self.cwd, file_name)
        print(path)

        if not os.path.exists(path):
            return

        file_read_type = "rb" if (self.mode == "I") else "r"

        file = open(path, file_read_type)

        self.create_data_socket()

        if self.rest:
            file.seek(self.pos)
            self.rest = False

        try:
            # with open(path, file_read_type) as file:

            with open(path, "rb") as file:
                data = file.read(SIZE)
                while data:
                    self.send_data(data)
                    data = file.read(SIZE)

            self.stop_data_socket()
            self.send_message("226 Transfer completed.\r\n")
        except OSError as e:
            self.send_message(f"GET error - Please try again - {e}.\r\n")
            self.stop_data_socket()

    """
        AUTH FUNCS
    """

    def USER(self, user):
        if user:
            print("USER: " + user)
            # Need verification here
            self.username = user
            self.send_message("331 Done, need password.\r\n")
        else:
            self.send_message("503 OK - Syntax error.\r\n")

    def PASS(self, password):
        if password:
            print("PASS :" + password)
            # Need verification here
            if not self.username:
                self.send_message("503 Bad sequence of commands - No username error.\r\n")

            user = session.query(User).filter_by(username=self.username).first()
            if user.password != password:
                self.send_message("530 Login incorrect - Wrong username or password error.\r\n")

            self.is_authorization = True
            self.send_message("230 Logged on - Login successfully!\r\n")
        else:
            self.send_message("503 Bad sequence of commands - Syntax error\r\n")

    def QUIT(self, *args):
        print("QUIT")
        self.is_authorization = False
        self.send_message("221 Goodbye!\r\n")

    """
        HELP
    """

    def HELP(self, *args):
        self.send_message("Ngu.\r\n")
