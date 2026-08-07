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
    """
    player_id = message.get("player_id")
    deck_list = message.get("deck_list", [])
    connection = game_server._find_connection(message)
    
    if not connection:
        return
    
    print(f"\n📥 PLAYER_READY from {player_id}")
    print(f"   Deck size: {len(deck_list)} cards")
    
    # Validate deck size (1-50 cards)
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
    
    # Validate cards exist in database
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
    
    # Check for duplicate player ID
    if player_id in game_server.connection_player:
        game_server.send_error(
            connection,
            "DUPLICATE_ID",
            f"Player ID '{player_id}' already taken"
        )
        return
    
    # Create player and build deck
    player = Player(player_id=player_id, name=player_id)

    deck = Deck()
    for card_id in deck_list:
        card_data = game_server.card_db[card_id]
    
        if hasattr(card_data, 'card_id'):
            card = card_data.clone() if hasattr(card_data, 'clone') else card_data
        else:
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
    
    # Add player to game
    if game_server.game and game_server.game.add_player(player):
        game_server.player_connections[connection] = player_id
        game_server.connection_player[player_id] = connection
        
        print(f"   ✅ Player {player_id} added with {len(deck_list)} cards")
        
        _broadcast_lobby_status(game_server)
        
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
    """
    player_id = message.get("player_id")
    keep = message.get("keep", True)
    cards_to_bottom = message.get("cards_to_bottom", [])
    
    # Get player
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
    
    # Handle keep decision
    if keep:
        mulligan_count = game_server.game.mulligan_manager.mulligan_count.get(player_id, 0)
        print(f"   🔍 DEBUG: mulligan_count = {mulligan_count}")
        
        if mulligan_count > 0:
            # ==========================================================
            # CRITICAL FIX: Auto-bottom cards if none specified
            # ==========================================================
            if len(cards_to_bottom) == 0:
                # Auto-bottom the last mulligan_count cards from hand
                print(f"   🔄 Auto-bottoming {mulligan_count} cards for {player_id}")
                hand_cards = list(player.hand)
                for i in range(min(mulligan_count, len(hand_cards))):
                    cards_to_bottom.append(hand_cards[-(i + 1)].card_id)
                print(f"   📥 Cards to bottom: {cards_to_bottom}")
            
            if len(cards_to_bottom) != mulligan_count:
                game_server.send_error(
                    game_server.connection_player.get(player_id),
                    "ILLEGAL_ACTION",
                    f"Need to bottom {mulligan_count} cards, got {len(cards_to_bottom)}"
                )
                return
            
            # Validate cards are in hand
            for card_id in cards_to_bottom:
                card = None
                for c in player.hand:
                    if c.card_id == card_id:
                        card = c
                        break
                
                if not card:
                    game_server.send_error(
                        game_server.connection_player.get(player_id),
                        "ILLEGAL_ACTION",
                        f"Card {card_id} not in hand"
                    )
                    return
            
            # Move cards to bottom of library
            for card_id in cards_to_bottom:
                for c in player.hand:
                    if c.card_id == card_id:
                        player.hand.remove(c)
                        player.library.add(c)
                        print(f"   📥 Bottomed {c.name}")
                        break
        
        # Mark player as finished with mulligan
        game_server.game.mulligan_manager.keep(player)
        print(f"   ✅ {player_id} kept hand after {mulligan_count} mulligan(s)")
    
    else:
        # Take mulligan
        game_server.game.mulligan_manager.mulligan(player)
        mulligan_count = game_server.game.mulligan_manager.mulligan_count.get(player_id, 0)
        print(f"   🔄 {player_id} took mulligan #{mulligan_count}")
        
        # Send updated hand to player
        game_server._broadcast_personalized_state()
    
    # ==========================================================
    # Check if all players finished mulligan
    # ==========================================================
    if game_server.game.mulligan_manager.all_players_finished():
        print("\n🎮 Mulligan complete! Starting game...")
        game_server._start_first_turn()
    
    # Broadcast updated state
    game_server._broadcast_personalized_state()


def _broadcast_lobby_status(game_server):
    """Broadcast lobby status to all connected players."""
    players_ready = len(game_server.connection_player)
    waiting_for = []
    
    for conn in game_server.connections:
        if conn not in game_server.player_connections:
            if len(waiting_for) == 0:
                waiting_for.append("Player 1")
            else:
                waiting_for.append("Player 2")
    
    if players_ready == len(game_server.connections) and len(game_server.connections) > 0:
        waiting_for = []
    
    if len(game_server.connections) == 0:
        waiting_for = ["Player 1", "Player 2"]
    
    status_msg = {
        "type": "GAME_STATE_UPDATE",
        "state": {
            "phase": "LOBBY",
            "players_ready": players_ready,
            "waiting_for": waiting_for
        }
    }
    
    for conn in game_server.connections:
        if hasattr(game_server, 'send_to_connection'):
            game_server.send_to_connection(conn, status_msg)
        else:
            conn.send(status_msg)