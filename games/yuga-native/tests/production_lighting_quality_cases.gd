extends SceneTree
## Resource/API regressions only. Rendered art acceptance is a separate gate.
const Courtyard = preload("res://scripts/production_lighting.gd")
const Confluence = preload("res://scripts/world_lighting.gd")
const Ground = preload("res://scripts/ground_shadow_policy.gd")
var checks: Array[Dictionary] = []
var receiver_sources := {}
var harness_cleanup: Array[Dictionary] = []

func check(value: bool, label: String) -> void:
	checks.append({"id": label, "passed": value})
	if not value: push_error(label)

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var portrait := OmniLight3D.new()
	portrait.name = "HeroPortraitFill"
	world.add_child(portrait)
	var lantern := OmniLight3D.new()
	lantern.name = "CourtyardLantern"
	world.add_child(lantern)
	var env := Environment.new()
	for night in [false, true, false, true]:
		Courtyard.apply(env, sun, world, night, not night)
		var fill := world.get_node("CoolSkyFill") as DirectionalLight3D
		check(world.get_child_count() == 4, "courtyard stable existing light budget %s" % night)
		check(fill.sky_mode == DirectionalLight3D.SKY_MODE_LIGHT_ONLY, "courtyard fill does not add a sky sun %s" % night)
		check(not fill.shadow_enabled and not portrait.shadow_enabled and not lantern.shadow_enabled, "courtyard only key may cast shadows %s" % night)
		check(sun.shadow_enabled == (not night), "courtyard shadow setting %s" % night)
		check(portrait.light_color.b > portrait.light_color.r and lantern.light_color.r > lantern.light_color.b, "neutral portrait distinct from warm practical %s" % night)
		check(portrait.light_energy > lantern.light_energy, "portrait not overwritten by lantern profile %s" % night)
		check(is_equal_approx(portrait.omni_attenuation, 1.0) and is_equal_approx(portrait.omni_range, 6.0), "portrait reach and falloff preserved %s" % night)
		check(env.ambient_light_energy >= 0.29999 and env.ambient_light_energy <= 0.32001, "courtyard visibility floor bounded %s" % night)
		check(env.fog_density <= 0.0016001, "courtyard close-range haze bounded %s" % night)
		check(is_equal_approx(env.tonemap_exposure, 1.0), "courtyard exposure fixed for comparisons %s" % night)
		check(env.glow_bloom == 0.0 and env.glow_hdr_threshold >= 1.6, "courtyard no broad bloom veil %s" % night)
		check(sun.shadow_bias <= 0.0251 and sun.shadow_normal_bias <= 0.35001, "courtyard shadow contact offsets bounded %s" % night)
		check(not env.volumetric_fog_enabled and not env.ssr_enabled and not env.sdfgi_enabled and not env.ssil_enabled, "courtyard expensive screen/GI effects disabled %s" % night)
	var sky_id := env.sky.get_instance_id()
	Courtyard.apply(env, sun, world)
	check(env.sky.get_instance_id() == sky_id, "courtyard does not allocate another sky on settings changes")
	Courtyard.apply(null, sun, world)
	Courtyard.apply(env, null, world)
	Courtyard.apply(env, sun, null)
	check(world.get_child_count() == 4, "courtyard invalid inputs do not create nodes")
	world.free()

	world = Node3D.new()
	root.add_child(world)
	sun = DirectionalLight3D.new()
	world.add_child(sun)
	env = Environment.new()
	var controller = Confluence.new()
	controller.configure(env, sun, world, [{"id":"test-diya", "position":[0, 1, 0], "day_energy":0.4, "night_energy":1.8}])
	sky_id = env.sky.get_instance_id()
	for phase in [0.0, 0.25, 0.5, 0.75, 1.0, 0.0]:
		controller.set_phase(phase)
		var fill := world.get_node("WorldSkyFill") as DirectionalLight3D
		check(env.sky.get_instance_id() == sky_id and world.get_child_count() == 3, "world stable sky and light allocation %s" % phase)
		check(env.ambient_light_energy >= 0.29999 and env.ambient_light_energy <= 0.32001, "world visibility floor bounded %s" % phase)
		check(env.fog_density >= 0.0007999 and env.fog_density <= 0.0013001, "world depth haze bounded %s" % phase)
		check(sun.light_energy >= 0.47999 and sun.light_energy <= 1.25001 and fill.light_energy >= 0.21999 and fill.light_energy <= 0.24001, "world key/fill energy bounded %s" % phase)
		check(fill.sky_mode == DirectionalLight3D.SKY_MODE_LIGHT_ONLY and not fill.shadow_enabled, "world fill has no shadow or second sky sun %s" % phase)
		check(is_equal_approx(env.tonemap_exposure, 1.0) and env.ambient_light_sky_contribution == 0.0, "world fixed exposure explicit ambient source %s" % phase)
		check(env.glow_bloom == 0.0 and env.glow_intensity <= 0.16001, "world no broad bloom veil %s" % phase)
		check(sun.directional_shadow_max_distance == 72.0 and sun.shadow_normal_bias <= 0.35001, "world retained camera shadow budget with contact bias %s" % phase)
	controller.set_phase(NAN)
	check(controller.diagnostics().phase == 0.0, "nonfinite phase resets to day")
	controller.set_phase(INF)
	check(controller.diagnostics().phase == 0.0, "infinite phase resets to day")
	controller.set_phase(-1)
	check(controller.diagnostics().phase == 0.0, "negative phase clamps to day")
	controller.set_phase(2)
	check(controller.diagnostics().phase == 1.0, "phase past night clamps")
	controller.configure(env, sun, world, [], false)
	check(not sun.shadow_enabled and world.get_child_count() == 3, "world reconfigure honors shadow off and no accumulation")
	check(controller.diagnostics().practical_count == 0, "world reconfigure removes stale practicals")
	world.free()
	_policy_counterexamples()
	await _actual_receiver_checks()
	var passed := true
	for result in checks: passed = passed and result.passed
	for retirement in harness_cleanup: passed = passed and retirement.retired
	var report := {"passed": passed, "engine":Engine.get_version_info().string,
		"production_lighting_sha256":FileAccess.get_sha256("res://scripts/production_lighting.gd"),
		"world_lighting_sha256":FileAccess.get_sha256("res://scripts/world_lighting.gd"),
		"ground_shadow_policy_sha256":FileAccess.get_sha256("res://scripts/ground_shadow_policy.gd"),
		"actual_receiver_sources":receiver_sources,
		"harness_cleanup":harness_cleanup,
		"test_sha256":FileAccess.get_sha256("res://tests/production_lighting_quality_cases.gd"),
		"checks":checks, "scope":"Godot resource properties, invalid inputs and allocation budgets only. No rendered colour, shadow-artifact, radiance, human readability or GPU performance acceptance."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report, "\t") + "\n")
			else:
				push_error("Cannot write lighting quality report")
				passed = false
	print("YUGA_PRODUCTION_LIGHTING_QUALITY_CASES ", JSON.stringify({"passed":passed, "checks":checks.size()}))
	quit(0 if passed else 1)

func _plane(parent: Node3D, name_: String, height: float, size_: Vector2 = Vector2(44,50)) -> MeshInstance3D:
	var node := MeshInstance3D.new()
	node.name = name_
	var mesh := PlaneMesh.new()
	mesh.size = size_
	node.mesh = mesh
	node.position.y = height
	parent.add_child(node)
	return node

func _policy_counterexamples() -> void:
	var world := Node3D.new(); root.add_child(world)
	var authored := Node3D.new(); authored.name = "AuthoredLankaCourtyard"; world.add_child(authored)
	var floor_ := _plane(authored, "FLOOR_BEVEL_Courtyard_stone_0", 0)
	var material := StandardMaterial3D.new(); floor_.material_override = material
	var raised := _plane(authored, "FLOOR_BEVEL_Courtyard_stone_1", 2)
	var small := _plane(authored, "FLOOR_BEVEL_Courtyard_stone_2", 0, Vector2(1,1))
	var lookalike := _plane(authored, "FLOOR_BEVEL_Courtyard_stone_0_extra", 0)
	var wrong_parent := _plane(world, "FLOOR_BEVEL_Courtyard_stone_3", 0)
	var hero := _plane(world, "Rama", 0)
	check(Ground.apply_courtyard(world) == 1, "courtyard policy accepts only exact-path large flat ground")
	check(floor_.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_OFF, "courtyard exact ground casting disabled")
	check(floor_.visible and floor_.material_override == material, "courtyard policy preserves receiving material and visibility")
	for mesh in [raised, small, lookalike, wrong_parent, hero]:
		check(mesh.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_ON, "courtyard preserves raised/lookalike/hero caster " + mesh.name)
	check(Ground.apply_courtyard(world) == 1 and world.get_child_count() == 3 and authored.get_child_count() == 4, "courtyard policy idempotent without node changes")
	world.free()
	world = Node3D.new(); root.add_child(world)
	var paving := _plane(world, "FlatCityPaving", 0, Vector2(140,260))
	var apron := _plane(world, "NoncollidingTerrainApron", -.18, Vector2(180,300))
	raised = _plane(world, "RaisedLandingDeck", 3)
	lookalike = _plane(world, "FlatCityPavingExtra", 0)
	hero = _plane(world, "Rama", 0)
	var collision := StaticBody3D.new(); collision.name = "AuthorityFloor"; world.add_child(collision)
	check(Ground.apply_world(world) == 2, "world policy accepts exact paving and lowered apron")
	check(paving.cast_shadow == 0 and apron.cast_shadow == 0, "world flat receivers stop self shadowing")
	check(raised.cast_shadow == 1 and lookalike.cast_shadow == 1 and hero.cast_shadow == 1, "world preserves raised platform lookalike and hero casters")
	check(world.get_child_count() == 6 and collision.collision_layer == 1, "world policy preserves graph and collider settings")
	paving.position.y = 2; paving.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	check(Ground.apply_world(world) == 1 and paving.cast_shadow == 1, "world rejects raised mesh even with exact floor name")
	paving.position.y = 0
	var sun := DirectionalLight3D.new(); world.add_child(sun)
	var env := Environment.new(); var controller = Confluence.new()
	controller.configure(env, sun, world)
	check(paving.cast_shadow == 0, "world configure applies ground policy")
	paving.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	controller.set_phase(.5)
	check(paving.cast_shadow == 1, "world phase path does not rescan or mutate ground policy")
	controller.configure(env, sun, world)
	check(paving.cast_shadow == 0, "explicit world reconfigure reapplies ground policy")
	check(Ground.apply_world(null) == 0 and Ground.apply_courtyard(null) == 0, "ground policy invalid world guards")
	world.free()

func _materials(mesh: MeshInstance3D) -> Array:
	var result := [mesh.material_override]
	for index in mesh.mesh.get_surface_count(): result.append(mesh.get_active_material(index))
	return result

func _actual_receiver_checks() -> void:
	for path in ["res://scripts/courtyard.gd", "res://scripts/confluence_world.gd", "res://scenes/courtyard.tscn", "res://scenes/confluence_world.tscn", "res://assets/environment/lanka_courtyard.glb"]:
		receiver_sources[path] = FileAccess.get_sha256(path)
	for kind in ["courtyard", "confluence_world"]:
		var scene: Node3D = load("res://scenes/" + kind + ".tscn").instantiate()
		root.add_child(scene)
		# Let the actual scene complete its two deferred HUD layout passes before teardown.
		for frame_index in 3: await process_frame
		paused = true
		var world: Node3D = scene.world
		var paths: Array = []
		for name_ in (Ground.COURTYARD_NAMES if kind == "courtyard" else Ground.WORLD_NAMES):
			paths.append(("AuthoredLankaCourtyard/" if kind == "courtyard" else "") + name_)
		var selected := []
		var preserved := {}
		var collision_count := world.find_children("*", "CollisionShape3D", true, false).size()
		for path in paths:
			var mesh := world.get_node_or_null(path) as MeshInstance3D
			check(mesh != null and mesh.cast_shadow == 0, kind + " actual ground configured as shadow receiver " + path)
			if mesh != null:
				selected.append(mesh)
				preserved[mesh.get_instance_id()] = {"materials":_materials(mesh), "visible":mesh.visible, "transform":mesh.global_transform}
				mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		var other_casters := {}
		for mesh in world.find_children("*", "MeshInstance3D", true, false):
			if mesh not in selected: other_casters[mesh.get_instance_id()] = mesh.cast_shadow
		var count: int = Ground.apply_courtyard(world) if kind == "courtyard" else Ground.apply_world(world)
		check(count == paths.size(), kind + " policy matches exact current imported ground inventory")
		for mesh in selected:
			var old: Dictionary = preserved[mesh.get_instance_id()]
			check(mesh.cast_shadow == 0 and mesh.visible == old.visible and mesh.global_transform == old.transform and _materials(mesh) == old.materials, kind + " actual ground receives unchanged materials and geometry " + mesh.name)
		var unchanged := true
		for mesh in world.find_children("*", "MeshInstance3D", true, false):
			if mesh.get_instance_id() in other_casters and mesh.cast_shadow != other_casters[mesh.get_instance_id()]: unchanged = false
		check(unchanged, kind + " actual hero building raised-platform casters unchanged")
		check(world.find_children("*", "CollisionShape3D", true, false).size() == collision_count, kind + " actual collision graph unchanged")
		harness_cleanup.append(await _retire_scene_audio(scene))

func _retire_scene_audio(scene: Node3D) -> Dictionary:
	# Dummy AudioServer retires playback asynchronously. Fast headless frames can
	# otherwise exit after free() while the last music WAV is still mixer-owned.
	var playbacks: Array[WeakRef] = []
	for type_ in ["AudioStreamPlayer", "AudioStreamPlayer2D", "AudioStreamPlayer3D"]:
		for voice in scene.find_children("*", type_, true, false):
			if voice.playing:
				var playback = voice.get_stream_playback()
				if playback != null: playbacks.append(weakref(playback))
				playback = null
			voice.stop()
	var label := String(scene.name)
	paused = false
	scene.queue_free()
	await process_frame
	await process_frame
	var started := Time.get_ticks_msec()
	# Pausing already stops the music voice, so get_stream_playback() can be null
	# while AudioServer still owns its retiring buffer. Always allow a real mixer
	# buffer interval, including that stopped-before-sampling case.
	await create_timer(.1, true, false, true).timeout
	while playbacks.any(func(reference: WeakRef): return reference.get_ref() != null) and Time.get_ticks_msec() - started < 1000:
		await create_timer(.025).timeout
	return {"scene":label, "sampled_playbacks":playbacks.size(),
		"retired":not playbacks.any(func(reference: WeakRef): return reference.get_ref() != null),
		"wait_ms":Time.get_ticks_msec() - started, "minimum_mixer_wait_s":.1, "driver":AudioServer.get_driver_name()}
