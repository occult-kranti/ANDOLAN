extends SceneTree
## Run only in an isolated minimal project with test/scene_transition_fixture=true.
## The test writes the three allowlisted fixture scenes there, never in the product.
const Transition = preload("res://scripts/scene_transition.gd")
var checks: Array[Dictionary] = []
var events: Array[String] = []
var output := ""
var overlay: Control
var caller: Control
var opener: Button
var phases: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": label, "passed": passed, "details": details})
	print("PASS " if passed else "FAIL ", label)

func _fixture(path: String, text: String = "[gd_scene format=3]\n[node name=\"Fixture\" type=\"Control\"]\n") -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(text)

func _frames(count: int = 5) -> void:
	for unused in range(count): await process_frame

func _until_phase(expected: StringName) -> void:
	for unused in range(180):
		if overlay.phase == expected: return
		await process_frame
	_record("Reached phase " + str(expected), false, overlay.snapshot())

func _make_caller() -> void:
	caller = Control.new()
	root.add_child(caller)
	current_scene = caller
	opener = Button.new()
	opener.text = "Open scene"
	caller.add_child(opener)
	opener.grab_focus()

func _run() -> void:
	if not ProjectSettings.get_setting("test/scene_transition_fixture", false):
		push_error("This suite requires its own minimal fixture project; refusing to write product scenes.")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute("res://scenes")
	root.size = Vector2i(960, 600)
	_fixture("res://scenes/courtyard.tscn")
	# Other fixtures start absent so missing-path recovery is tested against real I/O.
	_make_caller()
	overlay = Transition.new()
	root.add_child(overlay)
	overlay.completed.connect(func(id: StringName): events.append("done:" + str(id)))
	overlay.failed.connect(func(id: StringName, _message: String): events.append("failed:" + str(id)))
	overlay.cancelled.connect(func(id: StringName): events.append("cancelled:" + str(id)))
	overlay.phase_changed.connect(func(next: StringName, text: String, progress: float): phases.append({"phase":str(next),"message":text,"progress":progress}))
	await _frames()
	_record("Unknown IDs and arbitrary paths cannot navigate", not overlay.begin(&"online", caller, opener) and not overlay.begin(&"res://scenes/courtyard.tscn", caller, opener) and not overlay.begin(&"../courtyard", caller, opener))
	_record("Rejected paths do not alter caller input", caller.process_mode == Node.PROCESS_MODE_INHERIT and not overlay.visible and events.is_empty())
	var child_overlay := Transition.new()
	caller.add_child(child_overlay)
	_record("Loader cannot be owned by the scene it will replace", not child_overlay.begin(&"courtyard", caller, opener))
	child_overlay.queue_free()
	var other := Transition.new()
	root.add_child(other)
	paused = true
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	var previous_mouse_mode := Input.mouse_mode
	_record("Allowed destination begins immediately", overlay.begin(&"courtyard", caller, opener))
	_record("Visible queued state precedes resource work", overlay.visible and overlay.phase == &"queued" and overlay.resource_progress == -1 and not overlay.progress_bar.visible)
	_record("Caller processing is disabled while loading", caller.process_mode == Node.PROCESS_MODE_DISABLED)
	_record("Duplicate and competing transitions are rejected", not overlay.begin(&"courtyard", caller, opener) and not other.begin(&"courtyard", caller, opener))
	_record("Queued transition can be cancelled once", overlay.cancel() and not overlay.cancel())
	_record("Cancel restores pause, mouse, processing and opener focus", paused and Input.mouse_mode == previous_mouse_mode and caller.process_mode == Node.PROCESS_MODE_INHERIT and root.gui_get_focus_owner() == opener)
	await _frames()
	_record("Cancelled queued callbacks cannot complete", events == ["cancelled:courtyard"] and current_scene == caller)
	paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_record("Missing allowlisted scene is accepted for recoverable validation", overlay.begin(&"confluence", caller, opener))
	await _until_phase(&"error")
	_record("Missing file shows one failure and Retry/Back", events.count("failed:confluence") == 1 and overlay.retry_button.visible and not overlay.back_button.disabled and overlay.resource_progress == -1)
	_record("Error focus reaches retry", root.gui_get_focus_owner() == overlay.retry_button)
	await _frames()
	_record("Recovery controls remain inside the viewport", root.get_visible_rect().encloses(overlay.card.get_global_rect()), {"viewport":str(root.get_visible_rect()), "card":str(overlay.card.get_global_rect())})
	_record("Recovery Tab order stays within Retry and Back", overlay.retry_button.find_next_valid_focus() == overlay.back_button and overlay.back_button.find_next_valid_focus() == overlay.retry_button)
	_record("Recovery dialog rejects duplicate begin", not overlay.begin(&"courtyard", caller, opener))
	_fixture("res://scenes/confluence_world.tscn")
	_record("Retry starts a new attempt and rejects repeated retry", overlay.retry() and not overlay.retry())
	await _until_phase(&"done")
	_record("Real threaded PackedScene load replaces current scene", current_scene != caller and current_scene.name == "Fixture" and events.count("done:confluence") == 1)
	await _frames()
	_record("Completion fires exactly once and loader releases ownership", events.count("done:confluence") == 1 and not root.has_meta(Transition.OWNER_META) and not overlay.visible)
	var prior_scene := current_scene
	# Cancel from the actual load-request callback before polling can commit it.
	var cancel_on_loading := func(next: StringName, _message: String, _progress: float):
		if next == &"loading": overlay.cancel()
	overlay.phase_changed.connect(cancel_on_loading)
	_record("Completed overlay is reusable", overlay.begin(&"courtyard", current_scene))
	await _until_phase(&"cancelled")
	overlay.phase_changed.disconnect(cancel_on_loading)
	await _frames(10)
	_record("Cancelled threaded completion does not navigate", current_scene == prior_scene and events.count("done:courtyard") == 0 and events.count("cancelled:courtyard") == 2)
	_record("Cancelled path may be requested again", overlay.begin(&"courtyard", current_scene))
	await _until_phase(&"done")
	_record("Reuse after cancellation completes exactly once", events.count("done:courtyard") == 1)
	var cancel_on_construct := func(next: StringName, _message: String, _progress: float):
		if next == &"constructing": overlay.cancel()
	overlay.phase_changed.connect(cancel_on_construct)
	prior_scene = current_scene
	_record("Another loaded scene can begin", overlay.begin(&"confluence", current_scene))
	await _until_phase(&"cancelled")
	overlay.phase_changed.disconnect(cancel_on_construct)
	await _frames()
	_record("Cancel before construction invalidates deferred commit", current_scene == prior_scene and events.count("done:confluence") == 1)
	# A malformed text resource is rejected by the real loader, not a mocked status.
	_fixture("res://scenes/combat_film.tscn", "[gd_scene format=3]\nthis is not a node declaration\n")
	_record("Malformed local scene starts recoverable load", overlay.begin(&"combat_film", current_scene))
	await _until_phase(&"error")
	_record("Failed resource load preserves the previous scene", current_scene == prior_scene and events.count("failed:combat_film") == 1)
	_record("Back after failure restores caller and hides recovery", overlay.cancel() and not overlay.visible and current_scene.process_mode == Node.PROCESS_MODE_INHERIT)
	# Disposing an active loader must also restore the caller and release its lease.
	_record("Fresh loader can acquire released ownership", other.begin(&"courtyard", current_scene))
	other.queue_free()
	await _frames()
	_record("Disposal restores input and cannot leave owner metadata", current_scene.process_mode == Node.PROCESS_MODE_INHERIT and not root.has_meta(Transition.OWNER_META))
	var disposing := Transition.new()
	root.add_child(disposing)
	disposing.phase_changed.connect(func(next: StringName, _text: String, _progress: float):
		if next == &"loading": disposing.queue_free())
	prior_scene = current_scene
	_record("Disposal test starts a real load request", disposing.begin(&"confluence", current_scene))
	await _frames(12)
	_record("Disposed threaded request cannot navigate or hold caller input", current_scene == prior_scene and current_scene.process_mode == Node.PROCESS_MODE_INHERIT and not root.has_meta(Transition.OWNER_META))
	var honest := true
	var saw_construction := false
	for item in phases:
		honest = honest and (item.progress == -1.0 or (item.phase == "loading" and item.progress >= 0.0 and item.progress <= 1.0))
		if item.phase == "constructing":
			saw_construction = true
			honest = honest and item.progress == -1.0 and item.message.contains("Preparing")
	_record("Construction has its own message without an overall percentage", honest and saw_construction)
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var result := {"suite": "scene-transition", "checks": checks, "passed": checks.size() - failures.size(), "failed": failures.size(), "events": events, "phases":phases, "scope": "Godot 4.6.3 headless with actual threaded small PackedScene fixtures. No heavy imports, rendered acceptance or world startup performance claim."}
	if not output.is_empty():
		var file := FileAccess.open(output, FileAccess.WRITE)
		file.store_string(JSON.stringify(result, "\t"))
	print(JSON.stringify({"passed": result.passed, "failed": result.failed}))
	overlay.queue_free()
	await process_frame
	call_deferred("quit", 0 if failures.is_empty() else 1)
