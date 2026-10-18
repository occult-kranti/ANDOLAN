extends SceneTree
## Actual shared components and viewport input; no rendered/package acceptance.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Controls = preload("res://scripts/controls_overlay.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")

var output := ""
var checks: Array[Dictionary] = []
var source_before: Dictionary = {}
var source_paths: Array[String] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames(n: int = 3) -> void:
	for unused in n: await process_frame

func press(backward: bool, code: Key = KEY_TAB) -> void:
	for down in [true, false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.shift_pressed = backward
		event.pressed = down
		root.push_input(event)
		await process_frame

func focused() -> String:
	var node: Control = root.gui_get_focus_owner()
	return str(node.get_path()) if is_instance_valid(node) else "<none>"

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "detail":detail})
	print("PASS " if passed else "FAIL ", label)

func snapshot() -> Dictionary:
	var result: Dictionary = {}
	for path in source_paths: result[path] = FileAccess.get_sha256(path)
	return result

func exercise(kind: String, host: Control) -> void:
	var modal: Control = Guide.new() if kind == "guide" else Controls.new()
	host.add_child(modal)
	modal.open()
	await frames()
	var first: Control = modal.ability_buttons.kodanda if kind == "guide" else modal.binding_buttons.move_forward
	var last: Control = modal.close_button if kind == "guide" else modal.done_button
	var middle: Control = modal.ability_buttons.piercing_dawn if kind == "guide" else modal.binding_buttons.reload
	first.grab_focus()
	await press(true)
	check(kind+" normal backward wrap", root.gui_get_focus_owner() == last, {"actual":focused()})
	last.grab_focus()
	await press(false)
	check(kind+" normal forward wrap", root.gui_get_focus_owner() == first, {"actual":focused()})
	for state in ["unclaimed", "disabled", "hidden", "disposed"]:
		for backward in [true, false]:
			var original_count: int = modal.focus_order.size()
			if state == "unclaimed":
				root.gui_release_focus()
			elif state == "disabled":
				middle.grab_focus()
				middle.disabled = true
			elif state == "hidden":
				middle.grab_focus()
				middle.hide()
			else:
				# A real disposed peer challenges stale entries independently of
				# the ordinary component route. Restore the list after each case.
				var disposable := Button.new()
				disposable.name = "DisposableFocusPeer"
				host.add_child(disposable)
				modal.focus_order.append(disposable)
				disposable.grab_focus()
				disposable.queue_free()
				await frames(2)
			var before_key := focused()
			await press(backward)
			var expected: Control = last if backward else first
			check(kind+" "+state+" "+("backward" if backward else "forward")+" recovery",
				root.gui_get_focus_owner() == expected,
				{"before_key":before_key, "actual":focused(), "expected":str(expected.get_path())})
			if state == "disabled": middle.disabled = false
			elif state == "hidden": middle.show()
			elif state == "disposed": modal.focus_order.resize(original_count)
	if kind == "guide":
		for backward in [true, false]:
			var receiver := Effects.new()
			host.add_child(receiver)
			modal.configure_effects(receiver)
			modal.reduced_motion_button.grab_focus()
			receiver.queue_free()
			await frames()
			var before_key := focused()
			await press(backward)
			check("guide actual receiver disposal "+("backward" if backward else "forward"),
				modal.reduced_motion_button.disabled and root.gui_get_focus_owner() == (last if backward else first),
				{"before_key":before_key, "actual":focused()})
		for code in [KEY_UP, KEY_DOWN]:
			root.gui_release_focus()
			await press(false, code)
			check("guide unclaimed arrow "+str(code), root.gui_get_focus_owner() == (last if code == KEY_UP else first), {"actual":focused()})
	modal.close()
	modal.queue_free()
	await frames()

func run() -> void:
	root.size = Vector2i(960, 540)
	root.content_scale_size = root.size
	Bindings.install("user://focus-recovery.cfg")
	for relative in ["scripts/rama_hero_panel.gd", "scripts/controls_overlay.gd", "scripts/courtyard.gd",
			"scripts/hero_ui_theme.gd", "scripts/input_bindings.gd", "scripts/rama_ability_effects.gd"]:
		source_paths.append("res://"+relative)
	source_paths.append(get_script().resource_path)
	source_before = snapshot()
	var initial_bindings: Dictionary = Bindings.current().duplicate(true)
	var host := Control.new()
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(host)
	await exercise("guide", host)
	await exercise("controls", host)
	check("focus navigation never changes saved binding state", Bindings.current() == initial_bindings)
	host.queue_free()
	await frames()
	var after := snapshot()
	check("integrated runtime and fixture sources stable", after == source_before)
	var result := {"passed":checks.all(func(row): return row.passed), "count":checks.size(), "checks":checks,
		"source_before":source_before, "source_after":after,
		"scope":"Canonical shared 2D components with native viewport key dispatch. Real disabled/hidden/disposed focus peers, explicit unclaimed focus and actual effect receiver disposal. No raster, OS-window input or package qualification."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(result, "  ")+"\n")
		else: result.passed = false
	quit(0 if result.passed else 1)
