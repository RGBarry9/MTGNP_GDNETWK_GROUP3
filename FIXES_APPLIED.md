# Fixes applied to get MTGNP_GDNETWK_GROUP3 actually running

This is a record of everything changed so the game runs end-to-end
(lobby -> setup -> mulligan -> turn loop -> priority passing -> concede
-> game over), verified with `smoke_test.py`. Kept here so the group
can see exactly what was wrong and why, rather than silently losing
the history in a diff.

## 1. `server/game_server.py` — rewritten

The old `GameServer` was a bare skeleton (`self.server`, `self.dispatcher`,
`self.connections`, `self.game_state = GameState()`, plus a set of
`print()`-only stub methods that were never even called). Meanwhile
`handlers/*.py` all call things like `game_server.game`,
`game_server.card_db`, `game_server.connection_player`,
`game_server.player_connections`, `game_server.validator`,
`game_server.send_error()`, `game_server._start_game()`,
`game_server._broadcast_personalized_state()`, `game_server._give_priority()`,
`game_server.next_seq()`, etc. None of that existed, so the server would
crash with `AttributeError` on the very first real `PLAYER_READY`.

The new version wires up:
- `self.game` — an actual `engine.game.Game` instance (which already had
  almost everything needed: `add_player`, `mulligan_manager`,
  `priority_manager`, `turn_manager`, `win_manager`, etc.)
- `self.game_state` — alias for `self.game.game_state`
- `self.card_db` — `{card_id: raw_dict}` loaded from `game/cards.json`
  (handlers build `Card` objects out of these dicts directly, so this
  has to stay a plain dict, not a `CardLoader`/`Card`-object map)
- `self.player_connections` / `self.connection_player` — the two
  inverse lookup dicts the handlers use
- `self.validator` — a `GameValidator`
- Helper methods: `broadcast`, `send_to_connection`, `send_error`,
  `next_seq`, `_find_connection`, `_start_game`, `_start_first_turn`,
  `_phase_has_priority`, `_give_priority`, `_broadcast_phase_transition`,
  `_broadcast_personalized_state`, `_end_game`

## 2. `network/server.py` + `game_server.py` — concurrency deadlock

`game_loop()` used to iterate over both connections and call the
*blocking* `connection.receive()` on each in turn. If player 1 hadn't
sent anything yet, the loop would hang on `connections[0].receive()`
forever and never even check player 2's socket — the server could never
actually run a real two-player game.

Fixed by giving each connection its own reader thread
(`_connection_loop`), with a single `RLock` guarded around
`dispatcher.dispatch()` so game-state mutation stays single-threaded
(no data races) while the two sockets can block independently. Also
enabled `TCP_NODELAY` since MTGNP PDUs are small and latency-sensitive
(priority windows, heartbeats).

## 3. `main_client.py` — was a stub

It fired one hardcoded `PLAYER_READY` with an empty deck and waited for
Enter; it never read anything back from the server. The real client
(full send/receive/heartbeat loop) already existed at
`client_ui/terminal.py` (`Terminal` class) but nothing launched it.
`main_client.py` now just starts `Terminal`.

## 4. Missing `player_id` on most client PDUs

Per RFC 0001's schemas, most client->server PDUs (`MULLIGAN_CHOICE`,
`PRIORITY_PASS`, `CAST_SPELL`, `PLAY_LAND`, `ACTIVATE_ABILITY`,
`DECLARE_ATTACKERS`, `DECLARE_BLOCKERS`, `ASSIGN_DAMAGE_ORDER`, `DISCARD`)
don't carry a `player_id` field at all — the server is meant to know who
sent them from the TCP connection. But every handler in `handlers/*.py`
reads `message.get("player_id")` and blows up (`"Player None not found"`)
as soon as any of these arrive.

Fixed in `GameServer._connection_loop`: if an incoming message has no
`player_id`, the server stamps in the one associated with that
connection before dispatching. (Also more correct/secure than trusting
a client-supplied value for actions like this.)

## 5. Priority never actually passed to the other player

In `handlers/priority_handler.py`, `priority_pass()` calls
`game.pass_priority(player)`, which returns `"NEXT_PLAYER"`,
`"RESOLVE_STACK"`, or `"ADVANCE_PHASE"`. Only the latter two were
handled. On a plain single pass (`"NEXT_PLAYER"`), the engine updated
`game_state.priority_player` internally but the server never sent the
opponent a `PRIORITY_GRANT` — so the opponent had no seq_num token to
act on and the game hung permanently after one pass.

Added the missing `elif result == "NEXT_PLAYER"` branch, and made
`GameServer._give_priority()` accept an optional player argument (it
still defaults to the active player, which is correct when opening a
fresh priority window at the start of a step or after stack resolution).

## 6. `GameState.reset_priority()` double-incremented `priority_seq_num`

It bumped the counter itself *and* `PriorityManager.give_priority()`
bumps it again right after — so the seq_num the server actually put in
the next `PRIORITY_GRANT` was always one higher than what
`validate_seq_num()` expected, and clients could never echo a valid
token after the first double-pass. This is exactly why
`tests/test_priority.py` was failing. Removed the increment from
`reset_priority()`; only `give_priority()` advances it now, matching the
value that's actually broadcast.

## 7. `GameState.get_personalized_state()` never reported MULLIGAN/LOBBY

The `"phase"` field in `GAME_STATE_UPDATE` always reported the turn
`Phase` enum (`UNTAP`, `UPKEEP`, ...), which has no `MULLIGAN` member —
so during the entire mulligan phase, clients saw `"phase": "UNTAP"`
and had no reliable way to know it was time to send `MULLIGAN_CHOICE`.
Now it reports the top-level lifecycle state (`GameState` enum:
`LOBBY`/`GAME_SETUP`/`MULLIGAN`/`IN_GAME`/`GAME_OVER`) until the game
is actually `IN_GAME`, then switches to reporting the turn `Phase`,
matching the two `GAME_STATE_UPDATE` examples in RFC 0001 SS10.2.2.

## 8. `Game.start_game()` jumped straight to IN_GAME, skipping MULLIGAN

It called `game_state.set_game_state(GameStateEnum.IN_GAME)`
immediately after dealing opening hands, before either player had
actually kept a hand — violating RFC 0001 SS6.3's requirement that
"The server MUST NOT begin the first turn until both players have
completed the mulligan phase." Combined with bug #7 this made the
mulligan step invisible to clients. Now `start_game()` sets the
lifecycle to `MULLIGAN`, and `start_turn()` (only called once both
players have kept a hand — see `lobby_handler.mulligan_choice`) is what
transitions it to `IN_GAME`.

## 9. Stale test file

`tests/test_combat.py` constructed `Card(id=...)`, but the `Card`
dataclass field is `card_id`, not `id` — the test module failed to even
import, taking the whole suite down with it (`pytest
--continue-on-collection-errors` was needed just to see the other 39
tests). Fixed the two `Card(...)` calls to use `card_id=`.

## 10. Anyone who mulliganed could never finish the mulligan phase

Found by writing `mulligan_test.py` (see below) and actually mulliganing
once instead of always keeping the opening hand. `handlers/lobby_handler.py`'s
`mulligan_choice()` used to validate the bottom-count itself, move the
bottomed cards from hand to library **itself**, and only then call
`MulliganManager.keep(player)` — without passing `cards_to_bottom`. Two
problems stacked:

- `MulliganManager.keep()` defaults `cards_to_bottom` to `None`, so its
  own internal check (`cards_to_bottom is None or wrong length`) always
  failed for anyone with `mulligan_count > 0`, silently returning
  `False` and never adding them to `finished_players` — even though the
  handler had already printed "kept hand" and sent a success-looking
  `GAME_STATE_UPDATE`.
- Passing `cards_to_bottom` through fixed that check, but then exposed
  the second problem: `keep()` *also* re-validates that each bottomed
  card is still in the player's hand — and it wasn't, because the
  handler had already moved it out. Two pieces of code doing the same
  job, stepping on each other.

Fixed by deleting the handler's duplicate validate/bottom logic
entirely and letting `MulliganManager.keep(player, cards_to_bottom)` be
the single place that validates, bottoms cards, and marks the player
finished — the handler just checks its boolean return value now. Any
player who mulligans at least once can now actually finish the
mulligan phase and reach turn 1.

## 11. Playing/declaring a land during Precombat Main didn't work

`config/enums.py`'s `Phase` is a plain `Enum` (not `str, Enum`), so
`current_phase` values like `Phase.PRECOMBAT_MAIN` are never equal to
the raw string `"PRECOMBAT_MAIN"`. `handlers/spell_handler.py`'s
`play_land()` checked
`current_phase not in ["PRECOMBAT_MAIN", "POSTCOMBAT_MAIN"]` - a list
of bare strings - so that check was always `True` and every land play
was rejected with `WRONG_PHASE`, no matter what phase it actually was.
The identical bug existed for sorcery-speed spell casting in
`cast_spell()` and for ending the turn in `game_handler.py`. Fixed all
three to import `Phase` from `config.enums` and compare against the
actual enum members.

While tracking this down with a real two-player game, two more bugs
turned up:

- **Non-active player could play lands/cast sorceries at all.**
  Neither `play_land()` nor the sorcery branch of `cast_spell()` ever
  checked `game_state.active_player`, so the Non-Active Player could
  play a land (or cast a sorcery) any time they happened to hold
  priority - violating RFC 0001 SS7.5 ("the Active Player MAY cast
  sorceries... and play one land per turn"). Added an explicit
  active-player check to both.
- **"Retains priority" always went to the active player, not the
  actual actor.** Every `CAST_SPELL`/`PLAY_LAND`/`ACTIVATE_ABILITY`
  success path called `game_server._give_priority()` with no
  argument, which defaults to `game_state.active_player` - correct
  when the active player is the one acting, but wrong the moment the
  Non-Active Player takes a priority-retaining action (e.g. casting an
  instant in response to something). `_give_priority()` now accepts an
  explicit player, and every "same player retains priority" call site
  (in `spell_handler.py` and the `STALE_ACTION` re-grant paths in
  `spell_handler.py`/`priority_handler.py`) passes the actual acting
  player instead of relying on the default.

Verified with `play_land_test.py`: active player plays a land
successfully and keeps priority, a 2nd land the same turn is rejected,
and the non-active player is rejected even while holding priority -
checked across both outcomes of the random first-player coin flip,
8 runs in a row.

## 12. 3rd player got no explanation, just an eventual PING/PONG timeout

`network/server.py`'s accept loop stopped calling `accept()` once
`MAX_PLAYERS` (2) connections were seated. A 3rd client's TCP handshake
would still complete (it just sits in the kernel's listen backlog),
so `client.connect()` succeeded client-side with no error - but the
server never read from or wrote to that socket. The 3rd client would
sit at the input prompt until its own heartbeat's `PONG_TIMEOUT`
(10s) elapsed, at which point it disconnected with a generic
"No PONG received" message that had nothing to do with the actual
reason (lobby full).

Per RFC 0001 SS5.1 ("Additional connection attempts after two players
are seated MUST be refused"), `Server.start()` now spins up a
background thread once the lobby fills that keeps calling `accept()`
for the rest of the server's life, and for every connection beyond the
two seats sends an `ERROR` PDU (`code: "LOBBY_FULL"` - a pragmatic
protocol extension; RFC 0001 doesn't define a code for this exact
case) and closes the socket immediately. `client_ui/terminal.py` now
recognizes `LOBBY_FULL` specifically and exits right away with a clear
"Lobby full - cannot connect" message instead of leaving the process
sitting at the input prompt waiting for a PING/PONG timeout that would
never come with the real reason attached.

Verified with `lobby_full_test.py`: a 3rd connection gets the
`LOBBY_FULL` error and is closed by the server well under 1 second
(vs. the old 10s PONG_TIMEOUT), and the two real players are
completely unaffected.

---

All 40 existing unit tests pass (`python3 -m pytest tests/`),
`python3 smoke_test.py` runs a full two-client game through lobby,
setup, mulligan (no mulligans taken), turn 1, priority passing in both
directions, concede, and game-over, and `python3 mulligan_test.py`
specifically exercises: opening hand size, taking a mulligan and
getting a fresh 7-card hand, keeping with the wrong bottom-count
(rejected), keeping with the correct bottom-count (accepted, hand
drops by 1 per mulligan), and both players actually reaching turn 1
afterward. All checked 3x in a row for flakiness (mulligan_test.py
also covers both outcomes of the random first-player coin flip).

## Try it yourself

Terminal 1: `python3 main_server.py`
Terminal 2: `python3 main_client.py` -> enter a name -> `ready forest_001 forest_002 mountain_001 mountain_002` (see `game/cards.json` for all 54 legal card ids)
Terminal 3: same as terminal 2 with a different name
Then in either terminal: `help` lists every command (`mulligan keep`,
`pass`, `cast`, `land`, `attack`, `block`, `concede`, ...).

Or just run `python3 smoke_test.py` for an automated no-mulligan run,
`python3 mulligan_test.py` for a run that specifically exercises the
mulligan phase, `python3 play_land_test.py` for playing lands
(active/non-active enforcement + retains-priority), or
`python3 lobby_full_test.py` to see a 3rd connection get rejected.

## What's still rough / worth your group's attention next

- Combat (`combat_handler.py`) and spell effects (`effects/`) are wired
  up but only lightly exercised by the smoke test — worth a dedicated
  pass actually casting spells and attacking.
- `_broadcast_phase_transition()` doesn't track the real `from_phase`
  when called with no arguments (several handlers call it that way) —
  it currently sends `null`. Cosmetic, doesn't block gameplay, but not
  RFC-exact.
- No reconnect/disconnect-timeout handling per RFC 0001 SS4.2 yet.
