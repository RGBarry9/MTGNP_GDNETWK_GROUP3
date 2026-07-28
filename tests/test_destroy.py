# test_destroy.py
from effects.destroy import apply
from engine.gamestate import GameState
from models.player import Player
from models.card import Card

def test_destroy():
    # Create game state
    game = GameState()
    
    # Create players
    p1 = Player(player_id="player_1", name="Alice")
    p2 = Player(player_id="player_2", name="Bob")
    game.add_player(p1)
    game.add_player(p2)
    
    # Create creature
    goblin = Card(
        card_id="goblin_001",
        name="Goblin Guide",
        card_type="Creature",
        power=2,
        toughness=2,
        owner="player_1",
        controller="player_1"
    )
    
    # Add to battlefield
    p1.battlefield.add(goblin)
    
    print(f"Before: Battlefield size={len(p1.battlefield)}")  # 1
    print(f"Before: Graveyard size={len(p1.graveyard)}")  # 0
    
    # Destroy creature
    result = apply(game, goblin)
    
    print(f"After: Battlefield size={len(p1.battlefield)}")  # 0
    print(f"After: Graveyard size={len(p1.graveyard)}")  # 1
    print(f"Result: {result}")