extends SceneTree
## Actual nested screens retain the keyboard owner of the expanded world key.
var output := "/tmp/desktop-s5-overview-navigation.json"
var checks: Array[Dictionary] = []
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func frames(count := 5) -> void:
	for unused in count: await process_frame
func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await frames(2)
func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func run() -> void:
	root.size=Vector2i(960,540)
	root.content_scale_size=Vector2i(1280,720)
	var sources := {}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_hero_hud.gd","res://scripts/controls_overlay.gd",get_script().resource_path]: sources[path]=FileAccess.get_sha256(path)
	var world: Node3D=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	await frames()
	world.rama_runtime.set_volume(0)
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale
		await frames()
		await key(KEY_F1)
		check("Overview establishes visible keyboard owner at scale " + str(scale),world.overview and world.atlas_guide.visible and root.gui_get_focus_owner()==world.atlas_guide_scroll)
		var army: Dictionary=world.army.report()
		var kit: Dictionary=world.rama_runtime.kit.report()
		for route in [{"key":KEY_ESCAPE,"name":"pause"},{"key":KEY_F3,"name":"Rama guide"},{"key":KEY_F2,"name":"controls"}]:
			await key(route.key)
			var nested: bool=world.paused and paused and not world.atlas_guide.visible
			await key(KEY_ESCAPE)
			var focused:=root.gui_get_focus_owner()
			check(route.name+" returns exact overview scroll owner at scale "+str(scale),nested and world.overview and not world.paused and world.atlas_guide.visible and focused==world.atlas_guide_scroll,{"focus":str(focused),"overview":world.overview,"guide":str(world.atlas_guide.get_global_rect())})
			world.atlas_guide_scroll.scroll_vertical=0
			var bar: VScrollBar=world.atlas_guide_scroll.get_v_scroll_bar()
			await key(KEY_DOWN)
			check(route.name+" return retains keyboard reading at scale "+str(scale),bar.max_value<=bar.page+1 or world.atlas_guide_scroll.scroll_vertical>0,{"offset":world.atlas_guide_scroll.scroll_vertical,"max":bar.max_value,"page":bar.page})
			await key(KEY_END)
			var end_reached: bool=absf(float(world.atlas_guide_scroll.scroll_vertical)-(bar.max_value-bar.page))<=1
			await key(KEY_HOME)
			check(route.name+" keyboard reaches full key then returns to heading at scale "+str(scale),end_reached and world.atlas_guide_scroll.scroll_vertical==0)
			check(route.name+" return preserves suspended combat at scale "+str(scale),world.army.report()==army and world.rama_runtime.kit.report()==kit and not world.player.active and world.rama_runtime.suspended)
		await key(KEY_F1)
		check("Live practice exit releases overview keyboard focus at scale "+str(scale),not world.overview and not world.atlas_guide.visible and world.player.active and root.gui_get_focus_owner()!=world.atlas_guide_scroll)
	var stable:=true
	for path in sources:stable=stable and sources[path]==FileAccess.get_sha256(path)
	check("Current screen sources stable during observation",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":sources,"scope":"Actual native F1/Escape/F3/F2 dispatch and nested screen keyboard ownership at100/200% production logical scale. Authority observation only. No OS input, pixels or performance acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(8)
	quit(0 if result.passed else 1)
