# engine/validator.py
from typing import Tuple, Optional
from models.card import Card
from models.player import Player
from config.enums import Phase


class GameValidator:
    """
    Validates player actions according to the game rules.

    This class only determines whether an action is legal.
    It never modifies the game state.
    """

    def __init__(self, game_state):
        self.game_state = game_state

    # ==========================================================
    # General
    # ==========================================================

    def game_started(self) -> bool:
        """Check if the game has started."""
        return self.game_state.started

    def game_not_over(self) -> bool:
        """Check if the game is not over."""
        return not self.game_state.game_over

    def player_exists(self, player: Player) -> bool:
        """Check if a player exists in the game."""
        return player in self.game_state.players

    def is_active_player(self, player: Player) -> bool:
        """Check if the player is the active player."""
        return self.game_state.active_player == player

    def has_priority(self, player: Player) -> bool:
        """Check if the player has priority."""
        return self.game_state.priority_player == player

    def in_phase(self, phase: Phase) -> bool:
        """Check if the game is in a specific phase."""
        return self.game_state.current_phase == phase

    def in_main_phase(self) -> bool:
        """Check if the game is in a main phase."""
        return self.game_state.current_phase in [Phase.PRECOMBAT_MAIN, Phase.POSTCOMBAT_MAIN]

    # ==========================================================
    # Spell Casting
    # ==========================================================

    def can_cast_spell(self, player: Player, card: Card) -> Tuple[bool, str]:
        """
        Check if a player can cast a spell.
        
        Returns:
            Tuple[bool, str]: (is_valid, reason)
        """
        if not self.game_started():
            return False, "Game has not started."

        if not self.game_not_over():
            return False, "Game is already over."

        if not self.player_exists(player):
            return False, "Player is not in this game."

        if not self.has_priority(player):
            return False, "Player does not have priority."

        if card not in player.hand:
            return False, "Card is not in player's hand."

        # Check phase for sorceries
        if card.is_sorcery() and not self.in_main_phase():
            return False, f"Sorcery can only be cast in main phase, not {self.game_state.current_phase}"

        return True, ""

    def can_cast_instant(self, player: Player, card: Card) -> Tuple[bool, str]:
        """
        Check if a player can cast an instant.
        
        Instants can be cast anytime the player has priority.
        """
        return self.can_cast_spell(player, card)

    # ==========================================================
    # Land Plays
    # ==========================================================

    def can_play_land(self, player: Player, card: Card) -> Tuple[bool, str]:
        """
        Check if a player can play a land.
        """
        if not self.game_started():
            return False, "Game has not started."

        if not self.game_not_over():
            return False, "Game is already over."

        if not self.player_exists(player):
            return False, "Player is not in this game."

        if not self.has_priority(player):
            return False, "Player does not have priority."

        if not self.in_main_phase():
            return False, f"Lands can only be played in main phase, not {self.game_state.current_phase}"

        if card not in player.hand:
            return False, "Card is not in player's hand."

        if not card.is_land():
            return False, "Card is not a land."

        # Check if player already played a land this turn
        if player.lands_played >= 1:
            return False, "Player has already played a land this turn."

        return True, ""

    # ==========================================================
    # Target Validation
    # ==========================================================

    def valid_player_target(self, player_id: str) -> bool:
        """Check if a player ID is a valid target."""
        return self.game_state.get_player(player_id) is not None

    def valid_creature_target(self, creature_id: str) -> bool:
        """Check if a creature ID is a valid target."""
        for player in self.game_state.players:
            for creature in player.battlefield:
                if creature.card_id == creature_id:  # ← FIXED: Use card_id
                    return True
        return False

    def valid_target(self, target_id: str) -> bool:
        """
        Check if a target ID is valid (player or creature).
        """
        return self.valid_player_target(target_id) or self.valid_creature_target(target_id)

    def valid_spell_targets(self, card: Card, targets: list) -> Tuple[bool, str]:
        """
        Check if targets are valid for a spell.
        """
        if not targets:
            return True, ""

        # If spell requires targets, check each one
        for target in targets:
            if not self.valid_target(target):
                return False, f"Invalid target: {target}"

        return True, ""

    # ==========================================================
    # Combat
    # ==========================================================

    def can_attack(self, player: Player, creature: Card) -> Tuple[bool, str]:
        """
        Check if a creature can attack.
        """
        # Check phase
        if self.game_state.current_phase != Phase.DECLARE_ATTACKERS:
            return False, f"Not in Declare Attackers phase (current: {self.game_state.current_phase})"

        # Check if creature is on battlefield
        if creature not in player.battlefield:
            return False, "Creature is not on battlefield."

        # Check if it's a creature
        if not creature.is_creature():
            return False, "Only creatures can attack."

        # Check if tapped
        if creature.is_tapped():
            return False, "Tapped creatures cannot attack."

        # Check summoning sickness (unless it has Haste)
        if creature.summoning_sick and not creature.has_haste():
            return False, "Creature has summoning sickness and cannot attack."

        # Check Defender
        if creature.has_defender():
            return False, "Creatures with Defender cannot attack."

        return True, ""

    def can_block(self, player: Player, blocker: Card, attacker: Card) -> Tuple[bool, str]:
        """
        Check if a creature can block an attacker.
        """
        # Check phase
        if self.game_state.current_phase != Phase.DECLARE_BLOCKERS:
            return False, f"Not in Declare Blockers phase (current: {self.game_state.current_phase})"

        # Check if blocker is on battlefield
        if blocker not in player.battlefield:
            return False, "Blocker is not on battlefield."

        # Check if attacker exists
        if attacker is None:
            return False, "Invalid attacker."

        # Check if blocker is tapped
        if blocker.is_tapped():
            return False, "Tapped creatures cannot block."

        # Check if it's a creature
        if not blocker.is_creature():
            return False, "Only creatures can block."

        # Check if blocker has summoning sickness (doesn't matter for blocking)
        # In MTG, summoning sickness doesn't affect blocking

        return True, ""

    def can_assign_damage_order(self, player: Player, attacker: Card, blocker_order: list) -> Tuple[bool, str]:
        """
        Check if a player can assign damage order.
        """
        # Check phase
        if self.game_state.current_phase != Phase.ASSIGN_DAMAGE_ORDER:
            return False, f"Not in Assign Damage Order phase (current: {self.game_state.current_phase})"

        # Check if attacker exists
        if attacker not in self.game_state.attackers:
            return False, "Attacker not found."

        # Check if there are blockers for this attacker
        blockers = [b for b in self.game_state.blockers.values() if b]
        if len(blockers) <= 1:
            return False, "No multi-blocking to assign order for."

        return True, ""

    # ==========================================================
    # Stack
    # ==========================================================

    def stack_not_empty(self) -> bool:
        """Check if the stack is not empty."""
        return not self.game_state.stack_empty()

    def can_counter_spell(self, player: Player, target_stack_id: str) -> Tuple[bool, str]:
        """
        Check if a player can counter a spell.
        """
        if not self.has_priority(player):
            return False, "Player does not have priority."

        # Check if the target is on the stack
        target_item = None
        for item in self.game_state.stack:
            if hasattr(item, 'stack_item_id') and item.stack_item_id == target_stack_id:
                target_item = item
                break

        if not target_item:
            return False, f"Stack item {target_stack_id} not found."

        # Check if it's a spell (can only counter spells)
        if hasattr(target_item, 'is_spell') and not target_item.is_spell:
            return False, "Can only counter spells."

        return True, ""

    # ==========================================================
    # Miscellaneous
    # ==========================================================

    def valid_card(self, card) -> bool:
        """Check if an object is a valid Card."""
        return isinstance(card, Card)

    def valid_player(self, player) -> bool:
        """Check if an object is a valid Player."""
        return isinstance(player, Player)

    def can_activate_ability(self, player: Player, source: Card, ability_index: int) -> Tuple[bool, str]:
        """
        Check if a player can activate an ability.
        """
        if not self.has_priority(player):
            return False, "Player does not have priority."

        if source not in player.battlefield:
            return False, "Source is not on battlefield."

        if ability_index >= len(source.abilities):
            return False, "Ability not found."

        ability = source.abilities[ability_index]

        # Check tap cost
        if ability.requires_tap() and source.is_tapped():
            return False, "Source is already tapped."

        # Check summoning sickness for creatures with tap abilities
        if source.is_creature() and source.summoning_sick and ability.requires_tap():
            return False, "Source has summoning sickness and cannot tap."

        return True, ""