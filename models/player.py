from dataclasses import dataclass, field

from models.deck import Deck
from models.library import Library
from models.hand import Hand
from models.battlefield import Battlefield
from models.graveyard import Graveyard


@dataclass
class Player:
    """
    Represents a player in the game.

    This class stores player state and provides helper methods for
    common game actions. Rule enforcement is handled by the engine.
    """

    # --------------------------------------------------
    # Identity
    # --------------------------------------------------

    player_id: str

    name: str

    # --------------------------------------------------
    # Resources
    # --------------------------------------------------

    life: int = 20

    mana_pool: dict = field(default_factory=dict)

    lands_played: int = 0

    ready: bool = False

    passed_priority: bool = False

    # --------------------------------------------------
    # Zones
    # --------------------------------------------------

    deck: Deck = field(default_factory=Deck)

    library: Library = field(default_factory=Library)

    hand: Hand = field(default_factory=Hand)

    battlefield: Battlefield = field(default_factory=Battlefield)

    graveyard: Graveyard = field(default_factory=Graveyard)

    # ==================================================
    # Turn Helpers
    # ==================================================

    def reset_turn(self):
        """
        Reset values that only last for one turn.
        """

        self.lands_played = 0
        self.passed_priority = False
        self.mana_pool.clear()

    # ==================================================
    # Life
    # ==================================================

    def gain_life(self, amount: int):
        """
        Increase the player's life total.
        """

        if amount > 0:
            self.life += amount

    def lose_life(self, amount: int):
        """
        Reduce the player's life total.
        """

        if amount > 0:
            self.life -= amount

    def is_dead(self) -> bool:
        """
        Returns True if the player has lost due to life.
        """

        return self.life <= 0

    # ==================================================
    # Card Movement
    # ==================================================

    def draw_card(self):
        """
        Draw one card from the library into the hand.

        Returns the drawn card or None if the library is empty.
        """

        card = self.library.draw()

        if card is not None:
            self.hand.add(card)

        return card

    def discard_card(self, card):
        """
        Move a card from the hand to the graveyard.
        """

        if self.hand.remove(card):
            self.graveyard.add(card)
            return True

        return False

    def play_card(self, card):
        """
        Move a card from the hand onto the battlefield.
        """

        if self.hand.remove(card):
            self.battlefield.add(card)
            return True

        return False

    def destroy_permanent(self, card):
        """
        Move a permanent from the battlefield to the graveyard.
        """

        if self.battlefield.remove(card):
            self.graveyard.add(card)
            return True

        return False

    # ==================================================
    # Priority
    # ==================================================

    def pass_priority(self):
        """
        Mark this player as having passed priority.
        """

        self.passed_priority = True

    def receive_priority(self):
        """
        Give priority back to this player.
        """

        self.passed_priority = False

    # ==================================================
    # Mana
    # ==================================================

    def add_mana(self, colour: str, amount: int = 1):
        """
        Add mana to the player's mana pool.
        """

        if amount <= 0:
            return

        self.mana_pool[colour] = (
            self.mana_pool.get(colour, 0) + amount
        )

    def spend_mana(self, colour: str, amount: int = 1):
        """
        Spend mana from the player's mana pool.

        Returns True if successful.
        """

        if self.mana_pool.get(colour, 0) < amount:
            return False

        self.mana_pool[colour] -= amount

        if self.mana_pool[colour] == 0:
            del self.mana_pool[colour]

        return True

    # ==================================================
    # Ready State
    # ==================================================

    def set_ready(self):
        """
        Mark the player as ready.
        """

        self.ready = True

    def set_not_ready(self):
        """
        Mark the player as not ready.
        """

        self.ready = False


    #additional helpers
    def get_hand_size(self) -> int:
        """Return the number of cards in hand."""
        return len(self.hand)

    def get_library_size(self) -> int:
        """Return the number of cards in library."""
        return len(self.library)

    def get_battlefield_size(self) -> int:
        """Return the number of permanents on battlefield."""
        return len(self.battlefield)

    def get_graveyard_size(self) -> int:
        """Return the number of cards in graveyard."""
        return len(self.graveyard)

    def get_creatures(self):
        """Return all creatures on the battlefield."""
        return self.battlefield.get_creatures()

    def get_untapped_creatures(self):
        """Return all untapped creatures on the battlefield."""
        return self.battlefield.get_untapped_creatures()

    def get_attackers(self):
        """Return all creatures that can attack (no summoning sickness, untapped)."""
        return self.battlefield.get_creatures_without_summoning_sickness()

    def can_play_land(self) -> bool:
        """Check if the player can play a land this turn."""
        return self.lands_played < 1

    def get_mana_pool_summary(self) -> str:
        """Get a string summary of the mana pool."""
        if not self.mana_pool:
            return "Empty"
        return ", ".join(f"{k}: {v}" for k, v in self.mana_pool.items())

    def to_dict(self) -> dict:
        """Convert player to dictionary for GAME_STATE_UPDATE."""
        return {
            "player_id": self.player_id,
            "name": self.name,
            "life": self.life,
            "mana_pool": self.mana_pool,
            "lands_played": self.lands_played,
            "ready": self.ready,
            "hand_count": len(self.hand),
            "library_count": len(self.library),
            "battlefield_count": len(self.battlefield),
            "graveyard_count": len(self.graveyard)
        }