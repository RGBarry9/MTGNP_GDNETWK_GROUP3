# handlers/combat_handler.py
"""
Combat message handlers.

Handles DECLARE_ATTACKERS, DECLARE_BLOCKERS, and ASSIGN_DAMAGE_ORDER PDUs.
"""

from models.card import Card
from config.enums import Phase


def declare_attackers(game_server, message):
    """
    Handle DECLARE_ATTACKERS PDU.
    """
    player_id = message.get("player_id")
    attackers_data = message.get("attackers", [])
    
    # Get player
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    # Check if it's the active player's turn to declare attackers
    if game_server.game_state.active_player != player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            "Only the active player can declare attackers"
        )
        return
    
    # Check if in correct phase - FIXED: Compare with Phase enum
    if game_server.game_state.current_phase != Phase.DECLARE_ATTACKERS:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            f"Cannot declare attackers in phase: {game_server.game_state.current_phase}"
        )
        return
    
    # Convert attacker data to Card objects
    attackers = []
    for att_data in attackers_data:
        creature_id = att_data.get("creature_id")
        target = att_data.get("target")
        
        # Find creature on battlefield using the helper
        creature = _find_creature(player, creature_id)
        if not creature:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_ACTION",
                f"Creature {creature_id} not found on battlefield"
            )
            return
        
        # Validate can attack
        valid, reason = game_server.validator.can_attack(player, creature)
        if not valid:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_ACTION",
                reason
            )
            return
        
        attackers.append(creature)
    
    # Declare attackers in combat manager
    game_server.game.combat_manager.declare_attackers(player, attackers)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Give priority to the active player (AP retains priority after declaring)
    game_server._give_priority()


def declare_blockers(game_server, message):
    """
    Handle DECLARE_BLOCKERS PDU.
    """
    player_id = message.get("player_id")
    blockers_data = message.get("blockers", [])
    
    # Get player
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    # Check if in correct phase - FIXED: Compare with Phase enum
    if game_server.game_state.current_phase != Phase.DECLARE_BLOCKERS:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            f"Cannot declare blockers in phase: {game_server.game_state.current_phase}"
        )
        return
    
    # Process each blocker declaration
    for block_data in blockers_data:
        blocker_id = block_data.get("creature_id")
        blocking_id = block_data.get("blocking_id")
        
        # Find blocker on battlefield
        blocker = _find_creature(player, blocker_id)
        if not blocker:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_ACTION",
                f"Blocker {blocker_id} not found on battlefield"
            )
            return
        
        # Find attacker
        attacker = None
        for att in game_server.game_state.attackers:
            if att.card_id == blocking_id:
                attacker = att
                break
        
        if not attacker:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_TARGET",
                f"Attacker {blocking_id} not found"
            )
            return
        
        # Validate can block
        valid, reason = game_server.validator.can_block(player, blocker, attacker)
        if not valid:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_ACTION",
                reason
            )
            return
        
        # Assign blocker
        game_server.game.combat_manager.declare_blocker(player, blocker, attacker)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Give priority to the active player
    game_server._give_priority()


def assign_damage_order(game_server, message):
    """
    Handle ASSIGN_DAMAGE_ORDER PDU.
    """
    player_id = message.get("player_id")
    attacker_id = message.get("attacker_id")
    blocker_order = message.get("blocker_order", [])
    
    # Get player
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    # Check if in correct phase - FIXED: Compare with Phase enum
    if game_server.game_state.current_phase != Phase.ASSIGN_DAMAGE_ORDER:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            f"Cannot assign damage order in phase: {game_server.game_state.current_phase}"
        )
        return
    
    # Find the attacker
    attacker = None
    for att in game_server.game_state.attackers:
        if att.card_id == attacker_id:
            attacker = att
            break
    
    if not attacker:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Attacker {attacker_id} not found"
        )
        return
    
    # Store the damage order
    game_server.game_state.damage_assignments = blocker_order
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # If all damage orders assigned, resolve combat
    _resolve_combat(game_server)


# ==========================================================
# Helper Functions
# ==========================================================

def _find_creature(player, creature_id: str):
    """Find a creature on the battlefield by card_id."""
    for card in player.battlefield:
        if hasattr(card, 'card_id') and card.card_id == creature_id:
            return card
    return None


def _resolve_combat(game_server):
    """Resolve combat damage and broadcast results."""
    # Resolve combat damage
    game_server.game.combat_manager.resolve_combat()
    
    # Build damage events
    damage_events = []
    for attacker in game_server.game_state.attackers:
        blocker = game_server.game_state.blockers.get(attacker.card_id)
        if blocker:
            damage_events.append({
                "source": attacker.name,
                "target": blocker.name,
                "amount": attacker.power or 0
            })
        else:
            # Unblocked attacker deals damage to player
            defender = game_server.game_state.get_opponent(game_server.game_state.active_player)
            damage_events.append({
                "source": attacker.name,
                "target": defender.player_id,
                "amount": attacker.power or 0
            })
    
    # Broadcast COMBAT_DAMAGE_RESULT
    result_msg = {
        "type": "COMBAT_DAMAGE_RESULT",
        "damage_events": damage_events,
        "life_totals": {
            p.player_id: p.life for p in game_server.game_state.players
        },
        "creatures_died": []
    }
    game_server.broadcast(result_msg)
    
    # Clean up combat
    game_server.game.combat_manager.cleanup()
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Check win conditions
    winner = game_server.game.win_manager.check()
    if winner:
        game_server._end_game(game_server.game_state.get_opponent(winner).player_id, "LIFE_ZERO")
        return
    
    # Proceed to next phase
    game_server.game.turn_manager.next_phase()
    game_server._broadcast_phase_transition()
    game_server._give_priority()