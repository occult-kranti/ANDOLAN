extends SceneTree
## Native input with host visibility, explicit isolation and pause ownership.
const Overlay = preload("res://scripts/controls_overlay.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""
var closes := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(4): await process_frame

func press(code: int, shift := false) -> void:
	for down in [true,false]:
		var key := InputEventKey.new()
		key.keycode = code
		key.physical_keycode = code
		key.pressed = down
		key.shift_pressed = shift
		root.push_input(key)
		await process_frame

func _run() -> void:
	Bindings.install("user://controls-lifecycle.cfg")
	var host := Control.new()
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(host)
	var recovery := Button.new()
	recovery.text = "Host recovery"
	recovery.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(recovery)
	var overlay := Overlay.new()
	host.add_child(overlay)
	overlay.closed.connect(func():
		closes += 1
		recovery.grab_focus()
	)
	overlay.open()
	overlay.begin_capture("reload")
	var original := Bindings.current()
	host.hide()
	recovery.grab_focus()
	await press(KEY_T)
	record("Hidden ancestor cancels capture and cannot change a binding",overlay.capture_action.is_empty() and Bindings.current()==original and root.gui_get_focus_owner()==recovery and closes==0)
	overlay.begin_capture("reload")
	record("Hidden ancestor cannot start a new capture",overlay.capture_action.is_empty())
	host.show()
	overlay.open()
	overlay.begin_capture("reload")
	host.process_mode = Node.PROCESS_MODE_DISABLED
	recovery.grab_focus()
	await press(KEY_T)
	record("Explicitly disabled caller isolates an ALWAYS modal",overlay.capture_action.is_empty() and Bindings.current()==original and root.gui_get_focus_owner()==recovery and closes==0)
	overlay.open()
	record("Open behind isolated caller cannot steal recovery focus",root.gui_get_focus_owner()==recovery)
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	overlay.open()
	paused = true
	overlay.begin_capture("reload")
	await press(KEY_T)
	var saved: Dictionary = Bindings.read_config("user://controls-lifecycle.cfg").config.get_value("controls","bindings",{})
	record("Paused caller still permits native remap and persistence",paused and overlay.capture_action.is_empty() and Bindings.label("reload")=="T" and saved.get("reload",0)==KEY_T)
	overlay.begin_capture("pulse")
	await press(KEY_ESCAPE)
	record("First Escape cancels capture without closing or resuming caller",paused and overlay.visible and overlay.capture_action.is_empty() and closes==0)
	await press(KEY_ESCAPE)
	record("Second Escape closes once and preserves caller pause/focus",paused and not overlay.visible and closes==1 and root.gui_get_focus_owner()==recovery)
	overlay.close()
	record("Repeated close does not repeat host navigation",closes==1 and root.gui_get_focus_owner()==recovery and paused)
	overlay.open()
	record("Reopening uses saved labels with fresh initial focus",overlay.binding_buttons.reload.text=="T" and overlay.capture_action.is_empty() and root.gui_get_focus_owner()==overlay.binding_buttons.move_forward)
	overlay.begin_capture("pulse")
	overlay.reset_button.grab_focus()
	await press(KEY_ENTER)
	record("Reset retains its own focus instead of stealing mapping focus",overlay.capture_action.is_empty() and Bindings.current()==Bindings.DEFAULTS and root.gui_get_focus_owner()==overlay.reset_button)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		overlay.binding_buttons.guardian_circle.grab_focus()
		await frames()
		var scroll: ScrollContainer = overlay.card.find_child("MappingsScroll",true,false)
		record("Focused final mapping and footer remain reachable at "+str(dimensions),root.get_visible_rect().encloses(overlay.card.get_global_rect()) and scroll.get_global_rect().encloses(overlay.binding_buttons.guardian_circle.get_global_rect()) and overlay.card.get_global_rect().encloses(overlay.done_button.get_global_rect()),{"card":str(overlay.card.get_global_rect()),"scroll":str(scroll.get_global_rect())})
		overlay.binding_buttons.move_forward.grab_focus()
		await press(KEY_TAB,true)
		record("Paused modal wraps focus without reaching host at "+str(dimensions),root.gui_get_focus_owner()==overlay.done_button and paused)
	overlay.close()
	paused = false
	host.queue_free()
	recovery.queue_free()
	await frames()
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://controls-lifecycle.cfg"))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Headless viewport-dispatched native keys, hidden/disabled owner isolation, pause and close ownership, saved labels and 960x540/1280x720 scroll containment. No OS-window, loader rendering or 2x-scale claim.","sources":{}}
	for path in ["res://scripts/controls_overlay.gd","res://scripts/hero_ui_theme.gd","res://scripts/input_bindings.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	quit(0 if passed else 1)
