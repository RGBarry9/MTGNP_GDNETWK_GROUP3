def player_ready(message):

    print("\nPLAYER_READY RECEIVED")

    print("----------------------")

    print(f"Player ID : {message['player_id']}")

    print(f"Sequence  : {message['seq_num']}")

    print(f"Deck Size : {len(message['deck_list'])}")

    print()