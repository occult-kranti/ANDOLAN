extends SceneTree
const Client = preload("res://scripts/arena_client.gd")
const Interpolator = preload("res://scripts/arena_interpolator.gd")
var checks: Array[Dictionary] = []
var options: Dictionary = {}
var client: Node
var sampler: RefCounted
var recordings: Array[Dictionary] = []
var welcome_count := 0
var finish_count := 0
var initial_id := ""
var initial_room := ""
var initial_position := Vector2.ZERO
var moved := 0.0
var peer_id := ""
var local_ack := -1
var peer_ack := -1
var last_tick := -1
var monotonic_ticks := true
var purchase_ok := false
var resumed_progress := false
var command_id := ""
var faults: Array[String] = []
var states: Array[String] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--") and "=" in argument:
			var parts := argument.trim_prefix("--").split("=", true, 1)
			options[parts[0]] = parts[1]
	call_deferred("_run")

func _run() -> void:
	Engine.max_fps = 120
	var before := FileAccess.get_sha256("res://scripts/arena_client.gd")
	_defensive()
	if options.has("url"): await _live()
	_record("source_unchanged", before == FileAccess.get_sha256("res://scripts/arena_client.gd"), {})
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed": passed, "engine": Engine.get_version_info().string, "adapter_sha256": before,
		"test_sha256": FileAccess.get_sha256("res://tests/arena_client_cases.gd"), "role": options.get("role", "fixture"), "checks": checks, "states": states, "fault_codes": faults,
		"scope": "Explicit defensive fixtures plus, when requested, one of two independent headless native clients on the real loopback authority. No renderer or WAN performance claim."}
	if options.has("report"):
		var file := FileAccess.open(options.report, FileAccess.WRITE)
		file.store_string(JSON.stringify(report, "\t") + "\n")
	print("YUGA_ARENA_CLIENT_REPORT ", JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)

func _fixture() -> Dictionary:
	return {"protocol": 2, "room": "FIXTURE", "tick": 1, "time": 0.05, "duration": 8.0, "phase": "playing", "winner": null, "reason": "", "seed": 1,
		"actors": [{"id": "local", "heroId": "rama", "name": "Fixture", "kind": "hero", "team": "sun", "lane": 0, "bot": false, "connected": true, "x": 0, "y": 0, "z": 0, "yaw": 0, "health": 300, "maxHealth": 300, "lastInputSeq": -1,
			"shield": 0, "respawn": 0, "fireCooldown": 0, "credits": 180, "level": 1, "kills": 0, "deaths": 0, "assists": 0, "damageDealt": 0, "cooldowns": [0, 0, 0], "upgrades": {"power": 0, "vitality": 0, "tempo": 0}, "effects": {"haste": 0, "slow": 0, "ward": 0}}],
		"neutrals": [], "goldShards": [], "structures": [], "projectiles": [], "zones": [], "pickups": [], "events": [], "scores": {"sun": 0, "moon": 0}}

func _defensive() -> void:
	var probe := Client.new()
	_record("no_reconnect_without_session", probe.reconnect_arena() == ERR_UNCONFIGURED, {})
	_record("invalid_endpoint_rejected_locally", probe.connect_arena("https://invalid", "rama", "name") == ERR_INVALID_PARAMETER and probe.connect_arena("ws://user:secret@localhost/ws", "rama", "name") == ERR_INVALID_PARAMETER, {})
	probe.state = "joining"
	probe._handle_message(JSON.parse_string(JSON.stringify({"type": "welcome", "protocol": 2, "id": "local", "room": "FIXTURE", "token": "a".repeat(48), "snapshot": _fixture()})))
	_record("json_float_fields_accept_valid_welcome", probe.state == "playing" and probe.identity == "local", {})
	var base: Dictionary = probe.get_snapshot()
	var detached: Dictionary = probe.get_snapshot()
	detached.actors[0].health = -999
	_record("snapshot_copy_cannot_mutate_internal_state", probe.get_snapshot().actors[0].health == 300, {})
	probe._handle_message({"type": "snapshot", "snapshot": base})
	_record("duplicate_tick_dropped", probe.stale_snapshots == 1, {})
	var rejected := 0
	for variant in 10:
		var bad := base.duplicate(true)
		match variant:
			0: bad.protocol = 1
			1: bad.actors[0].health = NAN
			2: bad.actors.append(bad.actors[0].duplicate(true))
			3: bad.projectiles.resize(193)
			4: bad.room = "FOREIGN"
			5: bad.actors[0].erase("cooldowns")
			6: bad.actors[0].x = 1e200
			7: bad.actors[0].yaw = JSON.parse_string('{"yaw":1e308}').yaw
			8: bad.actors[0].yaw = JSON.parse_string('{"yaw":-1e308}').yaw
			9: bad.time = JSON.parse_string('{"time":1e-50}').time
		var count: int = probe.rejected_packets
		probe._handle_message({"type": "snapshot", "snapshot": bad})
		if probe.rejected_packets == count + 1 and probe.get_snapshot().actors[0].health == 300: rejected += 1
		base.tick += 1
		base.time += 0.05
		probe._handle_message({"type": "snapshot", "snapshot": base})
	_record("malformed_and_literal_numeric_inputs_preserve_last_good_state", rejected == 10 and probe.state == "playing", {"rejected_variants": rejected})
	var tiny := base.duplicate(true)
	tiny.tick += 1
	tiny.time += 0.000000001
	var count: int = probe.rejected_packets
	probe._handle_message({"type": "snapshot", "snapshot": tiny})
	_record("tiny_positive_server_delta_rejected", probe.rejected_packets == count + 1 and probe.last_tick == int(base.tick), {})
	for index in 32: probe._pending["bounded_%d" % index] = Time.get_ticks_msec()
	_record("pending_commands_bounded", probe.send_ability(0).is_empty() and probe.pending_command_count() == 32, {})
	base.tick += 1
	base.phase = "finished"
	base.winner = "draw"
	base.events = [{"id": 1, "type": "victory", "actorId": "", "team": "sun", "label": "Time limit", "color": "#fff", "time": base.time, "x": 0, "z": 0}]
	probe._handle_message({"type": "snapshot", "snapshot": base})
	base.tick += 1
	base.phase = "playing"
	base.winner = null
	probe._handle_message({"type": "snapshot", "snapshot": base})
	_record("victory_empty_actor_and_final_phase_handled", probe.state == "finished" and probe.pending_command_count() == 0 and probe.get_snapshot().phase == "finished", {})
	probe.disconnect_arena()
	probe.state = "joining"
	for index in 5: probe._handle_message({"type": "unknown"})
	_record("invalid_message_budget_disconnects", probe.state == "disconnected", {})
	probe.free()

func _live() -> void:
	var role: String = options.get("role", "host")
	var room_code := ""
	if role == "guest":
		var deadline := Time.get_ticks_msec() + 10000
		while room_code.is_empty() and Time.get_ticks_msec() < deadline:
			if FileAccess.file_exists(options.coordination):
				var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(options.coordination))
				if data is Dictionary and data.get("room") is String: room_code = data.room
			await create_timer(0.02).timeout
		if room_code.is_empty():
			_record("host_room_available", false, {})
			return
	client = Client.new()
	sampler = Interpolator.new()
	root.add_child(client)
	client.state_changed.connect(func(value: String):
		states.append(value)
		if value == "connecting": sampler.reset())
	client.welcomed.connect(_on_welcome)
	client.snapshot_received.connect(_on_snapshot)
	client.protocol_fault.connect(func(code: String): faults.append(code))
	client.match_finished.connect(func(_result: Dictionary): finish_count += 1)
	client.command_result.connect(func(result: Dictionary):
		if result.id == command_id: purchase_ok = result.ok and result.code == "UPGRADED")
	_record("connect_started", client.connect_arena(options.url, "rama", "Native " + role, room_code) == OK, {})
	var start := Time.get_ticks_msec()
	var joined := 0
	var burst := false
	var reconnect := false
	var sequence_before := -1
	var previous_render_time := -1.0
	var monotonic_render := true
	var finite_poses := true
	var interpolated := 0
	while Time.get_ticks_msec() - start < 16000:
		if client.state == "playing":
			if joined == 0: joined = Time.get_ticks_msec()
			var elapsed := Time.get_ticks_msec() - joined
			if command_id.is_empty(): command_id = client.send_upgrade("power")
			client.send_input(Vector2(1.0 if role == "host" else -1.0, 0) if elapsed < 1200 else Vector2.ZERO, 0, 0, false, false)
			if not burst and elapsed > 500:
				burst = true
				var accepted := 0
				for index in 128:
					if not client.send_ability(0).is_empty(): accepted += 1
				_record("button_burst_limited_locally", accepted == 1, {"attempts": 128, "sent": accepted})
			if role == "host" and not options.has("no-reconnect") and not reconnect and elapsed > 1800:
				reconnect = true
				sequence_before = client.sent_sequence
				_record("reconnect_started", client.reconnect_arena() == OK, {})
				previous_render_time = -1.0
		var frame: Dictionary = sampler.sample()
		monotonic_render = monotonic_render and float(frame.render_time) >= previous_render_time
		previous_render_time = frame.render_time
		for actor in frame.actors:
			finite_poses = finite_poses and Vector3(actor.x, actor.y, actor.z).is_finite() and is_finite(float(actor.yaw))
			if actor.presentation_mode == "interpolated": interpolated += 1
		if client.state == "finished": break
		await process_frame
	_record("unique_shared_room_peers", not peer_id.is_empty() and peer_id != initial_id, {"identity": initial_id, "peer": peer_id, "room": initial_room})
	_record("authoritative_movement_and_ordered_ack", moved > 0.5 and local_ack >= 10 and peer_ack >= 10 and monotonic_ticks, {"distance": moved, "local_ack": local_ack, "peer_ack": peer_ack, "last_tick": last_tick})
	_record("server_command_receipt", purchase_ok, {})
	_record("live_bad_packets_filtered", client.rejected_packets >= 2 and client.stale_snapshots >= 1 and "INVALID_JSON" in faults and "INVALID_SNAPSHOT" in faults, {"rejected": client.rejected_packets, "stale": client.stale_snapshots})
	if role == "host" and not options.has("no-reconnect"):
		_record("reconnect_preserves_identity_progress_sequence", welcome_count == 2 and client.identity == initial_id and resumed_progress and local_ack > sequence_before, {"sequence_before": sequence_before, "ack_after": local_ack})
	_record("one_final_result_blocks_intent", finish_count == 1 and not client.send_input(Vector2.ONE, 0, 0, true, true) and client.send_ability(0).is_empty(), {"finish_count": finish_count})
	_record("live_interpolator_finite_and_monotonic", finite_poses and monotonic_render and interpolated > 10, {"interpolated_actor_samples": interpolated, "snapshots": recordings.size()})
	if options.has("recording"):
		var file := FileAccess.open(options.recording, FileAccess.WRITE)
		for record in recordings: file.store_line(JSON.stringify(record))
	client.disconnect_arena()
	await create_timer(0.15).timeout
	_record("disconnect_clears_session_and_snapshots", client.state == "disconnected" and not client.can_reconnect() and client.get_snapshot().is_empty() and client.get_previous_snapshot().is_empty() and client.pending_command_count() == 0, {})
	client.queue_free()
	await process_frame

func _on_welcome(value: Dictionary) -> void:
	welcome_count += 1
	if initial_id.is_empty():
		initial_id = value.id
		initial_room = value.room
		if options.get("role") == "host":
			var file := FileAccess.open(options.coordination, FileAccess.WRITE)
			file.store_string(JSON.stringify({"id": value.id, "room": value.room}))
	else:
		for actor in client.get_snapshot().actors:
			if actor.id == initial_id: resumed_progress = actor.credits == 60 and actor.upgrades.power == 1

func _on_snapshot(snapshot: Dictionary) -> void:
	var received := float(Time.get_ticks_usec()) / 1000000.0
	recordings.append({"received": received, "snapshot": snapshot.duplicate(true)})
	sampler.push_snapshot(snapshot, received)
	monotonic_ticks = monotonic_ticks and int(snapshot.tick) >= last_tick
	last_tick = int(snapshot.tick)
	for actor in snapshot.actors:
		if actor.id == client.identity:
			var position := Vector2(actor.x, actor.z)
			if welcome_count == 0: initial_position = position
			moved = maxf(moved, position.distance_to(initial_position))
			local_ack = maxi(local_ack, int(actor.lastInputSeq))
		elif actor.kind == "hero" and actor.connected and not actor.bot:
			peer_id = actor.id
			peer_ack = maxi(peer_ack, int(actor.lastInputSeq))

func _record(label: String, passed: bool, details: Dictionary) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)
