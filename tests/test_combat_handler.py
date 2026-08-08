# tests/test_combat_handler.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock, MagicMock
from models.player import Player
from models.card import Card
from engine.game import Game
from engine.combat import CombatManager
from engine.validator import GameValidator
from handlers.combat_handler import declare_attackers, declare_blockers, assign_damage_order
from config.enums import Phase


class MockGameServer:
    """Mock GameServer with real game objects for testing."""
    
    def __init__(self):
        # Use real Game with real components
        self.game = Game()
        self.game_state = self.game.game_state
        
        # Add validator - this is what was missing!
        self.validator = GameValidator(self.game_state)
        
        # Create real players
        self.p1 = Player(player_id="player_1", name="Alice")
        self.p2 = Player(player_id="player_2", name="Bob")
        self.game.add_player(self.p1)
        self.game.add_player(self.p2)
        self.game_state.active_player = self.p1
        self.game_state.current_phase = Phase.DECLARE_ATTACKERS
        
        # Create real creatures
        self.goblin = Card(
            card_id="goblin_001",
            name="Goblin Guide",
            card_type="Creature",
            power=2,
            toughness=2,
            keywords=["Haste"]
        )
        self.bear = Card(
            card_id="bear_001",
            name="Grizzly Bears",
            card_type="Creature",
            power=2,
            toughness=2
        )
        
        # Add creatures to battlefield
        self.p1.battlefield.add(self.goblin)
        self.p2.battlefield.add(self.bear)
        
        self.connection_player = {"player_1": "conn1", "player_2": "conn2"}
        self.errors = []
        self.broadcasts = []
        self.state_updates = []
        self.priority_grants = []
    
    def get_player(self, player_id):
        return self.game_state.get_player(player_id)
    
    def send_error(self, connection, code, message):
        self.errors.append({"code": code, "message": message})
    
    def broadcast(self, message):
        self.broadcasts.append(message)
    
    def _broadcast_personalized_state(self):
        self.state_updates.append("state_broadcast")
    
    def _give_priority(self, player=None):
        self.priority_grants.append("priority_granted")
    
    def _resolve_combat(self):
        pass


def test_declare_attackers_success():
    """Test successful attacker declaration."""
    print("\n1. Testing DECLARE_ATTACKERS - Success...")
    
    server = MockGameServer()
    
    message = {
        "type": "DECLARE_ATTACKERS",
        "seq_num": 22,
        "player_id": "player_1",
        "attackers": [
            {"creature_id": "goblin_001", "target": "player_2"}
        ]
    }
    
    declare_attackers(server, message)
    
    # Verify attackers were declared in game state
    assert len(server.game_state.attackers) == 1
    assert server.game_state.attackers[0].card_id == "goblin_001"
    assert server.game_state.attackers[0].is_tapped() == True
    assert len(server.errors) == 0
    print("   ✅ Attackers declared successfully")


def test_declare_attackers_wrong_phase():
    """Test attacker declaration in wrong phase."""
    print("\n2. Testing DECLARE_ATTACKERS - Wrong Phase...")
    
    server = MockGameServer()
    server.game_state.current_phase = Phase.PRECOMBAT_MAIN
    
    message = {
        "type": "DECLARE_ATTACKERS",
        "seq_num": 22,
        "player_id": "player_1",
        "attackers": [
            {"creature_id": "goblin_001", "target": "player_2"}
        ]
    }
    
    declare_attackers(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "WRONG_PHASE"
    print("   ✅ Wrong phase error detected")


def test_declare_attackers_invalid_creature():
    """Test attacker declaration with invalid creature."""
    print("\n3. Testing DECLARE_ATTACKERS - Invalid Creature...")
    
    server = MockGameServer()
    server.game_state.current_phase = Phase.DECLARE_ATTACKERS
    
    message = {
        "type": "DECLARE_ATTACKERS",
        "seq_num": 22,
        "player_id": "player_1",
        "attackers": [
            {"creature_id": "invalid_creature", "target": "player_2"}
        ]
    }
    
    declare_attackers(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_ACTION"
    print("   ✅ Invalid creature error detected")


def test_declare_attackers_tapped_creature():
    """Test attacker declaration with tapped creature."""
    print("\n4. Testing DECLARE_ATTACKERS - Tapped Creature...")
    
    server = MockGameServer()
    server.goblin.tap()
    server.game_state.current_phase = Phase.DECLARE_ATTACKERS
    
    message = {
        "type": "DECLARE_ATTACKERS",
        "seq_num": 22,
        "player_id": "player_1",
        "attackers": [
            {"creature_id": "goblin_001", "target": "player_2"}
        ]
    }
    
    declare_attackers(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_ACTION"
    print("   ✅ Tapped creature error detected")


def test_declare_blockers_success():
    """Test successful blocker declaration."""
    print("\n5. Testing DECLARE_BLOCKERS - Success...")
    
    server = MockGameServer()
    
    # Set up combat state
    server.game_state.attackers = [server.goblin]
    server.game_state.current_phase = Phase.DECLARE_BLOCKERS
    
    message = {
        "type": "DECLARE_BLOCKERS",
        "seq_num": 24,
        "player_id": "player_2",
        "blockers": [
            {"creature_id": "bear_001", "blocking_id": "goblin_001"}
        ]
    }
    
    declare_blockers(server, message)
    
    # Verify blocker was assigned
    assert len(server.game_state.blockers) == 1
    assert server.game_state.blockers.get("goblin_001") is not None
    assert len(server.errors) == 0
    print("   ✅ Blockers declared successfully")


def test_declare_blockers_wrong_player():
    """Test blocker declaration by wrong player."""
    print("\n6. Testing DECLARE_BLOCKERS - Wrong Player...")
    
    server = MockGameServer()
    server.game_state.current_phase = Phase.DECLARE_BLOCKERS
    
    # Player 1 is the active player, trying to block
    message = {
        "type": "DECLARE_BLOCKERS",
        "seq_num": 24,
        "player_id": "player_1",
        "blockers": [
            {"creature_id": "goblin_001", "blocking_id": "bear_001"}
        ]
    }
    
    declare_blockers(server, message)
    
    # Should get an error because player_1 doesn't have a creature with that ID
    assert len(server.errors) >= 1
    print("   ✅ Wrong player/creature error detected")


def test_declare_blockers_tapped_blocker():
    """Test blocker declaration with tapped blocker."""
    print("\n7. Testing DECLARE_BLOCKERS - Tapped Blocker...")
    
    server = MockGameServer()
    server.bear.tap()
    server.game_state.attackers = [server.goblin]
    server.game_state.current_phase = Phase.DECLARE_BLOCKERS
    
    message = {
        "type": "DECLARE_BLOCKERS",
        "seq_num": 24,
        "player_id": "player_2",
        "blockers": [
            {"creature_id": "bear_001", "blocking_id": "goblin_001"}
        ]
    }
    
    declare_blockers(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_ACTION"
    print("   ✅ Tapped blocker error detected")


def run_all_combat_tests():
    """Run all combat handler tests."""
    print("\n" + "="*60)
    print("TESTING COMBAT HANDLER")
    print("="*60)
    
    test_declare_attackers_success()
    test_declare_attackers_wrong_phase()
    test_declare_attackers_invalid_creature()
    test_declare_attackers_tapped_creature()
    test_declare_blockers_success()
    test_declare_blockers_wrong_player()
    test_declare_blockers_tapped_blocker()
    
    print("\n" + "="*60)
    print("✅ ALL COMBAT HANDLER TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    run_all_combat_tests()