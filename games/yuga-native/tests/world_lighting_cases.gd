extends SceneTree
const Lighting = preload("res://scripts/world_lighting.gd")
var checks: Array[Dictionary] = []
func check(value: bool, label: String) -> void:
	checks.append({"id":label,"passed":value})
	if not value: push_error(label)
func _initialize() -> void:
	var world := Node3D.new()
	root.add_child(world)
	var sun := DirectionalLight3D.new()
	world.add_child(sun)
	var env := Environment.new()
	var controller = Lighting.new()
	var lights := []
	for i in range(20):
		lights.append({"id":"light-%02d" % i,"position":[i,1,0],"priority":i,"range":50,"day_energy":0.1,"night_energy":2.1})
	lights.append({"position":[NAN,1,0]})
	lights.append({"position":[1e308,1,0]})
	lights.append({"position":"bad"})
	controller.configure(env,sun,world,lights)
	var practicals := world.get_node("WorldPracticals")
	check(practicals.get_child_count() == 12,"practical budget")
	check(practicals.get_child(0).get_meta("placement_id") == "light-19","priority order")
	check(practicals.get_child(0).omni_range == 8.0,"range bounded")
	check(not practicals.get_child(0).shadow_enabled,"point shadow budget")
	check(sun.directional_shadow_max_distance == 72.0,"shadow distance")
	check(env.ambient_light_energy >= .3,"day fill visibility")
	var sky_id := env.sky.get_instance_id()
	for value in [0.0,0.25,0.5,0.75,1.0]:
		controller.set_phase(value)
		check(env.sky.get_instance_id() == sky_id,"no sky accumulation")
		check(env.ambient_light_energy >= .3,"night fill visibility")
	check(is_equal_approx(practicals.get_child(0).light_energy,2.1),"night practical energy")
	check(world.get_child_count() == 3,"sun one fill one practical root")
	check(world.get_node("WorldSkyFill").sky_mode == DirectionalLight3D.SKY_MODE_LIGHT_ONLY,"fill does not create second sky sun")
	controller.configure(env,sun,world,lights)
	check(practicals.get_child_count() == 12 and world.get_child_count() == 3,"reconfigure does not duplicate")
	controller.set_phase(NAN)
	check(controller.diagnostics().phase == 0.0,"nonfinite phase fallback")
	controller.set_phase(2.0)
	check(controller.diagnostics().phase == 1.0,"phase upper bound")
	controller.set_phase(-2.0)
	check(controller.diagnostics().phase == 0.0,"phase lower bound")
	var coast := Lighting.water_material("coast",false)
	var swamp := Lighting.water_material("swamp",true)
	check(coast.get_shader_parameter("animation_speed") > 0.0,"coast animation")
	check(swamp.get_shader_parameter("animation_speed") == 0.0,"reduced motion")
	check(coast.get_shader_parameter("base_roughness") < swamp.get_shader_parameter("base_roughness"),"swamp/coast difference")
	check(not env.volumetric_fog_enabled and not env.ssr_enabled and not env.sdfgi_enabled,"expensive effects disabled")
	Lighting.apply(null,sun,world)
	check(Lighting.configure_practicals(null,lights) == 0,"null guards")
	check(Lighting.configure_practicals(world,[{"position":[NAN,1,0]}, {"position":[1e308,1,0]}, {"position":"bad"}, {"position":[1,2]}, null]) == 0,"invalid positions excluded")
	controller.configure(env,sun,world,lights,false)
	check(not sun.shadow_enabled,"shadow setting honored")
	var passed := true
	for result in checks: passed = passed and result.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,
		"lighting_sha256":FileAccess.get_sha256("res://scripts/world_lighting.gd"),
		"shader_sha256":FileAccess.get_sha256("res://scripts/world_water.gdshader"),
		"ground_shader_sha256":FileAccess.get_sha256("res://scripts/world_ground.gdshader"),
		"ground_common_sha256":FileAccess.get_sha256("res://scripts/world_ground_common.gdshaderinc"),
		"test_sha256":FileAccess.get_sha256("res://tests/world_lighting_cases.gd"),
		"checks":checks,"diagnostics":controller.diagnostics(),
		"scope":"Godot resource, numeric-input and budget checks. No shader compilation, rendered color, shadow-artifact or frame-rate claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report,"\t") + "\n")
			else:
				push_error("Cannot write lighting report")
				passed = false
	print("YUGA_WORLD_LIGHTING_CASES ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	world.free()
	quit(0 if passed else 1)
