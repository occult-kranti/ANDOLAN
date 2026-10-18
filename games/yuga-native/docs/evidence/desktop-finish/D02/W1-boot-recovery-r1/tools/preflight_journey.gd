extends "res://tools/ui-campaign/integrated_capture.gd"
## Executes the same local plan through viewport key dispatch, with no renderer.
## It does not establish OS input, framebuffer quality, or native Quit behavior.
var plan_path := "res://tools/ui-campaign/desktop-journey-plan.json"
var report_path := ""
var checks: Array[Dictionary] = []
var source_pins := {}
var checkpoints: Array[Dictionary] = []
var failed := false

func _initialize() -> void:
	mode = "integrated"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): report_path = argument.trim_prefix("--report=")
		if argument.begins_with("--plan="): plan_path = argument.trim_prefix("--plan=")
	if report_path.is_empty():
		push_error("Journey preflight requires --report in a fresh isolated output directory.")
		quit(2)
		return
	output = report_path.get_base_dir()
	DirAccess.make_dir_recursive_absolute(output)
	Engine.max_fps = 60
	root.size = Vector2i(960,600)
	root.content_scale_size = Vector2i(1280,720)
	for directory in ["scripts","scenes","shaders","assets","NOTICE",".godot/imported"]:
		_pin_directory("res://"+directory)
	for path in ["res://project.godot",plan_path,get_script().resource_path,"res://tools/ui-campaign/observer.gd","res://tools/ui-campaign/integrated_capture.gd","res://tools/ui-campaign/authority_stage.gd"]:
		source_pins[path] = FileAccess.get_sha256(path)
	call_deferred("_boot")
	call_deferred("_run_plan")

func _pin_directory(path: String) -> void:
	var directory := DirAccess.open(path)
	if directory == null: return
	for name in directory.get_files(): source_pins[path+"/"+name] = FileAccess.get_sha256(path+"/"+name)
	for name in directory.get_directories(): _pin_directory(path+"/"+name)

func _process(_delta: float) -> bool:
	# Reuse read-only loader telemetry; skip base framebuffer requests headlessly.
	for node in root.find_children("*", "Control", true, false):
		if node.get_script() and node.get_script().resource_path.ends_with("scene_transition.gd"):
			_observe_transition(node)
	return false

func _frames(count := 4) -> void:
	for unused in count: await process_frame

func _key(name: String) -> bool:
	var code: Key = KEY_ENTER if name == "Return" else OS.find_keycode_from_string(name)
	if code == KEY_NONE: return false
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code
		event.physical_keycode = code
		event.pressed = down
		root.push_input(event)
		await _frames(3)
	return true

func _matches(state: Dictionary, expected: Dictionary) -> bool:
	for path in expected:
		var current: Variant = state
		for part in String(path).split("."):
			current = current.get(part) if current is Dictionary else null
		if current != expected[path]: return false
	return not state.is_empty()

func _wait(expected: Dictionary) -> bool:
	var deadline := Time.get_ticks_msec()+20000
	while Time.get_ticks_msec()<deadline:
		if _matches(snapshot(),expected): return true
		await process_frame
	return false

func _record(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	failed = failed or not passed
	print("PASS " if passed else "FAIL ",label)

func _run_plan() -> void:
	var plan: Variant = JSON.parse_string(FileAccess.get_file_as_string(plan_path))
	if not plan is Array:
		_record("Journey plan parses",false)
		await _finish()
		return
	for index in plan.size():
		var step: Dictionary = plan[index]
		var ok := true
		if step.has("tab_to_name") or step.has("tab_to_text"):
			var field := "focus_name" if step.has("tab_to_name") else "focus_text"
			var target: String = step.get("tab_to_name",step.get("tab_to_text",""))
			for attempt in 40:
				if snapshot().get(field) == target: break
				await _key("Tab")
			ok = snapshot().get(field) == target
		if step.has("expect_exit"):
			# Native capture sends this key and checks the real child-process exit.
			_record("Final Quit target reached; actual exit reserved for native capture",ok and snapshot().focus_name=="Quit")
			break
		if step.has("key"): ok = await _key(step.key) and ok
		if step.has("stage"):
			var authority = load("res://tools/ui-campaign/authority_stage.gd").new()
			var before := snapshot()
			var receipt: Dictionary = authority.perform(current_scene,step.stage)
			receipt.merge({"action":step.stage,"scope":"STAGED AUTHORITY: existing rule fixture; not native play.","before_snapshot":before},true)
			stage_history.append(receipt)
			ok = ok and receipt.get("passed",false)
			await _frames()
		ok = await _wait(step.get("expect",{})) and ok
		var state := snapshot()
		if step.has("capture"): checkpoints.append({"name":step.capture,"snapshot":state,"pixels":false})
		_record("Plan step %02d" % (index+1),ok,{"step":step,"snapshot":state if not ok else {},"frame":state.frame})
		if not ok: break
	await _finish()

func _finish() -> void:
	var changed: Array[String] = []
	for path in source_pins:
		if FileAccess.get_sha256(path) != source_pins[path]: changed.append(path)
	_record("All inspected runtime and capture sources unchanged",changed.is_empty(),{"changed":changed})
	_write(report_path,{"passed":not failed,"count":checks.size(),"checks":checks,"source_sha256":source_pins,"plan_sha256":FileAccess.get_sha256(plan_path),"checkpoints":checkpoints,"stages":stage_history,"transitions":transition_events,"scope":"Headless current configured boot and actual scenes; same journey plan through real viewport keyboard dispatch. Existing actual-rule outcomes are explicitly staged. No XTest, renderer, original PNG, cold-start, OS Quit, package or art acceptance."})
	paused = false
	if is_instance_valid(current_scene): current_scene.queue_free()
	current_scene = null
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if layer: layer.queue_free()
	await _frames(8)
	await create_timer(.08).timeout
	quit(1 if failed else 0)
