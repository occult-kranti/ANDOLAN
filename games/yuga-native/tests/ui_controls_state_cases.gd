extends SceneTree
## Engine-dispatched input and state tests. OS-window rendering is a separate gate.
const Overlay = preload("res://scripts/controls_overlay.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
var checks: Array[Dictionary] = []
var output := ""
var closed_count := 0
var changed_count := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _press(code: int, shift := false) -> void:
	for pressed in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = pressed
		event.shift_pressed = shift
		root.push_input(event)
		await process_frame

func _settle() -> void:
	for unused in range(4): await process_frame

func _run() -> void:
	var settings := "user://ui-controls-state.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(settings))
	Bindings.install(settings)
	var host := Control.new()
	root.add_child(host)
	var opener := Button.new()
	opener.text = "Open controls"
	host.add_child(opener)
	var overlay := Overlay.new()
	host.add_child(overlay)
	overlay.closed.connect(func():
		closed_count += 1
		opener.grab_focus()
	)
	overlay.bindings_changed.connect(func(): changed_count += 1)
	root.size = Vector2i(960,540)
	root.content_scale_size = root.size
	opener.grab_focus()
	overlay.open()
	await _settle()
	_record("opening focuses first mapping",root.gui_get_focus_owner() == overlay.binding_buttons.move_forward)
	await _press(KEY_TAB,true)
	_record("Shift Tab wraps first mapping to Done and skips disabled Cancel",root.gui_get_focus_owner() == overlay.done_button)
	await _press(KEY_TAB)
	_record("Tab wraps Done to first mapping without reaching host",root.gui_get_focus_owner() == overlay.binding_buttons.move_forward)
	var visited: Array[Control] = []
	for unused in range(overlay.focus_order.size()-1):
		visited.append(root.gui_get_focus_owner())
		await _press(KEY_TAB)
	_record("complete idle focus loop includes all enabled controls only",visited.size() == overlay.focus_order.size()-1 and not visited.has(opener) and not visited.has(overlay.cancel_button) and root.gui_get_focus_owner() == overlay.binding_buttons.move_forward)
	overlay.begin_capture("reload")
	var original := Bindings.current()
	await _press(KEY_W)
	_record("conflicting input leaves capture and bindings intact",overlay.capture_action == "reload" and Bindings.current() == original and overlay.status.text.contains("already assigned"))
	await _press(KEY_TAB)
	_record("Tab during capture reaches next mapping without consuming capture",root.gui_get_focus_owner() == overlay.binding_buttons.pulse and overlay.capture_action == "reload")
	await _press(KEY_TAB,true)
	_record("Shift Tab during capture returns to mapping",root.gui_get_focus_owner() == overlay.binding_buttons.reload and overlay.capture_action == "reload")
	overlay.cancel_button.grab_focus()
	await _press(KEY_ENTER)
	_record("Enter activates focused Cancel during capture",overlay.capture_action.is_empty() and overlay.visible and Bindings.current() == original and root.gui_get_focus_owner() == overlay.binding_buttons.reload)
	overlay.begin_capture("reload")
	await _press(KEY_ESCAPE)
	_record("first Escape cancels capture and retains modal",overlay.visible and overlay.capture_action.is_empty() and closed_count == 0 and Bindings.current() == original)
	await _press(KEY_ESCAPE)
	_record("second Escape closes and host restores original opener",not overlay.visible and closed_count == 1 and root.gui_get_focus_owner() == opener)
	await _press(KEY_T)
	_record("hidden modal ignores key events",Bindings.current() == original and closed_count == 1)
	overlay.open()
	overlay.begin_capture("reload")
	await _press(KEY_T)
	_record("engine-dispatched remap saves and refreshes label",Bindings.label("reload") == "T" and overlay.binding_buttons.reload.text == "T" and overlay.capture_action.is_empty() and changed_count == 1 and Bindings.read_config(settings).config.get_value("controls","bindings").reload == KEY_T)
	overlay.begin_capture("pulse")
	overlay.reset_button.grab_focus()
	await _press(KEY_ENTER)
	_record("Enter on Reset cancels capture and persists defaults",overlay.capture_action.is_empty() and Bindings.current() == Bindings.DEFAULTS and changed_count == 2 and overlay.status.text.contains("restored"))
	overlay.begin_capture("reload")
	overlay.done_button.grab_focus()
	await _press(KEY_ENTER)
	_record("Enter on Done closes capture without remapping",not overlay.visible and overlay.capture_action.is_empty() and closed_count == 2 and root.gui_get_focus_owner() == opener and Bindings.current() == Bindings.DEFAULTS)
	Bindings.install("user://ui-controls-missing-folder/settings.cfg")
	overlay.open()
	overlay.begin_capture("reload")
	await _press(KEY_T)
	_record("save failure stays visible and preserves active binding",overlay.visible and overlay.capture_action == "reload" and Bindings.label("reload") == "R" and overlay.status.text.contains("could not") and changed_count == 2,{"status":overlay.status.text})
	overlay.reset_bindings()
	_record("reset save failure cancels capture without false change event",overlay.capture_action.is_empty() and Bindings.current() == Bindings.DEFAULTS and changed_count == 2 and overlay.status.text.contains("could not"))
	var row_label: Label = overlay.binding_buttons.jump.get_parent().get_child(0)
	row_label.text = "Jump / ascend in flight with a deliberately extended localized instruction"
	overlay.status.text = "Settings could not be saved. Your existing controls remain active. Check available storage and try again."
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await _settle()
		var in_bounds := root.get_visible_rect().encloses(overlay.card.get_global_rect())
		var footer_fits := overlay.card.get_global_rect().encloses(overlay.done_button.get_global_rect()) and overlay.card.get_global_rect().encloses(overlay.cancel_button.get_global_rect())
		_record("long labels and failure status fit %s" % dimensions,in_bounds and footer_fits and row_label.get_global_rect().end.x <= overlay.binding_buttons.jump.get_global_rect().position.x and row_label.size.y > 30,{"card":str(overlay.card.get_global_rect()),"status":str(overlay.status.get_global_rect()),"label":str(row_label.get_global_rect())})
	_record("controls use shared semantic panel and minimum targets",overlay.card.theme != null and overlay.card.get_theme_stylebox("panel").bg_color == UI.INK and overlay.binding_buttons.reload.custom_minimum_size.y >= UI.TARGET_MIN and overlay.done_button.theme_type_variation == UI.BUTTON_TYPES.primary)
	overlay.close()
	host.queue_free()
	await process_frame
	DirAccess.remove_absolute(ProjectSettings.globalize_path(settings))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"checks":checks,"scope":"Native engine-dispatched key press/release, focus, layout and persistence. No OS-window or rendered acceptance.","sources":{}}
	for path in ["res://scripts/controls_overlay.gd","res://scripts/hero_ui_theme.gd","res://scripts/input_bindings.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t") + "\n")
		else: passed = false
	print("YUGA_UI_CONTROLS_STATE ",JSON.stringify(report))
	quit(0 if passed else 1)
