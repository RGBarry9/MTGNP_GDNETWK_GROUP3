# test_battlefield.py
from models.battlefield import Battlefield
from models.card import Card

def test_battlefield():
    bf = Battlefield()
    
    # Create creatures
    goblin = Card(
        card_id="goblin_001",
        name="Goblin Guide",
        card_type="Creature",
        power=2,
        toughness=2,
        keywords=["Haste"]
    )
    
    bear = Card(
        card_id="bear_001",
        name="Grizzly Bears",
        card_type="Creature",
        power=2,
        toughness=2
    )
    
    mountain = Card(
        card_id="mountain_001",
        name="Mountain",
        card_type="Land"
    )
    
    # Add cards
    bf.add(goblin)
    bf.add(bear)
    bf.add(mountain)
    
    print(f"Size: {len(bf)}")  # 3
    print(f"Creatures: {len(bf.get_creatures())}")  # 2
    print(f"Lands: {len(bf.get_lands())}")  # 1
    
    # Tap goblin
    goblin.tap()
    print(f"Untapped creatures: {len(bf.get_untapped_creatures())}")  # 1 (bear)
    print(f"Tapped creatures: {len(bf.get_tapped_creatures())}")  # 1 (goblin)