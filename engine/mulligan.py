import random


class MulliganManager:
    """
    Handles the London Mulligan procedure.
    """

    STARTING_HAND_SIZE = 7

    def __init__(self, game_state):

        self.game_state = game_state

        self.finished_players = set()

        self.mulligan_count = {}

    # ======================================================
    # Mulligan Setup
    # ======================================================

    def start(self):
        """
        Begin the mulligan process.
        """

        self.finished_players.clear()

        self.mulligan_count.clear()

        for player in self.game_state.players:

            self.mulligan_count[player.player_id] = 0

            self.draw_starting_hand(player)

    # ======================================================
    # Draw Opening Hand
    # ======================================================

    def draw_starting_hand(self, player):

        player.hand.clear()

        for _ in range(self.STARTING_HAND_SIZE):

            card = player.library.draw()

            if card is None:
                break

            player.hand.add(card)

    # ======================================================
    # Keep Current Hand
    # ======================================================

    def keep(self, player):

        if player.player_id in self.finished_players:
            return

        mulligans = self.mulligan_count[player.player_id]

        if mulligans > 0:

            self.bottom_cards(player, mulligans)

        self.finished_players.add(player.player_id)

    # ======================================================
    # Take Mulligan
    # ======================================================

    def mulligan(self, player):

        cards = list(player.hand)

        player.hand.clear()

        for card in cards:

            player.library.add(card)

        player.library.shuffle()

        self.mulligan_count[player.player_id] += 1

        self.draw_starting_hand(player)

    # ======================================================
    # Bottom Cards
    # ======================================================

    def bottom_cards(self, player, amount):
        """
        Put cards from hand on the bottom of the library.

        Currently removes the last cards in hand.
        A client UI can later let the player choose.
        """

        while amount > 0 and len(player.hand) > 0:

            card = player.hand.get_cards().pop()

            player.library.cards.append(card)

            amount -= 1

    # ======================================================
    # Status
    # ======================================================

    def player_finished(self, player):

        return player.player_id in self.finished_players

    def all_players_finished(self):

        return len(self.finished_players) == len(self.game_state.players)

    def reset(self):

        self.finished_players.clear()

        self.mulligan_count.clear()