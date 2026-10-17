extends SceneTree
## Synthetic solver probe, deliberately independent of project assets/runtime.

var skeleton: Skeleton3D
var solver: TwoBoneIK3D
var target: Node3D
var sampled: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	skeleton = Skeleton3D.new()
	world.add_child(skeleton)
	for bone_name in ["upper", "lower", "tip"]:
		skeleton.add_bone(bone_name)
	skeleton.set_bone_parent(1, 0)
	skeleton.set_bone_parent(2, 1)
	skeleton.set_bone_rest(0, Transform3D.IDENTITY)
	skeleton.set_bone_rest(1, Transform3D(Basis.IDENTITY, Vector3.UP))
	skeleton.set_bone_rest(2, Transform3D(Basis.IDENTITY, Vector3.UP))
	skeleton.reset_bone_poses()
	target = Node3D.new()
	target.name = "GripTarget"
	world.add_child(target)
	var pole := Node3D.new()
	pole.name = "ElbowPole"
	world.add_child(pole)
	pole.position = Vector3(0, 0, 1)
	solver = TwoBoneIK3D.new()
	skeleton.add_child(solver)
	solver.set_setting_count(1)
	solver.set_root_bone_name(0, "upper")
	solver.set_middle_bone_name(0, "lower")
	solver.set_end_bone_name(0, "tip")
	solver.set_target_node(0, solver.get_path_to(target))
	solver.set_pole_node(0, solver.get_path_to(pole))
	solver.set_pole_direction(0, SkeletonModifier3D.SECONDARY_DIRECTION_PLUS_Z)
	solver.modification_processed.connect(_capture)
	var scenarios := [
		["reachable", Vector3(1, 1, 0), 1.0, true],
		["out_of_plane", Vector3(0.6, 1.2, 0.4), 1.0, true],
		["near_full_extension", Vector3(0, 1.99, 0), 1.0, true],
		["unreachable_no_stretch", Vector3(3, 0, 0), 1.0, false],
		["influence_zero_restored", Vector3(1, 1, 0), 0.0, false],
	]
	var rows: Array[Dictionary] = []
	var all_passed := true
	for scenario in scenarios:
		skeleton.reset_bone_poses()
		target.position = scenario[1]
		solver.influence = scenario[2]
		sampled = {}
		for frame in range(3):
			await process_frame
		if scenario[2] == 0.0:
			_capture()
		var row := sampled.duplicate(true)
		row["name"] = scenario[0]
		row["target"] = _vector(scenario[1])
		row["influence"] = scenario[2]
		var passed: bool = row.get("finite", false)
		for length in row.get("segment_lengths", []):
			passed = passed and absf(length - 1.0) < 0.0001
		if scenario[3]:
			passed = passed and row.get("target_error_m", INF) < 0.001
		if scenario[2] == 0.0:
			passed = passed and row.get("rest_tip_error_m", INF) < 0.001
		row["passed"] = passed
		all_passed = all_passed and passed
		rows.append(row)
	var classes := {}
	for class_id in ["SkeletonModifier3D", "IKModifier3D", "TwoBoneIK3D", "FABRIK3D", "CCDIK3D", "LookAtModifier3D", "AnimationNodeOneShot"]:
		classes[class_id] = ClassDB.class_exists(class_id)
	var report := {"schema": 1, "engine": Engine.get_version_info(),
		"engine_binary_sha256": FileAccess.get_sha256(OS.get_executable_path()),
		"script_sha256": FileAccess.get_sha256(get_script().resource_path),
		"scope": "Headless synthetic three-bone solver fixture; not Rama grip, foot locking, animation quality or rendering proof.",
		"classes": classes, "cases": rows, "passed": all_passed}
	var output := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			output = argument.trim_prefix("--report=")
	if output.is_empty():
		printerr("Pass -- --report=/absolute/output.json")
		quit(2)
		return
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null:
		printerr("Cannot write report: ", output)
		quit(2)
		return
	file.store_string(JSON.stringify(report, "  ") + "\n")
	file.close()
	print(JSON.stringify({"passed": all_passed, "cases": rows.size(), "report": output}))
	quit(0 if all_passed else 1)

func _capture() -> void:
	var upper := skeleton.get_bone_global_pose(0)
	var middle := skeleton.get_bone_global_pose(1)
	var tip := skeleton.get_bone_global_pose(2)
	sampled = {"tip": _vector(tip.origin), "target_error_m": tip.origin.distance_to(target.position),
		"rest_tip_error_m": tip.origin.distance_to(Vector3(0, 2, 0)),
		"segment_lengths": [upper.origin.distance_to(middle.origin), middle.origin.distance_to(tip.origin)],
		"finite": upper.is_finite() and middle.is_finite() and tip.is_finite()}

func _vector(value: Vector3) -> Array[float]:
	return [value.x, value.y, value.z]
