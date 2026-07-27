from dataclasses import dataclass, field

from models.deck import Deck
from models.hand import Hand
from models.library import Library
from models.battlefield import Battlefield
from models.graveyard import Graveyard


@dataclass
class Player:
    """
    Represents a player in a MTGNP game.
    This class stores player state only.
    """

    # --------------------------------------------------
    # Player Identity
    # --------------------------------------------------

    player_id: str

    username: str = ""

    connected: bool = True

    ready: bool = False

    # --------------------------------------------------
    # Game Status
    # --------------------------------------------------

    life: int = 20

    lands_played: int = 0

    passed_priority: bool = False

    lost: bool = False

    # --------------------------------------------------
    # Mana
    # --------------------------------------------------

    mana_pool: dict = field(default_factory=lambda: {
        "W": 0,
        "U": 0,
        "B": 0,
        "R": 0,
        "G": 0,
        "C": 0
    })

    # --------------------------------------------------
    # Card Zones
    # --------------------------------------------------

    deck: Deck = field(default_factory=Deck)

    library: Library = field(default_factory=Library)

    hand: Hand = field(default_factory=Hand)

    battlefield: Battlefield = field(default_factory=Battlefield)

    graveyard: Graveyard = field(default_factory=Graveyard)

    # --------------------------------------------------
    # Utility Methods
    # --------------------------------------------------

    def reset_priority(self):
        """
        Reset the player's priority status.
        """
        self.passed_priority = False

    def pass_priority(self):
        """
        Mark that the player has passed priority.
        """
        self.passed_priority = True

    def reset_turn(self):
        """
        Reset turn-specific values.
        """
        self.lands_played = 0
        self.passed_priority = False

    def lose_game(self):
        """
        Mark this player as having lost the game.
        """
        self.lost = True