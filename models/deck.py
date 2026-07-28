# models/deck.py
import random
from typing import List, Optional
from models.card import Card


class Deck:
    """
    Represents a player's deck in MTGNP.
    
    A deck contains between 1 and 50 cards from the pre-defined card set.
    The server validates deck size and card legality during PLAYER_READY.
    
    MTGNP Requirements:
    - Minimum deck size: 1 card
    - Maximum deck size: 50 cards
    - All cards must exist in the card database
    """

    def __init__(self, cards: Optional[List[Card]] = None):
        """
        Initialize a deck with optional cards.
        
        Args:
            cards: Optional list of Card objects to populate the deck
        """
        self.cards = cards if cards is not None else []
        # Don't validate on init - allow empty deck building

    # ==========================================================
    # Card Operations
    # ==========================================================

    def add(self, card: Card) -> None:
        """Add a single card to the deck."""
        self.cards.append(card)

    def add_cards(self, cards: List[Card]) -> None:
        """Add multiple cards to the deck."""
        self.cards.extend(cards)

    def remove(self, card: Card) -> bool:
        """Remove a specific card from the deck."""
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def draw(self) -> Optional[Card]:
        """Draw the top card from the deck."""
        if not self.cards:
            return None
        return self.cards.pop(0)

    def draw_multiple(self, count: int) -> List[Card]:
        """Draw multiple cards from the deck."""
        drawn = []
        for _ in range(count):
            card = self.draw()
            if card is None:
                break
            drawn.append(card)
        return drawn

    def peek_top(self, count: int = 1) -> List[Card]:
        """Look at the top cards without removing them."""
        return self.cards[:count]

    def peek_bottom(self, count: int = 1) -> List[Card]:
        """Look at the bottom cards without removing them."""
        if count >= len(self.cards):
            return self.cards.copy()
        return self.cards[-count:]

    def shuffle(self) -> None:
        """Randomize the order of cards in the deck."""
        random.shuffle(self.cards)

    def clear(self) -> None:
        """Remove all cards from the deck."""
        self.cards.clear()

    # ==========================================================
    # Validation (MTGNP Requirements)
    # ==========================================================

    def validate(self) -> bool:
        """
        Validate the deck according to MTGNP requirements.
        
        MTGNP Requirements:
        - Deck must contain at least 1 card
        - Deck must contain at most 50 cards
        
        Returns:
            bool: True if valid, False otherwise
        """
        size = len(self.cards)
        return 1 <= size <= 50

    def get_validation_error(self) -> Optional[str]:
        """
        Get the validation error message if the deck is invalid.
        
        Returns:
            Optional[str]: Error message or None if valid
        """
        size = len(self.cards)
        if size < 1:
            return f"Deck must contain at least 1 card (currently {size})"
        if size > 50:
            return f"Deck must contain at most 50 cards (currently {size})"
        return None

    def is_valid(self) -> bool:
        """Check if the deck is valid."""
        return self.validate()

    def is_empty(self) -> bool:
        """Check if the deck is empty."""
        return len(self.cards) == 0

    def is_full(self) -> bool:
        """Check if the deck is at maximum size (50 cards)."""
        return len(self.cards) >= 50

    # ==========================================================
    # Card Counting
    # ==========================================================

    def size(self) -> int:
        """Return the number of cards in the deck."""
        return len(self.cards)

    def count_by_type(self, card_type: str) -> int:
        """Count how many cards of a specific type are in the deck."""
        return sum(1 for card in self.cards if card.card_type == card_type)

    def count_by_name(self, name: str) -> int:
        """Count how many cards with a specific name are in the deck."""
        return sum(1 for card in self.cards if card.name == name)

    def count_by_color(self, color: str) -> int:
        """Count how many cards of a specific color are in the deck."""
        return sum(1 for card in self.cards if color in card.colors)

    def get_card_ids(self) -> List[str]:
        """Get all card IDs in the deck (for PLAYER_READY protocol)."""
        return [card.card_id for card in self.cards]

    # ==========================================================
    # Deck Copying (for GAME_SETUP)
    # ==========================================================

    def clone(self) -> 'Deck':
        """
        Create a copy of the deck.
        
        Used when moving from deck to library during GAME_SETUP.
        """
        cloned_cards = [card.clone() for card in self.cards]
        return Deck(cloned_cards)

    def to_library(self) -> 'Deck':
        """
        Convert deck to a library (shuffled copy).
        
        During GAME_SETUP, the deck is shuffled and becomes the library.
        """
        library = self.clone()
        library.shuffle()
        return library

    # ==========================================================
    # Utility
    # ==========================================================

    def get_cards(self) -> List[Card]:
        """Return all cards in the deck."""
        return self.cards

    def __contains__(self, card: Card) -> bool:
        """Support 'card in deck' syntax."""
        return card in self.cards

    def __iter__(self):
        """Support iteration over deck."""
        return iter(self.cards)

    def __len__(self):
        """Support len(deck)."""
        return len(self.cards)

    def __repr__(self) -> str:
        """String representation of the deck."""
        return f"Deck({len(self.cards)} cards)"