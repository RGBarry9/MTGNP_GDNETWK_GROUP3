import socket

from protocol.framing import create_packet, HEADER_SIZE


class Connection:

    def __init__(self, sock: socket.socket):
        self.socket = sock


    # Send one MTGNP message
    def send(self, message: dict):
        packet = create_packet(message)
        self.socket.sendall(packet)


    #Receive one MTGNP message
    def receive(self):
        header = self._receive_exact(HEADER_SIZE)

        if not header:
            return None

        length = int.from_bytes(header, "big")

        payload = self._receive_exact(length)

        if payload is None:
            return None

        from protocol.serializer import decode

        return decode(payload)



    def close(self):
        self.socket.close()


    def _receive_exact(self, size: int):

        data = b''

        while len(data) < size:

            chunk = self.socket.recv(size - len(data))

            if not chunk:
                return None

            data += chunk

        return data