# test_damage.py
from effects.damage import apply
from models.player import Player
from models.card import Card

def test_damage():
    # Test player damage
    p1 = Player(player_id="player_1", name="Alice")
    result = apply(p1, 3)
    print(f"Player damage: {result}")
    print(f"Player life: {p1.life}")  # 17

    # Test creature damage
    goblin = Card(
        card_id="goblin_001",
        name="Goblin Guide",
        card_type="Creature",
        power=2,
        toughness=2
    )
    result = apply(goblin, 2)
    print(f"Creature damage: {result}")
    print(f"Creature damage_marked: {goblin.damage_marked}")  # 2
    print(f"Is destroyed: {goblin.is_destroyed()}")  # True (2 >= 2)