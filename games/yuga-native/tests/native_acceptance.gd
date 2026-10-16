extends SceneTree
## Deterministic native acceptance scenarios, not a recording of human OS input.
## Run after importing the project; see tests/README.md.

const PlayerScript = preload("res://scripts/player.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const TargetScript = preload("res://scripts/target.gd")
const REQUIRED_CLIPS := ["cast", "cast1", "cast2", "cast3", "defeat", "fire", "idle", "jump", "run"]
const ACTIONS := ["move_left", "move_right", "move_forward", "move_back", "jump", "sprint", "fire", "reload", "pulse", "dash"]

var checks: Array[Dictionary] = []
var failures: Array[String] = []
var source_hashes_before: Dictionary = {}
var started_at := Time.get_ticks_msec()
var courtyard: Node
var arena: Node3D
var player: CharacterBody3D

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	source_hashes_before = _source_hashes()
	var scene = load("res://scenes/courtyard.tscn")
	if not scene is PackedScene:
		_record("courtyard_loads", false, {"reason": "Courtyard PackedScene did not load."})
		_finish()
		return
	courtyard = scene.instantiate()
	root.add_child(courtyard)
	await _frames(3)
	var missing_actions: Array[String] = []
	for action in ACTIONS:
		if not InputMap.has_action(action):
			missing_actions.append(action)
	_record("gameplay_input_actions_exist", missing_actions.is_empty(), {"missing": missing_actions})
	if not missing_actions.is_empty():
		_finish()
		return
	_record("courtyard_contract", courtyard.has_method("start_training") and courtyard.has_method("set_paused") and courtyard.has_method("reset_training") and courtyard.has_method("return_to_menu"), {})
	if not failures.is_empty():
		_finish()
		return
	await _check_courtyard_controls()
	courtyard.queue_free()
	await _frames(2)
	await _make_physics_fixture()
	await _check_animations()
	await _check_movement()
	await _check_wall_and_dash()
	await _check_jump()
	await _check_weapon()
	await _check_projectile_and_target()
	_release_actions()
	arena.queue_free()
	await _frames(2)
	_finish()

func _check_courtyard_controls() -> void:
	courtyard.start_training()
	await _frames(10)
	var actor = courtyard.player
	_record("training_starts_with_skinned_rama", actor.active and actor.model_ready and not paused and actor.ammo == actor.MAGAZINE, {"ammo": actor.ammo, "model_ready": actor.model_ready, "targets": courtyard.targets.size()})
	Input.action_press("move_forward")
	Input.action_press("fire")
	await _frames(10)
	courtyard.set_paused(true)
	var paused_position: Vector3 = actor.global_position
	var paused_ammo: int = actor.ammo
	var paused_shots: int = actor.shots_fired
	var paused_cooldown: float = actor.fire_remaining
	await _frames(45)
	_record("pause_freezes_physics_and_weapon", paused and actor.global_position.distance_to(paused_position) < 0.00001 and actor.ammo == paused_ammo and actor.shots_fired == paused_shots and is_equal_approx(actor.fire_remaining, paused_cooldown), {"movement_metres": actor.global_position.distance_to(paused_position), "shots_before": paused_shots, "shots_after": actor.shots_fired, "cooldown_before": paused_cooldown, "cooldown_after": actor.fire_remaining})
	courtyard.set_paused(false)
	await _frames(15)
	_record("resume_clears_stale_held_input", not Input.is_action_pressed("move_forward") and not Input.is_action_pressed("fire") and actor.shots_fired == paused_shots and actor.global_position.distance_to(paused_position) < 0.15, {"movement_metres": actor.global_position.distance_to(paused_position), "shots_before": paused_shots, "shots_after": actor.shots_fired})
	_release_actions()
	# Explicit scenario setup: dirty state through ordinary public combat APIs.
	actor.shoot()
	actor.start_reload()
	courtyard.targets[0].take_hit(3)
	await _frames(2)
	courtyard.reset_training()
	await _frames(2)
	var targets_reset := true
	for target in courtyard.targets:
		targets_reset = targets_reset and target.health == target.max_health and target.reset_remaining == 0 and not target.collision.disabled
	_record("restart_resets_player_targets_and_projectiles", actor.active and not paused and actor.ammo == actor.MAGAZINE and actor.reload_remaining == 0 and actor.shots_fired == 0 and actor.jump_count == 0 and courtyard.hit_count == 0 and courtyard.defeat_count == 0 and courtyard.projectiles.get_child_count() == 0 and targets_reset and actor.global_position.distance_to(Vector3(0, 0.05, 12)) < 0.15, {"ammo": actor.ammo, "projectiles": courtyard.projectiles.get_child_count(), "targets_reset": targets_reset, "hit_count": courtyard.hit_count, "defeat_count": courtyard.defeat_count, "position": _vector(actor.global_position)})
	courtyard.return_to_menu()
	await _frames(3)
	var menu_position: Vector3 = actor.global_position
	Input.action_press("move_forward")
	Input.action_press("fire")
	await _frames(15)
	_record("menu_does_not_simulate_player_input", not actor.active and actor.global_position.distance_to(menu_position) < 0.00001 and actor.shots_fired == 0, {"active": actor.active, "movement_metres": actor.global_position.distance_to(menu_position), "shots": actor.shots_fired})
	_release_actions()
	paused = false

func _make_physics_fixture() -> void:
	arena = Node3D.new()
	arena.name = "ExplicitPhysicsFixture"
	root.add_child(arena)
	_add_box(Vector3(0, -0.5, 0), Vector3(60, 1, 60))
	player = PlayerScript.new()
	arena.add_child(player)
	player.reset()
	player.active = true
	await _frames(12)

func _check_animations() -> void:
	player.active = false
	var skeletons: Array[Skeleton3D] = []
	_collect_skeletons(player.visual, skeletons)
	var bone_count := 0
	for skeleton in skeletons:
		bone_count += skeleton.get_bone_count()
	var missing: Array[String] = []
	for clip in REQUIRED_CLIPS:
		if not player.clips.has(clip):
			missing.append(clip)
	var finite := true
	var samples := 0
	var moved_samples := 0
	var zero_length: Array[String] = []
	var clip_lengths := {}
	for name in REQUIRED_CLIPS:
		if not player.clips.has(name):
			continue
		var clip = player.animator.get_animation(player.clips[name])
		clip_lengths[name] = clip.length
		if clip.length <= 0:
			zero_length.append(name)
		player.animator.play(player.clips[name], 0)
		for ratio in [0.0, 0.25, 0.5, 0.75, 0.99]:
			player.animator.seek(clip.length * ratio, true)
			player.animator.advance(0)
			for skeleton in skeletons:
				for bone in skeleton.get_bone_count():
					var pose: Transform3D = skeleton.get_bone_global_pose(bone)
					finite = finite and pose.is_finite() and absf(pose.basis.determinant()) > 0.000001
					samples += 1
					if not pose.is_equal_approx(skeleton.get_bone_global_rest(bone)):
						moved_samples += 1
	_record("rama_rig_and_nine_animations_are_finite", player.model_ready and skeletons.size() > 0 and bone_count > 0 and missing.is_empty() and zero_length.is_empty() and finite and moved_samples > 0, {"skeleton_count": skeletons.size(), "bone_count": bone_count, "required_clips": REQUIRED_CLIPS, "missing_clips": missing, "zero_length_clips": zero_length, "clip_lengths_seconds": clip_lengths, "bone_transform_samples": samples, "non_rest_samples": moved_samples, "scope": "Five deterministic samples per clip; finite/non-singular transforms do not prove visual quality or every blend."})
	player.active_clip = "" # The scenario sampled AnimationPlayer directly; restore normal ownership.
	player.reset()
	player.active = true
	await _frames(12)

func _check_movement() -> void:
	var start: Vector3 = player.global_position
	Input.action_press("move_forward")
	await _frames(60)
	_release_actions()
	var moved := start.z - player.global_position.z
	_record("forward_movement_uses_real_character_physics", moved > 4.8 and moved < 6.5 and absf(player.global_position.x - start.x) < 0.05 and player.is_on_floor() and player.global_position.is_finite(), {"distance_metres": moved, "position": _vector(player.global_position), "on_floor": player.is_on_floor()})
	player.reset()
	await _frames(12)
	Input.action_press("move_forward")
	Input.action_press("move_right")
	await _frames(45)
	var diagonal_speed := Vector2(player.velocity.x, player.velocity.z).length()
	_release_actions()
	_record("diagonal_movement_is_speed_limited", diagonal_speed > 5.8 and diagonal_speed <= player.SPEED + 0.02, {"horizontal_speed": diagonal_speed, "speed_limit": player.SPEED})

func _check_wall_and_dash() -> void:
	player.reset()
	var wall := _add_box(Vector3(0, 1.5, 6), Vector3(12, 3, 0.4))
	await _frames(12)
	Input.action_press("move_forward")
	await _frames(100)
	var stopped_z: float = player.global_position.z
	Input.action_press("dash")
	await _frames(1)
	Input.action_release("dash")
	await _frames(20)
	_release_actions()
	var after_dash_z: float = player.global_position.z
	wall.queue_free()
	await _frames(2)
	player.reset()
	var target = TargetScript.new()
	target.position = Vector3(0, 0, 6)
	arena.add_child(target)
	await _frames(12)
	Input.action_press("move_forward")
	await _frames(100)
	var target_stop_z: float = player.global_position.z
	target.take_hit(3)
	await _frames(30)
	_release_actions()
	var defeated_target_pass_z: float = player.global_position.z
	_record("world_and_live_targets_block_character_motion", stopped_z > 6.40 and stopped_z < 6.70 and after_dash_z > 6.40 and target_stop_z > 6.40 and target_stop_z < 6.75 and defeated_target_pass_z < 5.5 and player.global_position.is_finite(), {"wall_front_z": 6.2, "capsule_radius": 0.29, "walk_stop_z": stopped_z, "after_dash_z": after_dash_z, "live_target_stop_z": target_stop_z, "after_defeated_target_pass_z": defeated_target_pass_z, "player_collision_mask": player.collision_mask})
	target.queue_free()
	await _frames(2)

func _check_jump() -> void:
	player.reset()
	await _frames(12)
	Input.action_press("jump")
	await _frames(1)
	Input.action_release("jump")
	var peak_y := player.global_position.y
	for frame in 75:
		await _frames(1)
		peak_y = maxf(peak_y, player.global_position.y)
	_record("jump_leaves_floor_and_lands", player.jump_count == 1 and peak_y > 1.1 and peak_y < 1.7 and player.is_on_floor() and absf(player.global_position.y) < 0.1, {"jump_count": player.jump_count, "peak_y": peak_y, "final_y": player.global_position.y, "on_floor": player.is_on_floor()})

func _check_weapon() -> void:
	player.reset()
	await _frames(12)
	var first: bool = player.shoot()
	var immediate_repeat: bool = player.shoot()
	var ammo_after_first: int = player.ammo
	for shot in 11:
		await _frames(16)
		player.shoot()
	var empty_ammo: int = player.ammo
	await _frames(16)
	var empty_shot: bool = player.shoot()
	var reload_started: bool = player.reload_remaining > 0
	var during_reload: bool = player.shoot()
	await _frames(100)
	_record("weapon_cooldown_magazine_and_reload", first and not immediate_repeat and ammo_after_first == 11 and empty_ammo == 0 and not empty_shot and reload_started and not during_reload and player.ammo == player.MAGAZINE and player.shots_fired == 12 and player.reload_remaining == 0, {"first_shot": first, "immediate_repeat": immediate_repeat, "ammo_after_first": ammo_after_first, "empty_ammo": empty_ammo, "empty_shot": empty_shot, "reload_started": reload_started, "shoot_during_reload": during_reload, "final_ammo": player.ammo, "successful_shots": player.shots_fired})

func _check_projectile_and_target() -> void:
	player.active = false
	var target = TargetScript.new()
	target.position = Vector3(0, 0, -8)
	arena.add_child(target)
	await _frames(2)
	for shot in 3:
		var projectile = ProjectileScript.new()
		projectile.position = Vector3(0, 1.65, -5)
		projectile.direction = Vector3.FORWARD
		projectile.speed = 600 # Explicit stress fixture: 10 m travelled per 60 Hz tick.
		arena.add_child(projectile)
		await _frames(3)
	var defeated_health: int = target.health
	var disabled_on_defeat: bool = target.collision.disabled
	var duplicate_hit: bool = target.take_hit()
	await _frames(245)
	_record("swept_projectiles_damage_and_target_respawns", defeated_health == 0 and disabled_on_defeat and not duplicate_hit and target.health == target.max_health and not target.collision.disabled and target.body.visible and target.reset_remaining == 0, {"projectile_speed_metres_per_second": 600, "target_thickness_metres": 0.45, "health_after_three_hits": defeated_health, "collision_disabled_on_defeat": disabled_on_defeat, "duplicate_hit_accepted": duplicate_hit, "health_after_respawn": target.health, "reset_delay_seconds": target.reset_after})
	var blocker := _add_box(Vector3(0, 1.6, -6.5), Vector3(3, 3.2, 0.1))
	await _frames(2)
	var blocked = ProjectileScript.new()
	blocked.position = Vector3(0, 1.65, -5)
	blocked.direction = Vector3.FORWARD
	blocked.speed = 600
	arena.add_child(blocked)
	await _frames(3)
	_record("swept_projectile_respects_world_occlusion", target.health == target.max_health and not is_instance_valid(blocked), {"target_health": target.health, "wall_thickness_metres": 0.1, "projectile_freed": not is_instance_valid(blocked)})
	blocker.queue_free()
	target.queue_free()

func _add_box(position: Vector3, size: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.collision_layer = 1
	body.collision_mask = 0
	body.position = position
	var collider := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = size
	collider.shape = shape
	body.add_child(collider)
	arena.add_child(body)
	return body

func _frames(count: int) -> void:
	for frame in count:
		await physics_frame
		await process_frame

func _collect_skeletons(node: Node, found: Array[Skeleton3D]) -> void:
	if node is Skeleton3D:
		found.append(node)
	for child in node.get_children():
		_collect_skeletons(child, found)

func _release_actions() -> void:
	for action in ACTIONS:
		Input.action_release(action)

func _vector(value: Vector3) -> Array[float]:
	return [value.x, value.y, value.z]

func _record(name: String, passed: bool, observed: Dictionary) -> void:
	checks.append({"name": name, "passed": passed, "observed": observed})
	if not passed:
		failures.append(name)
	print("NATIVE_QA %s %s" % ["PASS" if passed else "FAIL", name])

func _finish() -> void:
	paused = false
	_release_actions()
	var source_hashes_after := _source_hashes()
	_record("source_files_unchanged_during_scenarios", source_hashes_before == source_hashes_after, {"files": source_hashes_after.size()})
	var output := "res://tests/evidence/native-acceptance.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			output = argument.trim_prefix("--report=")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output.get_base_dir()))
	var report := {"schema_version": 1, "kind": "native-scripted-scenario-acceptance", "engine": Engine.get_version_info(), "renderer": "headless dummy; no visual or GPU performance evidence", "input_method": "Godot Input.action_press/action_release plus explicitly labelled public-API/isolated-world fixtures; not physical OS input", "timing": "60 Hz physics; runner --fixed-fps 60; no time scale change", "elapsed_wall_ms": Time.get_ticks_msec() - started_at, "passed": failures.is_empty(), "checks": checks, "failures": failures, "source_sha256": source_hashes_after, "limits": ["One Rama rig; nine clips sampled at five times each, not all possible blends or all heroes.", "Original offline courtyard foundation, not reconstruction or fidelity validation of commercial games.", "Rendering quality, camera feel and native hardware input require separate visible-window evidence."]}
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report, "\t") + "\n")
	else:
		push_error("Could not write report: " + output)
		quit(2)
		return
	print("NATIVE_QA_SUMMARY %s/%s checks passed; %s" % [checks.size() - failures.size(), checks.size(), output])
	quit(0 if failures.is_empty() else 1)

func _source_hashes() -> Dictionary:
	var hashes := {}
	for path in ["project.godot", "scenes/courtyard.tscn", "scripts/courtyard.gd", "scripts/player.gd", "scripts/projectile.gd", "scripts/target.gd", "assets/heroes/rama.glb", "assets/environment/lanka_courtyard.glb", "tests/native_acceptance.gd"]:
		hashes[path] = FileAccess.get_sha256("res://" + path)
	return hashes
