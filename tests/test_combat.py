from engine.gamestate import GameState
from engine.combat import CombatManager

from models.player import Player
from models.card import Card



game = GameState()

combat = CombatManager(game)

p1 = Player("0","P1")

p2 = Player("0","P2")

game.add_player(p1)

game.add_player(p2)

game.active_player = p1

goblin = Card(
    id="1",
    name="Goblin",
    card_type="Creature",
    power=2,
    toughness=2
)

bear = Card(
    id="2",
    name="Bear",
    card_type="Creature",
    power=2,
    toughness=2
)

p1.battlefield.add(goblin)

p2.battlefield.add(bear)

combat.declare_attackers(p1, [goblin])

combat.declare_blocker(
    p2,
    bear,
    goblin
)

combat.resolve_combat()

print(len(p1.graveyard))

print(len(p2.graveyard))