import argparse

from client_ui.terminal import Terminal


def main():

    parser = argparse.ArgumentParser(
        description="MTGNP Player Client"
    )

    parser.add_argument(
        "--player",
        default=None,
        help="Player ID/name"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose PDU logging"
    )

    args = parser.parse_args()

    if args.player:
        player_id = args.player
    else:
        player_id = input(
            "Enter your player name: "
        ).strip()

    if not player_id:
        player_id = "Player"

    terminal = Terminal(
        player_id,
        verbose=args.verbose
    )

    terminal.start()


if __name__ == "__main__":
    main()