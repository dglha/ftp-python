from settings import DATA_PORT
from settings import SIZE
import socket
from threading import Thread


class MessageHandler(Thread):
    def __init__(self, socket: socket.socket) -> None:
        Thread.__init__(self)
        self.socket = socket

    def run(self):
        print("syaty")
        while True:
            msg = self.socket.recv(SIZE).strip()
            print(msg.decode("utf-8"))
            print(">>> ", end="")


class FtpClientHandler(Thread):
    def __init__(self, socket: socket.socket) -> None:
        Thread.__init__(self)
        self.command_socket = socket
        self.data_socket = None
        self.is_authorized = False

    def run(self):
        # msg_handler = MessageHandler(self.command_socket)
        # msg_handler.start()
        while True:
            try:
                msg = self.command_socket.recv(SIZE).strip().rstrip()
                if not msg:
                    break

                print(msg.decode("utf-8"))
                command = input(">>> ")
                if not command:
                    command = input(">>> ")

            except Exception as e:
                print("ERROR: " + str(e))

            try:
                command, args = (
                    command[:4].upper().rstrip(),
                    command[4:].strip() or None,
                )
                func = getattr(self, command)
                func(args)
            except Exception as e:
                # print(e)
                print("Command not found. Please type h or HELP for help!")
                cmd = command + " " + args if args else ""
                if not cmd:
                    print("NULL")
                self.command_socket.send(cmd.encode("utf-8"))

    """
        DATA FUNCS
    """

    def create_data_socket(self):
        try:
            self.data_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.data_socket.bind(
                (socket.gethostbyname(socket.gethostname()), DATA_PORT)
            )
            self.data_socket.listen(5)
        except Exception as e:
            print("Error when create data connection")
            print(e)

    def stop_data_socket(self):
        try:
            self.data_socket.close()
        except Exception as e:
            print("Error when close data connection")
            print(e)

    """
        HELPER
    """

    def send_message(self, msg: str):
        self.command_socket.send(msg.encode("utf-8"))

    """
        AUTH FUNCS
    """

    def USER(self, user):
        self.command_socket.send("USER ".encode("utf-8") + user.encode("utf-8"))
        print("send")

    def PASS(self, password):
        command = "PASS " + str(password)
        self.command_socket.send(command.encode("utf-8"))
        self.is_authorized = True

    """
        FUNCS
    """

    def LIST(self, dir_path):
        if not dir_path:
            path_name = "."
        else:
            path_name = dir_path

        command = "LIST " + str(path_name)
        self.create_data_socket()
        self.send_message(command)

        if not self.is_authorized:
            return

        res_socket, address = self.data_socket.accept()
        while True:
            msg = res_socket.recv(SIZE).decode()
            if not msg:
                break
            print(msg)
        self.stop_data_socket()

    def CWD(self, dir_path):
        command = "CWD " + str(dir_path)
        if not self.is_authorized:
            return
        self.command_socket.send(command.encode("utf-8"))

    def CDUP(self, *args):
        command = "CDUP"
        if not self.is_authorized:
            return
        self.command_socket.send(command.encode("utf-8"))

    def PWD(self, *args):
        command = "PWD"
        if not self.is_authorized:
            return
        self.send_message(command)

    def CAT(self, file_path):
        command = "CAT " + file_path
        if not self.is_authorized:
            return
        self.create_data_socket()
        self.send_message(command)
        res_socket, address = self.data_socket.accept()
        while True:
            msg = res_socket.recv(SIZE).decode()
            if not msg:
                break
            print(msg)
        self.stop_data_socket()

    def GET(self, file_name):
        command = "GET " + file_name
        if not self.is_authorized:
            return

        self.create_data_socket()
        self.send_message(command)

        res_socket, address = self.data_socket.accept()
        print(res_socket)
        with open(file_name, "wb") as file:
            while True:
                data = res_socket.recv(SIZE)
                if not data:
                    break
                file.write(data) 
        self.stop_data_socket()

        
