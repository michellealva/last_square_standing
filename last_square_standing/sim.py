# Copyright (c) 2024, Michelle and contributors
"""Headless simulation/smoke-test of the game engine (no browser needed).

Run:  bench --site lss.localhost execute last_square_standing.sim.run
"""

import json

import frappe

from last_square_standing import api

# Make the core flow deterministic — no random modifier rounds. Modifiers are
# tested separately by constructing them explicitly.
api.MODIFIER_CHANCE = 0


def _force_deadline_passed(room_code):
	"""Pretend the round timer has expired so resolve_round will act."""
	rnd = api._latest_round(room_code)
	past = frappe.utils.add_to_date(frappe.utils.now_datetime(), seconds=-1)
	frappe.db.set_value("LSS Round", rnd.name, {"started_at": past, "deadline": past})
	frappe.db.commit()
	return api.get_room_state(frappe.get_doc("LSS Room", room_code))


def _begin_round_now(room_code):
	"""Skip the reveal delay: make the latest round open for selections now."""
	rnd = api._latest_round(room_code)
	now = frappe.utils.now_datetime()
	frappe.db.set_value(
		"LSS Round",
		rnd.name,
		{"started_at": now, "deadline": frappe.utils.add_to_date(now, seconds=10)},
	)
	frappe.db.commit()


def _started_game(n, prefix):
	"""Create a room with n human players, start it, return (code, tokens, host_token)."""
	host = api.create_room(f"{prefix}0", f"{prefix} room")
	code = host["room_code"]
	for i in range(1, n):
		api.join_room(code, f"{prefix}{i}")
	api.start_game(code, host["player_token"])
	tokens = {p.username: p.player_token for p in frappe.get_doc("LSS Room", code).players}
	return code, tokens, host["player_token"]


def run():
	frappe.set_user("Administrator")

	# === Grid scaling ===
	assert api.starting_grid_for(3) == 3, api.starting_grid_for(3)
	assert api.starting_grid_for(4) == 4, api.starting_grid_for(4)
	assert api.starting_grid_for(10) == 5, api.starting_grid_for(10)
	assert api.starting_grid_for(500) == api.MAX_GRID, "should cap at MAX_GRID"
	assert api.grid_size_for_round(1, 6) == 6 and api.grid_size_for_round(5, 6) == 2
	print("[ok] grid scales with players (3->3, 4->4, 10->5, capped) and shrinks per round")

	# === Core game (4 players -> 4x4 start) ===
	host = api.create_room("Michelle", "Sim Room")
	code = host["room_code"]
	for name in ["Rahul", "Sara", "Aman"]:
		api.join_room(code, name)
	state = api.get_state(code)
	assert state["player_count"] == 4 and state["status"] == "Lobby"

	try:
		api.start_game(code, "not-the-host")
		raise AssertionError("non-host should not start")
	except frappe.ValidationError:
		pass

	api.start_game(code, host["player_token"])
	state = api.get_state(code, host["player_token"])
	assert state["status"] == "Playing"
	assert state["round"]["grid_size"] == 4, state["round"]["grid_size"]
	assert len(state["round"]["labels"]) == 16 and state["round"]["prompt"]
	assert state["me"]["abilities"] == {"shield": 1, "peek": 1, "bomb": 1}
	print("[ok] 4 players -> 4x4 start; each player has shield/peek/bomb")

	tokens = {p.username: p.player_token for p in frappe.get_doc("LSS Room", code).players}

	# Round 1: Michelle & Rahul collide on 0; Sara->1, Aman->2 survive.
	api.submit_selection(code, tokens["Michelle"], 0)
	api.submit_selection(code, tokens["Rahul"], 0)
	api.submit_selection(code, tokens["Sara"], 1)
	api.submit_selection(code, tokens["Aman"], 2)
	mine = api.get_state(code, tokens["Sara"])
	assert mine["me"]["selected_square"] == 1
	assert "selected_square" not in mine["players"][0], "must not leak others' squares"
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	rev = state["reveal"]
	assert set(rev["eliminated"]) == {"Michelle", "Rahul"}, rev["eliminated"]
	assert set(rev["survivors"]) == {"Sara", "Aman"}, rev["survivors"]
	assert state["round"]["grid_size"] == 3, "should shrink to 3x3"
	print("[ok] round 1: Michelle & Rahul eliminated; grid shrank to 3x3")

	again = api.resolve_round(code)
	assert again["round"]["round_number"] == state["round"]["round_number"]
	print("[ok] resolve_round is idempotent")

	# Round 2 (3x3): both collide -> nobody survives -> replay.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 5)
	api.submit_selection(code, tokens["Aman"], 5)
	r2 = api._latest_round(code).round_number
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["replay"] is True
	assert api._latest_round(code).round_number == r2
	assert state["alive_count"] == 2
	print("[ok] mutual collision -> replay, both still alive")

	# Replay (3x3): no collision on a shrinkable grid -> nobody out, shrink to 2x2.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 0)
	api.submit_selection(code, tokens["Aman"], 1)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["shrink_only"] is True
	assert state["round"]["grid_size"] == 2, "should now be at terminal 2x2"
	print("[ok] no collision on 3x3 -> nobody out, grid shrank to 2x2")

	# 2x2 showdown: no collision -> speed tiebreak. Sara first, Aman slower -> Sara wins.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 0)
	api.submit_selection(code, tokens["Aman"], 1)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	rev = state["reveal"]
	assert rev["tiebreak"] is True and rev["eliminated"] == ["Aman"], rev
	assert state["status"] == "Finished" and state["winner_name"] == "Sara"
	assert state["rankings"][0]["place"] == 1 and state["rankings"][0]["points"] == 100
	print("[ok] 2x2 showdown: Aman (slowest) out -> Sara wins (+100)")

	sara = next(p for p in state["players"] if p["username"] == "Sara")
	assert sara["wins"] == 1, sara
	print("[ok] per-room tally: winner has 1 win")

	# Instant rematch keeps the room and the session win tally.
	state = api.restart_game(code, host["player_token"])
	assert state["status"] == "Playing" and state["round"]["round_number"] == 1
	assert next(p for p in state["players"] if p["username"] == "Sara")["wins"] == 1, (
		"session wins must persist across a rematch"
	)
	# Drive the rematch to a finish, then play_again returns to the lobby.
	guard = 0
	while api.get_state(code)["status"] == "Playing":
		guard += 1
		assert guard < 40, "rematch did not converge"
		_begin_round_now(code)
		alive = [p for p in frappe.get_doc("LSS Room", code).players if not p.eliminated]
		cells = api._latest_round(code).grid_size ** 2
		for i, p in enumerate(alive):
			api.submit_selection(code, p.player_token, i % cells)
		_force_deadline_passed(code)
		api.resolve_round(code)
	api.play_again(code, host["player_token"])
	assert api.get_state(code)["status"] == "Lobby"
	print("[ok] restart_game (instant) and play_again (lobby) both work; wins persist")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# === Abilities ===
	# Shield rescues a collided player.
	code, tok, _ = _started_game(3, "Sh")
	api.submit_selection(code, tok["Sh0"], 0)
	api.submit_selection(code, tok["Sh1"], 0)  # collides with Sh0
	api.submit_selection(code, tok["Sh2"], 1)
	api.use_ability(code, tok["Sh0"], "shield")
	_force_deadline_passed(code)
	rev = api.resolve_round(code)["reveal"]
	assert "Sh0" in rev["shielded"] and "Sh0" not in rev["eliminated"]
	assert "Sh1" in rev["eliminated"], rev["eliminated"]
	print("[ok] ability Shield: rescued a collided player")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# Bomb eliminates a lone player on the targeted square.
	code, tok, _ = _started_game(3, "Bm")
	api.submit_selection(code, tok["Bm0"], 0)
	api.submit_selection(code, tok["Bm1"], 1)  # alone on square 1
	api.submit_selection(code, tok["Bm2"], 2)
	api.use_ability(code, tok["Bm0"], "bomb", 1)
	_force_deadline_passed(code)
	rev = api.resolve_round(code)["reveal"]
	assert 1 in rev["bombed_squares"] and "Bm1" in rev["eliminated"], rev
	print("[ok] ability Bomb: blew up a lone player")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# Peek returns a square's live pick-count without leaking identities.
	code, tok, _ = _started_game(3, "Pk")
	api.submit_selection(code, tok["Pk1"], 5)
	api.submit_selection(code, tok["Pk2"], 5)
	res = api.use_ability(code, tok["Pk0"], "peek", 5)
	assert res["count"] == 2, res
	assert api.get_state(code, tok["Pk0"])["me"]["abilities"]["peek"] == 0
	print("[ok] ability Peek: reported count=2 and was consumed")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# === Modifier rounds ===
	# Frozen: rejects a frozen pick; bots/auto avoid them.
	code, tok, _ = _started_game(3, "Fz")
	rnd = api._latest_round(code)
	frappe.db.set_value("LSS Round", rnd.name, "modifier", "frozen")
	frappe.db.set_value("LSS Round", rnd.name, "modifier_data", json.dumps({"frozen": [0, 1, 2]}))
	frappe.db.commit()
	try:
		api.submit_selection(code, tok["Fz0"], 0)
		raise AssertionError("frozen tile should be rejected")
	except frappe.ValidationError:
		pass
	api.submit_selection(code, tok["Fz0"], 5)  # non-frozen is fine
	print("[ok] modifier Frozen: frozen tile rejected, free tile accepted")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# Bonus: lone survivor on the bonus tile banks bonus points.
	code, tok, _ = _started_game(3, "Bn")
	rnd = api._latest_round(code)
	frappe.db.set_value("LSS Round", rnd.name, "modifier", "bonus")
	frappe.db.set_value("LSS Round", rnd.name, "modifier_data", json.dumps({"bonus": 4}))
	frappe.db.commit()
	api.submit_selection(code, tok["Bn0"], 4)  # alone on bonus
	api.submit_selection(code, tok["Bn1"], 1)
	api.submit_selection(code, tok["Bn2"], 2)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["bonus_winner"] == "Bn0", state["reveal"]
	pts = {p["username"]: p["points"] for p in state["players"]}
	assert pts["Bn0"] == api.BONUS_POINTS, pts
	print(f"[ok] modifier Bonus: lone survivor banked +{api.BONUS_POINTS}")
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)

	# Sudden Death shortens the timer.
	saved = api.MODIFIERS
	api.MODIFIERS, api.MODIFIER_CHANCE = ["sudden_death"], 1
	m, _d, dur = api._roll_modifier(2, 3, 2)
	assert m == "sudden_death" and dur == api.SUDDEN_DEATH_DURATION < api.ROUND_DURATION
	api.MODIFIERS, api.MODIFIER_CHANCE = saved, 0
	print("[ok] modifier Sudden Death: shorter timer")

	# === Bots ===
	bhost = api.create_room("BotHost", "Bot room")
	bcode = bhost["room_code"]
	api.join_room(bcode, "Human2")
	st = api.add_bots(bcode, bhost["player_token"], 3)
	assert st["player_count"] == 5 and sum(p["is_bot"] for p in st["players"]) == 3
	a_bot = next(p["username"] for p in st["players"] if p["is_bot"])
	st = api.remove_bot(bcode, bhost["player_token"], a_bot)
	assert st["player_count"] == 4 and sum(p["is_bot"] for p in st["players"]) == 2
	api.start_game(bcode, bhost["player_token"])
	rnd = api._latest_round(bcode)
	assert frappe.db.count("LSS Selection", {"round": rnd.name}) == 2, "2 bots should auto-pick"
	print("[ok] bots: added 3, removed 1, 2 bots auto-locked at round start")

	guard = 0
	while api.get_state(bcode)["status"] == "Playing":
		guard += 1
		assert guard < 80, "bot game did not converge"
		_begin_round_now(bcode)
		humans = [
			p for p in frappe.get_doc("LSS Room", bcode).players
			if not p.eliminated and not p.is_bot
		]
		cells = api._latest_round(bcode).grid_size ** 2
		for i, p in enumerate(humans):
			api.submit_selection(bcode, p.player_token, i % cells)
		_force_deadline_passed(bcode)
		api.resolve_round(bcode)
	final = api.get_state(bcode)
	assert final["status"] == "Finished" and final["winner_name"]
	assert sum(p["wins"] for p in final["players"]) == 1, "exactly one winner recorded"
	print("[ok] bot game converged to a winner with bots in play")

	# === Reactions ===
	assert api.send_reaction(bcode, bhost["player_token"], "🔥")["ok"] is True
	try:
		api.send_reaction(bcode, bhost["player_token"], "not-an-emoji")
		raise AssertionError("invalid reaction should be rejected")
	except frappe.ValidationError:
		pass
	print("[ok] reactions: valid emoji accepted, junk rejected")
	frappe.delete_doc("LSS Room", bcode, force=True, ignore_permissions=True)
	frappe.db.commit()
	print("\nALL ENGINE CHECKS PASSED ✅")
