import random


class Library:
    """
    Represents a player's library.
    """

    def __init__(self):
        self.cards = []

    def add(self, card):
        self.cards.append(card)

    def draw(self):
        if not self.cards:
            return None

        return self.cards.pop(0)

    def shuffle(self):
        random.shuffle(self.cards)

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