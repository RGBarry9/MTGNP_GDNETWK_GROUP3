import socket

from config.settings import HOST
from config.settings import PORT

from network.connection import Connection


class Client:

    def __init__(self):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.connect((HOST, PORT))

        self.connection = Connection(sock)

        print("Connected to server.")