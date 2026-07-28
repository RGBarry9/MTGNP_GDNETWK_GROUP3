# models/graveyard.py
class Graveyard:
    """
    Represents a player's graveyard.
    
    The graveyard contains cards that have been destroyed, discarded,
    or otherwise put into the graveyard from play.
    Cards in the graveyard are ordered (most recent last).
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        """Add a card to the graveyard."""
        self.cards.append(card)

    def add_cards(self, cards):
        """Add multiple cards to the graveyard."""
        self.cards.extend(cards)

    def remove(self, card):
        """Remove a card from the graveyard."""
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def remove_by_id(self, card_id: str):
        """Remove a card from the graveyard by its ID."""
        for card in self.cards:
            if card.card_id == card_id:
                self.cards.remove(card)
                return card
        return None

    def clear(self):
        """Remove all cards from the graveyard."""
        self.cards.clear()

    def size(self):
        """Return the number of cards in the graveyard."""
        return len(self.cards)

    def get_cards(self):
        """Return all cards in the graveyard."""
        return self.cards

    def get_card_ids(self):
        """Return all card IDs in the graveyard."""
        return [card.card_id for card in self.cards]

    def get_latest(self, count: int = 1):
        """Get the most recently added cards."""
        if count >= len(self.cards):
            return self.cards.copy()
        return self.cards[-count:]

    def get_earliest(self, count: int = 1):
        """Get the oldest cards."""
        if count >= len(self.cards):
            return self.cards.copy()
        return self.cards[:count]

    def contains(self, card) -> bool:
        """Check if a specific card is in the graveyard."""
        return card in self.cards

    def contains_id(self, card_id: str) -> bool:
        """Check if a card with the given ID is in the graveyard."""
        return any(card.card_id == card_id for card in self.cards)

    def count(self) -> int:
        """Return the number of cards in the graveyard."""
        return len(self.cards)

    def is_empty(self) -> bool:
        """Check if the graveyard is empty."""
        return len(self.cards) == 0

    def __contains__(self, card):
        """Support 'card in graveyard' syntax."""
        return card in self.cards

    def __iter__(self):
        """Support iteration over graveyard."""
        return iter(self.cards)

    def __len__(self):
        """Support len(graveyard)."""
        return len(self.cards)

    def __repr__(self) -> str:
        """String representation of the graveyard."""
        card_names = [card.name for card in self.cards]
        return f"Graveyard({len(self.cards)} cards: {card_names})"