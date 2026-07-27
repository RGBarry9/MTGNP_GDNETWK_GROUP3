class Hand:
    """
    Represents a player's hand.
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def remove(self, card):
        if card in self.cards:
            self.cards.remove(card)

    def clear(self):
        self.cards.clear()

    def size(self):
        return len(self.cards)

    def get_cards(self):
        return self.cards

    def __iter__(self):
        return iter(self.cards)

    def __len__(self):
        return len(self.cards)