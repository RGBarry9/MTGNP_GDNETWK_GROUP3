"""
Spell-related message handlers.
"""


def cast_spell(game_server, message):
    """
    Handle CAST_SPELL.
    """
    game_server.cast_spell(message)


def play_land(game_server, message):
    """
    Handle PLAY_LAND.
    """
    game_server.play_land(message)


def activate_ability(game_server, message):
    """
    Handle ACTIVATE_ABILITY.
    """
    game_server.activate_ability(message)