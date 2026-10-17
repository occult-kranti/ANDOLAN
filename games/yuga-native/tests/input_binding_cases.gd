extends SceneTree
const Bindings = preload("res://scripts/input_bindings.gd")
const Overlay = preload("res://scripts/controls_overlay.gd")
const SETTINGS := "user://courtyard-settings.cfg"
var checks: Array[Dictionary] = []
var output := ""
var saved := PackedByteArray()
var existed := false
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")
func _record(name_: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":name_,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",name_)
func _write(source: String) -> void:
	var file := FileAccess.open(SETTINGS,FileAccess.WRITE)
	file.store_string(source)
	file.close()
func _key(code: int, shift := false) -> InputEventKey:
	var event := InputEventKey.new()
	event.physical_keycode = code
	event.keycode = code
	event.pressed = true
	event.shift_pressed = shift
	return event
func _run() -> void:
	existed = FileAccess.file_exists(SETTINGS)
	if existed: saved = FileAccess.get_file_as_bytes(SETTINGS)
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	_record("missing settings install all defaults",Bindings.install().ok and Bindings.current() == Bindings.DEFAULTS)
	var count := InputMap.action_get_events("move_forward").size()
	Bindings.install()
	_record("repeated scene install does not duplicate actions",count == 2 and InputMap.action_get_events("move_forward").size() == count and InputMap.action_get_events("fire").size() == 1)
	_record("flight grapple descent and fixed help labels",Bindings.label("fly") == "F" and Bindings.label("grapple") == "G" and Bindings.label("descend") == "Ctrl" and Bindings.label("help_controls") == "F2")
	var legacy := Bindings.DEFAULTS.duplicate()
	legacy.erase("ultimate")
	legacy.reload = KEY_X
	Bindings.merge_settings({"controls":{"bindings":legacy,"binding_version":1},"audio":{"volume":.2}})
	var legacy_bytes := FileAccess.get_file_as_bytes(SETTINGS)
	_record("legacy X remap survives new invocation binding without rewriting saves",Bindings.install().ok and Bindings.label("reload") == "X" and Bindings.label("ultimate") == "V" and FileAccess.get_file_as_bytes(SETTINGS) == legacy_bytes)
	_record("migrated invocation layout persists as version3 with other settings",Bindings.set_binding("ultimate",KEY_B).ok and Bindings.install().ok and Bindings.label("reload") == "X" and Bindings.label("ultimate") == "B" and Bindings.read_config().config.get_value("controls","binding_version") == 3 and Bindings.read_config().config.get_value("audio","volume") == .2)
	var before_guardian := Bindings.DEFAULTS.duplicate()
	before_guardian.erase("guardian_circle")
	before_guardian.reload = KEY_C
	Bindings.merge_settings({"controls":{"bindings":before_guardian,"binding_version":2},"audio":{"volume":.4}})
	var before_guardian_bytes := FileAccess.get_file_as_bytes(SETTINGS)
	_record("version2 C reload retains mapping and adds guardian on free V without rewriting save",Bindings.install().ok and Bindings.label("reload") == "C" and Bindings.label("ultimate") == "X" and Bindings.label("guardian_circle") == "V" and FileAccess.get_file_as_bytes(SETTINGS) == before_guardian_bytes)
	var preserved := true
	for action in before_guardian: preserved = preserved and Bindings.current()[action] == before_guardian[action]
	_record("guardian migration preserves every existing key and persists version3",preserved and Bindings.set_binding("guardian_circle",KEY_B).ok and Bindings.install().ok and Bindings.label("guardian_circle") == "B" and Bindings.label("reload") == "C" and Bindings.read_config().config.get_value("controls","binding_version") == 3 and Bindings.read_config().config.get_value("audio","volume") == .4)
	Bindings.reset_defaults()
	_record("invocation action resets and fixed selector stays discoverable",Bindings.label("ultimate") == "X" and Bindings.label("open_invocations") == "F3")
	Bindings.merge_settings({"audio":{"volume":.35},"film":{"reduced_motion":true},"controls":{"sensitivity":1.4}})
	var changed := Bindings.set_binding("reload",KEY_T)
	Bindings.install()
	var config: ConfigFile = Bindings.read_config().config
	_record("remap persists while preserving other settings",changed.ok and Bindings.label("reload") == "T" and config.get_value("audio","volume") == .35 and config.get_value("film","reduced_motion") and config.get_value("controls","sensitivity") == 1.4)
	var before := FileAccess.get_file_as_bytes(SETTINGS)
	_record("duplicate key rejects atomically",not Bindings.set_binding("reload",KEY_W).ok and FileAccess.get_file_as_bytes(SETTINGS) == before and Bindings.label("reload") == "T")
	_record("reserved navigation key rejects atomically",not Bindings.set_binding("reload",KEY_ESCAPE).ok and not Bindings.set_binding("reload",KEY_N).ok and FileAccess.get_file_as_bytes(SETTINGS) == before)
	_record("unknown action rejected",not Bindings.set_binding("execute",KEY_X).ok)
	_record("reset defaults persists immediately",Bindings.reset_defaults().ok and Bindings.current() == Bindings.DEFAULTS and Bindings.read_config().config.get_value("controls","bindings") == Bindings.DEFAULTS)
	_record("outgoing object constructor variant rejected",not Bindings.merge_settings({"unsafe":{"object":RefCounted.new()}}).ok and not Bindings.merge_settings({"unsafe":{"value":NAN}}).ok)
	var fixtures := [
		{"name":"oversize","source":"#".repeat(65537)},
		{"name":"constructor","source":"[audio]\nvolume=Object(\"RefCounted\")\n"},
		{"name":"deep nesting","source":"[audio]\nvolume=" + "[".repeat(9) + "0" + "]".repeat(9)},
		{"name":"malformed","source":"[audio\nvolume=0"}
	]
	for fixture in fixtures:
		_write(fixture.source)
		var bytes := FileAccess.get_file_as_bytes(SETTINGS)
		_record("unsafe persisted " + fixture.name + " rejected without overwrite",not Bindings.read_config().ok and not Bindings.merge_settings({"audio":{"volume":.5}}).ok and FileAccess.get_file_as_bytes(SETTINGS) == bytes)
	var backups: Array[String] = []
	for fixture in [{"name":"malformed","source":"[audio\nvolume=0"},{"name":"oversized","source":"#".repeat(65537)}]:
		_write(fixture.source)
		var original := FileAccess.get_file_as_bytes(SETTINGS)
		Bindings.install()
		var recovered := Bindings.reset_defaults()
		var backup: String = recovered.get("backup_path","")
		_record("explicit reset recovers " + fixture.name + " file with exact unique backup",recovered.ok and not backup.is_empty() and not backup in backups and FileAccess.get_file_as_bytes(backup) == original and Bindings.read_config().ok and Bindings.read_config().config.get_value("controls","bindings") == Bindings.DEFAULTS and recovered.message.contains(backup.get_file()))
		if not backup.is_empty(): backups.append(backup)
		_record("preferences can save after " + fixture.name + " reset",Bindings.set_binding("reload",KEY_T).ok and Bindings.merge_settings({"audio":{"volume":.25}}).ok and Bindings.read_config().config.get_value("audio","volume") == .25)
	var long_path := "user://" + "x".repeat(200) + ".cfg"
	var long_file := FileAccess.open(long_path,FileAccess.WRITE)
	long_file.store_string("invalid [")
	long_file.close()
	Bindings.install(long_path)
	var long_before := FileAccess.get_file_as_bytes(long_path)
	_record("bounded backup-path failure leaves original bytes untouched",not Bindings.reset_defaults().ok and FileAccess.get_file_as_bytes(long_path) == long_before)
	DirAccess.remove_absolute(long_path)
	for backup in backups: DirAccess.remove_absolute(backup)
	Bindings.install()
	_write('[controls]\nbindings={"reload":"T"}\n')
	_record("invalid key types fall back to defaults",not Bindings.install().ok and Bindings.current() == Bindings.DEFAULTS)
	_write('[controls]\nbindings={"missing":84}\n')
	_record("unknown saved actions fall back to defaults",not Bindings.install().ok and Bindings.current() == Bindings.DEFAULTS)
	_record("reset repairs invalid saved binding map and clears notice",Bindings.reset_defaults().ok and Bindings.load_notice.is_empty())
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	Bindings.install()
	for action in Bindings.DEFAULTS: Input.action_press(action)
	Input.action_press("fire")
	Bindings.release_gameplay()
	var released := not Input.is_action_pressed("fire")
	for action in Bindings.DEFAULTS: released = released and not Input.is_action_pressed(action)
	_record("all held gameplay and traversal actions released",released)
	root.content_scale_size = Vector2i(960,600)
	root.size = Vector2i(960,600)
	var overlay := Overlay.new()
	root.add_child(overlay)
	overlay.open()
	for unused in range(5): await process_frame
	_record("controls modal fits 960 by 600",root.get_visible_rect().size == Vector2(960,600) and root.get_visible_rect().encloses(overlay.card.get_global_rect()),{"rect":str(overlay.card.get_global_rect())})
	overlay.binding_buttons.move_forward.grab_focus()
	overlay._input(_key(KEY_TAB))
	_record("keyboard Tab navigates next mapping",root.gui_get_focus_owner() == overlay.binding_buttons.move_back)
	overlay._input(_key(KEY_TAB,true))
	_record("Shift Tab navigates previous mapping",root.gui_get_focus_owner() == overlay.binding_buttons.move_forward)
	overlay.begin_capture("reload")
	overlay._input(_key(KEY_W))
	_record("capture duplicate keeps existing binding and capture",overlay.capture_action == "reload" and Bindings.label("reload") == "R")
	overlay._input(_key(KEY_ESCAPE))
	_record("Escape cancels capture without closing modal",overlay.visible and overlay.capture_action.is_empty() and Bindings.label("reload") == "R")
	overlay.begin_capture("reload")
	overlay._input(_key(KEY_T))
	_record("capture commits new key and dynamic button label",Bindings.label("reload") == "T" and overlay.binding_buttons.reload.text == "T" and overlay.capture_action.is_empty())
	overlay.reset_bindings()
	_record("reset button restores persisted defaults",Bindings.label("reload") == "R" and Bindings.read_config().config.get_value("controls","bindings") == Bindings.DEFAULTS)
	root.content_scale_size = Vector2i(1280,720)
	root.size = Vector2i(1280,720)
	for unused in range(3): await process_frame
	_record("controls modal fits 1280 by 720",root.get_visible_rect().encloses(overlay.card.get_global_rect()))
	overlay._input(_key(KEY_ESCAPE))
	_record("Escape closes idle controls modal",not overlay.visible)
	overlay.queue_free()
	await process_frame
	var courtyard = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(courtyard)
	current_scene = courtyard
	for unused in range(4): await process_frame
	courtyard._open_settings(true)
	courtyard._open_controls()
	courtyard.controls_overlay.begin_capture("reload")
	courtyard.controls_overlay._input(_key(KEY_T))
	courtyard.controls_overlay.close()
	_record("courtyard controls return to Settings with focus and label",courtyard.settings_panel.visible and root.gui_get_focus_owner() == courtyard.controls_button and courtyard.status_label.text.contains("T reload"))
	courtyard.sensitivity = 1.7
	courtyard.volume = .25
	courtyard._save_settings()
	config = Bindings.read_config().config
	_record("ordinary settings preserve remapped controls",config.get_value("controls","bindings").reload == KEY_T and is_equal_approx(config.get_value("controls","sensitivity"),1.7))
	courtyard._close_settings()
	courtyard.start_training()
	Input.action_press("fly")
	Input.action_press("move_forward")
	courtyard._open_help()
	_record("help freezes live practice and releases held input",paused and courtyard.help_panel.visible and not Input.is_action_pressed("fly") and not Input.is_action_pressed("move_forward"))
	courtyard._close_help()
	_record("closing live help resumes practice",not paused and not courtyard.help_panel.visible and courtyard.player.active)
	courtyard.set_paused(true)
	var echo_event := _key(KEY_ESCAPE)
	echo_event.echo = true
	courtyard._input(echo_event)
	_record("held Escape repeat cannot toggle pause",paused and courtyard.pause_panel.visible)
	courtyard._open_help()
	courtyard._close_help()
	_record("help opened from pause returns to pause",paused and courtyard.pause_panel.visible)
	courtyard._open_settings(false)
	courtyard._open_controls()
	courtyard.controls_overlay.begin_capture("reload")
	courtyard._on_focus_lost()
	_record("focus loss cancels capture and preserves paused settings context",paused and courtyard.controls_overlay.visible and courtyard.controls_overlay.capture_action.is_empty())
	courtyard.controls_overlay.close()
	root.content_scale_size = Vector2i(960,600)
	root.size = Vector2i(960,600)
	for unused in range(4): await process_frame
	_record("courtyard Settings modal fits 960 by 600",root.get_visible_rect().encloses(courtyard.settings_panel.get_node("Card").get_global_rect()))
	courtyard.queue_free()
	current_scene = null
	paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	await process_frame
	if existed:
		var file := FileAccess.open(SETTINGS,FileAccess.WRITE)
		file.store_buffer(saved)
		file.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Recovered implementation; headless state, focus, layout and config fixtures. No OS-input or rendered visual acceptance implied.","sources":{}}
	for path in ["res://scripts/input_bindings.gd","res://scripts/controls_overlay.gd","res://scripts/courtyard.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t") + "\n")
		else: passed = false
	print("YUGA_INPUT_BINDINGS ",JSON.stringify(report))
	quit(0 if passed else 1)
