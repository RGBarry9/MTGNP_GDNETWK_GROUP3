"""
Application Configuration
MTGNP v1.0
"""


# Networking

HOST = "127.0.0.1"
PORT = 4444
MAX_PLAYERS = 2
BUFFER_SIZE = 4096
MESSAGE_LENGTH_BYTES = 4
ENCODING = "utf-8"

# End of Networking


# Timeouts

PRIORITY_TIMEOUT_MS = 60000
PING_INTERVAL = 30
PONG_TIMEOUT = 10

# End of Timeouts


# Game Rules

STARTING_LIFE = 20
STARTING_HAND_SIZE = 7
MAX_HAND_SIZE = 7
MIN_DECK_SIZE = 1
MAX_DECK_SIZE = 50

# End of Game Rules


# Gameplay

LANDS_PER_TURN = 1
FIRST_PLAYER_DRAWS = False

# End of Gameplay


# Card Database

CARD_DATABASE = "cards/cards.json"

# End of Card Database


# Logging

LOG_LEVEL = "INFO"

# End of Logging