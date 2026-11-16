extends SceneTree
## Mounted flow, actual authority effects and logical geometry; no hardware claim.
var scene: Node3D
var checks: Array[Dictionary] = []
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)
func frames(count := 6) -> void:
	for unused in count: await process_frame
func key(code: int) -> void:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	Input.parse_input_event(event)
	await frames(2)
	event.pressed = false
	Input.parse_input_event(event)
	await frames(2)
func run() -> void:
	root.size = Vector2i(1180,650)
	root.content_scale_size = root.size
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.army.set_physics_process(false)
	scene.player.set_physics_process(false)
	check("Configured mounted shop exposes its actual allowance", scene.world_ready and scene.field_shop.report().wallet == 120)
	await key(KEY_F4)
	check("F4 opens live shop and releases gameplay input", scene.field_shop_panel.visible and not scene.player.active and not paused and not scene.rama_runtime.suspended and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	var panel: Control = scene.field_shop_panel
	check("First open at1180 keeps receipt and Return inside the canvas",root.get_visible_rect().encloses(panel.panel.get_global_rect()) and root.get_visible_rect().encloses(panel.receipt.get_global_rect()) and root.get_visible_rect().encloses(panel.close_button.get_global_rect()),{"panel":str(panel.panel.get_global_rect()),"receipt":str(panel.receipt.get_global_rect()),"close":str(panel.close_button.get_global_rect())})
	var before: float = scene.army.elapsed
	scene.army.step_simulation(.05)
	check("Army clock continues while shopping", is_equal_approx(scene.army.elapsed,before + .05))
	scene.army.siege_event.emit({"kind":"impact","team":"moon","id":900001,"target":scene.player.global_position,"radius":3.0,"damage":60.0})
	check("Enemy siege impact still damages Rama while shop stops input", scene.rama_runtime.vitals.health == 240)
	scene.field_shop_panel.refresh()
	scene.field_shop_panel.rows.heal.button.pressed.emit()
	check("Real buy button spends gold and restores actual health", scene.field_shop.report().wallet == 85 and scene.rama_runtime.vitals.health == 300 and scene.field_shop_panel.receipt.text.contains("Purchased"), scene.field_shop_panel.report())
	await key(KEY_ESCAPE)
	check("Escape closes shop and restores active world", not scene.field_shop_panel.visible and scene.player.active and not paused)
	await key(KEY_F4)
	scene._focus_lost()
	check("Focus loss retires shop before pausing", not scene.field_shop_panel.visible and paused and not scene.player.active)
	scene.set_paused(false)
	await key(KEY_F4)
	scene.rama_runtime.vitals.receive_damage(1000,"shop defeat",scene.rama_runtime.vitals.generation,0)
	for unused in 61: scene.army.step_simulation(.05)
	check("Respawn does not capture input under an open shop", scene.rama_runtime.vitals.alive and scene.field_shop_panel.visible and not scene.player.active and Input.mouse_mode == Input.MOUSE_MODE_VISIBLE)
	scene._restart_army()
	check("Restart closes shop and resets wallet with the army", not scene.field_shop_panel.visible and scene.field_shop.report().wallet == 120 and scene.player.active and not paused)
	for dimensions in [Vector2i(1180,650),Vector2i(1280,720),Vector2i(1600,900)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		scene._layout_world_hud()
		await frames()
		var peers: Array[Control] = [scene.hud.get_node("TitleCard"),scene.hud.get_node("ControlsCard"),scene.hud.get_node("RelayStatus"),scene.hud.get_node("TraversalStatus"),scene.map_control,scene.rama_hud,scene.battle_hud.top,scene.battle_hud.shop_button]
		var errors := []
		for first in peers.size():
			if not root.get_visible_rect().encloses(peers[first].get_global_rect()): errors.append(str(peers[first].name) + " outside")
			for second in range(first+1,peers.size()):
				if peers[first].get_global_rect().intersects(peers[second].get_global_rect()): errors.append(str(peers[first].name)+"/"+str(peers[second].name))
		check("Wide dashboard and existing HUD stay separate " + str(dimensions),scene.battle_hud.visible and errors.is_empty(),{"errors":errors})
	for scale in [1.0,1.5,2.0]:
		root.size = Vector2i(960,540)
		root.content_scale_size = Vector2i(1280,720)
		root.content_scale_factor = scale
		await frames()
		scene._open_field_shop()
		await frames()
		var shop: Control = scene.field_shop_panel
		check("Shop panel stays on logical canvas at scale " + str(scale),root.get_visible_rect().encloses(shop.panel.get_global_rect()) and shop.panel.get_global_rect().encloses(shop.close_button.get_global_rect()),{"panel":str(shop.panel.get_global_rect()),"canvas":str(root.get_visible_rect())})
		await key(KEY_ESCAPE)
		check("Keyboard return works at scale " + str(scale),not shop.visible and scene.player.active)
	root.content_scale_factor = 1.0
	scene._restart_army()
	scene.army.step_simulation(.05)
	scene._open_field_shop()
	scene.army.cores = {"sun":100.0,"moon":0.0}
	scene.army.step_simulation(.05)
	scene._update_practice_hud()
	check("Authority outcome closes shop and presents actual recorded result",not scene.field_shop_panel.visible and paused and scene.outcome_summary.visible and scene.outcome_summary.detail.text.contains("Rama") and scene.match_metrics.report().completed)
	scene._restart_army()
	scene._update_practice_hud()
	check("Result restart clears metrics and retires summary",not scene.outcome_summary.visible and not scene.match_metrics.report().completed and scene.field_shop.report().wallet == 120)
	scene._open_field_shop()
	var state: Dictionary = scene.field_shop.report()
	scene.player.position = Vector3(0,.05,0)
	scene.field_shop_panel.refresh()
	check("Out of range services explain eligibility and cannot spend",scene.field_shop_panel.rows.ward.button.disabled and not scene.field_shop.purchase("ward",state.epoch,12345).accepted and scene.field_shop.report().wallet == state.wallet)
	scene.field_shop_panel.close()
	var passed := checks.all(func(row):return row.passed)
	var report := {"passed":passed,"checks":checks,"scope":"Mounted headless input, real local effects and logical geometry. Actual rendered readability is a separate receipt."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"\t"))
	paused = false
	scene.queue_free()
	await frames()
	quit(0 if passed else 1)
