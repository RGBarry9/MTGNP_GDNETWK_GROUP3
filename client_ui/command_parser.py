import time

from protocol.protocol import make_message
from protocol.message_types import MessageType


class CommandError(Exception):
    """
    Raised when a typed command is unknown, malformed, or attempted
    before the server has issued the token it needs to echo.
    """
    pass


# Commands the terminal itself handles and never sends to the server.
LOCAL_COMMANDS = {"help", "quit", "exit", "clear"}

# PHASE_TRANSITION.to_phase values that open a combat sub-step whose
# seq_num becomes the token for the corresponding client action.
COMBAT_STEP_PHASES = {"DECLARE_ATTACKERS", "DECLARE_BLOCKERS", "ASSIGN_DAMAGE_ORDER"}


class SequenceTracker:
    """
    Tracks the seq_num tokens a client needs to echo per RFC 0001
    Section 5.4, by observing every PDU received from the server.
    """

    def __init__(self):

        self.last_server_seq = 0  # for CONCEDE (any most-recent PDU)

        self.priority_token = None      # last PRIORITY_GRANT.seq_num
        self.combat_token = None        # last relevant PHASE_TRANSITION.seq_num
        self.mulligan_token = None      # GAME_STATE_UPDATE.seq_num at MULLIGAN
        self.discard_token = None       # GAME_STATE_UPDATE.seq_num at CLEANUP
        self.trigger_order_token = None    # last TRIGGER_ORDER.seq_num
        self.trigger_choice_token = None   # last TRIGGER_CHOICE.seq_num

        self._player_ready_seq = 0
        self._ping_seq = 0

    def observe(self, message: dict):
        """
        Update tokens from an incoming server PDU.
        """

        seq_num = message.get("seq_num")

        if seq_num is not None:
            self.last_server_seq = seq_num

        message_type = message.get("type")

        if message_type == "PRIORITY_GRANT":
            self.priority_token = seq_num

        elif message_type == "PHASE_TRANSITION":
            if message.get("to_phase") in COMBAT_STEP_PHASES:
                self.combat_token = seq_num

        elif message_type == "GAME_STATE_UPDATE":
            phase = message.get("state", {}).get("phase")
            if phase == "MULLIGAN":
                self.mulligan_token = seq_num
            elif phase == "CLEANUP":
                self.discard_token = seq_num

        elif message_type == "TRIGGER_ORDER":
            self.trigger_order_token = seq_num

        elif message_type == "TRIGGER_CHOICE":
            self.trigger_choice_token = seq_num

        elif message_type == "GAME_OVER":
            # Server returns to LOBBY; priority/combat/mulligan/discard
            # tokens from the finished game no longer apply.
            self.priority_token = None
            self.combat_token = None
            self.mulligan_token = None
            self.discard_token = None
            self.trigger_order_token = None
            self.trigger_choice_token = None

    def next_player_ready_seq(self) -> int:
        """
        Return the next value of the independent PLAYER_READY counter.
        """

        self._player_ready_seq += 1

        return self._player_ready_seq

    def next_ping_seq(self) -> int:
        """
        Return the next value of the independent PING counter.
        """

        self._ping_seq += 1

        return self._ping_seq


def _parse_csv(value: str) -> list:
    """
    Parse a comma-separated list argument. '-' or '' means empty.
    """

    if value in ("-", ""):
        return []

    return value.split(",")


def _parse_mana(value: str) -> dict:
    """
    Parse a mana payment argument like 'R:1,U:2' into a dict.
    '-' or '' means no mana.
    """

    if value in ("-", ""):
        return {}

    mana = {}

    for part in value.split(","):
        colour, sep, amount = part.partition(":")
        if not sep or not amount.isdigit():
            raise CommandError(f"Invalid mana amount '{part}'. Use the format R:1,U:2.")
        mana[colour] = int(amount)

    return mana


class CommandParser:
    """
    Turns a line of player input into an MTGNP protocol message,
    using a SequenceTracker to supply the correct seq_num.
    """

    def __init__(self, player_id: str, tracker: SequenceTracker = None):

        self.player_id = player_id

        self.tracker = tracker or SequenceTracker()

    def is_local(self, raw_input: str) -> bool:
        """
        Return True if the command is handled locally by the terminal.
        """

        command = raw_input.strip().split(" ")[0].lower()

        return command in LOCAL_COMMANDS

    def parse(self, raw_input: str) -> dict:
        """
        Parse raw player input into a protocol message ready to send.

        Raises CommandError if the input is invalid or if the token
        the command needs to echo hasn't been received yet.
        """

        raw_input = raw_input.strip()

        if not raw_input:
            raise CommandError("Empty command.")

        parts = raw_input.split(" ")

        command = parts[0].lower()
        args = parts[1:]

        builder = getattr(self, f"_build_{command}", None)

        if builder is None:
            raise CommandError(
                f"Unknown command: '{command}'. Type 'help' for a list of commands."
            )

        return builder(args)

    def _require(self, token, description: str) -> int:
        """
        Return a token, or raise CommandError if it hasn't arrived yet.
        """

        if token is None:
            raise CommandError(f"No {description} received yet. Please wait.")

        return token

    # ==========================================================
    # Lobby / Setup
    # ==========================================================

    def _build_ready(self, args: list) -> dict:

        if not args or len(args) > 50:
            raise CommandError("Usage: ready <card_id> ... (1 to 50 cards)")

        return make_message(
            MessageType.PLAYER_READY,
            self.tracker.next_player_ready_seq(),
            player_id=self.player_id,
            deck_list=args,
        )

    def _build_mulligan(self, args: list) -> dict:

        if not args or args[0].lower() not in ("keep", "redraw"):
            raise CommandError("Usage: mulligan keep [card_id ...]  |  mulligan redraw")

        seq_num = self._require(self.tracker.mulligan_token, "mulligan prompt")

        if args[0].lower() == "redraw":
            return make_message(MessageType.MULLIGAN_CHOICE, seq_num, keep=False, cards_to_bottom=[])

        return make_message(
            MessageType.MULLIGAN_CHOICE,
            seq_num,
            keep=True,
            cards_to_bottom=args[1:],
        )

    # ==========================================================
    # Main phase actions
    # ==========================================================

    def _build_land(self, args: list) -> dict:

        if not args:
            raise CommandError("Usage: land <card_id>")

        seq_num = self._require(self.tracker.priority_token, "priority grant")

        return make_message(MessageType.PLAY_LAND, seq_num, card_id=args[0])

    def _build_cast(self, args: list) -> dict:

        if not args:
            raise CommandError("Usage: cast <card_id> [targets_csv|-] [mana_csv|-]")

        seq_num = self._require(self.tracker.priority_token, "priority grant")

        targets = _parse_csv(args[1]) if len(args) > 1 else []
        mana_payment = _parse_mana(args[2]) if len(args) > 2 else {}

        return make_message(
            MessageType.CAST_SPELL,
            seq_num,
            card_id=args[0],
            targets=targets,
            mana_payment=mana_payment,
        )

    def _build_ability(self, args: list) -> dict:

        if len(args) < 2:
            raise CommandError(
                "Usage: ability <source_id> <ability_index> [targets_csv|-] [tap:yes|no] [mana_csv|-]"
            )

        if not args[1].isdigit():
            raise CommandError("ability_index must be a number.")

        seq_num = self._require(self.tracker.priority_token, "priority grant")

        targets = _parse_csv(args[2]) if len(args) > 2 else []
        tap = args[3].lower() in ("yes", "true", "tap") if len(args) > 3 else False
        mana = _parse_mana(args[4]) if len(args) > 4 else {}

        return make_message(
            MessageType.ACTIVATE_ABILITY,
            seq_num,
            source_id=args[0],
            ability_index=int(args[1]),
            targets=targets,
            cost_payment={"tap": tap, "mana": mana},
        )

    def _build_pass(self, args: list) -> dict:

        seq_num = self._require(self.tracker.priority_token, "priority grant")

        return make_message(MessageType.PRIORITY_PASS, seq_num)

    # ==========================================================
    # Combat
    # ==========================================================

    def _build_attack(self, args: list) -> dict:

        seq_num = self._require(self.tracker.combat_token, "declare-attackers step")

        attackers = []

        for pair in args:
            if ":" not in pair:
                raise CommandError(
                    "Usage: attack <creature_id>:<target> ...  (send with no args to attack with nothing)"
                )
            creature_id, target = pair.split(":", 1)
            attackers.append({"creature_id": creature_id, "target": target})

        return make_message(MessageType.DECLARE_ATTACKERS, seq_num, attackers=attackers)

    def _build_block(self, args: list) -> dict:

        seq_num = self._require(self.tracker.combat_token, "declare-blockers step")

        blockers = []

        for pair in args:
            if ":" not in pair:
                raise CommandError(
                    "Usage: block <creature_id>:<attacker_id> ...  (send with no args to block nothing)"
                )
            creature_id, blocking_id = pair.split(":", 1)
            blockers.append({"creature_id": creature_id, "blocking_id": blocking_id})

        return make_message(MessageType.DECLARE_BLOCKERS, seq_num, blockers=blockers)

    def _build_damage(self, args: list) -> dict:

        if len(args) < 2:
            raise CommandError("Usage: damage <attacker_id> <blocker_id> [blocker_id ...]")

        seq_num = self._require(self.tracker.combat_token, "assign-damage-order step")

        return make_message(
            MessageType.ASSIGN_DAMAGE_ORDER,
            seq_num,
            attacker_id=args[0],
            blocker_order=args[1:],
        )

    # ==========================================================
    # Triggers
    # ==========================================================

    def _build_trigger_order(self, args: list) -> dict:

        if not args:
            raise CommandError("Usage: trigger_order <trigger_id> <trigger_id> ...")

        seq_num = self._require(self.tracker.trigger_order_token, "TRIGGER_ORDER prompt")

        return make_message(MessageType.TRIGGER_ORDER_RESPONSE, seq_num, ordered_trigger_ids=args)

    def _build_trigger_choice(self, args: list) -> dict:

        if len(args) < 2 or args[1].lower() not in ("yes", "no"):
            raise CommandError("Usage: trigger_choice <trigger_id> <yes|no> [target]")

        seq_num = self._require(self.tracker.trigger_choice_token, "TRIGGER_CHOICE prompt")

        accept = args[1].lower() == "yes"
        chosen_target = args[2] if len(args) > 2 else None

        return make_message(
            MessageType.TRIGGER_CHOICE_RESPONSE,
            seq_num,
            trigger_id=args[0],
            accept=accept,
            chosen_target=chosen_target,
        )

    # ==========================================================
    # Cleanup
    # ==========================================================

    def _build_discard(self, args: list) -> dict:

        if not args:
            raise CommandError("Usage: discard <card_id> [card_id ...]")

        seq_num = self._require(self.tracker.discard_token, "cleanup discard prompt")

        return make_message(MessageType.DISCARD, seq_num, card_ids=args)

    # ==========================================================
    # Any time
    # ==========================================================

    def _build_concede(self, args: list) -> dict:

        return make_message(
            MessageType.CONCEDE,
            self.tracker.last_server_seq,
            player_id=self.player_id,
        )

    def _build_ping(self, args: list) -> dict:

        return make_message(
            MessageType.PING,
            self.tracker.next_ping_seq(),
            timestamp=int(time.time() * 1000),
        )
