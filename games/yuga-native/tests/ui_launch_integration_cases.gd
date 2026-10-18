extends SceneTree
## Real imported courtyard/film nodes; missing-resource injection touches no asset.
const LaunchShell = preload("res://scripts/launch_shell.gd")
var checks: Array[Dictionary] = []
var output := ""
var phases: Array[String] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _frames(count: int = 5) -> void:
	for unused in range(count): await process_frame

func _scene(path: String) -> bool:
	for unused in range(240):
		if is_instance_valid(current_scene) and current_scene.scene_file_path == path:
			await _frames()
			return true
		await process_frame
	return false

func _phase(loader: Control, phase: StringName) -> bool:
	for unused in range(180):
		if loader.phase == phase: return true
		await process_frame
	return false

func _key(code: int) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	return event

func _run() -> void:
	root.size = Vector2i(960,600)
	root.content_scale_size = Vector2i(960,600)
	change_scene_to_file("res://scenes/courtyard.tscn")
	if not await _scene("res://scenes/courtyard.tscn"):
		_record("Actual courtyard starts",false)
		await _finish()
		return
	var court := current_scene
	court.sounds.clear()
	var shell: Control = court.main_panel
	_record("Actual courtyard mounts reusable launch shell", shell.get_script() == LaunchShell and court.start_button == shell.primary_button and court.hero_button == shell.guide_button)
	_record("Legacy Explore ID refers to real selected-mode primary action", court.find_child("ExploreConfluence",true,false) == shell.primary_button)
	var actions: Array[Control] = []
	court._focusable_children(shell,actions)
	_record("Eight distinct launch controls are visible and reachable", actions.size() == 8)
	for dimensions in [Vector2i(960,600),Vector2i(1280,720),Vector2i(1366,768)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await _frames()
		var fit := true
		for action in actions: fit = fit and shell.card.get_global_rect().encloses(action.get_global_rect())
		_record("Integrated launch controls fit " + str(dimensions), fit and root.get_visible_rect().encloses(shell.card.get_global_rect()))
	for caption in ["Settings","Help"]:
		var opener: Button = shell.find_child(caption,true,false)
		opener.grab_focus()
		opener.pressed.emit()
		await _frames()
		_record(caption + " utility opens its real dialog", not shell.visible and (court.settings_panel.visible if caption == "Settings" else court.help_panel.visible))
		court._input(_key(KEY_ESCAPE))
		await _frames()
		_record(caption + " returns to its exact opener", shell.visible and root.gui_get_focus_owner() == opener)
	shell.train_mode_button.pressed.emit()
	shell.guide_button.grab_focus()
	shell.guide_button.pressed.emit()
	await _frames()
	_record("Guide utility opens without changing selected training", court.hero_panel.visible and shell.selected_mode == "train")
	court.hero_panel.close()
	await _frames()
	_record("Guide return preserves opener and selected mode", root.gui_get_focus_owner() == shell.guide_button and shell.selected_mode == "train")
	shell.primary_button.pressed.emit()
	await _frames()
	_record("Training primary activates the actual courtyard player", court.started and court.player.active and court.hud.visible and not shell.visible and court.player.camera.current)
	court.set_paused(true)
	_record("Training pause API remains usable", paused and court.pause_panel.visible)
	court.return_to_menu()
	await _frames()
	_record("Title return preserves training selection and primary focus", shell.selected_mode == "train" and root.gui_get_focus_owner() == shell.primary_button and court.title_camera.current)
	# Fail an actual ResourceLoader existence check after the allowlisted command.
	# The production SCENES map and all scene files remain untouched.
	shell.film_button.grab_focus()
	shell.film_button.pressed.emit()
	var loader: Control = court.scene_transition
	loader.phase_changed.connect(func(phase: StringName,_message: String,_progress: float): phases.append(str(phase)))
	loader._path = "res://scenes/ui-launch-intentionally-missing.tscn"
	_record("Film starts persistent visible loading before work", loader.phase == &"queued" and loader.visible and loader.get_parent().get_parent() == root and not court.is_ancestor_of(loader))
	var attempt: int = loader.snapshot().attempt
	shell.primary_button.pressed.emit()
	shell.film_button.pressed.emit()
	court.enter_confluence()
	court.start_training()
	court._input(_key(KEY_F3))
	_record("Duplicate clicks and title shortcuts cannot replace active navigation", loader.snapshot().attempt == attempt and loader.destination == &"combat_film" and not court.started and not court.hero_panel.visible)
	_record("Explicit world and UI processing are isolated", court.process_mode == Node.PROCESS_MODE_DISABLED and court.world.process_mode == Node.PROCESS_MODE_DISABLED and court.ui.process_mode == Node.PROCESS_MODE_DISABLED)
	var failed := await _phase(loader,&"error")
	_record("Missing scene gives real retry and back recovery", failed and loader.retry_button.visible and not loader.back_button.disabled and shell.launch_state == "loading" and current_scene == court)
	loader.back_button.pressed.emit()
	await _frames()
	_record("Back restores exact film opener and ready title", not loader.visible and shell.launch_state == "ready" and root.gui_get_focus_owner() == shell.film_button)
	_record("Back restores all explicit process modes", court.process_mode == Node.PROCESS_MODE_ALWAYS and court.world.process_mode == Node.PROCESS_MODE_PAUSABLE and court.ui.process_mode == Node.PROCESS_MODE_ALWAYS)
	shell.set_mode("world")
	shell.primary_button.grab_focus()
	shell.primary_button.pressed.emit()
	loader.cancel()
	await _frames()
	_record("Cancelling queued world launch restores selected primary", current_scene == court and shell.selected_mode == "world" and root.gui_get_focus_owner() == shell.primary_button and not loader.visible)
	# Exercise a real failure followed by Retry through the actual film destination.
	shell.film_button.pressed.emit()
	loader._path = "res://scenes/ui-launch-intentionally-missing.tscn"
	await _phase(loader,&"error")
	loader._path = "res://scenes/combat_film.tscn"
	var old_court: WeakRef = weakref(court)
	loader.retry_button.pressed.emit()
	var film_open := await _scene("res://scenes/combat_film.tscn")
	_record("Retry loads the actual duel film and releases old courtyard", film_open and not is_instance_valid(old_court.get_ref()) and current_scene.get("ready_to_play") == true and not loader.visible)
	_record("Real scene transition exposes resource and construction phases", phases.has("loading") and phases.has("constructing") and phases.has("done"))
	if film_open:
		current_scene.return_to_courtyard()
		var returned := await _scene("res://scenes/courtyard.tscn")
		_record("Film return reaches a fresh usable courtyard title", returned and current_scene.main_panel.visible and not current_scene.started and not paused)
		if returned:
			var reused: Control = current_scene._ensure_scene_transition()
			_record("Round trip reuses one persistent transition layer", reused == loader and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size() == 1)
	await _finish()

func _finish() -> void:
	paused = false
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var report := {"suite":"ui-launch-integration","passed":failures.is_empty(),"passed_count":checks.size()-failures.size(),"count":checks.size(),"failed":failures.size(),"checks":checks,"phases":phases,"scope":"Actual imported native scenes and threaded resource loading; no new pixel or OS-input acceptance.","sources":{}}
	for path in ["res://scripts/courtyard.gd","res://scripts/launch_shell.gd","res://scripts/scene_transition.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify({"passed":report.passed,"failed":report.failed}))
	if is_instance_valid(current_scene): current_scene.queue_free()
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if layer: layer.queue_free()
	await _frames()
	quit(0 if failures.is_empty() else 1)
