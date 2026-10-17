extends SceneTree
## Real-scene siege menu, focus, layout and presentation lifecycle regressions.
## Run with an isolated XDG_DATA_HOME; no persistent volume setting is written.

var scene: Node3D
var checks: Array = []
var source_hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func check(name_: String, result: bool, details: Dictionary = {}) -> void:
	checks.append({"name":name_,"passed":result,"details":details})
	print("PASS " if result else "FAIL ",name_," ",JSON.stringify(details))

func frames(count_: int = 3) -> void:
	for _i in range(count_): await process_frame

func _tab(reverse: bool=false) -> void:
	var event:=InputEventKey.new()
	event.keycode=KEY_TAB
	event.physical_keycode=KEY_TAB
	event.pressed=true
	event.shift_pressed=reverse
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await frames(2)
	event=InputEventKey.new()
	event.keycode=KEY_TAB
	event.physical_keycode=KEY_TAB
	event.pressed=false
	event.shift_pressed=reverse
	Input.parse_input_event(event)
	Input.flush_buffered_events()
	await frames(2)

func _run() -> void:
	for path in ["res://scripts/confluence_world.gd","res://scripts/lane_army.gd","res://scripts/siege_effects.gd","res://scripts/lane_minion.gd","res://scripts/lane_vehicle_art.gd","res://tests/siege_ui_cases.gd"]:
		source_hashes[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(1280,720)
	var packed = load("res://scenes/confluence_world.tscn")
	scene = packed.instantiate()
	root.add_child(scene)
	await frames()
	check("real world and siege presentation initialize",scene.world_ready and scene.army.report().configured and scene.siege_effects != null)
	scene.player.set_physics_process(false)
	for viewport in [Vector2i(960,600),Vector2i(1280,720)]:
		root.size = viewport
		root.content_scale_size = viewport
		scene.set_paused(true)
		await frames(5)
		var rect: Rect2 = scene.pause_panel.get_global_rect()
		check("pause panel fits " + str(viewport),Rect2(Vector2.ZERO,Vector2(viewport)).encloses(rect),{"rect":str(rect)})
		check("twelve focus targets including invocation, relay, siege and volume " + str(viewport),scene.pause_actions.size()==12 and scene.siege_practice_button in scene.pause_actions and scene.invocation_button in scene.pause_actions)
		var reached := []
		var focus_ok := true
		var scroll_ok := true
		for action in scene.pause_actions:
			action.grab_focus()
			await frames(4)
			reached.append(action.name)
			focus_ok = focus_ok and root.gui_get_focus_owner()==action
			var available: Rect2=scene.pause_scroll.get_global_rect()
			var actual: Rect2=action.get_global_rect()
			scroll_ok = scroll_ok and available.grow(1).encloses(actual)
			var next_control=action.get_node(action.focus_next)
			focus_ok=focus_ok and next_control in scene.pause_actions
		check("all actions scroll into view " + str(viewport),scroll_ok,{"actions":reached})
		scene.pause_actions[0].grab_focus()
		await frames(2)
		for index in range(1,scene.pause_actions.size()+1):
			await _tab()
			focus_ok=focus_ok and root.gui_get_focus_owner()==scene.pause_actions[index%scene.pause_actions.size()]
		check("Tab traverses and wraps every menu control " + str(viewport),focus_ok)
	await _tab(true)
	check("Shift Tab wraps backwards to final menu action",root.gui_get_focus_owner()==scene.pause_actions[-1])
	# Invalid fixture exercises the failure path without replacing the real army.
	var original_army: Dictionary=scene.army.report()
	var original_position: Vector3=scene.player.position
	scene.army.configured=false
	var rejected: bool=not scene._start_siege_practice()
	await frames(12)
	scene.army.configured=true
	check("rejected drill preserves practice and persistent error",rejected and scene.army.report()==original_army and scene.player.position==original_position and scene.paused and scene.pause_panel.visible and "unavailable" in scene.practice_hint_label.text)
	# Signal-driven actual menu entry, not a separately constructed mock army.
	scene.siege_practice_button.pressed.emit()
	await frames()
	var army: Dictionary=scene.army.report()
	check("pause siege action starts six-unit drill",army.get("siege_drill",false) and army.alive==6 and not scene.paused and not paused,{"army":army})
	var roles: Dictionary=army.get("roles_alive",{})
	check("drill role counts and visible copy",roles.get("cannon_cart",0)==2 and roles.get("royal_chariot",0)==2 and scene.practice_mode_label.text=="OFFLINE SIEGE DRILL" and "Enemy siege 2" in scene.score_label.text and "takes no damage" in scene.practice_hint_label.text)
	check("drill spawn enters centre court",scene.player.position.distance_to(Vector3(7,.05,-15))<.02,{"position":str(scene.player.position)})
	check("minimap carries two distinct siege roles",scene.map_control.units.filter(func(u):return u.get("role","") in ["cannon_cart","royal_chariot"]).size()==4)
	# The event source is the real army signal; this isolates UI routing from attack logic.
	var cue={"kind":"windup","id":99801,"role":"cannon_cart","team":"moon","origin":Vector3(0,1,10),"target":Vector3(0,0,-10),"delay":.8,"radius":3.0,"damage":18.0}
	scene.army.siege_event.emit(cue)
	await frames()
	check("army event routes to siege presentation",scene.siege_effects.report().windups>0,{"effects":scene.siege_effects.report()})
	scene._set_volume(0.0,false)
	check("world mute preserves telegraph",scene.siege_effects.report().muted and scene.siege_effects.report().windups>0 and scene.siege_effects.report().playing_voices==0)
	var before: Dictionary=scene.siege_effects.report()
	scene.set_paused(true)
	await frames(6)
	var after: Dictionary=scene.siege_effects.report()
	check("pause freezes siege cue ages",before.states==after.states and after.suspended and after.tree_paused)
	scene.set_paused(false)
	scene.set_overview(true)
	before=scene.siege_effects.report()
	var army_elapsed=scene.army.report().elapsed
	await frames(6)
	after=scene.siege_effects.report()
	check("overview freezes effects and army",before.states==after.states and after.suspended and scene.army.report().elapsed==army_elapsed)
	scene.set_overview(false)
	scene._restart_army()
	await frames()
	army=scene.army.report()
	check("regular restart restores normal round",not army.get("siege_drill",true) and army.alive==30 and army.waves==1,{"army":army})
	check("regular restart clears old presentation",scene.siege_effects.report().active_events==0 and scene.projectiles.get_child_count()==0 and scene.effects.get_child_count()==0)
	check("regular restart returns arrival spawn",scene.player.position.distance_to(Vector3(0,.05,-112))<.02)
	scene._start_siege_practice()
	var key:=InputEventKey.new()
	key.keycode=KEY_F5
	key.physical_keycode=KEY_F5
	key.pressed=true
	scene._unhandled_input(key)
	await frames()
	check("F5 restores regular lane round",not scene.army.report().get("siege_drill",true) and scene.army.report().alive==30)
	scene.set_paused(true)
	var echo:=InputEventKey.new()
	echo.keycode=KEY_ESCAPE
	echo.physical_keycode=KEY_ESCAPE
	echo.pressed=true
	echo.echo=true
	scene._unhandled_input(echo)
	check("Escape echo cannot resume paused practice",scene.paused and paused)
	var stable:=true
	for path in source_hashes: stable=stable and source_hashes[path]==FileAccess.get_sha256(path)
	check("integration sources stable during run",stable)
	paused=false
	scene.queue_free()
	await frames(3)
	OS.delay_msec(80)
	var passed:=true
	for entry in checks: passed=passed and entry.passed
	var report={"passed":passed,"engine":Engine.get_version_info().string,"sources":source_hashes,"checks":checks,"scope":"Headless real-scene integration, menu button callback, injected Tab navigation, focus/scroll rectangles and lifecycle routing. Signal test isolates presentation wiring; independent army suite owns actual attack semantics. No OS click, rendering, listening or performance claim."}
	var output="/tmp/siege-world-ui-cases.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	var file=FileAccess.open(output,FileAccess.WRITE)
	if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	else: passed=false
	print("SIEGE_WORLD_UI ",JSON.stringify(report))
	quit(0 if passed else 1)
