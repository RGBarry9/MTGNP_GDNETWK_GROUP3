# effects/counter.py
"""
Counter effect.

Counters a target spell on the stack. The spell is removed from the stack
without resolving (fizzled).
"""

from typing import Optional, Dict, Any, List
from models.stack_item import StackItem, StackItemStatus


def apply(stack: List[StackItem], stack_item_id: str, source=None) -> Optional[Dict[str, Any]]:
    """
    Counter a spell on the stack.
    
    Args:
        stack: The stack list
        stack_item_id: ID of the spell to counter
        source: The source of the counter effect (optional)
        
    Returns:
        Optional[Dict[str, Any]]: State change dictionary for STACK_RESOLVE PDU,
                                  or None if the spell wasn't found
    """
    # Find the item on the stack
    target_item = None
    for item in stack:
        if item.stack_item_id == stack_item_id:
            target_item = item
            break
    
    if target_item is None:
        return None
    
    # Mark as fizzled (countered) and remove from stack
    target_item.mark_fizzled()
    stack.remove(target_item)
    
    # Return state change for STACK_RESOLVE
    return {
        "change_type": "COUNTER",
        "target": stack_item_id,
        "spell_name": target_item.source_name,
        "controller": target_item.controller,
        "source": getattr(source, 'card_id', 'unknown') if source else 'unknown'
    }


def can_counter(target_item: StackItem) -> bool:
    """
    Check if a stack item can be countered.
    
    Args:
        target_item: The stack item to check
        
    Returns:
        bool: True if the item can be countered
    """
    # Spells can be countered
    if target_item.is_spell:
        return True
    
    # Some abilities can be countered (activated/triggered)
    # In MTG, most abilities can't be countered, but some can
    # For MTGNP v1.0, we'll keep it simple
    
    return target_item.is_spell