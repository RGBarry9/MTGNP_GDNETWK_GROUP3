class Dispatcher:

    def __init__(self):

        self.handlers = {}

    def register(self, message_type, handler):

        self.handlers[message_type] = handler

    def dispatch(self, message):

        message_type = message["type"]

        handler = self.handlers.get(message_type)

        if handler:

            handler(message)

        else:

            print(f"No handler registered for {message_type}")