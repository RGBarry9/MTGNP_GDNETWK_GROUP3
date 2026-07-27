from models.card import Card
from models.player import Player


class CombatManager:
    """
    Handles the combat phase.

    Responsibilities:
    - Declare attackers
    - Declare blockers
    - Resolve combat damage
    - Destroy creatures with lethal damage
    - Cleanup combat state
    """

    def __init__(self, game_state):

        self.game_state = game_state

    # ==================================================
    # Attackers
    # ==================================================

    def declare_attackers(self, attacking_player: Player, attackers: list[Card]):
        """
        Declare the attacking creatures.
        """

        self.game_state.attackers.clear()

        for creature in attackers:

            if not creature.is_creature():
                continue

            if creature.is_tapped():
                continue

            if creature not in attacking_player.battlefield:
                continue

            creature.tap()

            self.game_state.attackers.append(creature)

    # ==================================================
    # Blockers
    # ==================================================

    def declare_blocker(self,
                        defending_player: Player,
                        blocker: Card,
                        attacker: Card):
        """
        Assign one blocker to one attacker.
        """

        if blocker not in defending_player.battlefield:
            return False

        if blocker.is_tapped():
            return False

        if attacker not in self.game_state.attackers:
            return False

        self.game_state.blockers[attacker] = blocker

        return True

    # ==================================================
    # Combat Damage
    # ==================================================

    def resolve_combat(self):
        """
        Resolve combat damage.
        """

        defending_player = self.game_state.get_opponent(
            self.game_state.active_player
        )

        # ------------------------------------------
        # Resolve every attacker
        # ------------------------------------------

        for attacker in self.game_state.attackers:

            blocker = self.game_state.blockers.get(attacker)

            # --------------------------------------
            # Unblocked attacker
            # --------------------------------------

            if blocker is None:

                defending_player.life -= attacker.power

                continue

            # --------------------------------------
            # Simultaneous damage
            # --------------------------------------

            blocker.mark_damage(attacker.power)

            attacker.mark_damage(blocker.power)

        self._destroy_dead_creatures()

    # ==================================================
    # Destroy Creatures
    # ==================================================

    def _destroy_dead_creatures(self):
        """
        Destroy creatures with lethal damage.
        """

        for player in self.game_state.players:

            destroyed = []

            for creature in player.battlefield:

                if creature.is_destroyed():

                    destroyed.append(creature)

            for creature in destroyed:

                player.battlefield.remove(creature)

                player.graveyard.add(creature)

    # ==================================================
    # Cleanup
    # ==================================================

    def cleanup(self):
        """
        Remove combat damage and clear combat state.
        """

        for player in self.game_state.players:

            for creature in player.battlefield:

                creature.heal_damage()

        self.game_state.clear_combat()

    # ==================================================
    # Information
    # ==================================================

    def attacker_count(self):

        return len(self.game_state.attackers)

    def blocker_count(self):

        return len(self.game_state.blockers)

    def combat_active(self):

        return self.attacker_count() > 0