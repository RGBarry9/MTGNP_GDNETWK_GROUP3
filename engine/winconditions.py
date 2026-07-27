from models.player import Player


class WinConditionManager:
    """
    Determines whether the game has ended.

    This manager does not modify gameplay except for
    ending the game through GameState.
    """

    def __init__(self, game_state):

        self.game_state = game_state

    # ==================================================
    # Main Check
    # ==================================================

    def check(self):
        """
        Check every supported win condition.

        Returns:
            winner (Player) if someone has won,
            None otherwise.
        """

        if self.game_state.game_over:
            return self.game_state.winner

        # ------------------------------------------
        # Check every player
        # ------------------------------------------

        for player in self.game_state.players:

            winner = self._check_player_loss(player)

            if winner is not None:

                self.game_state.end_game(winner)

                return winner

        return None

    # ==================================================
    # Individual Conditions
    # ==================================================

    def _check_player_loss(self, player):
        """
        Returns the winning opponent if the specified
        player has lost.
        """

        # ------------------------------------------
        # Life Total
        # ------------------------------------------

        if player.life <= 0:

            return self.game_state.get_opponent(player)

        # ------------------------------------------
        # Empty Library
        # ------------------------------------------

        if self._lost_by_empty_library(player):

            return self.game_state.get_opponent(player)

        return None

    # ==================================================
    # Library
    # ==================================================

    def _lost_by_empty_library(self, player):
        """
        A player loses if they attempt to draw from an
        empty library.

        Player.draw_card() should set
        player.failed_to_draw = True when this occurs.
        """

        return getattr(player, "failed_to_draw", False)

    # ==================================================
    # Concede
    # ==================================================

    def concede(self, player: Player):
        """
        Handle a player conceding the game.
        """

        winner = self.game_state.get_opponent(player)

        self.game_state.end_game(winner)

        return winner

    # ==================================================
    # Information
    # ==================================================

    def game_over(self):

        return self.game_state.game_over

    def winner(self):

        return self.game_state.winner