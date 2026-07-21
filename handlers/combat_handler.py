"""
Combat message handlers.
"""


def declare_attackers(game_server, message):
    """
    Handle DECLARE_ATTACKERS.
    """
    game_server.declare_attackers(message)


def declare_blockers(game_server, message):
    """
    Handle DECLARE_BLOCKERS.
    """
    game_server.declare_blockers(message)


def assign_damage_order(game_server, message):
    """
    Handle ASSIGN_DAMAGE_ORDER.
    """
    game_server.assign_damage_order(message)