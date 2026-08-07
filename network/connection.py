import socket

from protocol.framing import (
    create_packet,
    HEADER_SIZE
)


class Connection:

    def __init__(
        self,
        sock: socket.socket,
        verbose: bool = False,
        label: str = "CONNECTION"
    ):

        self.socket = sock
        self.verbose = verbose
        self.label = label

    def send(self, message: dict):
        """
        Send one MTGNP PDU using the required
        4-byte big-endian length prefix.
        """

        packet = create_packet(message)

        if self.verbose:
            print(
                f"[{self.label} SEND] {message}"
            )

        self.socket.sendall(packet)

    def receive(self):
        """
        Receive exactly one MTGNP PDU.
        """

        header = self._receive_exact(
            HEADER_SIZE
        )

        if header is None:
            return None

        length = int.from_bytes(
            header,
            byteorder="big"
        )

        if length > 65535:
            raise ValueError(
                f"PDU exceeds 65535 bytes: {length}"
            )

        payload = self._receive_exact(
            length
        )

        if payload is None:
            return None

        from protocol.serializer import decode

        message = decode(payload)

        if self.verbose:
            print(
                f"[{self.label} RECV] {message}"
            )

        return message

    def close(self):

        try:
            self.socket.shutdown(
                socket.SHUT_RDWR
            )
        except OSError:
            pass

        try:
            self.socket.close()
        except OSError:
            pass

    def _receive_exact(self, size: int):

        data = b""

        while len(data) < size:

            chunk = self.socket.recv(
                size - len(data)
            )

            if not chunk:
                return None

            data += chunk

        return data
        return data