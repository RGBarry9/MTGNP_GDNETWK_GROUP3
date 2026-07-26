
def apply(player, amount=1, source=None):
    if amount <= 0:
        return None

    drawn = []
    empty_library = False

    for _ in range(amount):

        card = _draw_one(player.deck)

        if card is None:
            empty_library = True
            break

        drawn.append(card)

    player.hand.extend(drawn)

    return {
        "change_type": "DRAW",
        "target": player.player_id,
        "amount": len(drawn),
        "empty_library": empty_library
    }


def _draw_one(deck):
    """pop the top card from deck, whether it's a deck instance or a
    plain list. returns none if the library is empty."""

    if hasattr(deck, "draw"):
        return deck.draw()

    if not deck:
        return None

    return deck.pop(0)
