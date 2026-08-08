# test_discard.py
from effects.discard import apply, discard_all, discard_to_size
from models.player import Player
from models.card import Card

def test_discard():
    # Create player
    p1 = Player(player_id="player_1", name="Alice")
    
    # Add cards to hand
    cards = []
    for i in range(5):
        card = Card(
            card_id=f"card_{i:03d}",
            name=f"Card {i}",
            card_type="Creature"
        )
        cards.append(card)
        p1.hand.add(card)
    
    print(f"Before: Hand size={len(p1.hand)}")  # 5
    print(f"Before: Graveyard size={len(p1.graveyard)}")  # 0
    
    # Discard 2 cards
    result = apply(p1, ["card_001", "card_003"])
    
    print(f"After: Hand size={len(p1.hand)}")  # 3
    print(f"After: Graveyard size={len(p1.graveyard)}")  # 2
    print(f"Result: {result}")
    
    # Discard all
    result = discard_all(p1)
    print(f"After discard all: Hand size={len(p1.hand)}")  # 0
    print(f"After discard all: Graveyard size={len(p1.graveyard)}")  # 5