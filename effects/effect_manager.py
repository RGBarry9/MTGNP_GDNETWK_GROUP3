from effects import damage
from effects import destroy
from effects import counter
from effects import draw
from effects import gain_life
from effects import discard


class EffectManager:
    def __init__(self, game_state):
        self.game_state = game_state

    def apply(self, effect_spec, source=None):
        """
        Apply a single effect spec. Returns a state_change dict, a
        list of state_change dicts, or None if the effect had no
        effect
        """

        effect_type = effect_spec.get("effect_type")

        handler = self._handlers().get(effect_type)

        if handler is None:
            raise ValueError(f"Unknown effect_type '{effect_type}'.")

        return handler(effect_spec, source)

    def apply_all(self, effect_specs, source=None):
        """
        Apply a list of effect specs in order, skipping any that
        produced no change, and return the combined state_changes
        list in the order they were applied. Handlers that return a
        list (e.g. DISCARD) are flattened into the result.
        """

        state_changes = []

        for effect_spec in effect_specs:

            result = self.apply(effect_spec, source)

            if result is None:
                continue

            if isinstance(result, list):
                state_changes.extend(result)
            else:
                state_changes.append(result)

        return state_changes
      
    # Individual effect handlers
    def _handlers(self):

        return {
            "DAMAGE": self._damage,
            "DESTROY": self._destroy,
            "COUNTER": self._counter,
            "GAIN_LIFE": self._gain_life,
            "DRAW": self._draw,
            "DISCARD": self._discard,
        }

    def _damage(self, effect_spec, source):

        target = self._resolve_target(effect_spec.get("target"))

        if target is None:
            return None

        return damage.apply(target, effect_spec.get("amount", 0), source)

    def _destroy(self, effect_spec, source):

        creature = self._resolve_creature(effect_spec.get("target"))

        if creature is None:
            return None

        return destroy.apply(self.game_state, creature, source)

    def _counter(self, effect_spec, source):

        stack = getattr(self.game_state, "stack", None)

        if stack is None:
            return None

        return counter.apply(stack, effect_spec.get("target"), source)

    def _gain_life(self, effect_spec, source):

        player = self.game_state.get_player(effect_spec.get("target"))

        if player is None:
            return None

        return gain_life.apply(player, effect_spec.get("amount", 0), source)

    def _draw(self, effect_spec, source):

        player = self.game_state.get_player(effect_spec.get("target"))

        if player is None:
            return None

        return draw.apply(player, effect_spec.get("amount", 1), source)

    def _discard(self, effect_spec, source):

        player = self.game_state.get_player(effect_spec.get("target"))

        if player is None:
            return None

        return discard.apply(
            player, effect_spec.get("card_ids", []), source
        )

    # Target resolution
    def _resolve_target(self, target_id):
        player = self.game_state.get_player(target_id)

        if player is not None:
            return player

        return self._resolve_creature(target_id)

    def _resolve_creature(self, target_id):
        for player in self.game_state.players:

            for permanent in player.battlefield:

                permanent_ref = getattr(permanent, "id", permanent.name)

                if permanent_ref == target_id:
                    return permanent

        return None
