extends RefCounted
## Presentation-only actor poses from accepted protocol-2 authority snapshots.
const MAX_SNAPSHOTS := 32
const MIN_INTERVAL_SECONDS := 0.000001
const MAX_ABS_YAW := TAU
const MAX_MATCH_DURATION_SECONDS := 4800.0
var accepted_snapshots := 0
var rejected_snapshots := 0
var stale_snapshots := 0
var clock_regressions := 0
var rejected_computations := 0
var _room := ""
var _buffer: Array[Dictionary] = []
var _offset_samples: Array[float] = []
var _clock_offset := 0.0
var _last_local_time := -1.0
var _render_time := -1.0
var _delay := 0.1
var _extrapolation := 0.1
var _teleport_distance := 6.0
var _maximum_gap := 0.5
var _maximum_speed := 35.0
var _finished := false

func configure(delay_seconds := 0.1, extrapolation_seconds := 0.1, teleport_distance := 6.0, maximum_gap_seconds := 0.5, maximum_speed := 35.0) -> Error:
	for value in [delay_seconds, extrapolation_seconds, teleport_distance, maximum_gap_seconds, maximum_speed]:
		if not is_finite(value): return ERR_INVALID_PARAMETER
	if delay_seconds < 0 or delay_seconds > 1 or extrapolation_seconds < 0 or extrapolation_seconds > 0.25 or teleport_distance <= 0 or maximum_gap_seconds < MIN_INTERVAL_SECONDS or maximum_gap_seconds > 2 or maximum_speed <= 0 or maximum_speed > 1000:
		return ERR_INVALID_PARAMETER
	_delay = delay_seconds
	_extrapolation = extrapolation_seconds
	_teleport_distance = teleport_distance
	_maximum_gap = maximum_gap_seconds
	_maximum_speed = maximum_speed
	return OK

func reset(expected_room := "") -> void:
	_room = expected_room
	_buffer.clear()
	_offset_samples.clear()
	_clock_offset = 0.0
	_last_local_time = -1.0
	_render_time = -1.0
	_finished = false

func room_code() -> String:
	return _room

func buffered_snapshot_count() -> int:
	return _buffer.size()

func settings() -> Dictionary:
	return {"delay_seconds": _delay, "extrapolation_seconds": _extrapolation, "teleport_distance": _teleport_distance, "maximum_gap_seconds": _maximum_gap, "maximum_speed": _maximum_speed, "maximum_snapshots": MAX_SNAPSHOTS, "minimum_interval_seconds": MIN_INTERVAL_SECONDS, "maximum_absolute_yaw": MAX_ABS_YAW, "maximum_match_duration_seconds": MAX_MATCH_DURATION_SECONDS}

func push_snapshot(snapshot: Dictionary, received_at_seconds := -1.0) -> bool:
	if not _valid_snapshot(snapshot) or not _room.is_empty() and snapshot.room != _room:
		rejected_snapshots += 1
		return false
	if not _buffer.is_empty():
		var latest: Dictionary = _buffer[-1]
		if int(snapshot.tick) <= int(latest.tick):
			stale_snapshots += 1
			return false
		var interval := float(snapshot.time) - float(latest.time)
		if interval < 0 or _finished and snapshot.phase != "finished" or interval > 0 and interval < MIN_INTERVAL_SECONDS and snapshot.phase != "finished":
			rejected_snapshots += 1
			return false
	var received := _resolve_clock(received_at_seconds)
	if not is_finite(received):
		rejected_snapshots += 1
		return false
	_room = snapshot.room
	var frozen := {"room": snapshot.room, "tick": int(snapshot.tick), "time": float(snapshot.time), "duration": float(snapshot.duration), "phase": snapshot.phase, "actors": {}, "order": []}
	for actor in snapshot.actors:
		frozen.actors[actor.id] = actor.duplicate(true)
		# Bound first, normalize before subtraction: finite +/-1e308 can overflow.
		frozen.actors[actor.id].yaw = wrapf(float(actor.yaw), -PI, PI)
		frozen.order.append(actor.id)
	var offset := received - float(snapshot.time)
	if _buffer.is_empty(): _clock_offset = offset
	_offset_samples.append(offset)
	if _offset_samples.size() > MAX_SNAPSHOTS: _offset_samples.pop_front()
	var fastest := _offset_samples[0]
	for candidate in _offset_samples: fastest = minf(fastest, candidate)
	_clock_offset = move_toward(_clock_offset, fastest, 0.005)
	if not _buffer.is_empty() and float(_buffer[-1].time) == float(snapshot.time): _buffer.pop_back()
	_buffer.append(frozen)
	if _buffer.size() > MAX_SNAPSHOTS: _buffer.pop_front()
	_finished = snapshot.phase == "finished"
	accepted_snapshots += 1
	return true

func sample(at_seconds := -1.0) -> Dictionary:
	var now := _resolve_clock(at_seconds)
	if not is_finite(now) or _buffer.is_empty():
		return {"room": _room, "mode": "empty", "actors": [], "render_time": maxf(0, _render_time), "source_time": 0.0, "latest_tick": -1}
	var latest: Dictionary = _buffer[-1]
	if _finished:
		_render_time = maxf(_render_time, float(latest.time))
		return _exact(latest, "finished")
	_render_time = maxf(_render_time, clampf(now - _clock_offset - _delay, 0, float(latest.duration)))
	if _render_time <= float(_buffer[0].time): return _exact(_buffer[0], "warming")
	for index in range(1, _buffer.size()):
		if _render_time < float(_buffer[index].time): return _between(_buffer[index - 1], _buffer[index])
	return _after_latest()

func _exact(source: Dictionary, mode: String) -> Dictionary:
	var actors: Array[Dictionary] = []
	for actor_id in source.order:
		var actor: Dictionary = source.actors[actor_id].duplicate(true)
		actor.presentation_mode = "held"
		actors.append(actor)
	return _frame(source, mode, actors, float(source.time))

func _between(left: Dictionary, right: Dictionary) -> Dictionary:
	var interval := float(right.time) - float(left.time)
	var fraction := clampf((_render_time - float(left.time)) / interval, 0, 1) if interval >= MIN_INTERVAL_SECONDS else 0.0
	var actors: Array[Dictionary] = []
	for actor_id in left.order:
		var actor: Dictionary = left.actors[actor_id].duplicate(true)
		actor.presentation_mode = "held"
		if right.actors.has(actor_id):
			var next: Dictionary = right.actors[actor_id]
			var discontinuity := _discontinuity(actor, next, interval)
			if discontinuity.is_empty():
				if _set_pose(actor, _position(actor).lerp(_position(next), fraction), lerp_angle(float(actor.yaw), float(next.yaw), fraction)):
					actor.presentation_mode = "interpolated"
			else: actor.presentation_discontinuity = discontinuity
		actors.append(actor)
	return _frame(left, "interpolating", actors, _render_time)

func _after_latest() -> Dictionary:
	var latest: Dictionary = _buffer[-1]
	var previous: Dictionary = _buffer[-2] if _buffer.size() >= 2 else {}
	var lag := maxf(0, _render_time - float(latest.time))
	var projected_seconds := minf(lag, _extrapolation)
	var actors: Array[Dictionary] = []
	var has_projection := false
	for actor_id in latest.order:
		var actor: Dictionary = latest.actors[actor_id].duplicate(true)
		actor.presentation_mode = "held"
		if not previous.is_empty() and previous.actors.has(actor_id) and projected_seconds > 0:
			var before: Dictionary = previous.actors[actor_id]
			var interval := float(latest.time) - float(previous.time)
			var discontinuity := _discontinuity(before, actor, interval)
			if discontinuity.is_empty() and float(actor.health) > 0 and float(actor.respawn) <= 0:
				var velocity := (_position(actor) - _position(before)) / interval
				var angular_velocity := clampf(angle_difference(float(before.yaw), float(actor.yaw)) / interval, -TAU * 2, TAU * 2)
				if _set_pose(actor, _position(actor) + velocity * projected_seconds, float(actor.yaw) + angular_velocity * projected_seconds):
					actor.presentation_mode = "extrapolated" if lag <= _extrapolation else "projection_held"
					has_projection = true
			elif not discontinuity.is_empty(): actor.presentation_discontinuity = discontinuity
		actors.append(actor)
	return _frame(latest, "extrapolating" if has_projection and lag <= _extrapolation else "holding", actors, float(latest.time) + (projected_seconds if has_projection else 0.0))

func _frame(source: Dictionary, mode: String, actors: Array[Dictionary], source_time: float) -> Dictionary:
	return {"room": _room, "mode": mode, "phase": source.phase, "actors": actors, "render_time": _render_time, "source_time": source_time, "source_tick": source.tick, "latest_tick": _buffer[-1].tick, "buffered_snapshots": _buffer.size()}

func _discontinuity(before: Dictionary, after: Dictionary, interval: float) -> String:
	# A positive JSON double like 1e-50 underflows to zero in float32 vector division.
	if not is_finite(interval) or interval < MIN_INTERVAL_SECONDS or interval > _maximum_gap: return "snapshot_gap"
	for key in ["kind", "heroId", "team", "connected"]:
		if before.get(key) != after.get(key): return "identity_or_connection"
	if (float(before.health) <= 0) != (float(after.health) <= 0) or (float(before.respawn) > 0) != (float(after.respawn) > 0): return "death_or_respawn"
	var distance := _position(before).distance_to(_position(after))
	if distance > _teleport_distance or distance / interval > _maximum_speed: return "teleport"
	return ""

func _position(actor: Dictionary) -> Vector3:
	return Vector3(float(actor.x), float(actor.y), float(actor.z))

func _set_pose(actor: Dictionary, position: Vector3, yaw: float) -> bool:
	if not position.is_finite() or not is_finite(yaw):
		_reject_computation(actor)
		return false
	var normalized := wrapf(yaw, -PI, PI)
	if not is_finite(normalized):
		_reject_computation(actor)
		return false
	# Commit all pose fields only after the complete result passes validation.
	actor.x = position.x
	actor.y = position.y
	actor.z = position.z
	actor.yaw = normalized
	return true

func _reject_computation(actor: Dictionary) -> void:
	rejected_computations += 1
	actor.presentation_mode = "held"
	actor.presentation_discontinuity = "nonfinite_computation"

func _resolve_clock(value: float) -> float:
	var now := float(Time.get_ticks_usec()) / 1000000.0 if value == -1 else value
	if not is_finite(now) or now < 0: return NAN
	if now < _last_local_time:
		clock_regressions += 1
		now = _last_local_time
	_last_local_time = now
	return now

func _number(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value))

func _valid_snapshot(snapshot: Dictionary) -> bool:
	if snapshot.get("protocol") != 2 or not snapshot.get("room") is String or snapshot.room.is_empty() or snapshot.room.length() > 16 or snapshot.get("phase") not in ["playing", "finished"]: return false
	for field in ["tick", "time", "duration"]:
		if not _number(snapshot.get(field)): return false
	if float(snapshot.tick) < 0 or float(snapshot.tick) > 9007199254740991 or floor(float(snapshot.tick)) != float(snapshot.tick) or float(snapshot.time) < 0 or float(snapshot.duration) <= 0 or float(snapshot.duration) > MAX_MATCH_DURATION_SECONDS or float(snapshot.time) > float(snapshot.duration) + 0.1: return false
	if float(snapshot.time) > 0 and float(snapshot.time) < MIN_INTERVAL_SECONDS: return false
	if not snapshot.get("actors") is Array or snapshot.actors.size() > 96: return false
	var ids := {}
	for actor in snapshot.actors:
		if not actor is Dictionary or not actor.get("id") is String or actor.id.is_empty() or actor.id.length() > 64 or ids.has(actor.id): return false
		ids[actor.id] = true
		for field in ["x", "y", "z", "yaw", "health", "respawn"]:
			if not _number(actor.get(field)): return false
		for field in ["x", "y", "z"]:
			if absf(float(actor[field])) > 10000: return false
		if absf(float(actor.yaw)) > MAX_ABS_YAW: return false
	return true
