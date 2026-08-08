# models/deck.py
import random
from typing import List, Optional
from models.card import Card


class Deck:
    """
    Represents a player's deck in MTGNP.
    
    A deck contains between 1 and 50 cards from the pre-defined card set.
    The server validates deck size and card legality during PLAYER_READY.
    
    Responsibilities:
    - Store cards in order
    - Shuffle the deck
    - Draw cards from the top
    - Validate deck size
    - Count cards by type
    - Clone deck for library creation
    """

    def __init__(self, cards: Optional[List[Card]] = None):
        """
        Initialize a deck with optional cards.
        
        Args:
            cards: Optional list of Card objects to populate the deck
        """
        self.cards = cards if cards is not None else []
        self._validate()

    # ==========================================================
    # Core Operations
    # ==========================================================

    def add_card(self, card: Card) -> None:
        """
        Add a card to the bottom of the deck.
        
        Args:
            card: The Card object to add
        """
        self.cards.append(card)
        self._validate()

    def add_cards(self, cards: List[Card]) -> None:
        """
        Add multiple cards to the deck.
        
        Args:
            cards: List of Card objects to add
        """
        self.cards.extend(cards)
        self._validate()

    def remove_card(self, card: Card) -> bool:
        """
        Remove a specific card from the deck.
        
        Args:
            card: The Card object to remove
            
        Returns:
            bool: True if card was found and removed, False otherwise
        """
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def shuffle(self) -> None:
        """
        Randomize the order of cards in the deck.
        
        This is called during GAME_SETUP and after mulligans.
        """
        random.shuffle(self.cards)

    def draw(self) -> Optional[Card]:
        """
        Draw the top card from the deck.
        
        Returns:
            Optional[Card]: The drawn card, or None if the deck is empty
            
        Note:
            Drawing from an empty library causes the player to lose
            (checked by WinConditionManager).
        """
        if not self.cards:
            return None
        return self.cards.pop(0)

    def draw_multiple(self, count: int) -> List[Card]:
        """
        Draw multiple cards from the deck.
        
        Args:
            count: Number of cards to draw
            
        Returns:
            List[Card]: The drawn cards (may be fewer than requested if deck is empty)
        """
        drawn = []
        for _ in range(count):
            card = self.draw()
            if card is None:
                break
            drawn.append(card)
        return drawn

    def peek_top(self, count: int = 1) -> List[Card]:
        """
        Look at the top cards without removing them.
        
        Args:
            count: Number of cards to peek at
            
        Returns:
            List[Card]: The top cards
        """
        return self.cards[:count]

    def peek_bottom(self, count: int = 1) -> List[Card]:
        """
        Look at the bottom cards without removing them.
        
        Args:
            count: Number of cards to peek at
            
        Returns:
            List[Card]: The bottom cards
        """
        if count >= len(self.cards):
            return self.cards.copy()
        return self.cards[-count:]

    # ==========================================================
    # Deck Building & Validation
    # ==========================================================

    def _validate(self) -> None:
        """
        Validate the deck. Raises ValueError if invalid.
        
        MTGNP Requirements:
        - Deck must contain at least 1 card
        - Deck must contain at most 50 cards
        - All cards must have a valid card_id
        """
        size = len(self.cards)
        if size < 1:
            raise ValueError(f"Deck must contain at least 1 card (currently {size})")
        if size > 50:
            raise ValueError(f"Deck must contain at most 50 cards (currently {size})")
        
        # Validate each card
        for card in self.cards:
            if not card.card_id:
                raise ValueError(f"Card missing card_id: {card}")

    def is_valid(self) -> bool:
        """
        Check if the deck is valid without raising exceptions.
        
        Returns:
            bool: True if deck meets MTGNP requirements
        """
        try:
            self._validate()
            return True
        except ValueError:
            return False

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
        """
        Count how many cards of a specific type are in the deck.
        
        Args:
            card_type: The card type to count (e.g., "Creature", "Land")
            
        Returns:
            int: Number of cards with the specified type
        """
        return sum(1 for card in self.cards if card.card_type == card_type)

    def count_by_name(self, name: str) -> int:
        """
        Count how many cards with a specific name are in the deck.
        
        Args:
            name: The card name to count
            
        Returns:
            int: Number of cards with the specified name
        """
        return sum(1 for card in self.cards if card.name == name)

    def count_by_color(self, color: str) -> int:
        """
        Count how many cards of a specific color are in the deck.
        
        Args:
            color: The color to count (e.g., "R", "G", "B", "U", "W")
            
        Returns:
            int: Number of cards with the specified color
        """
        return sum(1 for card in self.cards if color in card.colors)

    def get_card_ids(self) -> List[str]:
        """
        Get all card IDs in the deck.
        
        Returns:
            List[str]: List of card_id strings
        """
        return [card.card_id for card in self.cards]

    # ==========================================================
    # Deck Copying
    # ==========================================================

    def clone(self) -> 'Deck':
        """
        Create a copy of the deck.
        
        Returns:
            Deck: A new Deck with the same cards in the same order
            
        Note:
            Used when moving from deck to library during GAME_SETUP.
        """
        cloned_cards = [card.clone() for card in self.cards]
        return Deck(cloned_cards)

    def to_library(self) -> 'Deck':
        """
        Convert deck to a library (shuffled copy).
        
        Returns:
            Deck: A shuffled copy of the deck
            
        Note:
            During GAME_SETUP, the deck is shuffled and becomes the library.
        """
        library = self.clone()
        library.shuffle()
        return library

    # ==========================================================
    # Utility Methods
    # ==========================================================

    def clear(self) -> None:
        """Remove all cards from the deck."""
        self.cards.clear()

    def __len__(self) -> int:
        """Return the number of cards in the deck."""
        return len(self.cards)

    def __iter__(self):
        """Iterate over cards in the deck."""
        return iter(self.cards)

    def __contains__(self, card: Card) -> bool:
        """Check if a card is in the deck."""
        return card in self.cards

    def __repr__(self) -> str:
        """String representation of the deck."""
        return f"Deck({len(self.cards)} cards)"