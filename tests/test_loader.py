# tests/test_loader.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from game.loader import CardLoader, load_cards


def test_loader():
    """Test the CardLoader."""
    print("\n" + "="*60)
    print("TESTING CARD LOADER")
    print("="*60)
    
    # Test 1: Load cards from file
    print("\n1. Loading cards from cards.json...")
    loader = CardLoader()
    cards = loader.load("game/cards.json")
    assert len(cards) > 0, "No cards loaded!"
    print(f"   ✅ Loaded {len(cards)} cards")
    
    # Test 2: Get a specific card
    print("\n2. Getting a specific card...")
    bolt = loader.get_card("lightning_bolt_001")
    assert bolt is not None, "Card not found!"
    assert bolt.name == "Lightning Bolt"
    assert bolt.mana_cost == "R"
    print(f"   ✅ Found: {bolt.name} (Cost: {bolt.mana_cost})")
    
    # Test 3: Get by type
    print("\n3. Getting cards by type...")
    creatures = loader.get_cards_by_type("Creature")
    lands = loader.get_cards_by_type("Land")
    instants = loader.get_cards_by_type("Instant")
    print(f"   ✅ Creatures: {len(creatures)}")
    print(f"   ✅ Lands: {len(lands)}")
    print(f"   ✅ Instants: {len(instants)}")
    
    # Test 4: Get by color
    print("\n4. Getting cards by color...")
    red = loader.get_cards_by_color("R")
    green = loader.get_cards_by_color("G")
    black = loader.get_cards_by_color("B")
    print(f"   ✅ Red cards: {len(red)}")
    print(f"   ✅ Green cards: {len(green)}")
    print(f"   ✅ Black cards: {len(black)}")
    
    # Test 5: Validate deck
    print("\n5. Validating a deck...")
    deck_ids = ["mountain_001", "mountain_002", "goblin_guide_001", "lightning_bolt_001"]
    valid, invalid = loader.validate_deck(deck_ids)
    assert valid == True, f"Invalid cards: {invalid}"
    print(f"   ✅ Deck is valid ({len(deck_ids)} cards)")
    
    # Test 6: Validate invalid deck
    print("\n6. Validating an invalid deck...")
    invalid_ids = ["mountain_001", "fake_card_001", "goblin_guide_001"]
    valid, invalid = loader.validate_deck(invalid_ids)
    assert valid == False, "Should have invalid cards!"
    print(f"   ✅ Found invalid cards: {invalid}")
    
    # Test 7: Print summary
    print("\n7. Printing summary...")
    loader.print_summary()
    
    # Test 8: Convenience function
    print("\n8. Testing convenience function...")
    cards = load_cards("game/cards.json")
    assert len(cards) > 0, "Convenience function failed!"
    print(f"   ✅ load_cards() loaded {len(cards)} cards")
    
    print("\n" + "="*60)
    print("✅ ALL LOADER TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_loader()