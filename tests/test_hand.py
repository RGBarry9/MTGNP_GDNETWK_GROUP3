# test_hand.py
from models.hand import Hand
from models.card import Card

def test_hand():
    hand = Hand()
    
    # Create cards
    bolt = Card(
        card_id="lightning_bolt_001",
        name="Lightning Bolt",
        card_type="Instant"
    )
    
    mountain = Card(
        card_id="mountain_001",
        name="Mountain",
        card_type="Land"
    )
    
    # Add cards
    hand.add(bolt)
    hand.add(mountain)
    
    print(f"Hand size: {len(hand)}")  # 2
    print(f"Card IDs: {hand.get_card_ids()}")  # ['lightning_bolt_001', 'mountain_001']
    
    # Remove by ID
    card = hand.remove_by_id("lightning_bolt_001")
    print(f"Removed: {card.name}")  # Lightning Bolt
    print(f"Hand size: {len(hand)}")  # 1
    
    # Check contains
    print(f"Contains Mountain: {hand.contains(mountain)}")  # True
    print(f"Contains Bolt: {hand.contains(bolt)}")  # False