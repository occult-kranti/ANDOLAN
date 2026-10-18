extends SceneTree
## Fixture mode writes only inside the explicitly marked scratch project.
## --native exercises existing product imports without modifying product scenes.
const Transition = preload("res://scripts/scene_transition.gd")
var checks: Array[Dictionary] = []
var output := ""
var phases: Array[String] = []
var completions: Array[String] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool) -> void:
	checks.append({"name":label,"passed":passed})
	print("PASS " if passed else "FAIL ", label)

func _frames(count: int = 4) -> void:
	for unused in range(count): await process_frame

func _until(predicate: Callable) -> bool:
	var deadline := Time.get_ticks_msec() + 60000
	while Time.get_ticks_msec() < deadline:
		if predicate.call(): return true
		await process_frame
	return false

func _write(path: String, content: String) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	file.store_string(content)

func _fixture(id: String, node_name: String) -> void:
	_write("res://scenes/" + id + ".tscn", '[gd_scene load_steps=2 format=3]\n[ext_resource type="Script" path="res://scripts/boot_fixture.gd" id="1"]\n[node name="' + node_name + '" type="Control"]\nscript = ExtResource("1")\n')

func _loader() -> Control:
	return root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition") as Control

func _run() -> void:
	var native := "--native" in OS.get_cmdline_user_args()
	if not native and not ProjectSettings.get_setting("test/scene_transition_fixture", false):
		push_error("Fixture mode requires a separate marked project; refusing product writes.")
		quit(2)
		return
	root.size = Vector2i(960,600)
	root.content_scale_size = Vector2i(960,600)
	if not native:
		DirAccess.make_dir_recursive_absolute("res://scenes")
		_write("res://scripts/boot_fixture.gd", 'extends Control\nvar focus_losses := 0\nvar args: PackedStringArray\nfunc _ready() -> void:\n\targs = OS.get_cmdline_user_args()\n\tget_window().focus_exited.connect(func(): focus_losses += 1)\n')
	_record("Boot script has no cached courtyard resource before entry", not ResourceLoader.has_cached("res://scenes/courtyard.tscn"))
	change_scene_to_file("res://scenes/boot.tscn")
	_record("Light boot mounts before courtyard", await _until(func(): return current_scene != null and current_scene.name == "YugaBoot"))
	var boot: Control = current_scene
	_record("Boot supplies visible fallback actions", boot.open_button.visible and boot.quit_button.visible)
	_record("Boot has no 3D world children", boot.find_children("*", "Node3D", true, false).is_empty())
	_record("Boot creates persistent transition", await _until(func(): return _loader() != null))
	var loader := _loader()
	loader.phase_changed.connect(func(phase: StringName, _message: String, _progress: float): phases.append(str(phase)))
	loader.completed.connect(func(id: StringName): completions.append(str(id)))
	_record("Boot and hosts resolve one loader", Transition.ensure_for_tree(self) == loader and root.find_children("YugaSceneTransitionLayer", "CanvasLayer", false, false).size() == 1)
	_record("Duplicate boot actions cannot create another attempt", not boot.open_game())
	if native:
		var arrived := await _until(func(): return loader.phase == &"done" or loader.phase == &"error")
		_record("Existing imported native courtyard opens through boot", arrived and loader.phase == &"done" and current_scene.scene_file_path == "res://scenes/courtyard.tscn")
		if loader.phase == &"done":
			var expects_training := "--smoke" in OS.get_cmdline_user_args() or "--autostart" in OS.get_cmdline_user_args()
			_record("Native command-line startup semantics preserved", current_scene.started == expects_training and current_scene.smoke_mode == ("--smoke" in OS.get_cmdline_user_args()))
			_record("Native launch adopts the boot loader", current_scene._ensure_scene_transition() == loader)
			_record("Native boot exposes separate construction phase", phases.has("constructing") and phases.has("done"))
			_record("Native training or title is usable", current_scene.player.active if expects_training else current_scene.main_panel.visible)
			root.focus_exited.emit()
			_record("Native focus pause policy remains scene-owned", paused == (expects_training and not current_scene.smoke_mode))
			if paused: current_scene.set_paused(false)
		await _finish(native)
		return
	_record("Missing courtyard produces recoverable boot error", await _until(func(): return loader.phase == &"error"))
	loader.back_button.pressed.emit()
	await _frames()
	_record("Back reaches usable Retry and Quit instead of blank screen", current_scene == boot and not loader.visible and boot.open_button.text.contains("Retry") and not boot.open_button.disabled and not boot.quit_button.disabled)
	_record("Boot recovery restores keyboard focus", root.gui_get_focus_owner() == boot.open_button and boot.open_button.find_next_valid_focus() == boot.quit_button)
	if "--quit-path" in OS.get_cmdline_user_args():
		print("YUGA_BOOT_QUIT_ACTION_EXECUTED")
		boot.quit_button.pressed.emit()
		return
	_record("Boot recovery can start another attempt", boot.open_game())
	_record("Repeated missing load returns to retry", await _until(func(): return loader.phase == &"error"))
	_fixture("courtyard", "CourtyardFixture")
	_fixture("confluence_world", "ConfluenceFixture")
	root.focus_exited.emit()
	_record("Retry accepts repaired courtyard fixture", loader.retry())
	_record("Boot completes a real threaded courtyard scene", await _until(func(): return loader.phase == &"done"))
	_record("Boot source is disposed after successful replacement", not is_instance_valid(boot) and current_scene.name == "CourtyardFixture")
	_record("Observed focus loss reaches the new scene once", current_scene.focus_losses == 1)
	_record("Startup user arguments survive scene replacement", current_scene.args == OS.get_cmdline_user_args())
	_record("One completion follows repaired boot", completions == ["courtyard"])
	_record("Same loader begins world transition", loader.begin(&"confluence", current_scene))
	root.focus_exited.emit()
	root.focus_entered.emit()
	_record("Fixture world completes", await _until(func(): return loader.phase == &"done"))
	_record("Focus regain prevents stale pause delivery", current_scene.name == "ConfluenceFixture" and current_scene.focus_losses == 0)
	_record("Same loader returns to courtyard", loader.begin(&"courtyard", current_scene))
	_record("Fixture courtyard return completes", await _until(func(): return loader.phase == &"done"))
	_record("Boot-title-world-title uses one persistent loader", completions == ["courtyard","confluence","courtyard"] and Transition.ensure_for_tree(self) == loader and root.find_children("YugaSceneTransitionLayer", "CanvasLayer", false, false).size() == 1)
	var cancel_boot := func(phase: StringName, _message: String, _progress: float):
		if phase == &"queued": loader.cancel()
	loader.phase_changed.connect(cancel_boot)
	change_scene_to_file("res://scenes/boot.tscn")
	_record("Boot can reenter using the existing loader", await _until(func(): return current_scene != null and current_scene.name == "YugaBoot" and loader.phase == &"cancelled"))
	loader.phase_changed.disconnect(cancel_boot)
	boot = current_scene
	_record("Cancelled initial load retains Open YUGA and Quit", boot.status.text.contains("Loading stopped") and root.gui_get_focus_owner() == boot.open_button and not loader.visible)
	_record("Cancelled boot can resume", boot.open_game())
	boot.queue_free()
	_record("Disposed boot cannot complete pending navigation", await _until(func(): return loader.phase == &"cancelled"))
	_record("Disposed boot releases navigation ownership", not root.has_meta(Transition.OWNER_META))
	await _finish(native)

func _finish(native: bool) -> void:
	var failures := checks.filter(func(item: Dictionary): return not item.passed)
	var result := {"suite":"ui-boot-native" if native else "ui-boot-fixtures", "passed":failures.is_empty(),"passed_count":checks.size()-failures.size(),"count":checks.size(), "failed":failures.size(), "checks":checks, "phases":phases, "completions":completions, "scope":"Headless native scene lifecycle; resource threading is separate from synchronous construction; no visual or GPU performance acceptance."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"\t") + "\n")
	print(JSON.stringify({"passed":result.passed,"failed":result.failed}))
	if is_instance_valid(current_scene): current_scene.queue_free()
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if layer: layer.queue_free()
	await _frames()
	call_deferred("quit", 0 if failures.is_empty() else 1)
