class Dispatcher:
    """
    Routes incoming messages to their registered handler.
    """

    def __init__(self):
        self.handlers = {}

    def register(self, message_type, handler):
        """
        Register a handler for a specific message type.
        """
        self.handlers[message_type] = handler

    def dispatch(self, message):
        """
        Dispatch a message to its handler.
        """
        message_type = message.get("type")

        handler = self.handlers.get(message_type)

        if handler is None:
            print(f"No handler registered for '{message_type}'.")
            return

        handler(message)