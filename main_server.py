import argparse

from server.game_server import GameServer


def main():
    parser = argparse.ArgumentParser(
        description="MTGNP Server"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose PDU logging"
    )

    args = parser.parse_args()

    server = GameServer(
        verbose=args.verbose
    )

    server.start()


if __name__ == "__main__":
    main()