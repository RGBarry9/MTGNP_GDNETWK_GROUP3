from protocol.serializer import encode, decode


HEADER_SIZE = 4


#Creates a length-prefixed packet
def create_packet(message: dict) -> bytes:
    payload = encode(message)

    length = len(payload).to_bytes(
        HEADER_SIZE,
        byteorder="big"
    )

    return length + payload

#Extracts JSON payload from packet
def unpack_packet(packet: bytes) -> dict:
    payload = packet[HEADER_SIZE:]

    return decode(payload)