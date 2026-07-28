# test_library.py
from models.library import Library
from models.card import Card

def test_library():
    lib = Library()
    
    # Create cards
    cards = []
    for i in range(10):
        card = Card(
            card_id=f"card_{i:03d}",
            name=f"Card {i}",
            card_type="Creature"
        )
        cards.append(card)
    
    # Add cards
    lib.add_cards(cards)
    print(f"Library size: {len(lib)}")  # 10
    
    # Shuffle
    lib.shuffle()
    print(f"Shuffled: {lib.cards != cards}")  # True (likely)
    
    # Peek top
    top = lib.peek_top(3)
    print(f"Top 3: {[c.name for c in top]}")
    
    # Draw
    card = lib.draw()
    print(f"Drew: {card.name}")
    print(f"Size after draw: {len(lib)}")  # 9
    
    # Draw multiple
    drawn = lib.draw_multiple(3)
    print(f"Drew 3 more: {[c.name for c in drawn]}")
    print(f"Size after draw: {len(lib)}")  # 6
    
    # Check empty
    print(f"Is empty: {lib.is_empty()}")  # False