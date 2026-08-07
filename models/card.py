from dataclasses import dataclass, field
from typing import (
    List,
    Optional,
    Dict,
    Any
)

from models.ability import Ability


@dataclass(init=False)
class Card:

    card_id: str
    name: str
    card_type: str

    mana_cost: str = ""
    text: str = ""

    colors: List[str] = field(
        default_factory=list
    )

    power: int | None = None
    toughness: int | None = None

    damage_marked: int = 0

    tapped: bool = False

    owner: str = ""
    controller: str = ""

    summoning_sick: bool = False

    keywords: List[str] = field(
        default_factory=list
    )

    abilities: List[Ability] = field(
        default_factory=list
    )

    trigger: Optional[
        Dict[str, Any]
    ] = None

    effects: List[
        Dict[str, Any]
    ] = field(
        default_factory=list
    )

    def __init__(
        self,
        card_id=None,
        name="",
        card_type="",
        mana_cost="",
        text="",
        colors=None,
        power=None,
        toughness=None,
        damage_marked=0,
        tapped=False,
        owner="",
        controller="",
        summoning_sick=False,
        keywords=None,
        abilities=None,
        trigger=None,
        effects=None,
        id=None
    ):

        if card_id is None:
            card_id = id

        if card_id is None:
            raise TypeError(
                "Card requires card_id or id"
            )

        self.card_id = card_id
        self.name = name
        self.card_type = card_type
        self.mana_cost = mana_cost
        self.text = text
        self.colors = (
            list(colors)
            if colors
            else []
        )

        self.power = power
        self.toughness = toughness

        self.damage_marked = (
            damage_marked
        )

        self.tapped = tapped

        self.owner = owner
        self.controller = controller

        self.summoning_sick = (
            summoning_sick
        )

        self.keywords = (
            list(keywords)
            if keywords
            else []
        )

        self.abilities = (
            list(abilities)
            if abilities
            else []
        )

        self.trigger = (
            trigger.copy()
            if trigger
            else None
        )

        self.effects = [
            effect.copy()
            for effect in effects
        ] if effects else []

    def tap(self):
        self.tapped = True

    def untap(self):
        self.tapped = False

    def is_tapped(self):
        return self.tapped

    def mark_damage(self, amount: int):

        if self.toughness is None:
            return

        if amount <= 0:
            return

        self.damage_marked += amount

    def heal_damage(self):
        self.damage_marked = 0

    def is_destroyed(self):

        if self.toughness is None:
            return False

        return (
            self.damage_marked
            >= self.toughness
        )

    def is_creature(self):
        return "Creature" in self.card_type

    def is_land(self):
        return "Land" in self.card_type

    def is_instant(self):
        return "Instant" in self.card_type

    def is_sorcery(self):
        return "Sorcery" in self.card_type

    def is_artifact(self):
        return "Artifact" in self.card_type

    def is_enchantment(self):
        return "Enchantment" in self.card_type

    def is_planeswalker(self):
        return "Planeswalker" in self.card_type

    def is_spell(self):
        return (
            self.is_instant()
            or self.is_sorcery()
        )

    def is_permanent(self):
        return not self.is_spell()

    def has_keyword(self, keyword):
        return keyword in self.keywords

    def has_haste(self):
        return self.has_keyword("Haste")

    def has_defender(self):
        return self.has_keyword("Defender")

    def has_first_strike(self):
        return self.has_keyword("First Strike")

    def has_double_strike(self):
        return self.has_keyword("Double Strike")

    def has_trample(self):
        return self.has_keyword("Trample")

    def has_flying(self):
        return self.has_keyword("Flying")

    def has_reach(self):
        return self.has_keyword("Reach")

    def has_lifelink(self):
        return self.has_keyword("Lifelink")

    def add_ability(self, ability):
        self.abilities.append(ability)

    def remove_ability(self, ability):

        if ability in self.abilities:
            self.abilities.remove(
                ability
            )

    def get_mana_abilities(self):
        return [
            ability
            for ability in self.abilities
            if ability.ability_type == "MANA"
        ]

    def get_activated_abilities(self):
        return [
            ability
            for ability in self.abilities
            if ability.ability_type == "ACTIVATED"
        ]

    def get_triggered_abilities(self):
        return [
            ability
            for ability in self.abilities
            if ability.ability_type == "TRIGGERED"
        ]

    def clone(self):

        return Card(
            card_id=self.card_id,
            name=self.name,
            card_type=self.card_type,
            mana_cost=self.mana_cost,
            text=self.text,
            colors=(
                self.colors.copy()
                if self.colors
                else []
            ),
            power=self.power,
            toughness=self.toughness,
            damage_marked=0,
            tapped=False,
            owner=self.owner,
            controller=self.controller,
            summoning_sick=True,
            keywords=(
                self.keywords.copy()
                if self.keywords
                else []
            ),
            abilities=(
                self.abilities.copy()
                if self.abilities
                else []
            ),
            trigger=(
                self.trigger.copy()
                if self.trigger
                else None
            ),
            effects=[
                effect.copy()
                for effect in self.effects
            ]
            if self.effects
            else []
        )

    def reset(self):

        self.damage_marked = 0
        self.tapped = False
        self.summoning_sick = False

    def __str__(self):

        if self.is_creature():
            return (
                f"{self.name} "
                f"({self.power}/{self.toughness})"
            )

        return self.name

    def __repr__(self):

        return (
            f"Card("
            f"id={self.card_id}, "
            f"name={self.name}, "
            f"type={self.card_type}"
            f")"
        )