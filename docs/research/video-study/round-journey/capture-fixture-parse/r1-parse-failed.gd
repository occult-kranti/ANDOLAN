extends SceneTree
## Scripted hero-origin fixture; actual native result UI, not a human match.
## Run on an owned display after the shared render lane is available.
const STEP := .05
const MAX_SIMULATION_SECONDS := 1800.0
const MAX_SIMULATION_WALL_MS := 30000
const REQUIRED := ["res://scenes/confluence_world.tscn", "res://scripts/confluence_world.gd", "res://scripts/lane_army.gd", "res://scripts/lane_minion.gd", "res://scripts/rama_ability_kit.gd", "res://scripts/rama_hero_runtime.gd", "res://scripts/rama_vitals.gd", "res://scripts/rama_motion.gd", "res://scripts/combat_match_metrics.gd", "res://scripts/world_outcome_summary.gd", "res://scripts/native_field_shop.gd", "res://scripts/confluence_battle_hud.gd", "res://scripts/lanka_lane_gate.gd", "res://scripts/lanka_water_garden.gd", "res://scripts/sangam_district.gd", "res://scripts/ultimate_rules.gd", "res://assets/design/rama-ability-kit.json", "res://assets/world/confluence-map.json", "res://assets/heroes/rama-hero.glb"]
var output := ""
var capture_restart := false
var scene: Node3D
var sources_before := {}
var casts: Array[Dictionary] = []
var checkpoints: Array[Dictionary] = []
var images: Array[Dictionary] = []
var outcomes: Array[Dictionary] = []
var event_counts := {}
var ticks := 0
var simulation_wall_ms := 0
var failure := ""
var core_changes_follow_arrivals := true

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output = argument.trim_prefix("--output=")
		elif argument == "--restart": capture_restart = true
		else: failure = "Unknown argument: " + argument
	call_deferred("run")

func resource_identity(path: String) -> Dictionary:
	var value := {"logical_path":path,"raw_file_available":FileAccess.file_exists(path)}
	if FileAccess.file_exists(path): value["raw_sha256"] = FileAccess.get_sha256(path)
	var remap := path + ".remap"
	if FileAccess.file_exists(remap):
		value["remap_sha256"] = FileAccess.get_sha256(remap)
		var config := ConfigFile.new()
		if config.load(remap) == OK:
			var mapped := String(config.get_value("remap","path",""))
			value["mapped_path"] = mapped
			if FileAccess.file_exists(mapped): value["mapped_sha256"] = FileAccess.get_sha256(mapped)
	return value

func identities() -> Dictionary:
	var values := {}
	for path in REQUIRED: values[path] = resource_identity(path)
	var runner := get_script().resource_path
	values[runner] = resource_identity(runner)
	return values

func vector(value: Vector3) -> Array:
	return [value.x,value.y,value.z]

func candidate(team: String):
	var selected = null
	for unit in scene.army.units:
		if not unit.alive or unit.team != team or unit.lane_id != 1: continue
		if selected == null or unit.progress > selected.progress: selected = unit
	return selected

func bot_action() -> void:
	# Death and respawn remain the mounted runtime's real siege/vitals behavior.
	if not scene.rama_runtime.vitals.alive or scene.rama_runtime.suspended: return
	var state: Dictionary = scene.rama_kit.report()
	if state.action_locked: return
	var enemy = candidate("moon")
	var ally = candidate("sun")
	var id := ""
	var origin := Vector3.ZERO
	var target := Vector3.ZERO
	if enemy != null and float(state.cooldowns.dawn_volley) <= .000001:
		id = "dawn_volley"; origin = Vector3(enemy.position.x,.05,enemy.position.z-10); target = enemy.position
	elif enemy != null and float(state.cooldowns.piercing_dawn) <= .000001:
		id = "piercing_dawn"; origin = Vector3(enemy.position.x,.05,enemy.position.z-5); target = enemy.position
	elif ally != null and float(state.cooldowns.guardian_circle) <= .000001:
		id = "guardian_circle"; origin = Vector3(ally.position.x,.05,ally.position.z-4); target = ally.position
	if id.is_empty(): return
	# Move the actual player root so the original authored muzzle sampler remains
	# valid. teleport_to/reset would refresh the kit and are deliberately unused.
	scene.player.global_position = scene.army.to_global(origin)
	scene.player.velocity = Vector3.ZERO
	scene.player.yaw = PI
	scene.player.visual.rotation.y = 0
	scene.player._update_camera()
	scene.player.reset_physics_interpolation()
	var world_origin: Vector3 = scene.player.global_position
	var world_target: Vector3 = scene.army.to_global(target)
	var accepted: Dictionary = scene.rama_kit.request_ability(id,world_origin,Vector3(0,0,1),world_target)
	casts.append({"simulation_s":scene.army.elapsed,"ability_id":id,"actual_player_origin":vector(world_origin),"target":vector(world_target),"accepted":accepted.get("accepted",false),"reason":accepted.get("reason",""),"cast_id":accepted.get("cast_id",0)})

func draw_frames(count := 3) -> void:
	for unused in count:
		await process_frame
		await RenderingServer.frame_post_draw

func save_image(filename: String) -> bool:
	var image := root.get_texture().get_image()
	if image == null or image.is_empty(): failure = "Viewport image is empty"; return false
	var path := output.path_join(filename)
	if image.save_png(path) != OK: failure = "Could not save " + filename; return false
	images.append({"path":path,"sha256":FileAccess.get_sha256(path),"width":image.get_width(),"height":image.get_height(),"render_frame":Engine.get_frames_drawn(),"army_time_s":scene.army.elapsed})
	return true

func finish(success: bool, result: Dictionary = {}, restart: Dictionary = {}) -> void:
	var after := identities()
	if sources_before != after:
		success = false
		failure = "A selected resource changed during capture"
	var report := {"schema":1,"complete":success,"failure":failure,"scope":"Scripted hero-origin fixture; actual native result UI, not a normal human match. Actual mounted army/kit/metrics, original muzzle and siege/vitals callbacks. No core/unit health, route progress, winner, cooldown or reward injection. No human navigation/input, audio listening, online or physical-GPU performance claim.","engine":Engine.get_version_info().string,"engine_path":OS.get_executable_path(),"display":DisplayServer.get_name(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"capture_size":[root.size.x,root.size.y],"fixed_step_s":STEP,"ticks":ticks,"simulation_limit_s":MAX_SIMULATION_SECONDS,"simulation_wall_budget_ms":MAX_SIMULATION_WALL_MS,"simulation_wall_ms":simulation_wall_ms,"core_changes_follow_arrivals":core_changes_follow_arrivals,"resource_identity_before":sources_before,"resource_identity_after":after,"casts":casts,"ability_event_counts":event_counts,"outcomes":outcomes,"checkpoints_30s":checkpoints,"result":result,"restart":restart,"images":images,"audio_muted":true,"automatic_world_player_army_physics_disabled":true,"relay_clock_policy":"Automatic world physics is frozen; relay capture/supply is not advanced or injected by this fixture."}
	var file := FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"  ")+"\n")
	if not success: push_error(failure)
	paused = false
	if is_instance_valid(scene): scene.queue_free()
	await process_frame
	quit(0 if success else 1)

func run() -> void:
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or FileAccess.file_exists(output):
		push_error("Use a fresh absolute --output directory"); quit(1); return
	if DirAccess.make_dir_recursive_absolute(output) != OK: quit(1); return
	sources_before = identities()
	if not failure.is_empty(): await finish(false); return
	if DisplayServer.get_name() == "headless": failure = "Actual displayed renderer required; this fixture is parse-checkable headless only"; await finish(false); return
	root.size = Vector2i(1280,720)
	root.content_scale_size = root.size
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.title = "YUGA · Scripted round result capture"
	root.show()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	# Freeze clocks immediately after mount, before waiting for actual draws.
	scene.set_process(false)
	scene.set_physics_process(false)
	if not scene.world_ready:
		failure = "Mounted native world did not configure"; await finish(false); return
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.rama_effects.set_process(false)
	scene.set_paused(false)
	scene._set_volume(0,false)
	scene.rama_runtime.combat_event.connect(func(event: Dictionary): event_counts[event.kind] = int(event_counts.get(event.kind,0))+1)
	scene.army.outcome.connect(func(winner: String): outcomes.append({"winner":winner,"time_s":scene.army.elapsed,"cores":scene.army.cores.duplicate()}))
	await draw_frames()
	var started := Time.get_ticks_msec()
	while ticks < int(MAX_SIMULATION_SECONDS/STEP) and scene.army.winner.is_empty():
		if ticks%10 == 0: bot_action()
		var before_cores: Dictionary = scene.army.cores.duplicate()
		var arrivals_before: int = int(scene.army.core_arrivals[0])+int(scene.army.core_arrivals[1])+int(scene.army.core_arrivals[2])
		scene.army.step_simulation(STEP)
		ticks += 1
		if before_cores != scene.army.cores:
			var arrivals_after: int = int(scene.army.core_arrivals[0])+int(scene.army.core_arrivals[1])+int(scene.army.core_arrivals[2])
			core_changes_follow_arrivals = core_changes_follow_arrivals and arrivals_after>arrivals_before and scene.army.cores.sun<=before_cores.sun and scene.army.cores.moon<=before_cores.moon
		if ticks%600 == 0: checkpoints.append(scene.army.report())
		if ticks%100 == 0 and Time.get_ticks_msec()-started >= MAX_SIMULATION_WALL_MS:
			failure = "Bounded simulation wall budget reached before core outcome"; break
		# Sparse yields keep the render loop responsive without recording a movie.
		if ticks%1000 == 0: await process_frame
	simulation_wall_ms = Time.get_ticks_msec()-started
	var metrics: Dictionary = scene.match_metrics.report()
	var result := {"army":scene.army.report(),"metrics":metrics,"runtime":scene.rama_runtime.report(),"world_gate":scene.lanka_lane_gate_report,"world_garden":scene.lanka_water_garden_report,"world_sangam":scene.sangam_district_report}
	if scene.army.winner.is_empty() or not metrics.get("completed",false) or metrics.get("winner","") != scene.army.winner or not core_changes_follow_arrivals:
		if failure.is_empty(): failure = "Natural completed army/metrics outcome was not established"
		await finish(false,result); return
	scene._update_practice_hud()
	await draw_frames(2)
	scene._layout_pause_panel()
	await draw_frames(2)
	result["outcome_ui"] = {"visible":scene.outcome_summary.is_visible_in_tree(),"heading":scene.outcome_summary.heading.text,"detail":scene.outcome_summary.detail.text,"chart_visible":scene.outcome_summary.chart.is_visible_in_tree(),"pause_visible":scene.pause_panel.is_visible_in_tree(),"focus":str(root.gui_get_focus_owner().get_path()) if root.gui_get_focus_owner() else ""}
	if not save_image("01-natural-core-result.png"): await finish(false,result); return
	var restart := {}
	if capture_restart:
		scene._restart_army()
		scene.army.set_physics_process(false)
		scene.player.set_physics_process(false)
		scene._update_practice_hud()
		await draw_frames()
		restart = {"army":scene.army.report(),"metrics":scene.match_metrics.report(),"outcome_visible":scene.outcome_summary.is_visible_in_tree()}
		if not String(restart.army.winner).is_empty() or restart.metrics.get("completed",true) or restart.metrics.get("hero",{}).get("damage_dealt",-1)!=0 or restart.outcome_visible:
			failure = "Actual restart did not clear result/metrics"; await finish(false,result,restart); return
		if not save_image("02-real-restart.png"): await finish(false,result,restart); return
	await finish(true,result,restart)
