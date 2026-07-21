from dataclasses import dataclass, field


@dataclass
class Card:
    """
    Represents a single MTG card.
    """

    name: str

    card_type: str

    mana_cost: str

    text: str = ""

    power: int | None = None

    toughness: int | None = None

    tapped: bool = False

    owner: str = ""

    controller: str = ""

    keywords: list[str] = field(default_factory=list)