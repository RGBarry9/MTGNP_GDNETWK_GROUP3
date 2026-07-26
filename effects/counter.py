def apply(stack, stack_item_id, source=None):

    for item in stack:

        if item.get("stack_item_id") == stack_item_id:

            stack.remove(item)

            return item

    return None
