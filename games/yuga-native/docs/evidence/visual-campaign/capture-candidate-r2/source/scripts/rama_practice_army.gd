extends Node3D
## Courtyard adapter for the same Rama combat clock and geometry contract as lanes.
signal simulation_stepped(delta: float)
signal simulation_reset(reason: String)
signal outcome(winning_team: String)

const Receiver = preload("res://scripts/rama_practice_target.gd")
const LaneGeometry = preload("res://scripts/lane_army.gd")
const STEP := .05
const MAX_TARGETS := 32
var configured := false
var suspended := false
var winner := ""
var elapsed := 0.0
var units: Array = []
var actor_bounds := [-22.0, 22.0, -25.0, 25.0]
var boxes: Array = [
	{"position":Vector3(-22.25,2,0), "size":Vector3(.5,4,50)},
	{"position":Vector3(22.25,2,0), "size":Vector3(.5,4,50)},
	{"position":Vector3(0,2,-25.25), "size":Vector3(45,4,.5)},
	{"position":Vector3(0,2,25.25), "size":Vector3(45,4,.5)},
]
var _accumulator := 0.0
var _geometry = LaneGeometry.new()
var generation := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func configure(targets: Array) -> bool:
	if not is_inside_tree() or targets.is_empty() or targets.size() > MAX_TARGETS:return false
	var seen: Array = []
	for target in targets:
		if not is_instance_valid(target) or not target is Node3D or not target.is_inside_tree() or not target.has_signal("struck") or not target.has_method("reset_target") or seen.has(target):return false
		if not is_instance_valid(target.get("body")) or not is_instance_valid(target.get("label")):return false
		seen.append(target)
	clear("reconfigure")
	configured = true
	suspended = false
	for index in targets.size():
		var receiver = Receiver.new()
		receiver.name = "PracticeReceiver%02d" % (index + 1)
		add_child(receiver)
		receiver.configure(self, targets[index], index + 1)
		units.append(receiver)
	reset("configure")
	return true

func set_suspended(value: bool) -> void:
	suspended = value
	# A pause must not leave accumulated time to catch up on resume.
	if value:_accumulator = 0.0

func _physics_process(delta: float) -> void:
	if not configured or suspended or not is_finite(delta) or delta <= 0.0:return
	_accumulator += minf(delta, .25)
	var steps := 0
	while _accumulator + 1e-9 >= STEP and steps < 5:
		_accumulator = maxf(0.0, _accumulator - STEP)
		if not step_simulation(STEP):break
		steps += 1

func step_simulation(delta: float = STEP) -> bool:
	if not configured or suspended or not is_inside_tree() or get_tree().paused or not winner.is_empty() or not is_finite(delta) or delta <= 0.0 or delta > STEP + .000001:return false
	elapsed += delta
	for unit in units:
		if is_instance_valid(unit):unit.step_statuses(elapsed, delta)
	simulation_stepped.emit(delta)
	return true

func reset(reason: String = "practice_reset") -> void:
	elapsed = 0.0
	_accumulator = 0.0
	winner = ""
	generation += 1
	# Subscribers first discard any cast-owned effects on the old target state.
	simulation_reset.emit(reason)
	for unit in units:
		if is_instance_valid(unit):unit.reset()

func clear(reason: String = "practice_clear") -> void:
	configured = false
	simulation_reset.emit(reason)
	for unit in units:
		if is_instance_valid(unit):
			unit.detach()
			unit.free()
	units.clear()
	elapsed = 0.0
	_accumulator = 0.0
	winner = ""

func _exit_tree() -> void:
	clear("scene_exit")
	if is_instance_valid(_geometry):_geometry.free()

func _blocked_with(point: Vector3, obstacles: Array, bounds: Array, margin: float) -> bool:
	if not point.is_finite() or not is_finite(margin) or margin < 0.0:return true
	return _geometry._blocked_with(point, obstacles, bounds, margin)

func line_clear(from_point: Vector3, to_point: Vector3, margin: float = 0.0) -> bool:
	return not is_finite(segment_wall_fraction(from_point, to_point, margin))

func segment_wall_fraction(start: Vector3, finish: Vector3, margin: float = 0.0) -> float:
	if not start.is_finite() or not finish.is_finite() or not is_finite(margin) or margin < 0.0:return 0.0
	_geometry.boxes = boxes
	var nearest: float = _geometry.segment_wall_fraction(start, finish, margin)
	if not is_inside_tree() or start.distance_squared_to(finish) < .00000001:return nearest
	# Imported courtyard meshes use collision layer 1. A chest-height ray adds
	# their actual occlusion to the planar boundary contract; targets are layer 4.
	var from := to_global(start + Vector3.UP * 1.2)
	var to := to_global(finish + Vector3.UP * 1.2)
	var query := PhysicsRayQueryParameters3D.create(from, to, 1)
	query.hit_from_inside = true
	var hit := get_world_3d().direct_space_state.intersect_ray(query)
	if not hit.is_empty():nearest = minf(nearest, from.distance_to(hit.position) / from.distance_to(to))
	return nearest

func report() -> Dictionary:
	var receivers: Array = []
	for unit in units:
		if is_instance_valid(unit):receivers.append(unit.report())
	return {"configured":configured, "suspended":suspended, "generation":generation, "elapsed":elapsed, "winner":winner, "targets":receivers, "clock_hz":20, "automatic_respawn":false, "network_enabled":false}
