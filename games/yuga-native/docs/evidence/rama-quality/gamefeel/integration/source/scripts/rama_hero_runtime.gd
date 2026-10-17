extends Node3D
## Shared native hero integration for courtyard and Confluence.
## All combat comes from one fixed-step kit; presentation cannot authorize damage.
signal changed
signal combat_event(event: Dictionary)
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const ActionBuffer = preload("res://scripts/rama_action_buffer.gd")
var player: CharacterBody3D
var army: Node3D
var kit: Node3D
var effects: Node3D
var vitals: Node
var action_buffer: Node
var configured := false
var suspended := false
var spawn := Vector3.ZERO
var spawn_yaw := 0.0
var notice := "Rama is ready"
var _voices: Array[AudioStreamPlayer] = []
var _sounds := {}
var _voice_index := 0
var _volume := .35
var _release_count := 0
var _hero_generation := -1
var _last_cast := 0
var _input_vitals_generation := -1

func _ready() -> void: process_mode = Node.PROCESS_MODE_PAUSABLE

func configure(hero: CharacterBody3D, simulation: Node3D) -> bool:
	if configured or not is_instance_valid(hero) or not is_instance_valid(simulation): return false
	player = hero
	army = simulation
	spawn = player.global_position
	spawn_yaw = player.yaw
	kit = Kit.new(); kit.name = "RamaAbilityKit"; add_child(kit)
	effects = Effects.new(); effects.name = "RamaAbilityEffects"; add_child(effects)
	vitals = Vitals.new(); vitals.name = "RamaVitals"; add_child(vitals)
	if not kit.configure(army) or not vitals.configure(army): return false
	player.vitals = vitals
	player.ability_request = cast_ability
	kit.set_origin_sampler(func(): return player.global_position)
	kit.set_muzzle_sampler(_muzzle_origin)
	kit.set_movement_receiver(player.accept_measured_step)
	kit.set_hero_receiver(vitals, func(): return player.global_position)
	kit.ability_event.connect(_event)
	action_buffer = ActionBuffer.new(); action_buffer.name = "RamaActionBuffer"; add_child(action_buffer)
	if not action_buffer.configure(kit, cast_ability, _input_eligibility): return false
	action_buffer.intent_changed.connect(_buffer_changed)
	action_buffer.dispatch_finished.connect(_buffer_dispatched)
	player.ability_input_request = request_input_ability
	player.ability_input_invalidated.connect(_clear_pending_input)
	kit.changed.connect(func(): changed.emit())
	_input_vitals_generation = vitals.generation
	vitals.changed.connect(_vitals_changed)
	vitals.damaged.connect(_damaged)
	vitals.defeated.connect(_defeated)
	vitals.respawn_ready.connect(_respawn)
	player.hero_reset.connect(_player_reset)
	if army.has_signal("siege_event"): army.siege_event.connect(_siege_event)
	army.outcome.connect(_round_ended)
	for index in 4:
		var voice := AudioStreamPlayer.new()
		voice.name = "RamaCue%d" % index
		add_child(voice); _voices.append(voice)
	for cue in ["windup", "rama-release", "sita-release", "arjuna-release", "cancel"]:
		var path: String = "res://assets/audio/invocations/" + cue + ".wav"
		if ResourceLoader.exists(path): _sounds[cue] = load(path)
	configured = true
	return true

func request_input_ability(id: String, edge_token: int, echoed := false) -> Dictionary:
	if not configured or not is_instance_valid(action_buffer): return {"accepted":false, "queued":false, "reason":"Return to practice to use Rama's kit"}
	var result: Dictionary = action_buffer.push_input(id, edge_token, echoed)
	if not result.get("accepted", false):
		notice = String(result.get("reason", "Ability input rejected"))
		changed.emit()
	return result

func _input_eligibility() -> Dictionary:
	if not configured or suspended or not is_instance_valid(player) or not player.active or not vitals.alive or get_tree().paused:
		return {"eligible":false, "reason":"Return to practice to use Rama's kit"}
	if player.reload_remaining > 0 or player.invocation_preparing:
		return {"eligible":false, "reason":"Finish the current action"}
	if not player.global_position.is_finite() or not is_instance_valid(player.pivot) or not is_instance_valid(player.camera):
		return {"eligible":false, "reason":"Aim must be finite"}
	if player.traversal.mode != "ground" or not player.is_on_floor() or absf(army.to_local(player.global_position).y) > .4:
		return {"eligible":false, "reason":"Land before using Rama's kit"}
	var forward: Vector3 = -player.pivot.global_basis.z
	forward.y = 0
	if not forward.is_finite() or not is_finite(forward.length_squared()) or forward.length_squared() < .0001 or not player.camera.global_position.is_finite():
		return {"eligible":false, "reason":"Aim must be finite"}
	for axis in [player.camera.global_basis.x, player.camera.global_basis.y, player.camera.global_basis.z]:
		if not axis.is_finite(): return {"eligible":false, "reason":"Aim must be finite"}
	var center := get_viewport().get_visible_rect().size * .5
	var ray: Vector3 = player.camera.project_ray_origin(center)
	var direction: Vector3 = player.camera.project_ray_normal(center)
	if not ray.is_finite() or not direction.is_finite():
		return {"eligible":false, "reason":"Aim must be finite"}
	return {"eligible":true}

func _buffer_changed() -> void:
	var state: Dictionary = action_buffer.report()
	if not state.pending.is_empty() or notice.ends_with("queued after recovery"):
		notice = String(state.last_reason)
		changed.emit()

func _buffer_dispatched(result: Dictionary) -> void:
	if not result.get("accepted", false):
		notice = String(result.get("reason", "Ability input rejected"))
		changed.emit()

func _clear_pending_input(reason: String) -> void:
	if is_instance_valid(action_buffer): action_buffer.cancel_pending(reason)

func _round_ended(_winner: String) -> void:
	_clear_pending_input("Round ended")

func _vitals_changed() -> void:
	if vitals.generation != _input_vitals_generation:
		_input_vitals_generation = vitals.generation
		_clear_pending_input("Hero generation changed")
	changed.emit()

func _exit_tree() -> void:
	_clear_pending_input("Scene changed")

func cast_ability(id: String) -> Dictionary:
	if not configured or suspended or not player.active or not vitals.alive or get_tree().paused:
		return {"accepted":false,"reason":"Return to practice to use Rama's kit"}
	if player.reload_remaining > 0 or player.invocation_preparing:
		return {"accepted":false,"reason":"Finish the current action"}
	if player.traversal.mode != "ground" or not player.is_on_floor():
		return {"accepted":false,"reason":"Land before using Rama's kit"}
	if id == "kodanda" and player.ammo <= 0: return {"accepted":false,"reason":"Reload the bow"}
	var forward: Vector3 = -player.pivot.global_basis.z
	forward.y = 0
	forward = forward.normalized()
	var target := player.global_position + forward * 10.0
	var center := get_viewport().get_visible_rect().size * .5
	var ray: Vector3 = player.camera.project_ray_origin(center)
	var direction: Vector3 = player.camera.project_ray_normal(center)
	var result := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(ray, ray + direction * 80.0, 1 | 4, [player.get_rid()]))
	if not result.is_empty():
		var offset: Vector3 = result.position - player.global_position
		offset.y = 0
		if offset.length() > .2:
			forward = offset.normalized()
			target = player.global_position + offset.limit_length(15.5)
	target.y = army.global_position.y
	var movement := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var step: Vector3 = Basis(Vector3.UP, player.yaw) * Vector3(movement.x, 0, movement.y)
	if step.length_squared() < .01: step = forward
	var accepted: Dictionary = kit.request_ability(id, player.global_position, forward, target, {"step_direction":step})
	if accepted.get("accepted", false) and int(accepted.get("generation", -1)) != kit.generation:
		return {"accepted":false,"reason":"Practice changed during the request"}
	if accepted.get("accepted", false) and id == "kodanda":
		player.ammo -= 1
		player.shots_fired += 1
		player.fire_remaining = .40
		player.changed.emit()
	notice = accepted.get("reason", "")
	changed.emit()
	return accepted

func _event(event: Dictionary) -> void:
	effects.consume_event(event)
	var id := String(event.get("ability_id", ""))
	var timing: Dictionary = event.get("timing", {})
	match String(event.get("kind", "")):
		"begin":
			_last_cast = int(event.cast_id)
			_hero_generation = int(event.generation)
			player.rama_action_locked = true
			player.rama_committed = id in ["piercing_dawn", "guardian_circle", "dawn_volley"]
			player.invocation_facing = event.forward
			if player.rama_committed:
				player.velocity.x = 0
				player.velocity.z = 0
			player.action_time = float(timing.get("windup_s", .2)) + float(timing.get("recovery_s", .2))
			if player.rama_motion: player.rama_motion.request_action(id, float(timing.windup_s), float(timing.recovery_s))
			if id != "kodanda": _cue("windup", .4)
		"release":
			if int(event.cast_id) == _last_cast and int(event.generation) == _hero_generation and vitals.alive:
				notice = id.replace("_", " ").capitalize() + " · released"
			_release_count += 1
			if player.rama_motion: player.rama_motion.release_action(id)
			_cue("sita-release" if id == "guardian_circle" else ("arjuna-release" if id == "dawn_volley" else "rama-release"), .7 if id == "kodanda" else 1.0)
		"recovery":
			if int(event.cast_id) == _last_cast and int(event.generation) == _hero_generation:
				if vitals.alive: notice = "Guardian Circle · field active" if id == "guardian_circle" else "Rama is ready"
				player.rama_committed = false
				player.rama_action_locked = false
		"tick":
			# The owned field ends before the cast's presentation cleanup tail.
			# Read its authority tick rather than leaving an obsolete active label.
			if id == "guardian_circle" and int(event.cast_id) == _last_cast and int(event.generation) == _hero_generation and vitals.alive:
				if float(event.age_s) + 1e-8 >= float(timing.windup_s) + float(timing.active_s):
					notice = "Rama is ready"
		"cancel":
			if int(event.cast_id) == _last_cast and int(event.generation) == _hero_generation:
				if vitals.alive: notice = "Action cancelled"
				player.action_time = 0
				player.rama_committed = false
				player.rama_action_locked = false
				if id == "measured_step":
					player.dash_time = 0
					player.dash_direction = Vector3.ZERO
					player.velocity.x = 0
					player.velocity.z = 0
				if player.rama_motion: player.rama_motion.cancel_action("combat cancelled")
		"end":
			if int(event.cast_id) == _last_cast and int(event.generation) == _hero_generation and vitals.alive:
				notice = "Rama is ready"
		"reset":
			_last_cast = 0
			_hero_generation = int(event.generation)
			if vitals.alive: notice = "Rama is ready"
			player.rama_committed = false
			player.rama_action_locked = false
			if player.rama_motion: player.rama_motion.cancel("combat reset")
	combat_event.emit(event.duplicate(true))

func set_suspended(value: bool) -> void:
	suspended = value
	if value: _clear_pending_input("Practice suspended")
	if not configured: return
	kit.set_suspended(value)
	effects.set_suspended(value)
	vitals.set_suspended(value)
	if value:
		for voice in _voices: voice.stop()

func set_volume(value: float) -> void:
	if is_finite(value): _volume = clampf(value, 0, 1)

func _cue(id: String, gain: float) -> void:
	if suspended or _volume <= 0 or not _sounds.has(id): return
	var voice := _voices[_voice_index % _voices.size()]
	_voice_index += 1
	voice.stop(); voice.stream = _sounds[id]
	voice.volume_db = linear_to_db(maxf(.001, _volume * gain))
	voice.play()

func _damaged(receipt: Dictionary) -> void:
	if not receipt.get("accepted", false) or not vitals.alive: return
	_clear_pending_input("Hit reaction")
	# Impact flinch cancels the current draw rather than leaving a held string.
	kit.cancel_windup("hit reaction")
	if int(receipt.get("generation", -1)) != vitals.generation or not vitals.alive: return
	if player.rama_motion:
		player.rama_motion.request_action("hit", .06, .22)
		player.rama_motion.release_action("hit")
	notice = "Hit · %.0f health" % vitals.health
	changed.emit()

func _defeated(receipt: Dictionary) -> void:
	if int(receipt.get("generation", -1)) != vitals.generation or vitals.alive: return
	_clear_pending_input("Defeated")
	kit.cancel_active("defeated")
	if int(receipt.get("generation", -1)) != vitals.generation or vitals.alive: return
	player.cancel_traversal("defeated")
	player.active = false
	player.velocity = Vector3.ZERO
	player.dash_time = 0
	player.rama_committed = false
	player.rama_action_locked = false
	if player.rama_motion:
		player.rama_motion.request_action("death", .12, .8)
		player.rama_motion.release_action("death")
	notice = "Defeated · returning in 3 seconds"
	changed.emit()

func _respawn() -> void:
	if suspended or not vitals.respawn(): return
	player.reset()
	player.global_position = spawn
	player.yaw = spawn_yaw
	player._update_camera()
	player.active = true
	if player.rama_motion:
		player.rama_motion.request_action("respawn", .1, .7)
		player.rama_motion.release_action("respawn")
	notice = "Returned to the arrival court"
	changed.emit()

func _siege_event(event: Dictionary) -> void:
	if not configured or suspended or not player.active or event.get("kind") != "impact" or event.get("team") != "moon" or event.get("cancelled", false): return
	var point = event.get("target")
	if not point is Vector3 or not point.is_finite(): return
	var radius := float(event.get("radius", 0))
	if not is_finite(radius) or radius <= 0 or radius > 10 or not event.get("id") is int or int(event.id) < 1: return
	if absf(player.global_position.y-point.y) > 2.7 or Vector2(player.global_position.x-point.x, player.global_position.z-point.z).length() > radius + .29: return
	if not army.line_clear(army.to_local(point), army.to_local(player.global_position)): return
	vitals.receive_damage(event.get("damage", 0), "enemy_siege:%d" % int(event.get("id", -1)), vitals.generation, 0)

func _player_reset() -> void:
	if not configured: return
	reset("player reset")

func reset(reason := "reset") -> void:
	if not configured: return
	_clear_pending_input(reason)
	kit.reset(reason)
	player.rama_committed = false
	player.rama_action_locked = false
	player.dash_time = 0
	player.dash_direction = Vector3.ZERO
	effects.reset()
	vitals.reset()
	for voice in _voices: voice.stop()
	notice = "Rama is ready"
	changed.emit()

func report() -> Dictionary:
	return {"configured":configured,"kit":kit.report() if kit else {},"effects":effects.report() if effects else {},"vitals":vitals.report() if vitals else {},"action_buffer":action_buffer.report() if action_buffer else {},"audio_voices":_voices.size(),"accepted_releases":_release_count,"notice":notice,"scope":"Offline native hero; enemy siege blasts damage Rama, ordinary lane troops still target troops."}

func _muzzle_origin() -> Vector3:
	if player.rama_motion:
		player.rama_motion.evaluate_pose()
		return player.rama_motion.socket_global("arrow_muzzle").origin
	return player.global_position + Vector3.UP * 1.25
