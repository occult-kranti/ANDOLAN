extends SceneTree
## Selected-mode guidance must survive remapping, errors and small UI scales.
const Shell = preload("res://scripts/launch_shell.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := "/tmp/launch-briefing.json"

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func frames() -> void:
	for unused in 6: await process_frame

func check(label: String, passed: bool) -> void:
	checks.append({"name": label, "passed": passed})
	print("PASS " if passed else "FAIL ", label)

func run() -> void:
	root.size = Vector2i(1280, 720)
	root.content_scale_size = Vector2i(1280, 720)
	var shell := Shell.new()
	root.add_child(shell)
	await frames()
	shell.focus_primary()
	var launch_count := [0]
	shell.world_requested.connect(func(): launch_count[0] += 1)
	check("Desktop briefing describes actual lane practice", shell.briefing.visible and shell.briefing.mode == "world" and shell.briefing.first_move.text.contains("wave"))
	check("All five real action bindings are shown", shell.briefing.snapshot().bindings == {"fire":"LMB", "pulse":"Q", "dash":"E", "guardian_circle":"C", "ultimate":"X"})
	check("Briefing fits without covering launch or utility controls", shell.card.get_global_rect().encloses(shell.briefing.get_global_rect()) and shell.briefing.get_global_rect().position.y > shell.primary_button.get_global_rect().end.y and shell.briefing.get_global_rect().end.y < shell.guide_button.get_global_rect().position.y)
	shell.set_mode("train")
	await frames()
	check("Mode selection changes briefing without launch or focus loss", shell.briefing.mode == "train" and shell.briefing.first_move.text.contains("ability") and launch_count[0] == 0 and root.gui_get_focus_owner() == shell.primary_button)
	var original := Bindings.bindings.duplicate()
	Bindings.bindings.pulse = KEY_J
	shell.hide()
	shell.show()
	await frames()
	check("Returning from remapping refreshes the visible key", shell.briefing.snapshot().bindings.pulse == "J")
	shell.set_launch_state("loading")
	check("Loading cannot switch briefing or launch again", not shell.set_mode("world") and shell.briefing.mode == "train" and shell.primary_button.disabled)
	shell.set_launch_state("error", "Try your practice again.")
	shell.set_mode("world")
	check("Recovery clears error and refreshes preserved binding", shell.briefing.mode == "world" and shell.launch_state == "ready" and shell.briefing.snapshot().bindings.pulse == "J")
	for dimensions in [Vector2i(1100, 680), Vector2i(1200, 680), Vector2i(1100, 720)]:
		root.size = dimensions
		root.content_scale_size = dimensions
		await frames()
		shell.focus_primary()
		await frames()
		var actions_fit := true
		for action in shell._actions:
			actions_fit = actions_fit and shell.card.get_global_rect().encloses(action.get_global_rect())
		check("Optional briefing yields to the full utility footer " + str(dimensions), not shell.briefing.visible and actions_fit and shell.card.get_global_rect().encloses(shell.menu_hint.get_global_rect()))
	root.content_scale_size = Vector2i(1280, 720)
	for scale in [1.0, 1.5, 2.0]:
		root.size = Vector2i(960, 540)
		root.content_scale_factor = scale
		await frames()
		shell.focus_primary()
		await frames()
		var fits := shell.scroll.get_global_rect().encloses(shell.primary_button.get_global_rect()) and shell.scroll.get_global_rect().encloses(shell.mode_description.get_global_rect())
		var optional_fits := not shell.briefing.visible or shell.card.get_global_rect().encloses(shell.briefing.get_global_rect())
		check("Compact scale preserves essential mode and action " + str(scale), optional_fits and fits and shell.mode_description.text.contains("Offline") and root.gui_get_focus_owner() == shell.primary_button)
	check("Read-only guidance introduces no focus or navigation action", shell.briefing.focus_mode == Control.FOCUS_NONE and shell._actions.size() == 8)
	Bindings.bindings = original
	var passed := checks.all(func(row: Dictionary): return row.passed)
	var sources := {}
	for path in ["res://scripts/launch_shell.gd", "res://scripts/launch_briefing.gd", get_script().resource_path]: sources[path] = FileAccess.get_sha256(path)
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":sources,"scope":"Native Controls, real current binding data, scale/focus/loading semantics; actual-window pixels/input reviewed separately."}, "  ") + "\n")
	shell.queue_free()
	await frames()
	quit(0 if passed else 1)
