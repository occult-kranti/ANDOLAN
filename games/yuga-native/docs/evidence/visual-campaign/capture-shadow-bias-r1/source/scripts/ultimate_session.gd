extends Node3D
## Actual offline troop invocations. Presentation is a pure event consumer.

signal invocation_event(event: Dictionary)
signal changed

const Rules = preload("res://scripts/ultimate_rules.gd")
var army: Node3D
var rules: Dictionary = {}
var _by_hero: Dictionary = {}
var selected_hero := "rama"
var suspended := false
var configured := false
var elapsed := 0.0
var epoch := 0
var _next_cast := 0
var _event_seq := 0
var _ready_at := 0.0
var _active: Dictionary = {}
var _history: Array = []
var accepted_casts := 0
var rejected_casts := 0
var applied_receipts := 0
var last_reason := "Choose an invocation; effects target lane troops."

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func configure(army_value: Node3D) -> bool:
	var loaded := Rules.load_rules()
	if not loaded.valid or not is_instance_valid(army_value) or not army_value.get("configured"):
		return false
	if not army_value.has_signal("simulation_stepped") or not army_value.has_signal("simulation_reset"):
		return false
	# Successful replacement retires effects on the old army before switching.
	cancel_active("reconfigure")
	_disconnect_army()
	army = army_value
	rules = loaded.data
	_by_hero.clear()
	for rule in rules.rules:_by_hero[rule.hero_id] = rule
	army.simulation_stepped.connect(_on_army_step)
	army.simulation_reset.connect(_on_army_reset)
	army.outcome.connect(_on_outcome)
	configured = true
	reset("configure")
	return true

func _disconnect_army() -> void:
	if not is_instance_valid(army):return
	if army.simulation_stepped.is_connected(_on_army_step):army.simulation_stepped.disconnect(_on_army_step)
	if army.simulation_reset.is_connected(_on_army_reset):army.simulation_reset.disconnect(_on_army_reset)
	if army.outcome.is_connected(_on_outcome):army.outcome.disconnect(_on_outcome)

func _exit_tree() -> void:
	cancel_active("scene_exit")
	_disconnect_army()
	configured = false

func select_invocation(hero_id: String) -> bool:
	if not _by_hero.has(hero_id):return false
	selected_hero = hero_id
	changed.emit()
	return true

func set_suspended(value: bool) -> void:
	suspended = value
	changed.emit()

func _enabled() -> bool:
	return configured and is_instance_valid(army) and army.configured and army.winner.is_empty() and not suspended and is_inside_tree() and not get_tree().paused and process_mode!=Node.PROCESS_MODE_DISABLED

func _reject(reason: String) -> Dictionary:
	rejected_casts += 1
	last_reason = reason
	changed.emit()
	return {"accepted":false,"reason":reason,"epoch":epoch,"cast_id":0}

func request_cast(origin: Vector3, forward: Vector3, ground_target: Vector3) -> Dictionary:
	if not _enabled():return _reject("Practice is paused or the round has ended")
	if not _active.is_empty() or elapsed+1e-8<_ready_at:return _reject("Shared practice cooldown is still active")
	if not origin.is_finite() or not forward.is_finite() or not ground_target.is_finite():return _reject("Aim must be finite")
	var local_origin: Vector3 = army.to_local(origin)
	if absf(local_origin.y)>.35:return _reject("Land before invoking troop practice")
	local_origin.y = 0
	if army._blocked_with(local_origin,army.boxes,army.actor_bounds,.05):return _reject("Invocation origin is blocked")
	var horizontal := Vector3(forward.x,0,forward.z)
	if not is_finite(horizontal.length_squared()) or horizontal.length_squared()<.0001:return _reject("Choose a horizontal aim direction")
	horizontal = horizontal.normalized()
	var rule: Dictionary = _by_hero[selected_hero].duplicate(true)
	var geometry: Dictionary = rule.geometry.duplicate(true)
	var fixed_origin: Vector3 = army.to_global(local_origin)
	var target := fixed_origin
	if geometry.anchor=="ground_target":
		var local_target: Vector3 = army.to_local(ground_target)
		if absf(local_target.y)>.1:return _reject("Choose a clear ground point")
		local_target.y = 0
		if local_origin.distance_to(local_target)>float(geometry.target_range_m)+.000001:return _reject("Ground target is out of range")
		if army._blocked_with(local_target,army.boxes,army.actor_bounds,.05) or not army.line_clear(local_origin,local_target):return _reject("Ground target is blocked by cover")
		target = army.to_global(local_target)
	geometry.origin = fixed_origin
	geometry.center = target
	geometry.forward = horizontal
	var specifications: Array = []
	if geometry.kind=="projectile_volley":
		geometry.projectiles = []
		for index in geometry.yaw_offsets_rad.size():
			geometry.projectiles.append({"index":index,"origin":fixed_origin,"forward":horizontal.rotated(Vector3.UP,float(geometry.yaw_offsets_rad[index]))})
	if geometry.kind=="summon_pair":
		var planned: Dictionary = army.plan_temporary_pair(fixed_origin,rule.effects[0].role)
		if not planned.valid:return _reject(planned.reason)
		specifications = planned.specifications
		geometry.placements = planned.placements
	_next_cast += 1
	var accepted_id := _next_cast
	var accepted_epoch := epoch
	_active = {"id":accepted_id,"hero_id":selected_hero,"effect_id":rule.effect_id,"rule":rule,"geometry":geometry,
		"origin":fixed_origin,"forward":horizontal,"target":target,"started":elapsed,"phase":"windup","released":false,"payload":false,
		"projectile_done":{},"specifications":specifications,"summon_ids":[],"shield_ids":[]}
	_ready_at = elapsed+float(rules.shared_cooldown_s)
	accepted_casts += 1
	last_reason = rule.name+" invoked for lane troops"
	_emit("begin")
	changed.emit()
	return {"accepted":true,"reason":last_reason,"epoch":accepted_epoch,"cast_id":accepted_id}

func cancel_active(reason := "cancel") -> void:
	if not _active.is_empty():_emit("cancel",[],{"reason":reason})
	_active.clear()
	if is_instance_valid(army):army.clear_practice_effects()
	last_reason = reason
	changed.emit()

func reset(reason := "reset") -> void:
	cancel_active(reason)
	epoch += 1
	elapsed = 0.0
	_ready_at = 0.0
	_next_cast = 0
	_event_seq = 0
	_history.clear()
	_emit("reset",[],{"reason":reason})
	changed.emit()

func _on_army_reset(reason: String) -> void:
	reset(reason)

func _on_outcome(_winner: String) -> void:
	cancel_active("round_ended")

func _on_army_step(delta: float) -> void:
	if not _enabled() or not is_finite(delta) or delta<=0 or delta>.050001:return
	var before := elapsed
	elapsed += delta
	if _active.is_empty():changed.emit();return
	var active_id: int = _active.id
	var active_epoch := epoch
	var rule: Dictionary = _active.rule
	var timing: Dictionary = rule.timing
	var old_age: float = before-_active.started
	var age: float = elapsed-_active.started
	var release_at: float = timing.windup_s
	var payload_at: float = timing.windup_s+timing.travel_s
	var active_end: float = payload_at+timing.active_s
	var total: float = active_end+timing.recovery_s
	if not _active.released and age+1e-8>=release_at:
		_active.released = true
		_active.phase = "travel" if timing.travel_s>0 else "active"
		_emit("release")
		if not _same_cast(active_epoch,active_id):return
	if rule.geometry.kind=="projectile_volley" and age+1e-8>=release_at:
		_step_projectiles(maxf(0,old_age-release_at),maxf(0,age-release_at))
		if not _same_cast(active_epoch,active_id):return
	elif not _active.payload and age+1e-8>=payload_at:
		_active.payload = true
		_active.phase = "active"
		if rule.geometry.kind=="summon_pair":
			var effect: Dictionary = rule.effects[0]
			var spawned: Array = army.spawn_temporary_pair(_active.specifications,effect.attack_damage,effect.health,effect.duration_s)
			if spawned.size()!=2:cancel_active("Summon placements became occupied");return
			var receipts: Array = []
			for unit in spawned:
				_active.summon_ids.append(unit.unit_id)
				receipts.append({"unit_id":unit.unit_id,"kind":"summon","position":unit.global_position,"health_after":unit.health,"remaining_s":effect.duration_s})
			_emit("impact",receipts)
		else:
			var receipts := _apply_payload(false,0)
			if not _same_cast(active_epoch,active_id):return
			_emit("impact",receipts)
		if not _same_cast(active_epoch,active_id):return
	var active_delta := maxf(0,minf(age,active_end)-maxf(old_age,payload_at))
	if active_delta>1e-9 and rule.geometry.kind=="zone_disk":
		var receipts := _apply_payload(true,active_delta)
		if not _same_cast(active_epoch,active_id):return
		_emit("tick",receipts)
	elif active_delta>1e-9 and rule.geometry.kind=="summon_pair":
		_emit("tick",_summon_receipts())
	elif active_delta>1e-9 and _active.hero_id=="chitrangada":
		_emit("tick")
	if not _same_cast(active_epoch,active_id):return
	if age+1e-8>=active_end:_active.phase = "recovery"
	if age+1e-8>=total:
		_emit("end")
		if _same_cast(active_epoch,active_id):_active.clear()
	changed.emit()

func _same_cast(check_epoch: int, check_id: int) -> bool:
	return epoch==check_epoch and not _active.is_empty() and int(_active.id)==check_id

func _line_clear(origin: Vector3, target: Vector3) -> bool:
	return is_instance_valid(army) and army.line_clear(army.to_local(origin),army.to_local(target))

func _apply_payload(tick: bool, delta: float) -> Array:
	var receipts: Array = []
	if _active.is_empty():return receipts
	var geometry: Dictionary = _active.geometry
	var effects: Array = _active.rule.effects
	var current_epoch := epoch
	var current_id: int = _active.id
	for unit in army.units.duplicate():
		if not _same_cast(current_epoch,current_id):break
		if not is_instance_valid(unit) or not unit.alive or not Rules.contains(geometry,unit.global_position) or not _line_clear(geometry.center,unit.global_position):continue
		var health_before: float = unit.health
		var shield_before: float = unit.shield
		var kinds: Array = []
		var damage_applied := 0.0
		var healing_applied := 0.0
		for effect in effects:
			if not is_instance_valid(unit) or not unit.alive:break
			if (effect.team=="ally") != (unit.team=="sun"):continue
			var kind: String = effect.kind
			if tick != (kind in ["damage_rate","heal_rate","slow"]):continue
			if kind in ["damage","damage_rate"]:
				var value: float = float(effect.amount_per_s)*delta if tick else float(effect.amount)
				var before_total: float = unit.health+unit.shield
				var accepted: bool = unit.take_hit(value)
				if not _same_cast(current_epoch,current_id):return []
				if accepted:damage_applied += before_total-unit.health-unit.shield;kinds.append(kind)
			elif kind in ["heal","heal_rate"]:
				var value: float = float(effect.amount_per_s)*delta if tick else float(effect.amount)
				var healed: float = unit.receive_heal(value)
				healing_applied += healed
				if healed>0:kinds.append(kind)
			elif kind=="shield" and unit.apply_shield(effect.amount,effect.duration_s):
				kinds.append(kind)
				if not _active.shield_ids.has(unit.unit_id):_active.shield_ids.append(unit.unit_id)
			elif kind=="slow" and unit.apply_slow(effect.multiplier,effect.duration_s):kinds.append(kind)
		if not kinds.is_empty() and is_instance_valid(unit):
			receipts.append({"unit_id":unit.unit_id,"kind":"payload","effects":kinds,"position":unit.global_position,
				"health_before":health_before,"health_after":unit.health,"shield_before":shield_before,"shield_after":unit.shield,
				"damage_applied":damage_applied,"healing_applied":healing_applied,"speed_multiplier":unit.slow_multiplier,"status_until_s":maxf(unit.shield_until,unit.slow_until)})
	return receipts

func _step_projectiles(previous_time: float, current_time: float) -> void:
	if _active.is_empty():return
	var geometry: Dictionary = _active.geometry
	var current_epoch := epoch
	var current_id: int = _active.id
	for projectile in geometry.projectiles:
		if not _same_cast(current_epoch,current_id):return
		var index: int = projectile.index
		if _active.projectile_done.has(index):continue
		var from_distance := minf(float(geometry.range_m),previous_time*float(geometry.speed_mps))
		var to_distance := minf(float(geometry.range_m),current_time*float(geometry.speed_mps))
		var start: Vector3 = projectile.origin+projectile.forward*from_distance
		var finish: Vector3 = projectile.origin+projectile.forward*to_distance
		var fraction: float = army.segment_wall_fraction(army.to_local(start),army.to_local(finish),float(geometry.radius_m))
		var reason := "wall"
		var victim: Node3D
		for unit in army.units:
			if not unit.alive or unit.team!="moon" or absf(unit.global_position.y-projectile.origin.y)>float(geometry.height_m):continue
			var contact := Rules.segment_circle_fraction(start,finish,unit.global_position,float(geometry.radius_m))
			if contact<fraction:
				fraction = contact
				victim = unit
				reason = "unit"
		var reached_range := to_distance+1e-8>=float(geometry.range_m)
		if is_finite(fraction) or reached_range:
			_active.projectile_done[index] = true
			var point := start.lerp(finish,fraction) if is_finite(fraction) else finish
			var receipts: Array = []
			if is_instance_valid(victim):
				var before: float = victim.health
				var shield_before: float = victim.shield
				var accepted: bool = victim.take_hit(_active.rule.effects[0].amount)
				if not _same_cast(current_epoch,current_id):return
				if accepted:
					receipts.append({"unit_id":victim.unit_id,"kind":"damage","position":victim.global_position,"health_before":before,"health_after":victim.health,"shield_before":shield_before,"shield_after":victim.shield,"damage_applied":before+shield_before-victim.health-victim.shield})
			_emit("impact",receipts,{"projectile_index":index,"contact_position":point,"reason":reason if is_finite(fraction) else "range"})
		if _same_cast(current_epoch,current_id) and _active.projectile_done.size()==geometry.projectiles.size():_active.phase = "active"

func _summon_receipts() -> Array:
	var receipts: Array = []
	for unit in army.units:
		if unit.alive and unit.practice_summon and _active.summon_ids.has(unit.unit_id):
			receipts.append({"unit_id":unit.unit_id,"kind":"summon","position":unit.global_position,"remaining_s":maxf(0,unit.summon_expires_at-army.elapsed)})
	return receipts

func _attachments() -> Array:
	var result: Array = []
	if _active.is_empty() or not is_instance_valid(army):return result
	for unit in army.units:
		if not unit.alive:continue
		if _active.summon_ids.has(unit.unit_id) and unit.practice_summon:
			result.append({"unit_id":unit.unit_id,"kind":"summon","position":unit.global_position,"remaining_s":maxf(0,unit.summon_expires_at-army.elapsed)})
		elif _active.shield_ids.has(unit.unit_id) and unit.shield>0:
			result.append({"unit_id":unit.unit_id,"kind":"shield","position":unit.global_position,"shield":unit.shield,"remaining_s":maxf(0,unit.shield_until-army.elapsed)})
	return result

func _emit(kind: String, receipts: Array = [], extra: Dictionary = {}) -> void:
	_event_seq += 1
	var geometry: Dictionary = _active.get("geometry",{}).duplicate(true)
	geometry.attachments = _attachments()
	var event := {"schema":1,"kind":kind,"epoch":epoch,"cast_id":int(_active.get("id",0)),"event_seq":_event_seq,
		"hero_id":_active.get("hero_id",selected_hero),"effect_id":_active.get("effect_id",selected_hero+".r.v1"),"team":"sun","time_s":elapsed,
		"age_s":elapsed-float(_active.get("started",elapsed)),"origin":_active.get("origin",Vector3.ZERO),"forward":_active.get("forward",Vector3.FORWARD),"target":_active.get("target",Vector3.ZERO),
		"timing":_active.get("rule",{}).get("timing",{}).duplicate(true),"geometry":geometry,"receipts":receipts.duplicate(true),"reason":""}
	for key in extra:event[key] = extra[key]
	applied_receipts += receipts.size()
	_history.append(event.duplicate(true))
	if _history.size()>64:_history.pop_front()
	invocation_event.emit(event)

func report() -> Dictionary:
	var selected: Dictionary = _by_hero.get(selected_hero,{}).duplicate(true)
	var geometry: Dictionary = selected.get("geometry",{})
	return {"configured":configured,"selected_hero":selected_hero,"selected_rule":selected,
		"selected_range_m":float(geometry.get("target_range_m",geometry.get("range_m",geometry.get("radius_m",5.0)))),"target_kind":geometry.get("anchor","caster"),
		"cooldown_remaining":maxf(0,_ready_at-elapsed),"active_phase":_active.get("phase","ready"),"active_cast_id":int(_active.get("id",0)),
		"suspended":suspended,"epoch":epoch,"elapsed":elapsed,"accepted_casts":accepted_casts,"rejected_casts":rejected_casts,
		"applied_receipts":applied_receipts,"history_size":_history.size(),"history_capacity":64,"last_reason":last_reason,
		"supported_receivers":"living_lane_troops","network_enabled":false,"hero_health_enabled":false,
		"scope":"Offline invocation practice through the current Rama avatar; troop effects only."}
