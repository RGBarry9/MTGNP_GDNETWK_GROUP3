# handlers/spell_handler.py
"""
Spell-related message handlers.

Handles CAST_SPELL, PLAY_LAND, and ACTIVATE_ABILITY PDUs.
"""

from models.stack_item import StackItem, StackItemType
from models.card import Card


def cast_spell(game_server, message):
    """
    Handle CAST_SPELL PDU.
    
    Expected message format:
    {
        "type": "CAST_SPELL",
        "seq_num": 7,
        "player_id": "player_1",
        "card_id": "lightning_bolt_001",
        "targets": ["player_2"],
        "mana_payment": {"R": 1}
    }
    """
    player_id = message.get("player_id")
    card_id = message.get("card_id")
    targets = message.get("targets", [])
    mana_payment = message.get("mana_payment", {})
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
        game_server._give_priority()
        return
    
    # ==========================================================
    # Step 4: Find card in hand
    # ==========================================================
    card = None
    for c in player.hand:
        if c.card_id == card_id:
            card = c
            break
    
    if not card:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Card {card_id} not in hand"
        )
        return
    
    # ==========================================================
    # Step 5: Validate spell casting
    # ==========================================================
    valid, reason = game_server.validator.can_cast_spell(player, card)
    if not valid:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            reason
        )
        return
    
    # ==========================================================
    # Step 6: Check phase for sorcery (only in main phase)
    # ==========================================================
    if card.is_sorcery():
        if game_server.game_state.current_phase not in ["PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"]:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "WRONG_PHASE",
                f"Sorcery can only be cast in main phase, not {game_server.game_state.current_phase}"
            )
            return
    
    # ==========================================================
    # Step 7: Validate targets
    # ==========================================================
    for target in targets:
        if not game_server.validator.valid_target(target):
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_TARGET",
                f"Invalid target: {target}"
            )
            return
    
    # ==========================================================
    # Step 8: Validate mana payment
    # ==========================================================
    if not _validate_mana_payment(game_server, player, card, mana_payment):
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "INSUFFICIENT_MANA",
            f"Unable to pay mana cost for {card.name}"
        )
        return
    
    print(f"📝 {player_id} casts {card.name}")
    print(f"   Targets: {targets}")
    print(f"   Mana payment: {mana_payment}")
    
    # ==========================================================
    # Step 9: Remove card from hand
    # ==========================================================
    player.hand.remove(card)
    
    # ==========================================================
    # Step 10: Handle based on card type
    # ==========================================================
    
    # If creature, put on battlefield
    if card.is_creature():
        card.summoning_sick = True
        card.controller = player_id
        card.owner = player_id
        player.battlefield.add(card)
        
        print(f"   🏟️ {card.name} enters battlefield")
        
        # Check for triggered abilities (ETB)
        _check_triggered_abilities(game_server, card, player)
        
        # Broadcast updated state
        game_server._broadcast_personalized_state()
        
        # Grant priority to same player (they retain priority)
        game_server._give_priority()
        return
    
    # If instant or sorcery, put on stack
    if card.is_instant() or card.is_sorcery():
        # Create stack item
        stack_item_id = f"stk_{game_server.next_seq()}"
        stack_item = StackItem(
            stack_item_id=stack_item_id,
            item_type=StackItemType.SPELL,
            source=card,
            source_id=card.card_id,
            source_name=card.name,
            controller=player_id,
            targets=targets,
            effects=getattr(card, 'effects', [])
        )
        
        # Push to stack
        game_server.game.cast_spell(stack_item)
        
        # Broadcast STACK_PUSH
        push_msg = {
            "type": "STACK_PUSH",
            "stack_item_id": stack_item_id,
            "item_type": "SPELL",
            "source": card.card_id,
            "targets": targets,
            "controller": player_id
        }
        game_server.broadcast(push_msg)
        
        # Broadcast updated state
        game_server._broadcast_personalized_state()
        
        # Grant priority to same player (they retain priority)
        game_server._give_priority()
        return
    
    # If land, use play_land handler
    if card.is_land():
        # Delegate to play_land
        play_land(game_server, message)
        return
    
    # Unknown card type
    game_server.send_error(
        game_server.connection_player.get(player_id),
        "ILLEGAL_ACTION",
        f"Unknown card type: {card.card_type}"
    )


def play_land(game_server, message):
    """
    Handle PLAY_LAND PDU.
    
    Expected message format:
    {
        "type": "PLAY_LAND",
        "seq_num": 5,
        "player_id": "player_1",
        "card_id": "mountain_003"
    }
    """
    player_id = message.get("player_id")
    card_id = message.get("card_id")
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
    # Step 3: Check sequence number
    # ==========================================================
    current_seq = game_server.game_state.priority_seq_num
    if seq_num != current_seq:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "STALE_ACTION",
            f"Priority token mismatch. Expected {current_seq}, got {seq_num}",
            rejected_action=message
        )
        game_server._give_priority()
        return
    
    # ==========================================================
    # Step 4: Find card in hand
    # ==========================================================
    card = None
    for c in player.hand:
        if c.card_id == card_id:
            card = c
            break
    
    if not card:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Card {card_id} not in hand"
        )
        return
    
    # ==========================================================
    # Step 5: Check if it's a land
    # ==========================================================
    if not card.is_land():
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"{card.name} is not a land"
        )
        return
    
    # ==========================================================
    # Step 6: Check if in main phase
    # ==========================================================
    if game_server.game_state.current_phase not in ["PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"]:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "WRONG_PHASE",
            f"Lands can only be played in main phase, not {game_server.game_state.current_phase}"
        )
        return
    
    # ==========================================================
    # Step 7: Check if already played a land this turn
    # ==========================================================
    if player.lands_played >= 1:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            "Already played a land this turn"
        )
        return
    
    print(f"🏔️ {player_id} plays {card.name}")
    
    # ==========================================================
    # Step 8: Play the land - CRITICAL: Remove from hand, add to battlefield
    # ==========================================================
    # Remove from hand
    player.hand.remove(card)
    
    # Add to battlefield
    player.battlefield.add(card)
    player.lands_played += 1
    
    print(f"   📥 {card.name} moved from hand to battlefield")
    print(f"   📊 {player_id} hand size: {len(player.hand)}, lands played: {player.lands_played}")
    
    # Land doesn't use the stack
    
    # ==========================================================
    # Step 9: Broadcast updated state
    # ==========================================================
    game_server._broadcast_personalized_state()
    
    # ==========================================================
    # Step 10: Grant priority to same player (they retain priority)
    # ==========================================================
    # NOTE: This increments the priority sequence number
    game_server._give_priority()


def activate_ability(game_server, message):
    """
    Handle ACTIVATE_ABILITY PDU.
    
    Expected message format:
    {
        "type": "ACTIVATE_ABILITY",
        "seq_num": 9,
        "player_id": "player_1",
        "source_id": "llanowar_elves_002",
        "ability_index": 0,
        "targets": [],
        "cost_payment": {"tap": true, "mana": {}}
    }
    """
    player_id = message.get("player_id")
    source_id = message.get("source_id")
    ability_index = message.get("ability_index", 0)
    targets = message.get("targets", [])
    cost_payment = message.get("cost_payment", {})
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
    # Step 3: Check sequence number
    # ==========================================================
    current_seq = game_server.game_state.priority_seq_num
    if seq_num != current_seq:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "STALE_ACTION",
            f"Priority token mismatch. Expected {current_seq}, got {seq_num}",
            rejected_action=message
        )
        game_server._give_priority()
        return
    
    # ==========================================================
    # Step 4: Find source permanent on battlefield
    # ==========================================================
    source = None
    for p in game_server.game_state.players:
        for permanent in p.battlefield:
            if permanent.card_id == source_id:
                source = permanent
                break
        if source:
            break
    
    if not source:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Source {source_id} not found on battlefield"
        )
        return
    
    # ==========================================================
    # Step 5: Check if source has abilities
    # ==========================================================
    if not source.abilities or ability_index >= len(source.abilities):
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Ability index {ability_index} not found on {source.name}"
        )
        return
    
    ability = source.abilities[ability_index]
    
    # ==========================================================
    # Step 6: Check if ability can be activated
    # ==========================================================
    # Check tap cost
    if ability.requires_tap() and source.is_tapped():
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"{source.name} is already tapped"
        )
        return
    
    # Check summoning sickness for creatures with tap abilities
    if source.is_creature() and source.summoning_sick and ability.requires_tap():
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"{source.name} has summoning sickness and cannot tap"
        )
        return
    
    print(f"⚡ {player_id} activates {ability.name} on {source.name}")
    
    # ==========================================================
    # Step 7: Pay costs
    # ==========================================================
    if ability.requires_tap():
        source.tap()
    
    # ==========================================================
    # Step 8: Apply ability effect
    # ==========================================================
    effect = ability.effect
    
    if effect.get("effect_type") == "ADD_MANA":
        # Mana ability - immediate
        color = effect.get("color")
        amount = effect.get("amount", 1)
        player.add_mana(color, amount)
        print(f"   💎 Added {amount} {color} mana")
        
        # Broadcast updated state
        game_server._broadcast_personalized_state()
        
        # Grant priority to same player
        game_server._give_priority()
        return
    
    # Non-mana abilities go on stack
    stack_item_id = f"stk_{game_server.next_seq()}"
    stack_item = StackItem(
        stack_item_id=stack_item_id,
        item_type=StackItemType.ABILITY,
        source=source,
        source_id=source.card_id,
        source_name=source.name,
        controller=player_id,
        targets=targets,
        effects=[effect],
        ability=ability
    )
    
    game_server.game.cast_spell(stack_item)
    
    # Broadcast STACK_PUSH
    push_msg = {
        "type": "STACK_PUSH",
        "stack_item_id": stack_item_id,
        "item_type": "ABILITY",
        "source": source.card_id,
        "targets": targets,
        "controller": player_id
    }
    game_server.broadcast(push_msg)
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()
    
    # Grant priority to same player
    game_server._give_priority()


# ==========================================================
# Helper Functions
# ==========================================================

def _validate_mana_payment(game_server, player, card, mana_payment):
    """
    Validate that the player can pay the mana cost.
    
    Returns:
        bool: True if mana payment is valid
    """
    # For now, simplified - just check if payment has required colors
    # In a real implementation, this would check against the card's mana cost
    
    # For creatures with mana cost like "1G", check if G is paid
    if 'G' in card.mana_cost and mana_payment.get('G', 0) < 1:
        return False
    
    # For spells with mana cost like "R", check if R is paid
    if 'R' in card.mana_cost and mana_payment.get('R', 0) < 1:
        return False
    
    # For spells with mana cost like "UU", check if U is paid twice
    if 'U' in card.mana_cost and mana_payment.get('U', 0) < card.mana_cost.count('U'):
        return False
    
    # For spells with mana cost like "3BB", check if B is paid twice
    if 'B' in card.mana_cost and mana_payment.get('B', 0) < card.mana_cost.count('B'):
        return False
    
    # For spells with mana cost like "1W", check if W is paid
    if 'W' in card.mana_cost and mana_payment.get('W', 0) < 1:
        return False
    
    return True


def _check_triggered_abilities(game_server, card, player):
    """
    Check for triggered abilities on a card entering the battlefield.
    """
    if not card.trigger:
        return
    
    event = card.trigger.get("event")
    if event == "ENTER_BATTLEFIELD":
        effect = card.trigger.get("effect")
        print(f"   🔄 Trigger: {card.name} enters battlefield")
        
        # Apply the triggered effect
        game_server.game.effect_manager.apply(effect, card)


def _find_card_in_hand(player, card_id):
    """Find a card in the player's hand by card_id."""
    for card in player.hand:
        if card.card_id == card_id:
            return card
    return None