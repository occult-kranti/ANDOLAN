extends SceneTree
## Exact existing unit art, arranged geometric fixtures only; no input claim.
const Visibility = preload("res://scripts/friendly_camera_visibility.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var output := ""
var checks: Array = []
func _initialize() -> void: call_deferred("run")
func check(label: String, pass_: bool, details: Variant = null) -> void:
	checks.append({"name": label, "passed": pass_, "details": details})
func meshes(node: Node) -> Array:
	var result: Array = []
	if node is MeshInstance3D: result.append(node)
	for child in node.get_children(): result.append_array(meshes(child))
	return result
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): quit(2); return
	var pins := {}
	var helper_script: Script = Visibility
	while helper_script != null:
		pins[helper_script.resource_path] = FileAccess.get_sha256(helper_script.resource_path)
		helper_script = helper_script.get_base_script()
	for path in ["res://scripts/lane_minion.gd"]:
		pins[path] = FileAccess.get_sha256(path)
	var world := Node3D.new(); root.add_child(world)
	var camera := Camera3D.new(); world.add_child(camera); camera.position = Vector3(0, 1.4, 0); camera.current = true
	var hero := Node3D.new(); world.add_child(hero); hero.position = Vector3(0, 0, -3)
	var midpoint := camera.position.lerp(hero.position + Vector3.UP * 1.25, .5)
	var helper := Visibility.new()
	var serial := 0
	for role in ["spearman", "bow_guard", "commander", "cannon_cart", "royal_chariot"]:
		serial += 1
		var ally := Unit.new(); ally.setup(null, serial, "sun", role, 0); world.add_child(ally)
		var source_meshes := meshes(ally.visual)
		var largest: MeshInstance3D = source_meshes[0]
		for candidate: MeshInstance3D in source_meshes:
			if candidate.get_aabb().get_volume() > largest.get_aabb().get_volume(): largest = candidate
		ally.position += midpoint - largest.to_global(largest.get_aabb().get_center())
		var all_meshes := meshes(ally)
		check(role + " complete existing mesh set fits cache cap", all_meshes.size() <= Visibility.MAX_MESHES_PER_UNIT, {"mesh_count": all_meshes.size()})
		var source_resource: Mesh = largest.mesh
		var initial_position: Vector3 = ally.position
		var initial_health: float = ally.health
		for frame in 20: helper.update(camera, hero, [ally], 1.0 / 60.0)
		check(role + " actual body part occlusion fades bounded per-instance", helper.report().faded_units == 1 and largest.transparency > .8 and largest.transparency < 1, helper.report())
		check(role + " source resources and authority are untouched", largest.mesh == source_resource and ally.position == initial_position and ally.health == initial_health and ally.collision_layer == 0)
		ally.team = "moon"
		helper.update(camera, hero, [ally], 1.0 / 60.0)
		check(role + " changed team restores previous alpha", all_meshes.all(func(mesh): return mesh.transparency == 0) and helper.report().cached_units == 0)
		ally.team = "sun"
		for frame in 20: helper.update(camera, hero, [ally], 1.0 / 60.0)
		helper.update(camera, hero, [ally], .016, false)
		check(role + " disabled presentation restores every part immediately", all_meshes.all(func(mesh): return mesh.transparency == 0) and helper.report().cached_units == 0)
		ally.free()
	var unchanged := true
	for path in pins: unchanged = unchanged and FileAccess.get_sha256(path) == pins[path]
	check("reviewed sources remain frozen", unchanged)
	helper.reset(); world.free()
	var result := {"passed": checks.all(func(row): return row.passed), "checks": checks, "source_pins": pins,
		"scope": "Five existing infantry/vehicle art roles in arranged headless corridor fixtures; per-instance presentation and reset admission only. No ordinary input, raster or physical-GPU performance acceptance."}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(result, "  ") + "\n")
	print(JSON.stringify({"passed": result.passed, "checks": checks.size()}))
	quit(0 if result.passed else 1)
