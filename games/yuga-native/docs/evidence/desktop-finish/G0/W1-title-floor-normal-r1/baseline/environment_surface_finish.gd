extends RefCounted
## Original Confluence/courtyard finish. Binds exact authored surfaces once;
## never changes shared meshes, imported materials, transforms or colliders.
const SHADER = preload("res://assets/environment-finish/masonry.gdshader")
const META := "confluence_surface_finish_v1"
const MAX_MATERIALS := 12
const PROFILES := {
	"Confluence_honey_sandstone": {"tint":Vector3(0.88,0.78,0.62), "mineral":Vector3(0.72,0.81,0.75), "weather":0.20, "carving":0.65},
	"Confluence_carved_limestone": {"tint":Vector3(0.74,0.81,0.80), "mineral":Vector3(0.69,0.79,0.77), "weather":0.18, "carving":0.45},
	"Confluence_warm_ivory": {"tint":Vector3(0.90,0.83,0.68), "mineral":Vector3(0.79,0.83,0.74), "weather":0.15, "carving":0.45},
	"Confluence_teal_ceramic": {"tint":Vector3(0.80,0.97,1.0), "mineral":Vector3(0.58,0.75,0.72), "weather":0.10},
	"Confluence_transit_indigo": {"tint":Vector3(0.72,0.84,1.0), "mineral":Vector3(0.69,0.75,0.87), "weather":0.08},
	"Confluence_opaque_blue_glass": {"tint":Vector3(0.70,0.88,1.0), "mineral":Vector3.ONE, "weather":0.0},
	"Confluence_warm_window": {"tint":Vector3(1.0,0.84,0.62), "mineral":Vector3.ONE, "weather":0.0},
}
const COURTYARD_PROFILES := {
	"Courtyard_stone_0": {"tint":Vector3(0.64,0.665,0.64), "mineral":Vector3(0.76,0.83,0.80), "weather":0.18},
	"Courtyard_stone_1": {"tint":Vector3(0.65,0.66,0.625), "mineral":Vector3(0.87,0.83,0.71), "weather":0.18},
	"Courtyard_stone_2": {"tint":Vector3(0.63,0.655,0.64), "mineral":Vector3(0.73,0.83,0.82), "weather":0.18},
	"Courtyard_stone_3": {"tint":Vector3(0.65,0.65,0.615), "mineral":Vector3(0.90,0.82,0.69), "weather":0.18},
	"Limestone_mortar": {"tint":Vector3(0.62,0.67,0.65), "mineral":Vector3(0.78,0.80,0.72), "weather":0.12},
	"Quiet_stone_inlay": {"tint":Vector3(0.76,0.75,0.66), "mineral":Vector3(0.85,0.84,0.72), "weather":0.10},
	"Warm_carved_sandstone": {"tint":Vector3(0.86,0.75,0.60), "mineral":Vector3(0.78,0.83,0.72), "weather":0.18, "carving":0.55},
	"Pale_limestone": {"tint":Vector3(0.78,0.81,0.73), "mineral":Vector3(0.75,0.83,0.80), "weather":0.16, "carving":0.40},
	"Indigo_glazed_stone": {"tint":Vector3(0.77,0.90,1.0), "mineral":Vector3(0.68,0.78,0.90), "weather":0.08},
}

static func configure(world: Node3D) -> Dictionary:
	if not is_instance_valid(world): return {}
	if world.has_meta(META): return diagnostics(world)
	var city := world.get_node_or_null("CityArt")
	var profiles: Dictionary = PROFILES
	var courtyard := false
	if city == null:
		city = world.get_node_or_null("AuthoredLankaCourtyard")
		profiles = COURTYARD_PROFILES
		courtyard = true
	# Exact subtree and material-name boundaries exclude hero, armies, district
	# ornaments, gameplay markers, water and merely similar material names.
	if city == null: return {}
	var cache: Dictionary = {}
	var windows: Array[ShaderMaterial] = []
	var count := 0
	var meshes := city.find_children("*", "MeshInstance3D", true, false)
	for node in meshes:
		var mesh := node as MeshInstance3D
		if mesh.mesh == null or mesh.material_override != null: continue
		for surface in range(mesh.mesh.get_surface_count()):
			if mesh.get_surface_override_material(surface) != null: continue
			var original := mesh.mesh.surface_get_material(surface) as StandardMaterial3D
			if original == null or not profiles.has(original.resource_name): continue
			# Refuse features the small finish shader cannot faithfully transport.
			if original.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED or original.next_pass != null: continue
			if original.cull_mode != BaseMaterial3D.CULL_DISABLED or original.vertex_color_use_as_albedo: continue
			if original.ao_enabled: continue
			if not courtyard and (original.roughness_texture != null or original.metallic_texture != null): continue
			var key := original.get_instance_id()
			if not cache.has(key):
				if cache.size() >= MAX_MATERIALS: continue
				var material := ShaderMaterial.new()
				material.shader = SHADER
				material.resource_name = "EnvironmentFinish_" + original.resource_name
				var profile: Dictionary = profiles[original.resource_name]
				material.set_shader_parameter("base_color", original.albedo_color)
				material.set_shader_parameter("surface_tint", profile.tint)
				material.set_shader_parameter("mineral_tint", profile.mineral)
				material.set_shader_parameter("weather_amount", profile.weather)
				material.set_shader_parameter("carving_amount", profile.get("carving",0.0))
				material.set_shader_parameter("base_roughness", original.roughness)
				material.set_shader_parameter("base_metallic", original.metallic)
				material.set_shader_parameter("base_specular", original.metallic_specular)
				material.set_shader_parameter("uv_scale", original.uv1_scale)
				material.set_shader_parameter("uv_offset", original.uv1_offset)
				material.set_shader_parameter("has_albedo", original.albedo_texture != null)
				material.set_shader_parameter("albedo_texture", original.albedo_texture)
				material.set_shader_parameter("has_normal", original.normal_enabled and original.normal_texture != null)
				material.set_shader_parameter("normal_texture", original.normal_texture)
				material.set_shader_parameter("normal_depth", original.normal_scale)
				material.set_shader_parameter("has_roughness", original.roughness_texture != null)
				material.set_shader_parameter("roughness_texture", original.roughness_texture)
				material.set_shader_parameter("roughness_channel", _channel(original.roughness_texture_channel))
				material.set_shader_parameter("has_metallic", original.metallic_texture != null)
				material.set_shader_parameter("metallic_texture", original.metallic_texture)
				material.set_shader_parameter("metallic_channel", _channel(original.metallic_texture_channel))
				if original.resource_name == "Confluence_warm_window":
					material.set_shader_parameter("window_surface", true)
					windows.append(material)
				cache[key] = material
			mesh.set_surface_override_material(surface, cache[key])
			count += 1
	world.set_meta(META, {"materials":cache, "windows":windows, "surfaces":count})
	set_phase(world, 0.0)
	return diagnostics(world)

static func _channel(channel: int) -> Vector4:
	match channel:
		BaseMaterial3D.TEXTURE_CHANNEL_RED: return Vector4(1,0,0,0)
		BaseMaterial3D.TEXTURE_CHANNEL_GREEN: return Vector4(0,1,0,0)
		BaseMaterial3D.TEXTURE_CHANNEL_BLUE: return Vector4(0,0,1,0)
		BaseMaterial3D.TEXTURE_CHANNEL_ALPHA: return Vector4(0,0,0,1)
		_: return Vector4(0.33333334,0.33333334,0.33333334,0)

static func set_phase(world: Node3D, value: float) -> void:
	if not is_instance_valid(world) or not world.has_meta(META): return
	var phase := clampf(value, 0.0, 1.0) if is_finite(value) else 0.0
	var records: Dictionary = world.get_meta(META)
	# Fixed cached resources only: no traversal, geometry or resource allocation.
	for material in records.windows:
		material.set_shader_parameter("night_blend", phase)

static func diagnostics(world: Node3D) -> Dictionary:
	if not is_instance_valid(world) or not world.has_meta(META): return {"surfaces":0,"materials":0,"windows":0}
	var records: Dictionary = world.get_meta(META)
	return {"surfaces":records.surfaces,"materials":records.materials.size(),"windows":records.windows.size(),
		"material_budget":MAX_MATERIALS,"extra_meshes":0,"extra_lights":0,"collision_writes":0}
