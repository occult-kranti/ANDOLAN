extends SceneTree
const Finish = preload("res://scripts/environment_surface_finish.gd")
const Production = preload("res://scripts/production_lighting.gd")
const Atmosphere = preload("res://scripts/hero_atmosphere.gd")
var checks: Array[Dictionary] = []
func check(ok: bool, label: String) -> void:
	checks.append({"id":label,"passed":ok})
	if not ok: push_error(label)
func _initialize() -> void:
	call_deferred("_run")
func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var authored := (load("res://assets/environment/lanka_courtyard.glb") as PackedScene).instantiate()
	authored.name = "AuthoredLankaCourtyard"
	world.add_child(authored)
	var before: Array[Dictionary] = []
	for node in authored.find_children("*","MeshInstance3D",true,false):
		for surface in range(node.mesh.get_surface_count()):
			before.append({"node":node,"surface":surface,"mesh":node.mesh,"material":node.mesh.surface_get_material(surface),"transform":node.transform})
	var children := world.get_child_count()
	var result := Finish.configure(world)
	check(result.materials == 9 and result.surfaces > 9, "nine actual courtyard profiles bind across existing imported surfaces")
	check(world.get_child_count() == children, "finish creates no scene node")
	var geometry := true
	var textures := true
	var channels := true
	var exclusions := true
	var original_ids: Array[int] = []
	var scalar_profiles: Array[String] = []
	for row in before:
		geometry = geometry and row.node.mesh == row.mesh and row.node.transform == row.transform and row.mesh.surface_get_material(row.surface) == row.material
		var original: StandardMaterial3D = row.material
		var material: ShaderMaterial = row.node.get_surface_override_material(row.surface)
		if Finish.COURTYARD_PROFILES.has(original.resource_name):
			textures = textures and material != null
			if material != null:
				original_ids.append(material.get_instance_id())
				for key in ["albedo_texture","normal_texture","roughness_texture","metallic_texture"]:
					textures = textures and material.get_shader_parameter(key) == original.get(key)
				textures = textures and material.get_shader_parameter("uv_scale") == original.uv1_scale and material.get_shader_parameter("uv_offset") == original.uv1_offset
				if original.roughness_texture != null:
					scalar_profiles.append(original.resource_name)
					channels = channels and original.roughness_texture_channel == BaseMaterial3D.TEXTURE_CHANNEL_GREEN and material.get_shader_parameter("roughness_channel") == Vector4(0,1,0,0)
				if original.metallic_texture != null:
					channels = channels and material.get_shader_parameter("metallic_channel") == Finish._channel(original.metallic_texture_channel)
		else: exclusions = exclusions and material == null
	check(geometry, "all original imported mesh identities transforms and source materials preserved")
	check(textures, "original albedo normal packed scalar textures and UV transforms transported")
	check(channels and scalar_profiles.size() >= 7, "actual imported linear roughness GREEN and metallic channel masks retained")
	check(exclusions, "brass water flames plants skyline and recess materials excluded")
	check(Finish._channel(BaseMaterial3D.TEXTURE_CHANNEL_RED) == Vector4(1,0,0,0) and Finish._channel(BaseMaterial3D.TEXTURE_CHANNEL_ALPHA) == Vector4(0,0,0,1), "channel counterexamples do not assume every scalar is GREEN")
	var environment := Environment.new()
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var portrait := OmniLight3D.new()
	portrait.name = "HeroPortraitFill"
	world.add_child(portrait)
	var overlay = Atmosphere.new()
	var stable := true
	for night in [false,true,false,true]:
		Production.apply(environment,sun,world,night)
		stable = stable and overlay.configure(world,environment,sun,night)
		stable = stable and Finish.configure(world) == result
		var sky: ProceduralSkyMaterial = environment.sky.sky_material
		stable = stable and sky.sky_horizon_color == sky.ground_horizon_color and sky.sky_energy_multiplier == sky.ground_energy_multiplier
		check(environment.ambient_light_energy >= .29999 and environment.tonemap_exposure == 1.0, "visibility floor and exposure retained %s" % night)
		check(is_equal_approx(world.get_node("CoolSkyFill").light_energy, .36 if night else .32), "day fill adjustment and retained night visibility floor are actual final writer %s" % night)
	check(stable, "day night repeated settings preserve finish IDs and sky join radiance")
	var after_ids: Array[int] = []
	for row in before:
		var material: Material = row.node.get_surface_override_material(row.surface)
		if material != null: after_ids.append(material.get_instance_id())
	check(original_ids == after_ids, "settings do not allocate replacement surface materials")
	check(overlay.set_mode("neutral"), "neutral restores current production baseline")
	check(overlay.set_mode("day"), "day can resume after neutral")
	sun.light_energy = 0.73
	var release: Dictionary = overlay.restore()
	check(is_equal_approx(sun.light_energy,0.73) and release.conflicts.has("sun:light_energy"), "new external light ownership survives overlay teardown")
	var passed := true
	for row in checks: passed = passed and row.passed
	var report := {"passed":passed,"checks":checks,"bindings":result,"scalar_profiles":scalar_profiles,"scope":"Read-only cached actual courtyard resources and atmosphere lifecycle. No shader compile/render acceptance.","source_sha256":{}}
	for path in ["res://scripts/environment_surface_finish.gd","res://scripts/production_lighting.gd","res://scripts/hero_atmosphere.gd","res://assets/environment-finish/masonry.gdshader","res://assets/environment/lanka_courtyard.glb"]:
		report.source_sha256[path] = FileAccess.get_sha256(path)
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			file.store_string(JSON.stringify(report,"\t") + "\n")
	print("G2_ENVIRONMENT_CASES ",JSON.stringify({"passed":passed,"checks":checks.size(),"bindings":result}))
	world.free()
	quit(0 if passed else 1)
