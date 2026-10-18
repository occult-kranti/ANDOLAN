extends SceneTree
## Seeded real-resource lifecycle census; only runs in a disposable tiny fixture.
const Transition = preload("res://scripts/scene_transition.gd")
var loader: Control
var checks: Array[Dictionary] = []
var events: Array[Dictionary] = []
var sequence: Array[Dictionary] = []
var completed := 0
var cancelled := 0
var failed := 0
var output := ""
var seed_value := 741903
var rng := RandomNumberGenerator.new()

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
		if arg.begins_with("--seed="): seed_value = int(arg.trim_prefix("--seed="))
	call_deferred("run")

func record(label: String, ok: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"details":detail})
	print("PASS " if ok else "FAIL ",label)

func frames(n: int = 3) -> void:
	for unused in range(n): await process_frame

func until_phase(target: StringName) -> bool:
	var deadline := Time.get_ticks_msec()+5000
	while Time.get_ticks_msec()<deadline:
		if loader.phase==target: return true
		await process_frame
	return false

func census() -> Dictionary:
	var layers := root.find_children("YugaSceneTransitionLayer","CanvasLayer",false,false)
	return {"layers":layers.size(),"same_loader":Transition.ensure_for_tree(self)==loader,"owner":root.has_meta(Transition.OWNER_META),"phase":str(loader.phase),"completed":completed,"cancelled":cancelled,"failed":failed,"pending":loader._abandoned.size(),"scene":current_scene.scene_file_path if is_instance_valid(current_scene) else ""}

func run() -> void:
	if not ProjectSettings.get_setting("test/ui_transition_stress_fixture",false):
		push_error("Refusing product project mutation")
		quit(2)
		return
	rng.seed=seed_value
	DirAccess.make_dir_recursive_absolute("res://scenes")
	for path in ["courtyard","confluence_world"]:
		var body := "[gd_scene format=3]\n[node name=\"Tiny\" type=\"Control\"]\n[node name=\"Opener\" type=\"Button\" parent=\".\"]\ntext = \"Open\"\n"
		for index in range(1200): body += "[node name=\"N%d\" type=\"Node\" parent=\".\"]\n" % index
		var file := FileAccess.open("res://scenes/"+path+".tscn",FileAccess.WRITE)
		file.store_string(body)
		file.close()
	var initial := Control.new()
	var button := Button.new()
	button.name="Opener"
	initial.add_child(button)
	root.add_child(initial)
	current_scene=initial
	loader=Transition.ensure_for_tree(self)
	loader.phase_changed.connect(func(phase,message,progress): events.append({"phase":str(phase),"message":message,"progress":progress,"attempt":loader.snapshot().attempt}))
	loader.completed.connect(func(_id):completed+=1)
	loader.cancelled.connect(func(_id):cancelled+=1)
	loader.failed.connect(func(_id,_message):failed+=1)
	for cycle in range(4):
		var cases := ["valid","invalid","queued","loading","constructing","missing","detach","reentrant"]
		for index in range(cases.size()-1,0,-1):
			var selected := rng.randi_range(0,index)
			var old: String=cases[index]
			cases[index]=cases[selected]
			cases[selected]=old
		for kind in cases:
			var before := census()
			var caller := current_scene
			var opener: Control=caller.get_node("Opener")
			caller.process_mode=Node.PROCESS_MODE_ALWAYS if cycle%2==0 else Node.PROCESS_MODE_INHERIT
			var mode := caller.process_mode
			paused=cycle%2==1
			opener.grab_focus()
			var old_pause := paused
			var id: StringName=&"courtyard" if (cycle+sequence.size())%2==0 else &"confluence"
			var c0 := completed
			var x0 := cancelled
			var f0 := failed
			var ok := true
			match kind:
				"invalid":
					var ticket: int=loader.snapshot().attempt
					for invalid in [&"",&"res://scenes/courtyard.tscn",&"../../outside",&"unknown"]: ok=not loader.begin(invalid,caller,opener) and ok
					ok=ok and loader.snapshot().attempt==ticket and current_scene==caller
				"valid":
					ok=loader.begin(id,caller,opener) and not loader.begin(id,caller,opener)
					ok=await until_phase(&"done") and ok
					ok=ok and completed==c0+1 and cancelled==x0
				"queued":
					ok=loader.begin(id,caller,opener) and not loader.begin(id,caller,opener) and loader.cancel() and not loader.cancel()
					ok=ok and current_scene==caller and cancelled==x0+1
				"loading":
					loader.begin(id,caller,opener)
					ok=await until_phase(&"loading")
					ok=loader.cancel() and ok
					ok=loader.begin(id,caller,opener) and ok
					ok=await until_phase(&"done") and ok
					ok=ok and completed==c0+1 and cancelled==x0+1
				"constructing":
					loader.begin(id,caller,opener)
					ok=await until_phase(&"constructing")
					ok=loader.cancel() and ok
					ok=ok and current_scene==caller and completed==c0 and cancelled==x0+1
				"missing":
					loader.begin(&"combat_film",caller,opener)
					ok=await until_phase(&"error")
					ok=ok and root.has_meta(Transition.OWNER_META) and not loader.begin(id,caller,opener) and loader.retry()
					ok=await until_phase(&"error") and ok
					ok=loader.cancel() and ok and failed==f0+2 and cancelled==x0+1 and current_scene==caller
				"detach":
					loader.begin(id,caller,opener)
					ok=await until_phase(&"loading")
					root.remove_child(caller)
					await frames()
					ok=ok and loader.phase==&"cancelled" and not loader.begin(id,caller,opener) and caller.process_mode==mode
					root.add_child(caller)
					current_scene=caller
					opener.grab_focus()
					ok=ok and completed==c0 and cancelled==x0+1
				"reentrant":
					var queue_cancel := func(phase,_message,_progress):
						if phase==&"queued": loader.cancel()
					loader.phase_changed.connect(queue_cancel)
					ok=loader.begin(id,caller,opener) and loader.phase==&"cancelled"
					loader.phase_changed.disconnect(queue_cancel)
					var reenter := func(_id): loader.begin(id,current_scene,current_scene.get_node("Opener"))
					loader.cancelled.connect(reenter,CONNECT_ONE_SHOT)
					loader.begin(id,caller,opener)
					ok=loader.cancel() and ok
					ok=await until_phase(&"done") and ok
					ok=ok and cancelled==x0+2 and completed==c0+1
			await frames(8)
			var after := census()
			ok=ok and after.layers==1 and after.same_loader and not after.owner and not loader.is_busy()
			if current_scene==caller:
				ok=ok and caller.process_mode==mode and paused==old_pause and root.gui_get_focus_owner()==opener
			sequence.append({"cycle":cycle,"case":kind,"destination":str(id),"before":before,"after":after})
			record("%02d %s" % [sequence.size(),kind],ok,sequence[-1])
			paused=false
			if loader.is_busy() or loader.phase==&"error":loader.cancel()
	var deadline := Time.get_ticks_msec()+5000
	while not loader._abandoned.is_empty() and Time.get_ticks_msec()<deadline: await process_frame
	var duplicates := 0
	for index in range(1,events.size()):
		if events[index]==events[index-1]:duplicates+=1
	record("Exact state notifications remain deduplicated",duplicates==0,{"events":events.size(),"duplicates":duplicates})
	record("All abandoned threaded requests drain",loader._abandoned.is_empty())
	record("Final persistent owner census",census().layers==1 and census().same_loader and not census().owner,census())
	var failures := checks.filter(func(item):return not item.passed).size()
	var result := {"passed":failures==0,"passed_count":checks.size()-failures,"count":checks.size(),"checks":checks,"seed":seed_value,"sequence":sequence,"events":events,"final_census":census(),"scope":"32 seeded real tiny-scene attempts and 3 final lifecycle gates. No product-scene mutation, mocked ResourceLoader, or rendered/performance claim."}
	var out := FileAccess.open(output,FileAccess.WRITE)
	out.store_string(JSON.stringify(result,"  ")+"\n")
	out.close()
	root.get_node("YugaSceneTransitionLayer").queue_free()
	current_scene.queue_free()
	await frames(5)
	OS.delay_msec(30)
	await process_frame
	quit(0 if failures==0 else 1)
