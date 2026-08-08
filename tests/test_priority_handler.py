# tests/test_priority_handler.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from unittest.mock import Mock
from handlers.priority_handler import priority_pass
from models.player import Player
from engine.gamestate import GameState


class MockGameServer:
    def __init__(self):
        self.game_state = GameState()
        self.game = Mock()
        self.game.priority_manager = Mock()
        self.game.priority_manager.has_priority = Mock(return_value=True)
        self.game.pass_priority = Mock(return_value="ADVANCE_PHASE")
        self.errors = []
        self.broadcasts = []
        self.priority_grants = []
        
        self.p1 = Player(player_id="player_1", name="Alice")
        self.game_state.priority_seq_num = 5
        
        self.connection_player = {"player_1": "conn1"}
    
    def get_player(self, player_id):
        return self.p1
    
    def send_error(self, connection, code, message, rejected_action=None):
        self.errors.append({"code": code, "message": message})
    
    def _give_priority(self, player=None):
        self.priority_grants.append("priority_granted")
    
    def _broadcast_phase_transition(self):
        pass
    
    def _phase_has_priority(self):
        return True


def test_priority_pass_success():
    print("\n1. Testing PRIORITY_PASS - Success...")
    
    server = MockGameServer()
    
    message = {
        "type": "PRIORITY_PASS",
        "seq_num": 5,
        "player_id": "player_1"
    }
    
    priority_pass(server, message)
    
    assert len(server.errors) == 0
    print("   ✅ Priority pass successful")


def test_priority_pass_stale_action():
    print("\n2. Testing PRIORITY_PASS - Stale Action...")
    
    server = MockGameServer()
    
    message = {
        "type": "PRIORITY_PASS",
        "seq_num": 3,  # Wrong seq_num
        "player_id": "player_1"
    }
    
    priority_pass(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "STALE_ACTION"
    print("   ✅ Stale action error detected")


def run_all_tests():
    print("\n" + "="*60)
    print("TESTING PRIORITY HANDLER")
    print("="*60)
    
    test_priority_pass_success()
    test_priority_pass_stale_action()
    
    print("\n" + "="*60)
    print("✅ ALL PRIORITY HANDLER TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    run_all_tests()