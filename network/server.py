import socket

from config.settings import HOST
from config.settings import PORT
from config.settings import MAX_PLAYERS

from network.connection import Connection


class Server:

    def __init__(self):

        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.server.bind((HOST, PORT))

        self.server.listen(MAX_PLAYERS)

        self.connections = []

    def start(self):

        print(f"Server listening on {HOST}:{PORT}")

        while len(self.connections) < MAX_PLAYERS:

            client_socket, address = self.server.accept()

            connection = Connection(client_socket)

            self.connections.append(connection)

            print(f"Player connected: {address}")

        print("Lobby full.")

        return self.connections