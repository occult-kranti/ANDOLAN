extends SceneTree
## Native import, rig/clip integrity and source scene gameplay checks.

const Actor = preload("res://scripts/hanuman_actor.gd")
var checks: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func note(id: String, passed: bool, details: Variant = null) -> void:
	checks[id] = {"ok":passed,"details":details.duplicate(true) if details is Dictionary else details}

func _run() -> void:
	var trial = (load("res://scenes/hanuman_trial.tscn") as PackedScene).instantiate()
	root.add_child(trial)
	current_scene = trial
	var ready: Dictionary = trial.report()
	note("trial startup", ready.ready and ready.paused and ready.collidable_court_meshes > 0 and ready.targets.targets.size() == 5,
		{"mesh_colliders":ready.collidable_court_meshes,"status":ready.status})
	var actor = trial.hero
	if actor == null or not actor.ready_for_play:
		_finish()
		return
	note("imported actor is distinct and skinned", actor.skeleton.get_bone_count() >= 164 and actor.has_clip(&"fire"), actor.report())
	var skin := _skin_report(actor)
	note("normalized bounded vertex weights and real bind transforms", skin.errors == 0 and skin.vertices > 1000 and skin.surfaces > 0, skin)
	var socket_count := 0
	for name_ in ["gada_grip", "gada_head", "tail_tip"]:
		var marker := actor.model.find_child(name_, true, false) as Node3D
		if is_instance_valid(marker) and marker.global_position.is_finite() and marker.global_position.distance_to(actor.global_position) > .1:
			socket_count += 1
	note("authored weapon and tail anchors", socket_count == 3, socket_count)
	var source_model := (load(Actor.MODEL_PATH) as PackedScene).instantiate()
	root.add_child(source_model)
	var source_animator: AnimationPlayer = source_model.find_children("*", "AnimationPlayer", true, false)[0]
	var pose_samples := _check_clips(source_model, source_animator)
	note("all eleven imported clips move in place with finite bones", pose_samples.errors == 0 and pose_samples.clips == 11, pose_samples)
	var clips_are_isolated := true
	for clip in [&"idle", &"run"]:
		var path: StringName = actor._clips[clip]
		clips_are_isolated = clips_are_isolated and actor.animator.get_animation(path) != source_animator.get_animation(path)
		clips_are_isolated = clips_are_isolated and actor.animator.get_animation(path).loop_mode == Animation.LOOP_LINEAR
	note("loop adjustments isolated from shared asset", clips_are_isolated)
	source_model.free()
	if not ready.ready:
		_finish()
		return
	# This probe qualifies geometry, timing and collision. The rendered
	# NativeInput run and the dedicated effects suite cover cue playback.
	trial.effects.set_options({"volume":0.0})
	var label: Dictionary = _target_label_scale(trial)
	note("camera limits near target labels and preserves far label size", label.near_pixels <= trial.MAX_TARGET_LABEL_PX + .001 and label.near_scale < label.base * .5 and label.far_scale == label.base and label.position_preserved, label)
	trial._set_paused(false)
	await _ticks(18)
	note("real court floor settles", actor.is_on_floor() and absf(actor.global_position.y) < .15, actor.global_position)
	var spawn: Vector3 = actor.global_position
	Input.action_press("move_forward")
	await _ticks(22)
	Input.action_release("move_forward")
	var walked: Vector3 = actor.global_position
	note("mace rig follows native run", walked.z < spawn.z - .7 and actor.report().motion == "run" and absf(wrapf(actor.model.rotation.y - PI, -PI, PI)) < .05, walked)
	await _ticks(24)
	var swing: Dictionary = trial._request("vajra_gada")
	var before: Vector3 = actor.socket_world(&"wrist.R")
	await _ticks(6)
	var after: Vector3 = actor.socket_world(&"wrist.R")
	note("authored windup moves live wrist socket", swing.accepted and after.is_finite() and after.distance_to(before) > .01, {"before":before,"after":after})
	await _ticks(44)
	var impacts: Array = trial.combat.report().history.filter(func(e: Dictionary): return e.kind == "impact" and e.ability_id == "vajra_gada")
	note("actual strike reaches existing practice receiver", impacts.size() == 1 and trial.army.units[0].health < trial.army.units[0].max_health and actor._action.is_empty(),
		{"impacts":impacts.size(),"target_hp":trial.army.units[0].health})
	trial._set_paused(true)
	var age: float = trial.army.elapsed
	await _ticks(17)
	note("pause freezes simulation and input", is_equal_approx(age, trial.army.elapsed) and trial.paused and not actor.active)
	trial._reset_trial()
	note("reset restores actor, target and ability state", actor.global_position.distance_to(trial.SPAWN) < .001 and actor._action.is_empty() and trial.army.units[0].health == trial.army.units[0].max_health)
	trial._set_paused(false)
	await _ticks(12)
	var start: Vector3 = actor.global_position
	var vault: Dictionary = trial.combat.request_ability("maruti_udayana", start, Vector3.RIGHT, start + Vector3.RIGHT * 4.0)
	var max_height := 0.0
	for frame in range(60):
		await physics_frame
		max_height = maxf(max_height, actor.global_position.y)
	note("actual release sweeps the body through takeoff and landing", vault.accepted and max_height > .4 and actor.global_position.x > start.x + 3.8 and actor.is_on_floor() and not actor._last_vault.get("blocked", true),
		{"height":max_height,"end":actor.global_position,"sweep":actor._last_vault})
	var start_blocked: Vector3 = actor.global_position
	var obstruction := StaticBody3D.new()
	var block := CollisionShape3D.new()
	var extent := BoxShape3D.new()
	extent.size = Vector3(.3, 4, 1.2)
	block.shape = extent
	block.position.y = 2.0
	obstruction.position = start_blocked + Vector3.RIGHT * 1.4
	obstruction.add_child(block)
	trial.add_child(obstruction)
	await _ticks(3)
	var started: bool = actor.accept_move(start_blocked, start_blocked + Vector3.RIGHT * 4.0, .42)
	await _ticks(40)
	note("physical sweep stops on a wall outside the cast oracle", started and actor._last_vault.get("blocked", false) and actor.global_position.x < start_blocked.x + 1.4, actor._last_vault)
	trial._reset_trial()
	trial.queue_free()
	for unused in range(8): await process_frame
	_finish()

func _ticks(count: int) -> void:
	for tick in range(count):
		await physics_frame

func _target_label_scale(trial: Node3D) -> Dictionary:
	var entry: Dictionary = trial._target_labels[0]
	var label: Label3D = entry.label
	var point := label.global_position
	var camera := Camera3D.new()
	trial.add_child(camera)
	camera.position = point + Vector3(0,0,1)
	camera.current = true
	trial._update_target_label_sizes()
	var near_size := label.pixel_size
	var upper := point + Vector3.UP * float(label.font_size) * near_size
	var near_pixels := camera.unproject_position(point).distance_to(camera.unproject_position(upper))
	camera.position = point + Vector3(0,0,22)
	trial._update_target_label_sizes()
	var result := {"near_pixels":near_pixels,"near_scale":near_size,"far_scale":label.pixel_size,"base":entry.size,"position_preserved":point == label.global_position}
	camera.free()
	return result

func _check_clips(model: Node3D, mixer: AnimationPlayer) -> Dictionary:
	var result := {"errors":0,"clips":0,"pose_frames":0,"max_root_travel_m":0.0}
	var rig: Skeleton3D = model.find_children("*", "Skeleton3D", true, false)[0]
	var root_bone := rig.find_bone(&"root")
	for action in mixer.get_animation_list():
		var clip := mixer.get_animation(action)
		result.clips += 1
		mixer.play(action)
		mixer.advance(0.0)
		var initial: Vector3 = rig.get_bone_pose_position(root_bone)
		var poses := {}
		for frame in range(9):
			mixer.seek(float(frame) * clip.length / 8.0, true)
			var travel := initial.distance_to(rig.get_bone_pose_position(root_bone))
			result.max_root_travel_m = maxf(result.max_root_travel_m, travel)
			var sample := []
			for bone in range(rig.get_bone_count()):
				var pose := rig.get_bone_global_pose(bone)
				if not pose.is_finite() or absf(pose.basis.determinant()) < .00001: result.errors += 1
				sample.append(pose)
			poses[hash(sample)] = true
			result.pose_frames += 1
		if poses.size() < 3 or result.max_root_travel_m > .001: result.errors += 1
	return result

func _skin_report(actor: Node3D) -> Dictionary:
	var result := {"errors":0,"surfaces":0,"vertices":0,"triangles":0,"max_influences":0}
	for instance: MeshInstance3D in actor.model.find_children("*", "MeshInstance3D", true, false):
		if instance.mesh == null: continue
		if instance.skin == null or instance.get_node_or_null(instance.skeleton) != actor.skeleton:
			result.errors += 1
			continue
		for index in range(instance.skin.get_bind_count()):
			var name_: StringName = instance.skin.get_bind_name(index)
			var id: int = instance.skin.get_bind_bone(index) if name_.is_empty() else actor.skeleton.find_bone(name_)
			var inverse: Transform3D = instance.skin.get_bind_pose(index)
			if id < 0 or id >= actor.skeleton.get_bone_count() or not inverse.is_finite() or absf(inverse.basis.determinant()) < .00001:
				result.errors += 1
		for index in range(instance.mesh.get_surface_count()):
			result.surfaces += 1
			var arrays: Array = instance.mesh.surface_get_arrays(index)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var weights: Variant = arrays[Mesh.ARRAY_WEIGHTS]
			var binds: Variant = arrays[Mesh.ARRAY_BONES]
			result.vertices += vertices.size()
			var indices: Variant = arrays[Mesh.ARRAY_INDEX]
			if indices != null: result.triangles += int(float(indices.size()) / 3.0)
			if vertices.is_empty() or weights == null or binds == null or weights.size() != binds.size() or weights.size() % vertices.size() != 0:
				result.errors += 1
				continue
			var influence := int(float(weights.size()) / float(vertices.size()))
			result.max_influences = maxi(result.max_influences, influence)
			for vertex in range(vertices.size()):
				var total := 0.0
				for offset in range(influence):
					var slot := vertex * influence + offset
					var fraction := float(weights[slot])
					total += fraction
					if not is_finite(fraction) or fraction < 0.0 or (fraction > 0.0 and (binds[slot] < 0 or binds[slot] >= instance.skin.get_bind_count())):
						result.errors += 1
				if not vertices[vertex].is_finite() or absf(total - 1.0) > .002:
					result.errors += 1
	return result

func _finish() -> void:
	var failed := checks.values().filter(func(row: Dictionary): return not row.ok).size()
	print("HANUMAN_RIG ", JSON.stringify({"model":Actor.MODEL_PATH,"model_sha256":FileAccess.get_sha256(Actor.MODEL_PATH),"checks":checks,"passed":checks.size()-failed,"failed":failed}))
	quit(0 if failed == 0 else 1)
