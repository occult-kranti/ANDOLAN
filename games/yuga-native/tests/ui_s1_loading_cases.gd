extends SceneTree
## Tiny marked project only. No product scenes, shader imports or 3D rendering.
const Boot = preload("res://scenes/boot.tscn")
const Transition = preload("res://scripts/scene_transition.gd")
var checks: Array[Dictionary] = []
var loader: Control
var output := ""
var completions := 0
var cancellations := 0

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func frames(count: int = 4) -> void:
	for unused in range(count): await process_frame

func until_phase(expected: StringName) -> bool:
	var deadline := Time.get_ticks_msec()+5000
	while Time.get_ticks_msec()<deadline:
		if loader.phase==expected: return true
		await process_frame
	return false

func mount_boot() -> Control:
	var boot: Control = Boot.instantiate()
	root.add_child(boot)
	current_scene=boot
	await process_frame
	return boot

func detach_case(expected: StringName) -> void:
	var boot: Control = await mount_boot()
	record(str(expected)+": boot reaches actual phase",await until_phase(expected))
	var status_before: String=boot.status.text
	var error_before: String=boot._last_error
	# Boot deliberately processes while paused; sampling after begin would see
	# the loader's temporary DISABLED mode rather than the mode it must restore.
	var mode: int=Node.PROCESS_MODE_ALWAYS
	var before_cancel := cancellations
	root.remove_child(boot)
	var replacement := Control.new()
	var opener := Button.new()
	replacement.add_child(opener)
	root.add_child(replacement)
	current_scene=replacement
	opener.grab_focus()
	await frames(12)
	record(str(expected)+": detached boot cancellation does not update abandoned UI",
		boot.status.text==status_before and boot._last_error==error_before)
	record(str(expected)+": replacement focus and input survive cancellation",
		root.gui_get_focus_owner()==opener and replacement.can_process() and not paused)
	record(str(expected)+": caller restored and navigation owner released once",
		loader.phase==&"cancelled" and cancellations==before_cancel+1 and
		boot.process_mode==mode and completions==0 and not root.has_meta(Transition.OWNER_META))
	boot._on_failed(&"courtyard","late detached failure")
	record(str(expected)+": late failure cannot alter detached boot state",boot._last_error==error_before)
	# The same live object can be reattached and deliberately start again.
	replacement.queue_free()
	await frames()
	root.add_child(boot)
	current_scene=boot
	record(str(expected)+": reattached boot can explicitly retry",boot.open_game())
	loader.cancel()
	record(str(expected)+": visible reattached recovery focuses its opener",
		root.gui_get_focus_owner()==boot.open_button and boot.can_process())
	boot.queue_free()
	await frames()

func run() -> void:
	if not ProjectSettings.get_setting("test/ui_s1_loading_fixture",false):
		push_error("Refusing product project mutation")
		quit(2)
		return
	loader=Transition.ensure_for_tree(self)
	loader.completed.connect(func(_id):completions+=1)
	loader.cancelled.connect(func(_id):cancellations+=1)
	record("Cold fixture has no cached courtyard or 3D scene",not ResourceLoader.has_cached("res://scenes/courtyard.tscn"))
	await detach_case(&"queued")
	await detach_case(&"error")
	# Existing ResourceLoader error recovery stays usable before adding any scene.
	var boot: Control=await mount_boot()
	record("Missing scene remains recoverable",await until_phase(&"error"))
	loader.cancel()
	record("Error Back reaches visible Retry and Quit with focus",
		boot.open_button.text.contains("Retry") and not boot.quit_button.disabled and root.gui_get_focus_owner()==boot.open_button)
	boot.queue_free()
	await frames()
	DirAccess.make_dir_recursive_absolute("res://scenes")
	var file := FileAccess.open("res://scenes/courtyard.tscn",FileAccess.WRITE)
	file.store_string('[gd_scene format=3]\n[node name="TinyCourtyard" type="Control"]\n')
	file.close()
	await detach_case(&"loading")
	for kind in ["hidden","disabled","disabled_button"]:
		boot=await mount_boot()
		var focus_host := Button.new()
		root.add_child(focus_host)
		focus_host.grab_focus()
		if kind=="hidden": boot.hide()
		elif kind=="disabled":
			# The transition restores its actual pre-attempt mode; change that owner
			# mode by cancelling and starting with an already disabled caller.
			loader.cancel()
			boot.process_mode=Node.PROCESS_MODE_DISABLED
			boot.open_game()
		else: boot.open_button.disabled=true
		focus_host.grab_focus()
		loader.cancel()
		record(kind+": inactive recovery does not steal focus",root.gui_get_focus_owner()==focus_host)
		boot.queue_free()
		focus_host.queue_free()
		await frames()
	boot=await mount_boot()
	record("Fresh usable boot completes a real threaded small scene",await until_phase(&"done") and current_scene.name=="TinyCourtyard" and completions==1)
	record("One persistent loader survives detach/error/reentry",Transition.ensure_for_tree(self)==loader and root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false).size()==1)
	var failures := checks.filter(func(item):return not item.passed).size()
	var result := {"suite":"ui-s1-loading","passed":failures==0,"passed_count":checks.size()-failures,
		"count":checks.size(),"checks":checks,"completed":completions,"cancelled":cancellations,
		"scope":"Actual tiny ResourceLoader boot/error/loading/detach/reentry; no 3D render, import, startup timing or GPU claim."}
	file=FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify(result,"  ")+"\n")
	file.close()
	current_scene.queue_free()
	root.get_node("YugaSceneTransitionLayer").queue_free()
	await frames()
	quit(0 if failures==0 else 1)
