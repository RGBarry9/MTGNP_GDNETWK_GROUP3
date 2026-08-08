"""
Focused lobby-full rejection test (not a pytest file - run directly).

Connects two real players (fills the lobby), then connects a 3rd and
checks that it's rejected immediately and explicitly rather than being
left to hang until a PING/PONG timeout:

  1. The 3rd connection receives an ERROR PDU with code LOBBY_FULL
     right after connecting (no PLAYER_READY needed to trigger it).
  2. The server closes that socket shortly after (recv() returns
     empty / connection closed), well within PONG_TIMEOUT.
  3. The two seated players are completely unaffected - the game
     still proceeds normally.
"""
import socket
import threading
import time
import sys

sys.path.insert(0, ".")

from server.game_server import GameServer
from protocol.framing import create_packet, HEADER_SIZE
from protocol.serializer import decode
from config.settings import PONG_TIMEOUT

CHECKS = []


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


def send_message(sock, message):
    sock.sendall(create_packet(message))


def run_server():
    GameServer().start()


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    deck = ["forest_001", "forest_002", "forest_003", "forest_004"]

    # Seat the two real players first.
    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.connect(("127.0.0.1", 4444))
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.connect(("127.0.0.1", 4444))

    # Give the server a moment to actually finish its accept loop and
    # spin up _reject_extra_connections() before p3 shows up.
    time.sleep(0.5)

    # --- Check 1 & 2: a 3rd connection gets an explicit, fast rejection ---
    sock3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock3.connect(("127.0.0.1", 4444))

    start = time.time()
    msg = recv_message(sock3, timeout=5)
    elapsed = time.time() - start

    check(
        "3rd connection gets an ERROR LOBBY_FULL PDU",
        msg is not None and msg.get("type") == "ERROR" and msg.get("code") == "LOBBY_FULL"
    )
    check(
        f"Rejection arrives fast (in {elapsed:.2f}s, well under PONG_TIMEOUT={PONG_TIMEOUT}s)",
        elapsed < PONG_TIMEOUT
    )

    # Server should then close the socket - next recv should hit EOF (None),
    # not just hang.
    followup = recv_message(sock3, timeout=3)
    check("Server closes the 3rd connection after rejecting it", followup is None)

    sock3.close()

    # --- Check 3: the two real players are unaffected - can still ready up ---
    send_message(sock1, {"type": "PLAYER_READY", "seq_num": 1, "player_id": "player_1", "deck_list": deck})
    send_message(sock2, {"type": "PLAYER_READY", "seq_num": 1, "player_id": "player_2", "deck_list": deck})

    got_setup = False
    end_time = time.time() + 10
    while time.time() < end_time:
        msg = recv_message(sock1, timeout=5)
        if msg is None:
            break
        state = msg.get("state", {})
        if msg.get("type") == "GAME_STATE_UPDATE" and state.get("phase") in ("MULLIGAN", "GAME_SETUP"):
            got_setup = True
            break

    check("The two seated players are unaffected - game proceeds normally", got_setup)

    sock1.close()
    sock2.close()

    print("\n===== SUMMARY =====")
    for desc, ok in CHECKS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    sys.exit(0 if all(ok for _, ok in CHECKS) else 1)


if __name__ == "__main__":
    main()
