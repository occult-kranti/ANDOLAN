extends RefCounted
## Original Confluence lighting controller. Phase 0 = day, 1 = night.
## configure() once; set_phase() smoothly changes existing resources only.
## Static entry points also support scene-owned transition state.

const MAX_PRACTICALS := 12
const SHADOW_DISTANCE := 72.0
const WATER_SHADER := preload("res://scripts/world_water.gdshader")
const MythicEnvironment = preload("res://scripts/mythic_environment.gd")
const GroundShadows = preload("res://scripts/ground_shadow_policy.gd")

var _environment: Environment
var _sun: DirectionalLight3D
var _world: Node3D
var _phase := 0.0
var _shadows := true

func configure(environment: Environment, sun: DirectionalLight3D, world: Node3D,
		placements: Array = [], shadows: bool = true) -> void:
	_environment = environment
	_sun = sun
	_world = world
	_shadows = shadows
	# Once per configure, never a traversal/mutation in the per-phase apply path.
	GroundShadows.apply_world(world)
	configure_practicals(world, placements)
	set_phase(_phase)

func set_phase(value: float) -> void:
	_phase = clampf(value, 0.0, 1.0) if is_finite(value) else 0.0
	apply(_environment, _sun, _world, _phase, _shadows)

func diagnostics() -> Dictionary:
	var root: Node = _world.get_node_or_null("WorldPracticals") if is_instance_valid(_world) else null
	return {
		"phase": _phase, "day_phase": 0.0, "night_phase": 1.0,
		"practical_count": root.get_child_count() if root != null else 0,
		"practical_budget": MAX_PRACTICALS, "practical_shadow_count": 0,
		"directional_budget": 2, "shadow_distance_m": SHADOW_DISTANCE,
		"volumetric_fog": false, "screen_space_reflections": false,
		"water_geometry_displacement": false,
	}

static func apply(environment: Environment, sun: DirectionalLight3D, world: Node3D,
		night_blend: float = 0.0, shadows: bool = true) -> void:
	if environment == null or not is_instance_valid(sun) or not is_instance_valid(world):
		return
	var phase := clampf(night_blend, 0.0, 1.0) if is_finite(night_blend) else 0.0
	var dusk := sin(phase * PI)
	var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
	environment.background_mode = Environment.BG_SKY
	if environment.sky == null:
		environment.sky = Sky.new()
	var sky := environment.sky.sky_material as ProceduralSkyMaterial
	if sky == null:
		sky = ProceduralSkyMaterial.new()
		environment.sky.sky_material = sky
	# Keep clear silhouettes at both endpoints. Blue night is a lighting mood,
	# never a vision or combat advantage. Constant ambient avoids black alleys.
	sky.sky_top_color = Color("3c6083").lerp(Color("1c2d49"), phase)
	sky.sky_horizon_color = Color("d1bca8").lerp(Color("647d9b"), phase).lerp(Color("b88e91"), dusk * 0.28)
	sky.ground_bottom_color = Color("354553").lerp(Color("1b2a40"), phase)
	sky.ground_horizon_color = sky.sky_horizon_color
	sky.sky_energy_multiplier = lerpf(0.92, 0.64, phase)
	sky.ground_energy_multiplier = 0.52
	sky.sky_curve = 0.22
	sky.ground_curve = 0.18
	sky.sun_angle_max = 0.8
	sky.sun_curve = 0.08
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	# Preserve a visibility floor through night, while key/fill direction defines
	# the forms. Neutral daylight avoids tinting every stone and skin surface tan.
	environment.ambient_light_color = Color("c5cbd4").lerp(Color("aec2e0"), phase)
	environment.ambient_light_energy = lerpf(0.30, 0.32, phase)
	environment.ambient_light_sky_contribution = 0.0
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	environment.tonemap_white = 1.0
	environment.fog_enabled = true
	environment.fog_light_color = Color("91a8bc").lerp(Color("536f94"), phase)
	environment.fog_light_energy = 0.4
	environment.fog_density = lerpf(0.0008, 0.0013, phase)
	environment.fog_sky_affect = 0.08
	environment.fog_sun_scatter = 0.05
	environment.volumetric_fog_enabled = false
	environment.ssr_enabled = false
	environment.ssil_enabled = false
	environment.sdfgi_enabled = false
	environment.glow_enabled = forward_plus
	environment.glow_intensity = 0.16
	environment.glow_strength = 0.45
	environment.glow_bloom = 0.0
	environment.glow_hdr_threshold = 1.6
	environment.ssao_enabled = forward_plus
	environment.ssao_radius = 0.45
	environment.ssao_intensity = 0.75
	environment.ssao_power = 1.1
	environment.ssao_detail = 0.4
	environment.ssao_light_affect = 0.1
	sun.rotation_degrees = Vector3(-42.0, -38.0, 0.0).lerp(Vector3(-34.0, -55.0, 0.0), phase)
	sun.light_color = Color("ffe4c2").lerp(Color("b7cbed"), phase).lerp(Color("ffd0a7"), dusk * 0.25)
	sun.light_energy = lerpf(1.25, 0.48, phase)
	sun.light_angular_distance = 0.6
	sun.shadow_enabled = shadows
	# Directional shadow distance is camera-local, not all 170 m of the arena.
	# Bias values are initial art settings: captured views must confirm contact.
	sun.shadow_bias = 0.025
	sun.shadow_normal_bias = 0.35
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = SHADOW_DISTANCE
	sun.directional_shadow_blend_splits = true
	var fill := world.get_node_or_null("WorldSkyFill") as DirectionalLight3D
	if fill == null:
		fill = DirectionalLight3D.new()
		fill.name = "WorldSkyFill"
		world.add_child(fill)
	fill.rotation_degrees = Vector3(-55.0, 137.0, 0.0)
	fill.light_color = Color("a8c7e5")
	fill.light_energy = lerpf(0.22, 0.24, phase)
	fill.shadow_enabled = false
	fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	MythicEnvironment.set_phase(world, phase)
	var practicals := world.get_node_or_null("WorldPracticals")
	if practicals != null:
		for child in practicals.get_children():
			if child is OmniLight3D:
				child.light_energy = lerpf(float(child.get_meta("day_energy", 0.4)),
					float(child.get_meta("night_energy", 1.8)), phase)

static func configure_practicals(world: Node3D, placements: Array) -> int:
	if not is_instance_valid(world):
		return 0
	var root := world.get_node_or_null("WorldPracticals") as Node3D
	if root == null:
		root = Node3D.new()
		root.name = "WorldPracticals"
		world.add_child(root)
	for child in root.get_children():
		root.remove_child(child)
		child.free()
	var ordered: Array[Dictionary] = []
	for entry in placements:
		if entry is Dictionary and _finite_vector(entry.get("position")):
			ordered.append(entry)
	ordered.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		var ap := _number(a.get("priority"), 0.0)
		var bp := _number(b.get("priority"), 0.0)
		return ap > bp if ap != bp else str(a.get("id", "")) < str(b.get("id", "")))
	for entry in ordered.slice(0, MAX_PRACTICALS):
		var light := OmniLight3D.new()
		light.name = "Practical_%02d" % root.get_child_count()
		light.set_meta("placement_id", str(entry.get("id", "")))
		var p: Array = entry["position"]
		light.position = Vector3(float(p[0]), float(p[1]), float(p[2]))
		var rgb: Variant = entry.get("color")
		light.light_color = Color(clampf(float(rgb[0]), 0.0, 1.0), clampf(float(rgb[1]), 0.0, 1.0), clampf(float(rgb[2]), 0.0, 1.0)) if _finite_vector(rgb) else Color("ffba71")
		light.omni_range = clampf(_number(entry.get("range"), 5.5), 0.5, 8.0)
		light.omni_attenuation = 1.8
		light.shadow_enabled = false
		var base := clampf(_number(entry.get("energy"), 1.8), 0.0, 3.0)
		var day := clampf(_number(entry.get("day_energy"), base * 0.22), 0.0, 3.0)
		var night := clampf(_number(entry.get("night_energy"), base), 0.0, 3.0)
		light.set_meta("day_energy", day)
		light.set_meta("night_energy", night)
		light.light_energy = day
		root.add_child(light)
	return root.get_child_count()

static func water_material(style: String = "coast", reduced_motion: bool = false) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.shader = WATER_SHADER
	var swamp := style == "swamp"
	material.set_shader_parameter("deep_color", Color("244e42") if swamp else Color("134b60"))
	material.set_shader_parameter("shallow_color", Color("54705a") if swamp else Color("3c8c93"))
	material.set_shader_parameter("ripple_strength", 0.025 if swamp else 0.055)
	material.set_shader_parameter("base_roughness", 0.38 if swamp else 0.23)
	material.set_shader_parameter("animation_speed", 0.0 if reduced_motion else (0.28 if swamp else 0.8))
	return material

static func _number(value: Variant, fallback: float) -> float:
	if (value is float or value is int) and is_finite(float(value)):
		return float(value)
	return fallback

static func _finite_vector(value: Variant) -> bool:
	if not value is Array or value.size() != 3:
		return false
	for component in value:
		if not (component is float or component is int) or not is_finite(float(component)) or absf(float(component)) > 1000000.0:
			return false
	return true
