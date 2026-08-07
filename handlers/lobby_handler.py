from models.player import Player
from models.deck import Deck
from models.card import Card


def player_ready(game_server, message):

    player_id = message.get(
        "player_id"
    )

    deck_list = message.get(
        "deck_list",
        []
    )

    connection = (
        game_server._find_connection(
            message
        )
    )

    if not connection:
        return

    print(
        f"\nPLAYER_READY from {player_id}"
    )

    print(
        f"Deck size: {len(deck_list)}"
    )

    # ==========================================================
    # Validate player ID
    # ==========================================================

    if (
        not isinstance(
            player_id,
            str
        )
        or not player_id.strip()
    ):

        game_server.send_error(
            connection,
            "ILLEGAL_ACTION",
            "player_id must be a non-empty string",
            rejected_action=message
        )

        return

    # ==========================================================
    # Validate deck size
    # ==========================================================

    if len(deck_list) < 1:

        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            (
                f"Deck has "
                f"{len(deck_list)} cards; "
                "minimum is 1"
            ),
            rejected_action=message
        )

        return

    if len(deck_list) > 50:

        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            (
                f"Deck has "
                f"{len(deck_list)} cards; "
                "maximum is 50"
            ),
            rejected_action=message
        )

        return

    # ==========================================================
    # Validate cards
    # ==========================================================

    invalid_cards = []

    for card_id in deck_list:

        if card_id not in game_server.card_db:
            invalid_cards.append(
                card_id
            )

    if invalid_cards:

        game_server.send_error(
            connection,
            "ILLEGAL_DECK",
            (
                "Invalid cards: "
                + ", ".join(
                    invalid_cards[:5]
                )
            ),
            rejected_action=message
        )

        return

    # ==========================================================
    # Duplicate player ID
    # ==========================================================

    duplicate_id = False

    if player_id in game_server.connection_player:
        duplicate_id = True

    elif player_id in game_server.connection_player.values():
        duplicate_id = True

    if duplicate_id:

        game_server.send_error(
            connection,
            "DUPLICATE_ID",
            (
                f"Player ID "
                f"'{player_id}' "
                "already taken"
            ),
            rejected_action=message
        )

        return

    # ==========================================================
    # If this connection already submitted
    # a player, remove its previous player.
    # ==========================================================

    old_player_id = (
        game_server.player_connections.get(
            connection
        )
    )

    if (
        old_player_id
        and old_player_id != player_id
    ):

        old_player = (
            game_server.game.get_player(
                old_player_id
            )
        )

        if old_player:

            game_server.game.remove_player(
                old_player
            )

        game_server.connection_player.pop(
            old_player_id,
            None
        )

    # ==========================================================
    # Remove old player object if replacing
    # ==========================================================

    old_player = (
        game_server.game.get_player(
            player_id
        )
    )

    if old_player:

        game_server.game.remove_player(
            old_player
        )

    # ==========================================================
    # Build deck
    # ==========================================================

    deck = Deck()

    for card_id in deck_list:

        card_data = (
            game_server.card_db[
                card_id
            ]
        )

        # CardLoader returns Card objects.
        if isinstance(
            card_data,
            Card
        ):

            card = card_data.clone()

        else:

            card = Card(
                card_id=card_id,
                name=card_data.get(
                    "name",
                    card_id
                ),
                card_type=card_data.get(
                    "card_type",
                    ""
                ),
                mana_cost=card_data.get(
                    "mana_cost",
                    ""
                ),
                text=card_data.get(
                    "text",
                    ""
                ),
                colors=card_data.get(
                    "colors",
                    []
                ),
                power=card_data.get(
                    "power"
                ),
                toughness=card_data.get(
                    "toughness"
                ),
                keywords=card_data.get(
                    "keywords",
                    []
                ),
                effects=card_data.get(
                    "effects",
                    []
                )
            )

        deck.add(card)

    # ==========================================================
    # Create player
    # ==========================================================

    player = Player(
        player_id=player_id,
        name=player_id
    )

    player.deck = deck
    player.set_ready()

    # ==========================================================
    # Add player
    # ==========================================================

    if not game_server.game.add_player(
        player
    ):

        game_server.send_error(
            connection,
            "ILLEGAL_ACTION",
            "Game is full or already started",
            rejected_action=message
        )

        return

    # ==========================================================
    # Register connection
    # ==========================================================

    game_server.player_connections[
        connection
    ] = player_id

    game_server.connection_player[
        player_id
    ] = connection

    print(
        f"Player {player_id} added."
    )

    # ==========================================================
    # Lobby update
    # ==========================================================

    game_server._broadcast_lobby_status()

    # ==========================================================
    # Start game if both players are ready
    # ==========================================================

    if (
        len(
            game_server.connection_player
        ) == 2
        and game_server.game.players_ready()
    ):

        print(
            "\nBoth players ready! "
            "Starting game setup..."
        )

        game_server._start_game()


def mulligan_choice(
    game_server,
    message
):

    player_id = message.get(
        "player_id"
    )

    keep = message.get(
        "keep",
        True
    )

    cards_to_bottom = message.get(
        "cards_to_bottom",
        []
    )

    connection = (
        game_server._find_connection(
            message
        )
    )

    player = (
        game_server.game.get_player(
            player_id
        )
    )

    if not player:

        game_server.send_error(
            connection,
            "ILLEGAL_ACTION",
            f"Player {player_id} not found",
            rejected_action=message
        )

        return

    print(
        f"\nMULLIGAN_CHOICE "
        f"from {player_id}"
    )

    # ==========================================================
    # KEEP
    # ==========================================================

    if keep:

        mulligan_count = (
            game_server.game
            .mulligan_manager
            .mulligan_count
            .get(
                player_id,
                0
            )
        )

        if (
            len(cards_to_bottom)
            != mulligan_count
        ):

            game_server.send_error(
                connection,
                "ILLEGAL_ACTION",
                (
                    f"Need to bottom "
                    f"{mulligan_count} "
                    f"cards, got "
                    f"{len(cards_to_bottom)}"
                ),
                rejected_action=message
            )

            return

        success = (
            game_server.game
            .mulligan_manager
            .keep(
                player,
                cards_to_bottom
            )
        )

        if not success:

            game_server.send_error(
                connection,
                "ILLEGAL_ACTION",
                "Invalid mulligan choice",
                rejected_action=message
            )

            return

    # ==========================================================
    # MULLIGAN
    # ==========================================================

    else:

        success = (
            game_server.game
            .mulligan_manager
            .mulligan(
                player
            )
        )

        if not success:

            game_server.send_error(
                connection,
                "ILLEGAL_ACTION",
                "Unable to mulligan",
                rejected_action=message
            )

            return

    # ==========================================================
    # Update clients
    # ==========================================================

    game_server._broadcast_personalized_state()

    # ==========================================================
    # Both players finished
    # ==========================================================

    if (
        game_server.game
        .mulligan_manager
        .all_players_finished()
    ):

        print(
            "\nMulligan complete! "
            "Starting first turn..."
        )

        game_server._start_first_turn()
