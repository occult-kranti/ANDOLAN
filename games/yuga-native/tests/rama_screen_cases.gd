extends SceneTree
## Source-level layout/state checks. Actual window and image review is separate.
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "details":detail})
	print("PASS " if passed else "FAIL ", label)

func _frames() -> void:
	for unused in range(5): await process_frame

func _key(code: int, shift: bool = false) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	event.shift_pressed = shift
	return event

func _run() -> void:
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	await _frames()
	_record("Title uses actual actor camera", scene.title_camera.current and not scene.player.active and scene.player.visual.get_child_count() > 0)
	for dimensions in [Vector2i(960,600), Vector2i(1280,720), Vector2i(1920,1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _frames()
		var card: Control = scene.main_panel.get_node("Card")
		var content: Control = scene.main_panel.get_node("Card/Scroll/Content")
		var viewport := root.get_visible_rect()
		var buttons_visible := true
		var actions: Array[Control] = []
		scene._focusable_children(scene.main_panel, actions)
		for button in actions: buttons_visible = buttons_visible and card.get_global_rect().encloses(button.get_global_rect())
		_record("Title actions fit " + str(dimensions), viewport.encloses(card.get_global_rect()) and buttons_visible, {"card":str(card.get_global_rect()),"content_height":content.size.y,"actions":actions.size()})
		var hero_screen: Vector2 = scene.title_camera.unproject_position(scene.player.global_position + Vector3(0,1.1,0))
		_record("Actual hero clear of title " + str(dimensions), hero_screen.x > card.get_global_rect().end.x + 20 and hero_screen.x < viewport.end.x - 30 and viewport.has_point(hero_screen), {"hero_torso":str(hero_screen),"menu_right":card.get_global_rect().end.x})
		scene.hero_button.grab_focus()
		scene._open_hero()
		await _frames()
		var guide = scene.hero_panel
		_record("Ability guide fits " + str(dimensions), viewport.encloses(guide.card.get_global_rect()) and guide.card.get_global_rect().encloses(guide.close_button.get_global_rect()) and guide.ability_buttons.size() == 5, {"card":str(guide.card.get_global_rect()),"close":str(guide.close_button.get_global_rect()),"abilities":guide.ability_buttons.size()})
		guide.select_ability("guardian_circle")
		_record("Guide shows real guardian contract " + str(dimensions), guide.detail_description.text == guide._rules.guardian_circle.description and guide.detail_timing.text.contains("11 s"), {"timing":guide.detail_timing.text,"description":guide.detail_description.text})
		guide.close_button.grab_focus()
		guide._input(_key(KEY_TAB))
		_record("Guide keyboard focus wraps within modal " + str(dimensions), root.gui_get_focus_owner() == guide.ability_buttons.kodanda)
		guide._input(_key(KEY_ESCAPE))
		_record("Guide returns to title " + str(dimensions), scene.main_panel.visible and not guide.visible and root.gui_get_focus_owner() == scene.hero_button)
		scene._open_settings(true)
		await _frames()
		_record("Settings fits " + str(dimensions), viewport.encloses(scene.settings_panel.get_node("Card").get_global_rect()) and root.gui_get_focus_owner().name == "Sensitivity")
		scene._close_settings()
		scene._open_help()
		await _frames()
		_record("Help has a focused return action " + str(dimensions), root.gui_get_focus_owner() == scene.help_back and viewport.encloses(scene.help_panel.get_node("Card").get_global_rect()))
		scene._close_help()
	scene.start_training()
	await _frames()
	_record("Training restores player camera", scene.player.camera.current and not scene.title_camera.current and scene.hud.visible)
	Input.action_press("move_forward")
	scene._open_hero()
	_record("Guide freezes training and releases input", paused and not scene.hud.visible and not Input.is_action_pressed("move_forward"))
	scene.hero_panel.close()
	_record("Guide resumes its live training owner", not paused and scene.hud.visible and scene.player.active)
	scene.set_paused(true)
	scene._open_hero()
	scene.hero_panel.close()
	_record("Guide preserves pause owner", paused and scene.pause_panel.visible and not scene.hud.visible)
	scene.return_to_menu()
	await _frames()
	_record("Title return restores portrait and clears overlays", scene.title_camera.current and scene.main_panel.visible and not scene.hud.visible and not scene.hero_panel.visible and not scene.player.active)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless Godot layout, focus and state checks; no rendered art or OS-input acceptance.","sources":{}}
	for path in ["res://scripts/courtyard.gd","res://scripts/hero_ui_theme.gd","res://scripts/rama_hero_panel.gd","res://assets/design/rama-ability-kit.json",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t") + "\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	await process_frame
	quit(0 if passed else 1)
