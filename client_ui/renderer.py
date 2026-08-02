import time


DIVIDER = "-" * 60


def render_banner():
    """
    Print the MTGNP client banner.
    """

    print(DIVIDER)
    print("MTGNP - Magic: The Gathering Network Protocol (RFC 0001)")
    print(DIVIDER)


def render_help():
    """
    Print the list of available terminal commands.
    """

    print(DIVIDER)
    print("Available commands:")
    print("  ready <card_id> ...              Submit your deck list (1-50 cards)")
    print("  mulligan keep [card_id ...]      Keep your hand (bottom N cards if mulliganed)")
    print("  mulligan redraw                  Take a mulligan")
    print("  land <card_id>                   Play a land")
    print("  cast <card_id> [targets] [mana]  Cast a spell, e.g. cast bolt_001 player_2 R:1")
    print("  ability <src> <idx> [t] [tap] [mana]  Activate an ability")
    print("  attack <id>:<target> ...         Declare attackers (no args = no attack)")
    print("  block <id>:<attacker_id> ...     Declare blockers (no args = no blocks)")
    print("  damage <attacker_id> <blk> ...   Assign multi-block damage order")
    print("  trigger_order <id> <id> ...      Order your simultaneous triggers")
    print("  trigger_choice <id> <yes|no> [t] Respond to an optional/targeted trigger")
    print("  discard <card_id> ...            Discard down to 7 cards at cleanup")
    print("  pass                             Pass priority")
    print("  concede                          Concede the game")
    print("  ping                             Send a manual heartbeat PING")
    print("  clear                            Clear the terminal")
    print("  help                             Show this help message")
    print("  quit                             Disconnect and exit")
    print(DIVIDER)
    print("Use '-' for an omitted targets/mana argument, e.g.: cast shock_001 - R:1")
    print(DIVIDER)


def render_error(text: str):
    """
    Print an error message.
    """

    print(f"[ERROR] {text}")


def render_info(text: str):
    """
    Print an informational message.
    """

    print(f"[INFO] {text}")


def render_message(message: dict, player_id: str = None):
    """
    Render an incoming PDU based on its 'type' field.
    """

    message_type = message.get("type")

    if message_type == "GAME_STATE_UPDATE":
        render_game_state(message.get("state", {}), player_id)

    elif message_type == "PHASE_TRANSITION":
        print(
            f"\n>> {message.get('from_phase', '?')} -> {message.get('to_phase', '?')} "
            f"(Turn {message.get('turn', '?')}, active: {message.get('active_player', '?')})"
        )

    elif message_type == "PRIORITY_GRANT":
        holder = message.get("player_id")
        who = "You" if holder == player_id else holder
        print(f"\n>> {who} received priority. ({message.get('time_limit_ms', '?')} ms to act)")

    elif message_type == "STACK_PUSH":
        targets = message.get("targets", [])
        target_str = f" -> {', '.join(targets)}" if targets else ""
        print(
            f"\n>> [Stack] {message.get('source', '?')} "
            f"({message.get('item_type', '?')}){target_str} "
            f"controlled by {message.get('controller', '?')}"
        )

    elif message_type == "STACK_RESOLVE":
        print(f"\n>> [Stack] {message.get('stack_item_id', '?')} {message.get('result', '?')}")
        for change in message.get("state_changes", []):
            amount = change.get("amount")
            amount_str = f" {amount}" if amount is not None else ""
            print(f"     - {change.get('change_type', '?')}: {change.get('target', '?')}{amount_str}")

    elif message_type == "TRIGGER_ORDER":
        print(
            f"\n>> Order your triggers: {message.get('trigger_ids', [])} "
            f"(use: trigger_order <id> <id> ...)"
        )

    elif message_type == "TRIGGER_CHOICE":
        target_note = " (target required)" if message.get("requires_target") else ""
        print(
            f"\n>> {message.get('effect_summary', '?')}{target_note}\n"
            f"   (use: trigger_choice {message.get('trigger_id', '?')} yes|no [target])"
        )

    elif message_type == "COMBAT_DAMAGE_RESULT":
        print("\n>> Combat damage:")
        for event in message.get("damage_events", []):
            print(f"     {event.get('source', '?')} -> {event.get('target', '?')}: {event.get('amount', '?')}")
        died = message.get("creatures_died", [])
        if died:
            print(f"   Died: {', '.join(died)}")
        life_totals = message.get("life_totals")
        if life_totals:
            life_str = ", ".join(f"{pid}: {life}" for pid, life in life_totals.items())
            print(f"   Life totals: {life_str}")

    elif message_type == "GAME_OVER":
        print(DIVIDER)
        print(
            f"GAME OVER - Winner: {message.get('winner_id', '?')}   "
            f"Loser: {message.get('loser_id', '?')}   "
            f"Reason: {message.get('reason', '?')}"
        )
        print("Send 'ready <deck...>' again to start a new game on this connection.")
        print(DIVIDER)

    elif message_type == "ERROR":
        render_error(f"[{message.get('code', '?')}] {message.get('message', 'Unknown error.')}")
        rejected = message.get("rejected_action")
        if rejected:
            print(f"          rejected: {rejected}")

    elif message_type == "PONG":
        render_pong(message)

    else:
        print(f"\n>> [{message_type}] {message}")


def render_pong(message: dict):
    """
    Render a PONG heartbeat reply, including the measured round-trip time.
    """

    sent_at = message.get("timestamp")

    if sent_at is None:
        return

    rtt_ms = int(time.time() * 1000) - sent_at

    print(f"\n>> PONG received (round-trip: {rtt_ms} ms)")


def render_game_state(state: dict, player_id: str = None):
    """
    Render a GAME_STATE_UPDATE's 'state' object (either variant).
    """

    if state.get("phase") == "LOBBY":
        render_lobby_state(state)
        return

    print(DIVIDER)
    print(f"Turn {state.get('turn', '?')} - Phase: {state.get('phase', '?')}")

    priority_holder = state.get("priority_holder")
    print(
        f"Active player: {state.get('active_player', '?')}   "
        f"Priority: {priority_holder if priority_holder else '(none)'}"
    )

    if state.get("land_played_this_turn"):
        print("(Active player has already played a land this turn.)")

    print(DIVIDER)

    life_totals = state.get("life_totals", {})
    hand = state.get("hand", {})
    hand_counts = state.get("hand_counts", {})
    library_counts = state.get("library_counts", {})
    battlefield = state.get("battlefield", {})
    graveyard = state.get("graveyard", {})

    for pid, life in life_totals.items():
        render_player(
            pid, life, hand, hand_counts, library_counts, battlefield, graveyard,
            is_self=(pid == player_id),
        )

    stack = state.get("stack", [])

    if stack:
        print("Stack (top resolves first):")
        for item in reversed(stack):
            targets = item.get("targets", [])
            target_str = f" -> {', '.join(targets)}" if targets else ""
            print(
                f"  * [{item.get('item_type', '?')}] {item.get('source', '?')}{target_str} "
                f"(controller: {item.get('controller', '?')})"
            )
        print(DIVIDER)


def render_lobby_state(state: dict):
    """
    Render the LOBBY-phase variant of GAME_STATE_UPDATE.
    """

    print(DIVIDER)
    print(f"Lobby: {state.get('players_ready', 0)} player(s) ready.")

    waiting_for = state.get("waiting_for", [])
    if waiting_for:
        print(f"Waiting for: {', '.join(waiting_for)}")

    print(DIVIDER)


def render_player(
    player_id: str,
    life: int,
    hand: dict,
    hand_counts: dict,
    library_counts: dict,
    battlefield: dict,
    graveyard: dict,
    is_self: bool = False,
):
    """
    Render one player's zones and life total.

    Only 'is_self' players ever have their hand contents visible -
    the server filters the opponent's hand down to hand_counts, per
    RFC 0001 Section 4.2 (hidden information).
    """

    label = "YOU" if is_self else "OPPONENT"

    print(f"{label} ({player_id})   Life: {life}")

    if is_self and player_id in hand:
        cards = hand[player_id]
        card_list = ", ".join(cards) if cards else "(empty)"
        print(f"  Hand ({len(cards)}): {card_list}")
    else:
        print(f"  Hand: {hand_counts.get(player_id, '?')} card(s) (hidden)")

    print(f"  Library: {library_counts.get(player_id, '?')} card(s)")

    permanents = battlefield.get(player_id, [])
    if permanents:
        print("  Battlefield:")
        for permanent in permanents:
            print(f"    {_render_permanent(permanent)}")
    else:
        print("  Battlefield: (empty)")

    gy = graveyard.get(player_id, [])
    gy_list = ", ".join(gy) if gy else "(empty)"
    print(f"  Graveyard ({len(gy)}): {gy_list}")

    print()


def _render_permanent(permanent: dict) -> str:
    """
    Render one battlefield permanent.

    Non-creature permanents only carry 'id' and 'tapped'; creatures
    additionally carry damage, power, toughness, and summoning_sick.
    """

    tap_str = "[T]" if permanent.get("tapped") else "[ ]"
    card_id = permanent.get("id", "?")

    if permanent.get("power") is not None:
        stats = f"{permanent.get('power')}/{permanent.get('toughness')}"
        damage = permanent.get("damage", 0)
        damage_str = f" dmg:{damage}" if damage else ""
        sick_str = " (summoning sick)" if permanent.get("summoning_sick") else ""
        return f"{tap_str} {card_id} {stats}{damage_str}{sick_str}"

    return f"{tap_str} {card_id}"
