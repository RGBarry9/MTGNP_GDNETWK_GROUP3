"""increase player's life total by amount."""
def apply(player, amount, source=None):
    if amount <= 0:
        return None

    player.life += amount

    return {
        "change_type": "LIFE_GAIN",
        "target": player.player_id,
        "amount": amount
    }
