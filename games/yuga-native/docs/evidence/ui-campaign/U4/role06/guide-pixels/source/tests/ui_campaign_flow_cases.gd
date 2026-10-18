extends SceneTree
## CPU-only contract for observer telemetry and actual engine keyboard dispatch.
const Shell = preload("res://scripts/launch_shell.gd")
var checks: Array = []
var output := ""
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")
func record(label: String, ok: bool) -> void:
	checks.append({"name":label,"passed":ok})
	print("PASS " if ok else "FAIL ", label)
func frames() -> void:
	for n in range(4): await process_frame
func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		Input.parse_input_event(event)
		await frames()
func _run() -> void:
	var shell := Shell.new()
	root.add_child(shell)
	await frames()
	var events: Array = []
	shell.train_requested.connect(func(): events.append("train"))
	shell.train_mode_button.grab_focus()
	await key(KEY_ENTER)
	record("Engine keyboard activation selects training", shell.selected_mode == "train")
	shell.primary_button.grab_focus()
	await key(KEY_ENTER)
	record("Engine keyboard activation emits one training intent", events == ["train"])
	shell.set_launch_state("loading")
	await key(KEY_ENTER)
	record("Disabled launch rejects keyboard activation", events == ["train"])
	shell.set_launch_state("ready")
	shell.primary_button.grab_focus()
	await key(KEY_TAB)
	record("Tab moves actual GUI focus", root.gui_get_focus_owner() == shell.guide_button)
	var failures := checks.filter(func(row): return not row.passed).size()
	var result := {"checks":checks,"passed":checks.size()-failures,"failed":failures,"scope":"CPU engine input dispatch only; not XTest/native-window or rendered approval."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t"))
	quit(0 if failures == 0 else 1)
