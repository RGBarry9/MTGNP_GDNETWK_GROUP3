# test_effect_manager.py
from effects.effect_manager import EffectManager
from engine.gamestate import GameState
from models.player import Player
from models.card import Card

def test_effect_manager():
    # Create game state
    game = GameState()
    
    # Create players
    p1 = Player(player_id="player_1", name="Alice")
    p2 = Player(player_id="player_2", name="Bob")
    game.add_player(p1)
    game.add_player(p2)
    
    # Create effect manager
    em = EffectManager(game)
    
    # Test damage effect
    damage_spec = {
        "effect_type": "DAMAGE",
        "target": "player_2",
        "amount": 3
    }
    result = em.apply(damage_spec)
    print(f"Damage result: {result}")
    print(f"P2 life: {p2.life}")  # 17
    
    # Test gain life effect
    gain_spec = {
        "effect_type": "GAIN_LIFE",
        "target": "player_1",
        "amount": 2
    }
    result = em.apply(gain_spec)
    print(f"Gain life result: {result}")
    print(f"P1 life: {p1.life}")  # 22
    
    # Test multiple effects
    specs = [
        {"effect_type": "DAMAGE", "target": "player_2", "amount": 1},
        {"effect_type": "DAMAGE", "target": "player_2", "amount": 2}
    ]
    results = em.apply_all(specs)
    print(f"Multiple effects results: {results}")
    print(f"P2 final life: {p2.life}")  # 14