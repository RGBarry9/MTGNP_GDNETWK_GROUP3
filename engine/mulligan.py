# engine/mulligan.py
import random
from typing import List, Optional
from models.player import Player
from models.card import Card


class MulliganManager:
    """
    Handles the London Mulligan procedure.

    London Mulligan Rules:
    - Each player draws 7 cards
    - Player may mulligan (shuffle hand back, draw 7 new cards)
    - After each mulligan, player must bottom 1 card for each mulligan taken
    - No minimum hand size limit
    """

    STARTING_HAND_SIZE = 7

    def __init__(self, game_state):
        self.game_state = game_state
        self.finished_players = set()
        self.mulligan_count = {}

    # ======================================================
    # Mulligan Setup
    # ======================================================

    def start(self) -> None:
        """
        Begin the mulligan process for all players.
        """
        self.finished_players.clear()
        self.mulligan_count.clear()

        for player in self.game_state.players:
            self.mulligan_count[player.player_id] = 0
            self.draw_starting_hand(player)

        print(f"🃏 Mulligan phase started for {len(self.game_state.players)} players")

    # ======================================================
    # Draw Opening Hand
    # ======================================================

    def draw_starting_hand(self, player: Player) -> None:
        """
        Draw the starting hand of 7 cards for a player.
        """
        player.hand.clear()
        
        print(f"   📄 {player.player_id} drawing from library with {len(player.library)} cards")
        
        for _ in range(self.STARTING_HAND_SIZE):
            card = player.library.draw()
            if card is None:
                print(f"   ⚠️ {player.player_id} library empty after {_} cards")
                break
            player.hand.add(card)
        
        print(f"   📄 {player.player_id} drew {len(player.hand)} cards")

    # ======================================================
    # Keep Current Hand
    # ======================================================

    def keep(self, player: Player, cards_to_bottom: Optional[List[str]] = None) -> bool:
        """
        Player keeps their current hand.
        
        If the player has mulliganed, they must bottom cards.
        
        Args:
            player: The player keeping their hand
            cards_to_bottom: List of card IDs to put on bottom
            
        Returns:
            bool: True if successful
        """
        if player.player_id in self.finished_players:
            print(f"   ⚠️ {player.player_id} already finished mulligan")
            return False

        mulligans = self.mulligan_count[player.player_id]

        # If they mulliganed, they must bottom cards
        if mulligans > 0:
            if cards_to_bottom is None or len(cards_to_bottom) != mulligans:
                print(f"   ❌ {player.player_id} must bottom {mulligans} cards, got {len(cards_to_bottom) if cards_to_bottom else 0}")
                return False

            # Validate cards are in hand
            for card_id in cards_to_bottom:
                if not self._card_in_hand(player, card_id):
                    print(f"   ❌ {card_id} not in {player.player_id}'s hand")
                    return False

            # Bottom the specified cards
            self.bottom_cards(player, cards_to_bottom)

        # Mark as finished
        self.finished_players.add(player.player_id)
        print(f"   ✅ {player.player_id} kept hand after {mulligans} mulligan(s)")
        return True

    # ======================================================
    # Take Mulligan
    # ======================================================

    def mulligan(self, player: Player) -> bool:
        """
        Player takes a mulligan.
        
        Returns:
            bool: True if successful
        """
        if player.player_id in self.finished_players:
            print(f"   ⚠️ {player.player_id} already finished mulligan")
            return False

        # Collect current hand
        cards = list(player.hand)

        # Return cards to library
        player.hand.clear()
        for card in cards:
            player.library.add(card)

        # Shuffle library
        player.library.shuffle()

        # Increment mulligan count
        self.mulligan_count[player.player_id] += 1

        # Draw new hand
        self.draw_starting_hand(player)

        print(f"   🔄 {player.player_id} took mulligan #{self.mulligan_count[player.player_id]}")
        return True

    # ======================================================
    # Bottom Cards
    # ======================================================

    def bottom_cards(self, player: Player, card_ids: List[str]) -> None:
        """
        Put specified cards from hand on the bottom of the library.
        
        Args:
            player: The player
            card_ids: List of card IDs to put on bottom
        """
        for card_id in card_ids:
            # Find card in hand
            card = self._find_card_in_hand(player, card_id)
            if card:
                player.hand.remove(card)
                player.library.add(card)
                print(f"   📥 {player.player_id} bottomed {card.name}")

    def bottom_cards_auto(self, player: Player, amount: int) -> None:
        """
        Auto-bottom cards (chooses the last cards in hand).
        
        This is used when the player doesn't specify which cards to bottom.
        In a full implementation, the player would choose.
        """
        if amount <= 0:
            return

        # Get cards from hand (last ones)
        cards_to_bottom = []
        hand_cards = list(player.hand)
        for i in range(min(amount, len(hand_cards))):
            cards_to_bottom.append(hand_cards[-(i + 1)].card_id)

        self.bottom_cards(player, cards_to_bottom)

    # ======================================================
    # Helper Methods
    # ======================================================

    def _card_in_hand(self, player: Player, card_id: str) -> bool:
        """Check if a card is in the player's hand."""
        return self._find_card_in_hand(player, card_id) is not None

    def _find_card_in_hand(self, player: Player, card_id: str) -> Optional[Card]:
        """Find a card in the player's hand by ID."""
        for card in player.hand:
            if card.card_id == card_id:
                return card
        return None

    # ======================================================
    # Status
    # ======================================================

    def player_finished(self, player: Player) -> bool:
        """Check if a player has finished mulligan."""
        return player.player_id in self.finished_players

    def all_players_finished(self) -> bool:
        """Check if all players have finished mulligan."""
        return len(self.finished_players) == len(self.game_state.players)

    def get_mulligan_count(self, player: Player) -> int:
        """Get the number of mulligans a player has taken."""
        return self.mulligan_count.get(player.player_id, 0)

    def reset(self) -> None:
        """Reset the mulligan state for a new game."""
        self.finished_players.clear()
        self.mulligan_count.clear()

    def get_summary(self) -> dict:
        """Get a summary of the mulligan state."""
        return {
            "finished_players": list(self.finished_players),
            "mulligan_counts": self.mulligan_count.copy(),
            "all_finished": self.all_players_finished()
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        finished = len(self.finished_players)
        total = len(self.game_state.players)
        return f"MulliganManager({finished}/{total} finished)"