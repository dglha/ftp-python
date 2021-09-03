import os 
import logging
import socket
import threading
import sys
from ftp_client_handler import FtpClientHandler

def main():
    server_ip = input("Server ip: ")
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # f = FTP('192.168.1.132', 21)
    client.connect((server_ip, 21))
    print("Connect successfully!")

    handler = FtpClientHandler(client)
    handler.start()

if __name__ == "__main__":
    main()