def apply(game_state, creature, source=None):

    owner = game_state.get_player(creature.owner)

    if owner is None or creature not in owner.battlefield:
        return None

    owner.battlefield.remove(creature)
    creature.tapped = False
    owner.graveyard.append(creature)

    return {
        "change_type": "DESTROY",
        "target": _creature_ref(creature)
    }


def _creature_ref(creature):

    return getattr(creature, "id", creature.name)
