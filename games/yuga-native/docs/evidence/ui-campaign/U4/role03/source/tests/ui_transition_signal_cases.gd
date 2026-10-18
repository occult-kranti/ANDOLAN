extends SceneTree
## Run in the isolated UI transition signal fixture, never in the product project.
const Transition = preload("res://scripts/scene_transition.gd")
var checks: Array[Dictionary] = []
var output := ""
var observed: Array[Dictionary] = []
var completions := 0
var cancellations := 0
var loader: Control

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ", label)

func frames(count: int = 5) -> void:
	for unused in range(count): await process_frame

func until_phase(expected: StringName) -> bool:
	var deadline := Time.get_ticks_msec() + 10000
	while Time.get_ticks_msec() < deadline:
		if loader.phase == expected: return true
		await process_frame
	return false

func capture(next: StringName, message: String, progress: float) -> void:
	observed.append({"phase":str(next),"message":message,"progress":progress,"attempt":loader.snapshot().attempt})

func run() -> void:
	if not ProjectSettings.get_setting("test/ui_transition_signal_fixture", false):
		push_error("Refusing to create fixtures inside a product project.")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute("res://scenes")
	var scene := "[gd_scene format=3]\n[node name=\"Sample\" type=\"Node\"]\n"
	# Real text parsing gives the worker enough work to span repeated headless polls.
	for index in range(5000): scene += "[node name=\"Item%d\" type=\"Node\" parent=\".\"]\n" % index
	var file := FileAccess.open("res://scenes/courtyard.tscn",FileAccess.WRITE)
	file.store_string(scene)
	file.close()
	file = FileAccess.open("res://scenes/confluence_world.tscn",FileAccess.WRITE)
	file.store_string("[gd_scene format=3]\n[node name=\"Second\" type=\"Node\"]\n")
	file.close()
	var caller := Node.new()
	root.add_child(caller)
	current_scene = caller
	loader = Transition.ensure_for_tree(self)
	loader.phase_changed.connect(capture)
	loader.completed.connect(func(_id): completions += 1)
	loader.cancelled.connect(func(_id): cancellations += 1)
	record("Real parse fixture starts",loader.begin(&"courtyard",caller))
	record("Real threaded scene completes",await until_phase(&"done"))
	await frames()
	var duplicates := 0
	for index in range(1,observed.size()):
		if observed[index] == observed[index-1]: duplicates += 1
	record("Unchanged resource polls do not repeat notifications",duplicates == 0,{"duplicate_notifications":duplicates,"total_notifications":observed.size()})
	record("Actual load and construction remain observable",observed.any(func(item):return item.phase=="loading") and observed.any(func(item):return item.phase=="constructing"))
	record("Success emits exactly once",completions == 1)
	var prior := current_scene
	var cancel_on_queue := func(next: StringName,_message: String,_progress: float):
		if next == &"queued": loader.cancel()
	loader.phase_changed.connect(cancel_on_queue)
	record("New attempt accepts reentrant queued cancellation",loader.begin(&"confluence",current_scene) and loader.phase == &"cancelled")
	loader.phase_changed.disconnect(cancel_on_queue)
	await frames(12)
	record("Reentrant cancellation restores caller without late completion",current_scene == prior and current_scene.process_mode == Node.PROCESS_MODE_INHERIT and cancellations == 1 and completions == 1 and not root.has_meta(Transition.OWNER_META))
	record("Cancelled loader can begin another attempt",loader.begin(&"confluence",current_scene))
	record("Reentry completes exactly once",await until_phase(&"done") and completions == 2)
	# Signal boundary check: retain tiny real-valued changes; no percentage rounding.
	var before := observed.size()
	loader._set_phase(&"loading","Boundary sample",0.125)
	loader._set_phase(&"loading","Boundary sample",0.125)
	loader._set_phase(&"loading","Boundary sample",0.125000001)
	loader._set_phase(&"loading","Updated message",0.125000001)
	record("Exact duplicates are suppressed but tiny progress and message changes survive",observed.size()==before+3 and observed[-2].progress==0.125000001)
	loader._set_phase(&"done","Ready.",-1.0)
	var count := observed.size()
	await frames(15)
	record("Terminal state does not emit repeated updates",observed.size()==count and completions==2)
	var detached_start := Node.new()
	var rejected: bool = not loader.begin(&"courtyard",detached_start)
	record("Detached callers cannot acquire navigation ownership",rejected)
	if not rejected: loader.cancel()
	detached_start.free()
	var prior_completions := completions
	var prior_cancellations := cancellations
	var detached_caller := current_scene
	var detach_on_load := func(next: StringName,_message: String,_progress: float):
		if next == &"loading" and detached_caller.get_parent()==root: root.remove_child(detached_caller)
	loader.phase_changed.connect(detach_on_load)
	loader.begin(&"courtyard",detached_caller)
	await frames(40)
	loader.phase_changed.disconnect(detach_on_load)
	record("Detaching a live caller cancels its threaded attempt",loader.phase==&"cancelled" and completions==prior_completions and cancellations==prior_cancellations+1 and not root.has_meta(Transition.OWNER_META) and detached_caller.process_mode==Node.PROCESS_MODE_INHERIT)
	detached_caller.free()
	var failed := checks.filter(func(item):return not item.passed).size()
	var result := {"passed":failed==0,"passed_count":checks.size()-failed,"count":checks.size(),"failed_count":failed,"checks":checks,"scope":"Actual small threaded PackedScene parsing and reentrant cancellation, plus an explicitly synthetic sub-percent signal boundary check. No renderer or total-game percentage claim.","loader_sha256":FileAccess.get_sha256("res://scripts/scene_transition.gd")}
	if not output.is_empty():
		file = FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(result,"  ")+"\n")
	root.get_node("YugaSceneTransitionLayer").queue_free()
	if is_instance_valid(current_scene): current_scene.queue_free()
	await frames()
	quit(0 if failed==0 else 1)
