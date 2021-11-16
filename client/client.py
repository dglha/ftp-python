import socket
from Worker.CommandLineWorker import CommandLineWorker


def command_line():
    server_ip = input("Server ip: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect((server_ip, 21))
    print("Connect successfully!")

    handler = CommandLineWorker(client)
    handler.start()


if __name__ == "__main__":
    command_line()
