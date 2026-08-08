import os
import threading
import time

from config.settings import PING_INTERVAL, PONG_TIMEOUT

from network.client import Client

from protocol.protocol import make_message
from protocol.message_types import MessageType

from client_ui.command_parser import CommandParser, CommandError
from client_ui import renderer


class Terminal:
    """
    Runs the interactive MTGNP terminal client.

    Opens a connection to the server, listens for incoming PDUs on a
    background thread, sends heartbeat PINGs on a second background
    thread, and reads player commands from stdin on the main thread.
    """

    def __init__(self, player_id: str):

        self.player_id = player_id

        self.client = Client()

        self.parser = CommandParser(player_id)

        self.running = False

        # Updated whenever a PONG is received; used by the heartbeat
        # thread to detect an unresponsive server (RFC 0001 SS4.3).
        self.last_pong_at = time.time()

    def start(self):
        """
        Connect to the server and run the client until the player quits.
        """

        renderer.render_banner()
        renderer.render_info(f"Connected as '{self.player_id}'. Type 'help' for commands.")

        self.running = True
        self.last_pong_at = time.time()

        threading.Thread(target=self._listen, daemon=True).start()
        threading.Thread(target=self._heartbeat, daemon=True).start()

        self._input_loop()

    def _listen(self):
        """
        Continuously receive PDUs from the server, update sequence
        tracking, and render them.
        """

        while self.running:

            try:
                message = self.client.connection.receive()
            except OSError:
                break

            if message is None:
                if self.running:
                    renderer.render_info("Disconnected from server.")
                self.running = False
                break

            if message.get("type") == "ERROR" and message.get("code") == "LOBBY_FULL":
                # RFC 0001 SS5.1: the server refuses a 3rd/4th/... client
                # outright. Show why and exit now rather than sitting at
                # the input prompt until PING/PONG eventually times out
                # (a different failure with a different, misleading
                # message) or waiting for the user to press Enter again
                # before the main thread notices self.running changed.
                renderer.render_message(message, self.player_id)
                renderer.render_info("Lobby full - cannot connect. Disconnecting.")
                self.running = False
                try:
                    self.client.connection.close()
                except OSError:
                    pass
                os._exit(0)

            if message.get("type") == "PONG":
                self.last_pong_at = time.time()

            self.parser.tracker.observe(message)

            renderer.render_message(message, self.player_id)

    def _heartbeat(self):
        """
        Send a PING every PING_INTERVAL seconds. If no PONG arrives
        within PONG_TIMEOUT seconds of that PING, treat the server as
        unresponsive and disconnect (RFC 0001 Section 4.3).
        """

        while self.running:

            time.sleep(PING_INTERVAL)

            if not self.running:
                return

            ping_sent_at = time.time()

            try:
                ping = make_message(
                    MessageType.PING,
                    self.parser.tracker.next_ping_seq(),
                    timestamp=int(ping_sent_at * 1000),
                )
                self.client.connection.send(ping)
            except OSError:
                self._fail("Connection lost while sending heartbeat.")
                return

            time.sleep(PONG_TIMEOUT)

            if self.running and self.last_pong_at < ping_sent_at:
                self._fail(f"No PONG received within {PONG_TIMEOUT}s. Disconnecting.")
                return

    def _input_loop(self):
        """
        Read player commands from stdin and send them to the server.
        """

        while self.running:

            try:
                raw_input = input("> ")
            except (EOFError, KeyboardInterrupt):
                raw_input = "quit"

            if not raw_input.strip():
                continue

            command = raw_input.strip().split(" ")[0].lower()

            if command in ("quit", "exit"):
                self._quit()
                break

            if command == "help":
                renderer.render_help()
                continue

            if command == "clear":
                print("\n" * 50)
                continue

            try:
                message = self.parser.parse(raw_input)
            except CommandError as error:
                renderer.render_error(str(error))
                continue

            try:
                self.client.connection.send(message)
            except OSError as error:
                self._fail(f"Failed to send command: {error}")
                break

    def _fail(self, reason: str):
        """
        Report a fatal connection problem and shut the client down.
        """

        renderer.render_error(reason)

        self.running = False

        try:
            self.client.connection.close()
        except OSError:
            pass

    def _quit(self):
        """
        Notify the player, stop background threads, and close the socket.
        """

        renderer.render_info("Disconnecting...")

        self.running = False

        try:
            self.client.connection.close()
        except OSError:
            pass


def main():
    """
    Entry point for running the terminal client directly.
    """

    player_id = input("Enter your player name: ").strip() or "Player"

    terminal = Terminal(player_id)
    terminal.start()


if __name__ == "__main__":
    main()
