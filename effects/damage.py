def apply(target, amount, source=None):

    if amount <= 0:
        return None

    if hasattr(target, "life"):
        return _damage_player(target, amount)

    return _damage_creature(target, amount)


def _damage_player(player, amount):

    player.life -= amount

    return {
        "change_type": "DAMAGE",
        "target": player.player_id,
        "amount": amount
    }


def _damage_creature(creature, amount):

    if not hasattr(creature, "damage"):
        creature.damage = 0

    creature.damage += amount

    return {
        "change_type": "DAMAGE",
        "target": _creature_ref(creature),
        "amount": amount
    }


def _creature_ref(creature):

    return getattr(creature, "id", creature.name)
