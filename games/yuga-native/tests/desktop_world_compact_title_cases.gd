extends SceneTree
## Live HUD refresh and native resize signals must share one lane visibility rule.
var output := "/tmp/desktop-world-compact-title.json"
var checks: Array[Dictionary] = []
var timeline: Array[Dictionary] = []
var world: Node3D
var stage := "boot"
var sources: Dictionary = {}

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 8) -> void:
	for unused in count: await process_frame

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func record(kind: String) -> void:
	timeline.append({"stage":stage,"kind":kind,"frame":Engine.get_process_frames(),"logical":str(root.get_visible_rect().size),"lane_visible":world.lane_label.visible,"title":str(world.hud.get_node("TitleCard").get_global_rect()),"relay":str(world.hud.get_node("RelayStatus").get_global_rect()),"constrained":world._constrained_world})

func key(code: Key) -> void:
	for down in [true,false]:
		var event:=InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await frames(2)

func observe(scale: float, ended := false) -> void:
	stage=("ended-" if ended else "live-")+str(scale)
	root.content_scale_factor=scale
	await frames(16)
	var start:=timeline.size()
	var visible_ok:=true
	var expected: bool=root.get_visible_rect().size.x>=1100 and not ended
	for sample in 32:
		await process_frame
		record("sample")
		visible_ok=visible_ok and world.lane_label.visible==expected
	var events:=0
	var resizes:=0
	for index in range(start,timeline.size()):
		if timeline[index].kind=="visibility": events+=1
		if timeline[index].kind=="title-resized": resizes+=1
	check("settled lane visibility stays correct without refresh toggles: "+stage,visible_ok and events==0,{"expected":expected,"visibility_events":events,"title_resize_events":resizes,"samples":32,"logical":str(root.get_visible_rect().size)})

func run() -> void:
	Engine.max_fps=60
	root.size=Vector2i(960,540)
	root.content_scale_size=Vector2i(1280,720)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/lane_army.gd",get_script().resource_path]: sources[path]=FileAccess.get_sha256(path)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	await frames(8)
	# Freeze simulation only. The world presentation process, its .12s HUD
	# refresh and native container/viewport signals remain active throughout.
	world.set_physics_process(false)
	world.player.set_physics_process(false)
	world.army.set_physics_process(false)
	world.lane_label.visibility_changed.connect(func():record("visibility"))
	world.hud.get_node("TitleCard").resized.connect(func():record("title-resized"))
	var army_before: Dictionary=world.army.report()
	for scale in [1.0,1.25,1.5,2.0,1.0]: await observe(scale)
	check("presentation transitions preserve live authority and active processing",world.army.report()==army_before and world.is_processing() and not world.paused)
	root.content_scale_factor=1.25;await frames(16)
	for route in [{"key":KEY_ESCAPE,"name":"pause cancel"},{"key":KEY_F2,"name":"controls cancel"}]:
		await key(route.key)
		var opened: bool=world.paused
		await key(KEY_ESCAPE)
		await frames(16)
		check("modal return keeps compact lane hidden: "+route.name,opened and not world.paused and not world.lane_label.visible and world.army.report()==army_before)
	# Stage a destroyed core, then use the existing army simulation/outcome
	# route. This is a deterministic terminal UI fixture, not a played match.
	world.army.cores.moon=0
	world.army.step_simulation()
	await frames(8)
	check("existing core outcome opens terminal pause",world.army.winner=="sun" and world.paused and world.objective_label.text.contains("victory"),{"winner":world.army.winner,"objective":world.objective_label.text})
	world.set_paused(false)
	var terminal: Dictionary=world.army.report()
	for scale in [1.0,1.25,1.5,2.0,1.0]: await observe(scale,true)
	check("terminal return and scale changes preserve outcome authority",world.army.report()==terminal and world.army.winner=="sun" and not world.paused)
	var stable:=true
	for path in sources: stable=stable and sources[path]==FileAccess.get_sha256(path)
	check("observed sources remain unchanged",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"timeline":timeline,"sources":sources,"scope":"Headless actual world-process-active production scale100→125→150→200→100, native container/visibility signals, real pause/help cancel keys and staged core outcome. Simulation physics frozen except one authority outcome step. No manual layout/HUD refresh calls, pixels or hardware acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(8)
	await create_timer(.08,true,false,true).timeout
	quit(0 if result.passed else 1)
