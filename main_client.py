from client_ui.terminal import Terminal


def main():
    """
    Entry point for running an MTGNP client.

    Connects to the server and starts the interactive terminal UI
    (send/receive loop + heartbeat), which is the real client
    implementation in client_ui/terminal.py.
    """

    player_id = input("Enter your player name: ").strip() or "Player"

    terminal = Terminal(player_id)
    terminal.start()


if __name__ == "__main__":
    main()
