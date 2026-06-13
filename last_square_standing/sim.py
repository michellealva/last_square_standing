# Copyright (c) 2024, Michelle and contributors
"""Headless simulation/smoke-test of the game engine (no browser needed).

Run:  bench --site lss.localhost execute last_square_standing.sim.run
"""

import frappe

from last_square_standing import api


def _force_deadline_passed(room_code):
	"""Pretend the round timer has expired so resolve_round will act."""
	rnd = api._latest_round(room_code)
	past = frappe.utils.add_to_date(frappe.utils.now_datetime(), seconds=-1)
	frappe.db.set_value("LSS Round", rnd.name, {"started_at": past, "deadline": past})
	frappe.db.commit()
	return api.get_room_state(frappe.get_doc("LSS Room", room_code))


def _begin_round_now(room_code):
	"""Skip the 5s reveal delay: make the latest round open for selections now."""
	rnd = api._latest_round(room_code)
	now = frappe.utils.now_datetime()
	frappe.db.set_value(
		"LSS Round",
		rnd.name,
		{"started_at": now, "deadline": frappe.utils.add_to_date(now, seconds=10)},
	)
	frappe.db.commit()


def run():
	frappe.set_user("Administrator")

	# Start from a clean slate so cumulative-leaderboard assertions are stable
	# across repeated runs (the winner is deterministic).
	for name in ["Michelle", "Rahul", "Sara", "Aman"]:
		if frappe.db.exists("LSS Leaderboard", name):
			frappe.delete_doc("LSS Leaderboard", name, force=True, ignore_permissions=True)
	frappe.db.commit()

	# --- create + join ---
	host = api.create_room("Michelle", "Sim Room")
	code = host["room_code"]
	rahul = api.join_room(code, "Rahul")
	api.join_room(code, "Sara")
	api.join_room(code, "Aman")
	state = api.get_state(code)
	assert state["player_count"] == 4, state["player_count"]
	assert state["status"] == "Lobby"
	print(f"[ok] room {code} created with 4 players")

	# --- min players guard ---
	try:
		api.start_game(code, "not-the-host")
		raise AssertionError("non-host should not start")
	except frappe.ValidationError:
		pass

	# --- start ---
	api.start_game(code, host["player_token"])
	state = api.get_state(code)
	assert state["status"] == "Playing"
	assert state["round"]["grid_size"] == 5, state["round"]["grid_size"]
	# Themed round: a prompt and one distinct word label per tile (25 for 5x5).
	assert state["round"]["prompt"], "round should have a themed prompt"
	labels = state["round"]["labels"]
	assert len(labels) == 25, len(labels)
	assert len(set(labels)) == 25, "tile words must be distinct"
	print(f"[ok] game started, round 1 is 5x5 — prompt: {state['round']['prompt']!r}")

	tokens = {p.username: p.player_token for p in frappe.get_doc("LSS Room", code).players}

	# Round 1: Michelle & Rahul collide on square 0; Sara->1, Aman->2 survive.
	api.submit_selection(code, tokens["Michelle"], 0)
	api.submit_selection(code, tokens["Rahul"], 0)
	api.submit_selection(code, tokens["Sara"], 1)
	api.submit_selection(code, tokens["Aman"], 2)

	# The server reflects each player's OWN pick (for tile-retention on the client)
	# and never leaks it to others.
	mine = api.get_state(code, tokens["Sara"])
	assert mine["me"]["selected_square"] == 1, mine["me"]["selected_square"]
	theirs = api.get_state(code, tokens["Aman"])
	assert theirs["me"]["selected_square"] == 2, theirs["me"]["selected_square"]
	assert "selected_square" not in theirs["players"][0], "must not leak others' squares"
	print("[ok] state reflects my own pick (square 1) and hides others'")

	_force_deadline_passed(code)
	state = api.resolve_round(code)
	rev = state["reveal"]
	assert set(rev["eliminated"]) == {"Michelle", "Rahul"}, rev["eliminated"]
	assert set(rev["survivors"]) == {"Sara", "Aman"}, rev["survivors"]
	assert state["status"] == "Playing"
	assert state["round"]["grid_size"] == 4, "round 2 should be 4x4"
	print("[ok] round 1 resolved: Michelle & Rahul eliminated; grid shrank to 4x4")

	# Idempotency: resolving again must not double-process.
	again = api.resolve_round(code)
	assert again["round"]["round_number"] == state["round"]["round_number"]
	print("[ok] resolve_round is idempotent")

	# Round 2 (4x4): both collide -> nobody survives -> replay same round.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 5)
	api.submit_selection(code, tokens["Aman"], 5)
	r2 = api._latest_round(code).round_number
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["replay"] is True, "should be a replay"
	assert api._latest_round(code).round_number == r2, "round number must not advance on replay"
	assert state["alive_count"] == 2, "nobody eliminated on replay"
	print("[ok] mutual collision -> nobody survives -> round replayed, both still alive")

	# No collision on a shrinkable grid: nobody is eliminated, the grid just shrinks.
	# 4x4 (round 2) -> 3x3 (round 3).
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 0)
	api.submit_selection(code, tokens["Aman"], 1)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["shrink_only"] is True, "no-collision big grid should just shrink"
	assert state["status"] == "Playing", state["status"]
	assert state["alive_count"] == 2, "nobody eliminated on a shrink round"
	assert state["round"]["grid_size"] == 3, state["round"]["grid_size"]
	print("[ok] no collision on 4x4 -> nobody out, grid shrank to 3x3")

	# Same again: 3x3 (round 3) -> 2x2 (round 4), still nobody out.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 0)
	api.submit_selection(code, tokens["Aman"], 1)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	assert state["reveal"]["shrink_only"] is True
	assert state["round"]["grid_size"] == 2, "should now be at the terminal 2x2 grid"
	print("[ok] no collision on 3x3 -> nobody out, grid shrank to 2x2")

	# Final 2x2 showdown: can't shrink further, so a no-collision round is a speed
	# tiebreak. Sara locks in first, Aman later -> Aman (slowest) is out, Sara wins.
	_begin_round_now(code)
	api.submit_selection(code, tokens["Sara"], 0)
	api.submit_selection(code, tokens["Aman"], 1)
	_force_deadline_passed(code)
	state = api.resolve_round(code)
	rev = state["reveal"]
	assert rev["tiebreak"] is True, "no-collision on 2x2 should be a speed tiebreak"
	assert rev["eliminated"] == ["Aman"], rev["eliminated"]
	assert state["status"] == "Finished", state["status"]
	assert state["winner_name"] == "Sara", state["winner_name"]
	print("[ok] 2x2 showdown: no collision -> slowest picker (Aman) out -> Sara wins")

	assert state["winner_name"], "must have a winner"
	rankings = state["rankings"]
	assert rankings[0]["place"] == 1 and rankings[0]["points"] == 100
	print(f"[ok] game finished. Winner: {state['winner_name']} (+100)")
	print("[ok] rankings:", [(r["username"], r["place"], r["points"]) for r in rankings])

	# Leaderboard updated for all 4 usernames.
	board = {b["username"]: b for b in api.get_leaderboard(20)}
	for name in ["Michelle", "Rahul", "Sara", "Aman"]:
		assert name in board, f"{name} missing from leaderboard"
	winner_row = board[state["winner_name"]]
	assert winner_row["wins"] == 1 and winner_row["total_score"] >= 100
	print("[ok] leaderboard updated; winner has 1 win")

	# restart_game: instant rematch, straight back into a fresh game (no lobby step).
	state = api.restart_game(code, host["player_token"])
	assert state["status"] == "Playing", state["status"]
	assert state["player_count"] == 4
	assert state["round"]["round_number"] == 1 and state["round"]["grid_size"] == 5
	assert all(not p["eliminated"] for p in state["players"])
	assert state["winner_name"] is None
	print("[ok] restart_game: instant rematch -> new game, same 4 players, round 1")

	# play_again resets to lobby keeping players (for adding/changing players).
	# Drive the rematch to a finish first: one player picks square 1, everyone else
	# collides on square 0, leaving a single survivor.
	guard = 0
	while api.get_state(code)["status"] == "Playing":
		guard += 1
		assert guard < 20, "rematch did not converge"
		_begin_round_now(code)
		alive = [p for p in frappe.get_doc("LSS Room", code).players if not p.eliminated]
		rnd = api._latest_round(code)
		cells = rnd.grid_size * rnd.grid_size
		for i, p in enumerate(alive):
			api.submit_selection(code, p.player_token, (1 if i == 0 else 0) % cells)
		_force_deadline_passed(code)
		api.resolve_round(code)
	api.play_again(code, host["player_token"])
	state = api.get_state(code)
	assert state["status"] == "Lobby" and state["player_count"] == 4
	assert all(not p["eliminated"] for p in state["players"])
	print("[ok] play_again reset room to lobby with same players")

	# Clean up the simulation room AND the leaderboard rows it created, so the
	# test never leaves sample data behind in the real leaderboard.
	frappe.delete_doc("LSS Room", code, force=True, ignore_permissions=True)
	for name in ["Michelle", "Rahul", "Sara", "Aman"]:
		if frappe.db.exists("LSS Leaderboard", name):
			frappe.delete_doc("LSS Leaderboard", name, force=True, ignore_permissions=True)
	frappe.db.commit()
	print("\nALL ENGINE CHECKS PASSED ✅")
