from network.server import Server
from network.dispatcher import Dispatcher

from protocol.message_types import MessageType

from handlers.lobby_handler import player_ready, mulligan_choice
from handlers.spell_handler import (
    cast_spell,
    play_land,
    activate_ability
)
from handlers.combat_handler import (
    declare_attackers,
    declare_blockers,
    assign_damage_order
)
from handlers.priority_handler import (
    priority_pass,
    stack_push,
    stack_resolve
)
from handlers.game_handler import (
    phase_transition,
    concede,
    game_over
)

from engine.gamestate import GameState


class GameServer:
    """
    Main controller for the MTGNP server.

    Responsibilities:
    - Owns the game state
    - Owns all network connections
    - Receives incoming messages
    - Dispatches messages to handlers
    """

    def __init__(self):

        self.server = Server()
        self.dispatcher = Dispatcher()

        self.connections = []

        self.running = False

        self.game_state = GameState()

        self.register_handlers()

    def register_handlers(self):
        """
        Register all protocol message handlers.
        """

        self.dispatcher.register(
            MessageType.PLAYER_READY.value,
            lambda message: player_ready(self, message)
        )

        self.dispatcher.register(
            MessageType.MULLIGAN_CHOICE.value,
            lambda message: mulligan_choice(self, message)
        )

        self.dispatcher.register(
            MessageType.CAST_SPELL.value,
            lambda message: cast_spell(self, message)
        )

        self.dispatcher.register(
            MessageType.PLAY_LAND.value,
            lambda message: play_land(self, message)
        )

        self.dispatcher.register(
            MessageType.ACTIVATE_ABILITY.value,
            lambda message: activate_ability(self, message)
        )

        self.dispatcher.register(
            MessageType.DECLARE_ATTACKERS.value,
            lambda message: declare_attackers(self, message)
        )

        self.dispatcher.register(
            MessageType.DECLARE_BLOCKERS.value,
            lambda message: declare_blockers(self, message)
        )

        self.dispatcher.register(
            MessageType.ASSIGN_DAMAGE_ORDER.value,
            lambda message: assign_damage_order(self, message)
        )

        self.dispatcher.register(
            MessageType.PRIORITY_PASS.value,
            lambda message: priority_pass(self, message)
        )

        self.dispatcher.register(
            MessageType.STACK_PUSH.value,
            lambda message: stack_push(self, message)
        )

        self.dispatcher.register(
            MessageType.STACK_RESOLVE.value,
            lambda message: stack_resolve(self, message)
        )

        self.dispatcher.register(
            MessageType.PHASE_TRANSITION.value,
            lambda message: phase_transition(self, message)
        )

        self.dispatcher.register(
            MessageType.CONCEDE.value,
            lambda message: concede(self, message)
        )

        self.dispatcher.register(
            MessageType.GAME_OVER.value,
            lambda message: game_over(self, message)
        )

    def start(self):

        print("Starting MTGNP Server...\n")

        self.connections = self.server.start()

        self.running = True

        print("\nGame server ready.")
        print("Waiting for messages...\n")

        self.game_loop()

    def game_loop(self):

        while self.running:

            for connection in self.connections:

                message = connection.receive()

                if message is None:
                    continue

                self.dispatcher.dispatch(message)

    # ==========================================================
    # Utility Methods
    # ==========================================================

    def broadcast(self, message):
        """
        Send a message to every connected player.
        """

        for connection in self.connections:
            connection.send(message)

    # ==========================================================
    # Lobby
    # ==========================================================

    def player_ready(self, message):
        print("PLAYER_READY")
        print(message)

    def mulligan_choice(self, message):
        print("MULLIGAN_CHOICE")
        print(message)

    # ==========================================================
    # Gameplay
    # ==========================================================

    def cast_spell(self, message):
        print("CAST_SPELL")
        print(message)

    def play_land(self, message):
        print("PLAY_LAND")
        print(message)

    def activate_ability(self, message):
        print("ACTIVATE_ABILITY")
        print(message)

    # ==========================================================
    # Combat
    # ==========================================================

    def declare_attackers(self, message):
        print("DECLARE_ATTACKERS")
        print(message)

    def declare_blockers(self, message):
        print("DECLARE_BLOCKERS")
        print(message)

    def assign_damage_order(self, message):
        print("ASSIGN_DAMAGE_ORDER")
        print(message)

    # ==========================================================
    # Priority / Stack
    # ==========================================================

    def priority_pass(self, message):
        print("PRIORITY_PASS")
        print(message)

    def stack_push(self, message):
        print("STACK_PUSH")
        print(message)

    def stack_resolve(self, message):
        print("STACK_RESOLVE")
        print(message)

    # ==========================================================
    # General Game
    # ==========================================================

    def phase_transition(self, message):
        print("PHASE_TRANSITION")
        print(message)

    def concede(self, message):
        print("CONCEDE")
        print(message)

    def game_over(self, message):
        print("GAME_OVER")
        print(message)