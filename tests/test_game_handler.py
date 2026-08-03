# tests/test_game_handler.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.player import Player
from engine.game import Game
from handlers.game_handler import concede, game_over, phase_transition


class MockGameServer:
    def __init__(self):
        self.game = Game()
        self.game_state = self.game.game_state
        self.errors = []
        self.broadcasts = []
        
        self.p1 = Player(player_id="player_1", name="Alice")
        self.p2 = Player(player_id="player_2", name="Bob")
        self.game.add_player(self.p1)
        self.game.add_player(self.p2)
        self.game_state.active_player = self.p1
        
        self.connection_player = {"player_1": "conn1", "player_2": "conn2"}
        self.player_connections = {"conn1": "player_1", "conn2": "player_2"}
        self.game_over_called = False
        self.phase_transition_called = False
        self.priority_granted = False
        self.state_broadcast = False
    
    def send_error(self, connection, code, message):
        self.errors.append({"code": code, "message": message})
    
    def broadcast(self, message):
        self.broadcasts.append(message)
    
    def _end_game(self, loser_id, reason):
        self.game_over_called = True
    
    def _broadcast_phase_transition(self):
        self.phase_transition_called = True
    
    def _give_priority(self):
        self.priority_granted = True
    
    def _phase_has_priority(self):
        return True
    
    def _broadcast_personalized_state(self):
        self.state_broadcast = True


def test_concede():
    """Test CONCEDE handler."""
    print("\n1. Testing CONCEDE...")
    
    server = MockGameServer()
    
    message = {
        "type": "CONCEDE",
        "seq_num": 99,
        "player_id": "player_2"
    }
    
    concede(server, message)
    
    assert server.game_over_called == True
    assert len(server.broadcasts) >= 1
    print("   ✅ Concede handled")


def test_concede_invalid_player():
    """Test CONCEDE with invalid player."""
    print("\n2. Testing CONCEDE - Invalid Player...")
    
    server = MockGameServer()
    
    message = {
        "type": "CONCEDE",
        "seq_num": 99,
        "player_id": "invalid_player"
    }
    
    concede(server, message)
    
    assert len(server.errors) == 1
    assert server.errors[0]["code"] == "ILLEGAL_ACTION"
    print("   ✅ Invalid player error detected")


def test_game_over():
    """Test GAME_OVER handler."""
    print("\n3. Testing GAME_OVER...")
    
    server = MockGameServer()
    
    message = {
        "type": "GAME_OVER",
        "seq_num": 100,
        "winner_id": "player_1",
        "loser_id": "player_2",
        "reason": "LIFE_ZERO"
    }
    
    game_over(server, message)
    
    assert len(server.broadcasts) >= 1
    assert server.game_state.game_over == True
    print("   ✅ GAME_OVER processed")


def test_phase_transition():
    """Test PHASE_TRANSITION handler."""
    print("\n4. Testing PHASE_TRANSITION...")
    
    server = MockGameServer()
    
    message = {
        "type": "PHASE_TRANSITION",
        "seq_num": 10,
        "from_phase": "UPKEEP",
        "to_phase": "DRAW",
        "active_player": "player_1",
        "turn": 3
    }
    
    phase_transition(server, message)
    
    # Verify phase was updated
    assert server.game_state.current_phase == "DRAW"
    # Verify priority was granted
    assert server.priority_granted == True
    # Verify state was broadcast
    assert server.state_broadcast == True
    print("   ✅ PHASE_TRANSITION processed")


def run_all_game_tests():
    """Run all game handler tests."""
    print("\n" + "="*60)
    print("TESTING GAME HANDLER")
    print("="*60)
    
    test_concede()
    test_concede_invalid_player()
    test_game_over()
    test_phase_transition()
    
    print("\n" + "="*60)
    print("✅ ALL GAME HANDLER TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    run_all_game_tests()