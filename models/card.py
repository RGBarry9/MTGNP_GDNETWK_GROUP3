# models/card.py
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from models.ability import Ability


@dataclass
class Card:
    """
    Base representation of a Magic card.

    This class only stores card state.
    Game rules are implemented by the engine.
    The constructor.
    """

    # Identity
    card_id: str  # MTGNP uses card_id for deck lists
    name: str
    card_type: str

    # Card Information
    mana_cost: str = ""
    text: str = ""
    colors: List[str] = field(default_factory=list)  # Required for MTGNP

    # Creature Statistics
    power: int | None = None
    toughness: int | None = None
    damage_marked: int = 0

    # State
    tapped: bool = False
    owner: str = ""
    controller: str = ""
    summoning_sick: bool = False  # Required for combat rules

    # Abilities & Effects
    keywords: List[str] = field(default_factory=list)
    abilities: List[Ability] = field(default_factory=list)
    trigger: Optional[Dict[str, Any]] = None  # For triggered abilities
    effects: List[Dict[str, Any]] = field(default_factory=list)  # For spell effects


    # Tapping
    def tap(self):
        """Tap this permanent."""
        self.tapped = True

    def untap(self):
        """Untap this permanent."""
        self.tapped = False

    def is_tapped(self) -> bool:
        """Return True if the permanent is tapped."""
        return self.tapped

    # ==================================================
    # Combat Damage
    # ==================================================

    def mark_damage(self, amount: int):
        """Mark combat or spell damage on this creature."""
        if self.toughness is None:
            return
        if amount <= 0:
            return
        self.damage_marked += amount

    def heal_damage(self):
        """Remove all marked damage. Called during cleanup step."""
        self.damage_marked = 0

    def is_destroyed(self) -> bool:
        """Return True if lethal damage has been marked."""
        if self.toughness is None:
            return False
        return self.damage_marked >= self.toughness

    # ==================================================
    # Card Type Helpers
    # ==================================================

    def is_creature(self) -> bool:
        return "Creature" in self.card_type

    def is_land(self) -> bool:
        return "Land" in self.card_type

    def is_instant(self) -> bool:
        return "Instant" in self.card_type

    def is_sorcery(self) -> bool:
        return "Sorcery" in self.card_type

    def is_artifact(self) -> bool:
        return "Artifact" in self.card_type

    def is_enchantment(self) -> bool:
        return "Enchantment" in self.card_type

    def is_planeswalker(self) -> bool:
        return "Planeswalker" in self.card_type

    def is_spell(self) -> bool:
        """Return True if this is a spell (Instant or Sorcery)."""
        return self.is_instant() or self.is_sorcery()

    def is_permanent(self) -> bool:
        """Return True if this is a permanent card type."""
        return not self.is_spell()

    # ==================================================
    # Keywords
    # ==================================================

    def has_keyword(self, keyword: str) -> bool:
        """Return True if the card has the specified keyword."""
        return keyword in self.keywords

    def has_haste(self) -> bool:
        """Return True if the card has Haste."""
        return self.has_keyword("Haste")

    def has_defender(self) -> bool:
        """Return True if the card has Defender."""
        return self.has_keyword("Defender")

    def has_first_strike(self) -> bool:
        """Return True if the card has First Strike."""
        return self.has_keyword("First Strike")

    def has_double_strike(self) -> bool:
        """Return True if the card has Double Strike."""
        return self.has_keyword("Double Strike")

    def has_trample(self) -> bool:
        """Return True if the card has Trample."""
        return self.has_keyword("Trample")

    def has_flying(self) -> bool:
        """Return True if the card has Flying."""
        return self.has_keyword("Flying")

    def has_reach(self) -> bool:
        """Return True if the card has Reach."""
        return self.has_keyword("Reach")

    def has_lifelink(self) -> bool:
        """Return True if the card has Lifelink."""
        return self.has_keyword("Lifelink")

    # ==================================================
    # Abilities
    # ==================================================

    def add_ability(self, ability: Ability):
        """Add an ability to the card."""
        self.abilities.append(ability)

    def remove_ability(self, ability: Ability):
        """Remove an ability from the card."""
        if ability in self.abilities:
            self.abilities.remove(ability)

    def get_mana_abilities(self) -> List[Ability]:
        """Get all mana abilities on this card."""
        return [a for a in self.abilities if a.ability_type == "MANA"]

    def get_activated_abilities(self) -> List[Ability]:
        """Get all activated abilities on this card."""
        return [a for a in self.abilities if a.ability_type == "ACTIVATED"]

    def get_triggered_abilities(self) -> List[Ability]:
        """Get all triggered abilities on this card."""
        return [a for a in self.abilities if a.ability_type == "TRIGGERED"]

    # ==================================================
    # Utility
    # ==================================================

    def clone(self) -> 'Card':
        """
        Create a copy of this card.
        
        Used when moving from deck to library during GAME_SETUP.
        """
        return Card(
            card_id=self.card_id,
            name=self.name,
            card_type=self.card_type,
            mana_cost=self.mana_cost,
            text=self.text,
            colors=self.colors.copy() if self.colors else [],
            power=self.power,
            toughness=self.toughness,
            damage_marked=0,  # Reset damage on clone
            tapped=False,     # Reset tapped state
            owner=self.owner,
            controller=self.controller,
            summoning_sick=True,  # New clone has summoning sickness
            keywords=self.keywords.copy() if self.keywords else [],
            abilities=self.abilities.copy() if self.abilities else [],
            trigger=self.trigger.copy() if self.trigger else None,
            effects=[e.copy() for e in self.effects] if self.effects else []
        )

    def reset(self):
        """
        Reset temporary state.
        Called during the cleanup phase.
        """
        self.damage_marked = 0
        self.tapped = False
        self.summoning_sick = False

    def __str__(self) -> str:
        """String representation of the card."""
        if self.is_creature():
            return f"{self.name} ({self.power}/{self.toughness})"
        return self.name

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Card(id={self.card_id}, name={self.name}, type={self.card_type})"