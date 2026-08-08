# effects/draw.py
"""
Draw effect.

Player draws cards from their library into their hand.
If the library is empty, the player loses (checked by WinConditionManager).
"""

from typing import Optional, Dict, Any, List
from models.player import Player
from models.card import Card


def apply(player: Player, amount: int = 1, source=None) -> Optional[Dict[str, Any]]:
    """
    Draw cards from the player's library into their hand.
    
    Args:
        player: The player drawing cards
        amount: Number of cards to draw
        source: The source of the draw effect (optional)
        
    Returns:
        Optional[Dict[str, Any]]: State change dictionary for STACK_RESOLVE PDU,
                                  or None if amount <= 0
    """
    if amount <= 0:
        return None

    drawn = []
    empty_library = False

    # Draw from library (not deck!)
    for _ in range(amount):
        card = player.library.draw()  # ← FIXED: Use library
        if card is None:
            empty_library = True
            break
        drawn.append(card)

    # Add drawn cards to hand
    for card in drawn:
        player.hand.add(card)

    return {
        "change_type": "DRAW",
        "target": player.player_id,
        "amount": len(drawn),
        "empty_library": empty_library,
        "source": getattr(source, 'card_id', 'unknown') if source else 'unknown'
    }


def draw_multiple(player: Player, amounts: List[int], source=None) -> List[Dict[str, Any]]:
    """
    Draw cards in multiple batches (for complex effects).
    
    Args:
        player: The player drawing cards
        amounts: List of amounts to draw (each creates a separate state change)
        source: The source of the draw effect (optional)
        
    Returns:
        List[Dict[str, Any]]: List of state change dictionaries
    """
    changes = []
    for amount in amounts:
        change = apply(player, amount, source)
        if change:
            changes.append(change)
    return changes