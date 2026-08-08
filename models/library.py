# models/library.py
import random
from typing import List, Optional
from models.card import Card


class Library:
    """
    Represents a player's library.
    
    The library is the player's deck during gameplay.
    Cards are drawn from the top (index 0).
    If the library is empty and a player needs to draw, they lose.
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        """Add a card to the bottom of the library."""
        self.cards.append(card)

    def add_cards(self, cards):
        """Add multiple cards to the bottom of the library."""
        self.cards.extend(cards)

    def add_to_top(self, card):
        """Add a card to the top of the library."""
        self.cards.insert(0, card)

    def draw(self):
        """
        Draw the top card from the library.
        
        Returns:
            Optional[Card]: The drawn card, or None if library is empty.
            
        Note:
            Drawing from an empty library causes the player to lose
            (checked by WinConditionManager).
        """
        if not self.cards:
            return None
        return self.cards.pop(0)

    def draw_multiple(self, count: int) -> List[Card]:
        """Draw multiple cards from the library."""
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

    def shuffle(self):
        """Randomize the order of cards in the library."""
        random.shuffle(self.cards)

    def clear(self):
        """Remove all cards from the library."""
        self.cards.clear()

    def size(self):
        """Return the number of cards in the library."""
        return len(self.cards)

    def get_cards(self):
        """Return all cards in the library."""
        return self.cards

    def get_card_ids(self):
        """Return all card IDs in the library."""
        return [card.card_id for card in self.cards]

    def is_empty(self) -> bool:
        """Check if the library is empty."""
        return len(self.cards) == 0

    def count(self) -> int:
        """Return the number of cards in the library."""
        return len(self.cards)

    def __contains__(self, card):
        """Support 'card in library' syntax."""
        return card in self.cards

    def __iter__(self):
        """Support iteration over library."""
        return iter(self.cards)

    def __len__(self):
        """Support len(library)."""
        return len(self.cards)

    def __repr__(self) -> str:
        """String representation of the library."""
        return f"Library({len(self.cards)} cards)"