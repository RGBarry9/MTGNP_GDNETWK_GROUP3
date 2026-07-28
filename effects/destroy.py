# effects/destroy.py
"""
Destroy effect.

Destroys a target creature or permanent on the battlefield.
The destroyed card is moved to its owner's graveyard.
"""

from typing import Optional, Dict, Any
from models.player import Player
from models.card import Card


def apply(game_state, creature: Card, source=None) -> Optional[Dict[str, Any]]:
    """
    Destroy a creature or permanent on the battlefield.
    
    Args:
        game_state: The current game state
        creature: The creature to destroy
        source: The source of the destroy effect (optional)
        
    Returns:
        Optional[Dict[str, Any]]: State change dictionary for STACK_RESOLVE PDU,
                                  or None if the creature couldn't be destroyed
    """
    # Get the owner
    owner = game_state.get_player(creature.owner)
    
    # Check if creature is on the battlefield
    if owner is None or creature not in owner.battlefield:
        return None
    
    # Remove from battlefield
    owner.battlefield.remove(creature)
    
    # Untap the creature (in case it was tapped)
    creature.tapped = False
    
    # Add to graveyard (use .add() method)
    owner.graveyard.add(creature)
    
    # Return state change
    return {
        "change_type": "DESTROY",
        "target": _creature_ref(creature),
        "creature_name": creature.name,
        "owner": owner.player_id,
        "source": getattr(source, 'card_id', 'unknown') if source else 'unknown'
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