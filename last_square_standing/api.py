# Copyright (c) 2024, Michelle and contributors
# For license information, please see license.txt
"""
Last Square Standing — server-authoritative game API.

All gameplay actions go through whitelisted (guest-allowed) methods here.
Players are identified by an anonymous `player_token` (stored in the browser),
so no login is required. The server owns all game state and timing; clients
only ever *request* transitions and the server validates them.
"""

import json
import math
import random

import frappe
from frappe.utils import add_to_date, get_datetime, now_datetime

from last_square_standing import words

ROUND_DURATION = 10  # seconds players have to pick a square
REVEAL_DELAY = 5  # seconds the reveal/results screen shows before next round
MIN_PLAYERS = 3
MAX_PLAYERS = 16
SUBMIT_GRACE = 2  # seconds of latency grace for auto-submit at the buzzer
MIN_GRID = 2  # the grid stops shrinking here (2x2); the final showdown happens on it
MAX_GRID = 8  # cap on the starting grid no matter how many players
CELLS_PER_PLAYER = 2.5  # starting grid aims for ~this many tiles per player

ROOM_DOCTYPE = "LSS Room"
ROUND_DOCTYPE = "LSS Round"
SELECTION_DOCTYPE = "LSS Selection"

PLACE_POINTS = {1: 100, 2: 50, 3: 25}

# Each player starts every game with one of each ability.
STARTING_ABILITIES = {"shield": 1, "peek": 1, "bomb": 1}

# Quick taunts players can fling at each other (validated server-side).
REACTION_EMOJIS = ["👍", "😂", "😮", "🔥", "💀", "👀"]

BONUS_POINTS = 15  # awarded for landing alone on a Bonus Tile
SUDDEN_DEATH_DURATION = 6  # shorter timer on a Sudden Death round
MODIFIERS = ["frozen", "bonus", "sudden_death"]
MODIFIER_CHANCE = 0.5  # chance a round (from round 2 on) gets a modifier

BOT_NAMES = [
	"Sir Clicks-a-Lot", "Botniss", "Clickbeard", "Tilevoid", "Robo Randy",
	"Bleep Bloop", "The Calculator", "Captain Pixel", "Lord Squareface", "Byte Me",
	"Gridlock", "Zappy", "Mr. Roboto", "Decoy Dan", "Glitchy",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def starting_grid_for(num_players: int) -> int:
	"""Pick the round-1 grid size from how many players are in the game, so more
	players get a bigger board (and 3-player games stay tight, not sparse). Aims
	for ~CELLS_PER_PLAYER tiles per player, clamped to [3, MAX_GRID]."""
	gs = math.ceil(math.sqrt(max(1, num_players) * CELLS_PER_PLAYER))
	return max(3, min(MAX_GRID, gs))


def grid_size_for_round(round_number: int, start_grid: int) -> int:
	"""The board shrinks by one each round from the starting size down to MIN_GRID."""
	return max(MIN_GRID, start_grid - (round_number - 1))


def points_for_place(place: int) -> int:
	return PLACE_POINTS.get(place, 0)


def _gen_room_code() -> str:
	# Unambiguous characters only (no O/0, I/1) for easy verbal sharing.
	alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
	for _ in range(50):
		code = "".join(random.choice(alphabet) for _ in range(4))
		if not frappe.db.exists(ROOM_DOCTYPE, code):
			return code
	frappe.throw("Could not allocate a room code, please retry.")


def _gen_token() -> str:
	return frappe.generate_hash(length=24)


def _iso(dt) -> str | None:
	if not dt:
		return None
	return get_datetime(dt).isoformat()


def _get_room(room_code: str):
	room_code = (room_code or "").strip().upper()
	if not room_code or not frappe.db.exists(ROOM_DOCTYPE, room_code):
		frappe.throw(f"Room {room_code} does not exist.", frappe.DoesNotExistError)
	return frappe.get_doc(ROOM_DOCTYPE, room_code)


def _player_by_token(room, player_token):
	for p in room.players:
		if p.player_token == player_token:
			return p
	return None


def _latest_round(room_code):
	rounds = frappe.get_all(
		ROUND_DOCTYPE,
		filters={"room_code": room_code},
		fields=["name"],
		order_by="creation desc",
		limit=1,
	)
	if not rounds:
		return None
	return frappe.get_doc(ROUND_DOCTYPE, rounds[0].name)


# ---------------------------------------------------------------------------
# State serialization (what every client sees)
# ---------------------------------------------------------------------------


def get_room_state(room, player_token=None):
	"""Build the public game state. Never leaks player tokens or in-progress
	square selections — only aggregate submission counts before the reveal."""
	current = _latest_round(room.room_code)

	round_state = None
	submitted_count = 0
	if current:
		if not current.resolved:
			submitted_count = frappe.db.count(
				SELECTION_DOCTYPE, {"round": current.name}
			)
		round_state = {
			"round_number": current.round_number,
			"grid_size": current.grid_size,
			"started_at": _iso(current.started_at),
			"deadline": _iso(current.deadline),
			"duration": current.duration,
			"resolved": bool(current.resolved),
			"submitted_count": submitted_count,
			"prompt": current.prompt,
			"labels": json.loads(current.labels) if current.labels else [],
			"modifier": current.modifier,
			"modifier_data": json.loads(current.modifier_data) if current.modifier_data else {},
		}

	players = []
	alive = 0
	for p in room.players:
		if not p.eliminated:
			alive += 1
		players.append(
			{
				"username": p.username,
				"is_host": bool(p.is_host),
				"eliminated": bool(p.eliminated),
				"place": p.place,
				"points": p.points,
				"connected": bool(p.connected),
				"is_bot": bool(p.is_bot),
				"wins": p.wins or 0,
			}
		)

	me = None
	if player_token:
		mp = _player_by_token(room, player_token)
		if mp:
			# Reflect the requester's OWN current pick so the client can restore the
			# selected tile across polls, reloads, and reconnects. This only ever
			# exposes your own square — never anyone else's (no leak).
			my_square = None
			if current and not current.resolved:
				own = frappe.get_all(
					SELECTION_DOCTYPE,
					filters={"round": current.name, "player_token": player_token},
					fields=["selected_square"],
					limit=1,
				)
				if own:
					my_square = own[0].selected_square
			me = {
				"username": mp.username,
				"is_host": bool(mp.is_host),
				"eliminated": bool(mp.eliminated),
				"place": mp.place,
				"points": mp.points,
				"selected_square": my_square,
				"abilities": _abilities(mp),
				"shield_active": bool(current and mp.shield_round == current.name),
			}

	rankings = None
	if room.status == "Finished":
		rankings = _build_rankings(room)

	return {
		"room_code": room.room_code,
		"room_name": room.room_name,
		"status": room.status,
		"host_name": room.host_name,
		"current_round": room.current_round,
		"grid_size": room.grid_size,
		"winner_name": room.winner_name,
		"players": players,
		"alive_count": alive,
		"player_count": len(room.players),
		"min_players": MIN_PLAYERS,
		"max_players": MAX_PLAYERS,
		"round": round_state,
		"reveal": json.loads(room.last_reveal) if room.last_reveal else None,
		"rankings": rankings,
		"server_now": _iso(now_datetime()),
		"me": me,
	}


def _build_rankings(room):
	ranked = sorted(
		room.players,
		key=lambda p: (p.place if p.place else 9999, -(p.points or 0)),
	)
	return [
		{
			"username": p.username,
			"place": p.place,
			"points": p.points,
		}
		for p in ranked
	]


def broadcast(room):
	"""Push the new state to everyone in the room (and a poll fallback exists
	on the client). Emitted to the site-wide `website` room — which every
	socket (including guests) auto-joins — under a per-room event name."""
	frappe.publish_realtime(
		event=f"lss:{room.room_code}",
		message=get_room_state(room),
		room="website",
		after_commit=True,
	)


# ---------------------------------------------------------------------------
# Lobby
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def create_room(username: str, room_name: str | None = None):
	username = (username or "").strip()
	if not username:
		frappe.throw("Please enter a name.")
	room_name = (room_name or "").strip()
	if not room_name:
		frappe.throw("Please name your room.")

	token = _gen_token()
	room = frappe.new_doc(ROOM_DOCTYPE)
	room.room_code = _gen_room_code()
	room.room_name = room_name
	room.status = "Lobby"
	room.host_token = token
	room.host_name = username
	room.current_round = 0
	room.grid_size = 0
	room.append(
		"players",
		{"player_token": token, "username": username, "is_host": 1, "connected": 1},
	)
	room.insert(ignore_permissions=True)
	broadcast(room)
	return {
		"room_code": room.room_code,
		"player_token": token,
		"state": get_room_state(room, token),
	}


@frappe.whitelist(allow_guest=True)
def join_room(room_code: str, username: str):
	username = (username or "").strip()
	if not username:
		frappe.throw("Please enter a name.")

	room = _get_room(room_code)
	if room.status != "Lobby":
		frappe.throw("This game has already started.")
	if len(room.players) >= MAX_PLAYERS:
		frappe.throw(f"Room is full (max {MAX_PLAYERS} players).")
	if any(p.username.lower() == username.lower() for p in room.players):
		frappe.throw("That name is already taken in this room.")

	token = _gen_token()
	room.append(
		"players",
		{"player_token": token, "username": username, "is_host": 0, "connected": 1},
	)
	room.save(ignore_permissions=True)
	broadcast(room)
	return {
		"room_code": room.room_code,
		"player_token": token,
		"state": get_room_state(room, token),
	}


@frappe.whitelist(allow_guest=True)
def leave_room(room_code: str, player_token: str):
	room = _get_room(room_code)
	player = _player_by_token(room, player_token)
	if not player:
		return {"ok": True}

	# Only allow clean leave in the lobby; mid-game leavers are just auto-played.
	if room.status == "Lobby":
		was_host = player.is_host
		room.players = [p for p in room.players if p.player_token != player_token]
		if not room.players:
			frappe.delete_doc(ROOM_DOCTYPE, room.name, ignore_permissions=True, force=True)
			frappe.db.commit()
			return {"ok": True, "room_deleted": True}
		if was_host:
			room.players[0].is_host = 1
			room.host_token = room.players[0].player_token
			room.host_name = room.players[0].username
		room.save(ignore_permissions=True)
		broadcast(room)
	else:
		player.connected = 0
		room.save(ignore_permissions=True)
		broadcast(room)
	return {"ok": True}


@frappe.whitelist(allow_guest=True)
def get_state(room_code: str, player_token: str | None = None):
	room = _get_room(room_code)
	return get_room_state(room, player_token)


# ---------------------------------------------------------------------------
# Game flow
# ---------------------------------------------------------------------------


def _create_round(room, round_number, grid_size, start_offset=0):
	cells = grid_size * grid_size
	alive = [p for p in room.players if not p.eliminated]
	modifier, modifier_data, duration = _roll_modifier(round_number, grid_size, len(alive))
	started = add_to_date(now_datetime(), seconds=start_offset)
	deadline = add_to_date(started, seconds=duration)
	prompt, labels = words.pick_round(cells)
	rnd = frappe.new_doc(ROUND_DOCTYPE)
	rnd.room = room.name
	rnd.room_code = room.room_code
	rnd.round_number = round_number
	rnd.grid_size = grid_size
	rnd.status = "Active"
	rnd.duration = duration
	rnd.started_at = started
	rnd.deadline = deadline
	rnd.resolved = 0
	rnd.prompt = prompt
	rnd.labels = json.dumps(labels)
	rnd.modifier = modifier
	rnd.modifier_data = json.dumps(modifier_data) if modifier_data else None
	rnd.bombs = json.dumps([])
	rnd.insert(ignore_permissions=True)
	room.current_round = round_number
	room.grid_size = grid_size
	_seed_bot_picks(room, rnd, modifier_data)
	return rnd


def _roll_modifier(round_number, grid_size, alive_count):
	"""Maybe spice up a round (from round 2 on). Returns (modifier, data, duration)."""
	cells = grid_size * grid_size
	if round_number < 2 or random.random() > MODIFIER_CHANCE:
		return None, None, ROUND_DURATION

	choices = list(MODIFIERS)
	# Only freeze tiles if there's room left for everyone to still pick uniquely.
	if cells - alive_count < 3:
		choices = [m for m in choices if m != "frozen"]
	choice = random.choice(choices)

	if choice == "frozen":
		max_freeze = max(1, cells - alive_count - 1)
		n = min(max(1, cells // 4), max_freeze)
		return "frozen", {"frozen": random.sample(range(cells), n)}, ROUND_DURATION
	if choice == "bonus":
		return "bonus", {"bonus": random.randint(0, cells - 1)}, ROUND_DURATION
	if choice == "sudden_death":
		return "sudden_death", {}, SUDDEN_DEATH_DURATION
	return None, None, ROUND_DURATION


def _seed_bot_picks(room, rnd, modifier_data):
	"""Bots never call the API — pick their squares server-side at round creation,
	with a random lock-in time so they count as 'locked in' and have a timestamp
	for the 2x2 speed tiebreak. They avoid frozen tiles."""
	cells = rnd.grid_size * rnd.grid_size
	frozen = set((modifier_data or {}).get("frozen", []))
	options = [c for c in range(cells) if c not in frozen] or list(range(cells))
	started = get_datetime(rnd.started_at)
	window = max(1.0, (rnd.duration or ROUND_DURATION) - 1.0)
	for p in room.players:
		if not p.is_bot or p.eliminated:
			continue
		sel = frappe.new_doc(SELECTION_DOCTYPE)
		sel.round = rnd.name
		sel.room_code = room.room_code
		sel.player_token = p.player_token
		sel.username = p.username
		sel.selected_square = random.choice(options)
		sel.submitted_at = add_to_date(started, seconds=random.uniform(0.3, window))
		sel.insert(ignore_permissions=True)


def _abilities(player) -> dict:
	try:
		return json.loads(player.abilities) if player.abilities else {}
	except Exception:
		return {}


def _begin_new_game(room):
	"""Reset every player and kick off round 1. Shared by the first start and by
	an instant rematch."""
	for p in room.players:
		p.eliminated = 0
		p.place = 0
		p.points = 0
		p.abilities = json.dumps(dict(STARTING_ABILITIES))
		p.shield_round = None
	room.status = "Playing"
	room.winner_name = None
	room.last_reveal = None
	room.start_grid = starting_grid_for(len(room.players))
	_create_round(room, 1, room.start_grid, start_offset=0)


@frappe.whitelist(allow_guest=True)
def start_game(room_code: str, player_token: str):
	room = _get_room(room_code)
	if room.host_token != player_token:
		frappe.throw("Only the host can start the game.")
	if room.status != "Lobby":
		frappe.throw("Game already started.")
	if len(room.players) < MIN_PLAYERS:
		frappe.throw(f"Need at least {MIN_PLAYERS} players to start.")

	_begin_new_game(room)
	room.save(ignore_permissions=True)
	broadcast(room)
	return get_room_state(room, player_token)


@frappe.whitelist(allow_guest=True)
def submit_selection(room_code: str, player_token: str, selected_square: int):
	room = _get_room(room_code)
	player = _player_by_token(room, player_token)
	if not player:
		frappe.throw("You are not in this room.")
	if player.eliminated:
		frappe.throw("You have been eliminated.")
	if room.status != "Playing":
		frappe.throw("No active round.")

	rnd = _latest_round(room.room_code)
	if not rnd or rnd.resolved:
		frappe.throw("Round is not accepting selections.")

	now = now_datetime()
	if now < get_datetime(rnd.started_at):
		frappe.throw("Round has not started yet.")
	if now > add_to_date(get_datetime(rnd.deadline), seconds=SUBMIT_GRACE):
		frappe.throw("Time is up.")

	selected_square = int(selected_square)
	cells = rnd.grid_size * rnd.grid_size
	if selected_square < 0 or selected_square >= cells:
		frappe.throw("Invalid square.")

	modifier_data = json.loads(rnd.modifier_data) if rnd.modifier_data else {}
	if selected_square in set(modifier_data.get("frozen", [])):
		frappe.throw("That tile is frozen this round — pick another.")

	# Upsert: one selection per player per round (last pick wins) — this is how
	# duplicate submissions are prevented.
	existing = frappe.get_all(
		SELECTION_DOCTYPE,
		filters={"round": rnd.name, "player_token": player_token},
		fields=["name"],
		limit=1,
	)
	if existing:
		frappe.db.set_value(
			SELECTION_DOCTYPE,
			existing[0].name,
			{"selected_square": selected_square, "submitted_at": now},
		)
	else:
		sel = frappe.new_doc(SELECTION_DOCTYPE)
		sel.round = rnd.name
		sel.room_code = room.room_code
		sel.player_token = player_token
		sel.username = player.username
		sel.selected_square = selected_square
		sel.submitted_at = now
		sel.insert(ignore_permissions=True)

	frappe.db.commit()
	# Broadcast only the updated submission count (never which square).
	broadcast(room)
	return {"ok": True, "selected_square": selected_square}


@frappe.whitelist(allow_guest=True)
def resolve_round(room_code: str):
	"""Idempotent, server-timed resolution. Any client may call this at the
	deadline; the server validates the timing and resolves exactly once."""
	room = _get_room(room_code)
	if room.status != "Playing":
		return get_room_state(room)

	rnd = _latest_round(room.room_code)
	if not rnd:
		return get_room_state(room)

	# Lock the round row so concurrent resolve() calls serialize; the loser
	# sees resolved=1 and bails out.
	locked_resolved = frappe.db.get_value(
		ROUND_DOCTYPE, rnd.name, "resolved", for_update=True
	)
	if locked_resolved:
		return get_room_state(room)

	now = now_datetime()
	if now < get_datetime(rnd.deadline):
		# Too early — not authoritative time yet.
		return get_room_state(room)

	_resolve(room, rnd)
	room.save(ignore_permissions=True)
	frappe.db.commit()
	broadcast(room)
	return get_room_state(room)


def _resolve(room, rnd):
	grid_size = rnd.grid_size
	cells = grid_size * grid_size
	modifier_data = json.loads(rnd.modifier_data) if rnd.modifier_data else {}
	frozen = set(modifier_data.get("frozen", []))
	bonus_square = modifier_data.get("bonus")
	bombed = set(json.loads(rnd.bombs) if rnd.bombs else [])

	active = [p for p in room.players if not p.eliminated]

	# Gather selections; auto-assign a random (non-frozen) square to non-pickers.
	sels = frappe.get_all(
		SELECTION_DOCTYPE,
		filters={"round": rnd.name},
		fields=["player_token", "username", "selected_square", "submitted_at"],
	)
	by_token = {s.player_token: s.selected_square for s in sels}
	time_by_token = {s.player_token: s.submitted_at for s in sels}
	auto_opts = [c for c in range(cells) if c not in frozen] or list(range(cells))

	picks = {}  # square -> [players]
	chosen = {}  # player_token -> square
	for p in active:
		sq = by_token.get(p.player_token)
		if sq is None:
			sq = random.choice(auto_opts)
		sq = int(sq)
		chosen[p.player_token] = sq
		picks.setdefault(sq, []).append(p)

	exploded_squares = [sq for sq, plist in picks.items() if len(plist) > 1]
	bombed_hit = [sq for sq in bombed if sq in picks]

	rnd.status = "Resolved"
	rnd.resolved = 1

	# A player is doomed if they collided OR sat on a bombed square...
	doomed = set()
	for sq in exploded_squares:
		doomed.update(p.player_token for p in picks[sq])
	for sq in bombed_hit:
		doomed.update(p.player_token for p in picks[sq])

	# ...unless they spent a Shield this round, which rescues them.
	shielded_names = []
	for p in active:
		if p.shield_round == rnd.name:
			if p.player_token in doomed:
				doomed.discard(p.player_token)
				shielded_names.append(p.username)
			p.shield_round = None  # shield is consumed regardless

	survivors = [p for p in active if p.player_token not in doomed]
	eliminated_now = [p for p in active if p.player_token in doomed]

	# Resolution outcome:
	#   * Someone doomed, someone left -> eliminate the doomed.
	#   * Everyone doomed (mutual wipeout) -> void & replay, nobody out.
	#   * Nobody doomed (no collisions/bombs): shrink the grid, or on the final 2x2
	#     break the deadlock on speed (slowest picker out).
	replay = False
	tiebreak = False
	shrink_only = False

	if eliminated_now:
		if not survivors:
			replay = True
			eliminated_now = []
	elif len(active) > 1:
		if grid_size <= MIN_GRID:
			tiebreak = True
			loser = _slowest_picker(active, time_by_token)
			eliminated_now = [loser]
			survivors = [p for p in active if p.player_token != loser.player_token]
		else:
			shrink_only = True

	if eliminated_now:
		place_for_eliminated = len(survivors) + 1
		for p in eliminated_now:
			p.eliminated = 1
			p.place = place_for_eliminated
			p.points = (p.points or 0) + points_for_place(place_for_eliminated)

	# Bonus Tile: a lone survivor sitting on it banks extra points.
	bonus_winner = None
	if bonus_square is not None and not replay:
		on_bonus = picks.get(bonus_square, [])
		if len(on_bonus) == 1 and on_bonus[0].player_token not in doomed:
			on_bonus[0].points = (on_bonus[0].points or 0) + BONUS_POINTS
			bonus_winner = on_bonus[0].username

	reveal = {
		"round_number": rnd.round_number,
		"grid_size": grid_size,
		"prompt": rnd.prompt,
		"labels": json.loads(rnd.labels) if rnd.labels else [],
		"modifier": rnd.modifier,
		"modifier_data": modifier_data,
		"selections": [
			{"username": p.username, "square": chosen[p.player_token]} for p in active
		],
		"exploded_squares": exploded_squares,
		"bombed_squares": bombed_hit,
		"shielded": shielded_names,
		"bonus_square": bonus_square,
		"bonus_winner": bonus_winner,
		"eliminated": [p.username for p in eliminated_now],
		"survivors": [p.username for p in survivors],
		"replay": replay,
		"tiebreak": tiebreak,
		"tiebreak_square": chosen[eliminated_now[0].player_token] if tiebreak else None,
		"shrink_only": shrink_only,
	}
	rnd.reveal_data = json.dumps(reveal)
	rnd.save(ignore_permissions=True)
	room.last_reveal = json.dumps(reveal)

	# Decide what comes next.
	if not replay and len(survivors) == 1:
		_finish_game(room, survivors[0])
		return

	if replay:
		# Same round number, same grid, fresh selections.
		_create_round(room, rnd.round_number, grid_size, start_offset=REVEAL_DELAY)
	else:
		next_number = rnd.round_number + 1
		_create_round(
			room,
			next_number,
			grid_size_for_round(next_number, room.start_grid or grid_size),
			start_offset=REVEAL_DELAY,
		)


def _slowest_picker(players, time_by_token):
	"""Return the player who locked in last. A player who never submitted (auto-
	assigned a random square) is treated as the slowest of all."""

	def lateness(p):
		t = time_by_token.get(p.player_token)
		if t is None:
			return (1, "")  # no pick at all -> slowest
		return (0, get_datetime(t))

	return max(players, key=lateness)


def _finish_game(room, winner):
	winner.eliminated = 0
	winner.place = 1
	winner.points = (winner.points or 0) + points_for_place(1)
	# Per-room session tally — counts wins across rematches in THIS room only.
	winner.wins = (winner.wins or 0) + 1
	room.status = "Finished"
	room.winner_name = winner.username


@frappe.whitelist(allow_guest=True)
def restart_game(room_code: str, player_token: str):
	"""Instant rematch: same room, same players, straight into a new game."""
	room = _get_room(room_code)
	if room.host_token != player_token:
		frappe.throw("Only the host can start a new game.")
	if room.status != "Finished":
		frappe.throw("Game is still in progress.")
	if len(room.players) < MIN_PLAYERS:
		frappe.throw(f"Need at least {MIN_PLAYERS} players to start.")

	_begin_new_game(room)
	room.save(ignore_permissions=True)
	broadcast(room)
	return get_room_state(room, player_token)


@frappe.whitelist(allow_guest=True)
def play_again(room_code: str, player_token: str):
	"""Back to the lobby with the same players (lets people join/leave before the
	next game). For a straight rematch use restart_game."""
	room = _get_room(room_code)
	if room.host_token != player_token:
		frappe.throw("Only the host can restart.")
	if room.status != "Finished":
		frappe.throw("Game is still in progress.")

	for p in room.players:
		p.eliminated = 0
		p.place = 0
		p.points = 0
	room.status = "Lobby"
	room.current_round = 0
	room.grid_size = 0
	room.winner_name = None
	room.last_reveal = None
	room.save(ignore_permissions=True)
	broadcast(room)
	return get_room_state(room, player_token)


# ---------------------------------------------------------------------------
# Bots
# ---------------------------------------------------------------------------


def _free_bot_name(room) -> str:
	taken = {p.username.lower() for p in room.players}
	for name in random.sample(BOT_NAMES, len(BOT_NAMES)):
		if name.lower() not in taken:
			return name
	# Fallback if every fun name is taken.
	i = 1
	while f"Bot {i}".lower() in taken:
		i += 1
	return f"Bot {i}"


@frappe.whitelist(allow_guest=True)
def add_bots(room_code: str, player_token: str, count: int = 1):
	room = _get_room(room_code)
	if room.host_token != player_token:
		frappe.throw("Only the host can add bots.")
	if room.status != "Lobby":
		frappe.throw("Bots can only be added in the lobby.")

	count = max(1, int(count))
	room_left = MAX_PLAYERS - len(room.players)
	if room_left <= 0:
		frappe.throw(f"Room is full (max {MAX_PLAYERS} players).")
	for _ in range(min(count, room_left)):
		room.append(
			"players",
			{
				"player_token": _gen_token(),
				"username": _free_bot_name(room),
				"is_host": 0,
				"connected": 1,
				"is_bot": 1,
			},
		)
	room.save(ignore_permissions=True)
	broadcast(room)
	return get_room_state(room, player_token)


@frappe.whitelist(allow_guest=True)
def remove_bot(room_code: str, player_token: str, bot_name: str):
	room = _get_room(room_code)
	if room.host_token != player_token:
		frappe.throw("Only the host can remove bots.")
	if room.status != "Lobby":
		frappe.throw("Bots can only be removed in the lobby.")
	kept, removed = [], False
	for p in room.players:
		if not removed and p.is_bot and p.username == bot_name:
			removed = True
			continue
		kept.append(p)
	room.players = kept
	room.save(ignore_permissions=True)
	broadcast(room)
	return get_room_state(room, player_token)


# ---------------------------------------------------------------------------
# Reactions (ephemeral taunts)
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def send_reaction(room_code: str, player_token: str, emoji: str):
	room = _get_room(room_code)
	player = _player_by_token(room, player_token)
	if not player:
		frappe.throw("You are not in this room.")
	if emoji not in REACTION_EMOJIS:
		frappe.throw("Unknown reaction.")
	frappe.publish_realtime(
		event=f"lss:{room.room_code}:reaction",
		message={"username": player.username, "emoji": emoji},
		room="website",
	)
	return {"ok": True}


# ---------------------------------------------------------------------------
# Power-ups / abilities
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def use_ability(room_code: str, player_token: str, ability: str, target_square: int | None = None):
	room = _get_room(room_code)
	player = _player_by_token(room, player_token)
	if not player:
		frappe.throw("You are not in this room.")
	if player.eliminated:
		frappe.throw("You have been eliminated.")
	if room.status != "Playing":
		frappe.throw("No active round.")

	rnd = _latest_round(room.room_code)
	if not rnd or rnd.resolved:
		frappe.throw("Round is not accepting abilities.")
	now = now_datetime()
	if now < get_datetime(rnd.started_at):
		frappe.throw("Round has not started yet.")
	if now > add_to_date(get_datetime(rnd.deadline), seconds=SUBMIT_GRACE):
		frappe.throw("Time is up.")

	ability = (ability or "").lower()
	inv = _abilities(player)
	if inv.get(ability, 0) <= 0:
		frappe.throw(f"No {ability} left.")

	cells = rnd.grid_size * rnd.grid_size

	if ability == "peek":
		ts = int(target_square)
		if ts < 0 or ts >= cells:
			frappe.throw("Invalid square.")
		count = frappe.db.count(SELECTION_DOCTYPE, {"round": rnd.name, "selected_square": ts})
		inv["peek"] -= 1
		player.abilities = json.dumps(inv)
		room.save(ignore_permissions=True)
		frappe.db.commit()
		broadcast(room)
		return {"ok": True, "ability": "peek", "square": ts, "count": count}

	if ability == "shield":
		player.shield_round = rnd.name
		inv["shield"] -= 1
		player.abilities = json.dumps(inv)
		room.save(ignore_permissions=True)
		frappe.db.commit()
		broadcast(room)
		return {"ok": True, "ability": "shield"}

	if ability == "bomb":
		ts = int(target_square)
		if ts < 0 or ts >= cells:
			frappe.throw("Invalid square.")
		bombs = json.loads(rnd.bombs) if rnd.bombs else []
		if ts not in bombs:
			bombs.append(ts)
		frappe.db.set_value(ROUND_DOCTYPE, rnd.name, "bombs", json.dumps(bombs))
		inv["bomb"] -= 1
		player.abilities = json.dumps(inv)
		room.save(ignore_permissions=True)
		frappe.db.commit()
		broadcast(room)
		return {"ok": True, "ability": "bomb", "square": ts}

	frappe.throw("Unknown ability.")
