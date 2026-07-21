import json

from game.card import Card


class CardLoader:

    @staticmethod
    def load(filename):

        with open(filename, "r", encoding="utf-8") as file:

            data = json.load(file)

        cards = {}

        for item in data:

            card = Card(

                name=item["name"],

                card_type=item["card_type"],

                mana_cost=item.get("mana_cost", ""),

                text=item.get("text", ""),

                power=item.get("power"),

                toughness=item.get("toughness"),

                keywords=item.get("keywords", [])
            )

            cards[card.name] = card

        return cards