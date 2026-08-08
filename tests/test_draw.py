# test_draw.py
from effects.draw import apply
from models.player import Player
from models.card import Card

def test_draw():
    # Create player
    p1 = Player(player_id="player_1", name="Alice")
    
    # Add cards to library (not deck!)
    for i in range(5):
        card = Card(
            card_id=f"card_{i:03d}",
            name=f"Card {i}",
            card_type="Creature"
        )
        p1.library.add(card)  # ← Add to library
    
    print(f"Before: Library size={len(p1.library)}")  # 5
    print(f"Before: Hand size={len(p1.hand)}")  # 0
    
    # Draw 3 cards
    result = apply(p1, 3)
    
    print(f"After: Library size={len(p1.library)}")  # 2
    print(f"After: Hand size={len(p1.hand)}")  # 3
    print(f"Result: {result}")
    
    # Draw remaining cards
    result = apply(p1, 5)  # Try to draw 5, only 2 left
    print(f"After draw 5: Library size={len(p1.library)}")  # 0
    print(f"After draw 5: Hand size={len(p1.hand)}")  # 5
    print(f"Empty library: {result.get('empty_library')}")  # True