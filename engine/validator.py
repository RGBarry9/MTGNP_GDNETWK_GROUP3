class Validator:
    """
    Performs game rule validation.

    This class should only validate actions.
    It must not modify the game state.
    """

    def __init__(self, game_state):

        self.game_state = game_state

    def can_cast_spell(self, player, card):

        return True

    def can_play_land(self, player):

        return True

    def can_attack(self, player, creature):

        return True

    def can_block(self, player, creature):

        return True

    def valid_target(self, target):

        return target is not None