# tests/test_lobby_handler.py - Fixed duplicate ID test
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.player import Player
from models.card import Card
from engine.game import Game
from handlers.lobby_handler import player_ready, mulligan_choice


class MockGameServer:
    """Mock GameServer for testing handlers."""
    
    def __init__(self):
        self.game = Game()
        self.game_state = self.game.game_state
        
        # IMPORTANT: These must match the handler's expectations
        self.connection_player = {}  # player_id -> connection
        self.player_connections = {}  # connection -> player_id
        self.connections = []  # List of all connections
        
        self.errors = []
        self.broadcasts = []
        self.state_updates = []
        self._connection_counter = 0
        
        # Card database
        self.card_db = {
            "mountain_001": {"name": "Mountain", "card_type": "Land", "colors": ["R"]},
            "forest_001": {"name": "Forest", "card_type": "Land", "colors": ["G"]},
            "goblin_001": {"name": "Goblin Guide", "card_type": "Creature", "power": 2, "toughness": 2, "keywords": ["Haste"]},
            "lightning_bolt_001": {"name": "Lightning Bolt", "card_type": "Instant", "mana_cost": "R", "effects": [{"effect_type": "DAMAGE", "amount": 3}]}
        }
        
        self.game_started = False
        self.first_turn_started = False
    
    def _find_connection(self, message):
        """Find or create a connection for a message."""
        player_id = message.get("player_id")
        
        # If this player already has a connection, return it
        if player_id in self.connection_player:
            return self.connection_player[player_id]
        
        # Assign a new connection
        self._connection_counter += 1
        conn = f"conn_{self._connection_counter}"
        self.connections.append(conn)
        return conn
    
    def send_error(self, connection, code, message, rejected_action=None):
        self.errors.append({"code": code, "message": message, "rejected_action": rejected_action})
    
    def send_to_connection(self, connection, message):
        self.broadcasts.append(message)
    
    def _broadcast_lobby_status(self):
        self.state_updates.append("lobby_status_broadcast")
    
    def _start_game(self):
        self.game_started = True
    
    def _start_first_turn(self):
        self.first_turn_started = True
    
    def _broadcast_personalized_state(self):
        self.state_updates.append("personalized_state_broadcast")


def test_player_ready_success():
    """Test successful PLAYER_READY."""
    print("\n1. Testing PLAYER_READY - Success...")
    
    server = MockGameServer()
    
    message = {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",
        "deck_list": ["mountain_001", "forest_001", "goblin_001"]
    }
    
    player_ready(server, message)
    
    # Verify player was added
    player = server.game.get_player("player_1")
    assert player is not None
    assert len(server.errors) == 0
    print("   ✅ PLAYER_READY processed successfully")


def test_player_ready_invalid_deck_size():
    """Test PLAYER_READY with invalid deck size."""
    print("\n2. Testing PLAYER_READY - Invalid Deck Size...")
    
    server = MockGameServer()
    
    # Empty deck
    message = {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",
        "deck_list": []
    }
    
    player_ready(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_DECK"
    print("   ✅ Empty deck error detected")
    
    # Too many cards
    server = MockGameServer()
    message["deck_list"] = [f"card_{i}" for i in range(51)]
    
    player_ready(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_DECK"
    print("   ✅ Deck size > 50 error detected")


def test_player_ready_invalid_cards():
    """Test PLAYER_READY with invalid card IDs."""
    print("\n3. Testing PLAYER_READY - Invalid Cards...")
    
    server = MockGameServer()
    
    message = {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",
        "deck_list": ["mountain_001", "fake_card_001", "goblin_001"]
    }
    
    player_ready(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_DECK"
    print("   ✅ Invalid card error detected")


def test_player_ready_duplicate_id():
    """Test PLAYER_READY with duplicate player ID."""
    print("\n4. Testing PLAYER_READY - Duplicate ID...")
    
    server = MockGameServer()
    
    # First player - this should succeed
    msg1 = {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",
        "deck_list": ["mountain_001", "forest_001"]
    }
    
    # Call the handler - this should succeed
    player_ready(server, msg1)
    
    # Verify first player was added and connection tracked
    assert server.game.get_player("player_1") is not None
    assert "player_1" in server.connection_player
    assert len(server.errors) == 0
    print("   ✅ First player added")
    
    # Second player with same ID - this should fail
    msg2 = {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",  # Same ID
        "deck_list": ["mountain_001", "forest_001"]
    }
    
    # Reset errors before second call
    server.errors = []
    
    # Call the handler again - this should fail with DUPLICATE_ID
    player_ready(server, msg2)
    
    # Now check that an error was sent
    # The handler checks: if player_id in game_server.connection_player.values()
    # Since player_1 is already in connection_player, it should send DUPLICATE_ID
    assert len(server.errors) == 1, f"Expected 1 error, got {len(server.errors)}"
    assert server.errors[0]["code"] == "DUPLICATE_ID"
    print("   ✅ Duplicate ID error detected")


def test_mulligan_keep():
    """Test MULLIGAN_CHOICE - Keep hand."""
    print("\n5. Testing MULLIGAN_CHOICE - Keep...")
    
    server = MockGameServer()
    
    # Setup: Add player and start mulligan
    player = Player(player_id="player_1", name="Alice")
    server.game.add_player(player)
    server.game.mulligan_manager.start()
    
    message = {
        "type": "MULLIGAN_CHOICE",
        "seq_num": 3,
        "player_id": "player_1",
        "keep": True,
        "cards_to_bottom": []
    }
    
    mulligan_choice(server, message)
    
    assert server.game.mulligan_manager.player_finished(server.game.get_player("player_1")) == True
    print("   ✅ Keep hand processed")


def test_mulligan_take():
    """Test MULLIGAN_CHOICE - Take mulligan."""
    print("\n6. Testing MULLIGAN_CHOICE - Take Mulligan...")
    
    server = MockGameServer()
    
    # Setup: Add player and start mulligan
    player = Player(player_id="player_1", name="Alice")
    server.game.add_player(player)
    server.game.mulligan_manager.start()
    
    message = {
        "type": "MULLIGAN_CHOICE",
        "seq_num": 3,
        "player_id": "player_1",
        "keep": False,
        "cards_to_bottom": []
    }
    
    mulligan_choice(server, message)
    
    assert server.game.mulligan_manager.mulligan_count["player_1"] == 1
    print("   ✅ Mulligan taken")


def test_mulligan_keep_after_mulligan():
    """Test MULLIGAN_CHOICE - Keep after mulligan (must bottom cards)."""
    print("\n7. Testing MULLIGAN_CHOICE - Keep after Mulligan...")
    
    server = MockGameServer()
    
    # Setup: Add player and start mulligan
    player = Player(player_id="player_1", name="Alice")
    server.game.add_player(player)
    server.game.mulligan_manager.start()
    
    # Take a mulligan first
    server.game.mulligan_manager.mulligan(player)
    
    # Get a card ID from hand
    card_to_bottom = list(player.hand)[0].card_id if len(player.hand) > 0 else None
    if card_to_bottom:
        message = {
            "type": "MULLIGAN_CHOICE",
            "seq_num": 3,
            "player_id": "player_1",
            "keep": True,
            "cards_to_bottom": [card_to_bottom]
        }
        
        mulligan_choice(server, message)
        
        assert server.game.mulligan_manager.player_finished(player) == True
        print("   ✅ Keep after mulligan with bottom processed")


def test_mulligan_keep_wrong_bottom_count():
    """Test MULLIGAN_CHOICE - Keep after mulligan with wrong bottom count."""
    print("\n8. Testing MULLIGAN_CHOICE - Wrong Bottom Count...")
    
    server = MockGameServer()
    
    # Setup: Add player and start mulligan
    player = Player(player_id="player_1", name="Alice")
    server.game.add_player(player)
    server.game.mulligan_manager.start()
    
    # Take a mulligan first
    server.game.mulligan_manager.mulligan(player)
    
    message = {
        "type": "MULLIGAN_CHOICE",
        "seq_num": 3,
        "player_id": "player_1",
        "keep": True,
        "cards_to_bottom": []  # Should be 1 card
    }
    
    mulligan_choice(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_ACTION"
    print("   ✅ Wrong bottom count error detected")


def run_all_lobby_tests():
    """Run all lobby handler tests."""
    print("\n" + "="*60)
    print("TESTING LOBBY HANDLER")
    print("="*60)
    
    test_player_ready_success()
    test_player_ready_invalid_deck_size()
    test_player_ready_invalid_cards()
    test_player_ready_duplicate_id()
    test_mulligan_keep()
    test_mulligan_take()
    test_mulligan_keep_after_mulligan()
    test_mulligan_keep_wrong_bottom_count()
    
    print("\n" + "="*60)
    print("✅ ALL LOBBY HANDLER TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    run_all_lobby_tests()