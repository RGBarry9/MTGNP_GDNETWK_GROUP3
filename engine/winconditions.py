class WinConditionManager:
    """
    Checks for game-ending conditions.
    """

    def __init__(self, game_state):

        self.game_state = game_state

    def check(self):

        for player in self.game_state.players:

            if player.life <= 0:

                self.game_state.game_over = True

                self.game_state.winner = self._other_player(player)

                return self.game_state.winner

        return None

    def _other_player(self, player):

        for opponent in self.game_state.players:

            if opponent != player:
                return opponent

        return None