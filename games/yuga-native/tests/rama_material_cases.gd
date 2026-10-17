extends SceneTree
## Lifecycle/PBR preservation checks. Actual matched appearance is a separate gate.
const Calibration = preload("res://scripts/rama_surface_materials.gd")
var checks: Array[Dictionary] = []
var output := ""

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _texture(color: Color) -> ImageTexture:
	var image := Image.create(2,2,false,Image.FORMAT_RGBA8)
	image.fill(color)
	return ImageTexture.create_from_image(image)

func _material(label: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.resource_name = label
	material.albedo_color = Color(.48,.265,.15,1)
	material.roughness = .53
	material.metallic = .2
	material.metallic_specular = .5
	material.albedo_texture = _texture(Color(.48,.265,.15,1))
	material.roughness_texture = _texture(Color(.2,.53,.8,1))
	material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
	material.metallic_texture = material.roughness_texture
	material.metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_BLUE
	material.normal_enabled = true
	material.normal_texture = _texture(Color(.5,.5,1,1))
	material.normal_scale = .24
	material.ao_enabled = true
	material.ao_texture = material.roughness_texture
	material.uv1_scale = Vector3(2,3,1)
	material.uv1_offset = Vector3(.1,.2,0)
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.render_priority = 3
	return material

func _mesh(material: Material) -> MeshInstance3D:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
	arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
	arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.UP])
	arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,.5),Color.WHITE])
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	mesh.surface_set_material(0,material)
	var instance := MeshInstance3D.new()
	instance.mesh = mesh
	return instance

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func _run() -> void:
	var visual := Node3D.new()
	root.add_child(visual)
	var sources := {}
	var meshes := {}
	var semantic_masks := {}
	for label in Calibration.PROFILES:
		var material := _material(label)
		var instance := _mesh(material)
		visual.add_child(instance)
		sources[label] = material
		meshes[label] = instance
		semantic_masks[label] = instance.mesh.surface_get_arrays(0)[Mesh.ARRAY_COLOR].to_byte_array()
	for label in Calibration.SECONDARY_OWNED:
		var material := _material(label)
		var instance := _mesh(material)
		visual.add_child(instance)
		sources[label] = material
		meshes[label] = instance
		semantic_masks[label] = instance.mesh.surface_get_arrays(0)[Mesh.ARRAY_COLOR].to_byte_array()
	var calibrator = Calibration.new()
	visual.add_child(calibrator)
	check("Null configure does not allocate",not calibrator.configure(null) and calibrator.diagnostics().owned_materials == 0)
	check("All six named non-secondary profiles configure",calibrator.configure(visual) and calibrator.diagnostics().owned_materials == 6,calibrator.diagnostics())
	for label in Calibration.PROFILES:
		var source: StandardMaterial3D = sources[label]
		var target: StandardMaterial3D = meshes[label].get_active_material(0)
		check(label + " has a unique instance material",target != source and target.resource_local_to_scene)
		var maps_preserved := target.albedo_texture == source.albedo_texture and target.normal_texture == source.normal_texture and target.roughness_texture == source.roughness_texture and target.metallic_texture == source.metallic_texture and target.ao_texture == source.ao_texture
		var setup_preserved := target.normal_enabled == source.normal_enabled and target.normal_scale == source.normal_scale and target.roughness_texture_channel == source.roughness_texture_channel and target.metallic_texture_channel == source.metallic_texture_channel and target.uv1_scale == source.uv1_scale and target.uv1_offset == source.uv1_offset and target.texture_filter == source.texture_filter and target.cull_mode == source.cull_mode and target.render_priority == source.render_priority and target.ao_enabled == source.ao_enabled and target.albedo_color == source.albedo_color
		check(label + " keeps original maps UV channels normal and render setup",maps_preserved and setup_preserved)
		var profile_correct := true
		for property in Calibration.PROFILES[label]: profile_correct = profile_correct and is_equal_approx(float(target.get(property)),float(Calibration.PROFILES[label][property]))
		check(label + " receives only its bounded profile",profile_correct and source.metallic_specular == .5 and is_equal_approx(source.metallic,.2) and is_equal_approx(source.roughness,.53))
	for label in Calibration.SECONDARY_OWNED:
		var instance: MeshInstance3D = meshes[label]
		var colors: PackedColorArray = instance.mesh.surface_get_arrays(0)[Mesh.ARRAY_COLOR]
		check(label + " stays under secondary owner with semantic alpha intact",instance.get_active_material(0) == sources[label] and instance.get_surface_override_material(0) == null and colors.to_byte_array() == semantic_masks[label])
	var ids := []
	for label in Calibration.PROFILES: ids.append(meshes[label].get_active_material(0).get_instance_id())
	var stable := true
	for unused in range(100):
		stable = stable and calibrator.configure(visual) and calibrator.diagnostics().owned_materials == 6
		for index in Calibration.PROFILES.size(): stable = stable and meshes[Calibration.PROFILES.keys()[index]].get_active_material(0).get_instance_id() == ids[index]
	check("100 configure calls retain exactly six identical owned resources",stable)
	var other := Node3D.new()
	root.add_child(other)
	var shared := MeshInstance3D.new()
	shared.mesh = meshes["Rama warm skin"].mesh
	other.add_child(shared)
	check("A second hero sharing imported mesh keeps original source",shared.get_active_material(0) == sources["Rama warm skin"] and shared.get_surface_override_material(0) == null)
	check("Configured component refuses rebinding another visual",not calibrator.configure(other))
	var second = Calibration.new()
	other.add_child(second)
	check("Second hero receives its own isolated calibration",second.configure(other) and shared.get_active_material(0) != meshes["Rama warm skin"].get_active_material(0))
	second.restore_materials()
	check("Second hero restore preserves first hero calibration",shared.get_active_material(0) == sources["Rama warm skin"] and meshes["Rama warm skin"].get_active_material(0) != sources["Rama warm skin"])
	var competing = Calibration.new()
	visual.add_child(competing)
	check("A second component cannot stack calibration on an owned surface",not competing.configure(visual) and competing.diagnostics().owned_materials == 0)
	var external := StandardMaterial3D.new()
	meshes["Deep brown iris"].set_surface_override_material(0,external)
	calibrator.restore_materials()
	check("Restore does not erase a later external override",meshes["Deep brown iris"].get_surface_override_material(0) == external)
	meshes["Deep brown iris"].set_surface_override_material(0,null)
	var restored := true
	for label in Calibration.PROFILES: restored = restored and meshes[label].get_active_material(0) == sources[label] and meshes[label].get_surface_override_material(0) == null
	check("Restore returns all original surface resources",restored and not calibrator.configured and calibrator.diagnostics().owned_materials == 0)
	var cycled := true
	for unused in range(100):
		cycled = cycled and calibrator.configure(visual) and calibrator.diagnostics().owned_materials == 6
		calibrator.restore_materials()
		cycled = cycled and calibrator.diagnostics().owned_materials == 0
	check("100 configure restore cycles leave no owned bindings",cycled)
	# Counterexample: a source with nonfinite color invalidates the whole stage.
	sources["Warm sclera"].albedo_color = Color(NAN,.2,.3,1)
	check("Nonfinite matching source rejects the entire transaction",not calibrator.configure(visual) and calibrator.diagnostics().owned_materials == 0)
	var untouched := true
	for label in Calibration.PROFILES: untouched = untouched and meshes[label].get_surface_override_material(0) == null
	check("Rejected transaction leaves earlier valid surfaces untouched",untouched)
	sources["Warm sclera"].albedo_color = Color(.48,.265,.15,1)
	var original_override := _material("Rama warm skin")
	meshes["Rama warm skin"].set_surface_override_material(0,original_override)
	calibrator.configure(visual)
	calibrator.restore_materials()
	check("Pre-existing per-surface override restores by exact identity",meshes["Rama warm skin"].get_surface_override_material(0) == original_override)
	meshes["Rama warm skin"].set_surface_override_material(0,null)
	meshes["Rama warm skin"].material_override = original_override
	check("Global override deliberately wins over surface calibration",calibrator.configure(visual) and meshes["Rama warm skin"].get_surface_override_material(0) == null and meshes["Rama warm skin"].get_active_material(0) == original_override and calibrator.diagnostics().owned_materials == 5)
	calibrator.restore_materials()
	meshes["Rama warm skin"].material_override = null
	calibrator.configure(visual)
	meshes["Natural lips"].free()
	calibrator.restore_materials()
	check("Freed mesh cleanup safely clears owned state",not calibrator.configured and calibrator.diagnostics().owned_materials == 0)
	var passed := true
	for result in checks: passed = passed and result.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"checks":checks,"source_sha256":FileAccess.get_sha256("res://scripts/rama_surface_materials.gd"),"test_sha256":FileAccess.get_sha256("res://tests/rama_material_cases.gd"),"scope":"Native StandardMaterial3D profile values, per-instance isolation, PBR map/feature preservation and lifecycle only. No actual appearance, SSS, corneal refraction, performance or commercial-parity acceptance."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	visual.free()
	other.free()
	quit(0 if passed else 1)
