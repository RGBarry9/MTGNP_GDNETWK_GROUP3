# server/game_server.py
from network.server import Server
from network.dispatcher import Dispatcher
from protocol.message_types import MessageType
from engine.game import Game
from engine.validator import GameValidator
from game.loader import CardLoader
import sys


class GameServer:
    """Main MTGNP server that integrates network, protocol, and game engine."""

    def __init__(self):
        # Network
        self.server = Server()
        self.dispatcher = Dispatcher()
        self.connections = []
        self.running = False
        self.verbose = False
        
        # Game engine
        self.game = Game()
        self.game_state = self.game.game_state
        self.validator = GameValidator(self.game_state)
        
        # Connection tracking
        self.player_connections = {}  # connection -> player_id
        self.connection_player = {}   # player_id -> connection
        
        # Card database
        self.card_db = {}
        self._load_cards()
        
        # Sequence number
        self._seq_num = 0
        
        # Register handlers
        self._register_handlers()
    
    def _load_cards(self):
        """Load card database from game/cards.json."""
        try:
            loader = CardLoader()
            self.card_db = loader.load("game/cards.json")
        except FileNotFoundError:
            print("⚠️ game/cards.json not found, using empty database")
            self.card_db = {}
        except Exception as e:
            print(f"⚠️ Error loading cards: {e}")
            self.card_db = {}
    
    def _register_handlers(self):
        """Register message handlers with dispatcher."""
        from handlers.lobby_handler import player_ready, mulligan_choice
        from handlers.combat_handler import declare_attackers, declare_blockers, assign_damage_order
        from handlers.priority_handler import priority_pass
        from handlers.spell_handler import cast_spell, play_land, activate_ability
        from handlers.game_handler import concede, game_over, phase_transition
        
        self.dispatcher.register(MessageType.PLAYER_READY.value, lambda m: player_ready(self, m))
        self.dispatcher.register(MessageType.MULLIGAN_CHOICE.value, lambda m: mulligan_choice(self, m))
        self.dispatcher.register(MessageType.CAST_SPELL.value, lambda m: cast_spell(self, m))
        self.dispatcher.register(MessageType.PLAY_LAND.value, lambda m: play_land(self, m))
        self.dispatcher.register(MessageType.ACTIVATE_ABILITY.value, lambda m: activate_ability(self, m))
        self.dispatcher.register(MessageType.DECLARE_ATTACKERS.value, lambda m: declare_attackers(self, m))
        self.dispatcher.register(MessageType.DECLARE_BLOCKERS.value, lambda m: declare_blockers(self, m))
        self.dispatcher.register(MessageType.ASSIGN_DAMAGE_ORDER.value, lambda m: assign_damage_order(self, m))
        self.dispatcher.register(MessageType.PRIORITY_PASS.value, lambda m: priority_pass(self, m))
        self.dispatcher.register(MessageType.CONCEDE.value, lambda m: concede(self, m))
        self.dispatcher.register(MessageType.GAME_OVER.value, lambda m: game_over(self, m))
        self.dispatcher.register(MessageType.PHASE_TRANSITION.value, lambda m: phase_transition(self, m))
        self.dispatcher.register(MessageType.PING.value, self._handle_ping)
    
    def _handle_ping(self, message):
        """Handle PING - respond with PONG."""
        conn = self._find_connection(message)
        if conn:
            pong = {
                "type": "PONG",
                "timestamp": message.get("timestamp")
            }
            self.send_to_connection(conn, pong)
    
    # ==========================================================
    # CRITICAL FIX: Find the correct connection for a message
    # ==========================================================
    
    def _find_connection(self, message):
        """
        Find the connection that sent a message.
        
        This is critical for proper player-to-connection mapping.
        """
        # Check if we have a player_id in the message
        player_id = message.get("player_id")
        
        # If we have a player_id and it's in our mapping, return the connection
        if player_id and player_id in self.connection_player:
            return self.connection_player[player_id]
        
        # If not, find the first connection that hasn't been assigned to a player yet
        for conn in self.connections:
            if conn not in self.player_connections:
                # This connection hasn't been assigned yet
                return conn
        
        # Fallback: return the first connection
        if self.connections:
            return self.connections[0]
        
        return None
    
    def next_seq(self):
        """Get next sequence number."""
        self._seq_num += 1
        return self._seq_num
    
    # ==========================================================
    # SEND METHODS
    # ==========================================================
    
    def send_to_connection(self, connection, message):
        """Send a message to a specific connection."""
        if connection:
            message['seq_num'] = self.next_seq()
            connection.send(message)
            if self.verbose:
                print(f"[SEND -> {connection}] {message.get('type')}")
    
    def send_to_player(self, player_id, message):
        """Send a message to a specific player."""
        if player_id in self.connection_player:
            conn = self.connection_player[player_id]
            self.send_to_connection(conn, message)
        else:
            if self.verbose:
                print(f"⚠️ No connection found for player {player_id}")
    
    def broadcast(self, message):
        """Broadcast a message to all players."""
        message['seq_num'] = self.next_seq()
        self.server.broadcast(message)
        if self.verbose:
            print(f"[BROADCAST] {message.get('type')}")
    
    def send_error(self, connection, code, message_text, rejected_action=None):
        """Send an ERROR PDU."""
        error_msg = {
            "type": "ERROR",
            "code": code,
            "message": message_text,
            "rejected_action": rejected_action
        }
        self.send_to_connection(connection, error_msg)
    
    # ==========================================================
    # GAME HELPERS
    # ==========================================================
    
    def _broadcast_personalized_state(self):
        """Broadcast personalized state to each player."""
        for player in self.game_state.players:
            state = self.game_state.get_personalized_state(player.player_id)
            
            # Debug print
            if self.verbose:
                hand = state.get("hand", {}).get(player.player_id, [])
                conn = self.connection_player.get(player.player_id)
                print(f"   📤 Sending state to {player.player_id}: phase={state.get('phase')}, hand={len(hand)} cards, conn={conn}")
            
            msg = {
                "type": "GAME_STATE_UPDATE",
                "state": state
            }
            self.send_to_player(player.player_id, msg)
    
    def _broadcast_phase_transition(self):
        """
        Broadcast phase transition.
        
        CRITICAL FIX: Convert Phase enum to string for JSON serialization.
        """
        # Convert Phase enum to string for JSON serialization
        phase_str = self.game_state.current_phase.value if hasattr(self.game_state.current_phase, 'value') else str(self.game_state.current_phase)
        
        msg = {
            "type": "PHASE_TRANSITION",
            "to_phase": phase_str,
            "active_player": self.game_state.active_player.player_id if self.game_state.active_player else None,
            "turn": self.game_state.turn_number
        }
        self.broadcast(msg)
        if self.verbose:
            print(f"   📤 PHASE_TRANSITION to {phase_str}")
    
    def _give_priority(self):
        """Give priority to the active player."""
        active = self.game_state.active_player
        if not active:
            if self.verbose:
                print("⚠️ No active player to give priority")
            return
        
        self.game.priority_manager.give_priority(active)
        msg = {
            "type": "PRIORITY_GRANT",
            "player_id": active.player_id,
            "time_limit_ms": 60000
        }
        self.send_to_player(active.player_id, msg)
        if self.verbose:
            print(f"   📤 PRIORITY_GRANT sent to {active.player_id}")
    
    def _phase_has_priority(self):
        """Check if current phase has priority."""
        no_priority = ["UNTAP", "CLEANUP"]
        return self.game_state.current_phase not in no_priority
    
    def _end_game(self, loser_id, reason):
        """End the game."""
        loser = self.game.get_player(loser_id)
        if loser:
            winner = self.game_state.get_opponent(loser)
            if winner:
                msg = {
                    "type": "GAME_OVER",
                    "winner_id": winner.player_id,
                    "loser_id": loser_id,
                    "reason": reason
                }
                self.broadcast(msg)
                self.game.end_game(winner)
                if self.verbose:
                    print(f"🏆 Game Over! Winner: {winner.player_id}, Reason: {reason}")
    
    # ==========================================================
    # GAME FLOW METHODS
    # ==========================================================
    
    def _start_game(self):
        """Start the game setup after both players are ready."""
        print("\n🎮 Both players ready! Starting game setup...")
        
        if not self.game:
            print("⚠️ No game instance")
            return
        
        if not self.game.players_ready():
            print("⚠️ Not all players are ready to start the game")
            return
        
        # Debug: Print connection mappings
        if self.verbose:
            print(f"   🔍 DEBUG: connection_player = {self.connection_player}")
            print(f"   🔍 DEBUG: player_connections = {self.player_connections}")
        
        try:
            # Ensure libraries are set up from decks
            for player in self.game_state.players:
                if player.deck and len(player.deck) > 0:
                    if len(player.library) == 0:
                        player.library = player.deck.to_library()
                        print(f"   📚 {player.player_id} library: {len(player.library)} cards")
                else:
                    print(f"   ⚠️ {player.player_id} has no deck!")
            
            # Start the game - this triggers mulligan phase
            self.game.start_game()
            print("✅ Game setup complete. Mulligan phase started.")
            
            # Broadcast initial personalized state to both players
            self._broadcast_personalized_state()
            
        except Exception as e:
            print(f"❌ Error starting game: {e}")
            import traceback
            traceback.print_exc()
    
    def _start_first_turn(self):
        """Start the first turn after mulligan is complete."""
        print("\n🎮 Starting first turn...")
        
        if not self.game:
            print("⚠️ No game instance")
            return
        
        if self.verbose:
            print(f"   🔍 DEBUG: active_player before start_turn = {self.game_state.active_player}")
        
        try:
            # Start the first turn
            self.game.start_turn()
            
            if self.verbose:
                print(f"   🔍 DEBUG: phase after start_turn = {self.game_state.current_phase}")
                print(f"   🔍 DEBUG: active_player after start_turn = {self.game_state.active_player}")
            
            # Broadcast phase transition
            self._broadcast_phase_transition()
            
            # Broadcast personalized state
            self._broadcast_personalized_state()
            
            # Give priority to the active player
            self._give_priority()
            
            print(f"✅ Turn {self.game_state.turn_number} started")
            
        except Exception as e:
            print(f"❌ Error starting first turn: {e}")
            import traceback
            traceback.print_exc()
    
    # ==========================================================
    # MAIN LOOP
    # ==========================================================
    
    def start(self):
        """Start the server."""
        self.connections = self.server.start()
        self.running = True
        
        # Debug: Print connection list
        if self.verbose:
            print(f"   🔍 DEBUG: connections = {self.connections}")
        
        print("\n🔄 Game server ready. Waiting for messages...\n")
        self._main_loop()
    
    def _main_loop(self):
        """Main server loop - receive and dispatch messages."""
        while self.running:
            for conn in self.connections:
                message = conn.receive()
                if message is None:
                    continue
                if self.verbose:
                    print(f"\n[RECV] {message.get('type')}")
                self.dispatcher.dispatch(message)
    
    def stop(self):
        """Stop the server."""
        self.running = False
        self.server.stop()
    
    def set_verbose(self, enabled):
        """Enable or disable verbose mode."""
        self.verbose = enabled