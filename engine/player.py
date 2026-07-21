from dataclasses import dataclass, field


@dataclass
class Player:
    """
    Represents one player in the game.
    """

    player_id: str

    ready: bool = False

    life: int = 20

    deck: list = field(default_factory=list)

    hand: list = field(default_factory=list)

    battlefield: list = field(default_factory=list)

    graveyard: list = field(default_factory=list)