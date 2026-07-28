# test_player.py
from models.player import Player
from models.card import Card

def test_player():
    # Create player
    p1 = Player(player_id="player_1", name="Alice")
    print(f"Player: {p1.name} ({p1.player_id})")
    print(f"Life: {p1.life}")
    
    # Test life
    p1.gain_life(3)
    print(f"After gain 3: {p1.life}")  # 23
    p1.lose_life(5)
    print(f"After lose 5: {p1.life}")  # 18
    print(f"Is dead: {p1.is_dead()}")  # False
    
    # Test mana
    p1.add_mana("R", 2)
    p1.add_mana("G", 1)
    print(f"Mana pool: {p1.mana_pool}")  # {'R': 2, 'G': 1}
    p1.spend_mana("R", 1)
    print(f"After spending R: {p1.mana_pool}")  # {'R': 1, 'G': 1}
    
    # Test draw
    card = Card(
        card_id="test_001",
        name="Test Card",
        card_type="Land"
    )
    p1.library.add(card)
    drawn = p1.draw_card()
    print(f"Drawn: {drawn.name}")
    print(f"Hand size: {len(p1.hand)}")  # 1
    
    # Test reset turn
    p1.lands_played = 1
    p1.passed_priority = True
    p1.reset_turn()
    print(f"Lands played: {p1.lands_played}")  # 0
    print(f"Passed priority: {p1.passed_priority}")  # False