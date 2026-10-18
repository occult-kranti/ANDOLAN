extends SceneTree
## Read-only imported-resource/ownership test. Does not compile a GPU shader.
const Finish = preload("res://scripts/environment_surface_finish.gd")
const Lighting = preload("res://scripts/world_lighting.gd")
var checks: Array[Dictionary] = []

func check(ok: bool, label: String) -> void:
	checks.append({"id":label,"passed":ok})
	if not ok: push_error(label)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var city := Node3D.new()
	city.name = "CityArt"
	world.add_child(city)
	var packed := load("res://assets/world/architecture.glb") as PackedScene
	var architecture := packed.instantiate()
	city.add_child(architecture)
	var before: Array[Dictionary] = []
	for node in architecture.find_children("*", "MeshInstance3D", true, false):
		var mesh := node as MeshInstance3D
		for index in range(mesh.mesh.get_surface_count()):
			before.append({"node":mesh,"surface":index,"mesh":mesh.mesh,"material":mesh.mesh.surface_get_material(index),"transform":mesh.transform})
	var report := Finish.configure(world)
	check(report.surfaces > 0 and report.materials == 7, "actual imported seven architecture profiles bound")
	check(report.materials <= Finish.MAX_MATERIALS and report.extra_meshes == 0 and report.extra_lights == 0, "fixed material budget without geometry or lights")
	var unchanged := true
	var transport := true
	var excluded := true
	var names: Dictionary = {}
	var ids: Array[int] = []
	for row in before:
		unchanged = unchanged and row.node.mesh == row.mesh and row.node.transform == row.transform and row.mesh.surface_get_material(row.surface) == row.material
		var original := row.material as StandardMaterial3D
		var current: Material = row.node.get_surface_override_material(row.surface)
		if Finish.PROFILES.has(original.resource_name):
			transport = transport and current is ShaderMaterial
			if current is ShaderMaterial:
				transport = transport and current.get_shader_parameter("base_color") == original.albedo_color
				transport = transport and current.get_shader_parameter("albedo_texture") == original.albedo_texture
				transport = transport and current.get_shader_parameter("normal_texture") == original.normal_texture
				transport = transport and current.get_shader_parameter("normal_depth") == original.normal_scale
				transport = transport and current.get_shader_parameter("uv_scale") == original.uv1_scale and current.get_shader_parameter("uv_offset") == original.uv1_offset
				names[original.resource_name] = true
				ids.append(current.get_instance_id())
		else:
			excluded = excluded and current == null
	check(unchanged, "imported geometry transform and shared material resources unchanged")
	check(transport, "actual original base colors albedo normal maps depth and UV transforms transported")
	check(excluded, "recesses brass and planting excluded")
	var again := Finish.configure(world)
	check(again == report, "repeated configure does not replace bound resources")
	for value in [0.0,0.5,1.0,NAN,-1.0,2.0]: Finish.set_phase(world,value)
	var after: Array[int] = []
	for row in before:
		var material: Material = row.node.get_surface_override_material(row.surface)
		if material != null: after.append(material.get_instance_id())
	check(ids == after, "phase updates allocate no replacement materials")
	var records: Dictionary = world.get_meta(Finish.META)
	check(records.windows.size() == 1 and records.windows[0].get_shader_parameter("night_blend") == 1.0, "one cached window material and clamped night endpoint")
	Finish.set_phase(world,NAN)
	check(records.windows[0].get_shader_parameter("night_blend") == 0.0, "nonfinite phase resets window emission to day")
	var empty := Node3D.new()
	root.add_child(empty)
	check(Finish.configure(empty).is_empty() and empty.get_child_count() == 0, "no CityArt means no courtyard hero or unrelated binding")
	empty.free()
	var guarded := Node3D.new()
	root.add_child(guarded)
	var guarded_city := Node3D.new()
	guarded_city.name = "CityArt"
	guarded.add_child(guarded_city)
	var declined: Array[MeshInstance3D] = []
	for kind in ["override","transparent","roughness_map","vertex_color","next_pass","back_cull","lookalike"]:
		var node := MeshInstance3D.new()
		var mesh := BoxMesh.new()
		var mat := StandardMaterial3D.new()
		mat.resource_name = "Confluence_honey_sandstone"
		mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		match kind:
			"override": node.material_override = StandardMaterial3D.new()
			"transparent": mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
			"roughness_map": mat.roughness_texture = GradientTexture1D.new()
			"vertex_color": mat.vertex_color_use_as_albedo = true
			"next_pass": mat.next_pass = StandardMaterial3D.new()
			"back_cull": mat.cull_mode = BaseMaterial3D.CULL_BACK
			"lookalike": mat.resource_name += "_other"
		mesh.material = mat
		node.mesh = mesh
		guarded_city.add_child(node)
		declined.append(node)
	check(Finish.configure(guarded).surfaces == 0, "unsupported features existing ownership and material lookalikes refused")
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var environment := Environment.new()
	for phase in [0.0,0.5,1.0]:
		Lighting.apply(environment,sun,world,phase)
		check(environment.fog_mode == Environment.FOG_MODE_DEPTH and environment.fog_depth_begin == 42.0 and environment.fog_depth_end >= 205.0, "clear combat near field and bounded depth haze %s" % phase)
		check(is_equal_approx(sun.shadow_bias,0.2) and is_equal_approx(sun.shadow_normal_bias,0.35) and sun.light_angular_distance == 0.0, "accepted shadow offsets preserved %s" % phase)
	var passed := true
	for row in checks: passed = passed and row.passed
	var receipt := {"passed":passed,"checks":checks,"bindings":report,"actual_profile_names":names.keys(),"source_sha256":{},"scope":"Actual cached architecture material/mesh ownership and Godot lighting resource checks. No import, GPU shader compilation, rendered appearance or performance claim."}
	for path in ["res://scripts/environment_surface_finish.gd","res://assets/environment-finish/masonry.gdshader","res://scripts/world_lighting.gd","res://assets/world/architecture.glb"]:
		receipt.source_sha256[path] = FileAccess.get_sha256(path)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(receipt,"\t") + "\n")
	print("G1_ENVIRONMENT_CASES ",JSON.stringify({"passed":passed,"checks":checks.size(),"bindings":report}))
	guarded.free()
	world.free()
	quit(0 if passed else 1)
