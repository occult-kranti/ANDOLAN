extends CharacterBody3D
## Original native locomotion. Feet are the character origin; +Y is up.

signal fired(origin: Vector3, direction: Vector3, empowered: bool)
signal pulse(origin: Vector3)
signal changed
signal traversal_event(kind: String, position: Vector3)

const TraversalController = preload("res://scripts/player_traversal.gd")
const TraversalPose = preload("res://scripts/traversal_pose.gd")

const HERO_PATH := "res://assets/heroes/rama-production.glb"
const SPEED := 6.0
const SPRINT_SPEED := 9.0
const MAGAZINE := 12
const RELOAD_TIME := 1.6

var camera: Camera3D
var pivot: Node3D
var spring: SpringArm3D
var visual: Node3D
var animator: AnimationPlayer
var clips: Dictionary = {}
var active_clip := ""
var active := false
var ammo := MAGAZINE
var reload_remaining := 0.0
var fire_remaining := 0.0
var pulse_remaining := 0.0
var dash_remaining := 0.0
var dash_time := 0.0
var dash_direction := Vector3.ZERO
var action_time := 0.0
var pitch := -0.10
var yaw := 0.0
var sensitivity := 0.0024
var invert_y := false
var shots_fired := 0
var jump_count := 0
var model_ready := false
var current_speed := 0.0
var traversal = TraversalController.new()
var traversal_pose: SkeletonModifier3D
var last_finite_position := Vector3.ZERO

func _ready() -> void:
	collision_layer = 2
	collision_mask = 1 | 4
	floor_snap_length = 0.3
	var body_shape := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.radius = 0.29
	capsule.height = 1.8
	body_shape.shape = capsule
	body_shape.position.y = 0.9
	add_child(body_shape)
	visual = Node3D.new()
	visual.name = "HeroVisual"
	add_child(visual)
	if ResourceLoader.exists(HERO_PATH):
		var model = load(HERO_PATH).instantiate()
		visual.add_child(model)
		animator = _find_animation(model)
		if animator:
			for clip: StringName in animator.get_animation_list():
				var simple := String(clip).get_file().to_lower()
				clips[simple] = clip
				if simple in ["idle", "run"]:
					animator.get_animation(clip).loop_mode = Animation.LOOP_LINEAR
			animator.speed_scale = 1.0
			model_ready = clips.has("idle") and clips.has("run") and clips.has("fire")
			_play("idle", 0.0)
		traversal_pose = TraversalPose.new()
		if not traversal_pose.configure(visual, animator):
			traversal_pose.free()
			traversal_pose = null
	else:
		push_error("Required skinned Rama GLB is missing: " + HERO_PATH)
	visual.rotation.y = PI
	pivot = Node3D.new()
	pivot.name = "CameraPivot"
	pivot.position.y = 1.50
	add_child(pivot)
	spring = SpringArm3D.new()
	spring.name = "CameraCollision"
	spring.spring_length = 3.5
	# Offset the arm itself: SpringArm3D controls its camera child's position.
	spring.position.x = 0.65
	spring.margin = 0.20
	spring.collision_mask = 1
	spring.add_excluded_object(get_rid())
	var camera_shape := SphereShape3D.new()
	camera_shape.radius = 0.18
	spring.shape = camera_shape
	pivot.add_child(spring)
	camera = Camera3D.new()
	camera.name = "PlayerCamera"
	camera.fov = 65
	camera.near = 0.08
	camera.far = 180
	camera.position.x = 0.0
	spring.add_child(camera)
	camera.current = true
	_update_camera()
	traversal.initialize(self)
	last_finite_position = global_position
	if not get_window().focus_exited.is_connected(_on_focus_lost):
		get_window().focus_exited.connect(_on_focus_lost)

func configure_traversal(anchors: Array, bounds: AABB) -> bool:
	return traversal.configure(anchors, bounds)

func toggle_flight() -> bool:
	return traversal.toggle_flight()

func try_grapple() -> bool:
	return traversal.try_grapple()

func cancel_traversal(reason := "cancelled") -> void:
	traversal.cancel(reason)
	if is_instance_valid(traversal_pose):
		traversal_pose.cancel()

func traversal_report() -> Dictionary:
	var result: Dictionary = traversal.report()
	result["pose"] = traversal_pose.diagnostics() if is_instance_valid(traversal_pose) else {}
	return result

func _on_focus_lost() -> void:
	cancel_traversal("Window focus lost")

func _notification(what: int) -> void:
	if what == NOTIFICATION_PAUSED and is_instance_valid(traversal):
		cancel_traversal("Paused")

func _find_animation(node: Node) -> AnimationPlayer:
	if node is AnimationPlayer:
		return node
	for child in node.get_children():
		var found := _find_animation(child)
		if found:
			return found
	return null

func _unhandled_input(event: InputEvent) -> void:
	if not active or get_tree().paused:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		if not event.relative.is_finite() or not is_finite(sensitivity):
			return
		yaw -= event.relative.x * sensitivity
		pitch -= event.relative.y * sensitivity * (-1.0 if invert_y else 1.0)
		pitch = clampf(pitch, -0.85, 0.6)
		_update_camera()

func _update_camera() -> void:
	if not is_finite(yaw) or not is_finite(pitch):
		yaw = 0.0
		pitch = -0.10
	pivot.rotation = Vector3(pitch, yaw, 0)

func _physics_process(delta: float) -> void:
	if not active:
		if traversal.mode != "ground":
			cancel_traversal("Player inactive")
		return
	if not is_finite(delta) or delta <= 0 or delta > 0.1:
		cancel_traversal("Invalid physics step")
		return
	if not global_position.is_finite() or not velocity.is_finite() or not is_finite(yaw) or not is_finite(pitch):
		if not global_position.is_finite():
			global_position = last_finite_position
		cancel_traversal("Invalid movement state")
		_update_camera()
		return
	fire_remaining = maxf(0, fire_remaining - delta)
	pulse_remaining = maxf(0, pulse_remaining - delta)
	dash_remaining = maxf(0, dash_remaining - delta)
	action_time = maxf(0, action_time - delta)
	if reload_remaining > 0:
		reload_remaining = maxf(0, reload_remaining - delta)
		if reload_remaining == 0:
			ammo = MAGAZINE
			changed.emit()
	var move_input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var desired := Basis(Vector3.UP, yaw) * Vector3(move_input.x, 0, move_input.y)
	var speed := SPRINT_SPEED if Input.is_action_pressed("sprint") else SPEED
	var traversal_owns_motion: bool = traversal.step(delta, desired)
	if not traversal_owns_motion and Input.is_action_just_pressed("dash") and dash_remaining <= 0:
		dash_direction = desired.normalized() if desired.length_squared() > 0.01 else -pivot.global_basis.z
		dash_direction.y = 0
		dash_direction = dash_direction.normalized()
		dash_time = 0.18
		dash_remaining = 5.0
	if traversal_owns_motion:
		pass
	elif dash_time > 0:
		dash_time = maxf(0, dash_time - delta)
		velocity.x = dash_direction.x * 21.0
		velocity.z = dash_direction.z * 21.0
	else:
		var accel := 38.0 if is_on_floor() else 12.0
		velocity.x = move_toward(velocity.x, desired.x * speed, accel * delta)
		velocity.z = move_toward(velocity.z, desired.z * speed, accel * delta)
	if traversal_owns_motion:
		pass
	elif is_on_floor():
		if Input.is_action_just_pressed("jump"):
			velocity.y = 7.2
			jump_count += 1
			_play("jump", 0.12)
	else:
		velocity.y -= 18.0 * delta
	traversal.limit_to_bounds(delta)
	move_and_slide()
	last_finite_position = global_position
	traversal.after_step()
	current_speed = Vector2(velocity.x, velocity.z).length()
	if Input.is_action_just_pressed("reload"):
		start_reload()
	if Input.is_action_pressed("fire"):
		shoot()
	if Input.is_action_just_pressed("pulse") and pulse_remaining <= 0:
		pulse_remaining = 8.0
		action_time = 0.7
		_play("cast1", 0.12)
		pulse.emit(global_position + Vector3.UP)
		changed.emit()
	var forward := -pivot.global_basis.z
	forward.y = 0
	if action_time > 0:
		_rotate_visual(forward, delta * 16.0)
	elif traversal.mode in ["flight", "grapple"]:
		_rotate_visual(forward, delta * 10.0)
		_play("idle", 0.18)
	elif not is_on_floor():
		_play("jump", 0.14)
	elif current_speed > 0.15:
		_rotate_visual(Vector3(velocity.x, 0, velocity.z), delta * 14.0)
		_play("run", 0.16)
		if animator:
			animator.speed_scale = clampf(current_speed / SPEED, 0.7, 1.5)
	else:
		_play("idle", 0.20)
		if animator:
			animator.speed_scale = 1.0
	if is_instance_valid(traversal_pose):
		traversal_pose.set_state(traversal.mode, velocity.length(), velocity.y, delta, 1.0 if action_time > 0 else 0.0)
	if global_position.y < -8:
		reset()

func _rotate_visual(direction: Vector3, weight: float) -> void:
	if direction.length_squared() < 0.001:
		return
	# Authored GLB faces +Z; camera and gameplay forward are -Z.
	visual.rotation.y = lerp_angle(visual.rotation.y, atan2(direction.x, direction.z), clampf(weight, 0, 1))

func _play(clip: String, blend: float) -> void:
	if animator and clips.has(clip) and active_clip != clip:
		active_clip = clip
		animator.speed_scale = 1.0
		animator.play(clips[clip], blend)

func shoot() -> bool:
	if not active or get_tree().paused or fire_remaining > 0 or reload_remaining > 0:
		return false
	if ammo <= 0:
		start_reload()
		return false
	var center := get_viewport().get_visible_rect().size * 0.5
	var start := camera.project_ray_origin(center)
	var direction := camera.project_ray_normal(center)
	var query := PhysicsRayQueryParameters3D.create(start, start + direction * 100, 1 | 4, [get_rid()])
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	var destination: Vector3 = hit.position if not hit.is_empty() else start + direction * 100
	var origin := global_position + Vector3(0, 1.28, 0) + (-pivot.global_basis.z * 0.45)
	var aim := (destination - origin).normalized()
	ammo -= 1
	shots_fired += 1
	fire_remaining = 0.24
	action_time = 0.32
	_play("fire", 0.055)
	# Repeated primary fire restarts its pose without accumulating animation tracks.
	if animator and clips.has("fire"):
		animator.seek(0, true)
	fired.emit(origin, aim, false)
	changed.emit()
	return true

func start_reload() -> bool:
	if ammo == MAGAZINE or reload_remaining > 0 or not active:
		return false
	reload_remaining = RELOAD_TIME
	changed.emit()
	return true

func reset() -> void:
	cancel_traversal("Reset")
	position = Vector3(0, 0.05, 12)
	velocity = Vector3.ZERO
	yaw = 0
	pitch = -0.10
	ammo = MAGAZINE
	reload_remaining = 0
	fire_remaining = 0
	pulse_remaining = 0
	dash_remaining = 0
	dash_time = 0
	action_time = 0
	shots_fired = 0
	jump_count = 0
	visual.rotation.y = PI
	_update_camera()
	_play("idle", 0.12)
	traversal.reset()
	last_finite_position = global_position
	changed.emit()
