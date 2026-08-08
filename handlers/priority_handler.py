# handlers/priority_handler.py
"""
Priority and stack message handlers.

Handles PRIORITY_PASS, STACK_PUSH, and STACK_RESOLVE PDUs.
"""

from models.stack_item import StackItem, StackItemType


def priority_pass(game_server, message):
    """
    Handle PRIORITY_PASS PDU.
    
    Expected message format:
    {
        "type": "PRIORITY_PASS",
        "seq_num": 43,
        "player_id": "player_1"
    }
    """
    player_id = message.get("player_id")
    seq_num = message.get("seq_num")
    
    # ==========================================================
    # Step 1: Validate player exists
    # ==========================================================
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    # ==========================================================
    # Step 2: Check if player has priority
    # ==========================================================
    if not game_server.game.priority_manager.has_priority(player):
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "NOT_YOUR_PRIORITY",
            f"Player {player_id} does not have priority"
        )
        return
    
    # ==========================================================
    # Step 3: Check sequence number (stale action)
    # ==========================================================
    current_seq = game_server.game_state.priority_seq_num
    if seq_num != current_seq:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "STALE_ACTION",
            f"Priority token mismatch. Expected {current_seq}, got {seq_num}",
            rejected_action=message
        )
        # Re-issue the grant to the SAME player - a rejected/stale
        # action doesn't take priority away from whoever still holds it.
        game_server._give_priority(player)
        return
    
    # ==========================================================
    # Step 4: Process priority pass
    # ==========================================================
    print(f"📤 {player_id} passes priority")
    
    result = game_server.game.pass_priority(player)
    
    if result == "NEXT_PLAYER":
        # Priority moves to the other player. pass_priority() has
        # already updated game_state.priority_player internally; send
        # them the PRIORITY_GRANT so they actually receive a token to
        # act (or pass) on (RFC 0001 Section 8.1 rule 4).
        opponent = game_server.game_state.get_opponent(player)
        game_server._give_priority(opponent)

    elif result == "RESOLVE_STACK":
        # Both players passed with non-empty stack - resolve
        print("   🔄 Resolving stack...")
        _resolve_stack(game_server)
        
    elif result == "ADVANCE_PHASE":
        # Both players passed with empty stack - advance phase
        print("   ⏭️ Advancing phase...")
        game_server.game.turn_manager.next_phase()
        game_server._broadcast_phase_transition()
        
        # Check if new phase has priority
        if game_server._phase_has_priority():
            game_server._give_priority()
        else:
            # Phase without priority (e.g., Untap, Cleanup)
            # Auto-advance to next phase
            game_server.game.turn_manager.next_phase()
            game_server._broadcast_phase_transition()
            if game_server._phase_has_priority():
                game_server._give_priority()


def stack_push(game_server, message):
    """
    Handle STACK_PUSH PDU.
    
    Expected message format:
    {
        "type": "STACK_PUSH",
        "seq_num": 8,
        "stack_item_id": "stk_01",
        "item_type": "SPELL",
        "source": "lightning_bolt_001",
        "targets": ["player_2"],
        "controller": "player_1"
    }
    
    Note: This is typically a server-broadcast message.
    Clients do not normally send this PDU.
    """
    player_id = message.get("controller")
    
    # ==========================================================
    # Step 1: Check if this is a client trying to push
    # ==========================================================
    if player_id:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            "Only the server can push to the stack"
        )
        return
    
    # ==========================================================
    # Step 2: Server-side stack push
    # ==========================================================
    stack_item_id = message.get("stack_item_id")
    item_type = message.get("item_type")
    source = message.get("source")
    targets = message.get("targets", [])
    controller = message.get("controller")
    
    print(f"📚 STACK_PUSH: {source} ({item_type}) by {controller}")
    
    # Create stack item
    # Note: In a real implementation, you'd create from the actual card
    stack_item = StackItem(
        stack_item_id=stack_item_id,
        item_type=StackItemType(item_type) if item_type else StackItemType.SPELL,
        source=source,
        source_id=source,
        source_name=source,
        controller=controller,
        targets=targets
    )
    
    # Push to stack
    game_server.game.cast_spell(stack_item)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()


def stack_resolve(game_server, message):
    """
    Handle STACK_RESOLVE PDU.
    
    Expected message format:
    {
        "type": "STACK_RESOLVE",
        "seq_num": 31,
        "stack_item_id": "stk_01",
        "result": "RESOLVED",
        "state_changes": [...]
    }
    
    Note: This is typically a server-broadcast message.
    Clients do not normally send this PDU.
    """
    player_id = message.get("controller")
    
    # ==========================================================
    # Step 1: Check if this is a client trying to resolve
    # ==========================================================
    if player_id:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            "Only the server can resolve stack items"
        )
        return
    
    # ==========================================================
    # Step 2: Server-side stack resolution
    # ==========================================================
    stack_item_id = message.get("stack_item_id")
    result = message.get("result", "RESOLVED")
    state_changes = message.get("state_changes", [])
    
    print(f"📚 STACK_RESOLVE: {stack_item_id} -> {result}")
    
    # Broadcast to all clients
    game_server.broadcast(message)
    
    # Apply state changes
    for change in state_changes:
        _apply_state_change(game_server, change)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Check win conditions after resolution
    winner = game_server.game.win_manager.check()
    if winner:
        loser = game_server.game_state.get_opponent(winner)
        game_server._end_game(loser.player_id, "LIFE_ZERO")
        return
    
    # Grant priority to active player after resolution
    game_server._give_priority()


# ==========================================================
# Helper Functions
# ==========================================================

def _resolve_stack(game_server):
    """
    Resolve the top item on the stack.
    """
    # Get top stack item
    stack_item = game_server.game.stack_manager.peek()
    if not stack_item:
        return
    
    # Resolve the item
    state_changes = game_server.game.stack_manager.resolve()
    
    # Broadcast resolution
    resolve_msg = {
        "type": "STACK_RESOLVE",
        "stack_item_id": stack_item.stack_item_id,
        "result": "RESOLVED",
        "state_changes": state_changes or []
    }
    game_server.broadcast(resolve_msg)
    
    # Apply state changes
    for change in state_changes:
        _apply_state_change(game_server, change)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Check win conditions
    winner = game_server.game.win_manager.check()
    if winner:
        loser = game_server.game_state.get_opponent(winner)
        game_server._end_game(loser.player_id, "LIFE_ZERO")
        return
    
    # Grant priority to active player
    game_server._give_priority()


def _apply_state_change(game_server, change):
    """
    Apply a single state change from stack resolution.
    """
    change_type = change.get("change_type")
    target = change.get("target")
    amount = change.get("amount", 0)
    
    if change_type == "DAMAGE":
        # Apply damage to player or creature
        player = game_server.game_state.get_player(target)
        if player:
            player.life -= amount
            print(f"   💥 {player.player_id} takes {amount} damage")
        else:
            # Find creature
            for p in game_server.game_state.players:
                for creature in p.battlefield:
                    if creature.card_id == target:
                        creature.mark_damage(amount)
                        print(f"   💥 {creature.name} takes {amount} damage")
                        break
    
    elif change_type == "LIFE_GAIN":
        player = game_server.game_state.get_player(target)
        if player:
            player.life += amount
            print(f"   ❤️ {player.player_id} gains {amount} life")
    
    elif change_type == "DESTROY":
        # Find and destroy creature
        for p in game_server.game_state.players:
            for creature in p.battlefield:
                if creature.card_id == target:
                    p.battlefield.remove(creature)
                    p.graveyard.add(creature)
                    print(f"   💀 {creature.name} destroyed")
                    break
    
    elif change_type == "DRAW":
        player = game_server.game_state.get_player(target)
        if player:
            for _ in range(amount):
                card = player.draw_card()
                if card:
                    print(f"   📄 {player.player_id} drew {card.name}")
    
    elif change_type == "DISCARD":
        player = game_server.game_state.get_player(target)
        if player:
            card_id = change.get("card_id")
            for card in player.hand:
                if card.card_id == card_id:
                    player.hand.remove(card)
                    player.graveyard.add(card)
                    print(f"   🗑️ {player.player_id} discarded {card.name}")
                    break
    
    elif change_type == "COUNTER":
        # Counter effect already handled in stack resolution
        spell_name = change.get("spell_name", "Unknown")
        print(f"   🛑 {spell_name} was countered")