extends SceneTree
## Actual scene transitions via wired button signals and injected Escape events.
## No OS click or rendered layout claim; world_scene_cases covers logical UI bounds.

var checks: Array[Dictionary] = []
var sources: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for path in ["res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/player.gd","res://scenes/courtyard.tscn","res://scenes/confluence_world.tscn","res://assets/world/confluence-map.json","res://tests/world_flow_cases.gd"]:
		sources[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(1280,720)
	var error := change_scene_to_file("res://scenes/courtyard.tscn")
	if error != OK or not await _wait_scene("res://scenes/courtyard.tscn"):
		_record("courtyard scene opens",false,{"error":error})
		await _finish()
		return
	for round_index in range(3):
		var courtyard := current_scene
		var courtyard_ref: WeakRef = weakref(courtyard)
		var explore := courtyard.find_child("ExploreConfluence",true,false) as Button
		var menu_ready: bool=is_instance_valid(explore) and explore.is_visible_in_tree() and not explore.disabled and courtyard.main_panel.visible and not courtyard.started and not courtyard.player.active and not paused
		_record("menu ready before transition " + str(round_index+1),menu_ready,{"button_visible":is_instance_valid(explore) and explore.is_visible_in_tree()})
		if not menu_ready: break
		# Exercise the real connected callback, including courtyard menu sound and
		# change_scene_to_file, rather than calling the world constructor directly.
		explore.pressed.emit()
		var world_open := await _wait_scene("res://scenes/confluence_world.tscn")
		var world := current_scene
		var previous_freed: bool=not is_instance_valid(courtyard_ref.get_ref())
		var ready: bool=world_open and world.get("world_ready")==true and world.player.model_ready and world.player.active and not paused and previous_freed
		_record("Explore button enters actual world " + str(round_index+1),ready,{"scene":world.scene_file_path if is_instance_valid(world) else "","courtyard_freed":previous_freed})
		if not ready: break
		var world_ref: WeakRef = weakref(world)
		await _key(KEY_ESCAPE)
		var menu_paused: bool=world.paused and paused and world.pause_panel.visible and not world.player.active
		_record("Escape opens world pause menu " + str(round_index+1),menu_paused,{})
		var back: Button
		for candidate in world.pause_panel.find_children("*","Button",true,false):
			if candidate.text=="Return to courtyard": back=candidate
		if not is_instance_valid(back):
			_record("return button exists",false,{})
			break
		back.pressed.emit()
		var returned := await _wait_scene("res://scenes/courtyard.tscn")
		var no_world_left: bool=not is_instance_valid(world_ref.get_ref()) and get_nodes_in_group("confluence_authority_blocker").is_empty() and get_nodes_in_group("confluence_floor").is_empty()
		var menu_returned: bool=returned and current_scene.main_panel.visible and not current_scene.started and not current_scene.player.active and not paused and no_world_left
		_record("return button restores clean courtyard menu " + str(round_index+1),menu_returned,{"world_freed":not is_instance_valid(world_ref.get_ref()),"world_collision_groups_removed":no_world_left})
		if not menu_returned: break
	var unchanged := true
	for path in sources:
		unchanged=unchanged and sources[path]==FileAccess.get_sha256(path)
	_record("flow sources unchanged during run",unchanged,{})
	await _finish()

func _wait_scene(path: String) -> bool:
	for _i in range(120):
		await process_frame
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path:
			for _j in range(3): await process_frame
			return true
	return false

func _key(code: Key) -> void:
	var down := InputEventKey.new()
	down.physical_keycode=code
	down.keycode=code
	down.pressed=true
	Input.parse_input_event(down)
	Input.flush_buffered_events()
	for _i in range(2): await physics_frame
	var up := InputEventKey.new()
	up.physical_keycode=code
	up.keycode=code
	up.pressed=false
	Input.parse_input_event(up)
	Input.flush_buffered_events()
	for _i in range(2): await physics_frame

func _record(label: String,passed: bool,details: Dictionary) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _finish() -> void:
	paused=false
	if is_instance_valid(current_scene):
		current_scene.queue_free()
		await process_frame
		await process_frame
	var passed := checks.size()==13
	for check in checks: passed=passed and check.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"sources":sources,"checks":checks,
		"scope":"Three complete courtyard -> wired Explore button -> real world -> injected Escape -> wired Return button -> fresh courtyard cycles, with old instances and collision groups removed. Headless scene lifecycle and callback proof; not OS input, image quality or online match evidence."}
	print("YUGA_WORLD_FLOW ",JSON.stringify(report))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report,"\t")+"\n")
			else: passed=false
	quit(0 if passed else 1)
