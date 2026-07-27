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

    def give_priority(self, player):
        """
        Give priority to a player.
        """

        self.game_state.priority_player = player
        player.receive_priority()

    def current_player(self):
        """
        Return the player who currently has priority.
        """

        return self.game_state.priority_player

    def has_priority(self, player):
        """
        Return True if the specified player currently has priority.
        """

        return self.game_state.priority_player == player

    # ==================================================
    # Passing Priority
    # ==================================================

    def pass_priority(self, player):
        """
        Handle a player passing priority.

        Returns one of:

            "NEXT_PLAYER"
            "RESOLVE_STACK"
            "ADVANCE_PHASE"
        """

        if not self.has_priority(player):
            raise RuntimeError("Player does not currently have priority.")

        player.pass_priority()
        self.game_state.register_priority_pass()

        opponent = self.game_state.get_opponent(player)

        # First pass
        if not self.game_state.everyone_passed_priority():

            self.game_state.priority_player = opponent
            opponent.receive_priority()

            return "NEXT_PLAYER"

        # Both players have passed
        return self._handle_double_pass()

    # ==================================================
    # Internal Resolution
    # ==================================================

    def _handle_double_pass(self):
        """
        Handle two consecutive priority passes.
        """

        self.game_state.reset_priority()

        if not self.game_state.stack_empty():
            return "RESOLVE_STACK"

        return "ADVANCE_PHASE"

    # ==================================================
    # Reset
    # ==================================================

    def reset(self):
        """
        Reset the priority system.
        """

        self.game_state.reset_priority()

    # ==================================================
    # Information
    # ==================================================

    def everyone_passed(self):
        """
        Return True if every player has passed priority.
        """

        return self.game_state.everyone_passed_priority()