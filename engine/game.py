from engine.gamestate import GameState
from engine.turn import TurnManager
from engine.priority import PriorityManager
from engine.stack import StackManager
from engine.combat import CombatManager
from engine.mulligan import MulliganManager
from engine.winconditions import WinConditionManager
from effects.effect_manager import EffectManager


class Game:
    """
    Main game controller.

    Coordinates all engine subsystems and provides the primary API
    used by the GameServer.
    """

    def __init__(self):

        self.game_state = GameState()

        self.turn_manager = TurnManager(self.game_state)

        self.priority_manager = PriorityManager(self.game_state)

        self.stack_manager = StackManager(self.game_state)

        self.combat_manager = CombatManager(self.game_state)

        self.mulligan_manager = MulliganManager(self.game_state)

        self.effect_manager = EffectManager(self.game_state)

        self.win_manager = WinConditionManager(self.game_state)

    # ==========================================================
    # Player Management
    # ==========================================================

    def add_player(self, player):
        """
        Add a player to the game.
        """

        return self.game_state.add_player(player)

    def remove_player(self, player):
        """
        Remove a player from the game.
        """

        return self.game_state.remove_player(player)

    def get_player(self, player_id):
        """
        Return the player with the given player ID.
        """

        return self.game_state.get_player(player_id)

    def players_ready(self):
        """
        Return True when all players are ready.
        """

        return self.game_state.all_players_ready()

    # ==========================================================
    # Game Lifecycle
    # ==========================================================

    def start_game(self):
        """
        Start a new game.
        """

        if not self.players_ready():
            raise RuntimeError(
                "Cannot start the game until all players are ready."
            )

        self.game_state.start_game()

        print("Game started.")

        self.mulligan_manager.start()

    def end_game(self, winner):
        """
        End the current game.
        """

        self.game_state.end_game(winner)

        print(f"Winner: {winner.player_id}")

    # ==========================================================
    # Turn Management
    # ==========================================================

    def start_turn(self):
        """
        Begin the active player's turn.
        """

        self.turn_manager.start_turn()

    def end_turn(self):
        """
        End the active player's turn.
        """

        self.turn_manager.end_turn()

    # ==========================================================
    # Priority
    # ==========================================================

    def give_priority(self, player):
        """
        Give priority to a player.
        """

        self.priority_manager.give_priority(player)

    def pass_priority(self, player):
        """
        Player passes priority.
        """

        self.priority_manager.pass_priority(player)

    # ==========================================================
    # Stack
    # ==========================================================

    def cast_spell(self, stack_item):
        """
        Place a spell or ability onto the stack.
        """

        self.stack_manager.push(stack_item)

    def resolve_stack(self):
        """
        Resolve the top object on the stack.
        """

        self.stack_manager.resolve()

    # ==========================================================
    # Combat
    # ==========================================================

    def declare_attackers(self, attackers):
        """
        Declare attackers.
        """

        self.combat_manager.declare_attackers(attackers)

    def declare_blockers(self, blockers):
        """
        Declare blockers.
        """

        self.combat_manager.declare_blockers(blockers)

    def resolve_combat(self):
        """
        Resolve combat damage.
        """

        self.combat_manager.resolve_combat()

    # ==========================================================
    # Win Conditions
    # ==========================================================

    def check_win_conditions(self):
        """
        Check whether the game has ended.
        """

        winner = self.win_manager.check()

        if winner is not None:
            self.end_game(winner)

        return winner