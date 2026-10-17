extends SceneTree
## Independent geometry / actual-scene invariants. Headless evidence is not art acceptance.
const District = preload("res://scripts/hero_district_detail.gd")
var checks: Array[Dictionary] = []
var metrics := {}

func _initialize() -> void:
	call_deferred("_run")

func _check(name: String, passed: bool) -> void:
	checks.append({"name": name, "passed": passed})

func _outward_count(surface: Dictionary, kind: String) -> Dictionary:
	var result := {"outward": 0, "opposed": 0, "tested": 0}
	var vertices: PackedVector3Array = surface.vertices
	var normals: PackedVector3Array = surface.normals
	for i in range(0, vertices.size(), 3):
		var centre := (vertices[i] + vertices[i + 1] + vertices[i + 2]) / 3.0
		var expected := centre
		if kind == "arch":
			if absf(centre.z) < 0.49: continue
			expected = Vector3(0, 0, centre.z)
		elif kind == "south": expected = Vector3.FORWARD
		elif kind == "north": expected = Vector3.BACK
		elif kind == "cylinder": expected = Vector3(centre.x, 0, centre.z)
		result.tested += 1
		if expected.dot(normals[i]) > 0.0: result.outward += 1
		else: result.opposed += 1
	return result

func _primitive_checks() -> void:
	var builder = District.new()
	builder._lintel(Vector3.ZERO, 4.0, 2.0, 2.0, "stone")
	metrics.lintel = _outward_count(builder._surfaces.stone, "lintel")
	_check("closed lintel surfaces face away from interior", metrics.lintel.tested == 32 and metrics.lintel.opposed == 0)
	builder = District.new()
	builder._arch("stone", Vector3.ZERO, 3.0, 0.4, 1.0, 16)
	metrics.arch = _outward_count(builder._surfaces.stone, "arch")
	_check("both arch front and back surfaces face out", metrics.arch.tested == 64 and metrics.arch.opposed == 0)
	for positive in [false, true]:
		builder = District.new()
		builder._rosette(Vector3.ZERO, 1.0, positive)
		var key := "north" if positive else "south"
		metrics[key] = _outward_count(builder._surfaces.limestone, key)
		_check(key + " rosette normal agrees with relief direction", metrics[key].tested == 32 and metrics[key].opposed == 0)
	builder = District.new()
	var profile: Array[Vector2] = [Vector2(1, 0), Vector2(1, 2)]
	builder._lathe("stone", Vector3.ZERO, profile, 16)
	metrics.cylinder = _outward_count(builder._surfaces.stone, "cylinder")
	_check("existing lathe smooth normals retain outward direction", metrics.cylinder.tested == 32 and metrics.cylinder.opposed == 0)

func _physics_snapshot(world: Node3D) -> Array:
	var result := []
	for node in world.find_children("*", "", true, false):
		if node is CollisionObject3D:
			result.append([str(world.get_path_to(node)), node.get_instance_id(), node.global_transform,
				node.collision_layer, node.collision_mask])
		elif node is CollisionShape3D:
			result.append([str(world.get_path_to(node)), node.get_instance_id(), node.global_transform,
				node.disabled, node.shape.get_instance_id() if node.shape else 0])
	return result

func _mesh_digest(district: Node3D) -> String:
	var digest := HashingContext.new()
	digest.start(HashingContext.HASH_SHA256)
	for child in district.get_children():
		if not child is MeshInstance3D: continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		digest.update(arrays[Mesh.ARRAY_VERTEX].to_byte_array())
		digest.update(arrays[Mesh.ARRAY_NORMAL].to_byte_array())
	return digest.finish().hex_encode()

func _geometry_checks(district: Node3D) -> void:
	var finite := true
	var nondegenerate := true
	var front_agreement := true
	var bounds := true
	var no_authority := true
	var opaque_depth := true
	var callbacks := true
	var mismatches := 0
	var count := 0
	for node in district.find_children("*", "", true, false):
		no_authority = no_authority and not (node is CollisionObject3D or node is CollisionShape3D or node is NavigationRegion3D or node is NavigationLink3D)
		callbacks = callbacks and not node.is_processing() and not node.is_physics_processing()
		if not node is MeshInstance3D: continue
		var material: StandardMaterial3D = node.material_override
		opaque_depth = opaque_depth and material != null and material.transparency == BaseMaterial3D.TRANSPARENCY_DISABLED and material.depth_draw_mode == BaseMaterial3D.DEPTH_DRAW_OPAQUE_ONLY and not material.no_depth_test
		var arrays: Array = node.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		for i in range(vertices.size()):
			var p := vertices[i]
			finite = finite and p.is_finite() and normals[i].is_finite() and absf(normals[i].length() - 1.0) < 0.001
			# Independent regions from actual scene: clear training court ends at z=25;
			# northern ornaments adhere to existing piers, southern terrace is below ground.
			bounds = bounds and (p.z > 25.25 or (p.z < -20.0 and absf(p.x) > 6.0) or (p.z >= 24.98 and p.y <= -0.005))
		for i in range(0, vertices.size(), 3):
			count += 1
			var face := (vertices[i + 2] - vertices[i]).cross(vertices[i + 1] - vertices[i])
			nondegenerate = nondegenerate and face.length_squared() >= 0.00000000001
			var mean := normals[i] + normals[i + 1] + normals[i + 2]
			if face.dot(mean) <= 0.0: mismatches += 1
	front_agreement = mismatches == 0
	metrics.actual_triangles = count
	metrics.opposed_face_normal_triangles = mismatches
	_check("all actual vertices and normalized normals finite", finite)
	_check("actual triangle winding agrees with shading normal", front_agreement)
	_check("actual triangles have nonzero area", nondegenerate)
	_check("new geometry stays outboard below paving or on occupied north piers", bounds)
	_check("district cannot add collision or navigation authority", no_authority)
	_check("district materials retain opaque depth testing", opaque_depth)
	_check("static district has no processing callbacks", callbacks)

func _run() -> void:
	_primitive_checks()
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	for node in scene.find_children("*", "", true, false):
		node.set_process(false)
		node.set_physics_process(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	paused = false
	await physics_frame
	var world: Node3D = scene.world
	var district: Node3D = world.get_node(District.ROOT_NAME)
	var original_physics := _physics_snapshot(world)
	var geometry := _mesh_digest(district)
	var district_id := district.get_instance_id()
	_geometry_checks(district)
	_check("real courtyard contains its authored art", scene.environment_ready)
	_check("real courtyard traversal stays disabled", not scene.player.traversal.enabled)
	var south: StaticBody3D = world.get_node("SouthBoundary")
	var shape: BoxShape3D = south.get_child(0).shape
	_check("actual southern movement boundary ends the court at z25", is_equal_approx(south.position.z - shape.size.z / 2.0, 25.0) and shape.size.y == 4.0)
	var query := PhysicsRayQueryParameters3D.create(Vector3(0, 1, 24), Vector3(0, 1, 29), 1)
	var before_hit := world.get_world_3d().direct_space_state.intersect_ray(query)
	_check("actual southern boundary stops ground-level ray", before_hit.get("collider") == south)
	var relief_points: Array[Vector2] = []
	for side in [-1.0, 1.0]:
		for y in [2.85, 7.68]:
			for offset in [-1.65, -0.83, 0.0, 0.83, 1.65]: relief_points.append(Vector2(side * 9.0 + offset, y))
		for offset in [-2.28, 2.28]:
			for step in range(7): relief_points.append(Vector2(side * 9.0 + offset, 3.12 + step * 0.64))
	var backed_reliefs := 0
	for point in relief_points:
		var relief_query := PhysicsRayQueryParameters3D.create(Vector3(point.x, point.y, -19.5), Vector3(point.x, point.y, -21.5), 1)
		var hit := world.get_world_3d().direct_space_state.intersect_ray(relief_query)
		if not hit.is_empty() and world.get_node("AuthoredLankaCourtyard").is_ancestor_of(hit.collider): backed_reliefs += 1
	metrics.northern_reliefs_with_existing_solid_backing = backed_reliefs
	_check("all 48 northern relief centres have actual existing solid pier backing", relief_points.size() == 48 and backed_reliefs == 48)
	var cycle_ok := true
	for i in range(12):
		scene.night = i % 2 == 1
		scene._apply_settings()
		var sky: ProceduralSkyMaterial = scene.world_environment.environment.sky.sky_material
		cycle_ok = cycle_ok and sky.sky_horizon_color == sky.ground_horizon_color and sky.sky_energy_multiplier == sky.ground_energy_multiplier
		cycle_ok = cycle_ok and _physics_snapshot(world) == original_physics and _mesh_digest(district) == geometry
		District.configure(world)
		cycle_ok = cycle_ok and district.get_instance_id() == district_id
	_check("twelve actual settings toggles retain physics mesh identity and seamless sky radiance", cycle_ok)
	world.remove_child(district)
	district.free()
	_check("removing presentation leaves actual physics identical", _physics_snapshot(world) == original_physics)
	District.configure(world)
	district = world.get_node(District.ROOT_NAME)
	_check("rebuild creates a new visual owner", district.get_instance_id() != district_id)
	_check("rebuild retains exact geometry and actual physics", _mesh_digest(district) == geometry and _physics_snapshot(world) == original_physics)
	await physics_frame
	var after_hit := world.get_world_3d().direct_space_state.intersect_ray(query)
	_check("actual raycast unchanged after visual removal and rebuild", after_hit.get("collider") == before_hit.get("collider") and after_hit.get("position") == before_hit.get("position") and after_hit.get("normal") == before_hit.get("normal"))
	var old_atmosphere = scene.hero_atmosphere
	scene.free()
	_check("freed actual scene cannot accept atmosphere writes", not old_atmosphere.set_mode("night"))
	var restoration: Dictionary = old_atmosphere.restore()
	_check("freed-scene atmosphere releases references and reports missing objects", not restoration.passed and not old_atmosphere.diagnostics().bound)
	metrics.geometry_sha256 = geometry
	metrics.actual_collision_records = original_physics.size()
	var failures := 0
	for result in checks:
		if not result.passed: failures += 1
	var report := {"schema": 1, "passed": failures == 0, "assertions": checks.size(), "failures": failures,
		"checks": checks, "metrics": metrics, "engine": Engine.get_version_info().string,
		"sources": {}, "scope": "Independent headless primitive outward-orientation and actual courtyard physics/resource lifecycle; no continuous visual or hardware performance acceptance."}
	for path in ["res://scripts/hero_district_detail.gd", "res://scripts/hero_atmosphere.gd", "res://scripts/courtyard.gd", "res://tests/hero_environment_adversarial_cases.gd"]:
		report.sources[path] = FileAccess.get_sha256(path)
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var file := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report, "\t") + "\n")
			else: failures += 1
	print("YUGA_ENVIRONMENT_ADVERSARIAL ", JSON.stringify({"passed": failures == 0, "assertions": checks.size(), "failures": failures}))
	quit(0 if failures == 0 else 1)
