# tests/test_cards.py
import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.card import Card
from models.ability import Ability


def test_card():
    """Test the Card model."""
    print("\n" + "="*60)
    print("TESTING CARD MODEL")
    print("="*60)

    # Test 1: Basic card creation
    print("\n1. Testing basic card creation...")
    bolt = Card(
        card_id="lightning_bolt_001",
        name="Lightning Bolt",
        card_type="Instant",
        mana_cost="R",
        text="Deal 3 damage to any target.",
        colors=["R"],
        effects=[{"effect_type": "DAMAGE", "amount": 3}]
    )
    assert bolt.card_id == "lightning_bolt_001"
    assert bolt.name == "Lightning Bolt"
    assert bolt.is_instant() == True
    assert bolt.is_spell() == True
    assert bolt.is_permanent() == False
    print(f"   ✅ {bolt.name} created successfully")

    # Test 2: Creature card
    print("\n2. Testing creature card creation...")
    goblin = Card(
        card_id="goblin_guide_001",
        name="Goblin Guide",
        card_type="Creature",
        mana_cost="R",
        power=2,
        toughness=2,
        keywords=["Haste"]
    )
    assert goblin.is_creature() == True
    assert goblin.has_haste() == True
    assert goblin.power == 2
    assert goblin.toughness == 2
    print(f"   ✅ {goblin.name} ({goblin.power}/{goblin.toughness}) created")

    # Test 3: Damage tracking
    print("\n3. Testing damage tracking...")
    goblin.mark_damage(1)
    assert goblin.damage_marked == 1
    assert goblin.is_destroyed() == False
    print(f"   ✅ After 1 damage: {goblin.damage_marked} damage, destroyed={goblin.is_destroyed()}")

    goblin.mark_damage(1)
    assert goblin.damage_marked == 2
    assert goblin.is_destroyed() == True
    print(f"   ✅ After 2 damage: {goblin.damage_marked} damage, destroyed={goblin.is_destroyed()}")

    goblin.heal_damage()
    assert goblin.damage_marked == 0
    assert goblin.is_destroyed() == False
    print(f"   ✅ After healing: {goblin.damage_marked} damage")

    # Test 4: Clone
    print("\n4. Testing clone...")
    clone = goblin.clone()
    assert clone.card_id == goblin.card_id
    assert clone.name == goblin.name
    assert clone.summoning_sick == True
    assert clone.damage_marked == 0
    assert clone.tapped == False
    print(f"   ✅ Clone of {goblin.name} created")

    # Test 5: Reset
    print("\n5. Testing reset...")
    goblin.tap()
    goblin.summoning_sick = True
    goblin.mark_damage(1)
    goblin.reset()
    assert goblin.tapped == False
    assert goblin.summoning_sick == False
    assert goblin.damage_marked == 0
    print(f"   ✅ Reset successful")

    print("\n" + "="*60)
    print("✅ ALL TESTS PASSED!")
    print("="*60)


if __name__ == "__main__":
    test_card()