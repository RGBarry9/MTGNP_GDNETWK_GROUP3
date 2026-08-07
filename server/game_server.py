import threading

from network.server import Server
from network.dispatcher import Dispatcher

from protocol.message_types import MessageType

from handlers.lobby_handler import (
    player_ready,
    mulligan_choice
)

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

from config.enums import (
    GameState as GameStateEnum
)

from game.loader import CardLoader

from config.settings import (
    PRIORITY_TIMEOUT_MS
)


class GameServer:

    def __init__(
        self,
        verbose=False
    ):

        self.verbose = verbose

        self.server = Server(
            verbose=verbose
        )

        self.dispatcher = Dispatcher()

        self.connections = []

        self.running = False

        # ======================================================
        # Authoritative Game
        # ======================================================

        self.game = Game()

        self.game_state = (
            self.game.game_state
        )

        # ======================================================
        # Connection mappings
        # ======================================================

        # connection -> player_id
        self.player_connections = {}

        # player_id -> connection
        self.connection_player = {}

        # ======================================================
        # Server sequence number
        # ======================================================

        self._server_seq = 0

        # ======================================================
        # Card database
        # ======================================================

        loader = CardLoader()

        self.card_db = loader.load(
            "game/cards.json"
        )

        self.register_handlers()

    # ==========================================================
    # Handler Registration
    # ==========================================================

    def register_handlers(self):

        handlers = {

            MessageType.PLAYER_READY:
                player_ready,

            MessageType.MULLIGAN_CHOICE:
                mulligan_choice,

            MessageType.CAST_SPELL:
                cast_spell,

            MessageType.PLAY_LAND:
                play_land,

            MessageType.ACTIVATE_ABILITY:
                activate_ability,

            MessageType.DECLARE_ATTACKERS:
                declare_attackers,

            MessageType.DECLARE_BLOCKERS:
                declare_blockers,

            MessageType.ASSIGN_DAMAGE_ORDER:
                assign_damage_order,

            MessageType.PRIORITY_PASS:
                priority_pass,

            MessageType.STACK_PUSH:
                stack_push,

            MessageType.STACK_RESOLVE:
                stack_resolve,

            MessageType.PHASE_TRANSITION:
                phase_transition,

            MessageType.CONCEDE:
                concede,

            MessageType.GAME_OVER:
                game_over
        }

        for message_type, handler in (
            handlers.items()
        ):

            self.dispatcher.register(
                message_type.value,
                lambda message,
                h=handler:
                    h(self, message)
            )

    # ==========================================================
    # Startup
    # ==========================================================

    def start(self):

        print(
            "Starting MTGNP Server...\n"
        )

        self.connections = (
            self.server.start()
        )

        self.running = True

        print(
            "\nGame server ready."
        )

        print(
            "Waiting for messages...\n"
        )

        threads = []

        for connection in self.connections:

            thread = threading.Thread(
                target=self._connection_loop,
                args=(connection,),
                daemon=True
            )

            thread.start()

            threads.append(thread)

        try:

            for thread in threads:
                thread.join()

        except KeyboardInterrupt:

            self.running = False

            self.server.close()

    # ==========================================================
    # Per-connection receive loop
    # ==========================================================

    def _connection_loop(
        self,
        connection
    ):

        while self.running:

            try:

                message = (
                    connection.receive()
                )

            except (
                OSError,
                ValueError,
                ConnectionError
            ) as error:

                print(
                    f"Connection error: {error}"
                )

                self._handle_disconnect(
                    connection
                )

                return

            if message is None:

                self._handle_disconnect(
                    connection
                )

                return

            # Internal information used by
            # _find_connection().
            message[
                "_connection"
            ] = connection

            # Once a connection has been
            # associated with a player,
            # automatically attach player_id
            # to action messages that omit it.
            player_id = (
                self.player_connections.get(
                    connection
                )
            )

            if (
                player_id
                and "player_id" not in message
            ):

                message[
                    "player_id"
                ] = player_id

            # ==================================================
            # PING
            # ==================================================

            if (
                message.get("type")
                == MessageType.PING.value
            ):

                self.send_to_connection(
                    connection,
                    {
                        "type":
                            MessageType.PONG.value,

                        "seq_num":
                            message.get(
                                "seq_num",
                                0
                            ),

                        "timestamp":
                            message.get(
                                "timestamp"
                            )
                    }
                )

                continue

            self.dispatcher.dispatch(
                message
            )

    # ==========================================================
    # Sequence Numbers
    # ==========================================================

    def next_seq(self):

        self._server_seq += 1

        return self._server_seq

    # ==========================================================
    # Connection Lookup
    # ==========================================================

    def _find_connection(
        self,
        message
    ):

        connection = message.get(
            "_connection"
        )

        if connection is not None:
            return connection

        player_id = message.get(
            "player_id"
        )

        if player_id:

            return (
                self.connection_player.get(
                    player_id
                )
            )

        return None

    # ==========================================================
    # Send
    # ==========================================================

    def send_to_connection(
        self,
        connection,
        message
    ):

        if connection is None:
            return

        outgoing = dict(message)

        outgoing.pop(
            "_connection",
            None
        )

        if "seq_num" not in outgoing:

            outgoing[
                "seq_num"
            ] = self.next_seq()

        connection.send(
            outgoing
        )

    # ==========================================================
    # Error PDU
    # ==========================================================

    def send_error(
        self,
        connection,
        code,
        message,
        rejected_action=None
    ):

        if connection is None:
            return

        error = {

            "type":
                MessageType.ERROR.value,

            "seq_num":
                self.next_seq(),

            "code":
                code,

            "message":
                message
        }

        if rejected_action:

            rejected = dict(
                rejected_action
            )

            rejected.pop(
                "_connection",
                None
            )

            error[
                "rejected_action"
            ] = rejected

        self.send_to_connection(
            connection,
            error
        )

    # ==========================================================
    # Broadcast
    # ==========================================================

    def broadcast(
        self,
        message
    ):

        outgoing = dict(
            message
        )

        outgoing.pop(
            "_connection",
            None
        )

        if "seq_num" not in outgoing:

            outgoing[
                "seq_num"
            ] = self.next_seq()

        for connection in list(
            self.connections
        ):

            try:

                connection.send(
                    outgoing
                )

            except OSError:

                self._handle_disconnect(
                    connection
                )

    # ==========================================================
    # Lobby
    # ==========================================================

    def _broadcast_lobby_status(
        self
    ):

        waiting_for = []

        if len(
            self.connection_player
        ) < 2:

            waiting_for = [
                "second_player"
            ]

        self.broadcast({

            "type":
                MessageType
                .GAME_STATE_UPDATE
                .value,

            "state": {

                "phase":
                    "LOBBY",

                "players_ready":
                    len(
                        self.connection_player
                    ),

                "waiting_for":
                    waiting_for
            }
        })

    # ==========================================================
    # Personalized State
    # ==========================================================

    def _broadcast_personalized_state(
        self
    ):

        for (
            player_id,
            connection
        ) in list(
            self.connection_player.items()
        ):

            state = (
                self.game
                .get_personalized_state(
                    player_id
                )
            )

            if (
                self.game_state.game_state
                == GameStateEnum.MULLIGAN
            ):

                state[
                    "phase"
                ] = "MULLIGAN"

            self.send_to_connection(
                connection,
                {
                    "type":
                        MessageType
                        .GAME_STATE_UPDATE
                        .value,

                    "state":
                        state
                }
            )

    # ==========================================================
    # GAME_SETUP
    # ==========================================================

    def _start_game(self):

        if (
            len(
                self.game.get_players()
            ) != 2
        ):

            return

        if not (
            self.game.players_ready()
        ):

            return

        print(
            "\nStarting GAME_SETUP..."
        )

        # ======================================================
        # Copy deck into library
        # ======================================================

        for player in (
            self.game.get_players()
        ):

            player.library.clear()

            for card in (
                player.deck.cards
            ):

                clone = card.clone()

                clone.owner = (
                    player.player_id
                )

                clone.controller = (
                    player.player_id
                )

                player.library.add(
                    clone
                )

            player.library.shuffle()

            player.life = 20

        # Game.start_game():
        # - initializes state
        # - randomly chooses first player
        # - draws opening hands
        # - starts mulligan manager

        self.game.start_game()

        self.game_state.set_game_state(
            GameStateEnum.MULLIGAN
        )

        self._broadcast_personalized_state()

    # ==========================================================
    # First Turn
    # ==========================================================

    def _start_first_turn(self):

        if not (
            self.game
            .mulligan_manager
            .all_players_finished()
        ):

            return

        self.game_state.set_game_state(
            GameStateEnum.IN_GAME
        )

        self.game.start_turn()

        self._broadcast_phase_transition()

        self._give_priority()

        self._broadcast_personalized_state()

    # ==========================================================
    # Phase
    # ==========================================================

    def _phase_has_priority(self):

        return (
            self.game
            .turn_manager
            .has_priority_window()
        )

    def _broadcast_phase_transition(
        self,
        from_phase=None
    ):

        phase = (
            self.game_state.current_phase
        )

        if hasattr(
            phase,
            "value"
        ):

            to_phase = phase.value

        else:

            to_phase = str(
                phase
            )

        if hasattr(
            from_phase,
            "value"
        ):

            from_value = (
                from_phase.value
            )

        else:

            from_value = from_phase

        self.broadcast({

            "type":
                MessageType
                .PHASE_TRANSITION
                .value,

            "from_phase":
                from_value,

            "to_phase":
                to_phase,

            "active_player":
                (
                    self.game_state
                    .active_player
                    .player_id
                    if self.game_state.active_player
                    else None
                ),

            "turn":
                self.game_state.turn_number
        })

    # ==========================================================
    # Priority
    # ==========================================================

    def _give_priority(self):

        player = (
            self.game_state.active_player
        )

        if player is None:
            return

        self.game.give_priority(
            player
        )

        connection = (
            self.connection_player.get(
                player.player_id
            )
        )

        if connection is None:
            return

        # The priority token MUST be the seq_num
        # echoed by the client in its next
        # priority-bearing action.
        priority_token = (
            self.game_state.priority_seq_num
        )

        self.send_to_connection(

            connection,

            {
                "type":
                    MessageType
                    .PRIORITY_GRANT
                    .value,

                "player_id":
                    player.player_id,

                "time_limit_ms":
                    PRIORITY_TIMEOUT_MS,

                "seq_num":
                    priority_token
            }
        )

    # ==========================================================
    # GAME OVER
    # ==========================================================

    def _end_game(
        self,
        loser_id,
        reason
    ):

        loser = (
            self.game.get_player(
                loser_id
            )
        )

        if loser is None:
            return

        winner = (
            self.game_state
            .get_opponent(
                loser
            )
        )

        winner_id = (
            winner.player_id
            if winner
            else None
        )

        self.broadcast({

            "type":
                MessageType
                .GAME_OVER
                .value,

            "winner_id":
                winner_id,

            "loser_id":
                loser_id,

            "reason":
                reason
        })

        self.game_state.game_over = True

        self.game_state.started = False

        self.game_state.set_game_state(
            GameStateEnum.GAME_OVER
        )

    # ==========================================================
    # Disconnect
    # ==========================================================

    def _handle_disconnect(
        self,
        connection
    ):

        player_id = (
            self.player_connections.pop(
                connection,
                None
            )
        )

        if player_id:

            self.connection_player.pop(
                player_id,
                None
            )

            if (
                self.game_state.game_state
                == GameStateEnum.IN_GAME
            ):

                self._end_game(
                    player_id,
                    "DISCONNECT"
                )

        try:

            self.connections.remove(
                connection
            )

        except ValueError:

            pass

    # ==========================================================
    # Compatibility methods
    # ==========================================================

    def player_ready(self, message):
        player_ready(self, message)

    def mulligan_choice(self, message):
        mulligan_choice(self, message)

    def cast_spell(self, message):
        cast_spell(self, message)

    def play_land(self, message):
        play_land(self, message)

    def activate_ability(self, message):
        activate_ability(self, message)

    def declare_attackers(self, message):
        declare_attackers(self, message)

    def declare_blockers(self, message):
        declare_blockers(self, message)

    def assign_damage_order(self, message):
        assign_damage_order(self, message)

    def priority_pass(self, message):
        priority_pass(self, message)

    def stack_push(self, message):
        stack_push(self, message)

    def stack_resolve(self, message):
        stack_resolve(self, message)

    def phase_transition(self, message):
        phase_transition(self, message)

    def concede(self, message):
        concede(self, message)

    def game_over(self, message):
        game_over(self, message)