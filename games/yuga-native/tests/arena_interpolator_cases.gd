extends SceneTree
const Interpolator = preload("res://scripts/arena_interpolator.gd")
var checks: Array[Dictionary] = []
var options: Dictionary = {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var parts := argument.trim_prefix("--").split("=", true, 1)
			options[parts[0]] = parts[1]
	call_deferred("_run")

func _run() -> void:
	var source := FileAccess.get_sha256("res://scripts/arena_interpolator.gd")
	_cases()
	_numerical_cases()
	if options.has("replay"): _replay(options.replay)
	_record("source_unchanged", source == FileAccess.get_sha256("res://scripts/arena_interpolator.gd"), {})
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed": passed, "engine": Engine.get_version_info().string, "interpolator_sha256": source,
		"test_sha256": FileAccess.get_sha256("res://tests/arena_interpolator_cases.gd"), "settings": Interpolator.new().settings(), "checks": checks,
		"scope": "Deterministic actor sampling, literal numerical regressions and optional recorded-authority replay. No renderer, WAN or completed native online game claim."}
	if options.has("report"):
		var file := FileAccess.open(options.report, FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "\t") + "\n")
	print("YUGA_INTERPOLATOR_REPORT ", JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)

func _actor(actor_id := "hero", x := 0.0, yaw := 0.0, health := 300.0, respawn := 0.0) -> Dictionary:
	return {"id": actor_id, "x": x, "y": 0.0, "z": 0.0, "yaw": yaw, "health": health, "respawn": respawn, "kind": "hero", "heroId": "rama", "team": "sun", "connected": true, "credits": 180}

func _snapshot(time: float, actors: Array, room := "FIXTURE", phase := "playing", tick := -1) -> Dictionary:
	return {"protocol": 2, "room": room, "tick": tick if tick >= 0 else roundi(time * 20), "time": time, "duration": 8.0, "phase": phase, "actors": actors}

func _paired(x0 := 0.0, x1 := 0.2, yaw0 := 0.0, yaw1 := 0.0):
	var sampler := Interpolator.new()
	sampler.push_snapshot(_snapshot(0, [_actor("hero", x0, yaw0)]), 10.0)
	sampler.push_snapshot(_snapshot(0.1, [_actor("hero", x1, yaw1)]), 10.1)
	return sampler

func _find(frame: Dictionary, actor_id := "hero") -> Dictionary:
	for actor in frame.actors:
		if actor.id == actor_id: return actor
	return {}

func _close(actual: float, expected: float) -> bool:
	return is_finite(actual) and absf(actual - expected) < 0.00002

func _cases() -> void:
	var sampler = _paired()
	var frame: Dictionary = sampler.sample(10.15)
	_record("100ms_delay_interpolates_authority_midpoint", _close(_find(frame).x, 0.1) and _close(frame.render_time, 0.05), {})
	frame.actors[0].x = -999
	frame.actors[0].credits = -999
	_record("return_copy_cannot_mutate_history", _close(_find(sampler.sample(10.15)).x, 0.1) and _find(sampler.sample(10.15)).credits == 180, {})
	sampler = _paired(0, 0.2, deg_to_rad(179), deg_to_rad(-179))
	_record("yaw_takes_shortest_arc", absf(absf(float(_find(sampler.sample(10.15)).yaw)) - PI) < 0.00002, {})
	sampler = _paired()
	var short_loss: float = _find(sampler.sample(10.25)).x
	var long_loss: float = _find(sampler.sample(15.0)).x
	_record("extrapolation_is_bounded_then_held", _close(short_loss, 0.3) and _close(long_loss, 0.4), {"short_loss_x": short_loss, "long_loss_x": long_loss})
	sampler = _paired()
	sampler.configure(0.1, 0)
	_record("zero_extrapolation_holds_authority", _close(_find(sampler.sample(12.0)).x, 0.2), {})
	sampler = _paired(0, 40)
	var before: float = _find(sampler.sample(10.15)).x
	var after: float = _find(sampler.sample(10.21)).x
	_record("teleport_is_discrete", _close(before, 0) and _close(after, 40), {})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(0, [_actor()]), 10.0)
	sampler.push_snapshot(_snapshot(0.1, [_actor("hero", 0.4, 0, 0, 5)]), 10.1)
	var alive: Dictionary = _find(sampler.sample(10.15))
	var dead: Dictionary = _find(sampler.sample(10.21))
	sampler.push_snapshot(_snapshot(0.2, [_actor("hero", 30)]), 10.22)
	var waiting: Dictionary = _find(sampler.sample(10.25))
	var respawned: Dictionary = _find(sampler.sample(10.32))
	_record("death_respawn_are_discrete", alive.health == 300 and dead.health == 0 and waiting.health == 0 and respawned.health == 300 and _close(respawned.x, 30), {})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(0, [_actor("leaving")]), 10.0)
	sampler.push_snapshot(_snapshot(0.1, [_actor("arriving", 2)]), 10.1)
	var first: Dictionary = sampler.sample(10.15)
	var second: Dictionary = sampler.sample(10.21)
	_record("spawn_despawn_follow_source_time", not _find(first, "leaving").is_empty() and _find(first, "arriving").is_empty() and _find(second, "leaving").is_empty() and not _find(second, "arriving").is_empty(), {})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(0, [_actor()]), 10.0)
	sampler.push_snapshot(_snapshot(1, [_actor("hero", 1)]), 11.0)
	before = _find(sampler.sample(11.0)).x
	after = _find(sampler.sample(11.2)).x
	_record("long_gap_holds_then_snaps", _close(before, 0) and _close(after, 1), {})
	sampler = _paired()
	var duplicate: bool = sampler.push_snapshot(_snapshot(0.1, [_actor("hero", 999)]), 10.12)
	var old: bool = sampler.push_snapshot(_snapshot(0, [_actor("hero", 999)]), 10.13)
	var regressed: bool = sampler.push_snapshot(_snapshot(0.05, [_actor()], "FIXTURE", "playing", 3), 10.14)
	_record("out_of_order_and_time_regression_rejected", not duplicate and not old and not regressed and sampler.stale_snapshots == 2, {})
	before = sampler.sample(10.18).render_time
	after = sampler.sample(9.0).render_time
	_record("clock_does_not_reverse", after >= before and sampler.clock_regressions == 1, {})
	var foreign: bool = sampler.push_snapshot(_snapshot(0.2, [_actor()], "NEWROOM"), 10.2)
	sampler.reset("NEWROOM")
	var accepted: bool = sampler.push_snapshot(_snapshot(0, [_actor("new", 7)], "NEWROOM"), 20.0)
	_record("room_reset_drops_history", not foreign and accepted and _find(sampler.sample(20.0)).is_empty() and _find(sampler.sample(20.0), "new").x == 7, {})
	sampler.reset("NEWROOM")
	sampler.push_snapshot(_snapshot(0, [_actor("resumed", -2)], "NEWROOM"), 30.0)
	_record("same_room_reconnect_resets_clock_and_actors", sampler.buffered_snapshot_count() == 1 and _find(sampler.sample(30.0), "new").is_empty() and _find(sampler.sample(30.0), "resumed").x == -2, {})
	sampler = Interpolator.new()
	var empty: Dictionary = sampler.sample(0)
	sampler.push_snapshot(_snapshot(0, []), 0)
	_record("empty_room_and_buffer_safe", empty.mode == "empty" and sampler.sample(0.1).actors.is_empty(), {})
	sampler = _paired()
	sampler.push_snapshot(_snapshot(0.15, [_actor("hero", 0.3)], "FIXTURE", "finished", 3), 10.15)
	first = sampler.sample(10.15)
	second = sampler.sample(20.0)
	_record("finished_exact_pose_frozen", first.mode == "finished" and _close(_find(first).x, 0.3) and _close(_find(second).x, 0.3) and _close(first.render_time, second.render_time) and not sampler.push_snapshot(_snapshot(0.2, [_actor()], "FIXTURE", "playing", 4), 20.0), {})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(0.1, [_actor("hero", 0.2)], "FIXTURE", "playing", 2), 10.1)
	sampler.push_snapshot(_snapshot(0.1, [_actor("hero", 0.3)], "FIXTURE", "playing", 3), 10.12)
	_record("same_time_coalesces", sampler.buffered_snapshot_count() == 1 and _close(_find(sampler.sample(10.4)).x, 0.3), {})
	sampler = Interpolator.new()
	var source := _snapshot(0, [_actor()])
	sampler.push_snapshot(source, 0)
	source.actors[0].x = 888
	var bad := _snapshot(0.1, [_actor()])
	bad.actors[0].x = NAN
	_record("bad_pose_and_input_mutation_cannot_poison_history", not sampler.push_snapshot(bad, 0.1) and _close(_find(sampler.sample(0.1)).x, 0) and sampler.configure(NAN) == ERR_INVALID_PARAMETER, {})
	for index in range(1, 48): sampler.push_snapshot(_snapshot(index * 0.1, [_actor("hero", index * 0.1)]), index * 0.1)
	_record("history_bounded_to_32", sampler.buffered_snapshot_count() == 32, {})
	sampler = Interpolator.new()
	var arrivals := [0.0, 0.14, 0.27, 0.31, 0.49, 0.53]
	var cursor := 0
	var previous_time := -1.0
	var error := 0.0
	var monotonic := true
	for step in 80:
		var now := step * 0.01
		while cursor < arrivals.size() and float(arrivals[cursor]) <= now:
			sampler.push_snapshot(_snapshot(cursor * 0.1, [_actor("hero", cursor * 0.2)]), arrivals[cursor])
			cursor += 1
		frame = sampler.sample(now)
		if not frame.actors.is_empty():
			monotonic = monotonic and float(frame.render_time) >= previous_time
			previous_time = frame.render_time
			error = maxf(error, absf(float(_find(frame).x) - 2 * float(frame.source_time)))
	_record("jitter_preserves_authoritative_linear_fixture", monotonic and error < 0.00002, {"maximum_error": error})

func _numerical_cases() -> void:
	var positive: float = JSON.parse_string('{"yaw":1e308}').yaw
	var negative: float = JSON.parse_string('{"yaw":-1e308}').yaw
	var subnormal: float = JSON.parse_string('{"time":1e-50}').time
	# Fresh reconstruction of the two unsafe arithmetic expressions; this is
	# deliberately labelled separately from the original lost workspace probe.
	var unsafe_yaw := lerp_angle(positive, negative, 0.5)
	var unsafe_position := Vector3.ZERO / subnormal
	_record("reconstructed_prior_formulas_reproduce_nan", subnormal > 0 and not is_finite(unsafe_yaw) and not unsafe_position.is_finite(), {"yaw_finite": is_finite(unsafe_yaw), "position_finite": unsafe_position.is_finite(), "literal_time_positive": subnormal > 0})
	var sampler := Interpolator.new()
	var left := _snapshot(0, [_actor("hero", 0, positive)], "FIXTURE", "playing", 1)
	var right := _snapshot(0.1, [_actor("hero", 0, negative)], "FIXTURE", "playing", 2)
	var a := sampler.push_snapshot(left, 10.0)
	var b := sampler.push_snapshot(right, 10.1)
	_record("literal_extreme_yaw_rejected_before_arithmetic", not a and not b and sampler.sample(10.15).actors.is_empty(), {"accepted_left": a, "accepted_right": b})
	sampler = Interpolator.new()
	left = _snapshot(0, [_actor()], "FIXTURE", "playing", 1)
	right = _snapshot(subnormal, [_actor()], "FIXTURE", "playing", 2)
	a = sampler.push_snapshot(left, 10.0)
	b = sampler.push_snapshot(right, 10.1)
	var frame: Dictionary = sampler.sample(10.3)
	_record("literal_subnormal_interval_rejected_without_nan", a and not b and _close(float(frame.actors[0].x), 0), {"accepted_right": b, "x_finite": is_finite(float(frame.actors[0].x))})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(1, [_actor()]), 10.0)
	right = _snapshot(1.000000001, [_actor()], "FIXTURE", "playing", 21)
	_record("tiny_normal_timestamp_delta_rejected", not sampler.push_snapshot(right, 10.1), {})
	right.phase = "finished"
	right.actors[0].x = 0.25
	a = sampler.push_snapshot(right, 10.2)
	frame = sampler.sample(10.3)
	_record("tiny_terminal_remainder_freezes_without_division", a and frame.mode == "finished" and _close(frame.actors[0].x, 0.25), {})
	sampler = Interpolator.new()
	sampler.push_snapshot(_snapshot(0, [_actor("hero", 0, TAU - 0.1)]), 10.0)
	_record("accepted_yaw_normalized_before_storage", _close(_find(sampler.sample(10.0)).yaw, -0.1), {})
	var actor := _actor("hero", 3, 0.25)
	sampler._set_pose(actor, Vector3(NAN, 0, 0), 0.5)
	var guarded := _close(actor.x, 3) and _close(actor.yaw, 0.25)
	sampler._set_pose(actor, Vector3(4, 0, 0), NAN)
	_record("computed_nonfinite_pose_is_atomic", guarded and _close(actor.x, 3) and _close(actor.yaw, 0.25), {})

func _replay(path: String) -> void:
	var records: Array[Dictionary] = []
	for line in FileAccess.get_file_as_string(path).split("\n", false):
		var parsed: Variant = JSON.parse_string(line)
		if parsed is Dictionary: records.append(parsed)
	if records.size() < 2:
		_record("recording_has_snapshots", false, {})
		return
	for impaired in [false, true]:
		var events: Array[Dictionary] = []
		for index in records.size():
			if impaired and index % 7 == 3 and index != records.size() - 1: continue
			var delay: float = [0.0, 0.14, 0.02, 0.09, 0.0][index % 5] if impaired else 0.0
			var arrival := float(records[index].received) + delay
			events.append({"at": arrival, "snapshot": records[index].snapshot})
			if impaired and index % 9 == 0: events.append({"at": arrival + 0.22, "snapshot": records[index].snapshot})
		events.sort_custom(func(a: Dictionary, b: Dictionary): return float(a.at) < float(b.at))
		var sampler := Interpolator.new()
		var cursor := 0
		var now: float = events[0].at
		var end: float = events[-1].at + 0.4
		var previous_time := -1.0
		var monotonic := true
		var finite := true
		var maximum_projection := 0.0
		var latest: Dictionary = {}
		var frames := 0
		while now <= end:
			while cursor < events.size() and float(events[cursor].at) <= now:
				if sampler.push_snapshot(events[cursor].snapshot, events[cursor].at): latest = events[cursor].snapshot
				cursor += 1
			var frame: Dictionary = sampler.sample(now)
			monotonic = monotonic and float(frame.render_time) >= previous_time
			previous_time = frame.render_time
			for actor in frame.actors:
				finite = finite and Vector3(actor.x, actor.y, actor.z).is_finite() and is_finite(float(actor.yaw))
				if actor.presentation_mode in ["extrapolated", "projection_held"]:
					for original in latest.actors:
						if original.id == actor.id: maximum_projection = maxf(maximum_projection, Vector3(actor.x, actor.y, actor.z).distance_to(Vector3(original.x, original.y, original.z)))
			frames += 1
			now += 1.0 / 120.0
		_record("recorded_authority_impaired" if impaired else "recorded_authority_original", monotonic and finite and maximum_projection <= 3.5001 and sampler.accepted_snapshots > 10 and (not impaired or sampler.stale_snapshots > 0), {"recording_sha256": FileAccess.get_sha256(path), "source_snapshots": records.size(), "accepted": sampler.accepted_snapshots, "stale_dropped": sampler.stale_snapshots, "frames": frames, "maximum_projection_metres": maximum_projection})

func _record(label: String, passed: bool, details: Dictionary) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)
