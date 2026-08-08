# test_gain_life.py
from effects.gain_life import apply
from models.player import Player

def test_gain_life():
    # Create player
    p1 = Player(player_id="player_1", name="Alice")
    
    print(f"Before: Life={p1.life}")  # 20
    
    # Gain 5 life
    result = apply(p1, 5)
    
    print(f"After: Life={p1.life}")  # 25
    print(f"Result: {result}")
    
    # Try to gain 0 life (should return None)
    result = apply(p1, 0)
    print(f"Gain 0 result: {result}")  # None