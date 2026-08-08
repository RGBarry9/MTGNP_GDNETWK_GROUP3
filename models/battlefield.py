# models/battlefield.py
class Battlefield:
    """
    Represents the permanents a player controls.
    
    The battlefield contains all creatures, lands, artifacts,
    enchantments, and planeswalkers that are currently in play.
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        """Add a card to the battlefield."""
        self.cards.append(card)

    def remove(self, card):
        """Remove a card from the battlefield."""
        if card in self.cards:
            self.cards.remove(card)

    def clear(self):
        """Remove all cards from the battlefield."""
        self.cards.clear()

    def size(self):
        """Return the number of cards on the battlefield."""
        return len(self.cards)

    def get_cards(self):
        """Return all cards on the battlefield."""
        return self.cards

    def get_creatures(self):
        """Return all creatures on the battlefield."""
        return [card for card in self.cards if card.is_creature()]

    def get_lands(self):
        """Return all lands on the battlefield."""
        return [card for card in self.cards if card.is_land()]

    def get_untapped_creatures(self):
        """Return all untapped creatures."""
        return [card for card in self.cards if card.is_creature() and not card.is_tapped()]

    def get_tapped_creatures(self):
        """Return all tapped creatures."""
        return [card for card in self.cards if card.is_creature() and card.is_tapped()]

    def get_creatures_without_summoning_sickness(self):
        """Return all creatures that can attack (no summoning sickness)."""
        return [card for card in self.cards 
                if card.is_creature() and not card.summoning_sick and not card.is_tapped()]

    def contains(self, card) -> bool:
        """Check if a specific card is on the battlefield."""
        return card in self.cards

    def count(self) -> int:
        """Return the number of cards on the battlefield."""
        return len(self.cards)

    def count_creatures(self) -> int:
        """Return the number of creatures on the battlefield."""
        return len(self.get_creatures())

    def __contains__(self, card):
        """Support 'card in battlefield' syntax."""
        return card in self.cards

    def __iter__(self):
        """Support iteration over battlefield."""
        return iter(self.cards)

    def __len__(self):
        """Support len(battlefield)."""
        return len(self.cards)