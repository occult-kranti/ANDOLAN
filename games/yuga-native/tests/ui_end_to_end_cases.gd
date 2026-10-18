extends SceneTree
## Independent integrated input/lifecycle checks. No scene script is preloaded.
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool) -> void:
	checks.append({"name":label,"passed":passed})
	print("PASS " if passed else "FAIL ",label)

func frames(count: int = 3) -> void:
	for unused in range(count): await process_frame

func until(predicate: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 60000
	while Time.get_ticks_msec() < deadline:
		if predicate.call(): return true
		await process_frame
	return false

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		Input.parse_input_event(event)
		await frames()

func activate(button: BaseButton) -> void:
	# Move through the real tab chain, including scroll-to-focus behavior.
	for unused in range(50):
		if root.gui_get_focus_owner() == button:
			await key(KEY_ENTER)
			return
		await key(KEY_TAB)
	record("Keyboard can reach " + button.text, false)

func button(parent: Node, caption: String) -> Button:
	for candidate in parent.find_children("*","Button",true,false):
		if candidate.text == caption: return candidate
	return null

func scene(path: String) -> bool:
	var ready := await until(func(): return is_instance_valid(current_scene) and current_scene.scene_file_path == path)
	await frames()
	return ready

func loader() -> Control:
	return root.get_node("YugaSceneTransitionLayer/SceneTransition")

func _run() -> void:
	root.size = Vector2i(960,600)
	root.content_scale_size = Vector2i(960,600)
	record("Configured main scene is the light boot", ProjectSettings.get_setting("application/run/main_scene") == "res://scenes/boot.tscn")
	change_scene_to_file(ProjectSettings.get_setting("application/run/main_scene"))
	if not await scene("res://scenes/courtyard.tscn"):
		record("Configured boot reaches title",false)
		await finish()
		return
	var court := current_scene
	var transition := loader()
	record("Configured boot reaches usable title", court.main_panel.visible and not court.started and not transition.visible)
	await activate(court.main_panel.primary_button)
	if not await scene("res://scenes/confluence_world.tscn"):
		record("Keyboard primary enters Confluence",false)
		await finish()
		return
	var world := current_scene
	record("Keyboard primary enters real Confluence", world.world_ready and world.player.model_ready and not world.paused)
	await key(KEY_ESCAPE)
	record("World Escape opens pause", world.paused and world.pause_panel.visible)
	var return_button := button(world.pause_panel,"Return to courtyard")
	var missing_return := func(phase: StringName, _message: String, _progress: float):
		if phase == &"queued": transition._path = "res://scenes/independent-missing-return.tscn"
	transition.phase_changed.connect(missing_return)
	# Enter key dispatch activates the scene's real return handler.
	await activate(return_button)
	transition.phase_changed.disconnect(missing_return)
	# A private test-only path mutation causes actual ResourceLoader failure.
	# The public destination allowlist and all production files remain untouched.
	record("World return failure is recoverable", await until(func(): return transition.phase == &"error"))
	record("World and explicit processing are isolated during error", world.process_mode == Node.PROCESS_MODE_DISABLED and world.world.process_mode == Node.PROCESS_MODE_DISABLED and world.ui.process_mode == Node.PROCESS_MODE_DISABLED)
	var generation: int = transition.snapshot().attempt
	world.return_to_courtyard()
	record("Duplicate world return cannot start another attempt", transition.snapshot().attempt == generation)
	await key(KEY_ESCAPE)
	record("Back restores paused world and exact Return focus", current_scene == world and world.paused and paused and root.gui_get_focus_owner() == return_button and world.ui.process_mode == Node.PROCESS_MODE_ALWAYS and world.world.process_mode == Node.PROCESS_MODE_PAUSABLE)
	var old_world: WeakRef = weakref(world)
	await activate(return_button)
	record("World return uses threaded loader to restore title", await scene("res://scenes/courtyard.tscn"))
	court = current_scene
	record("Round trip disposes world and reuses loader", not is_instance_valid(old_world.get_ref()) and loader() == transition and not paused)
	await activate(court.main_panel.train_mode_button)
	await activate(court.main_panel.primary_button)
	record("Keyboard training starts player and HUD", court.started and court.player.active and court.hud.visible)
	await key(KEY_ESCAPE)
	record("Training Escape opens pause", paused and court.pause_panel.visible)
	await activate(button(court.pause_panel,"SETTINGS"))
	record("Pause settings remains paused", court.settings_panel.visible and paused)
	await activate(court.controls_button)
	record("Settings opens real controls dialog", court.controls_overlay.visible and paused)
	await key(KEY_ENTER)
	record("Keyboard activates binding capture", not court.controls_overlay.capture_action.is_empty())
	await key(KEY_ESCAPE)
	record("First Escape cancels capture without closing controls", court.controls_overlay.visible and court.controls_overlay.capture_action.is_empty() and paused)
	await key(KEY_ESCAPE)
	record("Second Escape returns to settings", not court.controls_overlay.visible and court.settings_panel.visible and paused)
	await key(KEY_ESCAPE)
	record("Third Escape returns to training pause", court.pause_panel.visible and not court.settings_panel.visible and paused)
	await activate(button(court.pause_panel,"RETURN TO TITLE"))
	record("Return to title ends training and restores selection", court.main_panel.visible and not court.started and court.main_panel.selected_mode == "train" and not paused)
	await activate(court.main_panel.film_button)
	record("Keyboard utility opens real film", await scene("res://scenes/combat_film.tscn"))
	var film := current_scene
	var was_playing: bool = film.playing
	# Freeze at the queued boundary via the real Return handler; then cancel by input.
	film.return_to_courtyard()
	record("Film return pauses playback before scene load", transition.phase == &"queued" and not film.playing)
	await key(KEY_ESCAPE)
	record("Cancelled film return restores playback", current_scene == film and film.playing == was_playing and not transition.visible)
	film.return_to_courtyard()
	root.focus_exited.emit()
	transition.cancel()
	record("Focus loss during cancelled return keeps film paused", current_scene == film and not film.playing)
	await key(KEY_ESCAPE)
	record("Film Escape returns through same loader", await scene("res://scenes/courtyard.tscn"))
	record("Entire path retains one transition layer", loader() == transition and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size() == 1)
	await finish()

func finish() -> void:
	paused = false
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var result := {"suite":"ui-independent-integrated-flow","passed":failures.is_empty(),"passed_count":checks.size()-failures.size(),"count":checks.size(),"failed":failures.size(),"checks":checks,"scope":"Existing-import native scenes; navigation primarily real Input.parse_input_event keyboard dispatch; explicit fault injection and film lifecycle calls are identified in source. Actual XTest/framebuffer gate is separate.","sources":{}}
	for path in ["project.godot","scripts/boot.gd","scripts/courtyard.gd","scripts/confluence_world.gd","scripts/combat_film.gd","scripts/scene_transition.gd","scripts/controls_overlay.gd","scripts/rama_hero_hud.gd","tests/ui_end_to_end_cases.gd"]:
		result.sources[path] = FileAccess.get_sha256("res://" + path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t")+"\n")
	print(JSON.stringify({"passed":result.passed,"failed":result.failed}))
	if is_instance_valid(current_scene): current_scene.queue_free()
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if layer: layer.queue_free()
	await frames()
	call_deferred("quit",0 if failures.is_empty() else 1)
