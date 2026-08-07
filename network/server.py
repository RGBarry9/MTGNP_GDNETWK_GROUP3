# network/server.py
import socket
import select
from config.settings import HOST, PORT, MAX_PLAYERS
from network.connection import Connection


class Server:
    """TCP server that accepts exactly 2 players."""

    def __init__(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server.bind((HOST, PORT))
        self.server.listen(MAX_PLAYERS)
        self.connections = []
        self.running = False

    def start(self):
        """Accept connections from exactly 2 players."""
        print(f"Server listening on {HOST}:{PORT}")

        while len(self.connections) < MAX_PLAYERS:
            client_socket, address = self.server.accept()
            connection = Connection(client_socket)
            self.connections.append(connection)
            print(f"Player connected: {address}")

        print("Lobby full.")
        self.running = True
        return self.connections

    def stop(self):
        """Stop the server."""
        self.running = False
        for conn in self.connections:
            conn.close()
        self.server.close()

    def broadcast(self, message, exclude=None):
        """Send a message to all connected players."""
        for conn in self.connections:
            if conn != exclude:
                conn.send(message)

    def get_connections(self):
        """Return all connections."""
        return self.connections