extends SceneTree
## Read-only presentation against actual world, army and relay rules.
const Rules = preload("res://scripts/relay_control.gd")
var checks: Array[Dictionary] = []
var output := ""
var scene: Node3D

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(6): await process_frame

func _run() -> void:
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.set_paused(false)
	scene.set_process(false)
	scene.set_physics_process(false)
	scene.player.set_physics_process(false)
	scene.army.set_physics_process(false)
	scene.rama_runtime.set_volume(0)
	scene.player.position = Vector3(0,.05,-60)
	scene._update_practice_hud()
	record("Lane goal names the actual nearby route and current population",scene.lane_label.text.contains("Temple avenue") and scene.lane_label.text.contains("%d troops" % scene.army.report().alive_by_lane[1]) and scene.objective_label.text.contains("Moon core"))
	scene.player.position = Vector3(-40,.05,0)
	scene._update_practice_hud()
	record("Moving lanes updates the goal without choosing a fake objective",scene.lane_label.text.contains("Ghat promenade") and not scene.outcome_summary.visible)
	var authority: Dictionary = scene.army.report()
	var relay_state: Dictionary = scene.relays.control.report()
	for unused in range(10): scene._update_practice_hud()
	record("Formatting never advances army or relay authority",scene.army.report()==authority and scene.relays.control.report()==relay_state)
	record("Core values are explicitly labeled and taken from the real army",scene.score_label.text.contains("Cores · Sun %d / Moon %d" % [authority.cores.sun,authority.cores.moon]))
	var atlas: Control = scene.map_control
	var legend: Label = atlas.get_node("AtlasLegend")
	record("Overview shortcut is discoverable beside the fixed-orientation map",legend.text.contains("F1 overview") and atlas.project(Vector3(0,0,-120)).y < atlas.project(Vector3(0,0,120)).y)
	# Stage actors through the real fixed-step relay rules, not UI-only states.
	scene.player.position = Vector3(0,.05,0)
	scene.relays.control.reset()
	var allies := [{"id":"ui-hero","team":"sun","position":Vector3.ZERO,"alive":true}]
	for unused in range(32): scene.relays.control.step(.25,allies)
	for unused in range(5): scene.relays.control.step(.25,allies)
	var site: Dictionary = scene.relays.sites()[1]
	scene._update_relay_hud()
	var next_supply := "%.1fs" % maxf(0,Rules.SUPPLY_PERIOD-float(site.supply_clock))
	record("Held relay displays the actual remaining supply clock",site.owner=="sun" and scene.relay_hint.text.contains(next_supply),{"hint":scene.relay_hint.text,"clock":site.supply_clock})
	var mixed := allies + [{"id":"ui-enemy","team":"moon","position":Vector3.ZERO,"alive":true}]
	scene.relays.control.step(.1,mixed)
	scene._update_relay_hud()
	record("Contested relay replaces supply countdown with actionable state",scene.relays.sites()[1].contested and scene.relay_hint.text.begins_with("Contested") and not scene.relay_hint.text.contains("next supply"))
	for dimensions in [Vector2i(960,540),Vector2i(960,600),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		var peers: Array[Control] = []
		var failures := []
		var rectangles := {}
		for child in scene.hud.get_children():
			if child is Control and child.is_visible_in_tree():
				peers.append(child)
				rectangles[String(child.name)] = str(child.get_global_rect())
				if not root.get_visible_rect().encloses(child.get_global_rect()): failures.append(str(child.name)+" outside")
		for first in peers.size():
			for second in range(first+1,peers.size()):
				if peers[first].get_global_rect().intersects(peers[second].get_global_rect()): failures.append(str(peers[first].name)+" / "+str(peers[second].name))
		record("HUD goals, map and controls fit without sibling overlap "+str(dimensions),failures.is_empty(),{"failures":failures,"rectangles":rectangles})
		record("Goal and overview legend remain contained "+str(dimensions),scene.objective_label.get_parent().get_global_rect().encloses(scene.objective_label.get_global_rect()) and atlas.get_global_rect().encloses(legend.get_global_rect()),{"goal":str(scene.objective_label.get_global_rect()),"stack":str(scene.objective_label.get_parent().get_global_rect()),"atlas":str(atlas.get_global_rect()),"legend":str(legend.get_global_rect())})
	for winner in ["sun","moon","draw"]:
		scene.army.reset()
		scene.set_paused(false)
		scene.army.cores = {"sun":0.0 if winner in ["moon","draw"] else 100.0,"moon":0.0 if winner in ["sun","draw"] else 100.0}
		scene.army.step_simulation(.05)
		scene._update_practice_hud()
		record("Actual terminal tick produces visible "+winner+" summary",scene.army.winner==winner and scene.paused and paused and scene.outcome_summary.is_visible_in_tree() and scene.objective_label.text.contains(scene.outcome_summary.heading.text) and scene.outcome_summary.detail.text.contains("Restart lane practice"))
		var terminal: Dictionary = scene.army.report()
		scene._update_practice_hud()
		record("Terminal presentation preserves authority for "+winner,scene.army.report()==terminal and scene.relay_hint.text.contains("stopped"))
	scene._restart_army()
	scene._update_practice_hud()
	record("Restart retires terminal summary and restores lane goal",scene.army.winner.is_empty() and not scene.outcome_summary.visible and scene.objective_label.text.contains("Escort Sun troops"))
	scene._start_siege_practice()
	scene._update_practice_hud()
	record("Siege goal reflects actual drill with inactive relays",scene.army.siege_drill and scene.objective_label.text.contains("enemy engines") and scene.relay_hint.text.contains("inactive") and scene.map_control.relays.is_empty())
	var all_engines := 0
	var enemy_engines := 0
	for unit in scene.army.minimap_units():
		if unit.get("role", "") in ["cannon_cart", "royal_chariot"]:
			all_engines += 1
			if unit.get("team", "") == "moon": enemy_engines += 1
	var siege_authority: Dictionary = scene.army.report()
	scene._update_practice_hud()
	record("Siege counter identifies two enemy engines without mixing four allied and enemy engines",enemy_engines == 2 and all_engines == 4 and scene.score_label.text == "Siege %d enemies · Gold %d" % [enemy_engines, siege_authority.gold] and scene.army.report() == siege_authority,{"enemy_engines":enemy_engines,"all_engines":all_engines,"score":scene.score_label.text})
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless existing world and read-only presentation. Relay actors and terminal cores are staged through actual rule ticks. Logical layout at 960x540/960x600/1280x720; no OS input, rendered, 2x scale or hardware claim.","sources":{}}
	for path in ["res://scripts/confluence_world.gd","res://scripts/world_outcome_summary.gd","res://scripts/world_atlas.gd","res://scripts/hero_ui_theme.gd","res://scripts/lane_army.gd","res://scripts/relay_control.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	paused = false
	scene.queue_free()
	current_scene = null
	await frames()
	OS.delay_msec(80)
	await process_frame
	quit(0 if passed else 1)
