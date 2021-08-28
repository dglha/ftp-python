import os 
import logging
import socket
import threading
import sys
from ftplib import FTP

def handler():
    pass

def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # f = FTP('192.168.1.132', 21)
    client.connect(('192.168.1.132', 21))

    while True:
        data = client.recv(1024).decode('utf-8')
        if data:
            print(data)

        command = input("> ")
        client.send(command.encode('utf-8'))
        

if __name__ == "__main__":
    main()