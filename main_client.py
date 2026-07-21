from network.client import Client

from protocol.protocol import make_message
from protocol.message_types import MessageType


def main():

    client = Client()

    packet = make_message(
        MessageType.PLAYER_READY,
        seq_num=1,
        player_id="Player",
        deck_list=[]
    )

    client.connection.send(packet)

    print("PLAYER_READY sent.")

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()