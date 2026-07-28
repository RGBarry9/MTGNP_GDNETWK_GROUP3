# effects/damage.py
"""
Damage effect.

Deals damage to a target player or creature.
"""

from typing import Optional, Dict, Any, Union
from models.player import Player
from models.card import Card


def apply(target: Union[Player, Card], amount: int, source=None) -> Optional[Dict[str, Any]]:
    """
    Apply damage to a target.
    
    Args:
        target: The target (Player or Card/creature)
        amount: Amount of damage to deal
        source: The source of the damage (optional)
        
    Returns:
        Optional[Dict[str, Any]]: State change dictionary for STACK_RESOLVE PDU,
                                  or None if amount <= 0
    """
    if amount <= 0:
        return None
    
    # Check if target is a player (has life attribute)
    if hasattr(target, "life") and hasattr(target, "player_id"):
        return _damage_player(target, amount)
    
    # Otherwise treat as creature
    return _damage_creature(target, amount, source)


def _damage_player(player: Player, amount: int) -> Dict[str, Any]:
    """
    Deal damage to a player.
    
    Args:
        player: The player to damage
        amount: Amount of damage
        
    Returns:
        Dict[str, Any]: State change dictionary
    """
    player.life -= amount
    
    return {
        "change_type": "DAMAGE",
        "target": player.player_id,
        "amount": amount,
        "target_type": "player"
    }


def _damage_creature(creature: Card, amount: int, source=None) -> Dict[str, Any]:
    """
    Deal damage to a creature.
    
    Args:
        creature: The creature to damage
        amount: Amount of damage
        source: The source of the damage
        
    Returns:
        Dict[str, Any]: State change dictionary
    """
    # Use the correct field name from Card model
    creature.damage_marked += amount
    
    return {
        "change_type": "DAMAGE",
        "target": _creature_ref(creature),
        "amount": amount,
        "target_type": "creature",
        "lethal": creature.is_destroyed()
    }


def _creature_ref(creature: Card) -> str:
    """
    Get the creature's identifier.
    
    Args:
        creature: The creature card
        
    Returns:
        str: The creature's card_id or name
    """
    return getattr(creature, "card_id", creature.name)