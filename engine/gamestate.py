from engine.player import Player


class GameState:
    """
    Stores the current state of a match.
    """

    def __init__(self):

        self.players = []

        self.started = False

        self.current_player = None

        self.current_phase = None

    def add_player(self, player: Player):

        if len(self.players) >= 2:
            raise ValueError("Game already has two players.")

        self.players.append(player)

    def get_player(self, player_id: str):

        for player in self.players:

            if player.player_id == player_id:
                return player

        return None

    def all_players_ready(self):

        if len(self.players) != 2:
            return False

        return all(player.ready for player in self.players)