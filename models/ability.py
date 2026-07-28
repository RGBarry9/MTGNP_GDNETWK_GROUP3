# models/ability.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class Ability:
    """
    Represents a card ability.
    
    An ability can be:
    - Mana ability (adds mana)
    - Activated ability (cost: effect)
    - Triggered ability (when X happens, do Y)
    """

    name: str
    ability_type: str  # "MANA", "ACTIVATED", "TRIGGERED"
    cost: Dict[str, Any] = field(default_factory=dict)  # e.g., {"tap": True, "mana": {"R": 1}}
    text: str = ""
    effect: Dict[str, Any] = field(default_factory=dict)  # The effect when ability resolves (singular)
    targets: int = 0  # Number of targets required
    
    # ==========================================================
    # Type Checking
    # ==========================================================
    
    def is_mana_ability(self) -> bool:
        """Return True if this is a mana ability."""
        return self.ability_type == "MANA"
    
    def is_activated_ability(self) -> bool:
        """Return True if this is an activated ability."""
        return self.ability_type == "ACTIVATED"
    
    def is_triggered_ability(self) -> bool:
        """Return True if this is a triggered ability."""
        return self.ability_type == "TRIGGERED"
    
    # ==========================================================
    # Cost Checking
    # ==========================================================
    
    def requires_tap(self) -> bool:
        """Return True if this ability requires tapping as part of the cost."""
        return self.cost.get("tap", False)
    
    def requires_mana(self) -> bool:
        """Return True if this ability requires mana as part of the cost."""
        return "mana" in self.cost
    
    def get_mana_cost(self) -> Dict[str, int]:
        """Get the mana cost of this ability."""
        return self.cost.get("mana", {})
    
    # ==========================================================
    # String Representation
    # ==========================================================
    
    def __str__(self) -> str:
        """String representation of the ability."""
        if self.ability_type == "MANA":
            return f"{self.name} (Mana ability)"
        elif self.ability_type == "ACTIVATED":
            cost_str = ""
            if self.cost.get("tap", False):
                cost_str += "Tap, "
            if "mana" in self.cost:
                mana = self.cost["mana"]
                cost_str += ", ".join(f"{v}{k}" for k, v in mana.items())
            return f"{self.name}: {cost_str} -> {self.text}"
        else:
            return f"{self.name}: {self.text}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Ability(name={self.name}, type={self.ability_type}, cost={self.cost})"