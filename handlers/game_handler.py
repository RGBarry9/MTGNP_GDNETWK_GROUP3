# handlers/game_handler.py
"""
General game message handlers.

Handles PHASE_TRANSITION, CONCEDE, and GAME_OVER PDUs.
"""

from config.enums import Phase


def phase_transition(game_server, message):
    """
    Handle PHASE_TRANSITION PDU.
    """
    player_id = message.get("player_id")
    
    # Check if this is a client trying to transition (shouldn't happen)
    if player_id:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            "Only the server can transition phases"
        )
        return
    
    # Server-side phase transition
    from_phase = message.get("from_phase")
    to_phase = message.get("to_phase")
    
    print(f"PHASE_TRANSITION: {from_phase} -> {to_phase}")
    
    # Update game state
    game_server.game_state.set_phase(to_phase)
    
    # If entering a phase with priority, give priority
    if game_server._phase_has_priority():
        game_server._give_priority()
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()


def concede(game_server, message):
    """
    Handle CONCEDE PDU.
    """
    player_id = message.get("player_id")
    
    # Validate player exists
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    # Get opponent (winner)
    opponent = game_server.game_state.get_opponent(player)
    if not opponent:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            "No opponent found"
        )
        return
    
    print(f"\n*** {player_id} CONCEDES! ***")
    print(f"Winner: {opponent.player_id}")
    
    # Broadcast GAME_OVER
    game_over_msg = {
        "type": "GAME_OVER",
        "winner_id": opponent.player_id,
        "loser_id": player_id,
        "reason": "CONCEDE"
    }
    game_server.broadcast(game_over_msg)
    
    # End the game
    game_server._end_game(player_id, "CONCEDE")


def game_over(game_server, message):
    """
    Handle GAME_OVER PDU.
    """
    winner_id = message.get("winner_id")
    loser_id = message.get("loser_id")
    reason = message.get("reason", "UNKNOWN")
    
    print(f"\n*** GAME OVER ***")
    print(f"Winner: {winner_id}")
    print(f"Loser: {loser_id}")
    print(f"Reason: {reason}")
    
    # Broadcast GAME_OVER to all clients
    game_over_msg = {
        "type": "GAME_OVER",
        "winner_id": winner_id,
        "loser_id": loser_id,
        "reason": reason
    }
    game_server.broadcast(game_over_msg)
    
    # Reset game state for next game
    game_server.game_state.game_over = True
    game_server.game_state.started = False
    game_server.game_state.set_phase("LOBBY")
    
    # Clear player states
    for player in game_server.game_state.players:
        player.battlefield.clear()
        player.hand.clear()
        player.graveyard.clear()
        player.library.clear()
        player.life = 20
        player.ready = False
        player.lands_played = 0
        player.passed_priority = False
    
    # Reset connections - only if attributes exist
    if hasattr(game_server, 'player_connections'):
        game_server.player_connections.clear()
    if hasattr(game_server, 'connection_player'):
        game_server.connection_player.clear()
    
    print("\nReturning to LOBBY state.")
    print("Waiting for new PLAYER_READY...\n")


def game_state_update(game_server, message):
    """Handle GAME_STATE_UPDATE PDU."""
    player_id = message.get("player_id")
    
    if player_id:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "UNKNOWN_TYPE",
            "GAME_STATE_UPDATE is server-to-client only"
        )
        return
    
    state = message.get("state", {})
    phase = state.get("phase")
    
    if phase:
        game_server.game_state.set_phase(phase)
        print(f"Game state updated: phase={phase}")


def end_turn(game_server, message):
    """Handle END_TURN PDU."""
    player_id = message.get("player_id")
    
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    if game_server.game_state.active_player != player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            "Only the active player can end the turn"
        )
        return
    
    if game_server.game_state.current_phase not in [Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN]:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            f"Cannot end turn in phase: {game_server.game_state.current_phase}"
        )
        return
    
    print(f"{player_id} ended the turn")
    game_server.game.turn_manager.end_turn()
    game_server._broadcast_phase_transition()
    game_server._give_priority()