extends SceneTree
## Reconstructed actual SkeletonModifier3D checks. This is numerical pose evidence.
const Player = preload("res://scripts/player.gd")
var player
var skeleton: Skeleton3D
var pose: SkeletonModifier3D
var baseline: Array[Dictionary] = []
var mapped := {}
var checks: Array[Dictionary] = []
var samples := 0
var phase_samples := 0
var max_angle := 0.0
var moved_bones := {}
var finite := true
var translation_preserved := true
var scale_preserved := true
var outside_rotations_preserved := true
var peak_radians := 0.0
var source_hashes := {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	source_hashes = _hashes()
	player = Player.new()
	root.add_child(player)
	await process_frame
	player.active = false
	_record("production_hero_and_pose_loaded", player.model_ready and is_instance_valid(player.traversal_pose))
	if not player.model_ready or not is_instance_valid(player.traversal_pose):
		_finish()
		return
	pose = player.traversal_pose
	skeleton = pose.get_skeleton()
	player.animator.pause()
	player.animator.seek(0, true)
	player.animator.advance(0)
	for index in skeleton.get_bone_count():
		baseline.append({"position":skeleton.get_bone_pose_position(index), "rotation":skeleton.get_bone_pose_rotation(index), "scale":skeleton.get_bone_pose_scale(index)})
	for entry in pose.mapping:
		mapped[entry.bone] = true
	pose.modification_processed.connect(_sample_actual_modifier)
	_record("actual_target_rig_has_164_bones", skeleton.get_bone_count() == 164)
	_record("ten_named_body_bones_mapped", pose.mapping.size() == 10)
	_record("original_nine_clips_preserved", player.clips.has_all(["idle","run","jump","fire","cast","cast1","cast2","cast3","defeat"]))
	for state in ["flight", "grapple"]:
		phase_samples = 0
		max_angle = 0.0
		moved_bones.clear()
		for index in 180:
			pose.set_state(state, 12.0, 4.0, 1.0 / 60.0)
			await process_frame
		_record(state + "_actual_modifier_executes", phase_samples > 100, {"samples":phase_samples})
		_record(state + "_body_pose_changes", moved_bones.size() == 10 and max_angle > deg_to_rad(20), {"changed_bones": moved_bones.size(),"max_angle":max_angle})
		_record(state + "_angles_stay_bounded", max_angle <= deg_to_rad(42.01))
		_record(state + "_finite_nonsingular_global_bones", finite)
		_record(state + "_translations_and_scales_preserved", translation_preserved and scale_preserved)
		_record(state + "_arms_wrists_and_other_rotations_preserved", outside_rotations_preserved)
	phase_samples = 0
	max_angle = 0
	pose.set_state("flight", 10, 0, 1.0 / 60.0, 1.0)
	await process_frame
	await process_frame
	_record("fire_or_cast_suppresses_additive_pose", pose.weight == 0 and max_angle < 0.0001)
	for index in 30:
		pose.set_state("grapple", 18, 2, 1.0 / 60.0)
		await process_frame
	var before_weight: float = pose.weight
	pose.set_state("ground", 0, 0, 1.0 / 60.0)
	_record("recovery_blends_from_previous_pose", pose.weight > 0 and pose.weight < before_weight and pose.pose_mode == "grapple")
	for index in 60:
		pose.set_state("ground", 0, 0, 1.0 / 60.0)
		await process_frame
	_record("recovery_reaches_zero_overlay", pose.weight == 0)
	pose.set_state("flight", 10, 1, 1.0 / 60.0)
	pose.cancel()
	_record("cancel_clears_overlay_immediately", pose.weight == 0 and pose.phase == 0)
	pose.set_state("flight", NAN, 1, 1.0 / 60.0)
	_record("nonfinite_pose_input_fails_closed", pose.weight == 0)
	pose.set_state("flight", 10, 1, INF)
	_record("invalid_delta_fails_closed", pose.weight == 0)
	_record("all_modifier_samples_are_bounded_finite", finite and peak_radians <= deg_to_rad(42.01), {"samples":samples,"bone_samples":samples * 164,"maximum_angle":peak_radians})
	_record("sources_unchanged_during_pose_checks", source_hashes == _hashes())
	_finish()

func _sample_actual_modifier() -> void:
	samples += 1
	phase_samples += 1
	for index in skeleton.get_bone_count():
		var current := skeleton.get_bone_global_pose(index)
		finite = finite and current.is_finite() and absf(current.basis.determinant()) > 0.000001
		translation_preserved = translation_preserved and skeleton.get_bone_pose_position(index).distance_to(baseline[index].position) < 0.000001
		scale_preserved = scale_preserved and skeleton.get_bone_pose_scale(index).distance_to(baseline[index].scale) < 0.000001
		# Quaternion.angle_to uses acos(dot), which amplifies float rounding near 1.
		# Relative atan2 measures identical orientations near zero without that loss.
		var difference: Quaternion = (baseline[index].rotation.inverse() * skeleton.get_bone_pose_rotation(index)).normalized()
		var angle := 2.0 * atan2(Vector3(difference.x, difference.y, difference.z).length(), absf(difference.w))
		max_angle = maxf(max_angle, angle)
		peak_radians = maxf(peak_radians, angle)
		if angle > 0.001:
			moved_bones[index] = true
		if not mapped.has(index):
			outside_rotations_preserved = outside_rotations_preserved and angle < 0.0001

func _record(id: String, passed: bool, evidence := {}) -> void:
	checks.append({"id":id,"passed":passed,"evidence":evidence})
	print(("PASS " if passed else "FAIL ") + id)

func _hashes() -> Dictionary:
	var values := {}
	for file in ["scripts/player.gd", "scripts/player_traversal.gd", "scripts/traversal_pose.gd", "tests/traversal_pose_cases.gd", "assets/heroes/rama-production.glb"]:
		values[file] = FileAccess.get_sha256("res://" + file)
	return values

func _finish() -> void:
	var passed := true
	for check in checks:
		passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"source_hashes":source_hashes,"actual_modifier_samples":samples,"scope":"Reconstructed numerical QA observes the real Godot SkeletonModifier3D modification_processed signal on the imported 164-bone hero. Finite bounded poses do not establish visual quality or weapon contact."}
	var path := "res://tests/evidence/traversal-pose-recovered.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			path = argument.trim_prefix("--report=")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report,"\t") + "\n")
	player.queue_free()
	await process_frame
	quit(0 if passed else 1)
