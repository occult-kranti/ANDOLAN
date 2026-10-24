extends SceneTree
## Isolated hair-only derivative: actual shared runtime rig/clip/skin eligibility.
## Uses GLTFDocument for BOTH ancestors, never writes/imports a canonical asset.
const SOURCE := "res://assets/heroes/rama-hero.glb"
const SOURCE_SHA := "db4b2ec7a14cad72299d462c1265374f615d5e9d8b8852c4669e1f960f78245e"
const CANDIDATE_SHA := "85c16967bdec0eeb6cf4c5b331fe07d236df114ebf3730937d97300e4dda0777"
const MOTION_PATH := "res://scripts/rama_motion.gd"
const MOTION_SHA := "6261a692308e84863dbac4ff049fb7855cc8c5ebf70d8ec844b1dfb2225e53c1"
const LIBRARY := "res://assets/animations/rama_hero_motion.tres"
const LIBRARY_SHA := "1d997aed90f71dae3d0f9e38d02485dbf202d8425e61c77d8de7108fa63a9ae8"
const Contacts = preload("res://tools/hero-family-reuse/motion_skin_contacts.gd")
var candidate := ""
var output := ""
var checks: Array[Dictionary] = []
var models: Array[Node] = []
var motions: Array[Node] = []
var surfaces: Array[Array] = []
var contact_sets: Array[Dictionary] = []
var source_before := {}
var clip_rows: Array[Dictionary] = []
var continuous_rows: Array[Dictionary] = []
var event_rows: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--candidate="): candidate = arg.trim_prefix("--candidate=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("run")

func check(name_: String, passed: bool, detail: Variant = null) -> void:
	checks.append({"name": name_, "passed": passed, "detail": detail})
	print("PASS " if passed else "FAIL ", name_)

func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_node(child, kind)
		if found: return found
	return null

func pins() -> Dictionary:
	var result := {}
	for path in [SOURCE, candidate, MOTION_PATH, LIBRARY, get_script().resource_path, "res://tools/hero-family-reuse/motion_skin_contacts.gd"]:
		result[path] = FileAccess.get_sha256(path)
	return result

func configure(path: String) -> bool:
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(path, state) != OK: return false
	var model := document.generate_scene(state)
	if not model: return false
	root.add_child(model)
	var motion = load(MOTION_PATH).new()
	if not motion.configure(model, find_node(model, "AnimationPlayer")):
		model.free()
		return false
	motion.active = false
	models.append(model)
	motions.append(motion)
	contact_sets.append(Contacts.collect(model, motion.rig))
	var data: Array = []
	collect_surfaces(model, motion.rig, model, data)
	surfaces.append(data)
	return true

func collect_surfaces(node: Node, rig: Skeleton3D, model: Node, result: Array) -> void:
	if node is MeshInstance3D and node.skin:
		var binds: Array = []
		for index in node.skin.get_bind_count():
			var name_ := str(node.skin.get_bind_name(index))
			var bone: int = rig.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone": bone, "inverse": node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array = node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
			var points: Array = []
			var stride: int = joints.size() / vertices.size()
			for vi in vertices.size():
				var influences: Array = []
				for slot in stride:
					var weight: float = weights[vi * stride + slot]
					if weight <= 0: continue
					var bind: Dictionary = binds[joints[vi * stride + slot]]
					influences.append({"bone": bind.bone, "point": bind.inverse * vertices[vi], "weight": weight})
				points.append({"influences": influences})
			var material: Material = node.mesh.surface_get_material(surface)
			result.append({"path": str(model.get_path_to(node)), "surface": surface, "material": material.resource_name if material else "", "hair": material != null and material.resource_name == "Swept black hair", "points": points, "transform": rig.global_transform.affine_inverse() * node.global_transform})
	for child in node.get_children(): collect_surfaces(child, rig, model, result)

func globals_finite(motion: Node) -> bool:
	for transform in motion.last_globals:
		if not transform.origin.is_finite() or not transform.basis.is_finite(): return false
	return true

func sockets_difference() -> float:
	var maximum := 0.0
	for name_ in ["bow_grip", "draw_hand", "string_nock", "arrow_muzzle", "head"]:
		maximum = maxf(maximum, motions[0].socket_global(name_).origin.distance_to(motions[1].socket_global(name_).origin))
	return maximum

func compare_skin() -> Dictionary:
	var protected_max := 0.0
	var hair_max := 0.0
	var finite := true
	var protected_count := 0
	var hair_count := 0
	for surface in surfaces[0].size():
		var left: Dictionary = surfaces[0][surface]
		var right: Dictionary = surfaces[1][surface]
		var before := Contacts.skin(left.points, motions[0])
		var after := Contacts.skin(right.points, motions[1])
		for vi in before.size():
			finite = finite and before[vi].is_finite() and after[vi].is_finite()
			var difference := before[vi].distance_to(after[vi])
			if left.hair: hair_max = maxf(hair_max, difference); hair_count += 1
			else: protected_max = maxf(protected_max, difference); protected_count += 1
	return {"protected_skin_max_delta_m": protected_max, "hair_skin_max_delta_m": hair_max, "protected_vertices": protected_count, "hair_vertices": hair_count, "finite": finite}

func tick_sequence(label: String, count: int, state: Dictionary) -> void:
	for frame in count:
		for motion in motions:
			motion.update_motion(1.0 / 60.0, state)
			motion.evaluate_pose()
		var socket_delta := sockets_difference()
		var left_string := Contacts.skin(contact_sets[0].string, motions[0])
		var right_string := Contacts.skin(contact_sets[1].string, motions[1])
		var left_fingers := Contacts.skin(contact_sets[0].draw_fingers, motions[0])
		var right_fingers := Contacts.skin(contact_sets[1].draw_fingers, motions[1])
		var bone_delta := 0.0
		var transforms_equal := true
		for index in motions[0].rig.get_bone_count():
			bone_delta = maxf(bone_delta, motions[0].last_globals[index].origin.distance_to(motions[1].last_globals[index].origin))
			transforms_equal = transforms_equal and motions[0].last_globals[index] == motions[1].last_globals[index]
		continuous_rows.append({"segment": label, "frame": frame, "action": motions[0].action, "stage": motions[0].action_stage, "release_count": motions[0].release_count, "same_authority_state": motions[0].action == motions[1].action and motions[0].action_stage == motions[1].action_stage and motions[0].release_count == motions[1].release_count, "finite": globals_finite(motions[0]) and globals_finite(motions[1]), "all164_bone_transforms_exact": transforms_equal, "bone_position_max_delta_m": bone_delta, "socket_max_delta_m": socket_delta, "actual_string_max_delta_m": Contacts.max_step(left_string, right_string).maximum_m, "actual_draw_finger_max_delta_m": Contacts.max_step(left_fingers, right_fingers).maximum_m})

func event(kind: String, action: String) -> void:
	var results: Array = []
	for motion in motions:
		if kind == "request": results.append(motion.request_action(action, .18, .22))
		elif kind == "release": results.append(motion.release_action(action))
		else: motion.cancel_action(action); results.append(true)
	event_rows.append({"kind": kind, "action": action, "both_accepted": results == [true, true]})

func run() -> void:
	if not candidate.is_absolute_path() or not output.is_absolute_path() or FileAccess.file_exists(output):
		printerr("Use absolute isolated candidate and fresh output")
		quit(2); return
	source_before = pins()
	check("exact canonical ancestor", source_before[SOURCE] == SOURCE_SHA)
	check("exact isolated hair derivative", source_before[candidate] == CANDIDATE_SHA)
	check("unchanged accepted motion and runtime library", source_before[MOTION_PATH] == MOTION_SHA and source_before[LIBRARY] == LIBRARY_SHA)
	if not checks.all(func(row): return row.passed): finish(); return
	check("both same-method runtime imports configure", configure(ProjectSettings.globalize_path(SOURCE)) and configure(candidate))
	if motions.size() != 2: finish(); return
	var surface_contract := surfaces[0].size() == surfaces[1].size()
	for index in mini(surfaces[0].size(), surfaces[1].size()):
		var left: Dictionary = surfaces[0][index]
		var right: Dictionary = surfaces[1][index]
		surface_contract = surface_contract and left.path == right.path and left.surface == right.surface and left.material == right.material and left.points.size() == right.points.size() and left.transform == right.transform and left.transform.is_equal_approx(Transform3D.IDENTITY)
	check("ordered surfaces and identity rig-space transforms", surface_contract)
	check("both inherit the shared23clip library", motions[0].library == motions[1].library and motions[0].library.get_animation_list().size() == 23)
	if not surface_contract: finish(); return
	var aimed := {"velocity": Vector3.ZERO, "grounded": true, "floor_y": 0.0, "aiming": true, "aim_pitch": .45, "aim_yaw": .3}
	tick_sequence("primed_aim", 60, aimed)
	event("request", "kodanda"); tick_sequence("draw_hold", 24, aimed)
	event("release", "kodanda"); tick_sequence("release", 5, aimed)
	event("request", "hit"); tick_sequence("hit_interrupt", 15, aimed)
	event("release", "hit"); tick_sequence("hit_recovery", 30, aimed)
	event("request", "death"); tick_sequence("death_windup", 24, aimed)
	event("release", "death"); tick_sequence("death_hold", 24, aimed)
	event("request", "respawn"); tick_sequence("respawn", 18, aimed)
	event("release", "respawn"); tick_sequence("respawn_recovery", 30, aimed)
	event("request", "piercing_dawn"); tick_sequence("piercing_draw", 24, aimed)
	event("cancel", "isolated_hair_probe"); tick_sequence("cancel", 24, aimed)
	check("all continuous requests and releases accepted identically", event_rows.all(func(row): return row.both_accepted))
	check("all advancing skin contacts and sockets unchanged", continuous_rows.all(func(row): return row.same_authority_state and row.finite and row.all164_bone_transforms_exact and row.bone_position_max_delta_m < .000001 and row.socket_max_delta_m < .000001 and row.actual_string_max_delta_m < .000001 and row.actual_draw_finger_max_delta_m < .000001), continuous_rows.size())
	for clip in motions[0].library.get_animation_list():
		for time in [0.0, 0.5, 1.0]:
			for motion in motions:
				var pose: Dictionary = motion._sample(clip, time)
				for index in motion.rig.get_bone_count():
					motion.rig.set_bone_pose_position(index, pose.positions[index])
					motion.rig.set_bone_pose_rotation(index, pose.rotations[index])
				for index in motion.rig.get_bone_count(): motion.last_globals[index] = motion.rig.get_bone_global_pose(index)
			var row := compare_skin()
			row.clip = clip; row.normalized_time = time; row.socket_max_delta_m = sockets_difference()
			row.finite = row.finite and globals_finite(motions[0]) and globals_finite(motions[1])
			clip_rows.append(row)
		print("HAIR_RUNTIME_CLIP ", clip)
	check("all23runtimeclips sampled at0 half and1", clip_rows.size() == 69)
	check("all protected body weapon skin and sockets unchanged", clip_rows.all(func(row): return row.finite and row.protected_vertices > 0 and row.protected_skin_max_delta_m < .000001 and row.socket_max_delta_m < .000001))
	check("all sampled hair finite and within original3cm editor budget", clip_rows.all(func(row): return row.hair_vertices > 0 and row.hair_skin_max_delta_m > .01 and row.hair_skin_max_delta_m < .03))
	finish()

func finish() -> void:
	check("all exact inputs remain unchanged", source_before == pins())
	var passed := checks.all(func(row): return row.passed)
	var report := {"schema_version": 1, "passed": passed, "checks": checks, "check_count": checks.size(), "sources": source_before, "sources_after": pins(), "same_import_method": "GLTFDocument.append_from_file/generate_scene for both ancestors", "sampling": "23 shared production clips at normalized0/.5/1 plus advancing60Hz action/interrupt/respawn sequence", "continuous_rows": continuous_rows, "events": event_rows, "clip_rows": clip_rows, "canonical_promoted": false, "scope": "Isolated hair derivative native rig/skin/clip/contact eligibility only. Same-body deltas, finite posed hair and original editor displacement budget; no visual hair/body collision, textured seam, LOD, gameplay or finished-art acceptance."}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	print("HAIR_RUNTIME_ELIGIBILITY_COMPLETE ", passed, " checks=", checks.size())
	for model in models: model.free()
	quit(0 if passed else 1)
