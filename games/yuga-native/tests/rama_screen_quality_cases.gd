extends SceneTree
## Ordinary scene focus/layout/settings checks. Rendered OS-input review is separate.
const Bindings = preload("res://scripts/input_bindings.gd")
const SETTINGS := "user://courtyard-settings.cfg"
var checks: Array[Dictionary] = []
var output := ""
var existed := false
var saved := PackedByteArray()
var courtyard_script := "res://scripts/courtyard.gd"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		elif arg.begins_with("--courtyard-script="): courtyard_script = arg.trim_prefix("--courtyard-script=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _frames() -> void:
	for unused in range(5): await process_frame

func _key(code: int, shift: bool = false) -> InputEventKey:
	var event := InputEventKey.new()
	event.keycode = code
	event.physical_keycode = code
	event.pressed = true
	event.shift_pressed = shift
	return event

func _button_with_text(owner: Node, caption: String) -> Button:
	for child in owner.get_children():
		if child is Button and child.text == caption: return child
		var result := _button_with_text(child, caption)
		if result: return result
	return null

func _focus_name() -> String:
	var focused := root.gui_get_focus_owner()
	return str(focused.get_path()) if focused else "<none>"

func _complete_cycle(scene: Node, owner: Control) -> bool:
	var order: Array[Control] = []
	scene._focusable_children(owner, order)
	if order.is_empty(): return false
	order[0].grab_focus()
	for index in order.size():
		if root.gui_get_focus_owner() != order[index]: return false
		scene._trap_modal_focus(_key(KEY_TAB))
	if root.gui_get_focus_owner() != order[0]: return false
	for index in range(order.size() - 1, -1, -1):
		scene._trap_modal_focus(_key(KEY_TAB, true))
		if root.gui_get_focus_owner() != order[index]: return false
	return true

func _run() -> void:
	existed = FileAccess.file_exists(SETTINGS)
	if existed: saved = FileAccess.get_file_as_bytes(SETTINGS)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var scene = load("res://scenes/courtyard.tscn").instantiate()
	if courtyard_script != "res://scripts/courtyard.gd": scene.set_script(load(courtyard_script))
	root.add_child(scene)
	current_scene = scene
	await _frames()
	# This fixture checks visual/control state, not listening or audio teardown.
	# Prevent many fast synthetic button activations from queuing menu sounds.
	scene.sounds.clear()
	var explore: Button = scene.main_panel.primary_button
	var settings: Button = _button_with_text(scene.main_panel, "Settings")
	var help: Button = _button_with_text(scene.main_panel, "Help")
	_record("Initial title focus is the primary world action", root.gui_get_focus_owner() == explore)
	for dimensions in [Vector2i(960,600),Vector2i(1280,720),Vector2i(1920,1080),Vector2i(2560,1440)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _frames()
		var view := root.get_visible_rect()
		var card: Control = scene.main_panel.get_node("Card")
		var actions: Array[Control] = []
		scene._focusable_children(scene.main_panel, actions)
		var required_actions := ["ConfluenceMode", "TrainingMode", "ExploreConfluence", "RamaAbilities", "WatchConfluenceDuel", "Help", "Settings", "Quit"]
		var actual_actions: Array[String] = []
		for action in actions: actual_actions.append(str(action.name))
		required_actions.sort()
		actual_actions.sort()
		var fit := actual_actions == required_actions
		for action in actions: fit = fit and card.get_global_rect().encloses(action.get_global_rect()) and action.size.y >= 44
		_record("Required mode, launch and utility actions fit without scrolling at " + str(dimensions), fit and view.encloses(card.get_global_rect()), {"card":str(card.get_global_rect()),"actions":actions.size()})
		_record("All title actions reached once in each Tab direction at " + str(dimensions), _complete_cycle(scene,scene.main_panel))
		var face: Vector2 = scene.title_camera.unproject_position(scene.player.global_position + Vector3(0,1.78,0))
		var veil: TextureRect = scene.main_panel.get_child(0)
		var face_veil_alpha: float = veil.texture.gradient.sample(clampf(face.x / view.size.x,0,1)).a
		_record("Actual portrait face stays clear of title and dark wash at " + str(dimensions), face.x > card.get_global_rect().end.x + 20 and view.has_point(face) and face_veil_alpha <= .03, {"face":str(face),"wash_alpha":face_veil_alpha})
		settings.grab_focus()
		settings.pressed.emit()
		await _frames()
		var scroll: ScrollContainer = scene.settings_panel.get_node("Card/Scroll")
		var sensitivity: Control = scroll.get_node("Content/Sensitivity")
		var eyebrow: Control = scroll.get_node("Content").get_child(0)
		_record("Settings entry keeps full heading and slider focus at " + str(dimensions), scroll.scroll_vertical == 0 and scroll.get_global_rect().encloses(eyebrow.get_global_rect()) and root.gui_get_focus_owner() == sensitivity)
		_record("Settings keyboard cycle includes every preference and Back at " + str(dimensions), _complete_cycle(scene,scene.settings_panel))
		scene._input(_key(KEY_ESCAPE))
		_record("Escape restores exact Settings opener at " + str(dimensions), scene.main_panel.visible and root.gui_get_focus_owner() == settings, {"focus":_focus_name()})
		help.grab_focus()
		help.pressed.emit()
		await _frames()
		scene._input(_key(KEY_ESCAPE))
		_record("Escape restores exact Help opener at " + str(dimensions), scene.main_panel.visible and root.gui_get_focus_owner() == help, {"focus":_focus_name()})
		explore.grab_focus()
		scene._input(_key(KEY_F3))
		await _frames()
		scene.hero_panel._input(_key(KEY_ESCAPE))
		_record("Shortcut guide returns to the previously focused title action at " + str(dimensions), scene.main_panel.visible and root.gui_get_focus_owner() == explore, {"focus":_focus_name()})
	# The opener can disappear or become disabled while another surface owns input.
	var temporary := Button.new()
	temporary.text = "Temporary opener"
	scene._modal_content(scene.main_panel).add_child(temporary)
	temporary.grab_focus()
	scene._open_help()
	temporary.free()
	scene._close_help()
	_record("Deleted opener safely falls back to the primary title action",root.gui_get_focus_owner() == explore,{"focus":_focus_name()})
	settings.grab_focus()
	scene._open_help()
	settings.disabled = true
	scene._close_help()
	_record("Disabled opener safely falls back to the primary title action",root.gui_get_focus_owner() == explore,{"focus":_focus_name()})
	settings.disabled = false
	settings.grab_focus()
	scene._open_hero()
	settings.disabled = true
	scene.hero_panel.close()
	_record("Guide cannot override the disabled-opener fallback",root.gui_get_focus_owner() == explore,{"focus":_focus_name()})
	settings.disabled = false
	var moved := Button.new()
	moved.text = "Moved opener"
	scene._modal_content(scene.main_panel).add_child(moved)
	moved.grab_focus()
	scene._open_hero()
	moved.reparent(scene.interface_root)
	scene.hero_panel.close()
	_record("Guide cannot restore an opener moved outside its owning screen",root.gui_get_focus_owner() == explore,{"focus":_focus_name()})
	moved.free()
	# Exercise the nested controls route and the actual saved map used by guide/HUD.
	settings.grab_focus()
	settings.pressed.emit()
	await _frames()
	scene.controls_button.grab_focus()
	scene.controls_button.pressed.emit()
	scene.controls_overlay.begin_capture("pulse")
	scene.controls_overlay._input(_key(KEY_J))
	_record("Keyboard capture saves the new ability key",Bindings.label("pulse") == "J" and scene.controls_overlay.binding_buttons.pulse.text == "J" and scene.controls_overlay.capture_action.is_empty())
	scene.controls_overlay.done_button.pressed.emit()
	_record("Controls returns to its exact Settings action",scene.settings_panel.visible and root.gui_get_focus_owner() == scene.controls_button)
	var sensitivity_slider: HSlider = scene.settings_panel.get_node("Card/Scroll/Content/Sensitivity")
	var volume_slider: HSlider = scene.settings_panel.get_node("Card/Scroll/Content/Volume")
	sensitivity_slider.value = 1.35
	volume_slider.value = .35
	var config: ConfigFile = Bindings.read_config().config
	_record("Preference saves preserve the changed ability map",is_equal_approx(config.get_value("controls","sensitivity"),1.35) and is_equal_approx(config.get_value("audio","volume"),.35) and config.get_value("controls","bindings").pulse == KEY_J)
	scene.settings_back.pressed.emit()
	_record("Nested controls and preference route retains original title opener",root.gui_get_focus_owner() == settings)
	scene._open_hero()
	scene.hero_panel.select_ability("piercing_dawn")
	_record("Guide describes the newly saved ability key",scene.hero_panel.ability_buttons.piercing_dawn.text.begins_with("J") and scene.hero_panel.key_label.text.begins_with("J"))
	scene.hero_panel.close()
	scene.start_training()
	await _frames()
	scene.rama_hud._refresh_slots()
	_record("Live HUD uses the same saved ability key",scene.rama_hud.slots[1].text.begins_with("J"))
	for entry in [{"caption":"RAMA’S ABILITIES","kind":"hero"},{"caption":"CONTROLS & HELP","kind":"help"},{"caption":"SETTINGS","kind":"settings"}]:
		scene.set_paused(true)
		var opener: Button = _button_with_text(scene.pause_panel,entry.caption)
		opener.grab_focus()
		opener.pressed.emit()
		await _frames()
		if entry.kind == "hero": scene.hero_panel.close()
		elif entry.kind == "help": scene._close_help()
		else: scene._close_settings()
		_record("Pause " + entry.kind + " restores its exact opener and frozen owner",paused and scene.pause_panel.visible and not scene.hud.visible and root.gui_get_focus_owner() == opener,{"focus":_focus_name()})
	scene.set_paused(false)
	var pause_action: Button = _button_with_text(scene.hud,"ESC  PAUSE")
	pause_action.grab_focus()
	scene._open_hero()
	scene.hero_panel.close()
	_record("Guide return to live play releases interface focus and resumes",not paused and scene.hud.visible and root.gui_get_focus_owner() == null and scene.player.active,{"focus":_focus_name()})
	scene._open_help()
	scene._close_help()
	_record("Help return to live play releases interface focus and resumes",not paused and scene.hud.visible and root.gui_get_focus_owner() == null and scene.player.active)
	scene.return_to_menu()
	await _frames()
	_record("Return to title restores its primary action and actual actor camera",scene.main_panel.visible and scene.title_camera.current and root.gui_get_focus_owner() == explore)
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless actual scene focus, keyboard navigation, saved controls and layout checks. No rendered appearance, OS input, hardware performance or human feel acceptance.","sources":{}}
	for path in [courtyard_script,"res://scripts/hero_ui_theme.gd","res://scripts/rama_hero_panel.gd","res://scripts/controls_overlay.gd","res://scripts/input_bindings.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t") + "\n")
		else: passed = false
	scene.queue_free()
	current_scene = null
	paused = false
	await process_frame
	if existed:
		var file := FileAccess.open(SETTINGS,FileAccess.WRITE)
		file.store_buffer(saved)
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	Bindings.install()
	quit(0 if passed else 1)
