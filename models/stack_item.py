# models/stack_item.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum


class StackItemType(str, Enum):
    """Types of items that can be on the stack."""
    SPELL = "SPELL"
    ABILITY = "ABILITY"
    TRIGGER_ABILITY = "TRIGGER_ABILITY"


class StackItemStatus(str, Enum):
    """Status of a stack item."""
    PENDING = "PENDING"      # Waiting to resolve
    RESOLVED = "RESOLVED"    # Successfully resolved
    FIZZLED = "FIZZLED"      # Failed to resolve (illegal targets)


@dataclass
class StackItem:
    """
    Represents one object on the stack.
    
    The stack is LIFO (Last In, First Out).
    The top item resolves first.
    
    MTGNP Requirements:
    - Each stack item has a unique ID (for STACK_PUSH/STACK_RESOLVE)
    - Item type determines how it behaves (SPELL, ABILITY, TRIGGER_ABILITY)
    - Targets must be validated before resolution
    """

    # ==========================================================
    # Identity
    # ==========================================================

    stack_item_id: str  # Unique ID for this stack item
    item_type: StackItemType  # SPELL, ABILITY, or TRIGGER_ABILITY

    # ==========================================================
    # Source
    # ==========================================================

    source: object  # The card or permanent that generated this
    source_id: str  # card_id of the source
    source_name: str  # name of the source

    # ==========================================================
    # Control
    # ==========================================================

    controller: str  # Player ID of the controller

    # ==========================================================
    # Targets
    # ==========================================================

    targets: List[str] = field(default_factory=list)  # Target IDs
    original_targets: List[str] = field(default_factory=list)  # For legality checking

    # ==========================================================
    # Effects
    # ==========================================================

    effects: List[Dict[str, Any]] = field(default_factory=list)

    # ==========================================================
    # Ability (if this is an ability)
    # ==========================================================

    ability: Optional[object] = None

    # ==========================================================
    # Status
    # ==========================================================

    status: StackItemStatus = StackItemStatus.PENDING

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def is_spell(self) -> bool:
        """Return True if this is a spell."""
        return self.item_type == StackItemType.SPELL

    @property
    def is_ability(self) -> bool:
        """Return True if this is an ability."""
        return self.item_type == StackItemType.ABILITY

    @property
    def is_triggered_ability(self) -> bool:
        """Return True if this is a triggered ability."""
        return self.item_type == StackItemType.TRIGGER_ABILITY

    @property
    def is_pending(self) -> bool:
        """Return True if this item is pending resolution."""
        return self.status == StackItemStatus.PENDING

    @property
    def is_resolved(self) -> bool:
        """Return True if this item has resolved."""
        return self.status == StackItemStatus.RESOLVED

    @property
    def is_fizzled(self) -> bool:
        """Return True if this item has fizzled."""
        return self.status == StackItemStatus.FIZZLED

    @property
    def has_targets(self) -> bool:
        """Return True if this item has targets."""
        return len(self.targets) > 0

    # ==========================================================
    # Methods
    # ==========================================================

    def validate_targets(self, valid_targets: List[str]) -> bool:
        """
        Validate that all targets are legal.
        
        Args:
            valid_targets: List of legal target IDs
            
        Returns:
            bool: True if all targets are legal
        """
        if not self.has_targets:
            return True
        return all(target in valid_targets for target in self.targets)

    def get_illegal_targets(self, valid_targets: List[str]) -> List[str]:
        """
        Get any illegal targets.
        
        Args:
            valid_targets: List of legal target IDs
            
        Returns:
            List[str]: List of illegal target IDs
        """
        if not self.has_targets:
            return []
        return [target for target in self.targets if target not in valid_targets]

    def mark_resolved(self) -> None:
        """Mark this stack item as resolved."""
        self.status = StackItemStatus.RESOLVED

    def mark_fizzled(self) -> None:
        """Mark this stack item as fizzled."""
        self.status = StackItemStatus.FIZZLED

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for STACK_PUSH PDU.
        
        Returns:
            Dict[str, Any]: PDU-ready dictionary
        """
        return {
            "stack_item_id": self.stack_item_id,
            "item_type": self.item_type.value,
            "source": self.source_id,
            "targets": self.targets,
            "controller": self.controller
        }

    def __str__(self) -> str:
        """String representation of the stack item."""
        status_str = self.status.value
        target_str = f" targeting {', '.join(self.targets)}" if self.targets else ""
        return f"{self.source_name} ({self.item_type.value}){target_str} [{status_str}]"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"StackItem(id={self.stack_item_id}, type={self.item_type.value}, "
                f"source={self.source_id}, targets={self.targets}, "
                f"status={self.status.value})")