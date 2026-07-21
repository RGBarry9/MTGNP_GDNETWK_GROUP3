from network.server import Server
from network.dispatcher import Dispatcher

from protocol.message_types import MessageType

from engine.gamestate import GameState
from engine.player import Player


class GameServer:
    """
    Main controller of the MTGNP game server.
    """

    def __init__(self):

        self.server = Server()
        self.dispatcher = Dispatcher()

        self.connections = []

        self.running = False

        self.game_state = GameState()

        # Register message handlers
        self.dispatcher.register(
            MessageType.PLAYER_READY.value,
            self.on_player_ready
        )

    def start(self):

        print("Starting MTGNP Server...\n")

        self.connections = self.server.start()

        self.running = True

        print("\nGame server ready.")
        print("Waiting for player messages...\n")

        self.game_loop()

    def game_loop(self):

        while self.running:

            for connection in self.connections:

                message = connection.receive()

                if message is None:
                    continue

                self.dispatcher.dispatch(message)

    def on_player_ready(self, message):
        """
        Handles PLAYER_READY messages.
        """

        player = Player(
            player_id=message["player_id"],
            ready=True
        )

        self.game_state.add_player(player)

        print(f"{player.player_id} is ready.")
        print(f"Players Ready: {len(self.game_state.players)}/2")

        if self.game_state.all_players_ready():

            self.game_state.started = True

            print("\n===================================")
            print("Both players are ready!")
            print("The game can now begin.")
            print("===================================\n")