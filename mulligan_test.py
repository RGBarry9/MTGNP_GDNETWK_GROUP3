"""
Focused mulligan test (not a pytest file - run directly).

Drives one real game through PLAYER_READY -> MULLIGAN and checks:
  1. Opening hand is 7 cards.
  2. A mulligan redraws a fresh 7-card hand.
  3. Keeping after N mulligans with the WRONG number of cards to
     bottom is rejected with ERROR ILLEGAL_ACTION (hand size unchanged).
  4. Keeping after N mulligans with the RIGHT number of cards to
     bottom succeeds and hand size drops to 7 - N.
  5. Once both players have kept, the game actually reaches IN_GAME
     (first PRIORITY_GRANT arrives).

Prints a PASS/FAIL summary per check.
"""
import socket
import threading
import time
import sys

sys.path.insert(0, ".")

from server.game_server import GameServer
from protocol.framing import create_packet, HEADER_SIZE
from protocol.serializer import decode

CHECKS = []  # (description, bool)


def check(desc, ok):
    CHECKS.append((desc, ok))
    print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")


def recv_exact(sock, size):
    data = b""
    while len(data) < size:
        chunk = sock.recv(size - len(data))
        if not chunk:
            return None
        data += chunk
    return data


def recv_message(sock, timeout=5):
    sock.settimeout(timeout)
    header = recv_exact(sock, HEADER_SIZE)
    if header is None:
        return None
    length = int.from_bytes(header, "big")
    return decode(recv_exact(sock, length))


def try_recv_message(sock, timeout=0.5):
    """Like recv_message but returns None (instead of raising) on timeout."""
    try:
        return recv_message(sock, timeout=timeout)
    except socket.timeout:
        return None


def send_message(sock, message):
    sock.sendall(create_packet(message))


def run_server():
    GameServer().start()


def bystander(name, deck, go_event, in_game_event):
    """player_2: waits for go_event, then keeps immediately and waits for the game to start."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 4444))
    send_message(sock, {"type": "PLAYER_READY", "seq_num": 1, "player_id": name, "deck_list": deck})

    mulligan_seq = None
    sent_keep = False
    end_time = time.time() + 20
    while time.time() < end_time:
        msg = try_recv_message(sock, timeout=0.5)
        if msg is not None:
            if msg.get("type") == "GAME_STATE_UPDATE" and msg.get("state", {}).get("phase") == "MULLIGAN":
                mulligan_seq = msg["seq_num"]
            if msg.get("type") == "PRIORITY_GRANT":
                in_game_event.set()
                sock.close()
                return
        if mulligan_seq is not None and go_event.is_set() and not sent_keep:
            send_message(sock, {"type": "MULLIGAN_CHOICE", "seq_num": mulligan_seq, "keep": True, "cards_to_bottom": []})
            sent_keep = True
    sock.close()


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    deck = ["forest_001", "forest_002", "forest_003", "forest_004",
            "mountain_001", "mountain_002", "mountain_003", "mountain_004"]

    go_event = threading.Event()
    in_game_event = threading.Event()
    p2 = threading.Thread(target=bystander, args=("player_2", deck, go_event, in_game_event))
    p2.start()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 4444))
    send_message(sock, {"type": "PLAYER_READY", "seq_num": 1, "player_id": "player_1", "deck_list": deck})

    # --- Wait for the initial MULLIGAN GAME_STATE_UPDATE with our 7-card hand ---
    mulligan_seq = None
    hand = None
    while True:
        msg = recv_message(sock)
        if msg is None:
            print("Connection closed unexpectedly."); sys.exit(1)
        state = msg.get("state", {})
        if msg.get("type") == "GAME_STATE_UPDATE" and state.get("phase") == "MULLIGAN":
            h = state.get("hand", {}).get("player_1")
            if h is not None:
                mulligan_seq = msg["seq_num"]
                hand = h
                break

    check("Opening hand has 7 cards", len(hand) == 7)

    # --- Check 2: take a mulligan, expect a fresh 7-card hand ---
    send_message(sock, {"type": "MULLIGAN_CHOICE", "seq_num": mulligan_seq, "keep": False, "cards_to_bottom": []})
    msg = recv_message(sock)
    new_hand = msg.get("state", {}).get("hand", {}).get("player_1")
    mulligan_seq = msg["seq_num"]
    check("Mulligan redraws a fresh 7-card hand", new_hand is not None and len(new_hand) == 7)

    # --- Check 3: keep with WRONG bottom count should be rejected ---
    send_message(sock, {"type": "MULLIGAN_CHOICE", "seq_num": mulligan_seq, "keep": True, "cards_to_bottom": []})
    msg = recv_message(sock)
    check(
        "Keeping with wrong bottom count is rejected (ERROR ILLEGAL_ACTION)",
        msg.get("type") == "ERROR" and msg.get("code") == "ILLEGAL_ACTION"
    )

    # --- Check 4: keep with CORRECT bottom count (1 card, since 1 mulligan taken) succeeds ---
    card_to_bottom = new_hand[0]
    send_message(sock, {"type": "MULLIGAN_CHOICE", "seq_num": mulligan_seq, "keep": True, "cards_to_bottom": [card_to_bottom]})
    msg = recv_message(sock)
    final_hand = msg.get("state", {}).get("hand", {}).get("player_1")
    check(
        "Keeping with correct bottom count succeeds, hand drops to 6",
        msg.get("type") == "GAME_STATE_UPDATE" and final_hand is not None and len(final_hand) == 6
        and card_to_bottom not in final_hand
    )

    # --- Check 5: once both players keep, game reaches IN_GAME (PRIORITY_GRANT arrives,
    #     on whichever socket the random first-player coin flip granted it to) ---
    go_event.set()  # let player_2 keep now that player_1 is done testing
    end_time = time.time() + 10
    reached_in_game = False
    while time.time() < end_time:
        msg = try_recv_message(sock, timeout=0.5)
        if msg is not None and msg.get("type") == "PRIORITY_GRANT":
            reached_in_game = True
            break
        if in_game_event.is_set():
            reached_in_game = True
            break
    check("Game reaches IN_GAME after both players keep (PRIORITY_GRANT received)", reached_in_game)

    sock.close()
    p2.join(timeout=5)

    print("\n===== SUMMARY =====")
    for desc, ok in CHECKS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    sys.exit(0 if all(ok for _, ok in CHECKS) else 1)


if __name__ == "__main__":
    main()
