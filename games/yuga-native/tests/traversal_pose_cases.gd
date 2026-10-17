extends SceneTree
## Reconstructed actual SkeletonModifier3D checks. This is numerical pose evidence.
const Player = preload("res://scripts/player.gd")
const LegacyPose = preload("res://scripts/traversal_pose.gd")
const LEGACY_HERO := "res://assets/heroes/rama-production.glb"
var legacy_model: Node3D
var legacy_animator: AnimationPlayer
var legacy_clips := {}
var current_samples := 0
var current_finite := true
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
	# Historical additive component checks retain their exact original mesh and
	# expectations. The current player owns a separate complete motion layer.
	legacy_model = load(LEGACY_HERO).instantiate()
	root.add_child(legacy_model)
	legacy_animator = _find_node(legacy_model,"AnimationPlayer")
	pose=LegacyPose.new()
	var legacy_bound: bool=pose.configure(legacy_model,legacy_animator)
	_record("historical_production_hero_and_additive_pose_loaded",legacy_bound)
	if not legacy_bound:
		pose.free(); _finish(); return
	skeleton=pose.get_skeleton()
	for clip in legacy_animator.get_animation_list(): legacy_clips[String(clip).get_file().to_lower()]=clip
	legacy_animator.play(legacy_clips.idle)
	legacy_animator.seek(0,true)
	legacy_animator.advance(0)
	legacy_animator.pause()
	await process_frame
	for index in skeleton.get_bone_count():
		baseline.append({"position":skeleton.get_bone_pose_position(index), "rotation":skeleton.get_bone_pose_rotation(index), "scale":skeleton.get_bone_pose_scale(index)})
	for entry in pose.mapping:
		mapped[entry.bone] = true
	pose.modification_processed.connect(_sample_actual_modifier)
	_record("actual_target_rig_has_164_bones", skeleton.get_bone_count() == 164)
	_record("ten_named_body_bones_mapped", pose.mapping.size() == 10)
	_record("original_nine_clips_preserved", legacy_clips.has_all(["idle","run","jump","fire","cast","cast1","cast2","cast3","defeat"]))
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
	legacy_model.queue_free()
	await process_frame
	await _current_player_checks()
	_record("sources_unchanged_during_pose_checks", source_hashes == _hashes())
	_finish()

func _find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result:=_find_node(child,kind)
		if result: return result
	return null

func _current_player_checks() -> void:
	var current_available:=ResourceLoader.exists("res://assets/heroes/rama-hero.glb")
	_record("current_hero_resource_available",current_available)
	if not current_available: return
	player=Player.new()
	root.add_child(player)
	player.set_physics_process(false)
	player.active=false
	await process_frame
	var motion_bound: bool=is_instance_valid(player.rama_motion) and player.rama_motion.configured
	_record("current_player_binds_complete_rama_motion",motion_bound)
	if not motion_bound: return
	_record("current_player_has_one_exclusive_pose_owner",not is_instance_valid(player.traversal_pose) and not is_instance_valid(player.hero_pose))
	player.rama_motion.modification_processed.connect(_sample_current_modifier)
	for mode in ["flight","grapple"]:
		var before:=current_samples
		for frame in 90:
			player.rama_motion.update_motion(1.0/60.0,{"velocity":Vector3(0,4,12),"grounded":false,"traversal":mode})
			await process_frame
		_record("current_"+mode+"_executes_complete_modifier",current_samples-before>60 and player.rama_motion.locomotion==mode,{"samples":current_samples-before})
		_record("current_"+mode+"_finite_global_bones",current_finite)
	player.rama_motion.cancel("traversal regression reset")
	for frame in 20:
		player.rama_motion.update_motion(1.0/60.0,{"grounded":true})
		await process_frame
	_record("current_traversal_cancel_recovers_idle",player.rama_motion.locomotion=="idle" and player.rama_motion.action_stage=="none" and not player.rama_motion.nocked)
	paused=true
	var before_pause:=current_samples
	await process_frame
	await process_frame
	_record("current_pose_callbacks_stop_while_paused",current_samples==before_pause)
	paused=false
	player.rama_motion.update_motion(1.0/60.0,{"traversal":"flight","grounded":false})
	await process_frame
	await process_frame
	_record("current_pose_callbacks_resume_after_pause",current_samples>before_pause)

func _sample_current_modifier() -> void:
	current_samples+=1
	var current_skeleton: Skeleton3D=player.rama_motion.get_skeleton()
	for index in current_skeleton.get_bone_count():
		var transform:=current_skeleton.get_bone_global_pose(index)
		current_finite=current_finite and transform.is_finite() and absf(transform.basis.determinant())>.000001

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
	for file in ["scripts/player.gd", "scripts/player_traversal.gd", "scripts/traversal_pose.gd", "tests/traversal_pose_cases.gd", "assets/heroes/rama-production.glb", "assets/heroes/rama-hero.glb", "scripts/rama_motion.gd", "assets/animations/rama_hero_motion.tres"]:
		values[file] = FileAccess.get_sha256("res://" + file)
	return values

func _finish() -> void:
	var passed := true
	for check in checks:
		passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"source_hashes":source_hashes,"actual_modifier_samples":samples,"current_rama_modifier_samples":current_samples,"scope":"Historical additive component checks retain the original production mesh. Current player checks independently observe RamaMotion flight/grapple, exclusive pose ownership, reset and actual paused modifier callbacks on the new hero. Numerical checks do not establish visual quality."}
	var path := "res://tests/evidence/traversal-pose-recovered.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			path = argument.trim_prefix("--report=")
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file:
		file.store_string(JSON.stringify(report,"\t") + "\n")
	if is_instance_valid(player): player.queue_free()
	if is_instance_valid(legacy_model): legacy_model.queue_free()
	await process_frame
	quit(0 if passed else 1)
