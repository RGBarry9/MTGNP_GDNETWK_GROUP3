# engine/gamestate.py
from typing import List, Optional, Dict, Any
from models.player import Player
from models.stack_item import StackItem
from config.enums import Phase, GameState as GameStateEnum


class GameState:
    """
    Stores the complete state of a single MTGNP game.
    """

    def __init__(self):

        # ==================================================
        # Players
        # ==================================================

        self.players: List[Player] = []
        self.max_players = 2

        # ==================================================
        # Match Status
        # ==================================================

        self.started = False
        self.game_over = False
        self.winner = None
        self.game_state = GameStateEnum.LOBBY  # ← LOBBY is GameState, not Phase

        # ==================================================
        # Turn Information
        # ==================================================

        self.turn_number = 1
        self.active_player = None
        self.current_phase = Phase.UNTAP  # ← Use a valid Phase value

        # ==================================================
        # Priority
        # ==================================================

        self.priority_player = None
        self.priority_passes = 0
        self.priority_seq_num = 0

        # ==================================================
        # Stack
        # ==================================================

        self.stack: List[StackItem] = []

        # ==================================================
        # Combat
        # ==================================================

        self.attackers = []
        self.blockers = {}
        self.damage_assignments = []

        # ==================================================
        # Turn State
        # ==================================================

        self.land_played_this_turn = False

    # ==========================================================
    # Player Management
    # ==========================================================

    def add_player(self, player: Player) -> bool:
        """Add a player to the game. Returns True if successful."""
        if len(self.players) >= self.max_players:
            return False
        if player in self.players:
            return False
        self.players.append(player)
        if self.active_player is None:
            self.active_player = player
        return True

    def remove_player(self, player: Player) -> bool:
        """Remove a player from the game."""
        if player not in self.players:
            return False
        self.players.remove(player)
        if self.active_player == player:
            self.active_player = None
        return True

    def get_player(self, player_id: str) -> Optional[Player]:
        """Return the player with the given ID."""
        for player in self.players:
            if player.player_id == player_id:
                return player
        return None

    def get_opponent(self, player: Player) -> Optional[Player]:
        """Return the opponent of the specified player."""
        for opponent in self.players:
            if opponent != player:
                return opponent
        return None

    def player_count(self) -> int:
        """Return the number of players currently in the game."""
        return len(self.players)

    # ==========================================================
    # Ready State
    # ==========================================================

    def all_players_ready(self) -> bool:
        """Return True when every player is ready."""
        if len(self.players) != self.max_players:
            return False
        return all(player.ready for player in self.players)

    # ==========================================================
    # Turn State
    # ==========================================================

    def next_turn(self) -> None:
        """Advance to the next turn."""
        self.turn_number += 1
        self.land_played_this_turn = False

    def set_active_player(self, player: Player) -> None:
        """Set the active player."""
        self.active_player = player
        self.land_played_this_turn = False

    def set_phase(self, phase: Phase) -> None:
        """Set the current phase."""
        self.current_phase = phase

    def reset_land_played(self) -> None:
        """Reset land played flag for new turn."""
        self.land_played_this_turn = False

    # ==========================================================
    # Priority
    # ==========================================================

    def reset_priority(self) -> None:
        """
        Reset priority for a new priority cycle.

        NOTE: priority_seq_num is intentionally NOT incremented here.
        It only advances when a PRIORITY_GRANT is actually issued (see
        PriorityManager.give_priority), which is the value clients must
        echo back per RFC 0001 SS8.5. Incrementing it here as well caused
        the counter to skip a value on every double-pass, desyncing the
        server's seq_num from what it had actually broadcast.
        """
        self.priority_passes = 0
        self.priority_player = None
        for player in self.players:
            player.receive_priority()

    def register_priority_pass(self) -> None:
        """Record a player passing priority."""
        self.priority_passes += 1

    def everyone_passed_priority(self) -> bool:
        """Return True if every player has passed priority."""
        return self.priority_passes >= len(self.players)

    def get_priority_seq_num(self) -> int:
        """Get the current priority sequence number."""
        return self.priority_seq_num

    # ==========================================================
    # Stack
    # ==========================================================

    def push_stack(self, stack_item: StackItem) -> None:
        """Push an object onto the stack."""
        self.stack.append(stack_item)

    def pop_stack(self) -> Optional[StackItem]:
        """Pop the top object from the stack."""
        if not self.stack:
            return None
        return self.stack.pop()

    def peek_stack(self) -> Optional[StackItem]:
        """Return the top object on the stack without removing it."""
        if not self.stack:
            return None
        return self.stack[-1]

    def clear_stack(self) -> None:
        """Remove all objects from the stack."""
        self.stack.clear()

    def stack_empty(self) -> bool:
        """Return True if the stack is empty."""
        return len(self.stack) == 0

    def stack_size(self) -> int:
        """Return the number of items on the stack."""
        return len(self.stack)

    # ==========================================================
    # Combat
    # ==========================================================

    def clear_combat(self) -> None:
        """Clear all combat assignments."""
        self.attackers.clear()
        self.blockers.clear()
        self.damage_assignments.clear()

    def has_attackers(self) -> bool:
        """Return True if there are attackers declared."""
        return len(self.attackers) > 0

    def get_blocker_for(self, attacker_id: str) -> Optional[Player]:
        """Get the blocker for a specific attacker."""
        return self.blockers.get(attacker_id)

    # ==========================================================
    # Game Status
    # ==========================================================

    def start_game(self) -> None:
        """Start the game."""
        self.started = True
        self.game_over = False
        self.game_state = GameStateEnum.IN_GAME

    def end_game(self, winner: Player) -> None:
        """End the game and record the winner."""
        self.game_over = True
        self.winner = winner
        self.game_state = GameStateEnum.GAME_OVER

    def set_game_state(self, state: GameStateEnum) -> None:
        """Set the overall game state."""
        self.game_state = state

    # ==========================================================
    # Personalized State (for GAME_STATE_UPDATE PDU)
    # ==========================================================

    def get_personalized_state(self, player_id: str) -> Dict[str, Any]:
        """Get the game state filtered for a specific player."""
        # RFC 0001 SS10.2.2: while the lifecycle is IN_GAME, "phase"
        # reports the current turn Phase (UPKEEP, PRECOMBAT_MAIN, ...).
        # Before that (MULLIGAN in particular - see SS6.4's example),
        # it reports the top-level lifecycle state instead, since there
        # is no meaningful turn Phase yet.
        if self.game_state == GameStateEnum.IN_GAME:
            phase_value = (
                self.current_phase.value
                if hasattr(self.current_phase, 'value') else str(self.current_phase)
            )
        else:
            phase_value = (
                self.game_state.value
                if hasattr(self.game_state, 'value') else str(self.game_state)
            )

        state = {
            "turn": self.turn_number,
            "active_player": self.active_player.player_id if self.active_player else None,
            "phase": phase_value,
            "priority_holder": self.priority_player.player_id if self.priority_player else None,
            "life_totals": {},
            "battlefield": {},
            "graveyard": {},
            "hand": {},
            "hand_counts": {},
            "library_counts": {},
            "stack": [],
            "land_played_this_turn": self.land_played_this_turn
        }

        for player in self.players:
            pid = player.player_id
            
            state["life_totals"][pid] = player.life
            
            state["battlefield"][pid] = []
            for card in player.battlefield:
                entry = {
                    "id": card.card_id,
                    "tapped": card.tapped
                }
                if card.is_creature():
                    entry["damage"] = card.damage_marked
                    entry["power"] = card.power
                    entry["toughness"] = card.toughness
                    entry["summoning_sick"] = card.summoning_sick
                state["battlefield"][pid].append(entry)
            
            state["graveyard"][pid] = [card.card_id for card in player.graveyard]
            state["library_counts"][pid] = len(player.library)
            
            if pid == player_id:
                state["hand"][pid] = [card.card_id for card in player.hand]
                state["hand_counts"][pid] = len(player.hand)
            else:
                state["hand_counts"][pid] = len(player.hand)

        for item in self.stack:
            state["stack"].append({
                "stack_item_id": getattr(item, 'stack_item_id', 'stk_unknown'),
                "item_type": getattr(item, 'item_type', 'SPELL'),
                "source": getattr(item, 'source_id', 'unknown'),
                "targets": getattr(item, 'targets', []),
                "controller": getattr(item, 'controller', '')
            })

        return state