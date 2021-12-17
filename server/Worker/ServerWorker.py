import os
import socket
from functools import wraps
from threading import Thread

from sqlalchemy.orm import sessionmaker

# from Model.User import User
from Model.User import User
from utils import get_file_properties, get_sys_info
from settings import *
import re
import shutil
import sqlalchemy as db
from pathlib import Path

from Worker.UserWorker import check_user


def authorization(func):
    # def decorator(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        is_auth = self.is_authorization
        # return check_authorization(is_auth)(func)(self, *args, **kwargs)
        if not is_auth:
            return self.client_socket.send("530 User not logged in!".encode("utf-8"))
        return func(self, *args, **kwargs)

    return wrapper
    # return decorator


def check_write_permission(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        is_write = self.is_write
        if not is_write:
            return self.send_message("450 - Put operation not allow on this user! \r\n")
        return func(self, *args, **kwargs)
    return wrapper


def check_delete_permission(func):
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        is_delete = self.is_delete
        if not is_delete:
            return self.send_message("450 - Delete operation not allow on this user! \r\n")
        return func(self, *args, **kwargs)
    return wrapper


class ServerWorker(Thread):
    def __init__(self, address, socket: socket.socket, host) -> None:
        Thread.__init__(self)
        self.is_kill = False

        self.cwd = Path(SERVER_DATA_PATH)
        self.client_address = address
        self.client_address_ip = address[0]
        self.client_address_port = address[1]
        self.client_socket = socket
        self.server_socket = None
        self.pasv_mode = False
        self.HOST = host
        self.rest = False
        self.pos = 0
        self.rnfr = Path()
        # Auth
        self.username = None
        self.is_authorization = False
        # User permission
        self.is_write = False
        self.is_delete = False

        self.client_data_socket = None
        self.mode = None

        # Each user is a private space
        # First initialize
        self.root_cwd = self.cwd

        print("started")

    def terminate(self):
        self.is_kill = True

    def initialize(self):
        # Each user is a private space
        self.root_cwd = self.root_cwd.joinpath(self.username)
        # Create folder
        if not self.root_cwd.exists():
            self.root_cwd.mkdir()
        self.cwd = self.root_cwd

    def run(self):
        self.send_message("220 Welcome.\r\n")
        # self.welcome()
        while not self.is_kill:
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
                print("[Exception]: ", e)
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

    def receive_data(self):
        return self.client_data_socket.recv(SIZE)

    """
        FUNCS
    """

    def TYPE(self, type_):
        """
        Sets the transfer mode (ASCII/Binary)
        :param type_: "I": Binary, "A": ASCII
        :return: 200 Code
        """
        self.mode = type_
        if self.mode == "I":
            self.send_message("200 binary mode. \r\n")
        elif self.mode == "A":
            self.send_message("200 ASCII mode. \r\n")

    def PASV(self, *args):
        """
        Enter passive mode

        :return: 227 Code (h1,h2,h3,h4,p1,p2): h1-4: IP Address, p1-2: Port number
                 p1 * 256 + p2
        """
        self.pasv_mode = True
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Pick free port number -> bind to 0
        self.server_socket.bind((self.HOST, 0))
        self.server_socket.listen(5)
        address, port = self.server_socket.getsockname()
        p1 = port // 256
        p2 = port % 256
        # text = f"227 Entering Passive Mode ({','.join(address.split('.'))},{port >> 8 & 0xFF},{port & 0xFF}).\r\n"
        text = f"227 Entering Passive Mode ({','.join(address.split('.'))},{p1},{p2}).\r\n"
        print(text)
        self.send_message(text)

    def PORT(self, command):
        """
        Specifies an address and port to which the server should connect.

        :param command: h1,h2,h3,h4,h5
        :return:
        """
        # TODO - implement PORT command
        pass

    @authorization
    def LIST(self, dir_path):
        """
        Returns information of a file or directory if specified,
        else information of the current working directory is returned.

        :param dir_path: path of a file or directory
        :return: 266. Closing data connection. List done
        """

        if not dir_path:
            # path_name = os.path.abspath(os.path.join(self.cwd, "."))
            path_name = self.cwd.absolute()
        else:
            # path_name = os.path.abspath(os.path.join(self.cwd, dir_path))
            path_name = self.cwd.joinpath(dir_path)
        if not os.path.exists(path_name):
            self.send_message(
                "550 Requested action not taken. File unavailable (e.g., file not found, no access)."
            )
            return

        self.create_data_socket()

        # if os.path.isdir(path_name):
        if path_name.is_dir():
            # If path_name is dir
            # for file in os.listdir(path_name):
            for file in path_name.iterdir():
                file_info = get_file_properties(file.absolute())
                self.send_data((file_info + "\r\n").encode())

        else:  # path_name is path of file
            file_info = os.path.basename(path_name)
            self.send_data((file_info + "\r\n").encode())

        self.stop_data_socket()
        self.send_message("226 Closing data connection. \r\n")

    def NLST(self, dir_path):
        """
        Returns a list of file names in a specified directory.

        :param: dir_path: path to check
        :return: 266. Closing data connection. NList done
        """
        self.LIST(dir_path)

    @authorization
    def PWD(self, *args):
        """
        Print working directory.

        :return: 257 Returns the current directory of the host.
        """
        # print(self.cwd)
        print(self.cwd)
        self.send_message(f"257 \"{self.cwd}\". \r\n")

    @authorization
    def CWD(self, dir_path):
        """
        Change working directory.

        :param dir_path: path to go
        :return: 250 Requested file action okay, completed.
        """
        # dir_path = dir_path.endswith(os.path.sep) and dir_path or os.path.join(self.cwd, dir_path)
        dir_path = Path(dir_path) if dir_path.endswith(os.path.sep) else self.cwd.joinpath(dir_path)
        # if not os.path.exists(dir_path) and not os.path.isdir(dir_path):
        if self.root_cwd not in dir_path.parents:
            dir_path = self.root_cwd
        elif not dir_path.exists() and not dir_path.is_dir():
            self.send_message("CWD false, directory not exists. \r\n")
            return
        self.cwd = dir_path
        self.send_message("250 CWD Successfully!\r\n")

    @authorization
    def CDUP(self, *args):
        """
        Change to Parent Directory.

        :return: 200 The requested action has been successfully completed.
        """
        # path = os.path.join(self.cwd, "..")
        self.cwd = self.cwd.parent
        # self.cwd = os.path.abspath(path)
        self.send_message("200 CDUP Successfully!\r\n")

    @authorization
    def CAT(self, file_path):
        """
        Display content of file (md, txt only)

        :param file_path: path of file (name)
        :return: 266. Closing data connection. Cat done
        """
        # ^READ content of one file
        path = os.path.join(self.cwd, file_path)

        if not os.path.exists(path) and os.path.isfile(path):
            self.send_message("CAT false, file not exists.\r\n")
            return

        # * Only accept txt and md file
        file_ext = re.search(REGEX_FILE_EXTENSION, path).group()
        if file_ext not in ACCEPT_CAT_FILE_TYPES:
            self.send_message("CAT false, only support *.txt or *.md file.\r\n")
            return

        # self.send_message("200. Here file contents. \r\n")
        self.create_data_socket()

        with open(path, "rb") as file:
            file_contents = (
                file.read()
            )  # Read all content of file into a string variable
        self.send_data(file_contents)

        self.stop_data_socket()
        self.send_message("226 Closing data connection. \r\n")

    @authorization
    def MKD(self, dir_name):
        """
        Make directory.

        :param dir_name: Directory name
        :return: 257 Directory created.
        """
        if not dir_name:
            self.send_message(f"501 MKD Failed - No directory name was provided!\r\n")
        # path = os.path.join(self.cwd, dir_name)
        path = self.cwd.joinpath(dir_name)

        try:
            os.mkdir(path)
            self.send_message(f"257 MKD Directory created - {dir_name}.\r\n")
        except OSError as e:
            print(e)
            self.send_message(
                f"550 MKD failed - Directory {dir_name} already exists.\r\n"
            )

    @authorization
    @check_delete_permission
    def RMD(self, dir_name):
        """
        Remove a directory.

        :param dir_name: Directory name
        :return: 250 Directory deleted
        """
        if not dir_name:
            self.send_message(f"501 RMD Failed - No directory name was provided!\r\n")
        # path = os.path.join(self.cwd, dir_name)
        path = self.cwd.joinpath(dir_name)

        # if not self.is_delete:
        #     self.send_message(
        #         f"450 RMD failed - Detele operation not allow on this server! \r\n"
        #     )

        # ^If dir is not exists
        # elif not os.path.exists(path):
        if not path.exists():
            self.send_message(f"550 RMD failed - Directory {dir_name} not exists!\r\n")

        else:
            # shutil.rmtree(path=path)
            try:
                path.rmdir()
                self.send_message(f"250 RMD Directory deteled!\r\n")
            except Exception as e:
                self.send_message(f"550 RMD failed - {e}\r\n")

    @authorization
    @check_delete_permission
    def DELE(self, file_name):
        """
        Delete file.

        :param file_name: File to delete
        :return: 250 File deleted
        """
        # path = os.path.join(self.cwd, file_name)
        path = self.cwd.joinpath(file_name)
        print(path)

        # ^If file or dir is not exists
        # if not os.path.exists(path):
        if not path.exists():
            self.send_message(f"550 DELE failed File {file_name} not exists.\r\n")

        # elif not self.is_delete:
        #     self.send_message(
        #         f"450 DELE failed - Detele operation not allow on this server! \r\n"
        #     )

        elif not path.is_file():
            self.send_message(f"550 DELE failed, {file_name} is directory.\r\n")
        else:
            # ^Delete file
            os.remove(path)
            self.send_message("250 DELE File deleted.\r\n")

    @authorization
    @check_write_permission
    def RNFR(self, file_name):
        """
        Choose file or dir to be rename.

        :param file_name: Directory/File name
        :return: 
        """
        if not file_name:
            self.send_message(f"501 RNFR Failed - No directory name was provided!\r\n")
        # path = os.path.join(self.cwd, dir_name)
        path = self.cwd.joinpath(file_name)

        if not path.exists():
            self.send_message(f"550 RNTO failed File or Direcotry {file_name} not exists.\r\n")

        self.rnfr = path
        self.send_message(f"350 RNTO Done, waitting for next command\r\n")

    @authorization
    @check_write_permission
    def RNTO(self, file_name):
        """
        Rename to.

        :param file_name: name
        :return: 257 Directory created.
        """
        if not file_name:
            self.send_message(f"501 RNTO Failed - No directory name was provided!\r\n")
        # path = os.path.join(self.cwd, dir_name)
        path = self.cwd.joinpath(file_name)

        try:
            self.rnfr.rename(path)
        except Exception as e:
            print(e)
            self.send_message(
                f"550 RNTO failed.\r\n"
            )
        self.send_message(f"250 RNTO Successfully.\r\n")


    """
        SOCKET RECEIVE - SEND FUNC
    """

    @authorization
    @check_write_permission
    def PUT(self, file_name):
        """"""
        # ^Check if user is authenticated
        # if not self.is_authorization:
        #     self.send_message("530 User not logged in!\r\n")
        #     return

        self.send_message("200. Created data connection.\r\n")
        self.create_data_socket()

        # ^Open in write Binary mode
        with open(file_name, "wb") as file:
            data = self.receive_data()
            while data:
                file.write(data)
                data = self.receive_data()
            self.send_message("200. File received.\r\n")

        self.stop_data_socket()

    @authorization
    @check_write_permission
    def STOR(self, file_name):
        """
        Accept the data and to store the data as a file at the server site

        :param file_name: File to send
        :return: 226 Transfer completed
        """
        # if not self.is_authorization:
        #     self.send_message("530 User not logged in!\r\n")
        #     return

        path = os.path.join(self.cwd, file_name)

        file_write_type = "wb" if self.mode == "I" else "w"

        self.create_data_socket()

        with open(path, file_write_type) as file:
            data = self.client_data_socket.recv(SIZE)
            while data:
                file.write(data)
                data = self.client_data_socket.recv(SIZE)

        self.send_message("226 Transfer completed.\r\n")
        self.stop_data_socket()

    """ Send file to client """

    @authorization
    def GET(self, file_name):
        # ^Check if user is authenticated
        # if not self.is_authorization:
        #     self.send_message("530 User not logged in!\r\n")
        #     return

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

    # def REST(self, position):
    #     self.pos = position
    #     self.rest = True
    #     self.send_message("250 File position reseted.\r\n")

    @authorization
    def RETR(self, file_name):
        """
        Retrieve a copy of the file

        :param file_name: Name of file
        :return: 226 Transfer completed
        """
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
        AUTHENTICATION FUNCS
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
            print("PASS :")
            # Need verification here
            if not self.username:
                self.send_message("503 Bad sequence of commands - No username error.\r\n")
                return

            check, user = check_user(self.username, password)
            if not check:
                self.send_message("530 Login incorrect - Wrong username or password error.\r\n")
                self.username = None
                return
            # elif user.password != password:
            #     self.send_message("530 Login incorrect - Wrong username or password error.\r\n")
            #     self.username = None
            #     return

            self.is_authorization = True
            self.is_write = bool(user.is_write)
            self.is_delete = bool(user.is_delete)

            print(f"{self.is_write=}, {self.is_delete=}")
            self.initialize()

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

    """
        UTILS FUNC
    """

    def SYS(self, *args):
        """
        Get system info

        :return: 215 Get system type
        """
        info = get_sys_info()
        text = ""
        for key in info.keys():
            text += f"{key}: {info[key]}\r\n"

        self.send_message("215 System information:\r\n" + text)

    @authorization
    def SIZE(self, file_name):
        path = os.path.join(self.cwd, file_name)
        if not os.path.exists(path):
            return

        # self.create_data_socket()

        size = str(os.path.getsize(path))

        # self.send_data(size.encode())

        # self.stop_data_socket()
        self.send_message(f"213 {size}\r\n")

    def welcome(self):
        info = get_sys_info()
        text = ""
        for key in info.keys():
            text += f"{key}: {info[key]}, "

        self.send_message("215 Welcome." + text)
