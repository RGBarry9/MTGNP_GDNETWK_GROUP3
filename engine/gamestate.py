from models.player import Player
from models.stack_item import StackItem


class GameState:
    """
    Stores the complete state of a single MTGNP game.

    This class owns all mutable game data but does not implement
    game rules. Rule enforcement belongs to the engine managers.
    """

    def __init__(self):

        # ==================================================
        # Players
        # ==================================================

        self.players: list[Player] = []

        self.max_players = 2

        # ==================================================
        # Match Status
        # ==================================================

        self.started = False

        self.game_over = False

        self.winner = None

        # ==================================================
        # Turn Information
        # ==================================================

        self.turn_number = 1

        self.active_player = None

        self.current_phase = "LOBBY"

        # ==================================================
        # Priority
        # ==================================================

        self.priority_player = None

        self.priority_passes = 0

        # ==================================================
        # Stack
        # ==================================================

        self.stack: list[StackItem] = []

        # ==================================================
        # Combat
        # ==================================================

        self.attackers = []

        self.blockers = {}

        self.damage_assignments = []

    # ==========================================================
    # Player Management
    # ==========================================================

    def add_player(self, player: Player) -> bool:
        """
        Add a player to the game.

        Returns True if successful.
        """

        if len(self.players) >= self.max_players:
            return False

        if player in self.players:
            return False

        self.players.append(player)

        if self.active_player is None:
            self.active_player = player

        return True

    def remove_player(self, player: Player) -> bool:
        """
        Remove a player from the game.
        """

        if player not in self.players:
            return False

        self.players.remove(player)

        if self.active_player == player:
            self.active_player = None

        return True

    def get_player(self, player_id):
        """
        Return the player with the given ID.
        """

        for player in self.players:

            if player.player_id == player_id:
                return player

        return None

    def get_opponent(self, player: Player):
        """
        Return the opponent of the specified player.
        """

        for opponent in self.players:

            if opponent != player:
                return opponent

        return None

    def player_count(self):
        """
        Return the number of players currently in the game.
        """

        return len(self.players)

    # ==========================================================
    # Ready State
    # ==========================================================

    def all_players_ready(self):
        """
        Return True when every player is ready.
        """

        if len(self.players) != self.max_players:
            return False

        return all(player.ready for player in self.players)

    # ==========================================================
    # Turn State
    # ==========================================================

    def next_turn(self):
        """
        Advance to the next turn.
        """

        self.turn_number += 1

    def set_active_player(self, player):
        """
        Set the active player.
        """

        self.active_player = player

    def set_phase(self, phase):
        """
        Set the current phase.
        """

        self.current_phase = phase

    # ==========================================================
    # Priority
    # ==========================================================

    def reset_priority(self):
        """
        Reset priority for a new priority cycle.
        """

        self.priority_passes = 0

        self.priority_player = None

        for player in self.players:
            player.receive_priority()

    def register_priority_pass(self):
        """
        Record a player passing priority.
        """

        self.priority_passes += 1

    def everyone_passed_priority(self):
        """
        Return True if every player has passed priority.
        """

        return self.priority_passes >= len(self.players)

    # ==========================================================
    # Stack
    # ==========================================================

    def push_stack(self, stack_item: StackItem):
        """
        Push an object onto the stack.
        """

        self.stack.append(stack_item)

    def pop_stack(self):
        """
        Pop the top object from the stack.
        """

        if not self.stack:
            return None

        return self.stack.pop()

    def peek_stack(self):
        """
        Return the top object on the stack.
        """

        if not self.stack:
            return None

        return self.stack[-1]

    def clear_stack(self):
        """
        Remove all objects from the stack.
        """

        self.stack.clear()

    def stack_empty(self):
        """
        Return True if the stack is empty.
        """

        return len(self.stack) == 0

    # ==========================================================
    # Combat
    # ==========================================================

    def clear_combat(self):
        """
        Clear all combat assignments.
        """

        self.attackers.clear()

        self.blockers.clear()

        self.damage_assignments.clear()

    # ==========================================================
    # Game Status
    # ==========================================================

    def start_game(self):
        """
        Start the game.
        """

        self.started = True

        self.game_over = False

    def end_game(self, winner: Player):
        """
        End the game and record the winner.
        """

        self.game_over = True

        self.winner = winner