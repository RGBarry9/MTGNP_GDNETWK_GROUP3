from dataclasses import dataclass, field


@dataclass
class Ability:
    """
    Represents a card ability.
    """

    name: str

    ability_type: str

    cost: str = ""

    text: str = ""

    effects: list = field(default_factory=list)

    targets: int = 0