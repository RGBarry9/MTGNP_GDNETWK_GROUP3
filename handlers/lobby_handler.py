"""
Lobby message handlers.
"""


def player_ready(game_server, message):
    """
    Handle PLAYER_READY.
    """
    game_server.player_ready(message)


def mulligan_choice(game_server, message):
    """
    Handle MULLIGAN_CHOICE.
    """
    game_server.mulligan_choice(message)