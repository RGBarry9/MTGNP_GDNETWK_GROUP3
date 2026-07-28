# effects/discard.py
"""
Discard effect.

Moves one or more cards from a player's hand to their graveyard.
"""

from typing import Optional, List, Dict, Any
from models.player import Player
from models.card import Card


def apply(player: Player, card_ids: List[str], source=None) -> Optional[List[Dict[str, Any]]]:
    """
    Discard the specified cards from the player's hand.
    
    Args:
        player: The player discarding cards
        card_ids: List of card IDs to discard
        source: The source of the discard effect (optional)
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of state change dictionaries,
                                        or None if no cards were discarded
    """
    state_changes = []

    for card_id in card_ids:
        card = _find_card(player.hand, card_id)
        
        if card is None:
            continue

        # Remove from hand, add to graveyard
        player.hand.remove(card)
        player.graveyard.add(card)

        state_changes.append({
            "change_type": "DISCARD",  # ← FIXED: Use "change_type" (consistent)
            "target": player.player_id,
            "card_id": card.card_id,   # ← FIXED: Use card_id
            "card_name": card.name,
            "source": getattr(source, 'card_id', 'unknown') if source else 'unknown'
        })

    if not state_changes:
        return None

    return state_changes


def _find_card(hand, card_id: str) -> Optional[Card]:
    """
    Find a card in a player's hand by ID.
    
    Args:
        hand: The player's hand
        card_id: The card ID to find
        
    Returns:
        Optional[Card]: The card if found, None otherwise
    """
    for card in hand.cards:
        # Use card_id, not id
        if card.card_id == card_id:
            return card
    return None


def discard_all(player: Player, source=None) -> Optional[List[Dict[str, Any]]]:
    """
    Discard all cards from the player's hand.
    
    Args:
        player: The player discarding cards
        source: The source of the discard effect (optional)
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of state change dictionaries
    """
    if len(player.hand) == 0:
        return None
    
    card_ids = [card.card_id for card in player.hand]
    return apply(player, card_ids, source)


def discard_to_size(player: Player, max_size: int = 7, source=None) -> Optional[List[Dict[str, Any]]]:
    """
    Discard cards until hand size is at most max_size.
    
    Args:
        player: The player discarding cards
        max_size: Maximum hand size (default 7)
        source: The source of the discard effect (optional)
        
    Returns:
        Optional[List[Dict[str, Any]]]: List of state change dictionaries
    """
    if len(player.hand) <= max_size:
        return None
    
    cards_to_discard = len(player.hand) - max_size
    card_ids = [card.card_id for card in player.hand[:cards_to_discard]]
    return apply(player, card_ids, source)