import json

from config.settings import ENCODING



#Converts Python dictionary to bytes.
def encode(message: dict) -> bytes:
    return json.dumps(message).encode(ENCODING)


#Convert bytes into Python dictionary.
def decode(data: bytes) -> dict:
    return json.loads(data.decode(ENCODING))