from dataclasses import dataclass, field

from models.ability import Ability


@dataclass
class Card:
    """
    Base representation of a Magic card.

    This class only stores card state.
    Game rules are implemented by the engine.
    """

    # ==================================================
    # Identity
    # ==================================================

    id: str

    name: str

    card_type: str

    # ==================================================
    # Card Information
    # ==================================================

    mana_cost: str = ""

    text: str = ""

    # ==================================================
    # Creature Statistics
    # ==================================================

    power: int | None = None

    toughness: int | None = None

    damage_marked: int = 0

    # ==================================================
    # State
    # ==================================================

    tapped: bool = False

    owner: str = ""

    controller: str = ""

    # ==================================================
    # Abilities
    # ==================================================

    keywords: list[str] = field(default_factory=list)

    abilities: list[Ability] = field(default_factory=list)

    # ==================================================
    # Tapping
    # ==================================================

    def tap(self):
        """
        Tap this permanent.
        """

        self.tapped = True

    def untap(self):
        """
        Untap this permanent.
        """

        self.tapped = False

    def is_tapped(self) -> bool:
        """
        Return True if the permanent is tapped.
        """

        return self.tapped

    # ==================================================
    # Combat Damage
    # ==================================================

    def mark_damage(self, amount: int):
        """
        Mark combat or spell damage on this creature.
        """

        if self.toughness is None:
            return

        if amount <= 0:
            return

        self.damage_marked += amount

    def heal_damage(self):
        """
        Remove all marked damage.

        This happens during the cleanup step.
        """

        self.damage_marked = 0

    def is_destroyed(self) -> bool:
        """
        Return True if lethal damage has been marked.
        """

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

    # ==================================================
    # Keywords
    # ==================================================

    def has_keyword(self, keyword: str) -> bool:
        """
        Return True if the card has the specified keyword.
        """

        return keyword in self.keywords

    # ==================================================
    # Abilities
    # ==================================================

    def add_ability(self, ability: Ability):
        """
        Add an ability to the card.
        """

        self.abilities.append(ability)

    def remove_ability(self, ability: Ability):
        """
        Remove an ability from the card.
        """

        if ability in self.abilities:
            self.abilities.remove(ability)

    # ==================================================
    # Utility
    # ==================================================

    def reset(self):
        """
        Reset temporary state.

        Called during the cleanup phase.
        """

        self.damage_marked = 0
        self.tapped = False