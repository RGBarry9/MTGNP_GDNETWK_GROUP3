import random


class Deck:

    def __init__(self):

        self.cards = []

    def add_card(self, card):

        self.cards.append(card)

    def shuffle(self):

        random.shuffle(self.cards)

    def draw(self):

        if not self.cards:
            return None

        return self.cards.pop(0)

    def size(self):

        return len(self.cards)