extends SceneTree
## Reversible-resource and allocation checks. These do not qualify final art.
const Atmosphere = preload("res://scripts/hero_atmosphere.gd")
const Production = preload("res://scripts/production_lighting.gd")
var checks: Array[Dictionary] = []

func _initialize() -> void:
	call_deferred("_run")

func check(value: bool, id: String) -> void:
	checks.append({"id": id, "passed": value})
	if not value: push_error(id)

func _fixture() -> Dictionary:
	var world := Node3D.new()
	root.add_child(world)
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var portrait := OmniLight3D.new()
	portrait.name = "HeroPortraitFill"
	world.add_child(portrait)
	var practical := OmniLight3D.new()
	practical.name = "ExistingDiya"
	world.add_child(practical)
	var env := Environment.new()
	Production.apply(env, sun, world)
	return {"world": world, "sun": sun, "env": env, "portrait": portrait,
		"fill": world.get_node("CoolSkyFill"), "practical": practical}

func _snapshot(fixture: Dictionary) -> Dictionary:
	var result := {}
	for entry in [["env", Atmosphere.ENVIRONMENT_PROPERTIES],
		["sun", Atmosphere.SUN_PROPERTIES], ["fill", Atmosphere.FILL_PROPERTIES],
		["portrait", Atmosphere.FILL_PROPERTIES]]:
		var properties := {}
		for property in entry[1]: properties[property] = fixture[entry[0]].get(property)
		result[entry[0]] = properties
	var sky := {}
	for property in Atmosphere.SKY_PROPERTIES:
		sky[property] = fixture.env.sky.sky_material.get(property)
	result["sky"] = sky
	return result

func _run() -> void:
	var f := _fixture()
	var original := _snapshot(f)
	var original_count: int = f.world.get_child_count()
	var practical_energy: float = f.practical.light_energy
	var practical_color: Color = f.practical.light_color
	var original_sun_id: int = f.sun.get_instance_id()
	var original_sky_id: int = f.env.sky.get_instance_id()
	var controller = Atmosphere.new()
	check(not controller.set_mode("day"), "unbound mode refused")
	check(not controller.configure(null, f.env, f.sun), "null world refused")
	check(not controller.configure(f.world, null, f.sun), "null environment refused")
	check(not controller.configure(f.world, f.env, null), "null sun refused")
	var foreign_sun := DirectionalLight3D.new()
	root.add_child(foreign_sun)
	check(not controller.configure(f.world, f.env, foreign_sun), "foreign scene sun refused")
	foreign_sun.free()
	check(_snapshot(f) == original, "invalid configure makes no changes")
	check(controller.configure(f.world, f.env, f.sun), "configure production day")
	var day := _snapshot(f)
	check(day != original, "day applies actual owned properties")
	check(f.world.get_child_count() == original_count, "day adds no nodes")
	check(f.sun.get_instance_id() == original_sun_id and f.env.sky.get_instance_id() == original_sky_id, "existing light and sky resources retained")
	# G2 reduces only the day opposing fill to recover form; night keeps .36.
	check(is_equal_approx(f.fill.light_energy, 0.32), "training gets opposing diffuse fill without portrait")
	check(f.env.ambient_light_energy >= 0.30 and f.env.ambient_light_energy <= 0.32001, "day visibility floor retained")
	check(f.env.fog_density <= 0.00135, "day near silhouette haze restrained")
	check(f.env.sky.sky_material.sky_horizon_color == f.env.sky.sky_material.ground_horizon_color,
		"day upper and lower horizon share color")
	check(f.env.sky.sky_material.sky_energy_multiplier == f.env.sky.sky_material.ground_energy_multiplier,
		"day equal horizon radiance multipliers prevent an energy step")
	check(f.env.reflected_light_source == Environment.REFLECTION_SOURCE_SKY,
		"reflection source remains the production sky")
	check(f.env.glow_bloom == 0.0 and f.env.glow_hdr_threshold >= 2.09999, "no broad glow veil")
	check(f.env.ssao_radius <= 0.28001 and f.env.ssao_light_affect <= 0.10001, "AO restricted to contact scale")
	check(not f.fill.shadow_enabled and not f.portrait.shadow_enabled, "existing unshadowed fills preserved")
	check(f.practical.light_energy == practical_energy and f.practical.light_color == practical_color, "scene practical untouched")
	check(controller.configure(f.world, f.env, f.sun), "identical reconfigure allowed")
	check(_snapshot(f) == day, "identical reconfigure deterministic")
	check(controller.set_mode("neutral") and _snapshot(f) == original, "repeat configure keeps original neutral baseline")
	check(is_equal_approx(f.env.sky.sky_material.ground_energy_multiplier, 0.5),
		"neutral restores original ground hemisphere energy")
	check(controller.set_mode("night"), "night comparison selectable")
	check(f.env.ambient_light_energy >= 0.31999 and f.fill.light_energy >= 0.35999, "night face visibility floor")
	check(f.env.sky.sky_material.sky_horizon_color == f.env.sky.sky_material.ground_horizon_color
		and f.env.sky.sky_material.sky_energy_multiplier == f.env.sky.sky_material.ground_energy_multiplier,
		"night horizon color and radiance multipliers agree")
	check(controller.set_mode("day") and _snapshot(f) == day, "day-night-day exact repeat")
	check(not controller.set_mode("invalid") and _snapshot(f) == day, "unknown mode atomic refusal")
	var another := _fixture()
	var another_original := _snapshot(another)
	check(not controller.configure(another.world, another.env, another.sun), "rebind requires explicit restore")
	check(_snapshot(another) == another_original, "refused rebind preserves new scene")
	another.world.free()
	# Upstream settings must write first. Configure captures those fresh values,
	# while settings fields outside our ownership retain the user's preferences.
	Production.apply(f.env, f.sun, f.world, true, false)
	var upstream_night := _snapshot(f)
	# Production does not write specular coefficients. They remain owned by
	# this overlay until neutral/restore, so the real baseline keeps defaults.
	for label in ["sun", "fill", "portrait"]:
		upstream_night[label].light_specular = original[label].light_specular
	check(controller.configure(f.world, f.env, f.sun, true), "configure after upstream night settings")
	check(not f.sun.shadow_enabled, "shadow off remains honored")
	check(controller.set_mode("neutral") and _snapshot(f) == upstream_night, "neutral follows latest upstream night baseline")
	check(controller.set_mode("day"), "comparison resumes after neutral")
	f.env.fog_density = 0.007
	var changed := _snapshot(f)
	check(not controller.set_mode("night"), "foreign property write requires reconfigure")
	check(_snapshot(f) == changed, "foreign change refuses mode atomically")
	var restore_receipt: Dictionary = controller.restore()
	check(not restore_receipt.passed and restore_receipt.conflicts == ["environment:fog_density"], "restore reports exact foreign property")
	check(is_equal_approx(f.env.fog_density, 0.007), "restore preserves newer foreign value")
	check(not controller.diagnostics().bound and controller.diagnostics().mode == "unbound", "restore releases scene")
	check(controller.restore().passed, "second restore is safe")
	Production.apply(f.env, f.sun, f.world)
	original = _snapshot(f)
	check(controller.configure(f.world, f.env, f.sun), "rebind after restore")
	check(controller.restore().passed and _snapshot(f) == original, "full exact restore without conflict")
	check(f.world.get_child_count() == original_count, "all modes preserve allocation budget")
	check(controller.diagnostics().added_lights == 0 and controller.diagnostics().per_frame_updates == 0, "diagnostics records zero new light and update budget")
	# An exchanged sky must not cause writes into stale detached resources.
	check(controller.configure(f.world, f.env, f.sun), "configure before sky exchange")
	var replacement := Sky.new()
	replacement.sky_material = ProceduralSkyMaterial.new()
	f.env.sky = replacement
	check(not controller.set_mode("night"), "exchanged sky refuses mode")
	check(not controller.configure(f.world, f.env, f.sun), "exchanged sky requires restore")
	controller.restore()
	check(f.env.sky == replacement, "restore preserves replacement sky identity")
	# Scene teardown leaves no callback and cannot dereference freed lights.
	check(controller.configure(f.world, f.env, f.sun), "configure replacement sky after restore")
	f.world.free()
	check(not controller.set_mode("night"), "freed scene refuses mode")
	restore_receipt = controller.restore()
	check(not restore_receipt.passed and not controller.diagnostics().bound, "freed scene restore releases controller and reports missing nodes")
	var passed := true
	for result in checks: passed = passed and result.passed
	var report := {"passed": passed, "checks": checks,
		"engine": Engine.get_version_info().string,
		"source_sha256": FileAccess.get_sha256("res://scripts/hero_atmosphere.gd"),
		"test_sha256": FileAccess.get_sha256("res://tests/hero_atmosphere_cases.gd"),
		"scope": "headless resource ownership, comparison/reconfiguration, teardown and allocation; visual quality remains subject to matched actual renders"}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var output := FileAccess.open(argument.trim_prefix("--report="), FileAccess.WRITE)
			if output: output.store_string(JSON.stringify(report, "\t") + "\n")
			else: passed = false
	print("YUGA_HERO_ATMOSPHERE_CASES ", JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)
