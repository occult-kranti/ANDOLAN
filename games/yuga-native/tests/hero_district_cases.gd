extends SceneTree
## Construction/geometry contract tests; visual quality still requires rendered review.
const District = preload("res://scripts/hero_district_detail.gd")
var checks: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func _check(label: String, condition: bool) -> void:
	checks.append({"name": label, "passed": condition})

func _run() -> void:
	_check("reject null parent", not District.configure(null).ok)
	var world := Node3D.new()
	root.add_child(world)
	var before := Time.get_ticks_msec()
	var report: Dictionary = District.configure(world)
	var elapsed := Time.get_ticks_msec() - before
	_check("configured", report.ok)
	_check("mesh batches bounded", report.meshes > 0 and report.meshes <= District.MAX_MESHES)
	_check("triangles bounded", report.triangles > 10000 and report.triangles <= District.MAX_TRIANGLES)
	_check("four bounded practical lights and no physics ownership", report.lights == 4 and report.light_budget == 4 and report.collision_objects == 0)
	_check("five open arches", report.counts.arches == 5)
	_check("three ribbed cupolas", report.counts.cupolas == 3)
	_check("six planted urns", report.counts.urns == 6 and report.counts.leaf_blades == 144)
	_check("four pooled emissive diyas", report.counts.diyas == 4)
	_check("three solid terrace courses", report.counts.terrace_courses == 3)
	var district: Node3D = world.get_node(District.ROOT_NAME)
	var instance_id := district.get_instance_id()
	var initial_hash := _geometry_digest(district)
	var child_count := world.get_child_count()
	for i in range(8): District.configure(world)
	_check("repeat configuration keeps owner identity", district.get_instance_id() == instance_id and world.get_child_count() == child_count)
	_check("repeat configuration preserves mesh bytes", _geometry_digest(district) == initial_hash)
	var practicals: Array[OmniLight3D] = []
	for child in district.get_children():
		if child is OmniLight3D: practicals.append(child)
	_check("idempotent four-light construction", practicals.size() == 4 and district.get_child_count() == 12)
	for lamp in practicals:
		_check("light disabled during day " + str(lamp.name), is_zero_approx(lamp.light_energy) and not lamp.visible)
		_check("light shadowless finite range " + str(lamp.name), not lamp.shadow_enabled and is_finite(lamp.omni_range) and lamp.omni_range >= 3.0 and lamp.omni_range <= 3.5)
		_check("warm practical attached to existing diya " + str(lamp.name), lamp.light_color.is_equal_approx(Color("ffb56b")) and is_equal_approx(lamp.position.z, 26.8) and is_equal_approx(lamp.position.y, 1.38) and (is_equal_approx(absf(lamp.position.x), 4.1) or is_equal_approx(absf(lamp.position.x), 12.6)))
	var finite := true
	var normal_lengths := true
	var area_positive := true
	var clear_rectangle := true
	var outside_boundary := true
	var matched_arrays := true
	var recursive_physics := false
	var total_vertices := 0
	for child in district.get_children():
		if not child is MeshInstance3D: continue
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var colors: PackedColorArray = arrays[Mesh.ARRAY_COLOR]
		matched_arrays = matched_arrays and vertices.size() == normals.size() and colors.size() == vertices.size()
		total_vertices += vertices.size()
		for i in range(vertices.size()):
			var p := vertices[i]
			finite = finite and p.is_finite() and normals[i].is_finite()
			normal_lengths = normal_lengths and absf(normals[i].length() - 1.0) < 0.001
			clear_rectangle = clear_rectangle and not (absf(p.x) <= 12.0 and absf(p.z) <= 14.0)
			# South detail is outboard; north detail hugs the original solid piers.
			outside_boundary = outside_boundary and (p.z > 25.25 or (p.z < -20.0 and absf(p.x) > 6.0) or (p.z >= 24.98 and p.y <= -0.005))
		for i in range(0, vertices.size(), 3):
			area_positive = area_positive and (vertices[i + 2] - vertices[i]).cross(vertices[i + 1] - vertices[i]).length_squared() >= 0.00000000001
		var material: StandardMaterial3D = child.material_override
		_check("material present " + str(child.name), material != null and material.roughness >= 0.77)
		if child.name in ["stone", "limestone", "indigo", "brass"]:
			_check("existing source textures " + str(child.name), material.albedo_texture != null and material.roughness_texture != null and material.uv1_world_triplanar)
			# Inspect exact source PNG channels without invoking the runtime
			# resource loader or its export-only warning for this authoring check.
			var rough := Image.new()
			var rough_loaded := rough.load_png_from_buffer(FileAccess.get_file_as_bytes(material.roughness_texture.resource_path)) == OK
			var minimum := 1.0
			var maximum := 0.0
			for y in range(0, rough.get_height(), 16):
				for x in range(0, rough.get_width(), 16):
					var pixel := rough.get_pixel(x, y)
					minimum = minf(minimum, pixel.g)
					maximum = maxf(maximum, pixel.g)
			_check("samples authored varying roughness channel " + str(child.name), rough_loaded and material.roughness_texture_channel == BaseMaterial3D.TEXTURE_CHANNEL_GREEN and maximum - minimum > 0.02 and maximum < 1.0)
	for node in district.find_children("*", "", true, false):
		if node is CollisionObject3D or node is CollisionShape3D: recursive_physics = true
	_check("all emitted coordinates finite", finite)
	_check("unit smooth and face normals", normal_lengths)
	_check("no degenerate emitted triangles", area_positive)
	_check("parallel array counts", matched_arrays)
	_check("clear central rectangle", clear_rectangle)
	_check("new geometry outside boundary or on existing solid piers", outside_boundary)
	_check("no hidden collider descendants", not recursive_physics)
	_check("no per frame scene script", district.get_script() == null)
	_check("vertex count matches diagnostic", total_vertices == int(report.triangles) * 3)
	var terrace_mesh: MeshInstance3D = district.get_node("limestone")
	var terrace_arrays: Array = terrace_mesh.mesh.surface_get_arrays(0)
	var terrace_vertices: PackedVector3Array = terrace_arrays[Mesh.ARRAY_VERTEX]
	var support_points: Array[Vector2] = []
	for side in [-1.0, 1.0]:
		for x_abs in [5.2, 10.4, 15.6]: support_points.append(Vector2(side * x_abs, 28.8))
		for z in [27.0, 30.5]: support_points.append(Vector2(side * 17.4, z))
		support_points.append(Vector2(side * 8.4, 26.6))
		for x_abs in [4.1, 12.6]: support_points.append(Vector2(side * x_abs, 26.8))
		for x_abs in [7.8, 13.0]:
			for step in range(7): support_points.append(Vector2(side * x_abs - 1.8 + step * 0.6, 31.7))
	var all_supported := true
	for point in support_points:
		all_supported = all_supported and _terrace_supports(terrace_vertices, point)
	_check("all 44 column urn diya and balustrade feet supported", support_points.size() == 44 and all_supported)
	_check("continuous surface meets old paving edge", _terrace_supports(terrace_vertices, Vector2(-20, 25.0)) and _terrace_supports(terrace_vertices, Vector2(0, 25.0)) and _terrace_supports(terrace_vertices, Vector2(20, 25.0)))
	_check("top below original paving avoids coplanar overlap", District.TERRACE_TOP_Y < -0.001 and District.TERRACE_TOP_Y > -0.01)
	_check("deck spans all southern furniture", District.TERRACE_FRONT_Z <= 25.0 and District.TERRACE_BACK_Z >= 32.0 and District.TERRACE_HALF_WIDTH >= 19.0)
	_check("no terrace inside clear plaza", not _terrace_supports(terrace_vertices, Vector2(0, 14.0)))
	District.set_phase(world, 1.0)
	var wick: MeshInstance3D = district.get_node("wick")
	var wick_material: StandardMaterial3D = wick.material_override
	_check("night emission applied", is_equal_approx(wick_material.emission_energy_multiplier, 2.4))
	for lamp in practicals:
		_check("bounded night pool " + str(lamp.name), lamp.visible and is_equal_approx(lamp.light_energy, 1.05))
	District.set_phase(world, INF)
	_check("nonfinite phase falls back", District.diagnostics(world).phase == 0.0 and is_equal_approx(wick_material.emission_energy_multiplier, 0.55))
	var nonfinite_light_safe := true
	for lamp in practicals: nonfinite_light_safe = nonfinite_light_safe and is_zero_approx(lamp.light_energy) and not lamp.visible
	_check("nonfinite phase disables every practical", nonfinite_light_safe)
	District.set_phase(world, NAN)
	_check("NaN phase safely falls back", District.diagnostics(world).phase == 0.0)
	District.set_phase(world, 0.5)
	var midpoint_safe := true
	for lamp in practicals: midpoint_safe = midpoint_safe and is_equal_approx(lamp.light_energy, 0.525) and lamp.visible
	_check("fractional phase bounds every practical", midpoint_safe)
	District.set_phase(world, -3.0)
	_check("negative phase clamped", District.diagnostics(world).phase == 0.0)
	District.set_phase(world, 3.0)
	_check("oversized phase clamped", District.diagnostics(world).phase == 1.0)
	var oversized_safe := true
	for lamp in practicals: oversized_safe = oversized_safe and is_equal_approx(lamp.light_energy, 1.05)
	_check("oversized phase cannot overbrighten practicals", oversized_safe)
	for i in range(8):
		District.set_phase(world, float(i % 2))
		District.configure(world)
	_check("phase toggles never allocate more lights", District.diagnostics(world).lights == 4 and district.get_child_count() == 12)
	_check("phase mutation preserves geometry", _geometry_digest(district) == initial_hash)
	var twin := Node3D.new()
	root.add_child(twin)
	District.configure(twin)
	_check("independent builds deterministic", _geometry_digest(twin.get_node(District.ROOT_NAME)) == initial_hash)
	var foreign_world := Node3D.new()
	var foreign := Node3D.new()
	foreign.name = District.ROOT_NAME
	foreign_world.add_child(foreign)
	root.add_child(foreign_world)
	_check("foreign owner refused", not District.configure(foreign_world).ok and foreign_world.get_child_count() == 1)
	District.set_phase(foreign_world, 1.0)
	_check("foreign phase unchanged", not foreign.has_meta("phase"))
	var failures := 0
	for check in checks:
		if not check.passed: failures += 1
	var output := {"passed": failures == 0, "checks": checks, "assertions": checks.size(), "failures": failures, "diagnostics": report, "construction_ms": elapsed, "geometry_sha256": initial_hash, "scope": "Headless construction and geometry contracts; no visual acceptance or physical GPU timing claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			if file != null: file.store_string(JSON.stringify(output, "\t"))
	print(JSON.stringify(output))
	world.free()
	twin.free()
	foreign_world.free()
	quit(0 if failures == 0 else 1)

func _geometry_digest(parent: Node3D) -> String:
	var hash := HashingContext.new()
	hash.start(HashingContext.HASH_SHA256)
	for child in parent.get_children():
		if not child is MeshInstance3D: continue
		hash.update(str(child.name).to_utf8_buffer())
		var arrays: Array = child.mesh.surface_get_arrays(0)
		var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		hash.update(vertices.to_byte_array())
		hash.update(normals.to_byte_array())
	return hash.finish().hex_encode()

func _terrace_supports(vertices: PackedVector3Array, point: Vector2) -> bool:
	for i in range(0, vertices.size(), 3):
		var a := vertices[i]
		var b := vertices[i + 1]
		var c := vertices[i + 2]
		if absf(a.y - District.TERRACE_TOP_Y) > 0.00001 or absf(b.y - District.TERRACE_TOP_Y) > 0.00001 or absf(c.y - District.TERRACE_TOP_Y) > 0.00001: continue
		if Geometry2D.is_point_in_polygon(point, PackedVector2Array([Vector2(a.x, a.z), Vector2(b.x, b.z), Vector2(c.x, c.z)])): return true
	return false
