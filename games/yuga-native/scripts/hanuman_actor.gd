extends CharacterBody3D
## Native feet-origin controller for the authored mace rig. Rock collision and
## traversal belong to this body. Imported animation never moves the body.

const CAPSULE_RADIUS := .32
const CAPSULE_HEIGHT := 1.98
const WALK_SPEED := 5.4
const SPRINT_SPEED := 8.1
const GROUND_ACCEL := 27.0
const AIR_ACCEL := 9.0
const JUMP_SPEED := 5.9
const TURN_RATE := 15.0
const ABILITY_BLEND := .11
const MODEL_PATH := "res://assets/heroes/hanuman/hanuman.glb"
const LOCOMOTION := [&"idle", &"run", &"jump"]
const ChainResponse = preload("res://scripts/hero_chain_response.gd")
const TAIL_PROFILE := "res://assets/design/hanuman-tail-response.json"

var model: Node3D
var skeleton: Skeleton3D
var animator: AnimationPlayer
var tail_response: SkeletonModifier3D
var camera: Camera3D
var pivot: Node3D
var active := false
var ready_for_play := false
var yaw := 0.0
var pitch := -.16
var look_sensitivity := .0024
var invert_y := false
var last_error := ""
var tail_error := ""
var _clips: Dictionary = {}
var _action: Dictionary = {}
var _vault: Dictionary = {}
var _last_vault: Dictionary = {}
var _last_motion := ""
var _gravity := 18.0

func _ready() -> void:
	collision_layer = 2
	collision_mask = 1 | 4
	floor_snap_length = .28
	_gravity = float(ProjectSettings.get_setting("physics/3d/default_gravity", 18.0))
	var body := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = CAPSULE_RADIUS
	capsule.height = CAPSULE_HEIGHT
	body.name = "HeroCapsule"
	body.shape = capsule
	body.position.y = CAPSULE_HEIGHT * .5
	add_child(body)
	_setup_camera()

func configure_visual(packed: PackedScene) -> bool:
	if is_instance_valid(model) or not is_inside_tree(): return false
	if packed == null:
		last_error = "The Hanuman character asset is unavailable."
		return false
	var candidate := packed.instantiate() as Node3D
	if candidate == null:
		last_error = "The character asset is not a 3D scene."
		return false
	var rigs := candidate.find_children("*", "Skeleton3D", true, false)
	var mixers := candidate.find_children("*", "AnimationPlayer", true, false)
	if rigs.size() != 1 or mixers.size() != 1:
		last_error = "The character needs one skeleton and one animation player."
		candidate.free()
		return false
	var rig: Skeleton3D = rigs[0]
	var mixer: AnimationPlayer = mixers[0]
	for socket in [&"root", &"head", &"wrist.R", &"foot.L", &"foot.R"]:
		if rig.find_bone(socket) < 0:
			last_error = "The character is missing a required bone: " + String(socket)
			candidate.free()
			return false
	var clip_map := {}
	for full_name in mixer.get_animation_list():
		var short_name := StringName(String(full_name).get_file().to_lower())
		if clip_map.has(short_name):
			last_error = "The character has two clips named " + String(short_name)
			candidate.free()
			return false
		clip_map[short_name] = full_name
	for short_name in LOCOMOTION:
		if not clip_map.has(short_name):
			last_error = "The character is missing its " + String(short_name) + " clip."
			candidate.free()
			return false
	model = candidate
	animator = mixer
	skeleton = rig
	_clips = clip_map
	model.name = &"HanumanModel"
	model.rotation.y = PI
	add_child(model)
	# Imported clips are shared. Own the library so loop flags never alter
	# other actor instances, including a portrait using the same GLB.
	for name_ in animator.get_animation_library_list():
		var library := animator.get_animation_library(name_).duplicate(true) as AnimationLibrary
		animator.remove_animation_library(name_)
		animator.add_animation_library(name_, library)
	for loop_name in [&"idle", &"run"]:
		animator.get_animation(_clips[loop_name]).loop_mode = Animation.LOOP_LINEAR
	var response := ChainResponse.new()
	if response.configure(skeleton, ChainResponse.load_profile(TAIL_PROFILE)):
		response.name = &"TailResponse"
		skeleton.add_child(response)
		tail_response = response
	else:
		tail_error = response.last_error
		response.free()
	ready_for_play = true
	_play_locomotion("idle")
	animator.advance(0.0)
	return true

func has_clip(clip: StringName) -> bool:
	return ready_for_play and _clips.has(clip)

func _setup_camera() -> void:
	pivot = Node3D.new()
	pivot.name = "CameraPivot"
	pivot.position.y = 1.65
	add_child(pivot)
	var spring := SpringArm3D.new()
	spring.name = "CameraCollision"
	spring.spring_length = 4.0
	spring.position.x = .70
	spring.margin = .18
	spring.collision_mask = 1
	spring.add_excluded_object(get_rid())
	var probe := SphereShape3D.new()
	probe.radius = .18
	spring.shape = probe
	pivot.add_child(spring)
	camera = Camera3D.new()
	camera.name = "HanumanCamera"
	camera.fov = 66.0
	camera.near = .09
	camera.far = 125.0
	spring.add_child(camera)
	camera.current = true
	_update_camera()

func _update_camera() -> void:
	pivot.rotation = Vector3(pitch, yaw, 0)

func turn_camera(motion: Vector2) -> void:
	if not active or not motion.is_finite(): return
	yaw = wrapf(yaw - motion.x * look_sensitivity, -PI, PI)
	pitch = clampf(pitch + motion.y * look_sensitivity * (1 if invert_y else -1), -.97, .62)
	_update_camera()

func aim_forward() -> Vector3:
	return Basis(Vector3.UP, yaw) * Vector3.FORWARD

func aim_ground() -> Vector3:
	var fallback := global_position + aim_forward() * 8.0
	var screen_center := get_viewport().get_visible_rect().size * .5
	var from := camera.project_ray_origin(screen_center)
	var direction := camera.project_ray_normal(screen_center)
	var ray := PhysicsRayQueryParameters3D.create(from, from + direction * 60.0, 1, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(ray)
	var target: Vector3 = hit.get("position", fallback)
	target.y = 0.0
	return target if target.is_finite() else fallback

func set_paused(value: bool) -> void:
	active = not value and ready_for_play
	if is_instance_valid(animator): animator.active = active
	if is_instance_valid(tail_response): tail_response.set_held(value)
	if value:
		velocity = Vector3.ZERO

func reset_at(point: Vector3) -> void:
	velocity = Vector3.ZERO
	_action.clear()
	_vault.clear()
	_last_vault.clear()
	global_position = point
	reset_physics_interpolation()
	yaw = 0.0
	pitch = -.16
	_update_camera()
	if is_instance_valid(model): model.rotation.y = PI
	if is_instance_valid(tail_response): tail_response.reset()
	_last_motion = ""
	_play_locomotion("idle")

func _physics_process(delta: float) -> void:
	if not active: return
	var previous_position := global_position
	var vaulting := not _vault.is_empty()
	if vaulting:
		_step_vault(delta)
	else:
		_step_movement(delta)
	_step_action(delta)
	if _action.is_empty():
		var speed := Vector2(velocity.x, velocity.z).length()
		var motion := "jump" if not is_on_floor() else ("run" if speed > .4 else "idle")
		_play_locomotion(motion, clampf(speed / WALK_SPEED, .72, 1.52) if motion == "run" else 1.0)
	if is_instance_valid(tail_response) and delta > 0.0:
		var local_velocity := model.global_basis.inverse() * ((global_position - previous_position) / delta)
		tail_response.sample_motion(delta, local_velocity, model.rotation.y, is_on_floor() and not vaulting, vaulting, _last_motion)

func _step_movement(delta: float) -> void:
	var movement := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := Basis(Vector3.UP, yaw) * Vector3(movement.x, 0, movement.y)
	var top_speed := SPRINT_SPEED if Input.is_action_pressed("sprint") else WALK_SPEED
	var grounded := is_on_floor()
	var acceleration := GROUND_ACCEL if grounded else AIR_ACCEL
	# Presentation-time commitment stops input drift while attack geometry is
	# resolved from the cast. Movement and gravity remain collision-aware.
	if not _action.is_empty(): direction = Vector3.ZERO
	velocity.x = move_toward(velocity.x, direction.x * top_speed, acceleration * delta)
	velocity.z = move_toward(velocity.z, direction.z * top_speed, acceleration * delta)
	if not grounded: velocity.y -= _gravity * delta
	elif _action.is_empty() and Input.is_action_just_pressed("jump"): velocity.y = JUMP_SPEED
	move_and_slide()
	if _action.is_empty() and direction.length_squared() > .01: _turn_model(direction, TURN_RATE * delta)

func _turn_model(direction: Vector3, weight: float) -> void:
	if direction.length_squared() > .0001:
		model.rotation.y = lerp_angle(model.rotation.y, atan2(direction.x, direction.z), clampf(weight, 0, 1))

func accept_move(origin: Vector3, destination: Vector3, duration: float) -> bool:
	if not active or not _vault.is_empty() or not is_on_floor() or not is_finite(duration): return false
	if not origin.is_finite() or not destination.is_finite() or duration <= 0.0 or duration > 2.0: return false
	if Vector2(origin.x - global_position.x, origin.z - global_position.z).length() > .6: return false
	var landing := Vector3(destination.x, global_position.y, destination.z)
	var distance := global_position.distance_to(landing)
	if distance <= .08 or distance > 12.0: return false
	_vault = {"start":global_position, "finish":landing, "duration":duration, "age":0.0, "height":clampf(distance * .19, .35, 1.55)}
	velocity = Vector3.ZERO
	return true

func _step_vault(delta: float) -> void:
	_vault.age = minf(float(_vault.duration), float(_vault.age) + delta)
	var phase := float(_vault.age) / float(_vault.duration)
	var start: Vector3 = _vault.start
	var finish: Vector3 = _vault.finish
	var next := start.lerp(finish, phase) + Vector3.UP * (4.0 * phase * (1.0 - phase) * float(_vault.height))
	var hit := move_and_collide(next - global_position)
	if hit != null or phase >= 1.0:
		_last_vault = {"blocked": hit != null and phase < .999, "position": global_position, "error_m": global_position.distance_to(finish)}
		_vault.clear()
		velocity = Vector3.ZERO

func play_event(event: Dictionary, definition: Dictionary) -> void:
	if not ready_for_play: return
	var kind := String(event.get("kind", ""))
	if kind == "reset":
		_action.clear()
		if is_instance_valid(tail_response): tail_response.reset()
		_last_motion = ""
		_play_locomotion("idle")
		return
	if kind == "begin":
		var clip := StringName(definition.get("motion", ""))
		if not _clips.has(clip): return
		var length := animator.get_animation(_clips[clip]).length
		var timing: Dictionary = event.get("timing", {})
		var phase := clampf(float(definition.get("motion_phase", .5)), .04, .96)
		_action = {"id": int(event.get("cast_id", -1)), "generation":int(event.get("generation", -1)),
			"clip":clip, "contact_s":length * phase, "length_s":length, "stage":"windup",
			"windup_s":maxf(.001, float(timing.get("windup_s", .2))), "age":0.0,
			"tail_s":maxf(.001, float(timing.get("travel_s", 0)) + float(timing.get("recovery_s", .2)))}
		_turn_model(event.get("forward", aim_forward()), 1.0)
		velocity.x = 0.0
		velocity.z = 0.0
		animator.speed_scale = 1.0
		animator.play(_clips[clip], ABILITY_BLEND, 0.0)
		animator.seek(0.0, true)
		_last_motion = String(clip)
	elif not _action.is_empty() and int(event.get("cast_id", -1)) == int(_action.id) and int(event.get("generation", -1)) == int(_action.generation):
		if kind == "release":
			_action.stage = "released"
			_action.age = 0.0
			animator.seek(float(_action.contact_s), true)
		elif kind in ["recovery", "end", "cancel"]:
			_action.clear()
			if kind == "cancel" and is_instance_valid(tail_response): tail_response.cancel_response()
			_last_motion = ""
			_play_locomotion("jump" if not is_on_floor() else "idle")

func _step_action(delta: float) -> void:
	if _action.is_empty(): return
	_action.age = float(_action.age) + delta
	var release := float(_action.contact_s)
	if _action.stage == "windup":
		animator.seek(release * minf(.999, float(_action.age) / float(_action.windup_s)), true)
	else:
		var phase := minf(1.0, float(_action.age) / float(_action.tail_s))
		animator.seek(lerpf(release, float(_action.length_s), phase), true)

func _play_locomotion(clip: String, speed := 1.0) -> void:
	if not ready_for_play or not _action.is_empty(): return
	animator.speed_scale = speed
	if clip == _last_motion: return
	_last_motion = clip
	animator.play(_clips[clip], ABILITY_BLEND)

func socket_world(socket: StringName) -> Vector3:
	if not ready_for_play: return global_position
	var marker := model.find_child(String(socket), true, false) as Node3D
	if is_instance_valid(marker): return marker.global_position
	if socket == &"wrist.R" or socket == &"head":
		var bone := skeleton.find_bone(socket)
		if bone >= 0: return skeleton.global_transform * skeleton.get_bone_global_pose(bone).origin
	return global_position

func report() -> Dictionary:
	return {"ready":ready_for_play, "error":last_error, "bones":skeleton.get_bone_count() if ready_for_play else 0,
		"clips":_clips.keys(), "motion":_last_motion, "position":global_position,
		"grounded":is_on_floor(), "vault":_vault.duplicate(), "last_vault":_last_vault.duplicate(), "action":_action.duplicate(),
		"tail":tail_response.report() if is_instance_valid(tail_response) else {"configured":false,"last_error":tail_error}}
