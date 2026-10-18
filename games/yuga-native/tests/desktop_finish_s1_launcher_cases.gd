extends SceneTree
## Source-bound launch lifecycle/style ownership; actual composition needs renders.
const SHELL = preload("res://scripts/launch_shell.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("_run")

func _check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ", label)

func _frames() -> void:
	for unused in 5: await process_frame

func _run() -> void:
	root.size = Vector2i(1280,720)
	root.content_scale_size = Vector2i(1280,720)
	var first := SHELL.new()
	root.add_child(first)
	await _frames()
	var selected_style: StyleBox = first.world_mode_button.get_theme_stylebox("normal")
	var other_style: StyleBox = first.train_mode_button.get_theme_stylebox("normal")
	first.film_button.grab_focus()
	first.set_launch_state("loading", "Preparing actual practice…")
	first.set_launch_state("error", "Opening failed. Try again.")
	first.set_launch_state("ready")
	first.set_mode("world")
	await _frames()
	_check("Unchanged practice keeps private style resources across loading/error/status refresh", first.world_mode_button.get_theme_stylebox("normal") == selected_style and first.train_mode_button.get_theme_stylebox("normal") == other_style)
	_check("Status refresh preserves selection and host-restored footer focus", first.selected_mode == "world" and first.world_mode_button.button_pressed and root.gui_get_focus_owner() == first.film_button)
	var second := SHELL.new()
	root.add_child(second)
	await _frames()
	var peer_style := second.world_mode_button.get_theme_stylebox("normal") as StyleBoxFlat
	var own_style := selected_style as StyleBoxFlat
	var before := peer_style.border_color
	own_style.border_color = Color.MAGENTA
	_check("Two launcher instances cannot mutate each other's selector resources", peer_style != own_style and peer_style.border_color == before)
	first.set_mode("train")
	await _frames()
	_check("Changing selection replaces role resources and pressed states together", first.world_mode_button.get_theme_stylebox("normal") != selected_style and first.train_mode_button.get_theme_stylebox("normal") != other_style and not first.world_mode_button.button_pressed and first.train_mode_button.button_pressed)
	var new_style := first.train_mode_button.get_theme_stylebox("normal")
	first.set_launch_state("ready", "Practice is ready")
	_check("A new selected role also survives unrelated status refresh", first.train_mode_button.get_theme_stylebox("normal") == new_style)
	var quiet := true
	var primary_count := 0
	for action in first._actions:
		if action.theme_type_variation == &"YugaUtilityButton": quiet = quiet and action.flat and action.focus_mode == Control.FOCUS_ALL and action.get_combined_minimum_size().y >= 44
		if action.theme_type_variation == &"YugaPrimaryButton": primary_count += 1
	_check("Quiet navigation keeps native focus and hit areas with one primary action", quiet and primary_count == 1 and not first.primary_button.flat)
	second.queue_free()
	await _frames()
	for dimensions in [Vector2i(960,600),Vector2i(1280,720),Vector2i(1366,768),Vector2i(1920,1080)]:
		root.content_scale_size = dimensions
		root.size = dimensions
		await _frames()
		var decision: Control = first.find_child("PracticeDecision",true,false)
		var footer: Control = first.find_child("LaunchFooter",true,false)
		var fit := first.card.get_global_rect().encloses(footer.get_global_rect()) and decision.get_global_rect().end.y < footer.get_global_rect().position.y
		for action in first._actions: fit = fit and first.card.get_global_rect().encloses(action.get_global_rect())
		_check("Practice and footer remain separated and fully reachable " + str(dimensions), fit, {"decision":str(decision.get_global_rect()),"footer":str(footer.get_global_rect()),"card":str(first.card.get_global_rect())})
	var passed := checks.all(func(row: Dictionary): return row.passed)
	var report := {"passed":passed,"count":checks.size(),"checks":checks,"sources":{},"scope":"Headless native layout, semantic control roles and mutable style lifecycle; no actual-window/rendered approval."}
	for path in ["res://scripts/launch_shell.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]: report.sources[path] = FileAccess.get_sha256(path)
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	first.queue_free()
	await process_frame
	quit(0 if passed else 1)
