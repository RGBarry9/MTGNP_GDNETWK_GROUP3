"""
Priority and stack message handlers.
"""


def priority_pass(game_server, message):
    """
    Handle PRIORITY_PASS.
    """
    game_server.priority_pass(message)


def stack_push(game_server, message):
    """
    Handle STACK_PUSH.
    """
    game_server.stack_push(message)


def stack_resolve(game_server, message):
    """
    Handle STACK_RESOLVE.
    """
    game_server.stack_resolve(message)