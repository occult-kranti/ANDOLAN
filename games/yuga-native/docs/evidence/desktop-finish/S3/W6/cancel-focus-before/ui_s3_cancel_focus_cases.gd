extends SceneTree
## Explicit caller children are restored by cancellation callbacks, after the
## loader restores the caller itself. New callback ownership must still win.
const Transition = preload("res://scripts/scene_transition.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, ok: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail})
	print("PASS " if ok else "FAIL ",label)

func frames(count: int = 3) -> void:
	for unused in count: await process_frame

func scenario(kind: String) -> void:
	var host := Control.new()
	host.process_mode=Node.PROCESS_MODE_ALWAYS
	var ui := Control.new()
	ui.process_mode=Node.PROCESS_MODE_ALWAYS
	host.add_child(ui)
	var opener := Button.new()
	opener.text="Return"
	ui.add_child(opener)
	var alternate := Button.new()
	alternate.text="New callback focus"
	alternate.position.x=200
	ui.add_child(alternate)
	root.add_child(host)
	current_scene=host
	opener.grab_focus()
	paused=true
	var loader := Transition.ensure_for_tree(self)
	check(kind+": paused request accepted",loader.begin(&"confluence",host,opener))
	ui.process_mode=Node.PROCESS_MODE_DISABLED
	var replacement := Control.new()
	var callback := func(_destination: StringName):
		if kind!="still_disabled": ui.process_mode=Node.PROCESS_MODE_ALWAYS
		if kind=="new_focus": alternate.grab_focus()
		elif kind=="replacement": root.add_child(replacement);current_scene=replacement
		elif kind=="detached": root.remove_child(host)
		elif kind=="disabled_button": opener.disabled=true
		elif kind=="focus_none": opener.focus_mode=Control.FOCUS_NONE
		elif kind=="queued_delete": opener.queue_free()
		elif kind=="reentry": loader.begin(&"courtyard",host,alternate)
	loader.cancelled.connect(callback)
	if kind=="error":
		var deadline := Time.get_ticks_msec()+3000
		while loader.phase!=&"error" and Time.get_ticks_msec()<deadline: await process_frame
		check("error: missing local resource enters recovery",loader.phase==&"error")
		for down in [true,false]:
			var event := InputEventKey.new()
			event.keycode=KEY_ESCAPE;event.physical_keycode=KEY_ESCAPE;event.pressed=down
			Input.parse_input_event(event)
			await process_frame
	elif kind=="disposed":
		loader.queue_free()
		await frames()
	else: loader.cancel()
	var focus := root.gui_get_focus_owner()
	var focused := focus==opener if is_instance_valid(opener) else false
	if kind in ["queued","error","disposed"]:
		check(kind+": callback-restored opener owns focus",focused and paused and host.process_mode==Node.PROCESS_MODE_ALWAYS and ui.process_mode==Node.PROCESS_MODE_ALWAYS)
	elif kind=="new_focus": check("New explicit callback focus wins",focus==alternate)
	elif kind=="reentry": check("Reentrant attempt retains its loading focus",loader.phase==&"queued" and focus==loader.back_button and root.get_meta(Transition.OWNER_META)==loader)
	else: check(kind+": ineligible or replaced opener cannot regain focus",not focused)
	if is_instance_valid(loader):
		loader.cancelled.disconnect(callback)
		if loader.is_busy(): loader.cancel()
	paused=false
	current_scene=null
	if is_instance_valid(host): host.free()
	if is_instance_valid(replacement): replacement.free()
	await frames()

func run() -> void:
	if not ProjectSettings.get_setting("test/ui_s3_cancel_focus_fixture",false):
		push_error("Refusing product project mutation")
		quit(2);return
	for kind in ["queued","error","disposed","new_focus","replacement","detached","still_disabled","disabled_button","focus_none","queued_delete","reentry"]:
		await scenario(kind)
	var layer := root.get_node_or_null("YugaSceneTransitionLayer")
	if is_instance_valid(layer): layer.queue_free()
	await frames()
	var passed := checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,
		"scope":"Tiny actual loader/error input and cancellation callback ownership. Explicit pause/child process restoration, reentry, replacement, focus eligibility and disposal; no renderer or OS-input acceptance."},"  ")+"\n")
	quit(0 if passed else 1)
