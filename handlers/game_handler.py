"""
General game message handlers.
"""


def phase_transition(game_server, message):
    """
    Handle PHASE_TRANSITION.
    """
    game_server.phase_transition(message)


def concede(game_server, message):
    """
    Handle CONCEDE.
    """
    game_server.concede(message)


def game_over(game_server, message):
    """
    Handle GAME_OVER.
    """
    game_server.game_over(message)