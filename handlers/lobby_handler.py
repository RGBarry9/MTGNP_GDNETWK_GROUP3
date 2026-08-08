# handlers/lobby_handler.py
"""
Lobby message handlers.

Handles PLAYER_READY and MULLIGAN_CHOICE PDUs during game setup.
"""

from models.player import Player
from models.deck import Deck
from models.card import Card
import random


def player_ready(game_server, message):
    """
    Handle PLAYER_READY PDU.
    
    Expected message format:
    {
        "type": "PLAYER_READY",
        "seq_num": 1,
        "player_id": "player_1",
        "deck_list": [
            "lightning_bolt_001",
            "mountain_001",
            "goblin_guide_001"
            // ... 1 to 50 cards
        ]
    }
    """
    player_id = message.get("player_id")
    deck_list = message.get("deck_list", [])
    connection = game_server._find_connection(message)
    
    if not connection:
        return
    
    # DEBUG: Print what we're receiving
    print(f"\n📥 PLAYER_READY from {player_id}")
    print(f"   Deck size: {len(deck_list)} cards")
    
    # ==========================================================
    # Step 1: Validate deck size (1-50 cards)
    # ==========================================================
    if len(deck_list) < 1:
        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            f"Deck has {len(deck_list)} cards; minimum is 1"
        )
        return
    
    if len(deck_list) > 50:
        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            f"Deck has {len(deck_list)} cards; maximum is 50"
        )
        return
    
    # ==========================================================
    # Step 2: Validate cards exist in database
    # ==========================================================
    invalid_cards = []
    for card_id in deck_list:
        if card_id not in game_server.card_db:
            invalid_cards.append(card_id)
    
    if invalid_cards:
        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            f"Invalid cards: {', '.join(invalid_cards[:5])}"
        )
        return
    
    # ==========================================================
    # Step 3: Check for duplicate player ID
    # ==========================================================
    # FIXED: Check if player_id is in the KEYS of connection_player
    if player_id in game_server.connection_player:  # ← FIXED
        game_server.send_error(
            connection,
            "DUPLICATE_ID",
            f"Player ID '{player_id}' already taken"
        )
        return
    
    # ==========================================================
    # Step 4: Create player and build deck
    # ==========================================================
    player = Player(player_id=player_id, name=player_id)
    
    # Build deck from card IDs
    deck = Deck()
    for card_id in deck_list:
        card_data = game_server.card_db[card_id]
        
        # Create card from data
        card = Card(
            card_id=card_id,
            name=card_data.get('name', card_id),
            card_type=card_data.get('card_type', ''),
            mana_cost=card_data.get('mana_cost', ''),
            text=card_data.get('text', ''),
            colors=card_data.get('colors', []),
            power=card_data.get('power'),
            toughness=card_data.get('toughness'),
            keywords=card_data.get('keywords', []),
            effects=card_data.get('effects', [])
        )
        deck.add(card)
    
    player.deck = deck
    player.set_ready()
    
    # ==========================================================
    # Step 5: Add player to game
    # ==========================================================
    if game_server.game and game_server.game.add_player(player):
        game_server.player_connections[connection] = player_id
        game_server.connection_player[player_id] = connection
        
        print(f"   ✅ Player {player_id} added with {len(deck_list)} cards")
        
        # Broadcast lobby status to all players
        _broadcast_lobby_status(game_server)
        
        # ==========================================================
        # Step 6: Check if all players are ready
        # ==========================================================
        if len(game_server.connection_player) == 2:
            print("\n🎮 Both players ready! Starting game setup...")
            game_server._start_game()
    else:
        game_server.send_error(
            connection,
            "ILLEGAL_ACTION",
            "Game is full or already started"
        )


def mulligan_choice(game_server, message):
    """
    Handle MULLIGAN_CHOICE PDU.
    
    Expected message format:
    {
        "type": "MULLIGAN_CHOICE",
        "seq_num": 3,
        "player_id": "player_1",
        "keep": true,
        "cards_to_bottom": ["shock_001"]
    }
    """
    player_id = message.get("player_id")
    keep = message.get("keep", True)
    cards_to_bottom = message.get("cards_to_bottom", [])
    
    # ==========================================================
    # Step 1: Get player
    # ==========================================================
    player = game_server.game.get_player(player_id)
    if not player:
        game_server.send_error(
            game_server.connection_player.get(player_id),
            "ILLEGAL_ACTION",
            f"Player {player_id} not found"
        )
        return
    
    print(f"\n📥 MULLIGAN_CHOICE from {player_id}")
    print(f"   Keep: {keep}")
    print(f"   Cards to bottom: {cards_to_bottom}")
    
    # ==========================================================
    # Step 2: Handle keep decision
    # ==========================================================
    if keep:
        # Get mulligan count for this player
        mulligan_count = game_server.game.mulligan_manager.mulligan_count.get(player_id, 0)

        # MulliganManager.keep() already validates the bottom-count,
        # validates each card is actually in hand, and moves them to
        # the bottom of the library - all in one place. (Previously
        # this handler duplicated that validation/bottoming here AND
        # called keep() afterwards, which then failed its own
        # "still in hand?" check because this code had already moved
        # the cards - silently leaving the player stuck, never marked
        # finished, even though the client was told "kept hand".)
        success = game_server.game.mulligan_manager.keep(player, cards_to_bottom)

        if not success:
            game_server.send_error(
                game_server.connection_player.get(player_id),
                "ILLEGAL_ACTION",
                f"Unable to keep hand: cards_to_bottom must contain exactly "
                f"{mulligan_count} card id(s) currently in your hand."
            )
            return

        # Mark player as finished with mulligan
        print(f"   ✅ {player_id} kept hand after {mulligan_count} mulligan(s)")
    
    else:
        # ==========================================================
        # Step 3: Handle mulligan (take a mulligan)
        # ==========================================================
        game_server.game.mulligan_manager.mulligan(player)
        mulligan_count = game_server.game.mulligan_manager.mulligan_count.get(player_id, 0)
        print(f"   🔄 {player_id} took mulligan #{mulligan_count}")
        
        # Send updated hand to player
        game_server._broadcast_personalized_state()
        return
    
    # ==========================================================
    # Step 4: Check if all players finished mulligan
    # ==========================================================
    if game_server.game.mulligan_manager.all_players_finished():
        print("\n🎮 Mulligan complete! Starting game...")
        game_server._start_first_turn()
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()


# ==========================================================
# Helper Functions
# ==========================================================

def _broadcast_lobby_status(game_server):
    """
    Broadcast lobby status to all connected players.
    """
    waiting_for = []
    connected_ids = set(game_server.connection_player.values())
    
    # Determine which players are waiting
    # In a real implementation, you'd track expected player IDs
    expected_players = ["player_1", "player_2"]
    for pid in expected_players:
        if pid not in connected_ids:
            waiting_for.append(pid)
    
    status_msg = {
        "type": "GAME_STATE_UPDATE",
        "state": {
            "phase": "LOBBY",
            "players_ready": len(game_server.connection_player),
            "waiting_for": waiting_for
        }
    }
    
    for conn in game_server.connections:
        game_server.send_to_connection(conn, status_msg)