from network.server import Server
from protocol.message_types import MessageType


def main():

    server = Server()

    connections = server.start()

    print("\nBoth players connected.\n")

    for i, connection in enumerate(connections):

        message = connection.receive()

        print(f"Player {i+1} sent:")

        print(message)


if __name__ == "__main__":
    main()