extends SceneTree
## Material ownership and preserved-data checks; visible quality is a render gate.
const Finish = preload("res://scripts/rama_surface_finish.gd")
var checks: Array[Dictionary] = []
var output := ""
var use_resources := false

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func _texture() -> ImageTexture:
	var image := Image.create(4,4,false,Image.FORMAT_RGBA8)
	image.fill(Color(.29,.58,.81,1))
	return ImageTexture.create_from_image(image)

func _maps() -> Dictionary:
	var result := {}
	for key in Finish.MAP_PATHS: result[key] = _texture()
	return result

func _standard(label: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.resource_name = label
	material.albedo_color = Color(.42,.25,.13,1)
	material.albedo_texture = _texture()
	material.roughness_texture = _texture()
	material.roughness_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_GREEN
	material.metallic_texture = material.roughness_texture
	material.metallic_texture_channel = BaseMaterial3D.TEXTURE_CHANNEL_BLUE
	material.roughness = .53
	material.metallic = .2
	material.metallic_specular = .5
	material.normal_enabled = true
	material.normal_scale = .24
	material.normal_texture = _texture()
	material.ao_enabled = true
	material.ao_texture = material.roughness_texture
	material.uv1_scale = Vector3(2,3,1)
	material.uv1_offset = Vector3(.12,.07,0)
	material.uv2_scale = Vector3(3,2,1)
	material.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.render_priority = 3
	return material

func _shader(label: String) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.resource_name = label + " · bounded secondary"
	material.shader = Finish.SECONDARY_SHADER
	material.render_priority = 5
	material.set_shader_parameter("base_color",Color(.13,.22,.43,1))
	material.set_shader_parameter("base_texture",_texture())
	material.set_shader_parameter("use_base_texture",true)
	material.set_shader_parameter("roughness_value",.53)
	material.set_shader_parameter("rough_texture",_texture())
	material.set_shader_parameter("use_rough_texture",true)
	material.set_shader_parameter("rough_channel",Vector4(0,1,0,0))
	material.set_shader_parameter("metallic_value",.2)
	material.set_shader_parameter("metal_texture",_texture())
	material.set_shader_parameter("use_metal_texture",true)
	material.set_shader_parameter("metal_channel",Vector4(0,0,1,0))
	material.set_shader_parameter("normal_texture",_texture())
	material.set_shader_parameter("normal_strength",.24)
	material.set_shader_parameter("use_normal_texture",true)
	material.set_shader_parameter("specular_value",.5)
	material.set_shader_parameter("secondary_offset",Vector3(.01,.02,.03))
	return material

func _mesh(material: Material) -> MeshInstance3D:
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3.ZERO,Vector3.RIGHT,Vector3.UP])
	arrays[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.FORWARD,Vector3.FORWARD,Vector3.FORWARD])
	arrays[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2.ZERO,Vector2.RIGHT,Vector2.UP])
	arrays[Mesh.ARRAY_COLOR] = PackedColorArray([Color(1,1,1,0),Color(1,1,1,.5),Color.WHITE])
	var array_mesh := ArrayMesh.new()
	array_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	array_mesh.surface_set_material(0,material)
	var instance := MeshInstance3D.new()
	instance.mesh = array_mesh
	return instance

func _stored(resource: Resource) -> Dictionary:
	var result := {}
	for property in resource.get_property_list():
		if int(property.usage) & PROPERTY_USAGE_STORAGE: result[property.name] = resource.get(property.name)
	return result

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
		if argument == "--resources": use_resources = true
	call_deferred("_run")

func _run() -> void:
	var visual := Node3D.new()
	root.add_child(visual)
	var finish = Finish.new()
	visual.add_child(finish)
	var supplied := _maps()
	var standards := {}
	var secondaries := {}
	var mesh_by_label := {}
	var source_records := {}
	var arrays_before := {}
	for label in Finish.STANDARD_PROFILES:
		var material := _standard(label)
		if label != "Ivory silk" and label != "Pupil": material.resource_name += " · Rama calibration v1"
		standards[label] = material
		source_records[label] = _stored(material)
		mesh_by_label[label] = []
		for index in 2:
			var mesh := _mesh(material)
			visual.add_child(mesh)
			mesh_by_label[label].append(mesh)
			arrays_before[mesh.get_instance_id()] = mesh.mesh.surface_get_arrays(0)
	for label in Finish.SECONDARY_PROFILES:
		var material := _shader(label)
		secondaries[label] = material
		source_records[label] = _stored(material)
		mesh_by_label[label] = []
		for index in 2:
			var mesh := _mesh(material)
			visual.add_child(mesh)
			mesh_by_label[label].append(mesh)
			arrays_before[mesh.get_instance_id()] = mesh.mesh.surface_get_arrays(0)
	var foreign := _mesh(_standard("Unrelated NPC metal"))
	visual.add_child(foreign)
	var global := _mesh(standards["Rama warm skin"])
	global.material_override = _standard("Intentional global override")
	visual.add_child(global)
	check("Only a live tree visual can configure",not finish.configure(null,supplied))
	var detached_finish = Finish.new()
	check("Detached owner cannot configure and leave permanent overrides",not detached_finish.configure(visual,supplied) and mesh_by_label["Ivory silk"][0].get_surface_override_material(0) == null)
	detached_finish.free()
	var bad_maps := supplied.duplicate()
	bad_maps.skin = 4
	check("Invalid supplied texture rejects before any material writes",not finish.configure(visual,bad_maps) and mesh_by_label["Ivory silk"][0].get_surface_override_material(0) == null)
	check("Configure all recognized PBR surfaces",finish.configure(visual,supplied))
	check("Shared near and LOD source deduplicates to 8 standard and 4 secondary resources",finish.report().standard_materials == 8 and finish.report().secondary_materials == 4 and finish.report().surface_slots == 24)
	check("Unrecognized and global-override appearances remain untouched",foreign.get_surface_override_material(0) == null and global.get_surface_override_material(0) == null)
	for label in standards:
		var target: StandardMaterial3D = mesh_by_label[label][0].get_active_material(0)
		var source: StandardMaterial3D = standards[label]
		var profile: Dictionary = Finish.STANDARD_PROFILES[label]
		var allowed: Array = profile.values.keys() + ["resource_name","resource_local_to_scene"]
		if profile.has("map"): allowed += ["roughness","roughness_texture","roughness_texture_channel"]
		var preserved := true
		for key in source_records[label]:
			if key not in allowed: preserved = preserved and target.get(key) == source_records[label][key]
		check(label + " preserves every unrelated stored property and original source",preserved and _stored(source) == source_records[label])
		var tuned := true
		for key in profile.values:
			var expected: Variant = profile.values[key]
			tuned = tuned and (is_equal_approx(float(target.get(key)),expected) if expected is float else target.get(key) == expected)
		if profile.has("map"): tuned = tuned and target.roughness_texture == supplied[profile.map] and target.roughness_texture_channel == BaseMaterial3D.TEXTURE_CHANNEL_RED
		check(label + " applies only declared finish and shares LOD reference",tuned and target != source and target == mesh_by_label[label][1].get_active_material(0) and target.resource_local_to_scene)
	for label in secondaries:
		var material: ShaderMaterial = secondaries[label]
		var profile: Dictionary = Finish.SECONDARY_PROFILES[label]
		var changed := ["shader_parameter/roughness_value","shader_parameter/rough_texture","shader_parameter/rough_channel","shader_parameter/use_rough_texture","metadata/"+String(Finish.OWNER_META)]
		for key in profile.values: changed.append("shader_parameter/"+key)
		var preserved := true
		for key in source_records[label]:
			if key not in changed: preserved = preserved and material.get(key) == source_records[label][key]
		check(label + " keeps secondary material identity albedo normal UV and offset",preserved and mesh_by_label[label][0].get_active_material(0) == material and material.shader == Finish.SECONDARY_SHADER)
		check(label + " binds bounded roughness without touching metallic texture",material.get_shader_parameter("rough_texture") == supplied[profile.map] and material.get_shader_parameter("rough_channel") == Vector4(1,0,0,0) and material.get_shader_parameter("metal_channel") == Vector4(0,0,1,0))
	var arrays_same := true
	for label in mesh_by_label:
		for mesh in mesh_by_label[label]: arrays_same = arrays_same and mesh.mesh.surface_get_arrays(0) == arrays_before[mesh.get_instance_id()]
	check("All positions normals UVs and semantic alpha masks remain exact",arrays_same)
	var ids := []
	for label in standards: ids.append(mesh_by_label[label][0].get_active_material(0).get_instance_id())
	var stable := true
	for unused in 100:
		stable = stable and finish.configure(visual,supplied)
		for index in standards.size(): stable = stable and mesh_by_label[standards.keys()[index]][0].get_active_material(0).get_instance_id() == ids[index]
	check("100 configure calls retain material identities without writes",stable)
	var one_lod_override := _standard("external LOD appearance")
	mesh_by_label["Ivory silk"][1].set_surface_override_material(0,one_lod_override)
	check("Replacing only one shared LOD slot is detected",not finish.configure(visual,supplied))
	mesh_by_label["Ivory silk"][1].set_surface_override_material(0,mesh_by_label["Ivory silk"][0].get_active_material(0))
	var competitor = Finish.new()
	visual.add_child(competitor)
	check("Second finish owner cannot stack or steal surfaces",not competitor.configure(visual,supplied) and not competitor.configured)
	competitor.free()
	secondaries["Cobalt handwoven silk"].set_shader_parameter("secondary_offset",Vector3(.04,.03,.02))
	check("Animation owner can keep writing its unowned offset",finish.configure(visual,supplied))
	var restored := finish.release()
	check("Release restores all 16 slots and 21 shader fields",restored.restored_slots == 16 and restored.restored_uniforms == 21 and restored.conflicts.is_empty())
	check("Release retains secondary motion written during finish",secondaries["Cobalt handwoven silk"].get_shader_parameter("secondary_offset") == Vector3(.04,.03,.02))
	var same := true
	for label in standards:
		for mesh in mesh_by_label[label]: same = same and mesh.get_active_material(0) == standards[label] and mesh.get_surface_override_material(0) == null
	for label in secondaries: same = same and not secondaries[label].has_meta(Finish.OWNER_META)
	check("Release returns exact calibration material identities and clears ownership",same and not finish.configured)
	check("Repeated release is harmless",finish.release().restored_slots == 0)
	var cycled := true
	for unused in 100:
		cycled = cycled and finish.configure(visual,supplied)
		var result: Dictionary = finish.release()
		cycled = cycled and result.restored_slots == 16 and result.conflicts.is_empty()
	check("100 full configure/release cycles leave no owned resources",cycled and finish.report().standard_materials == 0)
	standards["Pupil"].roughness = NAN
	check("A late invalid standard rejects the complete transaction",not finish.configure(visual,supplied) and not secondaries["Cobalt handwoven silk"].has_meta(Finish.OWNER_META) and mesh_by_label["Rama warm skin"][0].get_surface_override_material(0) == null)
	standards["Pupil"].roughness = .53
	secondaries["Swept black hair"].set_shader_parameter("specular_value",NAN)
	check("A late invalid shader rejects the complete transaction",not finish.configure(visual,supplied) and mesh_by_label["Rama warm skin"][0].get_surface_override_material(0) == null)
	secondaries["Swept black hair"].set_shader_parameter("specular_value",.5)
	finish.configure(visual,supplied)
	secondaries["Swept black hair"].set_shader_parameter("roughness_value",.89)
	check("External mutation of an owned uniform is detected",not finish.configure(visual,supplied))
	var foreign_override := _standard("new foreign override")
	mesh_by_label["Ivory silk"][0].set_surface_override_material(0,foreign_override)
	var conflicts: Dictionary = finish.release()
	check("Release preserves newer shader uniform and surface override",secondaries["Swept black hair"].get_shader_parameter("roughness_value") == .89 and mesh_by_label["Ivory silk"][0].get_active_material(0) == foreign_override and conflicts.conflicts.size() == 2)
	mesh_by_label["Ivory silk"][0].set_surface_override_material(0,null)
	secondaries["Swept black hair"].set_shader_parameter("roughness_value",.53)
	var preexisting := _standard("Ivory silk")
	mesh_by_label["Ivory silk"][0].set_surface_override_material(0,preexisting)
	finish.configure(visual,supplied)
	finish.release()
	check("Existing per-surface override is restored by exact identity",mesh_by_label["Ivory silk"][0].get_surface_override_material(0) == preexisting)
	mesh_by_label["Ivory silk"][0].set_surface_override_material(0,null)
	finish.configure(visual,supplied)
	var edited: StandardMaterial3D = mesh_by_label["Rama warm skin"][0].get_active_material(0)
	edited.albedo_color = Color(.11,.22,.33,1)
	var edited_release: Dictionary = finish.release()
	check("Release preserves later unrelated property edits on an isolated material",mesh_by_label["Rama warm skin"][0].get_active_material(0) == edited and edited.albedo_color == Color(.11,.22,.33,1) and edited_release.conflicts.size() == 2)
	for mesh in mesh_by_label["Rama warm skin"]: mesh.set_surface_override_material(0,null)
	finish.configure(visual,supplied)
	mesh_by_label["Pupil"][0].free()
	check("Freed mesh lifecycle safely invalidates its slot",finish.release().invalidated == 1)
	var second_visual := Node3D.new()
	root.add_child(second_visual)
	var isolated := _mesh(standards["Rama warm skin"])
	second_visual.add_child(isolated)
	finish.configure(visual,supplied)
	check("Other heroes sharing imported materials remain isolated",isolated.get_active_material(0) == standards["Rama warm skin"] and isolated.get_surface_override_material(0) == null)
	check("Configured owner refuses a different visual",not finish.configure(second_visual,supplied))
	finish.release()
	finish.configure(visual,supplied)
	var transferred: MeshInstance3D = mesh_by_label["Ivory silk"][0]
	var transferred_material := transferred.get_active_material(0)
	transferred.reparent(second_visual)
	check("Transfer out of bound visual invalidates shared material ownership",not finish.configure(visual,supplied))
	var transfer_release: Dictionary = finish.release()
	check("Release does not write to a transferred mesh outside its bound visual",transfer_release.invalidated == 1 and transferred.get_active_material(0) == transferred_material)
	transferred.reparent(visual)
	transferred.set_surface_override_material(0,null)
	finish.configure(visual,supplied)
	var transferred_hair: MeshInstance3D = mesh_by_label["Swept black hair"][0]
	var shared_hair: ShaderMaterial = secondaries["Swept black hair"]
	transferred_hair.reparent(second_visual)
	var before_hair: Variant = shared_hair.get_shader_parameter("roughness_value")
	var hair_release: Dictionary = finish.release()
	check("A transferred shared secondary slot blocks uniform rollback for the entire material",hair_release.invalidated == 1 and shared_hair.get_shader_parameter("roughness_value") == before_hair and not shared_hair.has_meta(Finish.OWNER_META))
	transferred_hair.reparent(visual)
	finish.configure(visual,supplied)
	visual.remove_child(finish)
	check("Component tree exit releases materials automatically",not finish.configured and mesh_by_label["Rama warm skin"][0].get_surface_override_material(0) == null)
	finish.free()
	if use_resources:
		var real_finish = Finish.new()
		visual.add_child(real_finish)
		check("Imported runtime map resources configure through public default API",real_finish.configure(visual) and real_finish.report().configured)
		real_finish.release()
	var passed := true
	for result in checks: passed = passed and result.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"checks":checks,"source_sha256":FileAccess.get_sha256("res://scripts/rama_surface_finish.gd"),"test_sha256":FileAccess.get_sha256("res://tests/rama_surface_finish_cases.gd"),"real_maps":use_resources,"scope":"Focused PBR ownership, source preservation and lifecycle checks. Not visual, animation or GPU performance acceptance."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	visual.free(); second_visual.free()
	quit(0 if passed else 1)
