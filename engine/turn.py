# engine/turn.py
from config.enums import Phase
from models.player import Player


class TurnManager:
    """
    Controls turn progression.

    Responsibilities:
    - Starting a turn
    - Ending a turn
    - Advancing phases
    - Switching the active player
    - Managing priority windows
    """

    # Full turn order with all phases and steps
    PHASES = [
        Phase.UNTAP,
        Phase.UPKEEP,
        Phase.DRAW,
        Phase.PRECOMBAT_MAIN,
        Phase.BEGIN_COMBAT,
        Phase.DECLARE_ATTACKERS,
        Phase.DECLARE_BLOCKERS,
        Phase.ASSIGN_DAMAGE_ORDER,
        Phase.FIRST_STRIKE_DAMAGE,
        Phase.COMBAT_DAMAGE,
        Phase.END_OF_COMBAT,
        Phase.POSTCOMBAT_MAIN,
        Phase.END_STEP,
        Phase.CLEANUP
    ]

    # Phases/steps that have priority windows
    PRIORITY_PHASES = [
        Phase.UPKEEP,
        Phase.DRAW,
        Phase.PRECOMBAT_MAIN,
        Phase.BEGIN_COMBAT,
        Phase.DECLARE_ATTACKERS,
        Phase.DECLARE_BLOCKERS,
        Phase.ASSIGN_DAMAGE_ORDER,
        Phase.FIRST_STRIKE_DAMAGE,
        Phase.COMBAT_DAMAGE,
        Phase.END_OF_COMBAT,
        Phase.POSTCOMBAT_MAIN,
        Phase.END_STEP
    ]

    def __init__(self, game_state):
        self.game_state = game_state
        self.is_first_turn = True
        self.first_player = None

    # ======================================================
    # Turn Control
    # ======================================================

    def start_turn(self):
        """
        Begin the current player's turn.
        """
        player = self.game_state.active_player

        if player is None:
            raise RuntimeError("No active player has been assigned.")

        # Reset turn-specific player values
        player.reset_turn()
        self.game_state.reset_land_played()

        # Check if this is the first turn
        if self.is_first_turn:
            self.first_player = player
            self.is_first_turn = False

        print(f"\n=== Turn {self.game_state.turn_number} - {player.player_id}'s turn ===")

        # Begin with the Untap step (no priority)
        self._advance_to_phase(Phase.UNTAP)
        self.untap_step(player)
        
        # Automatically advance to Upkeep (no priority in Untap)
        self._advance_to_phase(Phase.UPKEEP)
        self.upkeep_step(player)
        
        # Upkeep has priority - handled by caller

    def end_turn(self):
        """
        Finish the current turn.
        """
        print(f"=== End of Turn {self.game_state.turn_number} ===")
        
        # Cleanup step
        self.cleanup_step()

        # Switch active player
        self.switch_active_player()

        # Advance turn counter
        self.game_state.next_turn()

    # ======================================================
    # Individual Steps
    # ======================================================

    def untap_step(self, player: Player):
        """
        Untap every permanent controlled by the player.
        No priority window.
        """
        print(f"   🔄 Untap step for {player.player_id}")
        
        for permanent in player.battlefield:
            if hasattr(permanent, "tapped"):
                permanent.tapped = False

    def upkeep_step(self, player: Player):
        """
        Handle upkeep triggers.
        Priority window opens after triggers.
        """
        print(f"   ⏰ Upkeep step for {player.player_id}")
        
        # Check for upkeep triggers
        # In a full implementation, check permanents with "At the beginning of upkeep" triggers
        
        # Priority window opens here (handled by caller)

    def draw_step(self, player: Player):
        """
        Draw one card from the player's library.
        Priority window opens after draw.
        """
        # First player does not draw on their first turn
        if self.is_first_turn and player == self.first_player:
            print(f"   📄 {player.player_id} skips draw (first player)")
            return
        
        card = player.library.draw()
        
        if card is not None:
            player.hand.add(card)
            print(f"   📄 {player.player_id} draws {card.name}")
        else:
            print(f"   ❌ {player.player_id} library is empty!")
            # Player loses - handled by win condition check
        
        # Priority window opens here (handled by caller)

    def cleanup_step(self):
        """
        Cleanup the battlefield after the turn ends.
        """
        print(f"   🧹 Cleanup step")
        
        active_player = self.game_state.active_player
        
        # Discard down to 7 cards if hand size > 7
        if len(active_player.hand) > 7:
            cards_to_discard = len(active_player.hand) - 7
            print(f"   🗑️ {active_player.player_id} must discard {cards_to_discard} cards")
            # In a real implementation, this would ask the player to choose cards
        
        # Heal damage from all creatures
        for player in self.game_state.players:
            for creature in player.battlefield:
                creature.heal_damage()
                # Clear summoning sickness (creatures that entered this turn)
                creature.summoning_sick = False
        
        # Clear combat state
        self.game_state.clear_combat()

    # ======================================================
    # Combat Steps
    # ======================================================

    def begin_combat_step(self, player: Player):
        """
        Beginning of Combat step.
        Priority window opens.
        """
        print(f"   ⚔️ Beginning of Combat for {player.player_id}")
        # Priority window opens here (handled by caller)

    def declare_attackers_step(self, player: Player):
        """
        Declare Attackers step.
        Priority window opens after declaration.
        """
        print(f"   ⚔️ Declare Attackers for {player.player_id}")
        # This step is handled by the combat handler
        # The handler will call combat_manager.declare_attackers()

    def declare_blockers_step(self, player: Player):
        """
        Declare Blockers step.
        Priority window opens after declaration.
        """
        print(f"   ⚔️ Declare Blockers for {player.player_id}")
        # This step is handled by the combat handler

    def assign_damage_order_step(self, player: Player):
        """
        Assign Damage Order step.
        Priority window opens.
        """
        print(f"   ⚔️ Assign Damage Order for {player.player_id}")
        # Only if multiple blockers on one attacker

    def combat_damage_step(self, player: Player):
        """
        Combat Damage step.
        Priority window opens after damage.
        """
        print(f"   ⚔️ Combat Damage for {player.player_id}")
        # Resolved by combat_manager

    def end_of_combat_step(self, player: Player):
        """
        End of Combat step.
        Priority window opens.
        """
        print(f"   ⚔️ End of Combat for {player.player_id}")

    # ======================================================
    # Phase Control
    # ======================================================

    def next_phase(self) -> Phase:
        """
        Advance to the next phase.
        Returns the new phase.
        """
        current = self.game_state.current_phase

        if current not in self.PHASES:
            self.game_state.set_phase(self.PHASES[0])
            return self.PHASES[0]

        index = self.PHASES.index(current)

        if index == len(self.PHASES) - 1:
            self.end_turn()
            return self.PHASES[0]  # Return to start after end turn

        new_phase = self.PHASES[index + 1]
        self.game_state.set_phase(new_phase)
        print(f"   ⏭️ Phase transition: {current} -> {new_phase}")
        
        return new_phase

    def _advance_to_phase(self, phase: Phase):
        """
        Advance to a specific phase (for automatic transitions).
        """
        self.game_state.set_phase(phase)

    def has_priority_window(self) -> bool:
        """
        Check if the current phase has a priority window.
        """
        return self.game_state.current_phase in self.PRIORITY_PHASES

    def is_first_turn_draw(self, player: Player) -> bool:
        """
        Check if this is the first player's first turn draw.
        """
        return self.is_first_turn and player == self.first_player

    # ======================================================
    # Player Control
    # ======================================================

    def switch_active_player(self):
        """
        Pass the turn to the opponent.
        """
        players = self.game_state.players

        if len(players) != 2:
            return

        current = self.game_state.active_player

        if current == players[0]:
            self.game_state.set_active_player(players[1])
        else:
            self.game_state.set_active_player(players[0])
        
        print(f"   🔄 Active player switched to {self.game_state.active_player.player_id}")

    # ======================================================
    # Information
    # ======================================================

    def current_player(self) -> Player:
        """Return the current active player."""
        return self.game_state.active_player

    def current_phase(self) -> Phase:
        """Return the current phase."""
        return self.game_state.current_phase

    def turn_number(self) -> int:
        """Return the current turn number."""
        return self.game_state.turn_number

    def is_phase(self, phase: Phase) -> bool:
        """Check if the current phase matches the given phase."""
        return self.game_state.current_phase == phase

    def reset_for_new_game(self):
        """Reset turn manager for a new game."""
        self.is_first_turn = True
        self.first_player = None