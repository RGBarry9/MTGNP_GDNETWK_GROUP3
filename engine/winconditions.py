# engine/winconditions.py
from typing import Optional, Literal
from models.player import Player
from config.enums import WinnerReason


class WinConditionManager:
    """
    Determines whether the game has ended.

    Win Conditions:
    - A player's life total reaches 0 or below
    - A player attempts to draw from an empty library
    - A player concedes
    - A player disconnects (handled elsewhere)

    This manager does not modify gameplay except for
    ending the game through GameState.
    """

    def __init__(self, game_state):
        self.game_state = game_state
        self.win_reason = None

    # ==================================================
    # Main Check
    # ==================================================

    def check(self) -> Optional[Player]:
        """
        Check every supported win condition.

        Returns:
            winner (Player) if someone has won,
            None otherwise.
        """
        if self.game_state.game_over:
            return self.game_state.winner

        # Check each player for loss
        for player in self.game_state.players:
            winner, reason = self._check_player_loss(player)

            if winner is not None:
                self.win_reason = reason
                self.game_state.end_game(winner)
                return winner

        return None

    # ==================================================
    # Individual Conditions
    # ==================================================

    def _check_player_loss(self, player: Player) -> tuple[Optional[Player], Optional[WinnerReason]]:
        """
        Returns (winning_opponent, reason) if the specified player has lost.
        """
        opponent = self.game_state.get_opponent(player)

        if not opponent:
            return None, None

        # ------------------------------------------
        # Life Total
        # ------------------------------------------
        if player.life <= 0:
            print(f"   💀 {player.player_id} lost (life: {player.life})")
            return opponent, WinnerReason.LIFE_ZERO

        # ------------------------------------------
        # Empty Library
        # ------------------------------------------
        if self._lost_by_empty_library(player):
            print(f"   💀 {player.player_id} lost (empty library)")
            return opponent, WinnerReason.DECK_EMPTY

        return None, None

    def check_player_dead(self, player: Player) -> bool:
        """
        Check if a specific player has lost.
        
        Returns:
            bool: True if the player has lost
        """
        winner, _ = self._check_player_loss(player)
        return winner is not None

    # ==================================================
    # Library
    # ==================================================

    def _lost_by_empty_library(self, player: Player) -> bool:
        """
        A player loses if they attempt to draw from an empty library.
        
        This is set when player.draw_card() returns None and
        player.failed_to_draw is set to True.
        """
        return getattr(player, "failed_to_draw", False)

    def check_library_empty(self, player: Player) -> bool:
        """
        Check if a player's library is empty.
        
        Returns:
            bool: True if library is empty
        """
        return len(player.library) == 0

    # ==================================================
    # Concede
    # ==================================================

    def concede(self, player: Player) -> Optional[Player]:
        """
        Handle a player conceding the game.
        
        Args:
            player: The player conceding
            
        Returns:
            Optional[Player]: The winner (opponent)
        """
        winner = self.game_state.get_opponent(player)

        if not winner:
            return None

        print(f"   🏳️ {player.player_id} concedes!")
        self.win_reason = WinnerReason.CONCEDE
        self.game_state.end_game(winner)

        return winner

    # ==================================================
    # Disconnect
    # ==================================================

    def disconnect(self, player: Player) -> Optional[Player]:
        """
        Handle a player disconnecting from the game.
        
        Args:
            player: The player who disconnected
            
        Returns:
            Optional[Player]: The winner (opponent)
        """
        winner = self.game_state.get_opponent(player)

        if not winner:
            return None

        print(f"   🔌 {player.player_id} disconnected!")
        self.win_reason = WinnerReason.DISCONNECT
        self.game_state.end_game(winner)

        return winner

    # ==================================================
    # Draw Conditions
    # ==================================================

    def check_draw(self) -> Optional[str]:
        """
        Check for a draw condition.
        
        In MTGNP v1.0, there are no draw conditions.
        This is a placeholder for future expansion.
        """
        # Currently no draw conditions in MTGNP v1.0
        return None

    # ==================================================
    # Information
    # ==================================================

    def game_over(self) -> bool:
        """Return True if the game is over."""
        return self.game_state.game_over

    def winner(self) -> Optional[Player]:
        """Return the winner of the game."""
        return self.game_state.winner

    def get_win_reason(self) -> Optional[WinnerReason]:
        """Return the reason the game ended."""
        return self.win_reason

    def get_win_reason_string(self) -> Optional[str]:
        """Return the win reason as a string."""
        if self.win_reason:
            return self.win_reason.value
        return None

    def get_summary(self) -> dict:
        """Get a summary of the win/loss state."""
        return {
            "game_over": self.game_state.game_over,
            "winner": self.game_state.winner.player_id if self.game_state.winner else None,
            "win_reason": self.win_reason.value if self.win_reason else None,
            "players": [
                {
                    "player_id": p.player_id,
                    "life": p.life,
                    "library_size": len(p.library),
                    "failed_to_draw": getattr(p, "failed_to_draw", False)
                }
                for p in self.game_state.players
            ]
        }

    def reset(self) -> None:
        """Reset the win condition manager for a new game."""
        self.win_reason = None

    def __str__(self) -> str:
        """String representation for debugging."""
        if not self.game_over:
            return "Game in progress"
        winner = self.game_state.winner
        winner_name = winner.player_id if winner else "None"
        reason = self.win_reason.value if self.win_reason else "Unknown"
        return f"Game Over - Winner: {winner_name} ({reason})"