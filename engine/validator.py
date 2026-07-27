from models.card import Card
from models.player import Player


class GameValidator:
    """
    Validates player actions according to the game rules.

    This class only determines whether an action is legal.
    It never modifies the game state.
    """

    def __init__(self, game_state):
        self.game_state = game_state

    # ==========================================================
    # General
    # ==========================================================

    def game_started(self):
        return self.game_state.started

    def game_not_over(self):
        return not self.game_state.game_over

    def player_exists(self, player: Player):
        return player in self.game_state.players

    # ==========================================================
    # Turn Validation
    # ==========================================================

    def is_active_player(self, player: Player):
        return self.game_state.active_player == player

    def has_priority(self, player: Player):
        return self.game_state.priority_player == player

    # ==========================================================
    # Spell Casting
    # ==========================================================

    def can_cast_spell(self, player: Player, card: Card):
        """
        Returns (bool, reason)
        """

        if not self.game_started():
            return False, "Game has not started."

        if not self.game_not_over():
            return False, "Game is already over."

        if not self.player_exists(player):
            return False, "Player is not in this game."

        if not self.has_priority(player):
            return False, "Player does not have priority."

        if card not in player.hand:
            return False, "Card is not in player's hand."

        return True, ""

    # ==========================================================
    # Land Plays
    # ==========================================================

    def can_play_land(self, player: Player, card: Card):

        legal, reason = self.can_cast_spell(player, card)

        if not legal:
            return False, reason

        if not card.is_land():
            return False, "Card is not a land."

        if player.land_plays_remaining <= 0:
            return False, "Player has already played a land this turn."

        return True, ""

    # ==========================================================
    # Target Validation
    # ==========================================================

    def valid_player_target(self, player_id):

        return self.game_state.get_player(player_id) is not None

    def valid_creature_target(self, creature_id):

        for player in self.game_state.players:

            for creature in player.battlefield:

                creature_ref = getattr(creature, "id", None)

                if creature_ref == creature_id:
                    return True

        return False

    # ==========================================================
    # Combat
    # ==========================================================

    def can_attack(self, player: Player, creature: Card):

        if self.game_state.current_phase != "COMBAT":
            return False, "Not combat phase."

        if creature not in player.battlefield:
            return False, "Creature is not on battlefield."

        if not creature.is_creature():
            return False, "Only creatures can attack."

        if creature.is_tapped():
            return False, "Tapped creatures cannot attack."

        return True, ""

    def can_block(self, player: Player, blocker: Card, attacker: Card):

        if self.game_state.current_phase != "COMBAT":
            return False, "Not combat phase."

        if blocker not in player.battlefield:
            return False, "Blocker is not on battlefield."

        if attacker is None:
            return False, "Invalid attacker."

        if blocker.is_tapped():
            return False, "Tapped creatures cannot block."

        if not blocker.is_creature():
            return False, "Only creatures can block."

        return True, ""

    # ==========================================================
    # Stack
    # ==========================================================

    def stack_not_empty(self):

        return not self.game_state.stack_empty()

    # ==========================================================
    # Miscellaneous
    # ==========================================================

    def valid_card(self, card):

        return isinstance(card, Card)

    def valid_player(self, player):

        return isinstance(player, Player)