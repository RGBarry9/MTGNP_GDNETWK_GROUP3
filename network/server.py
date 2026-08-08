import socket
import threading

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

        # Without this, restarting the server quickly after stopping it
        # (very common during dev/testing) fails with "Address already
        # in use" for ~30-60s while the old socket sits in TIME_WAIT.
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.server.bind((HOST, PORT))

        # Backlog bigger than MAX_PLAYERS on purpose: a 3rd/4th/... client
        # can still complete the TCP handshake and sit in the OS backlog
        # even though we'll never seat them, and we want _reject_extra_
        # connections() below to be able to accept() and reject them
        # promptly instead of leaving them queued indefinitely.
        self.server.listen(MAX_PLAYERS + 4)

        self.connections = []

    def start(self):

        print(f"Server listening on {HOST}:{PORT}")

        while len(self.connections) < MAX_PLAYERS:

            client_socket, address = self.server.accept()

            # Nagle's algorithm can add up to ~40ms of latency to every
            # small PDU we send; MTGNP messages are small and latency
            # sensitive (priority windows, heartbeats), so disable it.
            client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

            connection = Connection(client_socket)

            self.connections.append(connection)

            print(f"Player connected: {address}")

        print("Lobby full.")

        # RFC 0001 SS5.1: "Additional connection attempts after two
        # players are seated MUST be refused." Previously the server
        # simply stopped calling accept() once MAX_PLAYERS was reached,
        # which let a 3rd client's TCP handshake complete (it sits in
        # the kernel backlog) while the application never touched that
        # socket - the 3rd client would just sit there until its own
        # PING/PONG heartbeat timed out, with no indication of *why*.
        # Keep accepting in the background for the rest of the server's
        # life specifically so we can send an explicit rejection and
        # close the socket right away instead.
        threading.Thread(target=self._reject_extra_connections, daemon=True).start()

        return self.connections

    def _reject_extra_connections(self):
        """
        Accept and immediately refuse any connection beyond the two
        seats already filled, sending a LOBBY_FULL ERROR PDU first so
        the client can show a real reason instead of just timing out.
        """
        while True:
            try:
                client_socket, address = self.server.accept()
            except OSError:
                return

            print(f"Rejecting extra connection from {address}: lobby full.")

            try:
                client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
                connection = Connection(client_socket)
                connection.send({
                    "type": "ERROR",
                    "seq_num": 0,
                    "code": "LOBBY_FULL",
                    "message": "Lobby is full (2/2 players already connected). Try again later.",
                })
            except OSError:
                pass
            finally:
                try:
                    client_socket.close()
                except OSError:
                    pass