extends RefCounted
## Original bounded native traversal, reconstructed after workspace loss.
## CharacterBody3D.move_and_slide remains the only traversal translation path.

const MAX_ENERGY := 100.0
const FLIGHT_SPEED := 12.0
const GRAPPLE_SPEED := 18.0
const MAX_RANGE := 36.0
const AIM_COS := 0.9271838546 # 22 degrees.
const MAX_ANCHORS := 64

var actor
var enabled := false
var mode := "ground"
var energy := MAX_ENERGY
var flight_cooldown := 0.0
var grapple_cooldown := 0.0
var target: Dictionary = {}
var anchors: Array[Dictionary] = []
var bounds := AABB()
var status := "Traversal is available in Confluence"
var grapple_elapsed := 0.0
var rope: MeshInstance3D
var last_position := Vector3.ZERO
var have_position := false
var recharge_notified := true

func initialize(player) -> void:
	actor = player
	rope = MeshInstance3D.new()
	rope.name = "TraversalRope"
	var cylinder := CylinderMesh.new()
	cylinder.top_radius = 0.022
	cylinder.bottom_radius = 0.022
	cylinder.height = 1.0
	cylinder.radial_segments = 8
	rope.mesh = cylinder
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(0.95, 0.67, 0.19)
	material.emission_enabled = true
	material.emission = Color(0.7, 0.35, 0.05)
	material.emission_energy_multiplier = 0.65
	material.roughness = 0.75
	rope.material_override = material
	rope.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	actor.add_child(rope)
	rope.top_level = true
	rope.visible = false
	last_position = actor.global_position
	have_position = true

func configure(values: Array, area: AABB) -> bool:
	cancel("configuration changed")
	enabled = false
	anchors.clear()
	if not area.position.is_finite() or not area.size.is_finite() or area.size.x <= 0 or area.size.y <= 0 or area.size.z <= 0 or values.is_empty() or values.size() > MAX_ANCHORS:
		status = "Invalid traversal configuration"
		return false
	var prepared: Array[Dictionary] = []
	var ids := {}
	for index in values.size():
		var value = values[index]
		var point: Vector3
		var id := "anchor-%02d" % index
		if value is Vector3:
			point = value
		elif value is Dictionary and value.get("position") is Vector3:
			point = value.position
			id = str(value.get("id", id))
		else:
			status = "Invalid anchor position"
			return false
		if not point.is_finite() or id.is_empty() or ids.has(id) or not area.has_point(point):
			status = "Invalid or duplicate anchor"
			return false
		ids[id] = true
		prepared.append({"id": id, "position": point})
	anchors = prepared
	bounds = area
	enabled = true
	energy = MAX_ENERGY
	flight_cooldown = 0.0
	grapple_cooldown = 0.0
	status = "Traversal ready"
	last_position = actor.global_position
	have_position = true
	return true

func _allowed() -> bool:
	return enabled and is_instance_valid(actor) and actor.active and actor.is_inside_tree() and not actor.get_tree().paused

func _event(kind: String) -> void:
	if is_instance_valid(actor) and actor.global_position.is_finite():
		actor.traversal_event.emit(kind, actor.global_position)

func _clear_dash() -> void:
	actor.dash_time = 0.0
	actor.dash_direction = Vector3.ZERO

func toggle_flight() -> bool:
	if mode == "flight":
		cancel("Flight released")
		return true
	if not _allowed() or not is_finite(energy) or energy < 15.0 or flight_cooldown > 0.0:
		status = "Flight needs energy and a ready cooldown"
		return false
	if mode == "grapple":
		cancel("Tether released")
	mode = "flight"
	target = {}
	energy = maxf(0.0, energy - 10.0)
	recharge_notified = false
	_clear_dash()
	actor.velocity = actor.velocity.limit_length(FLIGHT_SPEED) if actor.velocity.is_finite() else Vector3.ZERO
	status = "Flight active"
	_event("flight_start")
	return true

func candidate() -> Dictionary:
	if not _allowed() or not actor.global_position.is_finite() or not is_instance_valid(actor.camera):
		return {}
	var chest: Vector3 = actor.global_position + Vector3(0, 1.28, 0)
	var eye: Vector3 = actor.camera.global_position
	var forward: Vector3 = -actor.camera.global_basis.z.normalized()
	if not eye.is_finite() or not forward.is_finite():
		return {}
	var best := {}
	var score := -INF
	for entry in anchors:
		var point: Vector3 = entry.position
		if not point.is_finite():
			continue
		var distance := chest.distance_to(point)
		var view := point - eye
		if distance < 1.7 or distance > MAX_RANGE or view.length_squared() < 0.001:
			continue
		var alignment := forward.dot(view.normalized())
		if alignment < AIM_COS or not _clear_ray(eye, point) or not _clear_ray(chest, point):
			continue
		var value := alignment - distance * 0.0001
		if value > score:
			score = value
			best = {"id": entry.id, "position": point, "distance": distance}
	return best

func _clear_ray(from: Vector3, to: Vector3) -> bool:
	var exclusions: Array[RID] = [actor.get_rid()]
	var query := PhysicsRayQueryParameters3D.create(from, to, 1 | 4, exclusions)
	return actor.get_world_3d().direct_space_state.intersect_ray(query).is_empty()

func try_grapple() -> bool:
	if mode == "grapple":
		cancel("Tether released")
		return true
	if not _allowed() or not is_finite(energy) or energy < 18.0 or grapple_cooldown > 0:
		status = "Tether needs energy and a ready cooldown"
		return false
	var found := candidate()
	if found.is_empty():
		status = "No clear ring in aim and range"
		return false
	if mode == "flight":
		cancel("Flight released")
	target = found
	mode = "grapple"
	grapple_elapsed = 0.0
	energy = maxf(0.0, energy - 18.0)
	recharge_notified = false
	_clear_dash()
	actor.velocity = actor.velocity.limit_length(GRAPPLE_SPEED) if actor.velocity.is_finite() else Vector3.ZERO
	status = "Tether engaged"
	_event("grapple_lock")
	return true

func cancel(reason := "cancelled") -> void:
	var previous := mode
	mode = "ground"
	target = {}
	grapple_elapsed = 0.0
	status = reason
	if previous == "flight":
		flight_cooldown = maxf(flight_cooldown, 1.2)
	if previous == "grapple":
		grapple_cooldown = maxf(grapple_cooldown, 1.0)
		_event("grapple_release")
	if is_instance_valid(actor):
		actor.velocity = Vector3.ZERO
		_clear_dash()
	if is_instance_valid(rope):
		rope.visible = false
	for action in ["grapple", "fly", "descend", "jump"]:
		if InputMap.has_action(action):
			Input.action_release(action)

func reset() -> void:
	cancel("Traversal ready" if enabled else "Traversal is available in Confluence")
	energy = MAX_ENERGY
	flight_cooldown = 0.0
	grapple_cooldown = 0.0
	recharge_notified = true
	last_position = actor.global_position
	have_position = true

func step(delta: float, desired: Vector3) -> bool:
	if not enabled:
		return false
	if not is_finite(delta) or delta <= 0 or delta > 0.1 or not desired.is_finite() or not is_finite(energy):
		energy = 0.0 if not is_finite(energy) else clampf(energy, 0, MAX_ENERGY)
		cancel("Invalid traversal state")
		return true
	if have_position and actor.global_position.distance_to(last_position) > 2.0:
		cancel("Position changed")
	flight_cooldown = maxf(0, flight_cooldown - delta)
	grapple_cooldown = maxf(0, grapple_cooldown - delta)
	energy = clampf(energy, 0, MAX_ENERGY)
	if InputMap.has_action("fly") and Input.is_action_just_pressed("fly"):
		toggle_flight()
	if InputMap.has_action("grapple") and Input.is_action_just_pressed("grapple"):
		try_grapple()
	if mode == "ground":
		if actor.is_on_floor():
			energy = minf(MAX_ENERGY, energy + 26.0 * delta)
			if energy >= MAX_ENERGY and not recharge_notified:
				recharge_notified = true
				_event("flight_recharge")
		return false
	_clear_dash()
	if mode == "flight":
		energy = maxf(0, energy - 18.0 * delta)
		var vertical := float(Input.is_action_pressed("jump")) - float(InputMap.has_action("descend") and Input.is_action_pressed("descend"))
		var wanted := (desired.limit_length(1.0) * 10.0 + Vector3.UP * vertical * 6.0).limit_length(FLIGHT_SPEED)
		actor.velocity = actor.velocity.move_toward(wanted, 30.0 * delta).limit_length(FLIGHT_SPEED)
	else:
		energy = maxf(0, energy - 10.0 * delta)
		grapple_elapsed += delta
		if target.is_empty() or not target.position.is_finite():
			cancel("Tether target unavailable")
			return true
		var chest: Vector3 = actor.global_position + Vector3(0, 1.28, 0)
		var offset: Vector3 = target.position - chest
		if offset.length() < 1.7 or grapple_elapsed >= 3.0 or not _clear_ray(chest, target.position):
			cancel("Tether arrived" if offset.length() < 1.7 else "Tether released")
			return true
		var wanted := offset.normalized() * minf(GRAPPLE_SPEED, offset.length() * 4.0)
		actor.velocity = actor.velocity.move_toward(wanted, 42.0 * delta).limit_length(GRAPPLE_SPEED)
	if energy <= 0:
		var exhausted_flight := mode == "flight"
		cancel("Energy depleted")
		if exhausted_flight:
			_event("flight_exhaust")
	return true

func limit_to_bounds(delta: float) -> void:
	if not enabled or delta <= 0 or not is_finite(delta):
		return
	var point: Vector3 = actor.global_position
	var low := bounds.position
	var high := bounds.end
	for axis in 3:
		# Velocity clipping keeps movement collision-based; it never teleports feet.
		actor.velocity[axis] = clampf(actor.velocity[axis], minf(0.0, (low[axis] - point[axis]) / delta), maxf(0.0, (high[axis] - point[axis]) / delta))

func after_step() -> void:
	last_position = actor.global_position
	have_position = true
	rope.visible = mode == "grapple" and not target.is_empty()
	if not rope.visible:
		return
	var from: Vector3 = actor.global_position + Vector3(0, 1.28, 0)
	if is_instance_valid(actor.traversal_pose):
		var skeleton: Skeleton3D = actor.traversal_pose.get_skeleton()
		if skeleton:
			var wrist := skeleton.find_bone("wrist.L")
			if wrist >= 0:
				from = skeleton.global_transform * skeleton.get_bone_global_pose(wrist).origin
	var offset: Vector3 = target.position - from
	var length := offset.length()
	if not from.is_finite() or not offset.is_finite() or length < 0.001:
		rope.visible = false
		return
	var up := offset / length
	var right := up.cross(Vector3.FORWARD).normalized()
	if right.length_squared() < 0.1:
		right = up.cross(Vector3.RIGHT).normalized()
	rope.global_transform = Transform3D(Basis(right, up * length, right.cross(up)), from + offset * 0.5)

func report() -> Dictionary:
	return {"enabled": enabled, "mode": mode, "energy": energy, "max_energy": MAX_ENERGY,
		"flight_cooldown": flight_cooldown, "grapple_cooldown": grapple_cooldown,
		"target": target.duplicate(true), "candidate": candidate(), "status": status,
		"altitude": actor.global_position.y, "altitude_cap": bounds.end.y if enabled else 0.0,
		"rope_visible": is_instance_valid(rope) and rope.visible, "anchor_count": anchors.size(),
		"max_range": MAX_RANGE, "speed_cap": GRAPPLE_SPEED if mode == "grapple" else FLIGHT_SPEED}
