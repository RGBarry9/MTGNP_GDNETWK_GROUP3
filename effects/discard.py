"""
Discard effect.

Moves one or more cards from a player's hand to their graveyard.
"""


def apply(player, card_ids, source=None):
    """
    Discard the specified cards from the player's hand.

    Parameters
    ----------
    player : Player
        The player discarding cards.

    card_ids : list
        List of card IDs (or names) to discard.

    source : object, optional
        The source of the discard effect.

    Returns
    -------
    list | None
        A list of state change dictionaries, or None if no cards
        were discarded.
    """

    state_changes = []

    for card_id in card_ids:

        card = _find_card(player.hand, card_id)

        if card is None:
            continue

        player.hand.remove(card)
        player.graveyard.add(card)

        state_changes.append({
            "type": "DISCARD",
            "player": player.player_id,
            "card": getattr(card, "id", card.name),
            "source": source,
        })

    if not state_changes:
        return None

    return state_changes


def _find_card(hand, card_id):
    """
    Find a card in a player's hand by ID or name.
    """

    for card in hand.cards:

        reference = getattr(card, "id", card.name)

        if reference == card_id:
            return card

    return None