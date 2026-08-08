# test_priority.py
from engine.priority import PriorityManager
from engine.gamestate import GameState
from models.player import Player

def test_priority():
    # Create game state
    game = GameState()
    priority = PriorityManager(game)
    
    # Create players
    p1 = Player(player_id="player_1", name="Alice")
    p2 = Player(player_id="player_2", name="Bob")
    game.add_player(p1)
    game.add_player(p2)
    
    # Give priority to p1
    priority.give_priority(p1)
    assert priority.has_priority(p1) == True
    assert priority.get_priority_seq_num() == 1
    
    # Pass priority to p2
    result = priority.pass_priority(p1)
    assert result == "NEXT_PLAYER"
    assert priority.has_priority(p2) == True
    assert priority.get_priority_seq_num() == 1  # Seq num doesn't change on pass
    
    # Pass priority with empty stack (both passed)
    result = priority.pass_priority(p2)
    assert result == "ADVANCE_PHASE"
    
    # Validate sequence number
    assert priority.validate_seq_num(1) == True
    assert priority.validate_seq_num(2) == False
    
    print("✅ All priority tests passed!")