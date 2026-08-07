# network/client.py
import socket
from config.settings import HOST, PORT
from network.connection import Connection


class Client:
    """TCP client that connects to the MTGNP server."""

    def __init__(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect((HOST, PORT))
        self.connection = Connection(sock)
        print(f"Connected to server at {HOST}:{PORT}")
        self.running = True

    def send(self, message):
        """Send a message to the server."""
        self.connection.send(message)

    def receive(self):
        """Receive a message from the server."""
        return self.connection.receive()

    def close(self):
        """Close the connection."""
        self.running = False
        self.connection.close()

    def start_message_loop(self, message_handler):
        """
        Start the main message loop.
        
        Args:
            message_handler: Function to handle incoming messages
        """
        while self.running:
            message = self.receive()
            if message is None:
                print("Disconnected from server.")
                break
            message_handler(message)