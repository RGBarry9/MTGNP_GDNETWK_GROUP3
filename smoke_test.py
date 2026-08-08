"""
Manual end-to-end smoke test (not a pytest file).

Starts the real GameServer in a background thread, connects two plain
TCP clients, and drives them through:
  LOBBY -> GAME_SETUP -> MULLIGAN -> IN_GAME (turn 1) -> priority pass
  loop -> CONCEDE -> GAME_OVER -> back to LOBBY

Prints every PDU exchanged. Exits non-zero if anything looks wrong.
"""
import json
import socket
import threading
import time
import sys

sys.path.insert(0, ".")

from server.game_server import GameServer
from protocol.framing import create_packet, HEADER_SIZE
from protocol.serializer import decode


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
    payload = recv_exact(sock, length)
    return decode(payload)


def send_message(sock, message):
    sock.sendall(create_packet(message))


def run_server():
    server = GameServer()
    server.start()


def client_thread(name, deck, log):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(("127.0.0.1", 4444))

    send_message(sock, {"type": "PLAYER_READY", "seq_num": 1, "player_id": name, "deck_list": deck})

    mulligan_done = False
    got_priority = False
    passes_sent = 0

    end_time = time.time() + 15
    while time.time() < end_time:
        msg = recv_message(sock, timeout=5)
        if msg is None:
            log.append(f"[{name}] connection closed")
            break

        log.append(f"[{name}] <- {msg.get('type')}: {json.dumps(msg)[:200]}")

        mtype = msg.get("type")

        if mtype == "GAME_STATE_UPDATE" and msg.get("state", {}).get("phase") == "MULLIGAN" and not mulligan_done:
            mulligan_done = True
            send_message(sock, {
                "type": "MULLIGAN_CHOICE",
                "seq_num": msg["seq_num"],
                "keep": True,
                "cards_to_bottom": []
            })
            log.append(f"[{name}] -> MULLIGAN_CHOICE keep=True")

        elif mtype == "PRIORITY_GRANT":
            got_priority = True
            passes_sent += 1
            send_message(sock, {"type": "PRIORITY_PASS", "seq_num": msg["seq_num"]})
            log.append(f"[{name}] -> PRIORITY_PASS (#{passes_sent})")
            if passes_sent >= 2:
                send_message(sock, {"type": "CONCEDE", "seq_num": msg["seq_num"], "player_id": name})
                log.append(f"[{name}] -> CONCEDE")

        elif mtype == "GAME_OVER":
            log.append(f"[{name}] GAME_OVER received, done.")
            sock.close()
            return

    sock.close()
    if not got_priority:
        log.append(f"[{name}] !!! NEVER RECEIVED PRIORITY_GRANT !!!")


def main():
    t = threading.Thread(target=run_server, daemon=True)
    t.start()
    time.sleep(0.5)

    deck1 = ["forest_001", "forest_002", "forest_003", "mountain_001"]
    deck2 = ["island_001", "island_002", "island_003", "mountain_002"]

    log1, log2 = [], []
    c1 = threading.Thread(target=client_thread, args=("player_1", deck1, log1))
    c2 = threading.Thread(target=client_thread, args=("player_2", deck2, log2))
    c1.start()
    c2.start()
    c1.join(timeout=20)
    c2.join(timeout=20)

    print("\n===== player_1 log =====")
    print("\n".join(log1))
    print("\n===== player_2 log =====")
    print("\n".join(log2))

    combined = "\n".join(log1 + log2)
    ok = (
        "PRIORITY_GRANT" in combined
        and "GAME_OVER" in combined
        and "!!!" not in combined
    )
    print("\n===== RESULT:", "PASS" if ok else "FAIL", "=====")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
