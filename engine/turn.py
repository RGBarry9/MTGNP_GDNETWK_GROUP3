class TurnManager:
    """
    Controls turn progression.

    Responsibilities:
    - Starting a turn
    - Ending a turn
    - Advancing phases
    - Switching the active player
    """

    PHASES = [
        "UNTAP",
        "UPKEEP",
        "DRAW",
        "PRECOMBAT_MAIN",
        "BEGIN_COMBAT",
        "DECLARE_ATTACKERS",
        "DECLARE_BLOCKERS",
        "COMBAT_DAMAGE",
        "END_COMBAT",
        "POSTCOMBAT_MAIN",
        "END_STEP",
        "CLEANUP"
    ]

    def __init__(self, game_state):
        self.game_state = game_state

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

        # Begin with the Untap step
        self.game_state.set_phase("UNTAP")

        self.untap_step(player)
        self.upkeep_step(player)
        self.draw_step(player)

        # Enter first main phase
        self.game_state.set_phase("PRECOMBAT_MAIN")

    def end_turn(self):
        """
        Finish the current turn.
        """

        self.cleanup_step()

        self.switch_active_player()

        # Advance to the next turn only after the player changes
        self.game_state.next_turn()

    # ======================================================
    # Individual Steps
    # ======================================================

    def untap_step(self, player):
        """
        Untap every permanent controlled by the player.
        """

        for permanent in player.battlefield:

            if hasattr(permanent, "tapped"):
                permanent.tapped = False

    def upkeep_step(self, player):
        """
        Handle upkeep triggers.

        Triggered abilities will be added later.
        """
        pass

    def draw_step(self, player):
        """
        Draw one card from the player's library.
        """

        card = player.library.draw()

        if card is not None:
            player.hand.add(card)

    def cleanup_step(self):
        """
        Cleanup the battlefield after the turn ends.
        """

        self.game_state.clear_combat()

    # ======================================================
    # Phase Control
    # ======================================================

    def next_phase(self):
        """
        Advance to the next phase.
        """

        current = self.game_state.current_phase

        if current not in self.PHASES:

            self.game_state.set_phase(self.PHASES[0])

            return

        index = self.PHASES.index(current)

        if index == len(self.PHASES) - 1:

            self.end_turn()

            return

        self.game_state.set_phase(self.PHASES[index + 1])

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

    # ======================================================
    # Information
    # ======================================================

    def current_player(self):

        return self.game_state.active_player

    def current_phase(self):

        return self.game_state.current_phase

    def turn_number(self):

        return self.game_state.turn_number