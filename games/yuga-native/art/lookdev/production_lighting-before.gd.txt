extends RefCounted
## Original, inexpensive art direction for the authored Lanka courtyard.
## Call after the world and its lantern lights exist, and again when settings change.
## This configures existing resources; it does not own the scene or gameplay.

static func apply(environment: Environment, sun: DirectionalLight3D, world: Node3D,
		night: bool = false, shadows: bool = true) -> void:
	if environment == null or not is_instance_valid(sun) or not is_instance_valid(world):
		return
	var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
	environment.background_mode = Environment.BG_SKY
	if environment.sky == null:
		environment.sky = Sky.new()
	var sky_material := environment.sky.sky_material as ProceduralSkyMaterial
	if sky_material == null:
		sky_material = ProceduralSkyMaterial.new()
		environment.sky.sky_material = sky_material
	# Separate a warm horizon from a cool vault; a 16-degree sun bleaches both.
	sky_material.sky_top_color = Color("111d37") if night else Color("253f5b")
	sky_material.sky_horizon_color = Color("46516a") if night else Color("c59776")
	sky_material.ground_bottom_color = Color("080e18") if night else Color("15212b")
	sky_material.ground_horizon_color = sky_material.sky_horizon_color
	sky_material.sky_energy_multiplier = 0.65 if night else 0.82
	sky_material.ground_energy_multiplier = 0.5
	sky_material.sky_curve = 0.20
	sky_material.ground_curve = 0.12
	sky_material.sun_angle_max = 0.9
	sky_material.sun_curve = 0.08
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("93a9cc") if night else Color("9eafc6")
	environment.ambient_light_energy = 0.21 if night else 0.27
	environment.ambient_light_sky_contribution = 0.0
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	environment.tonemap_white = 1.0
	# Light depth haze, not a coloured veil over nearby stone and hero materials.
	environment.fog_enabled = true
	environment.fog_light_color = Color("354861") if night else Color("78858c")
	environment.fog_light_energy = 0.5
	environment.fog_density = 0.0035 if night else 0.0025
	environment.fog_sky_affect = 0.12
	environment.fog_sun_scatter = 0.08
	# No real-time GI, screen reflections, volumetric fog or shadowed point lights.
	environment.volumetric_fog_enabled = false
	environment.ssr_enabled = false
	environment.ssil_enabled = false
	environment.sdfgi_enabled = false
	environment.glow_enabled = forward_plus
	environment.glow_intensity = 0.28
	environment.glow_strength = 0.65
	environment.glow_bloom = 0.0
	environment.glow_hdr_threshold = 1.5
	environment.ssao_enabled = forward_plus
	environment.ssao_radius = 0.7
	environment.ssao_intensity = 1.0
	environment.ssao_power = 1.3
	environment.ssao_detail = 0.5
	environment.ssao_light_affect = 0.15
	sun.name = "SettingSun"
	sun.rotation_degrees = Vector3(-32, -47, 0) if night else Vector3(-26, -47, 0)
	sun.light_color = Color("b2c9ee") if night else Color("ffd2a0")
	sun.light_energy = 0.42 if night else 1.12
	sun.light_angular_distance = 0.7
	sun.shadow_enabled = shadows
	sun.shadow_bias = 0.035
	sun.shadow_normal_bias = 0.7
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 70.0
	sun.directional_shadow_blend_splits = true
	# Keep an existing fill; do not accumulate lights as settings are toggled.
	var fill := world.get_node_or_null("CoolSkyFill") as DirectionalLight3D
	if fill == null:
		fill = DirectionalLight3D.new()
		fill.name = "CoolSkyFill"
		world.add_child(fill)
	fill.rotation_degrees = Vector3(-58, 137, 0)
	fill.light_color = Color("9ab8da")
	fill.light_energy = 0.06 if night else 0.10
	fill.shadow_enabled = false
	for child in world.get_children():
		if child is OmniLight3D:
			child.light_color = Color("ffae65")
			child.light_energy = 2.0 if night else 1.45
			child.omni_range = 5.5
			child.omni_attenuation = 1.8
			child.shadow_enabled = false
