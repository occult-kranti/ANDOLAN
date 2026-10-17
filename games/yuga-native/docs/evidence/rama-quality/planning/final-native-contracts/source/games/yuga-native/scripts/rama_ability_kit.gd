extends Node3D
## Rama's actual offline combat owner. The army clock alone releases attacks.
## Presentation receives immutable event snapshots and never mutates receivers.
signal ability_event(event: Dictionary)
signal changed

const RULES_PATH := "res://assets/design/rama-ability-kit.json"
const Geometry = preload("res://scripts/ultimate_rules.gd")
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const MAX_CASTS := 12
const HISTORY_CAP := 96
var army: Node3D
var configured := false
var suspended := false
var elapsed := 0.0
var generation := 0
var accepted_casts := 0
var rejected_casts := 0
var release_count := 0
var receipts_count := 0
var last_reason := "Rama is ready"
var _rules: Dictionary = {}
var _cooldowns: Dictionary = {}
var _casts: Dictionary = {}
var _history: Array = []
var _next_cast := 0
var _event_seq := 0
var _action_cast := 0
var _teardown_depth := 0
var _movement_receiver := Callable()
var _origin_sampler := Callable()
var _muzzle_sampler := Callable()
var _hero_receiver: Node
var _hero_position := Callable()

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func configure(army_value: Node3D) -> bool:
	if _teardown_depth>0:return false
	if not is_instance_valid(army_value) or not army_value.get("configured") or not army_value.has_signal("simulation_stepped"):return false
	var parsed = JSON.parse_string(FileAccess.get_file_as_string(RULES_PATH))
	if not parsed is Dictionary or parsed.get("schema_version") != 1 or not parsed.get("abilities") is Array or parsed.abilities.size() != IDS.size():return false
	var candidate := {}
	for index in IDS.size():
		var rule = parsed.abilities[index]
		if not rule is Dictionary or rule.get("id") != IDS[index]:return false
		for spec in [["windup_s",.01,2.0],["recovery_s",.01,1.0],["cooldown_s",.1,60.0],["range_m",.1,40.0]]:
			if not _number(rule.get(spec[0]),float(spec[1]),float(spec[2])):return false
		if rule.id in ["kodanda","piercing_dawn","dawn_volley"]:
			for spec in [["speed_mps",1,80],["damage",1,500],["radius_m",.05,2],["max_hits",1,6]]:
				if not _number(rule.get(spec[0]),float(spec[1]),float(spec[2])):return false
			if not rule.max_hits is int and float(rule.max_hits)!=floorf(float(rule.max_hits)):return false
		if rule.id=="dawn_volley":
			if not rule.get("yaw_offsets_rad") is Array or rule.yaw_offsets_rad.size()!=3 or not _number(rule.get("stagger_s"),.05,.2):return false
			for angle in rule.yaw_offsets_rad:
				if not _number(angle,-.3,.3):return false
		elif rule.id=="guardian_circle":
			for spec in [["active_s",1,6],["radius_m",1,6],["shield",1,100],["heal_per_s",1,30]]:
				if not _number(rule.get(spec[0]),float(spec[1]),float(spec[2])):return false
		elif rule.id=="measured_step" and not _number(rule.get("movement_s"),.1,.5):return false
		var lifetime: float=float(rule.windup_s)+maxf(float(rule.recovery_s),maxf(float(rule.get("active_s",0.0))+.30,(float(rule.range_m)/float(rule.speed_mps)+float(rule.get("stagger_s",0.0))*2.0+.28) if rule.has("speed_mps") else .28))
		if lifetime>8.0:return false
		if not rule.get("label") is String or rule.label.length()>80:return false
		candidate[rule.id] = rule.duplicate(true)
	cancel_active("reconfigure")
	_disconnect()
	army = army_value
	_rules = candidate
	army.simulation_stepped.connect(_on_step)
	army.simulation_reset.connect(_on_reset)
	army.outcome.connect(_on_outcome)
	configured = true
	reset("configure")
	return true

func _disconnect() -> void:
	if not is_instance_valid(army):return
	if army.simulation_stepped.is_connected(_on_step):army.simulation_stepped.disconnect(_on_step)
	if army.simulation_reset.is_connected(_on_reset):army.simulation_reset.disconnect(_on_reset)
	if army.outcome.is_connected(_on_outcome):army.outcome.disconnect(_on_outcome)

func _exit_tree() -> void:
	cancel_active("scene_exit")
	_disconnect()
	configured = false

func set_movement_receiver(receiver: Callable) -> void:
	_movement_receiver = receiver

func set_hero_receiver(receiver: Node, position_sampler: Callable) -> void:
	_hero_receiver = receiver
	_hero_position = position_sampler

func set_muzzle_sampler(sampler: Callable) -> void:
	_muzzle_sampler = sampler

func set_origin_sampler(sampler: Callable) -> void:
	_origin_sampler = sampler

func set_suspended(value: bool) -> void:
	suspended = value
	changed.emit()

func _number(value: Variant, low: float, high: float) -> bool:
	return typeof(value) in [TYPE_FLOAT, TYPE_INT] and is_finite(float(value)) and float(value) >= low and float(value) <= high

func _enabled() -> bool:
	return configured and is_instance_valid(army) and army.configured and army.winner.is_empty() and not suspended and is_inside_tree() and not get_tree().paused and process_mode != Node.PROCESS_MODE_DISABLED

func _reject(reason: String) -> Dictionary:
	rejected_casts += 1
	last_reason = reason
	changed.emit()
	return {"accepted":false, "reason":reason, "cast_id":0, "generation":generation}

func request_ability(ability_id: String, origin: Vector3, forward: Vector3, ground_target: Vector3, options: Dictionary = {}) -> Dictionary:
	if _teardown_depth>0:return _reject("Combat is resetting")
	if not _enabled():return _reject("Practice is paused or the round has ended")
	if not _rules.has(ability_id):return _reject("Unknown Rama ability")
	if _action_cast != 0:return _reject("Finish the current draw or recovery")
	if _casts.size() >= MAX_CASTS:return _reject("Too many active arrows")
	if elapsed + 1e-8 < float(_cooldowns.get(ability_id, 0.0)):return _reject("Ability is cooling down")
	if not origin.is_finite() or not forward.is_finite() or not ground_target.is_finite():return _reject("Aim must be finite")
	var local_origin: Vector3 = army.to_local(origin)
	if absf(local_origin.y) > .4:return _reject("Land before using Rama's kit")
	local_origin.y = 0.0
	if army._blocked_with(local_origin, army.boxes, army.actor_bounds, .05):return _reject("Cast origin is blocked")
	var direction := Vector3(forward.x, 0, forward.z)
	if not is_finite(direction.length_squared()) or direction.length_squared() < .0001:return _reject("Choose a horizontal aim")
	direction = direction.normalized()
	var rule: Dictionary = _rules[ability_id].duplicate(true)
	var fixed_origin: Vector3 = army.to_global(local_origin)
	var target := fixed_origin + direction * float(rule.range_m)
	var geometry := {"kind":"projectiles", "origin":fixed_origin, "center":fixed_origin, "forward":direction, "range_m":float(rule.range_m), "height_m":2.7, "radius_m":float(rule.get("radius_m", .2)), "speed_mps":float(rule.get("speed_mps", 0.0)), "projectiles":[]}
	if ability_id == "guardian_circle":
		var local_target: Vector3 = army.to_local(ground_target)
		if absf(local_target.y) > .15 or local_target.distance_to(local_origin) > float(rule.range_m) + 1e-6:return _reject("Choose a ground point within 16 metres")
		local_target.y = 0
		if army._blocked_with(local_target, army.boxes, army.actor_bounds, .05) or not army.line_clear(local_origin, local_target):return _reject("Guardian Circle cannot cross cover")
		target = army.to_global(local_target)
		geometry.kind = "circle"
		geometry.center = target
	elif ability_id == "measured_step":
		if not _movement_receiver.is_valid():return _reject("Step receiver is unavailable")
		var requested = options.get("step_direction", direction)
		if not requested is Vector3 or not requested.is_finite():return _reject("Step direction must be finite")
		var step_dir := Vector3(requested.x, 0, requested.z)
		if not is_finite(step_dir.length_squared()):return _reject("Step direction is too large")
		if step_dir.length_squared() < .0001:step_dir = direction
		step_dir = step_dir.normalized()
		var local_end: Vector3 = army.to_local(fixed_origin + step_dir * float(rule.range_m))
		var fraction: float = army.segment_wall_fraction(local_origin, local_end, .48)
		if is_finite(fraction):local_end = local_origin.lerp(local_end, maxf(0.0, fraction - .025))
		local_end.x = clampf(local_end.x, float(army.actor_bounds[0]) + .5, float(army.actor_bounds[1]) - .5)
		local_end.z = clampf(local_end.z, float(army.actor_bounds[2]) + .5, float(army.actor_bounds[3]) - .5)
		if local_end.distance_to(local_origin) < .25:return _reject("No room to step")
		target = army.to_global(local_end)
		geometry.kind = "step"
		geometry.center = target
		geometry.step_direction = step_dir
	else:
		var offsets: Array = rule.get("yaw_offsets_rad", [0.0])
		for index in offsets.size():
			geometry.projectiles.append({"index":index, "origin":fixed_origin, "forward":direction.rotated(Vector3.UP, float(offsets[index])), "delay_s":float(rule.get("stagger_s",0.0)) * index})
	_next_cast += 1
	var travel: float = float(rule.range_m) / float(rule.speed_mps) + float(rule.get("stagger_s",0.0)) * 2.0 if rule.has("speed_mps") else 0.0
	var timing := {"windup_s":float(rule.windup_s), "recovery_s":float(rule.recovery_s), "travel_s":travel, "active_s":float(rule.get("active_s",0.0)), "movement_s":float(rule.get("movement_s",0.0))}
	var duration := float(rule.windup_s) + maxf(float(rule.recovery_s), maxf(travel + .28, float(rule.get("active_s",0.0)) + .30))
	var cast := {"id":_next_cast, "ability_id":ability_id, "generation":generation, "rule":rule, "geometry":geometry, "timing":timing, "origin":fixed_origin, "forward":direction, "target":target, "started":elapsed, "phase":"windup", "released":false, "release_age_s":-1.0, "recovered":false, "duration":duration, "projectile_done":{}, "projectile_hits":{}, "ward_ids":{}, "ward_snapshots":{}, "hero_ward":{}, "ward_cleaned":false}
	_casts[_next_cast] = cast
	_action_cast = _next_cast
	_cooldowns[ability_id] = elapsed + float(rule.cooldown_s)
	accepted_casts += 1
	last_reason = rule.label + " · drawing"
	var response := {"accepted":true, "reason":last_reason, "cast_id":_next_cast, "generation":generation, "windup_s":rule.windup_s, "recovery_s":rule.recovery_s}
	_emit("begin", cast)
	changed.emit()
	return response

func cancel_windup(reason := "interrupt") -> bool:
	if _action_cast==0 or not _casts.has(_action_cast) or _casts[_action_cast].released:return false
	_cancel_cast(_casts[_action_cast],reason)
	changed.emit()
	return true

func cancel_active(reason := "cancel") -> void:
	_teardown_depth+=1
	for id in _casts.keys():
		if _casts.has(id):_cancel_cast(_casts[id], reason)
	_action_cast = 0
	last_reason = reason
	changed.emit()
	_teardown_depth-=1

func _cancel_cast(cast: Dictionary, reason: String) -> void:
	_casts.erase(cast.id)
	if _action_cast == int(cast.id):_action_cast = 0
	_restore_wards(cast)
	_emit("cancel", cast, [], {"reason":reason})

func reset(reason := "reset") -> void:
	_teardown_depth+=1
	cancel_active(reason)
	generation += 1
	elapsed = 0.0
	_next_cast = 0
	_event_seq = 0
	_cooldowns.clear()
	_history.clear()
	_emit("reset", {}, [], {"reason":reason})
	changed.emit()
	_teardown_depth-=1

func _on_reset(reason: String) -> void:reset(reason)
func _on_outcome(_winner: String) -> void:cancel_active("round_ended")
func _same(cast: Dictionary) -> bool:
	return int(cast.generation) == generation and _casts.has(cast.id) and _casts[cast.id] == cast

func _on_step(delta: float) -> void:
	if not _enabled() or not is_finite(delta) or delta <= 0.0 or delta > .050001:return
	var previous := elapsed
	elapsed += delta
	for id in _casts.keys():
		if not _casts.has(id):continue
		var cast: Dictionary = _casts[id]
		var age: float = elapsed - cast.started
		var old_age: float = previous - cast.started
		var release_at: float = cast.timing.windup_s
		var tick_receipts: Array = []
		if not cast.released and age + 1e-8 >= release_at:
			if cast.ability_id == "kodanda" and _origin_sampler.is_valid():
				var sample = _origin_sampler.call()
				if not _same(cast):continue
				if not sample is Vector3 or not sample.is_finite() or absf(army.to_local(sample).y) > .4 or cast.origin.distance_to(sample) > 4.0 or not army.line_clear(army.to_local(cast.origin), army.to_local(sample), .05):
					_cancel_cast(cast, "draw_origin_invalid");continue
				var sampled_local: Vector3 = army.to_local(sample)
				sampled_local.y = 0
				cast.origin = army.to_global(sampled_local)
				cast.geometry.origin = cast.origin
				cast.geometry.center = cast.origin
				for p in cast.geometry.projectiles:p.origin = cast.origin
			if cast.geometry.kind=="projectiles":
				var muzzle: Variant = _muzzle_sampler.call() if _muzzle_sampler.is_valid() else cast.origin+Vector3.UP*1.25
				if not _same(cast):continue
				if not muzzle is Vector3 or not muzzle.is_finite() or muzzle.distance_to(cast.origin)>3.0 or muzzle.y-cast.origin.y<.4 or not army.line_clear(army.to_local(cast.origin),army.to_local(muzzle),.05):
					_cancel_cast(cast,"muzzle_invalid");continue
				for p in cast.geometry.projectiles:p.origin=muzzle
			cast.released = true
			cast.release_age_s = age
			cast.phase = "recovery"
			release_count += 1
			_emit("release", cast)
			if not _same(cast):continue
			if cast.ability_id == "measured_step":
				var movement = _movement_receiver.call(cast.origin, cast.target, float(cast.rule.movement_s))
				if not _same(cast):continue
				if not movement is Dictionary or not movement.get("accepted",false):
					_cancel_cast(cast, "step_obstructed_at_release");continue
				var destination = movement.get("destination",cast.target)
				if not destination is Vector3 or not destination.is_finite() or destination.distance_to(cast.origin)>float(cast.rule.range_m)+.1 or absf(destination.y-cast.origin.y)>.5 or not army.line_clear(army.to_local(cast.origin),army.to_local(destination),.05):
					_cancel_cast(cast, "invalid_step_receipt");continue
				cast.target = destination
				cast.geometry.center = destination
				_emit("impact", cast, [], {"contact_position":destination, "reason":"movement_accepted"})
			elif cast.ability_id == "guardian_circle":
				_emit("impact", cast, _ward_payload(cast, 0.0))
		if not _same(cast):continue
		if cast.released:
			if cast.geometry.kind == "projectiles":_step_projectiles(cast, maxf(0, old_age-float(cast.release_age_s)), maxf(0, age-float(cast.release_age_s)))
			elif cast.geometry.kind == "circle":
				var active_delta := maxf(0, minf(age, release_at+float(cast.rule.active_s)) - maxf(old_age, release_at))
				if active_delta > 1e-9:tick_receipts = _ward_payload(cast, active_delta)
				if _same(cast) and not cast.ward_cleaned and age+1e-8>=release_at+float(cast.rule.active_s):
					_restore_wards(cast)
					cast.ward_cleaned = true
		if not _same(cast):continue
		if not cast.recovered and age + 1e-8 >= release_at + float(cast.timing.recovery_s):
			cast.recovered = true
			cast.phase = "active"
			if _action_cast == id:_action_cast = 0
			_emit("recovery", cast)
		if not _same(cast):continue
		_emit("tick", cast, tick_receipts)
		if not _same(cast):continue
		if age + 1e-8 >= float(cast.duration):
			_casts.erase(id)
			_restore_wards(cast)
			_emit("end", cast)
	changed.emit()

func _step_projectiles(cast: Dictionary, previous: float, current: float) -> void:
	var g: Dictionary = cast.geometry
	for p in g.projectiles:
		if not _same(cast):return
		var index: int = p.index
		if cast.projectile_done.has(index) or current + 1e-8 < float(p.delay_s):continue
		var start: Vector3 = p.origin + p.forward * minf(float(g.range_m), maxf(0,previous-float(p.delay_s))*float(g.speed_mps))
		var finish: Vector3 = p.origin + p.forward * minf(float(g.range_m), maxf(0,current-float(p.delay_s))*float(g.speed_mps))
		var wall: float = army.segment_wall_fraction(army.to_local(start), army.to_local(finish), float(g.radius_m))
		var contacts: Array = []
		var hit_ids: Array = cast.projectile_hits.get(index, [])
		for unit in army.units.duplicate():
			if not is_instance_valid(unit) or not unit.alive or unit.team != "moon" or hit_ids.has(unit.unit_id) or absf(unit.global_position.y-p.origin.y)>float(g.height_m):continue
			var fraction := Geometry.segment_circle_fraction(start, finish, unit.global_position, float(g.radius_m)+float(unit.radius))
			if is_finite(fraction) and fraction < wall:contacts.append({"unit":unit, "fraction":fraction, "id":unit.unit_id})
		contacts.sort_custom(func(a,b):return a.fraction < b.fraction if absf(a.fraction-b.fraction)>1e-9 else a.id < b.id)
		for contact in contacts:
			if not _same(cast):return
			var unit = contact.unit
			if not is_instance_valid(unit) or not unit.alive:continue
			var before: float = unit.health
			var shield_before: float = unit.shield
			var accepted: bool = unit.take_hit(float(cast.rule.damage))
			if not _same(cast):return
			hit_ids.append(contact.id)
			cast.projectile_hits[index] = hit_ids
			var receipts: Array = []
			if accepted:receipts.append({"unit_id":contact.id, "kind":"damage", "position":unit.global_position, "health_before":before, "health_after":unit.health, "shield_before":shield_before, "shield_after":unit.shield, "damage_applied":before+shield_before-unit.health-unit.shield})
			var terminal := hit_ids.size() >= int(cast.rule.max_hits)
			if terminal:cast.projectile_done[index] = true
			_emit("impact", cast, receipts, {"projectile_index":index, "contact_position":start.lerp(finish,contact.fraction), "reason":"unit", "terminal":terminal})
			if terminal:break
		if not _same(cast):return
		if not cast.projectile_done.has(index) and (is_finite(wall) or (current-float(p.delay_s))*float(g.speed_mps)+1e-8>=float(g.range_m)):
			cast.projectile_done[index] = true
			_emit("impact", cast, [], {"projectile_index":index, "contact_position":start.lerp(finish,wall) if is_finite(wall) else finish, "reason":"wall" if is_finite(wall) else "range", "terminal":true})

func _ward_payload(cast: Dictionary, delta: float) -> Array:
	var result: Array = []
	var remaining := maxf(.001, float(cast.timing.windup_s)+float(cast.rule.active_s)-(elapsed-float(cast.started)))
	for unit in army.units.duplicate():
		if not _same(cast):return []
		if not is_instance_valid(unit) or not unit.alive or unit.team != "sun":continue
		if absf(unit.global_position.y-cast.target.y)>float(cast.geometry.height_m) or Vector2(unit.global_position.x-cast.target.x,unit.global_position.z-cast.target.z).length()>float(cast.rule.radius_m):continue
		if not army.line_clear(army.to_local(cast.target),unit.position):continue
		var before: float = unit.health
		var shield_before: float = unit.shield
		var granted := false
		if not cast.ward_ids.has(unit.unit_id) and unit.shield < float(cast.rule.shield):
			cast.ward_snapshots[unit.unit_id] = {"before":unit.shield, "until":unit.shield_until, "owned_until":float(army.elapsed)+remaining}
			granted = unit.apply_shield(float(cast.rule.shield),remaining)
			cast.ward_snapshots[unit.unit_id].owned_until = unit.shield_until
			cast.ward_ids[unit.unit_id] = true
		var healed: float = unit.receive_heal(float(cast.rule.heal_per_s)*delta) if delta>0 else 0.0
		if granted or healed>0:result.append({"unit_id":unit.unit_id,"kind":"guardian","position":unit.global_position,"health_before":before,"health_after":unit.health,"shield_before":shield_before,"shield_after":unit.shield,"healing_applied":healed,"damage_applied":0.0,"remaining_s":remaining})
	if _same(cast):
		var hero_receipt := _hero_ward_payload(cast, delta, remaining)
		if not hero_receipt.is_empty():result.append(hero_receipt)
	return result

func _hero_ward_payload(cast: Dictionary, delta: float, remaining: float) -> Dictionary:
	if not is_instance_valid(_hero_receiver) or not _hero_position.is_valid() or not _hero_receiver.get("alive"):return {}
	var point = _hero_position.call()
	if not _same(cast):return {}
	if not point is Vector3 or not point.is_finite() or absf(point.y-cast.target.y)>.4:return {}
	if Vector2(point.x-cast.target.x,point.z-cast.target.z).length()>float(cast.rule.radius_m) or not army.line_clear(army.to_local(cast.target),army.to_local(point)):return {}
	var hero_generation: int = _hero_receiver.generation
	var before: float = _hero_receiver.health
	var shield_before: float = _hero_receiver.shield
	var granted := false
	if cast.hero_ward.is_empty() and shield_before<float(cast.rule.shield):
		cast.hero_ward = {"before":shield_before,"until":_hero_receiver.shield_until,"owned_until":float(_hero_receiver.elapsed)+remaining,"generation":_hero_receiver.generation}
		granted = _hero_receiver.apply_shield(float(cast.rule.shield),remaining)
		if not _same(cast) or _hero_receiver.generation!=hero_generation:return {}
		cast.hero_ward.owned_until = _hero_receiver.shield_until
	var healed: float = _hero_receiver.receive_heal(float(cast.rule.heal_per_s)*delta) if delta>0 else 0.0
	if not _same(cast) or _hero_receiver.generation!=hero_generation:return {}
	if not granted and healed<=0:return {}
	return {"unit_id":0,"receiver_kind":"hero","kind":"guardian","position":point,"health_before":before,"health_after":_hero_receiver.health,"shield_before":shield_before,"shield_after":_hero_receiver.shield,"healing_applied":healed,"damage_applied":0.0,"remaining_s":remaining}

func _restore_wards(cast: Dictionary) -> void:
	var hero_previous: Dictionary = cast.get("hero_ward",{}).duplicate(true)
	cast.hero_ward = {}
	if not hero_previous.is_empty() and is_instance_valid(_hero_receiver) and _hero_receiver.generation==hero_previous.generation:
		if absf(_hero_receiver.shield_until-float(hero_previous.owned_until))<.0001 and _hero_receiver.shield<=float(cast.rule.shield):
			_hero_receiver.shield=minf(_hero_receiver.shield,float(hero_previous.before)) if float(hero_previous.until)>float(_hero_receiver.elapsed) else 0.0
			_hero_receiver.shield_until=float(hero_previous.until) if _hero_receiver.shield>0 else 0.0
			_hero_receiver.changed.emit()
	if int(cast.generation)!=generation:return
	if not is_instance_valid(army) or cast.get("ward_snapshots",{}).is_empty():return
	# Restore only a status whose expiry still identifies this cast. Later/stronger
	# grants from the independent legacy invocation system remain untouched.
	for unit in army.units:
		if not is_instance_valid(unit) or not cast.ward_snapshots.has(unit.unit_id):continue
		var previous: Dictionary = cast.ward_snapshots[unit.unit_id]
		if absf(unit.shield_until-float(previous.owned_until)) < .0001 and unit.shield <= float(cast.rule.shield):
			unit.shield = minf(unit.shield,float(previous.before)) if float(previous.until)>float(army.elapsed) else 0.0
			unit.shield_until = float(previous.until) if unit.shield>0 else 0.0
			unit._update_health_bar()
	cast.ward_ids.clear()
	cast.ward_snapshots.clear()

func _attachments(cast: Dictionary) -> Array:
	var result: Array = []
	if not cast.get("hero_ward",{}).is_empty() and is_instance_valid(_hero_receiver) and _hero_position.is_valid() and _hero_receiver.alive and _hero_receiver.shield>0:
		var point = _hero_position.call()
		if point is Vector3 and point.is_finite():result.append({"unit_id":0,"receiver_kind":"hero","position":point,"shield":_hero_receiver.shield,"remaining_s":maxf(0,_hero_receiver.shield_until-_hero_receiver.elapsed)})
	if cast.get("ward_ids",{}).is_empty() or not is_instance_valid(army):return result
	for unit in army.units:
		if is_instance_valid(unit) and unit.alive and cast.ward_ids.has(unit.unit_id) and unit.shield>0:
			result.append({"unit_id":unit.unit_id,"position":unit.global_position,"shield":unit.shield,"remaining_s":maxf(0,unit.shield_until-float(army.elapsed))})
	return result

func _emit(kind: String, cast: Dictionary, receipts: Array = [], extra: Dictionary = {}) -> void:
	if kind not in ["reset","cancel","end"] and not _same(cast):return
	if not cast.is_empty() and int(cast.generation)!=generation:return
	var emission_generation := generation
	var geometry: Dictionary = cast.get("geometry",{}).duplicate(true)
	geometry.attachments = _attachments(cast)
	if generation!=emission_generation:return
	if kind not in ["reset","cancel","end"] and not _same(cast):return
	_event_seq += 1
	var event := {"schema":1,"kind":kind,"generation":generation,"epoch":generation,"cast_id":int(cast.get("id",0)),"event_seq":_event_seq,"hero_id":"rama","ability_id":cast.get("ability_id",""),"time_s":elapsed,"age_s":maxf(0,elapsed-float(cast.get("started",elapsed))),"origin":cast.get("origin",Vector3.ZERO),"forward":cast.get("forward",Vector3.FORWARD),"target":cast.get("target",Vector3.ZERO),"timing":cast.get("timing",{}).duplicate(true),"geometry":geometry,"duration_s":float(cast.get("duration",0.0)),"release_age_s":float(cast.get("release_age_s",-1.0)),"receipts":receipts.duplicate(true)}
	for key in extra:event[key] = extra[key]
	receipts_count += receipts.size()
	_history.append(event.duplicate(true))
	if _history.size()>HISTORY_CAP:_history.pop_front()
	ability_event.emit(event)

func report() -> Dictionary:
	var cooldowns := {}
	for id in IDS:cooldowns[id] = maxf(0,float(_cooldowns.get(id,0))-elapsed)
	var active: Array = []
	for cast in _casts.values():active.append({"cast_id":cast.id,"ability_id":cast.ability_id,"phase":cast.phase,"age_s":elapsed-cast.started,"released":cast.released,"geometry":cast.geometry.duplicate(true)})
	return {"configured":configured,"generation":generation,"elapsed":elapsed,"suspended":suspended,"action_locked":_action_cast!=0,"active_cast_id":_action_cast,"active_ability":_casts.get(_action_cast,{}).get("ability_id",""),"cooldowns":cooldowns,"casts":active,"max_casts":MAX_CASTS,"accepted_casts":accepted_casts,"rejected_casts":rejected_casts,"release_count":release_count,"receipts_count":receipts_count,"history_size":_history.size(),"history_capacity":HISTORY_CAP,"last_reason":last_reason,"network_enabled":false,"receiver_scope":"lane_troops_and_explicit_movement_receiver"}
