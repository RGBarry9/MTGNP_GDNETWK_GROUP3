import socket

from config.settings import (
    HOST,
    PORT
)

from network.connection import Connection


class Client:

    def __init__(self, verbose=False):

        sock = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        sock.connect(
            (HOST, PORT)
        )

        self.connection = Connection(
            sock,
            verbose=verbose,
            label="CLIENT"
        )

        print(
            "Connected to server."
        )