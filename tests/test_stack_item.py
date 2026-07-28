# test_stack_item.py
from models.stack_item import StackItem, StackItemType, StackItemStatus
from models.card import Card

def test_stack_item():
    # Create a source card
    bolt = Card(
        card_id="lightning_bolt_001",
        name="Lightning Bolt",
        card_type="Instant",
        colors=["R"],
        effects=[{"effect_type": "DAMAGE", "amount": 3}]
    )

    # Create a stack item
    item = StackItem(
        stack_item_id="stk_001",
        item_type=StackItemType.SPELL,
        source=bolt,
        source_id=bolt.card_id,
        source_name=bolt.name,
        controller="player_1",
        targets=["player_2"],
        effects=bolt.effects
    )

    print(f"Stack item: {item}")
    print(f"Is spell: {item.is_spell}")
    print(f"Has targets: {item.has_targets}")
    print(f"Status: {item.status.value}")

    # Validate targets
    valid_targets = ["player_1", "player_2"]
    print(f"Targets valid: {item.validate_targets(valid_targets)}")

    # Mark resolved
    item.mark_resolved()
    print(f"After resolve: {item.status.value}")

    # Convert to dict (for PDU)
    print(f"To dict: {item.to_dict()}")