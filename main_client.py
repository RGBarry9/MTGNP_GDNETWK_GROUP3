# main_client.py - Complete Fixed Version
import sys
import argparse
import json
from network.client import Client
from protocol.protocol import make_message
from protocol.message_types import MessageType


class MTGNPClient:
    """Interactive MTGNP client."""
    
    def __init__(self):
        self.client = None
        self.player_id = None
        self.running = True
        self.verbose = False
        self.seq_num = 0
        self.hand = []
        self.battlefield = []
        self.life = 20
        self.phase = "LOBBY"
        self.active_player = None
        self.priority_holder = None
        
        # ==========================================================
        # CRITICAL FIX: Track priority sequence number separately
        # ==========================================================
        self.priority_seq_num = 0  # Track the current priority sequence number
        
        # Mulligan state
        self.mulligan_done = False
        self.waiting_for_mulligan = False
        self.hand_received = False
    
    def next_seq(self):
        """Get next general sequence number (for non-priority messages)."""
        self.seq_num += 1
        return self.seq_num
    
    def connect(self):
        print("="*60)
        print("MTGNP CLIENT v1.0")
        print("="*60)
        
        try:
            self.client = Client()
            return True
        except ConnectionRefusedError:
            print("❌ Could not connect to server. Make sure the server is running.")
            return False
        except Exception as e:
            print(f"❌ Connection error: {e}")
            return False
    
    def send_player_ready(self):
        self.player_id = input("Enter your player ID (e.g., player_1): ").strip()
        if not self.player_id:
            self.player_id = "player_1"
        
        print("\nBuilding deck...")
        deck = self._build_deck()
        print(f"Deck: {len(deck)} cards")
        
        # PLAYER_READY uses its own seq_num (not priority_seq_num)
        msg = make_message(
            MessageType.PLAYER_READY,
            seq_num=self.next_seq(),
            player_id=self.player_id,
            deck_list=deck
        )
        self.client.send(msg)
        print(f"✅ PLAYER_READY sent as {self.player_id}")
        print("⏳ Waiting for other player to connect...\n")
    
    def _build_deck(self):
        """Build a default deck for testing."""
        return [
            "mountain_001", "mountain_001", "mountain_001", "mountain_001",
            "mountain_001", "mountain_001", "mountain_001", "mountain_001",
            "goblin_guide_001",
            "lightning_bolt_001", "lightning_bolt_001", "lightning_bolt_001",
            "shock_001", "shock_001",
            "wall_of_stone_001",
            "grizzly_bears_001", "grizzly_bears_001",
            "hill_giant_001",
            "giant_growth_001", "giant_growth_001"
        ]
    
    def start_message_loop(self):
        """Start the main message loop."""
        print("🔄 Connected to server. Waiting for messages...\n")
        
        while self.running:
            try:
                message = self.client.receive()
                
                if message is None:
                    print("❌ Disconnected from server.")
                    break
                
                if self.verbose:
                    print(f"\n[RECV] {message.get('type')}")
                    # Print full JSON for important messages
                    if message.get('type') in ["GAME_STATE_UPDATE", "PRIORITY_GRANT", "GAME_OVER"]:
                        print(json.dumps(message, indent=2, default=str))
                
                self._handle_message(message)
                
            except Exception as e:
                if self.running:
                    print(f"⚠️ Error receiving message: {e}")
                break
    
    def _handle_message(self, message):
        """Handle incoming messages."""
        msg_type = message.get("type")
        
        if msg_type == "GAME_STATE_UPDATE":
            self._handle_state_update(message.get("state", {}))
        elif msg_type == "PRIORITY_GRANT":
            self._handle_priority_grant(message)
        elif msg_type == "PHASE_TRANSITION":
            self.phase = message.get("to_phase", "UNKNOWN")
            print(f"\n--- PHASE: {self.phase} ---")
        elif msg_type == "STACK_PUSH":
            print(f"[STACK] {message.get('source')} added to stack")
        elif msg_type == "STACK_RESOLVE":
            print(f"[STACK] {message.get('stack_item_id')} resolved")
        elif msg_type == "COMBAT_DAMAGE_RESULT":
            self._handle_combat_damage(message)
        elif msg_type == "GAME_OVER":
            self._handle_game_over(message)
        elif msg_type == "ERROR":
            print(f"❌ ERROR [{message.get('code')}]: {message.get('message')}")
        elif msg_type == "PONG":
            pass
        else:
            if self.verbose:
                print(f"📨 {msg_type}: {message}")
    
    def _handle_state_update(self, state):
        """Handle GAME_STATE_UPDATE."""
        new_phase = state.get("phase", "UNKNOWN")
        
        # Debug: Print what we received
        print(f"\n🔍 DEBUG: Received state update - phase={new_phase}, my_id={self.player_id}")
        
        # Update phase
        if new_phase != self.phase:
            self.phase = new_phase
            print(f"🔍 DEBUG: Phase changed to {self.phase}")
            # Reset mulligan state when leaving mulligan phase
            if self.phase != "MULLIGAN":
                self.mulligan_done = False
                self.waiting_for_mulligan = False
        
        self.active_player = state.get("active_player")
        self.priority_holder = state.get("priority_holder")
        
        # Life totals
        lives = state.get("life_totals", {})
        for pid, life in lives.items():
            if pid == self.player_id:
                self.life = life
        
        # Hand - CRITICAL: Check if we have hand data
        hand_data = state.get("hand", {})
        hand_counts = state.get("hand_counts", {})
        
        print(f"🔍 DEBUG: hand_data keys = {list(hand_data.keys())}")
        print(f"🔍 DEBUG: hand_counts = {hand_counts}")
        
        if self.player_id in hand_data:
            self.hand = hand_data[self.player_id]
            self.hand_received = True
            print(f"🔍 DEBUG: Received hand with {len(self.hand)} cards")
        elif self.player_id in hand_counts:
            print(f"🔍 DEBUG: Hand count = {hand_counts[self.player_id]}")
        
        # Battlefield
        bf = state.get("battlefield", {})
        self.battlefield = bf.get(self.player_id, [])
        
        # Display
        self._display_state(state)
        
        # ==========================================================
        # Handle MULLIGAN phase
        # ==========================================================
        if self.phase == "MULLIGAN":
            print(f"🔍 DEBUG: In MULLIGAN phase, mulligan_done={self.mulligan_done}")
            
            # If this player has already finished mulligan, don't show prompt
            if self.mulligan_done:
                if not self.waiting_for_mulligan:
                    self.waiting_for_mulligan = True
                    print("\n⏳ Waiting for other player to finish mulligan...")
                return
            
            # If we have a hand and haven't finished mulligan, show prompt
            if self.player_id in hand_data and len(hand_data[self.player_id]) > 0:
                print("🔍 DEBUG: Showing mulligan prompt")
                self._handle_mulligan_phase()
            else:
                print("🔍 DEBUG: No hand data yet, waiting...")
    
    def _display_state(self, state):
        """Display the current game state."""
        print("\n" + "-"*50)
        print(f"📊 Turn {state.get('turn', 0)} | {state.get('phase', 'UNKNOWN')}")
        print(f"Active: {state.get('active_player', 'None')}")
        
        lives = state.get("life_totals", {})
        for pid, life in lives.items():
            marker = "👤" if pid == self.player_id else "👥"
            print(f"  {marker} {pid}: {life} life")
        
        # Hand
        hand_data = state.get("hand", {})
        hand_counts = state.get("hand_counts", {})
        
        if self.player_id in hand_data:
            self.hand = hand_data[self.player_id]
            if self.hand:
                print(f"\n📝 Hand ({len(self.hand)}): {', '.join(self.hand[:5])}{'...' if len(self.hand) > 5 else ''}")
            else:
                print(f"\n📝 Hand: empty")
        elif self.player_id in hand_counts:
            print(f"\n📝 Hand: {hand_counts[self.player_id]} cards")
        
        # Battlefield
        bf = state.get("battlefield", {})
        self.battlefield = bf.get(self.player_id, [])
        if self.battlefield:
            print(f"\n🏟️ Battlefield:")
            for p in self.battlefield:
                tapped = " [TAPPED]" if p.get("tapped") else ""
                if "power" in p:
                    print(f"  - {p.get('id')} ({p.get('power')}/{p.get('toughness')}){tapped}")
                else:
                    print(f"  - {p.get('id')}{tapped}")
        
        print("-"*50)
    
    def _handle_mulligan_phase(self):
        """Handle mulligan phase - ask player for decision."""
        # Don't show if already done
        if self.mulligan_done:
            print("🔍 DEBUG: Mulligan already done, skipping prompt")
            return
        
        print("\n" + "="*40)
        print("🃏 MULLIGAN PHASE")
        print("="*40)
        print(f"You have {len(self.hand)} cards in hand.")
        print("Commands:")
        print("  keep          - Keep your hand")
        print("  mulligan      - Take a mulligan (shuffle hand back, draw 7 new cards)")
        print()
        
        while True:
            try:
                cmd = input("> ").strip().lower()
                if cmd == "keep":
                    self._send_mulligan_keep()
                    break
                elif cmd == "mulligan":
                    self._send_mulligan_mulligan()
                    break
                else:
                    print("Unknown command. Type 'keep' or 'mulligan'.")
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _send_mulligan_keep(self):
        """Send MULLIGAN_CHOICE with keep=True."""
        # MULLIGAN_CHOICE uses its own seq_num (not priority_seq_num)
        msg = make_message(
            MessageType.MULLIGAN_CHOICE,
            seq_num=self.next_seq(),
            player_id=self.player_id,
            keep=True,
            cards_to_bottom=[]
        )
        self.client.send(msg)
        print("✅ Kept hand")
        self.mulligan_done = True
        self.waiting_for_mulligan = False
    
    def _send_mulligan_mulligan(self):
        """Send MULLIGAN_CHOICE with keep=False."""
        # MULLIGAN_CHOICE uses its own seq_num (not priority_seq_num)
        msg = make_message(
            MessageType.MULLIGAN_CHOICE,
            seq_num=self.next_seq(),
            player_id=self.player_id,
            keep=False,
            cards_to_bottom=[]
        )
        self.client.send(msg)
        print("🔄 Taking mulligan...")
        # Don't set mulligan_done = True - we'll get a new hand and need to decide again
    
    def _handle_priority_grant(self, message):
        """Handle PRIORITY_GRANT - user can take actions."""
        if message.get("player_id") != self.player_id:
            return
        
        # ==========================================================
        # CRITICAL FIX: Store the priority sequence number
        # ==========================================================
        self.priority_seq_num = message.get("seq_num", 0)
        if self.verbose:
            print(f"🔍 DEBUG: Stored priority_seq_num = {self.priority_seq_num}")
        
        print("\n" + "="*40)
        print("🎯 YOU HAVE PRIORITY!")
        print("="*40)
        print("Commands:")
        print("  pass          - Pass priority")
        print("  cast <id>     - Cast a spell")
        print("  land <id>     - Play a land")
        print("  attack <id>   - Attack with creature")
        print("  block <id> <attacker> - Block an attacker")
        print("  concede       - Concede the game")
        print("  help          - Show this help")
        print()
        
        while True:
            try:
                cmd = input("> ").strip().split()
                if not cmd:
                    continue
                
                action = cmd[0].lower()
                
                if action == "pass":
                    self._send_pass()
                    break
                elif action == "cast" and len(cmd) > 1:
                    self._send_cast_spell(cmd[1])
                    break
                elif action == "land" and len(cmd) > 1:
                    self._send_play_land(cmd[1])
                    break
                elif action == "attack" and len(cmd) > 1:
                    self._send_attack(cmd[1])
                    break
                elif action == "block" and len(cmd) > 2:
                    self._send_block(cmd[1], cmd[2])
                    break
                elif action == "concede":
                    self._send_concede()
                    break
                elif action == "help":
                    self._show_help()
                else:
                    print("Unknown command. Type 'help' for options.")
            except KeyboardInterrupt:
                print("\n")
                break
            except Exception as e:
                print(f"Error: {e}")
    
    def _show_help(self):
        print("\nCommands:")
        print("  pass          - Pass priority")
        print("  cast <id>     - Cast a spell (e.g., cast lightning_bolt_001)")
        print("  land <id>     - Play a land (e.g., land mountain_001)")
        print("  attack <id>   - Attack with creature (e.g., attack goblin_001)")
        print("  block <id> <attacker> - Block an attacker")
        print("  concede       - Concede the game")
        print("  help          - Show this help")
        print()
    
    # ==========================================================
    # ACTION METHODS - Use priority_seq_num for priority actions
    # ==========================================================
    
    def _send_pass(self):
        """Send PRIORITY_PASS using the current priority sequence number."""
        msg = make_message(
            MessageType.PRIORITY_PASS,
            seq_num=self.priority_seq_num,  # ← Use priority_seq_num
            player_id=self.player_id
        )
        self.client.send(msg)
        print("✅ Priority passed")
    
    def _send_cast_spell(self, card_id):
        """Send CAST_SPELL using the current priority sequence number."""
        target = input("Target (player_id or 'none'): ").strip()
        targets = [] if target.lower() == "none" else [target]
        
        msg = make_message(
            MessageType.CAST_SPELL,
            seq_num=self.priority_seq_num,  # ← Use priority_seq_num
            player_id=self.player_id,
            card_id=card_id,
            targets=targets,
            mana_payment={"R": 1}
        )
        self.client.send(msg)
        print(f"✅ Cast {card_id}")
    
    def _send_play_land(self, card_id):
        """Send PLAY_LAND using the current priority sequence number."""
        msg = make_message(
            MessageType.PLAY_LAND,
            seq_num=self.priority_seq_num,  # ← Use priority_seq_num
            player_id=self.player_id,
            card_id=card_id
        )
        self.client.send(msg)
        print(f"✅ Played {card_id}")
    
    def _send_attack(self, creature_id):
        """Send DECLARE_ATTACKERS using the current priority sequence number."""
        target = input("Target (player_id): ").strip()
        attackers = [{"creature_id": creature_id, "target": target}]
        
        msg = make_message(
            MessageType.DECLARE_ATTACKERS,
            seq_num=self.priority_seq_num,  # ← Use priority_seq_num
            player_id=self.player_id,
            attackers=attackers
        )
        self.client.send(msg)
        print(f"✅ {creature_id} attacks")
    
    def _send_block(self, blocker_id, attacker_id):
        """Send DECLARE_BLOCKERS using the current priority sequence number."""
        blockers = [{"creature_id": blocker_id, "blocking_id": attacker_id}]
        
        msg = make_message(
            MessageType.DECLARE_BLOCKERS,
            seq_num=self.priority_seq_num,  # ← Use priority_seq_num
            player_id=self.player_id,
            blockers=blockers
        )
        self.client.send(msg)
        print(f"✅ {blocker_id} blocks {attacker_id}")
    
    # ==========================================================
    # FIXED: CONCEDE - Wait for GAME_OVER response
    # ==========================================================
    
    def _send_concede(self):
        """Send CONCEDE and wait for GAME_OVER response."""
        # CONCEDE uses its own seq_num (exempt from priority-echo rule)
        msg = make_message(
            MessageType.CONCEDE,
            seq_num=self.next_seq(),
            player_id=self.player_id
        )
        self.client.send(msg)
        print("🏳️ You conceded. Waiting for game to end...")
        # DO NOT set self.running = False here!
        # Wait for GAME_OVER from the server
    
    def _handle_combat_damage(self, message):
        events = message.get("damage_events", [])
        print("\n⚔️ COMBAT DAMAGE:")
        for event in events:
            print(f"  {event.get('source')} -> {event.get('target')}: {event.get('amount')} damage")
        
        lives = message.get("life_totals", {})
        for pid, life in lives.items():
            if pid == self.player_id:
                self.life = life
    
    def _handle_game_over(self, message):
        print("\n" + "="*50)
        print("🏆 GAME OVER")
        print("="*50)
        print(f"Winner: {message.get('winner_id')}")
        print(f"Loser: {message.get('loser_id')}")
        print(f"Reason: {message.get('reason')}")
        print("="*50)
        self.running = False
    
    def run(self):
        if not self.connect():
            return
        
        self.send_player_ready()
        self.start_message_loop()
        
        print("\n👋 Client disconnected")


def main():
    parser = argparse.ArgumentParser(description="MTGNP Client")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose mode")
    args = parser.parse_args()
    
    client = MTGNPClient()
    client.verbose = args.verbose
    
    try:
        client.run()
    except KeyboardInterrupt:
        print("\n\n👋 Client stopped by user")
    except Exception as e:
        print(f"\n❌ Client error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()