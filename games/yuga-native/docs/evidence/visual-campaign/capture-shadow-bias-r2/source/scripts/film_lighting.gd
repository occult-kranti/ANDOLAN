extends RefCounted
## Film-only lighting revision from actual R1 frames, never shared scene assets.
## Drop-in apply() API; repeated calls reuse two local lights and one sky fill.

static func apply(environment: Environment, sun: DirectionalLight3D, world: Node3D,
		_night: bool = false, shadows: bool = true) -> void:
	if environment == null or not is_instance_valid(sun) or not is_instance_valid(world):
		return
	var forward_plus := RenderingServer.get_current_rendering_method() == "forward_plus"
	environment.background_mode = Environment.BG_SKY
	if environment.sky == null:
		environment.sky = Sky.new()
	var sky := environment.sky.sky_material as ProceduralSkyMaterial
	if sky == null:
		sky = ProceduralSkyMaterial.new()
		environment.sky.sky_material = sky
	# R1 looked into a flat brown lower hemisphere. Use a coherent cool horizon
	# on both sides while keeping warmth in the actual directional key light.
	sky.sky_top_color = Color("395b79")
	sky.sky_horizon_color = Color("9bb9ca")
	sky.ground_horizon_color = Color("8ba5b6")
	sky.ground_bottom_color = Color("374a60")
	sky.sky_energy_multiplier = 0.84
	sky.ground_energy_multiplier = 0.64
	sky.sky_curve = 0.18
	sky.ground_curve = 0.16
	sky.sun_angle_max = 0.75
	sky.sun_curve = 0.08
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("b9cee1")
	environment.ambient_light_energy = 0.36
	environment.ambient_light_sky_contribution = 0.0
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.0
	environment.tonemap_white = 1.0
	environment.fog_enabled = true
	environment.fog_light_color = Color("90aabd")
	environment.fog_light_energy = 0.38
	environment.fog_density = 0.0012
	environment.fog_sky_affect = 0.08
	environment.fog_sun_scatter = 0.0
	environment.volumetric_fog_enabled = false
	environment.ssr_enabled = false
	environment.ssil_enabled = false
	environment.sdfgi_enabled = false
	# Preserve thin VFX silhouettes; no bloom blanket or noisy screen-space AO.
	environment.ssao_enabled = false
	environment.glow_enabled = forward_plus
	environment.glow_intensity = 0.18
	environment.glow_strength = 0.5
	environment.glow_bloom = 0.0
	environment.glow_hdr_threshold = 1.8
	sun.rotation_degrees = Vector3(-48.0,-38.0,0.0)
	sun.light_color = Color("ffe0b6")
	sun.light_energy = 1.08
	# R2 actor shadows showed coarse grain with PCSS enabled in software capture.
	# Zero angular distance disables contact-hardening sampling; keep the
	# existing depth/bias/floor settings fixed for the next comparison.
	sun.light_angular_distance = 0.0
	sun.shadow_enabled = shadows
	sun.shadow_bias = 0.05
	sun.shadow_normal_bias = 0.85
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	sun.directional_shadow_max_distance = 48.0
	sun.directional_shadow_blend_splits = true
	var fill := world.get_node_or_null("FilmCoolFill") as DirectionalLight3D
	if fill == null:
		fill = DirectionalLight3D.new()
		fill.name = "FilmCoolFill"
		world.add_child(fill)
	fill.rotation_degrees = Vector3(-38.0,140.0,0.0)
	fill.light_color = Color("a6c7ed")
	fill.light_energy = 0.18
	fill.shadow_enabled = false
	fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	_soft_light(world,"FilmWarmSoftbox",Vector3(-6.0,4.0,-8.0),Color("ffe6c3"),0.65,14.0)
	_soft_light(world,"FilmCoolSoftbox",Vector3(6.0,4.0,8.0),Color("bacaf4"),0.55,12.0)
	# A controlled R2 candidate: these floor instances no longer self-shadow,
	# but still receive actors' and architecture's shadows. Actual captures must
	# distinguish shadow sampling from material aliasing. Shared GLB unchanged.
	var model := world.get_node_or_null("AuthoredCourtyard")
	if model != null:
		_floor_shadow_policy(model)

static func _soft_light(world: Node3D, id: String, position_: Vector3, tint: Color,
		energy: float, range_: float) -> void:
	var light := world.get_node_or_null(id) as OmniLight3D
	if light == null:
		light = OmniLight3D.new()
		light.name = id
		world.add_child(light)
	light.position = position_
	light.light_color = tint
	light.light_energy = energy
	light.omni_range = range_
	light.omni_attenuation = 1.4
	light.shadow_enabled = false

static func _floor_shadow_policy(node: Node) -> void:
	if node is MeshInstance3D:
		var id := String(node.name)
		if id.begins_with("FLOOR_") or id == "COL_Limestone_mortar" or id == "DECOR_Quiet_stone_inlay":
			node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		if id == "DECOR_Quiet_stone_inlay":
			# Verified GLB minimum Y=-0.003794 intersects slabs at Y=0.
			# Lift this film instance by 8 mm; retain the authored floor height.
			if not node.has_meta("film_original_y"):
				node.set_meta("film_original_y", node.position.y)
			node.position.y = float(node.get_meta("film_original_y")) + 0.008
	for child in node.get_children():
		_floor_shadow_policy(child)
