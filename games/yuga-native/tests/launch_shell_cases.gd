extends SceneTree
## Native Control behavior and geometry; rendered approval is a separate gate.
const LaunchShell = preload("res://scripts/launch_shell.gd")
var checks: Array[Dictionary] = []
var output := ""
var events: Array[String] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ", label)

func _frames() -> void:
	for unused in range(5): await process_frame

func _run() -> void:
	var shell := LaunchShell.new()
	root.add_child(shell)
	await _frames()
	shell.world_requested.connect(func(): events.append("world"))
	shell.train_requested.connect(func(): events.append("train"))
	for action in ["guide","film","settings","help","quit"]:
		shell.connect(action + "_requested", func(): events.append(action))
	_record("Default is the available offline Confluence mode", shell.snapshot().selected_mode == "world" and shell.snapshot().offline)
	_record("One explicit selected mode", shell.world_mode_button.button_pressed and not shell.train_mode_button.button_pressed)
	for dimensions in [Vector2i(960,600),Vector2i(1280,720),Vector2i(1366,768),Vector2i(1920,1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _frames()
		var all_fit := true
		var usable_targets := true
		var rects: Dictionary = {}
		for action in shell._actions:
			all_fit = all_fit and shell.card.get_global_rect().encloses(action.get_global_rect())
			usable_targets = usable_targets and action.size.y >= 44
			rects[action.name] = str(action.get_global_rect())
		_record("Launch controls fit " + str(dimensions), root.get_visible_rect().encloses(shell.card.get_global_rect()) and all_fit, rects)
		_record("Native action targets remain at least 44 high " + str(dimensions), usable_targets)
		_record("Column leaves portrait side clear " + str(dimensions), shell.card.get_global_rect().end.x < dimensions.x * .52)
		shell.set_mode("train")
		await _frames()
		_record("Training description fits " + str(dimensions), shell.mode_description.get_line_count() <= 3 and shell.card.get_global_rect().encloses(shell.primary_button.get_global_rect()), {"lines":shell.mode_description.get_line_count(),"description":str(shell.mode_description.get_global_rect())})
		shell.set_mode("world")
	shell.focus_primary()
	_record("Entry focus reaches the launch action", root.gui_get_focus_owner() == shell.primary_button)
	var focus := root.gui_get_focus_owner()
	for unused in range(shell._actions.size()):
		focus = focus.find_next_valid_focus()
	_record("Tab order cycles within launch actions", focus == shell.primary_button)
	shell.primary_button.pressed.emit()
	_record("World launch emits host intent", events == ["world"])
	shell.train_mode_button.pressed.emit()
	_record("Selecting training updates context without launching", shell.selected_mode == "train" and events == ["world"] and shell.primary_button.text.contains("bow training"))
	shell.primary_button.pressed.emit()
	_record("Training launch emits host intent", events == ["world","train"])
	_record("Unknown modes are rejected", not shell.set_mode("online") and shell.selected_mode == "train")
	shell.set_launch_state("loading", "Preparing the courtyard…")
	var all_disabled := true
	for action in shell._actions: all_disabled = all_disabled and action.disabled
	_record("Loading locks actions and shows host status", all_disabled and shell.menu_hint.text == "Preparing the courtyard…" and shell.primary_button.text == "Opening bow training…")
	shell.primary_button.pressed.emit()
	shell.guide_button.pressed.emit()
	_record("Loading cannot emit repeated navigation", events == ["world","train"] and not shell.set_mode("world"))
	shell.set_launch_state("error", "The courtyard could not open. Try again.")
	_record("Failure preserves selection and enables retry", shell.selected_mode == "train" and not shell.primary_button.disabled and shell.menu_hint.text.contains("Try again"))
	shell.primary_button.pressed.emit()
	_record("Retry emits the preserved training intent", events == ["world","train","train"])
	shell.set_mode("world")
	_record("Choosing another mode clears stale error", shell.launch_state == "ready" and not shell.menu_hint.text.contains("could not"))
	for action in ["guide","film","settings","help","quit"]: shell._emit_utility(action)
	_record("Every preserved utility has a signal", events.slice(3) == ["guide","film","settings","help","quit"])
	shell.hide()
	shell.primary_button.pressed.emit()
	shell._emit_utility("quit")
	_record("Hidden launch shell cannot navigate", events.size() == 8)
	shell.show()
	await _frames()
	_record("Returning to title restores primary focus", root.gui_get_focus_owner() == shell.primary_button)
	shell.hide()
	shell.show()
	shell.guide_button.grab_focus()
	await _frames()
	_record("Host-restored dialog opener focus is preserved", root.gui_get_focus_owner() == shell.guide_button)
	_record("Unknown launch states are rejected", not shell.set_launch_state("pretend_online") and shell.launch_state == "ready")
	root.content_scale_size = Vector2i(800,400)
	root.size = Vector2i(800,400)
	await _frames()
	var last_action: Button = shell._actions.back()
	last_action.grab_focus()
	shell.scroll.ensure_control_visible(last_action)
	await _frames()
	_record("Short windows keep utilities reachable by scrolling", shell.card.get_global_rect().encloses(last_action.get_global_rect()) and root.gui_get_focus_owner() == last_action)
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var result := {"suite":"launch-shell", "checks":checks, "passed":failures.is_empty(), "passed_count":checks.size() - failures.size(), "count":checks.size(), "failed":failures.size(), "scope":"Native headless Controls and state; actual rendered review remains separate."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t"))
	print(JSON.stringify({"passed":result.passed,"failed":result.failed}))
	shell.queue_free()
	await process_frame
	quit(0 if failures.is_empty() else 1)
