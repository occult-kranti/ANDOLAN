extends SceneTree
## Isolated Godot-space collision regression, not input or renderer evidence.
## godot --headless --path games/yuga-native --script res://tests/projectile_cases.gd

const ProjectileScript = preload("res://scripts/projectile.gd")

class DamageTarget extends StaticBody3D:
	var hits := 0
	func take_hit(amount: int) -> void:
		hits += amount

class StepDriver extends Node:
	signal stepped
	var pending: Callable
	func _physics_process(_delta: float) -> void:
		if pending.is_valid():
			var work := pending
			pending = Callable()
			work.call()
			stepped.emit()

var arena: Node3D
var driver: StepDriver
var checks: Array[Dictionary] = []
var source_before := ""

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	source_before = FileAccess.get_sha256("res://scripts/projectile.gd")
	driver = StepDriver.new()
	root.add_child(driver)
	await _final_segment_hit()
	await _range_limit()
	await _wall_occlusion()
	await _ignored_shooter()
	await _partitioned_lifetime()
	await _already_expired()
	_record("source_unchanged_during_cases", source_before == FileAccess.get_sha256("res://scripts/projectile.gd"), {})
	var passed := true
	for check in checks:
		passed = passed and check.passed
	var report := {"passed": passed, "engine": Engine.get_version_info().string,
		"projectile_sha256": source_before, "checks": checks,
		"scope": "Explicit isolated fixtures and injected physics deltas. Ray queries run inside a real _physics_process callback. No renderer, normal-input, multiplayer or frame-rate claim."}
	print("YUGA_PROJECTILE_CASES ", JSON.stringify(report))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			if file:
				file.store_string(JSON.stringify(report, "\t") + "\n")
			else:
				push_error("Could not write projectile report")
				passed = false
	driver.queue_free()
	await process_frame
	quit(0 if passed else 1)

func _fixture() -> void:
	if is_instance_valid(arena):
		arena.queue_free()
		await process_frame
		await process_frame
	arena = Node3D.new()
	root.add_child(arena)

func _target(distance: float, layer: int = 4) -> DamageTarget:
	var target := DamageTarget.new()
	target.collision_layer = layer
	target.collision_mask = 0
	target.position = Vector3(0, 1, -distance)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(1, 1, 0.02)
	shape.shape = box
	target.add_child(shape)
	arena.add_child(target)
	return target

func _projectile(remaining: float, metres_per_second: float = 54.0):
	var projectile = ProjectileScript.new()
	projectile.position = Vector3(0, 1, 0)
	projectile.life = remaining
	projectile.speed = metres_per_second
	arena.add_child(projectile)
	projectile.set_physics_process(false)
	return projectile

func _ready_physics() -> void:
	await physics_frame
	await physics_frame

func _step(projectile: Node3D, delta: float) -> void:
	driver.pending = func(): projectile._physics_process(delta)
	await driver.stepped

func _final_segment_hit() -> void:
	await _fixture()
	var target := _target(2.30)
	await _ready_physics()
	var projectile = _projectile(0.05)
	var impacts: Array[Dictionary] = []
	projectile.impacted.connect(func(position: Vector3, collider: Node): impacts.append({"position": position, "collider": collider}))
	await _step(projectile, 0.10)
	_record("final_partial_lifetime_still_hits", target.hits == 1 and impacts.size() == 1 and impacts[0].collider == target and is_equal_approx(impacts[0].position.z, -2.29) and projectile.is_queued_for_deletion(), {"damage": target.hits, "impacts": impacts.size(), "remaining_seconds": 0.05, "tick_seconds": 0.1, "maximum_travel_metres": 2.7})

func _range_limit() -> void:
	await _fixture()
	var target := _target(2.72)
	await _ready_physics()
	var projectile = _projectile(0.05)
	await _step(projectile, 0.10)
	_record("expiry_does_not_overshoot_range", target.hits == 0 and is_equal_approx(projectile.position.z, -2.7) and projectile.is_queued_for_deletion(), {"damage": target.hits, "travel_metres": -projectile.position.z, "first_out_of_range_surface_metres": 2.71})

func _wall_occlusion() -> void:
	await _fixture()
	var wall := _target(2.0, 1)
	var target := _target(6.0)
	await _ready_physics()
	var projectile = _projectile(1.0, 600.0)
	var colliders: Array[Node] = []
	projectile.impacted.connect(func(_position: Vector3, collider: Node): colliders.append(collider))
	await _step(projectile, 1.0 / 60.0)
	_record("fast_sweep_respects_thin_wall", wall.hits == 1 and target.hits == 0 and colliders.size() == 1 and colliders[0] == wall and projectile.is_queued_for_deletion(), {"wall_damage": wall.hits, "target_damage": target.hits, "wall_thickness_metres": 0.02, "tick_travel_metres": 10.0})

func _ignored_shooter() -> void:
	await _fixture()
	var shooter := _target(1.0)
	var target := _target(2.0)
	await _ready_physics()
	var projectile = _projectile(1.0, 300.0)
	projectile.ignore.assign([shooter.get_rid()])
	await _step(projectile, 1.0 / 60.0)
	_record("shooter_exclusion_preserved", shooter.hits == 0 and target.hits == 1 and projectile.is_queued_for_deletion(), {"shooter_damage": shooter.hits, "target_damage": target.hits})

func _partitioned_lifetime() -> void:
	await _fixture()
	await _ready_physics()
	var projectile = _projectile(0.05)
	# All five substeps stay in one real physics callback so the queued deletion
	# can be inspected before the engine frees the completed projectile.
	driver.pending = func():
		for index in 5:
			projectile._physics_process(0.01)
	await driver.stepped
	_record("partitioned_expiry_preserves_total_range", is_equal_approx(projectile.position.z, -2.7) and projectile.is_queued_for_deletion(), {"travel_metres": -projectile.position.z, "substeps": 5, "substep_seconds": 0.01})

func _already_expired() -> void:
	await _fixture()
	var target := _target(0.1)
	await _ready_physics()
	var projectile = _projectile(0.0)
	await _step(projectile, 0.1)
	_record("already_expired_has_no_travel_or_damage", target.hits == 0 and projectile.position == Vector3(0, 1, 0) and projectile.is_queued_for_deletion(), {"damage": target.hits, "travel_metres": -projectile.position.z})

func _record(label: String, passed: bool, details: Dictionary) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)
