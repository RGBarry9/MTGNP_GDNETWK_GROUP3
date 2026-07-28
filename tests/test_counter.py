# test_counter.py
from effects.counter import apply
from models.stack_item import StackItem, StackItemType
from models.card import Card

def test_counter():
    # Create a stack with items
    stack = []
    
    bolt = Card(
        card_id="lightning_bolt_001",
        name="Lightning Bolt",
        card_type="Instant"
    )
    
    # Add a spell to the stack
    item = StackItem(
        stack_item_id="stk_001",
        item_type=StackItemType.SPELL,
        source=bolt,
        source_id=bolt.card_id,
        source_name=bolt.name,
        controller="player_1",
        targets=["player_2"]
    )
    stack.append(item)
    
    print(f"Stack size before: {len(stack)}")  # 1
    
    # Counter the spell
    result = apply(stack, "stk_001")
    
    print(f"Stack size after: {len(stack)}")  # 0
    print(f"Result: {result}")
    print(f"Change type: {result.get('change_type')}")  # COUNTER
    print(f"Target: {result.get('target')}")  # stk_001