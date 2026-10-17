extends RefCounted
## Original, bounded lighting for the authored Lanka courtyard and Rama portrait.
## Call after the world and its lantern lights exist, and again when settings change.
## This configures existing resources; it does not own the scene or gameplay.
const GroundShadows = preload("res://scripts/ground_shadow_policy.gd")

static func apply(environment: Environment, sun: DirectionalLight3D, world: Node3D,
		night: bool = false, shadows: bool = true) -> void:
	if environment == null or not is_instance_valid(sun) or not is_instance_valid(world):
		return
	# Exact flat receivers only; keep hero/building shadows and all colliders.
	GroundShadows.apply_courtyard(world)
	var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
	environment.background_mode = Environment.BG_SKY
	if environment.sky == null:
		environment.sky = Sky.new()
	var sky_material := environment.sky.sky_material as ProceduralSkyMaterial
	if sky_material == null:
		sky_material = ProceduralSkyMaterial.new()
		environment.sky.sky_material = sky_material
	# Separate a warm horizon from a cool vault; a 16-degree sun bleaches both.
	sky_material.sky_top_color = Color("172640") if night else Color("3c5879")
	sky_material.sky_horizon_color = Color("526781") if night else Color("d4ba9e")
	sky_material.ground_bottom_color = Color("080e18") if night else Color("15212b")
	sky_material.ground_horizon_color = sky_material.sky_horizon_color
	sky_material.sky_energy_multiplier = 0.68 if night else 0.90
	sky_material.ground_energy_multiplier = 0.5
	sky_material.sky_curve = 0.20
	sky_material.ground_curve = 0.12
	sky_material.sun_angle_max = 0.9
	sky_material.sun_curve = 0.08
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	# A restrained, near-neutral ambient preserves local skin/cloth colour. Shape
	# comes from the directional key/fill rather than an orange ambient wash.
	environment.ambient_light_color = Color("a6b9d7") if night else Color("c3c9d2")
	environment.ambient_light_energy = 0.32 if night else 0.30
	environment.ambient_light_sky_contribution = 0.0
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	environment.tonemap_white = 1.0
	# Light depth haze, not a coloured veil over nearby stone and hero materials.
	environment.fog_enabled = true
	environment.fog_light_color = Color("405777") if night else Color("96a8b6")
	environment.fog_light_energy = 0.5
	environment.fog_density = 0.0016 if night else 0.0013
	environment.fog_sky_affect = 0.12
	environment.fog_sun_scatter = 0.08
	# No real-time GI, screen reflections, volumetric fog or shadowed point lights.
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
	environment.ssao_detail = 0.5
	environment.ssao_light_affect = 0.15
	sun.name = "SettingSun"
	sun.rotation_degrees = Vector3(-32, -47, 0) if night else Vector3(-26, -47, 0)
	sun.light_color = Color("b7cbed") if night else Color("ffe2bd")
	sun.light_energy = 0.50 if night else 1.35
	sun.light_angular_distance = 0.7
	sun.shadow_enabled = shadows
	sun.shadow_bias = 0.025
	sun.shadow_normal_bias = 0.35
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
	fill.light_color = Color("a8c7e5")
	fill.light_energy = 0.20 if night else 0.24
	fill.shadow_enabled = false
	# The fill illuminates forms without adding a second sun to the procedural sky.
	fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	for child in world.get_children():
		if child is OmniLight3D:
			# This is an existing scene-owned portrait fill, not a practical lantern.
			# Keep its neutral spectrum so skin/eyes and blue/gold remain separable.
			if child.name == "HeroPortraitFill":
				child.light_color = Color("e0e8f3")
				child.light_energy = 2.6 if night else 3.0
				child.omni_range = 6.0
				child.omni_attenuation = 1.0
				child.shadow_enabled = false
				continue
			child.light_color = Color("ffae65")
			child.light_energy = 2.0 if night else 1.45
			child.omni_range = 5.5
			child.omni_attenuation = 1.8
			child.shadow_enabled = false
