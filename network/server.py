import socket

from config.settings import (
    HOST,
    PORT,
    MAX_PLAYERS
)

from network.connection import Connection


class Server:

    def __init__(self, verbose=False):

        self.verbose = verbose

        self.server = socket.socket(
            socket.AF_INET,
            socket.SOCK_STREAM
        )

        self.server.setsockopt(
            socket.SOL_SOCKET,
            socket.SO_REUSEADDR,
            1
        )

        self.server.bind(
            (HOST, PORT)
        )

        self.server.listen(
            MAX_PLAYERS
        )

        self.connections = []

    def start(self):

        print(
            f"Server listening on "
            f"{HOST}:{PORT}"
        )

        while len(self.connections) < MAX_PLAYERS:

            client_socket, address = (
                self.server.accept()
            )

            connection = Connection(
                client_socket,
                verbose=self.verbose,
                label=f"SERVER {address}"
            )

            self.connections.append(
                connection
            )

            print(
                f"Player connected: {address}"
            )

        print("Lobby full.")

        return self.connections

    def close(self):

        for connection in self.connections:
            connection.close()

        try:
            self.server.close()
        except OSError:
            pass