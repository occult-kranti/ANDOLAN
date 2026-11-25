extends Node3D
## One data-driven offline kit on the current practice clock and receivers.
## Events expose authority geometry and accepted changes to presentation only.

signal ability_event(event: Dictionary)
signal changed

const Geometry = preload("res://scripts/ultimate_rules.gd")
const PROFILE := "res://assets/design/hanuman-ability-kit.json"
const SLOTS := ["primary", "ability_1", "ability_2", "ability_3", "ultimate"]
const MAX_CASTS := 3
const MAX_RECEIVERS := 72
const MAX_HISTORY := 64
const STEP := .05
const EPSILON := 1e-8

var army: Node3D
var configured := false
var suspended := false
var elapsed := 0.0
var generation := 0
var _next_id := 0
var _seq := 0
var _action_id := 0
var _locked := false
var _abilities: Dictionary = {}
var _casts: Dictionary = {}
var _cooldowns: Dictionary = {}
var _history: Array[Dictionary] = []
var _move := Callable()
var _hero: Node
var _hero_position := Callable()
var _notice := "Hanuman is ready"

static func load_profile(path := PROFILE) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null or file.get_length() > 32768:
		return {}
	var source := file.get_as_text()
	if Geometry._duplicate_or_deep(source):
		return {}
	var data: Variant = JSON.parse_string(source)
	if not data is Dictionary or data.get("schema_version") != 1 or data.get("hero_id") != "hanuman":
		return {}
	var entries: Variant = data.get("abilities")
	if not entries is Array or entries.size() != SLOTS.size():
		return {}
	var definitions: Dictionary = {}
	for index in entries.size():
		var rule: Variant = entries[index]
		if not _valid_rule(rule, SLOTS[index]) or definitions.has(rule.id):
			return {}
		definitions[rule.id] = rule
	return definitions

static func _valid_rule(rule: Variant, slot: String) -> bool:
	if not rule is Dictionary or rule.get("slot") != slot:
		return false
	for key in ["id", "label", "description", "motion", "color"]:
		if not rule.get(key) is String or rule[key].is_empty() or rule[key].length() > 240:
			return false
	if not Color.html_is_valid(rule.color) or not Geometry.number(rule.get("motion_phase"), .05, .95):
		return false
	var timing: Variant = rule.get("timing")
	if not timing is Dictionary or not Geometry.number(rule.get("cooldown_s"), .25, 90):
		return false
	for key in ["windup_s", "travel_s", "active_s", "recovery_s"]:
		if not Geometry.number(timing.get(key), STEP if key in ["windup_s", "recovery_s"] else 0.0, 3.0):
			return false
	if float(rule.cooldown_s) + EPSILON < float(timing.windup_s) + float(timing.travel_s) + maxf(float(timing.recovery_s), float(timing.active_s)):
		return false
	var g: Variant = rule.get("geometry")
	if not g is Dictionary or not Geometry.number(g.get("height_m"), .1, 3):
		return false
	var kind: Variant = g.get("kind")
	var anchor: Variant = g.get("anchor")
	if kind not in ["sector", "disk", "movement"] or anchor not in ["caster", "ground_target"] or g.get("direction", "front") not in ["front", "rear"]:
		return false
	if anchor == "ground_target" or kind == "movement":
		if not Geometry.number(g.get("target_range_m"), .25, 16):
			return false
	if kind == "sector" and (not Geometry.number(g.get("range_m"), .25, 10) or not Geometry.number(g.get("half_angle_cos"), 0, .99)):
		return false
	if kind == "disk" and not Geometry.number(g.get("radius_m"), .25, 9):
		return false
	var effects: Variant = rule.get("effects")
	if not effects is Array:
		return false
	if kind == "movement":
		return anchor == "caster" and effects.is_empty() and Geometry.number(g.get("clearance_m"), .2, 1) and Geometry.number(timing.travel_s, .1, 1)
	if effects.is_empty() or effects.size() > 3:
		return false
	var seen: Dictionary = {}
	for effect in effects:
		if not effect is Dictionary:
			return false
		var effect_kind: Variant = effect.get("kind")
		if effect_kind not in ["damage", "damage_rate", "shield", "heal"] or seen.has(effect_kind):
			return false
		var hostile: bool = effect_kind in ["damage", "damage_rate"]
		if effect.get("team") != ("enemy" if hostile else "ally"):
			return false
		if typeof(effect.get("include_caster", false)) != TYPE_BOOL or (hostile and effect.get("include_caster", false)):
			return false
		if effect_kind == "damage_rate":
			if not Geometry.number(effect.get("amount_per_s"), .1, 20) or float(timing.active_s) < STEP:
				return false
		elif not Geometry.number(effect.get("amount"), .1, 100):
			return false
		if effect_kind == "shield" and not Geometry.number(effect.get("duration_s"), .1, 6):
			return false
		seen[effect_kind] = true
	return true

func configure(simulation: Node3D, move_receiver := Callable(), hero_receiver: Node = null, hero_position := Callable()) -> bool:
	if _locked or not is_instance_valid(simulation) or not simulation.get("configured"):
		return false
	for sig in ["simulation_stepped", "simulation_reset", "outcome"]:
		if not simulation.has_signal(sig):
			return false
	for method in ["_blocked_with", "segment_wall_fraction", "line_clear"]:
		if not simulation.has_method(method):
			return false
	if not simulation.get("units") is Array or not simulation.get("boxes") is Array or not simulation.get("actor_bounds") is Array:
		return false
	if hero_receiver != null and (not hero_position.is_valid() or not hero_receiver.has_method("apply_shield") or not hero_receiver.has_method("receive_heal")):
		return false
	var profile := load_profile()
	if profile.is_empty():
		return false
	cancel_active("reconfigure")
	_disconnect_army()
	army = simulation
	_move = move_receiver
	_hero = hero_receiver
	_hero_position = hero_position
	_abilities = profile
	suspended = false
	army.simulation_stepped.connect(_on_step)
	army.simulation_reset.connect(reset)
	army.outcome.connect(_on_outcome)
	configured = true
	reset("configure")
	return true

func _disconnect_army() -> void:
	if not is_instance_valid(army):
		return
	if army.simulation_stepped.is_connected(_on_step):
		army.simulation_stepped.disconnect(_on_step)
	if army.simulation_reset.is_connected(reset):
		army.simulation_reset.disconnect(reset)
	if army.outcome.is_connected(_on_outcome):
		army.outcome.disconnect(_on_outcome)

func _exit_tree() -> void:
	configured = false
	cancel_active("scene_exit")
	_disconnect_army()

func _available() -> bool:
	return configured and not suspended and is_inside_tree() and not get_tree().paused and is_instance_valid(army) and army.configured and not army.get("suspended") and army.winner.is_empty()

func set_suspended(value: bool) -> void:
	suspended = value
	changed.emit()

func _reject(reason: String) -> Dictionary:
	_notice = reason
	return {"accepted": false, "reason": reason, "generation": generation, "cast_id": 0}

func request_ability(id: String, origin: Vector3, aim: Vector3, ground_target: Vector3) -> Dictionary:
	if _locked or not _available() or (is_instance_valid(_hero) and not _hero.get("alive")):
		return _reject("Return to practice to cast")
	if not _abilities.has(id):
		return _reject("Unknown ability")
	if _action_id != 0 or _casts.size() >= MAX_CASTS:
		return _reject("Finish the current action")
	if elapsed + EPSILON < float(_cooldowns.get(id, 0.0)):
		return _reject("Ability is cooling down")
	if not origin.is_finite() or not aim.is_finite() or not ground_target.is_finite():
		return _reject("Choose a finite aim")
	var forward := Vector3(aim.x, 0, aim.z)
	if not is_finite(forward.length_squared()) or forward.length_squared() < .0001:
		return _reject("Choose a horizontal aim")
	forward = forward.normalized()
	var local: Vector3 = army.to_local(origin)
	if absf(local.y) > .35:
		return _reject("Land before casting")
	local.y = 0
	if army._blocked_with(local, army.boxes, army.actor_bounds, .05):
		return _reject("Cast origin is blocked")
	var rule: Dictionary = _abilities[id]
	var geometry: Dictionary = rule.geometry.duplicate(true)
	var fixed_origin: Vector3 = army.to_global(local)
	var destination := fixed_origin
	if geometry.anchor == "ground_target":
		var target: Vector3 = army.to_local(ground_target)
		if absf(target.y) > .15:
			return _reject("Aim at the courtyard floor")
		target.y = 0
		if local.distance_to(target) > float(geometry.target_range_m) + .000001:
			return _reject("Ground target is out of range")
		if army._blocked_with(target, army.boxes, army.actor_bounds, .05) or not army.line_clear(local, target):
			return _reject("Cover blocks the ground target")
		destination = army.to_global(target)
	elif geometry.kind == "movement":
		if not _move.is_valid():
			return _reject("Vault receiver is unavailable")
		var endpoint: Vector3 = army.to_local(fixed_origin + forward * float(geometry.target_range_m))
		var wall: float = army.segment_wall_fraction(local, endpoint, float(geometry.clearance_m))
		if is_finite(wall):
			endpoint = local.lerp(endpoint, maxf(0.0, wall - .025))
		var bounds: Array = army.actor_bounds
		endpoint.x = clampf(endpoint.x, float(bounds[0]) + float(geometry.clearance_m), float(bounds[1]) - float(geometry.clearance_m))
		endpoint.z = clampf(endpoint.z, float(bounds[2]) + float(geometry.clearance_m), float(bounds[3]) - float(geometry.clearance_m))
		if local.distance_to(endpoint) < .5:
			return _reject("There is no room to vault")
		destination = army.to_global(endpoint)
	geometry.origin = fixed_origin
	geometry.center = destination
	geometry.forward = -forward if geometry.get("direction") == "rear" else forward
	_next_id += 1
	var cast := {"id": _next_id, "generation": generation, "rule": rule, "geometry": geometry, "started": elapsed,
		"origin": fixed_origin, "forward": forward, "target": destination, "released": false, "impacted": false, "recovered": false}
	_casts[_next_id] = cast
	_action_id = _next_id
	_cooldowns[id] = elapsed + float(rule.cooldown_s)
	_notice = rule.label + " · preparing"
	var response := {"accepted": true, "reason": _notice, "generation": generation, "cast_id": _next_id}
	_emit("begin", cast)
	changed.emit()
	return response

func _on_outcome(_winner: String) -> void:
	cancel_active("round ended")

func _same(cast: Dictionary) -> bool:
	return generation == int(cast.generation) and _casts.has(cast.id)

func _end_cast(cast: Dictionary, kind: String, reason := "") -> void:
	_casts.erase(cast.id)
	if _action_id == int(cast.id):
		_action_id = 0
	_emit(kind, cast, [], reason)

func _clear_casts(reason: String) -> void:
	var retired: Array = _casts.values()
	_casts.clear()
	_action_id = 0
	for cast in retired:
		_emit("cancel", cast, [], reason)

func cancel_active(reason := "cancelled") -> void:
	if _locked:
		return
	_locked = true
	_clear_casts(reason)
	_notice = reason
	changed.emit()
	_locked = false

func reset(reason := "reset") -> void:
	if _locked:
		return
	_locked = true
	_clear_casts(reason)
	generation += 1
	_next_id = 0
	_seq = 0
	elapsed = 0
	_cooldowns.clear()
	_history.clear()
	_notice = "Hanuman is ready"
	_emit("reset", {}, [], reason)
	changed.emit()
	_locked = false

func _on_step(delta: float) -> void:
	if not _available() or not Geometry.number(delta, EPSILON, STEP + .000001):
		return
	if is_instance_valid(_hero) and not _hero.get("alive"):
		cancel_active("defeated")
		return
	var previous := elapsed
	elapsed += delta
	for id in _casts.keys():
		if _casts.has(id):
			_advance(_casts[id], previous)
	changed.emit()

func _advance(cast: Dictionary, previous: float) -> void:
	var timing: Dictionary = cast.rule.timing
	var age: float = elapsed - float(cast.started)
	var release_at: float = float(timing.windup_s)
	var impact_at := release_at + float(timing.travel_s)
	var active_end := impact_at + float(timing.active_s)
	var recovered_at := impact_at + float(timing.recovery_s)
	if not cast.released and age + EPSILON >= release_at:
		cast.released = true
		if cast.geometry.kind == "movement":
			var current: Vector3 = army.to_local(cast.origin)
			var destination: Vector3 = army.to_local(cast.target)
			if not army.line_clear(current, destination, float(cast.geometry.clearance_m)) or not _move.is_valid() or _move.call(cast.origin, cast.target, float(timing.travel_s)) != true:
				if _same(cast):
					_end_cast(cast, "cancel", "Vault became obstructed")
				return
			if not _same(cast):
				return
		_notice = String(cast.rule.label) + " · released"
		_emit("release", cast)
		if not _same(cast):
			return
		if cast.geometry.kind == "movement":
			# This receipt starts an accepted sweep. Actual movement belongs to
			# the player's CharacterBody controller and can be shortened by cover.
			_emit("impact", cast, [], "movement_accepted")
			if not _same(cast):
				return
	if not cast.impacted and age + EPSILON >= impact_at:
		cast.impacted = true
		if cast.geometry.kind != "movement":
			var receipts := _apply(cast, 0.0)
			if not _same(cast):
				return
			_emit("impact", cast, receipts, "hit" if not receipts.is_empty() else "clear")
			if not _same(cast):
				return
	var exposure := minf(age, active_end) - maxf(previous - float(cast.started), impact_at)
	if exposure > EPSILON:
		var receipts := _apply(cast, exposure)
		if not _same(cast):
			return
		_emit("tick", cast, receipts)
		if not _same(cast):
			return
	if not cast.recovered and age + EPSILON >= recovered_at:
		cast.recovered = true
		if _action_id == int(cast.id):
			_action_id = 0
		_notice = "Hanuman is ready"
		_emit("recovery", cast)
		if not _same(cast):
			return
	if age + EPSILON >= maxf(active_end, recovered_at):
		_end_cast(cast, "end")

func _apply(cast: Dictionary, duration: float) -> Array:
	var receipts: Array = []
	var geometry: Dictionary = cast.geometry
	for unit in army.units.slice(0, MAX_RECEIVERS):
		if not _same(cast):
			return []
		if not is_instance_valid(unit) or not unit.alive or unit.team not in ["sun", "moon"]:
			continue
		var point: Vector3 = unit.global_position
		if Geometry.contains(geometry, point) and army.line_clear(army.to_local(geometry.center), army.to_local(point)):
			var receipt := _apply_receiver(cast, unit, unit.team == "sun", false, point, duration)
			if not receipt.is_empty():
				receipts.append(receipt)
	if _same(cast) and is_instance_valid(_hero) and _hero.get("alive") and _hero_position.is_valid() and receipts.size() < MAX_RECEIVERS:
		var point: Variant = _hero_position.call()
		if _same(cast) and point is Vector3 and Geometry.contains(geometry, point) and army.line_clear(army.to_local(geometry.center), army.to_local(point)):
			var receipt := _apply_receiver(cast, _hero, true, true, point, duration)
			if not receipt.is_empty():
				receipts.append(receipt)
	return receipts

func _apply_receiver(cast: Dictionary, receiver: Node, ally: bool, caster: bool, point: Vector3, duration: float) -> Dictionary:
	var before: float = receiver.health
	var shield_before: float = receiver.shield
	var id: int = 0 if caster else int(receiver.unit_id)
	var kinds: Array[String] = []
	var damage := 0.0
	var healing := 0.0
	for effect in cast.rule.effects:
		if not is_instance_valid(receiver) or not receiver.alive:
			break
		if ally != (effect.team == "ally") or (caster and not effect.get("include_caster", false)):
			continue
		var kind: String = effect.kind
		if (duration > 0.0) != (kind == "damage_rate"):
			continue
		if kind in ["damage", "damage_rate"]:
			var previous: float = receiver.health + receiver.shield
			var value: float = float(effect.amount_per_s) * duration if duration > 0.0 else float(effect.amount)
			var accepted: bool = receiver.take_hit(value)
			if not _same(cast) or not is_instance_valid(receiver):
				return {}
			if accepted:
				damage += maxf(0, previous - float(receiver.health) - float(receiver.shield))
				kinds.append(kind)
		elif kind == "heal":
			var applied: float = receiver.receive_heal(effect.amount)
			if applied > 0.0:
				healing += applied
				kinds.append(kind)
		elif receiver.apply_shield(effect.amount, effect.duration_s):
			kinds.append(kind)
		if not _same(cast) or not is_instance_valid(receiver):
			return {}
	if kinds.is_empty():
		return {}
	return {"unit_id": id, "kind": "payload", "effects": kinds, "position": point, "health_before": before,
		"health_after": receiver.health, "shield_before": shield_before, "shield_after": receiver.shield,
		"damage_applied": damage, "healing_applied": healing, "status_until_s": receiver.shield_until}

func _emit(kind: String, cast: Dictionary, receipts: Array = [], reason := "") -> void:
	_seq += 1
	var rule: Dictionary = cast.get("rule", {})
	var event := {
		"schema": 1, "kind": kind, "generation": generation, "event_seq": _seq, "cast_id": int(cast.get("id", 0)),
		"hero_id": "hanuman", "ability_id": rule.get("id", ""), "label": rule.get("label", ""), "motion": rule.get("motion", ""),
		"motion_phase": rule.get("motion_phase", 0.0), "color": rule.get("color", ""),
		"time_s": elapsed, "age_s": elapsed - float(cast.get("started", elapsed)),
		"origin": cast.get("origin", Vector3.ZERO), "forward": cast.get("forward", Vector3.FORWARD), "target": cast.get("target", Vector3.ZERO),
		"timing": rule.get("timing", {}).duplicate(true), "geometry": cast.get("geometry", {}).duplicate(true),
		"receipts": receipts.duplicate(true), "reason": reason,
	}
	_history.append(event.duplicate(true))
	if _history.size() > MAX_HISTORY:
		_history.pop_front()
	ability_event.emit(event)

func report(include_history := true) -> Dictionary:
	var abilities: Array = []
	for rule in _abilities.values():
		var status: Dictionary = rule.duplicate(true)
		status.cooldown_remaining = maxf(0, float(_cooldowns.get(rule.id, 0.0)) - elapsed)
		abilities.append(status)
	var cast: Dictionary = _casts.get(_action_id, {})
	var phase := "ready"
	if not cast.is_empty():
		phase = "windup" if not cast.released else ("travel" if not cast.impacted else "recovery")
	var state := {"configured": configured, "suspended": suspended, "hero_id": "hanuman", "abilities": abilities,
		"generation": generation, "elapsed": elapsed, "active_cast_id": _action_id, "action_locked": _action_id != 0,
		"phase": phase, "notice": _notice, "network_enabled": false}
	if include_history:
		state.history = _history.duplicate(true)
	return state
