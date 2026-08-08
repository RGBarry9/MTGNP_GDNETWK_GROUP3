import json
import os
import threading

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

from engine.game import Game
from engine.validator import GameValidator

from config.settings import CARD_DATABASE, PRIORITY_TIMEOUT_MS


class GameServer:
    """
    Main controller for the MTGNP server.

    Responsibilities:
    - Owns the game engine (Game) and its GameState
    - Owns all network connections and the player <-> connection mapping
    - Receives incoming messages (one reader thread per connection)
    - Dispatches messages to handlers, one at a time, under a lock
    - Provides the broadcast/send/priority/phase helpers the handlers
      in handlers/*.py rely on
    """

    def __init__(self):

        self.server = Server()
        self.dispatcher = Dispatcher()

        self.connections = []

        self.running = False

        # ------------------------------------------------------------
        # Game engine
        # ------------------------------------------------------------
        self.game = Game()
        # Handlers reach the engine's GameState through either
        # game_server.game.game_state or the game_server.game_state
        # alias directly - both point at the same object.
        self.game_state = self.game.game_state
        self.validator = GameValidator(self.game_state)

        # card_id -> raw card dict, as loaded from game/cards.json.
        # Handlers build Card objects out of these dicts directly.
        self.card_db = self._load_card_db()

        # ------------------------------------------------------------
        # Connection <-> player bookkeeping
        # ------------------------------------------------------------
        self.player_connections = {}   # Connection -> player_id
        self.connection_player = {}    # player_id -> Connection

        # Monotonically increasing counter used for server-issued
        # seq_num values (PRIORITY_GRANT, GAME_STATE_UPDATE, stack item
        # ids, etc.) per RFC 0001 SS5.4 / SS8.5.
        self._seq_counter = 0

        # All game-state mutation happens while holding this lock, so
        # the two connection-reader threads can never race on it even
        # though each is blocked independently on its own socket.
        self._lock = threading.RLock()
        # Set for the duration of dispatch() so handlers that only
        # receive the raw message dict (e.g. PLAYER_READY, before a
        # player_id is registered) can still find the sending socket.
        self.current_connection = None

        self.register_handlers()

    # ==========================================================
    # Setup
    # ==========================================================

    def _load_card_db(self):
        """Load game/cards.json into a {card_id: raw_dict} map."""
        path = CARD_DATABASE
        if not os.path.isabs(path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(project_root, path)

        with open(path, "r", encoding="utf-8") as f:
            cards = json.load(f)

        return {card["card_id"]: card for card in cards}

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

        self.dispatcher.register(
            MessageType.PING.value,
            lambda message: self._handle_ping(message)
        )

    # ==========================================================
    # Networking
    # ==========================================================

    def start(self):

        print("Starting MTGNP Server...\n")

        self.connections = self.server.start()

        self.running = True

        print("\nGame server ready.")
        print("Waiting for messages...\n")

        self.game_loop()

    def game_loop(self):
        """
        Run one reader thread per connection so that both players can
        send PDUs independently (a blocking recv() on Player 1's socket
        no longer starves Player 2). Each received message is then
        dispatched under self._lock so game-state mutation stays
        single-threaded and race-free.
        """

        threads = []

        for connection in self.connections:
            t = threading.Thread(
                target=self._connection_loop,
                args=(connection,),
                daemon=True
            )
            t.start()
            threads.append(t)

        for t in threads:
            t.join()

    def _connection_loop(self, connection):
        while self.running:

            try:
                message = connection.receive()
            except OSError:
                break

            if message is None:
                print("A player disconnected.")
                break

            with self._lock:
                self.current_connection = connection

                # Most client PDUs (MULLIGAN_CHOICE, PRIORITY_PASS,
                # CAST_SPELL, DECLARE_ATTACKERS, ...) do not carry a
                # player_id in their RFC 0001 schema - the server is
                # meant to know who sent them from the TCP connection
                # itself. The handlers in handlers/*.py all read
                # message["player_id"] though, so stamp it in here
                # from the connection <-> player_id mapping rather
                # than trusting a client-supplied value.
                if not message.get("player_id"):
                    known_id = self.player_connections.get(connection)
                    if known_id:
                        message["player_id"] = known_id

                try:
                    self.dispatcher.dispatch(message)
                except Exception as exc:
                    print(f"Error handling '{message.get('type')}': {exc}")
                finally:
                    self.current_connection = None

    def _handle_ping(self, message):
        pong = {
            "type": "PONG",
            "seq_num": message.get("seq_num"),
            "timestamp": message.get("timestamp"),
        }
        self.send_to_connection(self.current_connection, pong)

    # ==========================================================
    # Utility Methods used by handlers/*.py
    # ==========================================================

    def broadcast(self, message):
        """Send a message to every connected player."""
        for connection in self.connections:
            connection.send(message)

    def send_to_connection(self, connection, message):
        """Send a message to a single connection."""
        if connection is None:
            return
        connection.send(message)

    def send_error(self, connection, code, message_text, rejected_action=None):
        """Send an ERROR PDU to a single connection (RFC 0001 Section 11)."""
        if connection is None:
            print(f"[warn] Tried to send ERROR '{code}' but had no connection: {message_text}")
            return

        error_msg = {
            "type": "ERROR",
            "seq_num": self.next_seq(),
            "code": code,
            "message": message_text,
        }
        if rejected_action is not None:
            error_msg["rejected_action"] = rejected_action

        connection.send(error_msg)

    def next_seq(self):
        """Server-side monotonically increasing sequence counter."""
        self._seq_counter += 1
        return self._seq_counter

    def _find_connection(self, message):
        """
        Return the connection the message currently being dispatched
        arrived on. Valid only while dispatch() is running (see
        _connection_loop), which covers every place handlers call this.
        """
        return self.current_connection

    # ==========================================================
    # Game-flow helpers used by handlers/*.py
    # ==========================================================

    def _start_game(self):
        """
        Called once both players have sent a valid PLAYER_READY.
        Shuffles each player's deck into their library, starts the
        Game (which also kicks off the mulligan phase and draws
        opening hands), then broadcasts state.
        """
        for player in self.game.get_players():
            player.library = player.deck.to_library()

        self.game.start_game()
        self._broadcast_personalized_state()

    def _start_first_turn(self):
        """
        Called once both players have finished mulligan. Begins turn 1
        (Untap + Upkeep happen automatically inside TurnManager) and
        opens the first priority window.
        """
        self.game.start_turn()
        self._broadcast_phase_transition()

        if self._phase_has_priority():
            self._give_priority()

    def _phase_has_priority(self):
        return self.game.turn_manager.has_priority_window()

    def _give_priority(self, player=None):
        """
        Grant priority and broadcast PRIORITY_GRANT.

        Defaults to the active player (used when opening a fresh
        priority window at the start of a step/phase, or after a stack
        item resolves - RFC 0001 Section 8.1 rule 1). Callers pass an
        explicit player when priority is instead moving to whichever
        player doesn't currently hold it (e.g. after a single
        PRIORITY_PASS - see handlers/priority_handler.py).
        """
        if player is None:
            player = self.game_state.active_player
        if player is None:
            return

        self.game.give_priority(player)

        grant_msg = {
            "type": "PRIORITY_GRANT",
            "player_id": player.player_id,
            "seq_num": self.game_state.priority_seq_num,
            "time_limit_ms": PRIORITY_TIMEOUT_MS,
        }
        connection = self.connection_player.get(player.player_id)
        self.send_to_connection(connection, grant_msg)

    def _broadcast_phase_transition(self, from_phase=None):
        to_phase = self.game_state.current_phase
        msg = {
            "type": "PHASE_TRANSITION",
            "seq_num": self.next_seq(),
            "from_phase": getattr(from_phase, "value", from_phase),
            "to_phase": getattr(to_phase, "value", to_phase),
            "active_player": (
                self.game_state.active_player.player_id
                if self.game_state.active_player else None
            ),
            "turn": self.game_state.turn_number,
        }
        self.broadcast(msg)

    def _broadcast_personalized_state(self):
        for player in self.game.get_players():
            state = self.game.get_personalized_state(player.player_id)
            msg = {
                "type": "GAME_STATE_UPDATE",
                "seq_num": self.next_seq(),
                "state": state,
            }
            connection = self.connection_player.get(player.player_id)
            self.send_to_connection(connection, msg)

    def _end_game(self, loser_id, reason):
        loser = self.game.get_player(loser_id)
        winner = self.game_state.get_opponent(loser) if loser else None

        msg = {
            "type": "GAME_OVER",
            "seq_num": self.next_seq(),
            "winner_id": winner.player_id if winner else None,
            "loser_id": loser_id,
            "reason": reason,
        }
        self.broadcast(msg)

        # RFC 0001 SS6.6: return to LOBBY, keep the TCP connections open
        # so both players can send a fresh PLAYER_READY.
        self.game.reset_game()
        self.player_connections.clear()
        self.connection_player.clear()
