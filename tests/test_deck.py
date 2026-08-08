# tests/test_deck.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.deck import Deck
from models.card import Card


def test_deck():
    """Test the Deck model."""
    print("\n" + "="*60)
    print("TESTING DECK MODEL")
    print("="*60)

    # Test 1: Create empty deck
    print("\n1. Creating empty deck...")
    deck = Deck()
    assert deck.is_empty() == True
    assert deck.is_valid() == False  # Empty deck is invalid
    print(f"   ✅ Empty deck created (size={len(deck)})")

    # Test 2: Add cards
    print("\n2. Adding cards...")
    cards = []
    for i in range(5):
        card = Card(
            card_id=f"card_{i:03d}",
            name=f"Card {i}",
            card_type="Creature" if i % 2 == 0 else "Land",
            colors=["R"] if i % 2 == 0 else ["G"]
        )
        cards.append(card)
    
    deck.add_cards(cards)
    print(f"   ✅ Added {len(cards)} cards (size={len(deck)})")

    # Test 3: Validate
    print("\n3. Validating deck...")
    assert deck.is_valid() == True
    error = deck.get_validation_error()
    assert error is None
    print(f"   ✅ Deck is valid")

    # Test 4: Count by type
    print("\n4. Counting by type...")
    creatures = deck.count_by_type("Creature")
    lands = deck.count_by_type("Land")
    print(f"   ✅ Creatures: {creatures}, Lands: {lands}")
    assert creatures == 3
    assert lands == 2

    # Test 5: Count by color
    print("\n5. Counting by color...")
    red = deck.count_by_color("R")
    green = deck.count_by_color("G")
    print(f"   ✅ Red: {red}, Green: {green}")

    # Test 6: Draw
    print("\n6. Drawing cards...")
    card = deck.draw()
    print(f"   ✅ Drew: {card.name}")
    assert len(deck) == 4

    # Test 7: Clone
    print("\n7. Cloning deck...")
    clone = deck.clone()
    print(f"   ✅ Clone created (size={len(clone)})")
    assert len(clone) == len(deck)

    # Test 8: To library
    print("\n8. Converting to library...")
    library = deck.to_library()
    print(f"   ✅ Library created (size={len(library)})")

    # Test 9: Deck validation
    print("\n9. Testing deck validation...")
    # Try to create a deck with 51 cards (should be invalid)
    big_deck = Deck()
    for i in range(51):
        card = Card(
            card_id=f"big_{i:03d}",
            name=f"Big Card {i}",
            card_type="Creature"
        )
        big_deck.add(card)
    
    assert big_deck.is_valid() == False
    error = big_deck.get_validation_error()
    assert error is not None
    print(f"   ✅ Invalid deck detected: {error}")

    print("\n" + "="*60)
    print("✅ ALL DECK TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_deck()