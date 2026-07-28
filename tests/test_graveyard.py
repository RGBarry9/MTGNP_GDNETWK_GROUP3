# test_graveyard.py
from models.graveyard import Graveyard
from models.card import Card

def test_graveyard():
    gy = Graveyard()
    
    # Create cards
    cards = []
    for i in range(5):
        card = Card(
            card_id=f"card_{i:03d}",
            name=f"Card {i}",
            card_type="Creature"
        )
        cards.append(card)
    
    # Add cards
    for card in cards:
        gy.add(card)
    
    print(f"Graveyard size: {len(gy)}")  # 5
    
    # Get latest
    latest = gy.get_latest(2)
    print(f"Latest 2: {[c.name for c in latest]}")  # ['Card 3', 'Card 4']
    
    # Get earliest
    earliest = gy.get_earliest(2)
    print(f"Earliest 2: {[c.name for c in earliest]}")  # ['Card 0', 'Card 1']
    
    # Get card IDs
    print(f"Card IDs: {gy.get_card_ids()}")
    
    # Check contains
    print(f"Contains Card 0: {gy.contains(cards[0])}")  # True