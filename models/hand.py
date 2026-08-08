# models/hand.py
class Hand:
    """
    Represents a player's hand.
    
    The hand contains cards that the player has drawn but not yet played.
    MTGNP rules: Maximum hand size is 7 cards (enforced during Cleanup step).
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        """Add a card to the hand."""
        self.cards.append(card)

    def add_cards(self, cards):
        """Add multiple cards to the hand."""
        self.cards.extend(cards)

    def remove(self, card):
        """Remove a card from the hand."""
        if card in self.cards:
            self.cards.remove(card)
            return True
        return False

    def remove_by_id(self, card_id: str):
        """Remove a card from the hand by its ID."""
        for card in self.cards:
            if card.card_id == card_id:
                self.cards.remove(card)
                return card
        return None

    def clear(self):
        """Remove all cards from the hand."""
        self.cards.clear()

    def size(self):
        """Return the number of cards in the hand."""
        return len(self.cards)

    def get_cards(self):
        """Return all cards in the hand."""
        return self.cards

    def get_card_ids(self):
        """Return all card IDs in the hand."""
        return [card.card_id for card in self.cards]

    def contains(self, card) -> bool:
        """Check if a specific card is in the hand."""
        return card in self.cards

    def contains_id(self, card_id: str) -> bool:
        """Check if a card with the given ID is in the hand."""
        return any(card.card_id == card_id for card in self.cards)

    def count(self) -> int:
        """Return the number of cards in the hand."""
        return len(self.cards)

    def is_empty(self) -> bool:
        """Check if the hand is empty."""
        return len(self.cards) == 0

    def is_full(self) -> bool:
        """Check if the hand is full (7 cards)."""
        return len(self.cards) >= 7

    def __contains__(self, card):
        """Support 'card in hand' syntax."""
        return card in self.cards

    def __iter__(self):
        """Support iteration over hand."""
        return iter(self.cards)

    def __len__(self):
        """Support len(hand)."""
        return len(self.cards)

    def __repr__(self) -> str:
        """String representation of the hand."""
        card_names = [card.name for card in self.cards]
        return f"Hand({len(self.cards)} cards: {card_names})"