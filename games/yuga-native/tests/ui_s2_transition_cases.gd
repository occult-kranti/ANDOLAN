extends SceneTree
## Real small resources; replacement hosts own their pause, mouse and focus state.
const Transition = preload("res://scripts/scene_transition.gd")
const Boot = preload("res://scripts/boot.gd")
var loader: Control
var checks: Array[Dictionary] = []
var output := ""
var completed := 0
var cancelled := 0
var focus_loss_events := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, ok: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"details":details})
	print("PASS " if ok else "FAIL ",label)

func frames(count: int = 5) -> void:
	for unused in count: await process_frame

func until_phase(value: StringName) -> bool:
	var deadline := Time.get_ticks_msec()+5000
	while Time.get_ticks_msec()<deadline:
		if loader.phase==value: return true
		await process_frame
	return false

func owner() -> Control:
	var host := Control.new()
	host.process_mode=Node.PROCESS_MODE_ALWAYS
	var opener := Button.new()
	opener.name="Opener"
	host.add_child(opener)
	root.add_child(host)
	current_scene=host
	opener.grab_focus()
	return host

func ensure_loader() -> void:
	loader=Transition.ensure_for_tree(self)
	loader.completed.connect(func(_id):completed+=1)
	loader.cancelled.connect(func(_id):cancelled+=1)

func replacement_case(kind: String, phase: StringName) -> void:
	paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	var old := owner()
	var before_cancel := cancelled
	var before_completed := completed
	var before_focus_loss := focus_loss_events
	var destination: StringName = &"confluence" if phase==&"error" else &"courtyard"
	record(kind+": transition begins",loader.begin(destination,old,old.get_node("Opener")))
	record(kind+": requested phase observed",await until_phase(phase))
	loader._focus_lost_during_transition=true
	if kind not in ["attached","attached-error"]: root.remove_child(old)
	if kind=="freed": old.free()
	var replacement := owner()
	paused=true
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	var expected_mouse := Input.mouse_mode
	replacement.get_node("Opener").grab_focus()
	if kind=="disposed":
		loader.queue_free()
		await frames(10)
	else:
		await frames(10)
	record(kind+": retiring load cannot commit over replacement",completed==before_completed and is_instance_valid(replacement) and current_scene==replacement)
	record(kind+": replacement pause and mouse policy survive",
		paused and Input.mouse_mode==expected_mouse,{"paused":paused,"mouse":Input.mouse_mode,"expected_mouse":expected_mouse})
	record(kind+": replacement focus remains owned",is_instance_valid(replacement) and root.gui_get_focus_owner()==replacement.get_node("Opener"))
	record(kind+": cancellation releases navigation exactly once",cancelled==before_cancel+1 and not root.has_meta(Transition.OWNER_META))
	record(kind+": stale window-focus policy is not replayed",focus_loss_events==before_focus_loss)
	if is_instance_valid(old):
		record(kind+": old caller processing is restored",old.process_mode==Node.PROCESS_MODE_ALWAYS)
		old.queue_free()
	paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	if is_instance_valid(current_scene) and current_scene!=replacement and current_scene!=old:
		current_scene.queue_free()
	if is_instance_valid(replacement): replacement.queue_free()
	await frames()
	if kind=="disposed": ensure_loader()

func boot_replacement() -> void:
	var boot := Boot.new()
	root.add_child(boot)
	current_scene=boot
	record("Boot caller starts its automatic attempt",await until_phase(&"queued"))
	var replacement := owner()
	paused=true
	await frames(10)
	record("Attached obsolete boot cannot steal replacement focus",is_instance_valid(replacement) and root.gui_get_focus_owner()==replacement.get_node("Opener") and paused)
	record("Attached obsolete boot cannot restart navigation",not boot.open_game() and not loader.is_busy())
	boot.queue_free()
	if is_instance_valid(current_scene) and current_scene!=replacement: current_scene.queue_free()
	if is_instance_valid(replacement): replacement.queue_free()
	paused=false
	await frames()

func run() -> void:
	if not ProjectSettings.get_setting("test/ui_s2_transition_fixture",false):
		push_error("Refusing product project mutation")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute("res://scenes")
	var file := FileAccess.open("res://scenes/courtyard.tscn",FileAccess.WRITE)
	file.store_string('[gd_scene format=3]\n[node name="LoadedScene" type="Control"]\n')
	file.close()
	ensure_loader()
	root.focus_exited.connect(func():focus_loss_events+=1)
	await replacement_case("detached",&"queued")
	await replacement_case("freed",&"loading")
	await replacement_case("disposed",&"loading")
	await replacement_case("attached",&"queued")
	await replacement_case("attached-error",&"error")
	await boot_replacement()
	var host := owner()
	paused=true
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	var original_mouse := Input.mouse_mode
	record("Same-host cancellation begins while paused",loader.begin(&"courtyard",host,host.get_node("Opener")))
	loader.cancel()
	record("Same-host cancellation still restores original pause mouse and focus",paused and Input.mouse_mode==original_mouse and root.gui_get_focus_owner()==host.get_node("Opener"))
	paused=false
	var before_completed := completed
	record("Reused persistent loader can finish a normal transition",loader.begin(&"courtyard",host))
	record("Normal completion still occurs once",await until_phase(&"done") and completed==before_completed+1 and current_scene.name=="LoadedScene")
	record("Final owner and pending census is clean",not root.has_meta(Transition.OWNER_META) and loader._abandoned.is_empty() and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size()==1)
	var failed := checks.filter(func(item):return not item.passed).size()
	var result := {"passed":failed==0,"passed_count":checks.size()-failed,"count":checks.size(),"checks":checks,
		"scope":"Real tiny threaded resources plus external host replacement/disposal. Headless mouse mode is informational only; no OS capture, rendered loading, GPU or cold-start timing acceptance."}
	file=FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"  ")+"\n")
	file.close()
	if is_instance_valid(current_scene): current_scene.queue_free()
	root.get_node("YugaSceneTransitionLayer").queue_free()
	await frames()
	quit(0 if failed==0 else 1)
