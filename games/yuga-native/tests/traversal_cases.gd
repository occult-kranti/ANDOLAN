extends SceneTree
## Reconstructed implementation QA: actual CharacterBody3D physics, synthetic input.
## No rendering, independent-author claim, or visual acceptance is implied.

const Player = preload("res://scripts/player.gd")
const AREA := AABB(Vector3(-40, 0, -40), Vector3(80, 24, 80))
const ACTIONS := ["move_left", "move_right", "move_forward", "move_back", "jump", "sprint", "fire", "reload", "pulse", "dash", "fly", "grapple", "descend"]
var player
var fixture: Node3D
var checks: Array[Dictionary] = []
var events: Array[String] = []
var peak_speed := 0.0
var min_energy := 100.0
var finite := true
var physics_samples := 0
var initial_hashes := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	initial_hashes = _hashes()
	for action in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
	fixture = Node3D.new()
	root.add_child(fixture)
	_box(Vector3(0, -0.5, 0), Vector3(100, 1, 100))
	player = Player.new()
	fixture.add_child(player)
	player.traversal_event.connect(func(kind: String, _position: Vector3): events.append(kind))
	player.active = true
	player.position = Vector3(0, 0.05, 12)
	await _frames(20)
	_record("disabled_until_valid_world_configuration", not player.traversal_report().enabled and not player.toggle_flight() and not player.try_grapple())
	_record("empty_anchor_configuration_rejected", not player.configure_traversal([], AREA))
	_record("nonfinite_anchor_rejected", not player.configure_traversal([Vector3(NAN, 2, 1)], AREA))
	_record("duplicate_anchor_id_rejected", not player.configure_traversal([{"id":"same", "position":Vector3(0, 8, -12)}, {"id":"same", "position":Vector3(2, 8, -12)}], AREA))
	_record("out_of_bounds_anchor_rejected", not player.configure_traversal([Vector3(0, 30, 0)], AREA))
	_record("invalid_bounds_rejected", not player.configure_traversal([Vector3.ZERO], AABB(Vector3.ZERO, Vector3(-1, 24, 80))))
	var excessive: Array = []
	for index in 65:
		excessive.append(Vector3(index * 0.1, 12, 0))
	_record("anchor_pool_is_bounded", not player.configure_traversal(excessive, AREA))
	_record("finite_configuration_enables_traversal", player.configure_traversal([{"id":"north", "position":Vector3(0, 12, -12)}], AREA))
	await _reset()
	_record("flight_starts_and_charges_energy", player.toggle_flight() and player.traversal.mode == "flight" and is_equal_approx(player.traversal.energy, 90.0))
	Input.action_press("jump")
	Input.action_press("move_forward")
	Input.action_press("move_right")
	await _frames(90)
	_record("flight_uses_real_ascent_and_planar_motion", player.position.y > 5.0 and player.position.x > 5.0 and player.position.z < 7.0, {"position": _v(player.position)})
	_record("flight_diagonal_speed_is_capped", peak_speed <= 12.0001, {"maximum_speed": peak_speed})
	Input.action_press("dash")
	await _frames(2)
	_record("flight_cannot_add_dash_acceleration", player.dash_time == 0 and player.velocity.length() <= 12.0001)
	_release()
	player.position = Vector3(0, 23.8, 0)
	player.traversal.after_step() # Fixture setup; the take itself uses real physics.
	Input.action_press("jump")
	await _frames(50)
	_record("feet_ceiling_is_enforced_without_teleport", player.position.y <= 24.001, {"feet_y": player.position.y})
	_release()
	player.cancel_traversal("fixture")
	await _reset()
	player.toggle_flight()
	Input.action_press("jump")
	await _frames(320)
	_record("finite_fuel_exhausts_flight", player.traversal.mode == "ground" and events.has("flight_exhaust") and min_energy >= 0, {"energy": player.traversal.energy})
	await _frames(130)
	player.traversal.energy = 10.0
	player.traversal.recharge_notified = false
	await _frames(240)
	_record("ground_recharges_bounded_energy", player.is_on_floor() and is_equal_approx(player.traversal.energy, 100.0) and events.has("flight_recharge"))
	await _reset()
	_aim(Vector3(0, 12, -12))
	_record("eligible_ring_requires_actual_camera_aim", player.traversal_report().candidate.get("id", "") == "north")
	_record("grapple_locks_visible_ring", player.try_grapple() and player.traversal.mode == "grapple")
	var start: Vector3 = player.position
	peak_speed = 0
	await _frames(45)
	_record("grapple_pulls_through_character_physics", player.position.distance_to(start) > 6 and player.position.y > 2, {"position": _v(player.position), "distance": player.position.distance_to(start)})
	_record("grapple_speed_and_rope_are_bounded", peak_speed <= 18.0001 and player.traversal.rope.visible and player.traversal.rope.global_transform.is_finite(), {"maximum_speed": peak_speed})
	_record("grapple_toggle_releases_once", player.try_grapple() and player.traversal.mode == "ground" and not player.traversal.rope.visible and player.traversal.grapple_cooldown > 0)
	_record("grapple_cooldown_blocks_reentry", not player.try_grapple())
	await _reset()
	_aim(Vector3(0, 12, -12))
	var blocker := _box(Vector3(0, 6, 0), Vector3(12, 14, 0.10))
	await _frames(3)
	_record("solid_wall_blocks_grapple_los", player.traversal_report().candidate.is_empty() and not player.try_grapple())
	player.toggle_flight()
	Input.action_press("move_forward")
	await _frames(120)
	_record("thin_wall_stops_flight_without_tunneling", player.position.z >= 0.33 and player.position.is_finite(), {"z": player.position.z})
	_release()
	blocker.queue_free()
	await _frames(2)
	await _reset()
	player.configure_traversal([Vector3(39, 12, -12)], AREA)
	_aim(Vector3(39, 12, -12))
	_record("out_of_range_ring_is_not_candidate", player.traversal_report().candidate.is_empty() and not player.try_grapple())
	await _reset()
	_aim(Vector3(0, 12, 30))
	_record("off_aim_ring_is_not_candidate", player.traversal_report().candidate.is_empty())
	player.toggle_flight()
	Input.action_press("jump")
	Input.action_press("fly")
	player.cancel_traversal("pause fixture")
	_record("cancel_clears_velocity_dash_rope_and_held_actions", player.velocity == Vector3.ZERO and player.dash_time == 0 and not player.traversal.rope.visible and not Input.is_action_pressed("jump") and not Input.is_action_pressed("fly"))
	await _reset()
	player.toggle_flight()
	paused = true
	_record("tree_pause_cancels_active_traversal", player.traversal.mode == "ground" and player.velocity == Vector3.ZERO)
	paused = false
	await _reset()
	player.toggle_flight()
	player._on_focus_lost()
	_record("focus_loss_cancels_traversal", player.traversal.mode == "ground" and player.velocity == Vector3.ZERO)
	await _reset()
	player.toggle_flight()
	player.active = false
	await _frames(2)
	_record("inactive_player_cancels_traversal", player.traversal.mode == "ground")
	player.active = true
	await _reset()
	player.toggle_flight()
	player.position += Vector3(8, 0, 0)
	await _frames(2)
	_record("external_teleport_cancels_traversal", player.traversal.mode == "ground")
	await _reset()
	player.toggle_flight()
	player.traversal.energy = NAN
	await _frames(2)
	_record("nonfinite_energy_fails_closed", player.traversal.mode == "ground" and is_finite(player.traversal.energy) and player.velocity.is_finite())
	await _reset()
	player.toggle_flight()
	player._physics_process(NAN)
	_record("nonfinite_delta_fails_closed", player.traversal.mode == "ground" and player.velocity == Vector3.ZERO)
	await _reset()
	player.toggle_flight()
	player.position = Vector3(39.99, 5, 0)
	player.traversal.after_step()
	Input.action_press("move_right")
	await _frames(40)
	_record("horizontal_feet_bounds_are_enforced", player.position.x <= 40.001, {"x": player.position.x})
	_release()
	await _reset()
	player.toggle_flight()
	_record("weapon_remains_available_in_flight", player.shoot() and player.shots_fired == 1 and player.ammo == 11)
	_record("all_observed_physics_are_finite", finite, {"samples": physics_samples})
	_record("runtime_sources_did_not_change_during_run", initial_hashes == _hashes())
	_finish()

func _reset() -> void:
	_release()
	player.reset()
	player.position = Vector3(0, 0.05, 12)
	player.active = true
	player.configure_traversal([{"id":"north", "position":Vector3(0, 12, -12)}], AREA)
	await _frames(20)
	peak_speed = 0
	min_energy = 100

func _aim(point: Vector3) -> void:
	player.camera.look_at(point, Vector3.UP)

func _box(position: Vector3, size: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	fixture.add_child(body)
	body.position = position
	return body

func _frames(count: int) -> void:
	for index in count:
		await physics_frame
		await process_frame
		if is_instance_valid(player):
			finite = finite and player.position.is_finite() and player.velocity.is_finite()
			peak_speed = maxf(peak_speed, player.velocity.length())
			min_energy = minf(min_energy, player.traversal.energy) if is_finite(player.traversal.energy) else min_energy
			physics_samples += 1

func _release() -> void:
	for action in ACTIONS:
		Input.action_release(action)

func _record(id: String, passed: bool, evidence := {}) -> void:
	checks.append({"id": id, "passed": passed, "evidence": evidence})
	print(("PASS " if passed else "FAIL ") + id)

func _v(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func _hashes() -> Dictionary:
	var result := {}
	for path in ["scripts/player.gd", "scripts/player_traversal.gd", "scripts/traversal_pose.gd", "tests/traversal_cases.gd", "assets/heroes/rama-production.glb", "assets/heroes/rama-hero.glb", "scripts/rama_motion.gd", "assets/animations/rama_hero_motion.tres"]:
		result[path] = FileAccess.get_sha256("res://" + path)
	return result

func _finish() -> void:
	_release()
	var passed := true
	for check in checks:
		passed = passed and check.passed
	var report := {"passed": passed, "checks": checks, "source_hashes": initial_hashes, "godot": Engine.get_version_info(), "physics_ticks_per_second": Engine.physics_ticks_per_second, "scope": "Reconstructed numerical implementation QA, actual collision physics with synthetic inputs; not independent authorship or rendered visual acceptance."}
	var path := "res://tests/evidence/traversal-cases-recovered.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			path = argument.trim_prefix("--report=")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t") + "\n")
	fixture.queue_free()
	await process_frame
	quit(0 if passed else 1)
