# effects/effect_manager.py
"""
Effect Manager - Orchestrates all card effects.

Routes effect specifications to the appropriate effect handler
and aggregates state changes for STACK_RESOLVE PDUs.
"""

from typing import Optional, Dict, Any, List, Union
from models.player import Player
from models.card import Card

from effects import damage
from effects import destroy
from effects import counter
from effects import draw
from effects import gain_life
from effects import discard


class EffectManager:
    """
    Manages the application of card effects.
    
    Responsibilities:
    - Route effect specs to appropriate handlers
    - Aggregate state changes
    - Resolve targets
    """

    def __init__(self, game_state):
        self.game_state = game_state

    def apply(self, effect_spec: Dict[str, Any], source=None) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """
        Apply a single effect spec.
        
        Args:
            effect_spec: Effect specification dictionary
            source: The source of the effect (optional)
            
        Returns:
            Union[Dict, List, None]: State change dict, list of state changes,
                                     or None if no effect
            
        Raises:
            ValueError: If effect_type is unknown
        """
        effect_type = effect_spec.get("effect_type")

        handler = self._handlers().get(effect_type)

        if handler is None:
            raise ValueError(f"Unknown effect_type '{effect_type}'.")

        return handler(effect_spec, source)

    def apply_all(self, effect_specs: List[Dict[str, Any]], source=None) -> List[Dict[str, Any]]:
        """
        Apply a list of effect specs in order.
        
        Args:
            effect_specs: List of effect specifications
            source: The source of the effects (optional)
            
        Returns:
            List[Dict[str, Any]]: Combined list of state changes
        """
        state_changes = []

        for effect_spec in effect_specs:
            result = self.apply(effect_spec, source)

            if result is None:
                continue

            if isinstance(result, list):
                state_changes.extend(result)
            else:
                state_changes.append(result)

        return state_changes

    # ==========================================================
    # Effect Handlers
    # ==========================================================

    def _handlers(self) -> Dict[str, callable]:
        """Return the effect handler registry."""
        return {
            "DAMAGE": self._damage,
            "DESTROY": self._destroy,
            "COUNTER": self._counter,
            "GAIN_LIFE": self._gain_life,
            "DRAW": self._draw,
            "DISCARD": self._discard,
            # Add more effects as needed:
            # "BUFF": self._buff,
            # "ADD_MANA": self._add_mana,
        }

    def _damage(self, effect_spec: Dict[str, Any], source) -> Optional[Dict[str, Any]]:
        """Handle DAMAGE effect."""
        target = self._resolve_target(effect_spec.get("target"))
        if target is None:
            return None
        return damage.apply(target, effect_spec.get("amount", 0), source)

    def _destroy(self, effect_spec: Dict[str, Any], source) -> Optional[Dict[str, Any]]:
        """Handle DESTROY effect."""
        creature = self._resolve_creature(effect_spec.get("target"))
        if creature is None:
            return None
        return destroy.apply(self.game_state, creature, source)

    def _counter(self, effect_spec: Dict[str, Any], source) -> Optional[Dict[str, Any]]:
        """Handle COUNTER effect."""
        stack = getattr(self.game_state, "stack", None)
        if stack is None:
            return None
        return counter.apply(stack, effect_spec.get("target"), source)

    def _gain_life(self, effect_spec: Dict[str, Any], source) -> Optional[Dict[str, Any]]:
        """Handle GAIN_LIFE effect."""
        player = self.game_state.get_player(effect_spec.get("target"))
        if player is None:
            return None
        return gain_life.apply(player, effect_spec.get("amount", 0), source)

    def _draw(self, effect_spec: Dict[str, Any], source) -> Optional[Dict[str, Any]]:
        """Handle DRAW effect."""
        player = self.game_state.get_player(effect_spec.get("target"))
        if player is None:
            return None
        return draw.apply(player, effect_spec.get("amount", 1), source)

    def _discard(self, effect_spec: Dict[str, Any], source) -> Optional[List[Dict[str, Any]]]:
        """Handle DISCARD effect."""
        player = self.game_state.get_player(effect_spec.get("target"))
        if player is None:
            return None
        return discard.apply(player, effect_spec.get("card_ids", []), source)

    # ==========================================================
    # Target Resolution
    # ==========================================================

    def _resolve_target(self, target_id: str) -> Optional[Union[Player, Card]]:
        """
        Resolve a target ID to a Player or Card.
        
        Args:
            target_id: Target identifier (player_id or card_id)
            
        Returns:
            Optional[Union[Player, Card]]: Resolved target, or None
        """
        # Try as player
        player = self.game_state.get_player(target_id)
        if player is not None:
            return player

        # Try as creature
        return self._resolve_creature(target_id)

    def _resolve_creature(self, target_id: str) -> Optional[Card]:
        """
        Resolve a target ID to a creature Card.
        
        Args:
            target_id: Card ID of the creature
            
        Returns:
            Optional[Card]: Resolved creature, or None
        """
        for player in self.game_state.players:
            for permanent in player.battlefield:
                # Use card_id, not id
                if permanent.card_id == target_id:
                    return permanent
        return None