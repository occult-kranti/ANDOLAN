extends SceneTree
const Art = preload("res://scripts/mythic_environment.gd")
const Lighting = preload("res://scripts/world_lighting.gd")
var checks: Array[Dictionary] = []
var reports: Dictionary = {}
var courtyard: Node3D

func check(ok: bool, label: String, details: Dictionary = {}) -> void:
	checks.append({"id":label,"passed":ok,"details":details})
	if not ok: push_error(label)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for district in ["courtyard", "confluence"]:
		var world := Node3D.new()
		root.add_child(world)
		var art := Art.configure(world, district)
		var report := Art.diagnostics(world)
		reports[district] = report
		check(report.meshes <= Art.MAX_MESHES and report.meshes >= 3, district + " bounded batched draw geometry", report)
		check(report.triangles <= Art.MAX_TRIANGLES and report.triangles > 0, district + " triangle budget", report)
		check(report.lights == 0 and report.collision_objects == 0, district + " adds no light or collision")
		check(Art.configure(world, district) == art and world.get_child_count() == 1, district + " idempotent setup")
		var ids: Array[int] = []
		var finite := true
		var positional_safe := true
		var normals_valid := true
		for mesh in art.get_children():
			normals_valid = normals_valid and _normals_valid(mesh.mesh)
			ids.append(mesh.mesh.get_instance_id())
			ids.append(mesh.material_override.get_instance_id())
			for vertex in mesh.mesh.get_faces():
				finite = finite and vertex.is_finite()
				if district == "courtyard":
					positional_safe = positional_safe and (vertex.y > 3.9 or absf(vertex.x) > 22.0 or vertex.z < -25.3)
				elif vertex.x < -60.0:
					positional_safe = positional_safe and vertex.x < -70.0
		check(finite, district + " finite vertices")
		check(normals_valid, district + " material normals match clockwise front faces")
		check(positional_safe, district + " sculpture outside ground-level aim and playable west boundary")
		for step in range(12000): Art.set_phase(world, float(step % 100) / 99.0)
		var after: Array[int] = []
		for mesh in art.get_children():
			after.append(mesh.mesh.get_instance_id())
			after.append(mesh.material_override.get_instance_id())
		check(ids == after and world.get_child_count() == 1, district + " twelve thousand phase changes allocate no geometry or materials")
		Art.set_phase(world, NAN)
		check(Art.diagnostics(world).phase == 0.0, district + " nonfinite phase fallback")
		Art.set_phase(world, 3.0)
		check(Art.diagnostics(world).phase == 1.0, district + " phase upper bound")
		Art.set_phase(world, -3.0)
		check(Art.diagnostics(world).phase == 0.0, district + " phase lower bound")
		world.free()
	var tower := AABB(Vector3(-83, 0, -2), Vector3(10, 14, 14))
	var loom := AABB(Art.RIVER_LOOM_ORIGIN + Vector3(-1.5, 0, -4.2), Vector3(3, 10, 8.4))
	check(not loom.intersects(tower), "river loom does not overlap existing coastal watchtower art")
	check(Art.configure(null, "courtyard") == null, "invalid world rejected")
	var empty := Node3D.new()
	check(Art.configure(empty, "unknown") == null and empty.get_child_count() == 0, "invalid district rejected")
	empty.free()
	var world := Node3D.new()
	root.add_child(world)
	Art.configure(world, "confluence")
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var env := Environment.new()
	var lighting = Lighting.new()
	lighting.configure(env, sun, world, [])
	var bad_phase := false
	for step in range(101):
		var phase := float(step) / 100.0
		lighting.set_phase(phase)
		bad_phase = bad_phase or not is_finite(sun.light_energy) or sun.light_energy < 0.45 or env.ambient_light_energy < 0.3
		bad_phase = bad_phase or not is_equal_approx(Art.diagnostics(world).phase, phase)
	check(not bad_phase, "all daylight dusk night samples preserve visible fill and synchronize ornament emission")
	check(sun.shadow_normal_bias <= 0.6 and sun.directional_shadow_max_distance == 72.0, "bounded contact shadow settings")
	check(world.get_node("WorldSkyFill").shadow_enabled == false, "fill remains unshadowed")
	world.free()
	courtyard = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(courtyard)
	current_scene = courtyard
	await physics_frame
	await physics_frame
	courtyard.get_tree().paused = false
	courtyard.player.active = false
	courtyard.player.set_physics_process(false)
	await physics_frame
	# Actual imported collision ray results must remain the same when only this
	# scenery is detached. Includes training targets and a grid of floor points.
	var before := _physics_samples()
	var ornaments: Node3D = courtyard.world.get_node(Art.ROOT_NAME)
	courtyard.world.remove_child(ornaments)
	await physics_frame
	var without := _physics_samples()
	courtyard.world.add_child(ornaments)
	await physics_frame
	var restored := _physics_samples()
	check(before == without and before == restored, "actual training floor and target rays unchanged with ornaments attached", {"samples":before.size()})
	var target_hits := 0
	for sample in before.slice(0, 5):
		if str(sample.collider).begins_with("Target"): target_hits += 1
	check(target_hits == 5, "all five actual training target aim rays visible", {"hit_count":target_hits})
	check(courtyard.collidable_meshes > 0 and courtyard.targets.size() == 5, "authored courtyard collision and targets present")
	var old_collision := _collision_count(courtyard.world)
	for phase in [false, true, false]:
		courtyard.night = phase
		courtyard._apply_settings()
	check(old_collision == _collision_count(courtyard.world), "courtyard settings preserve collision count")
	var passed := true
	for entry in checks: passed = passed and entry.passed
	var result := {"passed":passed,"checks":checks,"geometry":reports,"engine":Engine.get_version_info().string,
		"source_sha256":{},"scope":"Headless resource, finite-state, allocation budget and actual training collision-ray comparisons. No rendered appearance, performance or commercial-quality claim."}
	for path in ["res://scripts/mythic_environment.gd","res://scripts/world_lighting.gd","res://scripts/courtyard.gd","res://shaders/production_water.gdshader","res://scripts/world_ground_common.gdshaderinc","res://tests/world_presentation_cases.gd"]:
		result.source_sha256[path] = FileAccess.get_sha256(path)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(result, "\t") + "\n")
			else: passed = false
	print("YUGA_WORLD_PRESENTATION_CASES ", JSON.stringify({"passed":passed,"checks":checks.size(),"geometry":reports}))
	courtyard.free()
	quit(0 if passed else 1)

func _physics_samples() -> Array:
	var points: Array[Array] = []
	for target in courtyard.targets:
		points.append([Vector3(0, 1.35, 12), target.global_position + Vector3(0, 1.3, 0)])
	for x in [-10.0, 0.0, 10.0]:
		for z in [-12.0, 0.0, 12.0]:
			points.append([Vector3(x, 3, z), Vector3(x, -1, z)])
	var samples := []
	for points_pair in points:
		var query := PhysicsRayQueryParameters3D.create(points_pair[0], points_pair[1], 5)
		query.exclude = [courtyard.player.get_rid()]
		var hit := courtyard.get_world_3d().direct_space_state.intersect_ray(query)
		samples.append({"collider":str(hit.collider.name) if not hit.is_empty() else "none",
			"position":str(hit.position) if not hit.is_empty() else "none"})
	return samples

func _collision_count(node: Node) -> int:
	var count := 1 if node is CollisionObject3D else 0
	for child in node.get_children(): count += _collision_count(child)
	return count

func _normals_valid(mesh: ArrayMesh) -> bool:
	for surface in range(mesh.get_surface_count()):
		var arrays := mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		for i in range(0, vertices.size(), 3):
			var outward := (vertices[i + 2] - vertices[i]).cross(vertices[i + 1] - vertices[i]).normalized()
			if normals[i].dot(outward) < 0.99 or normals[i+1].dot(outward) < 0.99 or normals[i+2].dot(outward) < 0.99:
				return false
	return true
