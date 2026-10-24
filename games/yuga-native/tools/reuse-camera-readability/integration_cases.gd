extends SceneTree
## Existing Confluence lifecycle calls with arranged occlusion; no render/input claim.
var world: Node3D
var checks: Array = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check_(label: String, passed_: bool, details = {}) -> void:
	checks.append({"name":label,"passed":passed_,"details":details})

func stage() -> void:
	world.player.camera.current = true
	world.player.active = true
	world.player.camera.global_position = world.player.global_position+Vector3(0,1.4,3)
	world.player.camera.look_at(world.player.global_position+Vector3.UP*1.25)
	var ally: Node3D
	for unit in world.army.units:
		unit.set_process(false)
		if ally == null and unit.team == "sun" and unit.role == "spearman": ally = unit
	ally.global_position = world.player.global_position+Vector3(0,0,1.5)
	ally.previous_position = ally.position; ally.heading = 0.0; ally.previous_yaw = 0.0; ally.update_pose(0.0,1.0)
	for index in range(6): world._process(.05)
	check_("ordinary_world_process_applies_fade",world.friendly_camera_visibility_report().faded_units >= 1,world.friendly_camera_visibility_report(true))

func run() -> void:
	world = load("res://scenes/confluence_world.tscn").instantiate(); root.add_child(world); current_scene = world
	while not world.world_ready or not world.player.model_ready: await process_frame
	for unused in 8: await physics_frame
	world.set_process(false); world.set_physics_process(false)
	world.player.set_process(false); world.player.set_physics_process(false); world.army.set_physics_process(false)
	stage()
	world.set_paused(true)
	check_("pause_restores_before_paused_process_can_stop",world.friendly_camera_visibility_report().cached_units == 0 and paused)
	world.set_paused(false); stage()
	world.set_overview(true)
	check_("overview_restores_before_camera_switch",world.friendly_camera_visibility_report().cached_units == 0 and world.review_camera.current)
	world.set_overview(false); stage()
	world.army.reset()
	check_("actual_army_reset_signal_releases_cache",world.friendly_camera_visibility_report().cached_units == 0)
	stage(); world.teleport_to(Vector3(0,.05,-100))
	check_("actual_teleport_restores_immediately",world.friendly_camera_visibility_report().cached_units == 0)
	stage(); world._restart_army()
	check_("actual_restart_releases_old_units",world.friendly_camera_visibility_report().cached_units == 0)
	stage()
	var helper = world.friendly_camera_visibility
	current_scene = null; world.free()
	check_("scene_exit_releases_weak_geometry_cache",helper.report().cached_units == 0 and not paused)
	var pins := {}; for path in ["res://scripts/confluence_world.gd","res://scripts/friendly_camera_visibility.gd",get_script().resource_path]: pins[path] = FileAccess.get_sha256(path)
	var report := {"passed":checks.all(func(value):return value.passed),"checks":checks,"source_sha256":pins,
		"scope":"Actual existing Confluence lifecycle and normal _process entry, with arranged camera/ally positions; headless, not ordinary player input or image evidence"}
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify({"passed":report.passed,"checks":checks.size(),"failures":checks.filter(func(value):return not value.passed)}))
	quit(0 if report.passed else 1)
