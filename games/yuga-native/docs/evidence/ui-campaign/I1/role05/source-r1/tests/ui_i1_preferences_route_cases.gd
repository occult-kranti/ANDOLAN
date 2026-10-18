extends SceneTree
## I1 fresh full-scene route contract. Native GUI dispatch is used for remap and
## effect toggles; slider/checkbox signals exercise real settings callbacks.
const Bindings := preload("res://scripts/input_bindings.gd")
var output := "/tmp/ui-i1-preferences-route.json"
var checks: Array[Dictionary] = []
var sources := {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(number := 5) -> void:
	for unused in number: await process_frame

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		root.push_input(event)
		await frames(2)

func checkbox(parent: Node, caption: String) -> CheckButton:
	for node in parent.find_children("*","CheckButton",true,false):
		if node.text==caption: return node
	return null

func wait_scene(path: String) -> bool:
	var deadline := Time.get_ticks_msec()+20000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		var loader := root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if is_instance_valid(loader) and loader.phase==&"error": return false
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path and (not is_instance_valid(loader) or loader.phase==&"done"):
			await frames()
			return true
	return false

func run() -> void:
	for path in ["res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/combat_film.gd","res://scripts/scene_transition.gd","res://scripts/input_bindings.gd","res://scripts/controls_overlay.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_hero_hud.gd","res://scripts/traversal_audio.gd","res://scripts/rama_action_audio.gd","res://assets/heroes/rama-hero.glb",get_script().resource_path]: sources[path]=FileAccess.get_sha256(path)
	var court: Node = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene = court
	await frames()
	court._open_settings(true)
	await frames()
	court.settings_panel.get_node("Card/Scroll/Content/Sensitivity").value = 1.65
	court.settings_panel.get_node("Card/Scroll/Content/Volume").value = .25
	checkbox(court.settings_panel,"Invert vertical aim").button_pressed = true
	checkbox(court.settings_panel,"Fullscreen").button_pressed = true
	checkbox(court.settings_panel,"Dynamic sun shadows").button_pressed = false
	checkbox(court.settings_panel,"Moonlit courtyard").button_pressed = true
	var saved: ConfigFile = Bindings.read_config().config
	check("real settings callbacks save control sound and display preferences",is_equal_approx(saved.get_value("controls","sensitivity",0),1.65) and saved.get_value("controls","invert_y",false) and is_equal_approx(saved.get_value("audio","volume",0),.25) and saved.get_value("video","fullscreen",false) and not saved.get_value("video","shadows",true) and saved.get_value("video","night",false))
	court._open_controls()
	court.controls_overlay.begin_capture("pulse")
	await key(KEY_J)
	check("native GUI remap saves and updates the actual action map",Bindings.label("pulse")=="J" and InputMap.action_get_events("pulse").any(func(event):return event is InputEventKey and event.physical_keycode==KEY_J) and court.controls_overlay.capture_action.is_empty())
	court.controls_overlay.close()
	court._close_settings()
	court._open_hero()
	await frames()
	court.hero_panel.reduced_effects_button.grab_focus()
	await key(KEY_ENTER)
	court.hero_panel.reduced_motion_button.grab_focus()
	await key(KEY_ENTER)
	check("actual guide receiver receives both saved reductions",court.rama_effects.report().reduced_effects and court.rama_effects.report().reduced_motion and court.hero_panel.ability_buttons.piercing_dawn.text.begins_with("J"))
	court.hero_panel.close()
	court.start_training()
	court.set_paused(true)
	court._open_settings(false)
	court.settings_panel.get_node("Card/Scroll/Content/Volume").value = 0
	check("paused training mute reaches live action audio",paused and court.rama_runtime.action_audio.report().volume==0 and court.rama_runtime.action_audio.report().playing==0)
	court._close_settings()
	check("settings Done restores training pause without losing preferences",paused and court.pause_panel.visible and is_equal_approx(court.player.sensitivity,.0024*1.65) and court.player.invert_y)
	court.return_to_menu()
	var old_court: WeakRef = weakref(court)
	court.enter_confluence()
	var arrived := await wait_scene("res://scenes/confluence_world.tscn")
	check("actual asynchronous route enters world and frees old courtyard",arrived and old_court.get_ref()==null)
	if not arrived:
		await finish()
		return
	var world: Node = current_scene
	check("world loads saved aim and key preferences",is_equal_approx(world.player.sensitivity,.0024*1.65) and world.player.invert_y and Bindings.label("pulse")=="J")
	check("world mute reaches traversal siege action and invocation audio",world.audio.volume==0 and world.siege_effects.report().volume==0 and world.rama_runtime.action_audio.report().volume==0 and world.invocation_audio.report().volume==0)
	world._open_rama_panel()
	await frames()
	check("world guide loads saved reductions and remapped ability label",world.rama_panel.reduced_effects_button.button_pressed and world.rama_panel.reduced_motion_button.button_pressed and world.rama_effects.report().reduced_effects and world.rama_effects.report().reduced_motion and world.rama_panel.ability_buttons.piercing_dawn.text.begins_with("J"))
	world.rama_panel.close()
	world.set_paused(true)
	world.pause_panel.find_child("WorldVolume",true,false).value = .55
	check("world sound callback saves one value across all active receivers",is_equal_approx(world.audio.volume,.55) and is_equal_approx(world.rama_runtime.action_audio.report().volume,.55) and is_equal_approx(Bindings.read_config().config.get_value("audio","volume",0),.55))
	var old_world: WeakRef = weakref(world)
	world.return_to_courtyard()
	arrived = await wait_scene("res://scenes/courtyard.tscn")
	check("actual world return retires old owner and restores title",arrived and old_world.get_ref()==null and not paused and current_scene.main_panel.visible)
	if not arrived:
		await finish()
		return
	court = current_scene
	check("returned courtyard loads world sound and preserves display preferences",is_equal_approx(court.volume,.55) and is_equal_approx(court.rama_runtime.action_audio.report().volume,.55) and court.full_screen and not court.shadows and court.night and court.invert_y and is_equal_approx(court.sensitivity,1.65))
	court._open_settings(true)
	court._open_controls()
	check("returned controls retain the saved key label",court.controls_overlay.binding_buttons.pulse.text.contains("J") and Bindings.label("pulse")=="J")
	court.controls_overlay.close()
	court._close_settings()
	var saved_bytes := FileAccess.get_sha256(Bindings.SAVE_PATH)
	court.enter_combat_film()
	arrived = await wait_scene("res://scenes/combat_film.tscn")
	check("actual film route preserves preferences bytes",arrived and FileAccess.get_sha256(Bindings.SAVE_PATH)==saved_bytes)
	if not arrived:
		await finish()
		return
	current_scene.return_to_courtyard()
	arrived = await wait_scene("res://scenes/courtyard.tscn")
	check("actual film return preserves saved settings and displayed sound",arrived and FileAccess.get_sha256(Bindings.SAVE_PATH)==saved_bytes and is_equal_approx(current_scene.volume,.55) and current_scene.full_screen and Bindings.label("pulse")=="J")
	await finish()

func finish() -> void:
	var stable := true
	for path in sources: stable = stable and FileAccess.get_sha256(path)==sources[path]
	check("combined settings route sources remain unchanged",stable)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":sources,"settings_sha256":FileAccess.get_sha256(Bindings.SAVE_PATH),"display_backend":DisplayServer.get_name(),"scope":"I1 newly executed actual courtyard training/world/film route and return callbacks; native GUI dispatch for remap/toggles and real settings signals. Isolated XDG save. Fullscreen/shadows/night persistence and live audio volume values only; headless does not apply OS fullscreen or establish audible/rendered quality."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused = false
	if is_instance_valid(current_scene): current_scene.queue_free()
	current_scene = null
	await frames(8)
	OS.delay_msec(100)
	await process_frame
	quit(0 if result.passed else 1)
