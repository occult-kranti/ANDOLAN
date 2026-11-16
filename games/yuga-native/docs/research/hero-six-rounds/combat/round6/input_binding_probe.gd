extends SceneTree
const Bindings = preload("res://scripts/input_bindings.gd")
var rows: Array = []

func _initialize() -> void:
	call_deferred("_run")

func _mouse(button: MouseButton, down: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button
	event.pressed = down
	Input.parse_input_event(event)
	Input.flush_buffered_events()

func _check(label: String, expected: bool) -> void:
	rows.append({"case":label,"fire":Input.is_action_pressed("fire"),"expected":expected,"passed":Input.is_action_pressed("fire")==expected,"mouse_mask":Input.get_mouse_button_mask()})

func _run() -> void:
	var source := FileAccess.get_sha256("res://scripts/input_bindings.gd")
	Bindings.install("user://not-present-input-audit-settings.cfg")
	_check("clean",false)
	_mouse(MOUSE_BUTTON_RIGHT,true)
	_check("right_down_alone",false)
	_mouse(MOUSE_BUTTON_RIGHT,false)
	_check("right_up_alone",false)
	_mouse(MOUSE_BUTTON_LEFT,true)
	_check("left_down",true)
	_mouse(MOUSE_BUTTON_LEFT,false)
	_check("left_up",false)
	_mouse(MOUSE_BUTTON_LEFT,true)
	_check("left_down_before_gameplay_release",true)
	Bindings.release_gameplay()
	_check("release_gameplay_while_physical_left_down",false)
	_mouse(MOUSE_BUTTON_RIGHT,true)
	_check("right_down_after_gameplay_release",false)
	_mouse(MOUSE_BUTTON_RIGHT,false)
	_check("right_up_after_gameplay_release",false)
	_mouse(MOUSE_BUTTON_LEFT,false)
	_check("left_up_after_gameplay_release",false)
	var mapped: Array = []
	for event in InputMap.action_get_events("fire"):
		mapped.append({"type":event.get_class(),"button_index":event.button_index if event is InputEventMouseButton else -1})
	var passed: bool = rows.all(func(row): return row.passed) and mapped.size()==1 and mapped[0].button_index==MOUSE_BUTTON_LEFT and source==FileAccess.get_sha256("res://scripts/input_bindings.gd")
	var report := {"passed":passed,"count":rows.size(),"checks":rows,"fire_bindings":mapped,"bindings_sha256":source,"engine":Engine.get_version_info(),"scope":"Exact engine Input.parse_input_event and actual Bindings.install/release_gameplay; no X11 event path, world/render/input injection into the live package, gameplay or runtime edits."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var output := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			output.store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"count":rows.size(),"checks":rows}))
	quit(0 if passed else 1)
