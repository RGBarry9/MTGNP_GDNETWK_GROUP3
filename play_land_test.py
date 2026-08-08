"""
Focused PLAY_LAND test (not a pytest file - run directly).

Single-threaded, drives both player sockets from one place so there's
no race with the random first-player coin flip. Gets a real game to
Turn 1 Precombat Main, then checks:

  1. Playing a land during PRECOMBAT_MAIN succeeds for the active
     player (moves hand -> battlefield, a fresh PRIORITY_GRANT comes
     back to the same player - RFC 0001 SS7.5 / SS8.1 rule 3).
  2. A second land the same turn is rejected (ERROR ILLEGAL_ACTION).
  3. The NON-active player cannot play a land even while they hold
     priority (ERROR) - RFC 0001 SS7.5: only the Active Player may
     play a land.
"""
import socket
import time
import sys

sys.path.insert(0, ".")

import threading
from server.game_server import GameServer
from protocol.framing import create_packet, HEADER_SIZE
from protocol.serializer import decode

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


def try_recv(sock, timeout=0.3):
    try:
        return recv_message(sock, timeout=timeout)
    except socket.timeout:
        return None


def send_message(sock, message):
    sock.sendall(create_packet(message))


def run_server():
    GameServer().start()


def send_ready(sock, name, deck):
    send_message(sock, {"type": "PLAYER_READY", "seq_num": 1, "player_id": name, "deck_list": deck})


def wait_and_keep(sock, name):
    """Block until the MULLIGAN-phase GAME_STATE_UPDATE for this player arrives, then keep."""
    while True:
        msg = recv_message(sock, timeout=15)
        state = msg.get("state", {})
        if msg.get("type") == "GAME_STATE_UPDATE" and state.get("phase") == "MULLIGAN":
            hand = state.get("hand", {}).get(name)
            if hand is not None:
                send_message(sock, {"type": "MULLIGAN_CHOICE", "seq_num": msg["seq_num"], "keep": True, "cards_to_bottom": []})
                return


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    deck = ["forest_001", "forest_002", "forest_003", "forest_004",
            "mountain_001", "mountain_002", "mountain_003", "mountain_004"]

    sock1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock1.connect(("127.0.0.1", 4444))
    sock2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock2.connect(("127.0.0.1", 4444))

    send_ready(sock1, "player_1", deck)
    send_ready(sock2, "player_2", deck)
    wait_and_keep(sock1, "player_1")
    wait_and_keep(sock2, "player_2")

    socks = {"player_1": sock1, "player_2": sock2}
    hands = {"player_1": None, "player_2": None}
    active_player = None
    phase = None
    priority_holder = None
    priority_seq = {"player_1": None, "player_2": None}

    end_time = time.time() + 20
    reached = False
    while time.time() < end_time and not reached:
        for pid, sock in socks.items():
            msg = try_recv(sock, timeout=0.3)
            if msg is None:
                continue

            if msg.get("type") == "GAME_STATE_UPDATE":
                state = msg["state"]
                if "phase" in state:
                    phase = state["phase"]
                h = state.get("hand", {}).get(pid)
                if h is not None:
                    hands[pid] = h
                if state.get("active_player"):
                    active_player = state["active_player"]

            if msg.get("type") == "PHASE_TRANSITION":
                phase = msg.get("to_phase")
                active_player = msg.get("active_player", active_player)

            if msg.get("type") == "PRIORITY_GRANT":
                priority_seq[pid] = msg["seq_num"]
                priority_holder = pid
                if phase == "PRECOMBAT_MAIN":
                    # This is the grant we're actually waiting for -
                    # stop here without passing it, so seq_num/holder
                    # stay in sync with what's still unconsumed.
                    reached = True
                else:
                    send_message(sock, {"type": "PRIORITY_PASS", "seq_num": msg["seq_num"]})

    check("Reached PRECOMBAT_MAIN", phase == "PRECOMBAT_MAIN")
    check("Know who the active player is", active_player in ("player_1", "player_2"))

    non_active = "player_2" if active_player == "player_1" else "player_1"

    check("Active player holds priority entering PRECOMBAT_MAIN", priority_holder == active_player)

    land_id = None
    for c in hands[active_player] or []:
        if "forest" in c or "mountain" in c:
            land_id = c
            break
    check("Active player has a land in hand", land_id is not None)

    active_sock = socks[active_player]
    seq = priority_seq[active_player]

    send_message(active_sock, {"type": "PLAY_LAND", "seq_num": seq, "card_id": land_id})
    msg = recv_message(active_sock)
    played_ok = False
    if msg.get("type") == "GAME_STATE_UPDATE":
        battlefield = msg["state"].get("battlefield", {}).get(active_player, [])
        new_hand = msg["state"].get("hand", {}).get(active_player, [])
        if any(p.get("id") == land_id for p in battlefield) and land_id not in new_hand:
            played_ok = True
            hands[active_player] = new_hand
    else:
        print(f"  Unexpected response to PLAY_LAND: {msg}")
    check("Playing a land in PRECOMBAT_MAIN succeeds for the active player", played_ok)

    msg = recv_message(active_sock)
    check(
        "Active player retains priority after playing a land (fresh PRIORITY_GRANT)",
        msg.get("type") == "PRIORITY_GRANT"
    )
    seq = msg.get("seq_num", seq)

    land_id_2 = None
    for c in hands[active_player] or []:
        if c != land_id and ("forest" in c or "mountain" in c):
            land_id_2 = c
            break

    if land_id_2:
        send_message(active_sock, {"type": "PLAY_LAND", "seq_num": seq, "card_id": land_id_2})
        msg = recv_message(active_sock)
        check(
            "Second land the same turn is rejected (ERROR ILLEGAL_ACTION)",
            msg.get("type") == "ERROR" and msg.get("code") == "ILLEGAL_ACTION"
        )
    else:
        check("Second land the same turn is rejected (ERROR ILLEGAL_ACTION)", False)
        print("  (no second land in hand to test with)")

    send_message(active_sock, {"type": "PRIORITY_PASS", "seq_num": seq})

    # The land-play broadcast earlier sent non_active a GAME_STATE_UPDATE
    # too (we only drained active_sock's copy) - skip past any leftover
    # non-PRIORITY_GRANT messages before checking.
    msg = None
    for _ in range(5):
        msg = recv_message(socks[non_active])
        if msg.get("type") == "PRIORITY_GRANT":
            break
    if msg.get("type") == "PRIORITY_GRANT":
        na_land = None
        for c in hands[non_active] or []:
            if "forest" in c or "mountain" in c:
                na_land = c
                break
        if na_land:
            send_message(socks[non_active], {"type": "PLAY_LAND", "seq_num": msg["seq_num"], "card_id": na_land})
            reply = recv_message(socks[non_active])
            check(
                "Non-active player cannot play a land (ERROR, even while holding priority)",
                reply.get("type") == "ERROR"
            )
        else:
            check("Non-active player cannot play a land (ERROR, even while holding priority)", False)
            print("  (non-active player had no land to test with)")
    else:
        check("Non-active player cannot play a land (ERROR, even while holding priority)", False)
        print(f"  (expected PRIORITY_GRANT for {non_active}, got {msg.get('type')})")

    sock1.close()
    sock2.close()

    print("\n===== SUMMARY =====")
    for desc, ok in CHECKS:
        print(f"  [{'PASS' if ok else 'FAIL'}] {desc}")
    sys.exit(0 if all(ok for _, ok in CHECKS) else 1)


if __name__ == "__main__":
    main()
