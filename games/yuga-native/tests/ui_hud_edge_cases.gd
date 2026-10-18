extends SceneTree
## Existing world at valid vitals limits plus explicit long-copy layout fixtures.
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

func surface_errors() -> Array:
	var peers: Array[Control] = []
	var failures := []
	for child in scene.hud.get_children():
		if child is Control and child.is_visible_in_tree():
			peers.append(child)
			if not root.get_visible_rect().encloses(child.get_global_rect()): failures.append(str(child.name)+" outside")
	for first in peers.size():
		for second in range(first+1,peers.size()):
			if peers[first].get_global_rect().intersects(peers[second].get_global_rect()): failures.append(str(peers[first].name)+" / "+str(peers[second].name))
	return failures

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
	scene.rama_hud.set_process(false)
	scene.rama_runtime.set_volume(0)
	var hud: Control = scene.rama_hud
	var runtime: Node3D = scene.rama_runtime
	var vitals: Node = runtime.vitals
	scene.player.position = Vector3(0,.05,-60)
	var original_name: String = scene.manifest.lanes[1].name
	scene.manifest.lanes[1].name = "Temple avenue — a deliberately extended translated route description for narrow-window coverage"
	var contesting_actors := []
	for site in scene.relays.control._sites:
		site.label = "Long translated relay name "+str(site.id)+" Relay"
		for team in ["sun","moon"]:
			contesting_actors.append({"id":team+str(site.id),"team":team,"position":site.position,"alive":true})
	scene.relays.control.step(.1,contesting_actors)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		scene._update_practice_hud()
		await frames()
		var failures := surface_errors()
		record("Long route and all contested relay captions retain HUD geometry "+str(dimensions),failures.is_empty(),{"failures":failures,"title":str(scene.hud.get_node("TitleCard").get_global_rect()),"relay":str(scene.hud.get_node("RelayStatus").get_global_rect())})
		var state_visible := true
		for label in scene.relay_labels: state_visible = state_visible and label.text.contains("Contested") and scene.hud.get_node("RelayStatus").get_global_rect().encloses(label.get_global_rect())
		record("Every contested state stays in its own readable row "+str(dimensions),state_visible)
		runtime.notice = "Warning: return to open ground.\nExtra diagnostic detail.\nThird detail.\nFourth detail.\nFifth detail."
		hud._refresh()
		await frames()
		var bounds: Rect2 = hud.get_global_rect()
		var contents_fit := bounds.encloses(hud.status_panel.get_global_rect())
		for card in hud.slot_cards: contents_fit = contents_fit and bounds.encloses(card.get_global_rect())
		record("Dense multiline notices cannot displace health or ability slots "+str(dimensions),contents_fit,{"hud":str(bounds),"notice":str(hud.note.get_global_rect()),"status":str(hud.status_panel.get_global_rect())})
	scene.manifest.lanes[1].name = original_name
	scene.relays.reset()
	runtime.notice = "Rama is ready"
	var shield_ok: bool = vitals.apply_shield(vitals.MAX_SHIELD,1.0)
	hud._refresh()
	record("Maximum valid health and shield retain exact live values",shield_ok and hud.life.value==vitals.MAX_HEALTH and hud.life_text.text=="300 / 300 +100")
	var damage: Dictionary = vitals.receive_damage(1000,"ui_edge_defeat",vitals.generation,1)
	hud._process(1.0/60.0)
	record("Zero health uses actual defeat state and clears readiness",damage.accepted and hud.life.value==0 and hud.note.text=="RETURNING IN 3.0s" and not hud.slots.any(func(label): return label.text.contains("READY")))
	var dead_clock: float = vitals.elapsed
	scene.set_paused(true)
	for unused in range(12): hud._process(.1)
	record("Paused defeat readout preserves return clock",vitals.elapsed==dead_clock and hud.note.text=="RETURNING IN 3.0s")
	scene.set_paused(false)
	for unused in range(60): scene.army.step_simulation(.05)
	hud._process(1.0/60.0)
	record("Normal army ticks restore full life and retire defeat text",vitals.alive and hud.life.value==vitals.MAX_HEALTH and not hud.note.text.begins_with("RETURNING") and scene.player.active)
	scene._update_practice_hud()
	record("Maximum initial cores stay explicit after reset",scene.score_label.text.contains("Sun 100 / Moon 100"))
	scene.army.cores = {"sun":0.0,"moon":0.0}
	scene.army.step_simulation(.05)
	scene._update_practice_hud()
	record("Zero cores show the real draw and stopped relay state",scene.army.winner=="draw" and scene.outcome_summary.heading.text.contains("Draw") and scene.outcome_summary.detail.text.contains("Sun 0 / Moon 0") and scene.relay_hint.text.contains("stopped"))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless existing runtime and actual vitals/army ticks. Long route/relay labels and contested states are explicit presentation fixtures. No rendering, OS input, 2x scale or hardware claim.","sources":{}}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/world_outcome_summary.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
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
