# engine/combat.py
from typing import List, Optional, Dict, Any
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

    def declare_attackers(self, attacking_player: Player, attackers: List[Card]) -> List[Card]:
        """
        Declare the attacking creatures.
        
        Returns:
            List[Card]: List of successfully declared attackers
        """
        self.game_state.attackers.clear()
        declared_attackers = []

        for creature in attackers:
            # Check if it's a creature
            if not creature.is_creature():
                continue

            # Check if on battlefield
            if creature not in attacking_player.battlefield:
                continue

            # Check if tapped
            if creature.is_tapped():
                continue

            # Check summoning sickness (unless has Haste)
            if creature.summoning_sick and not creature.has_haste():
                continue

            # Check Defender
            if creature.has_defender():
                continue

            # Declare as attacker
            creature.tap()
            self.game_state.attackers.append(creature)
            declared_attackers.append(creature)

        return declared_attackers

    def get_attackers(self) -> List[Card]:
        """Return the current attackers."""
        return self.game_state.attackers

    def has_attackers(self) -> bool:
        """Return True if there are attackers declared."""
        return len(self.game_state.attackers) > 0

    # ==================================================
    # Blockers
    # ==================================================

    def declare_blocker(self,
                        defending_player: Player,
                        blocker: Card,
                        attacker: Card) -> bool:
        """
        Assign one blocker to one attacker.
        
        Returns:
            bool: True if blocker was assigned successfully
        """
        # Check if blocker is on battlefield
        if blocker not in defending_player.battlefield:
            return False

        # Check if blocker is tapped
        if blocker.is_tapped():
            return False

        # Check if attacker is declared
        if attacker not in self.game_state.attackers:
            return False

        # Check if blocker is a creature
        if not blocker.is_creature():
            return False

        # Use attacker.card_id as key (hashable)
        self.game_state.blockers[attacker.card_id] = blocker

        return True

    def declare_blockers(self, defending_player: Player, blockers: List[Dict]) -> List[Dict]:
        """
        Declare multiple blockers.
        
        Args:
            defending_player: The defending player
            blockers: List of dicts with 'blocker' and 'attacker'
            
        Returns:
            List[Dict]: List of successful declarations
        """
        successful = []
        for block in blockers:
            blocker = block.get('blocker')
            attacker = block.get('attacker')
            if self.declare_blocker(defending_player, blocker, attacker):
                successful.append(block)
        return successful

    def get_blockers(self) -> Dict[str, Card]:
        """Return the current blockers (attacker_id -> blocker)."""
        return self.game_state.blockers

    def has_blockers(self) -> bool:
        """Return True if there are blockers declared."""
        return len(self.game_state.blockers) > 0

    # ==================================================
    # Combat Damage
    # ==================================================

    def resolve_combat(self) -> Dict[str, Any]:
        """
        Resolve combat damage.
        
        Returns:
            Dict: Damage events and results
        """
        defending_player = self.game_state.get_opponent(
            self.game_state.active_player
        )

        if not defending_player:
            return {"damage_events": [], "creatures_died": []}

        damage_events = []

        # Resolve every attacker
        for attacker in self.game_state.attackers:
            # Get blocker using attacker.card_id
            blocker = self.game_state.blockers.get(attacker.card_id)

            # Unblocked attacker
            if blocker is None:
                damage_amount = attacker.power or 0
                if damage_amount > 0:
                    defending_player.life -= damage_amount
                    damage_events.append({
                        "source": attacker.name,
                        "source_id": attacker.card_id,
                        "target": defending_player.player_id,
                        "amount": damage_amount,
                        "blocked": False
                    })
                continue

            # Blocked - simultaneous damage
            attacker_damage = attacker.power or 0
            blocker_damage = blocker.power or 0

            # Assign damage order if multiple blockers
            # For now, just deal damage simultaneously
            if attacker_damage > 0:
                blocker.mark_damage(attacker_damage)
                damage_events.append({
                    "source": attacker.name,
                    "source_id": attacker.card_id,
                    "target": blocker.name,
                    "target_id": blocker.card_id,
                    "amount": attacker_damage,
                    "blocked": True
                })

            if blocker_damage > 0:
                attacker.mark_damage(blocker_damage)
                damage_events.append({
                    "source": blocker.name,
                    "source_id": blocker.card_id,
                    "target": attacker.name,
                    "target_id": attacker.card_id,
                    "amount": blocker_damage,
                    "blocked": True
                })

        # Destroy creatures with lethal damage
        creatures_died = self._destroy_dead_creatures()

        return {
            "damage_events": damage_events,
            "creatures_died": creatures_died
        }

    def resolve_combat_with_order(self, damage_order: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Resolve combat damage with custom damage order.
        
        Args:
            damage_order: Dict mapping attacker_id to list of blocker_ids in order
            
        Returns:
            Dict: Damage events and results
        """
        # Apply damage order to blockers
        # This handles multi-blocking scenarios
        # For each attacker, assign damage to blockers in order
        # After a blocker dies, assign remaining damage to next blocker
        
        # For MTGNP v1.0, simplified implementation
        return self.resolve_combat()

    def get_blocker_order_for_attacker(self, attacker_id: str) -> List[str]:
        """
        Get the blocker order for a specific attacker.
        
        Returns:
            List[str]: Blocker IDs in order, or empty list if not assigned
        """
        return self.game_state.damage_assignments.get(attacker_id, [])

    # ==================================================
    # Destroy Creatures
    # ==================================================

    def _destroy_dead_creatures(self) -> List[str]:
        """
        Destroy creatures with lethal damage.
        
        Returns:
            List[str]: IDs of destroyed creatures
        """
        destroyed = []

        for player in self.game_state.players:
            dead_creatures = []

            for creature in player.battlefield:
                if creature.is_destroyed():
                    dead_creatures.append(creature)

            for creature in dead_creatures:
                player.battlefield.remove(creature)
                player.graveyard.add(creature)
                destroyed.append(creature.card_id)
                print(f"   💀 {creature.name} destroyed")

        return destroyed

    # ==================================================
    # First Strike
    # ==================================================

    def resolve_first_strike(self) -> Dict[str, Any]:
        """
        Resolve first strike damage step.
        
        Only creatures with first strike or double strike deal damage.
        """
        first_strike_attackers = []
        first_strike_blockers = []

        # Find creatures with first strike or double strike
        for attacker in self.game_state.attackers:
            if attacker.has_first_strike() or attacker.has_double_strike():
                first_strike_attackers.append(attacker)

        for blocker in self.game_state.blockers.values():
            if blocker.has_first_strike() or blocker.has_double_strike():
                first_strike_blockers.append(blocker)

        # If no first strike creatures, skip
        if not first_strike_attackers and not first_strike_blockers:
            return {"damage_events": [], "creatures_died": []}

        print(f"   ⚔️ First Strike damage")

        # Process first strike damage
        # Similar to normal combat but only for first strike creatures
        # For simplicity, we'll treat it as normal combat with filtering

        # In a full implementation, you'd process damage for first strike creatures only
        # and then check for state-based actions before regular combat damage

        return self.resolve_combat()

    # ==================================================
    # Cleanup
    # ==================================================

    def cleanup(self) -> None:
        """
        Remove combat damage and clear combat state.
        """
        for player in self.game_state.players:
            for creature in player.battlefield:
                creature.heal_damage()

        self.game_state.clear_combat()
        print("   🧹 Combat state cleaned up")

    # ==================================================
    # Information
    # ==================================================

    def attacker_count(self) -> int:
        """Return the number of attackers."""
        return len(self.game_state.attackers)

    def blocker_count(self) -> int:
        """Return the number of blockers."""
        return len(self.game_state.blockers)

    def combat_active(self) -> bool:
        """Return True if combat is active."""
        return self.attacker_count() > 0

    def get_combat_summary(self) -> Dict[str, Any]:
        """Get a summary of the current combat state."""
        attackers = [{
            "name": a.name,
            "card_id": a.card_id,
            "power": a.power,
            "toughness": a.toughness
        } for a in self.game_state.attackers]

        blockers = {}
        for att_id, blocker in self.game_state.blockers.items():
            blockers[att_id] = {
                "name": blocker.name,
                "card_id": blocker.card_id,
                "power": blocker.power,
                "toughness": blocker.toughness
            }

        return {
            "attackers": attackers,
            "blockers": blockers,
            "attackers_count": len(attackers),
            "blockers_count": len(blockers)
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        if not self.combat_active():
            return "No combat"
        return f"Combat({len(self.game_state.attackers)} attackers, {len(self.game_state.blockers)} blockers)"