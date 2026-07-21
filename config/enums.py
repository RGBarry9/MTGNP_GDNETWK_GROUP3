from enum import Enum


class GameState(Enum):
    LOBBY = "LOBBY"
    GAME_SETUP = "GAME_SETUP"
    MULLIGAN = "MULLIGAN"
    IN_GAME = "IN_GAME"
    GAME_OVER = "GAME_OVER"


class Phase(Enum):
    UNTAP = "UNTAP"
    UPKEEP = "UPKEEP"
    DRAW = "DRAW"

    PRECOMBAT_MAIN = "PRECOMBAT_MAIN"

    BEGIN_COMBAT = "BEGIN_COMBAT"
    DECLARE_ATTACKERS = "DECLARE_ATTACKERS"
    DECLARE_BLOCKERS = "DECLARE_BLOCKERS"
    ASSIGN_DAMAGE_ORDER = "ASSIGN_DAMAGE_ORDER"
    FIRST_STRIKE_DAMAGE = "FIRST_STRIKE_DAMAGE"
    COMBAT_DAMAGE = "COMBAT_DAMAGE"
    END_OF_COMBAT = "END_OF_COMBAT"

    POSTCOMBAT_MAIN = "POSTCOMBAT_MAIN"

    END_STEP = "END_STEP"
    CLEANUP = "CLEANUP"


class CardType(Enum):
    LAND = "Land"
    CREATURE = "Creature"
    INSTANT = "Instant"
    SORCERY = "Sorcery"
    ENCHANTMENT = "Enchantment"
    ARTIFACT = "Artifact"


class Color(Enum):
    WHITE = "W"
    BLUE = "U"
    BLACK = "B"
    RED = "R"
    GREEN = "G"
    COLORLESS = "C"


class StackItemType(Enum):
    SPELL = "SPELL"
    ABILITY = "ABILITY"
    TRIGGER_ABILITY = "TRIGGER_ABILITY"


class WinnerReason(Enum):
    LIFE_ZERO = "LIFE_ZERO"
    DECK_EMPTY = "DECK_EMPTY"
    CONCEDE = "CONCEDE"
    DISCONNECT = "DISCONNECT"