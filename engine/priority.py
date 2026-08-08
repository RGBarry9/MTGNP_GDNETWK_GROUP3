# engine/priority.py
from typing import Optional, Literal
from models.player import Player


class PriorityManager:
    """
    Controls priority passing between players.

    Responsibilities:
    - Give priority to a player.
    - Handle players passing priority.
    - Detect consecutive passes.
    - Signal when the stack should resolve.
    - Signal when the game should advance to the next phase.
    """

    def __init__(self, game_state):
        self.game_state = game_state

    # ==================================================
    # Priority Control
    # ==================================================

    def give_priority(self, player: Player) -> None:
        """
        Give priority to a player.
        
        This increments the priority sequence number for stale action checking.
        """
        self.game_state.priority_player = player
        player.receive_priority()
        
        # Increment sequence number for stale action detection
        self.game_state.priority_seq_num += 1

    def current_player(self) -> Optional[Player]:
        """
        Return the player who currently has priority.
        """
        return self.game_state.priority_player

    def has_priority(self, player: Player) -> bool:
        """
        Return True if the specified player currently has priority.
        """
        return self.game_state.priority_player == player

    def get_priority_seq_num(self) -> int:
        """
        Get the current priority sequence number.
        
        Used for stale action detection (STALE_ACTION error).
        """
        return self.game_state.priority_seq_num

    # ==================================================
    # Passing Priority
    # ==================================================

    def pass_priority(self, player: Player) -> Literal["NEXT_PLAYER", "RESOLVE_STACK", "ADVANCE_PHASE"]:
        """
        Handle a player passing priority.

        Returns one of:
            "NEXT_PLAYER" - Other player now has priority
            "RESOLVE_STACK" - Both passed, stack non-empty → resolve
            "ADVANCE_PHASE" - Both passed, stack empty → advance
        """
        if not self.has_priority(player):
            raise RuntimeError(f"Player {player.player_id} does not currently have priority.")

        # Mark player as passed
        player.pass_priority()
        self.game_state.register_priority_pass()

        # Check if everyone has passed
        if not self.game_state.everyone_passed_priority():
            # Give priority to opponent
            opponent = self.game_state.get_opponent(player)
            if opponent:
                self.game_state.priority_player = opponent
                opponent.receive_priority()
                return "NEXT_PLAYER"
            else:
                raise RuntimeError("No opponent found")
        else:
            # Both players have passed
            return self._handle_double_pass()

    # ==================================================
    # Internal Resolution
    # ==================================================

    def _handle_double_pass(self) -> Literal["RESOLVE_STACK", "ADVANCE_PHASE"]:
        """
        Handle two consecutive priority passes.
        """
        # Reset priority tracking
        self.game_state.reset_priority()

        # Check if stack is empty
        if not self.game_state.stack_empty():
            return "RESOLVE_STACK"
        else:
            return "ADVANCE_PHASE"

    # ==================================================
    # Sequence Number Validation
    # ==================================================

    def validate_seq_num(self, seq_num: int) -> bool:
        """
        Validate that a sequence number matches the current priority token.
        
        Returns:
            bool: True if valid, False if stale
        """
        return seq_num == self.game_state.priority_seq_num

    def get_stale_error_message(self, seq_num: int) -> str:
        """
        Get error message for stale action.
        """
        return (f"Priority token mismatch. Expected {self.game_state.priority_seq_num}, "
                f"got {seq_num}")

    # ==================================================
    # Reset
    # ==================================================

    def reset(self) -> None:
        """
        Reset the priority system.
        """
        self.game_state.reset_priority()
        # Don't reset priority_seq_num - it should keep incrementing

    def reset_for_new_game(self) -> None:
        """
        Reset priority system for a new game.
        """
        self.game_state.reset_priority()
        self.game_state.priority_seq_num = 0

    # ==================================================
    # Information
    # ==================================================

    def everyone_passed(self) -> bool:
        """
        Return True if every player has passed priority.
        """
        return self.game_state.everyone_passed_priority()

    def is_priority_window_open(self) -> bool:
        """
        Return True if a priority window is currently open.
        """
        return self.game_state.priority_player is not None

    def __str__(self) -> str:
        """String representation for debugging."""
        priority_holder = self.game_state.priority_player
        holder_name = priority_holder.player_id if priority_holder else "None"
        return f"PriorityManager(holder={holder_name}, seq={self.game_state.priority_seq_num})"