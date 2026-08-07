# engine/game.py
from typing import Optional, List, Dict, Any
from models.player import Player
from models.card import Card
from engine.gamestate import GameState
from engine.turn import TurnManager
from engine.priority import PriorityManager
from engine.stack import StackManager
from engine.combat import CombatManager
from engine.mulligan import MulliganManager
from engine.winconditions import WinConditionManager
from effects.effect_manager import EffectManager
from config.enums import Phase, GameState as GameStateEnum


class Game:
    """
    Main game controller.

    Coordinates all engine subsystems and provides the primary API
    used by the GameServer.
    """

    def __init__(self):
        self.game_state = GameState()
        self.turn_manager = TurnManager(self.game_state)
        self.priority_manager = PriorityManager(self.game_state)
        self.stack_manager = StackManager(self.game_state)
        self.combat_manager = CombatManager(self.game_state)
        self.mulligan_manager = MulliganManager(self.game_state)
        self.effect_manager = EffectManager(self.game_state)
        self.win_manager = WinConditionManager(self.game_state)
        
        self._is_initialized = False

    # ==========================================================
    # Player Management
    # ==========================================================

    def add_player(self, player: Player) -> bool:
        """Add a player to the game."""
        return self.game_state.add_player(player)

    def remove_player(self, player: Player) -> bool:
        """Remove a player from the game."""
        return self.game_state.remove_player(player)

    def get_player(self, player_id: str) -> Optional[Player]:
        """Return the player with the given player ID."""
        return self.game_state.get_player(player_id)

    def get_players(self) -> List[Player]:
        """Return all players in the game."""
        return self.game_state.players

    def get_active_player(self) -> Optional[Player]:
        """Return the active player."""
        return self.game_state.active_player

    def get_opponent(self, player: Player) -> Optional[Player]:
        """Return the opponent of the specified player."""
        return self.game_state.get_opponent(player)

    def players_ready(self) -> bool:
        """Return True when all players are ready."""
        return self.game_state.all_players_ready()

    def is_active_player(self, player: Player) -> bool:
        """Check if a player is the active player."""
        return self.game_state.active_player == player

    # ==========================================================
    # Game Lifecycle
    # ==========================================================

    def start_game(self) -> None:
        """Start a new game."""
        if not self.players_ready():
            raise RuntimeError("Cannot start the game until all players are ready.")

        print("\n" + "="*60)
        print("🎮 GAME STARTING")
        print("="*60)

        # Initialize game state
        self.game_state.start_game()
        self.game_state.set_game_state(GameStateEnum.IN_GAME)

        # Set first player (random)
        import random
        first_player = random.choice(self.game_state.players)
        self.game_state.active_player = first_player
        print(f"📍 {first_player.player_id} goes first")

        # Start mulligan phase
        self.mulligan_manager.start()
        print("🃏 Mulligan phase started")

        self._is_initialized = True

    def end_game(self, winner: Player) -> None:
        """End the current game."""
        self.game_state.end_game(winner)
        print(f"\n🏆 Winner: {winner.player_id}")

    def reset_game(self) -> None:
        """Reset the game for a new session."""
        # Reset all managers
        self.mulligan_manager.reset()
        self.win_manager.reset()
        self.priority_manager.reset_for_new_game()
        
        # Reset game state
        self.game_state.game_over = False
        self.game_state.started = False
        self.game_state.set_game_state(GameStateEnum.LOBBY)
        
        # Clear all player states
        for player in self.game_state.players:
            player.battlefield.clear()
            player.hand.clear()
            player.graveyard.clear()
            player.library.clear()
            player.life = 20
            player.ready = False
            player.lands_played = 0
        
        self._is_initialized = False

    # ==========================================================
    # Turn Management
    # ==========================================================

    def start_turn(self) -> None:
        """Begin the active player's turn."""
        if not self._is_initialized:
            raise RuntimeError("Game not initialized. Call start_game() first.")
        self.turn_manager.start_turn()

    def end_turn(self) -> None:
        """End the active player's turn."""
        self.turn_manager.end_turn()
        self.check_win_conditions()

    def next_phase(self) -> Phase:
        """Advance to the next phase."""
        return self.turn_manager.next_phase()

    def get_current_phase(self) -> Phase:
        """Get the current phase."""
        return self.turn_manager.current_phase()

    def get_turn_number(self) -> int:
        """Get the current turn number."""
        return self.turn_manager.turn_number()

    # ==========================================================
    # Priority
    # ==========================================================

    def give_priority(self, player: Player) -> None:
        """Give priority to a player."""
        self.priority_manager.give_priority(player)

    def pass_priority(self, player: Player) -> str:
        """Player passes priority."""
        return self.priority_manager.pass_priority(player)

    def has_priority(self, player: Player) -> bool:
        """Check if a player has priority."""
        return self.priority_manager.has_priority(player)

    def get_priority_player(self) -> Optional[Player]:
        """Get the player who currently has priority."""
        return self.priority_manager.current_player()

    def get_priority_seq_num(self) -> int:
        """Get the current priority sequence number."""
        return self.priority_manager.get_priority_seq_num()

    def validate_priority_seq(self, seq_num: int) -> bool:
        """Validate a priority sequence number."""
        return self.priority_manager.validate_seq_num(seq_num)

    # ==========================================================
    # Stack
    # ==========================================================

    def cast_spell(self, stack_item) -> None:
        """Place a spell or ability onto the stack."""
        self.stack_manager.push(stack_item)

    def resolve_stack(self) -> List[Dict[str, Any]]:
        """Resolve the top object on the stack."""
        return self.stack_manager.resolve()

    def stack_is_empty(self) -> bool:
        """Check if the stack is empty."""
        return self.stack_manager.is_empty()

    def stack_size(self) -> int:
        """Get the number of items on the stack."""
        return self.stack_manager.size()

    def get_stack(self) -> List:
        """Get the entire stack."""
        return self.game_state.stack

    # ==========================================================
    # Combat
    # ==========================================================

    def declare_attackers(self, player: Player, attackers: List[Card]) -> List[Card]:
        """Declare attackers for the active player."""
        return self.combat_manager.declare_attackers(player, attackers)

    def declare_blocker(self, player: Player, blocker: Card, attacker: Card) -> bool:
        """Declare a blocker for a specific attacker."""
        return self.combat_manager.declare_blocker(player, blocker, attacker)

    def declare_blockers(self, player: Player, blockers: List[Dict]) -> List[Dict]:
        """Declare multiple blockers."""
        return self.combat_manager.declare_blockers(player, blockers)

    def resolve_combat(self) -> Dict[str, Any]:
        """Resolve combat damage."""
        return self.combat_manager.resolve_combat()

    def resolve_first_strike(self) -> Dict[str, Any]:
        """Resolve first strike damage."""
        return self.combat_manager.resolve_first_strike()

    def get_attackers(self) -> List[Card]:
        """Get the current attackers."""
        return self.combat_manager.get_attackers()

    def get_blockers(self) -> Dict[str, Card]:
        """Get the current blockers."""
        return self.combat_manager.get_blockers()

    def combat_active(self) -> bool:
        """Check if combat is active."""
        return self.combat_manager.combat_active()

    def cleanup_combat(self) -> None:
        """Clean up combat state."""
        self.combat_manager.cleanup()

    # ==========================================================
    # Win Conditions
    # ==========================================================

    def check_win_conditions(self) -> Optional[Player]:
        """Check whether the game has ended."""
        winner = self.win_manager.check()
        if winner is not None:
            self.end_game(winner)
        return winner

    def concede(self, player: Player) -> Optional[Player]:
        """Handle a player conceding the game."""
        winner = self.win_manager.concede(player)
        if winner is not None:
            self.end_game(winner)
        return winner

    def disconnect(self, player: Player) -> Optional[Player]:
        """Handle a player disconnecting."""
        winner = self.win_manager.disconnect(player)
        if winner is not None:
            self.end_game(winner)
        return winner

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.win_manager.game_over()

    def get_winner(self) -> Optional[Player]:
        """Get the winner of the game."""
        return self.win_manager.winner()

    def get_win_reason(self) -> Optional[str]:
        """Get the reason the game ended."""
        return self.win_manager.get_win_reason_string()

    # ==========================================================
    # State Information
    # ==========================================================

    def get_game_state(self) -> GameState:
        """Get the current game state."""
        return self.game_state

    def get_personalized_state(self, player_id: str) -> Dict[str, Any]:
        """Get personalized state for a player."""
        return self.game_state.get_personalized_state(player_id)

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the game state."""
        return {
            "started": self.game_state.started,
            "game_over": self.game_state.game_over,
            "turn": self.game_state.turn_number,
            "phase": self.game_state.current_phase.value if hasattr(self.game_state.current_phase, 'value') else str(self.game_state.current_phase),
            "active_player": self.game_state.active_player.player_id if self.game_state.active_player else None,
            "priority_player": self.game_state.priority_player.player_id if self.game_state.priority_player else None,
            "stack_size": len(self.game_state.stack),
            "players": [
                {
                    "player_id": p.player_id,
                    "life": p.life,
                    "hand_size": len(p.hand),
                    "library_size": len(p.library),
                    "battlefield_size": len(p.battlefield),
                    "lands_played": p.lands_played
                }
                for p in self.game_state.players
            ]
        }

    def __str__(self) -> str:
        """String representation for debugging."""
        if self.is_game_over():
            winner = self.get_winner()
            winner_name = winner.player_id if winner else "None"
            return f"Game Over - Winner: {winner_name}"
        return f"Game - Turn {self.get_turn_number()}, Phase: {self.get_current_phase()}"