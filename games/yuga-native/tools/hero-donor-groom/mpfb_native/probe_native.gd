extends SceneTree
## Actual glTF skin data, native production clips, and continuous actions.
const Adapter = preload("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd")
const Contacts = preload("res://tools/hero-family-reuse/motion_skin_contacts.gd")
const Motion = preload("res://scripts/rama_motion.gd")
var output := ""
var base := ""
var hair := ""
var checks: Array = []
var rows: Array = []
var continuous: Array = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--base="): base = arg.trim_prefix("--base=")
		elif arg.begins_with("--hair="): hair = arg.trim_prefix("--hair=")
		elif arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	call_deferred("run")

func check(label: String, value: bool, detail: Variant = null) -> void:
	checks.append({"name": label, "passed": value, "detail": detail})
	print("PASS " if value else "FAIL ", label)

func measure(points: Array, motion: Node) -> Dictionary:
	var positions := Contacts.skin(points, motion)
	var minimum := Vector3(INF, INF, INF)
	var maximum := Vector3(-INF, -INF, -INF)
	var finite := true
	for point in positions:
		finite = finite and point.is_finite()
		minimum = minimum.min(point)
		maximum = maximum.max(point)
	return {"finite": finite, "count": positions.size(), "min": [minimum.x, minimum.y, minimum.z], "max": [maximum.x, maximum.y, maximum.z], "span_m": (maximum - minimum).length()}

func run() -> void:
	if not base.is_absolute_path() or not hair.is_absolute_path() or not output.is_absolute_path() or FileAccess.file_exists(output): quit(2); return
	var model := Adapter.load_glb(base)
	check("explicitly pinned body derivative GLB loads", model != null)
	if not model: finish(); return
	root.add_child(model)
	var motion := Motion.new()
	check("existing production motion configures", motion.configure(model, Adapter.first(model, "AnimationPlayer")))
	motion.active = false
	var attachment := Adapter.attach(model, hair)
	check("hair carrier eligible and rebinds to164canonicalbones", attachment.ok, {"rest_error_m": attachment.get("rest_error_m"), "basis_error": attachment.get("basis_error"), "inverse_bind_source": attachment.get("inverse_bind_source"), "reason": attachment.get("reason")})
	if not attachment.ok: model.free(); finish(); return
	var mesh: MeshInstance3D = attachment.mesh
	var points := Adapter.points(mesh, motion.rig)
	check("2304actual card vertices havehead-onlyunitweights", points.size() == 2304 and points.all(func(p): return p.influences.size() == 1 and p.influences[0].bone == motion.rig.find_bone("head") and absf(p.influences[0].weight - 1) < .000001))
	var arrays := mesh.mesh.surface_get_arrays(0)
	var original_vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var rest_residual := 0.0
	for vertex in points.size():
		var influence: Dictionary = points[vertex].influences[0]
		var rebound: Vector3 = motion.rig.get_bone_global_rest(influence.bone) * influence.point
		rest_residual = maxf(rest_residual, rebound.distance_to(original_vertices[vertex]))
	check("canonicalrestrebindpreserveseverycardposition", rest_residual < .000001, rest_residual)
	check("texture embedded actual native image loaded", (mesh.get_surface_override_material(0) as StandardMaterial3D).albedo_texture.get_width() == 1024)
	check("one shared production23clip library", motion.library.get_animation_list().size() == 23)
	for clip in motion.library.get_animation_list():
		for time in [0.0, .25, .5, .75, 1.0]:
			var pose: Dictionary = motion._sample(clip, time)
			for index in motion.rig.get_bone_count():
				motion.rig.set_bone_pose_position(index, pose.positions[index])
				motion.rig.set_bone_pose_rotation(index, pose.rotations[index])
			for index in motion.rig.get_bone_count(): motion.last_globals[index] = motion.rig.get_bone_global_pose(index)
			var measured := measure(points, motion)
			measured.clip = clip
			measured.normalized_time = time
			rows.append(measured)
	check("all23clips five times actual skin finite bounded", rows.size() == 115 and rows.all(func(r): return r.finite and r.count == 2304 and r.span_m > .2 and r.span_m < .6))
	var state := {"velocity": Vector3.ZERO, "grounded": true, "floor_y": 0.0, "aiming": true, "aim_pitch": .4, "aim_yaw": .3}
	for frame in 300:
		if frame == 30: motion.request_action("kodanda", .18, .22)
		if frame == 65: motion.release_action("kodanda")
		if frame == 90: motion.request_action("piercing_dawn", .18, .22)
		if frame == 120: motion.cancel_action("probe interruption")
		if frame == 150: state.velocity = Vector3(2, 0, -5)
		if frame == 180: state.aim_yaw = -.8
		if frame == 210: motion.request_action("death", .18, .22)
		if frame == 240: motion.request_action("respawn", .18, .22)
		motion.update_motion(1.0 / 60.0, state)
		motion.evaluate_pose()
		var measured := measure(points, motion)
		measured.frame = frame
		measured.action = motion.action
		continuous.append(measured)
	check("300advancingdrawreleaseinterruptturnrunrecoveryframesfinite", continuous.size() == 300 and continuous.all(func(r): return r.finite and r.span_m > .2 and r.span_m < .6))
	check("exact one active production skeleton", Adapter.first(model, "Skeleton3D") == motion.rig and mesh.get_node(mesh.skeleton) == motion.rig)
	model.free()
	finish()

func finish() -> void:
	var passed := checks.all(func(row): return row.passed)
	var report := {"schema_version": 1, "passed": passed, "checks": checks,
		"source_base_sha256": FileAccess.get_sha256(base), "hair_sha256": FileAccess.get_sha256(hair),
		"motion_sha256": FileAccess.get_sha256("res://scripts/rama_motion.gd"),
		"script_sha256": FileAccess.get_sha256(get_script().resource_path),
		"adapter_sha256": FileAccess.get_sha256("res://tools/hero-donor-groom/mpfb_native/native_candidate.gd"),
		"clip_rows": rows, "continuous_rows": continuous, "canonical_promoted": false,
		"scope": "Native rig/clip/finite skin eligibility, not rendered contact, game camera, LOD or hardware acceptance"}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	print("MPFB_NATIVE_PROBE ", passed)
	quit(0 if passed else 1)
