extends SceneTree
## Real world presentation with staged authority values; no traversal timing claim.
const Bindings = preload("res://scripts/input_bindings.gd")
var output := ""
var world_script := "res://scripts/confluence_world.gd"
var checks: Array[Dictionary] = []
var world: Node3D
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
		if arg.begins_with("--world-script="): world_script=arg.trim_prefix("--world-script=")
	call_deferred("run")
func frames(count := 8) -> void:
	for unused in count: await process_frame
func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)
func fit(label: Label, card: Control) -> bool:
	var text_size := label.get_theme_font("font").get_multiline_string_size(label.text,HORIZONTAL_ALIGNMENT_LEFT,label.size.x,label.get_theme_font_size("font_size"))
	return label.is_visible_in_tree() and card.get_global_rect().encloses(label.get_global_rect()) and label.size.y+1>=text_size.y
func update() -> void:
	world._update_practice_hud()
	await frames()
func idle_copy() -> bool:
	return world.ability_label.text=="Energy 100 / 100" and world.goal_label.text=="%s flight · %s tether ≤36m" % [Bindings.label("fly"),Bindings.label("grapple")]
func run() -> void:
	Engine.max_fps=60
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	Bindings.install("user://idle-hud-fixture.cfg")
	world=load(world_script).new()
	root.add_child(world);current_scene=world
	await frames(20)
	Bindings.install("user://idle-hud-fixture.cfg")
	world.set_process(false);world.set_physics_process(false)
	world.player.set_physics_process(false);world.army.set_physics_process(false)
	var traversal=world.player.traversal
	traversal.anchors.clear() # Deterministic no-anchor aim; no active tether is staged.
	traversal.mode="ground";traversal.energy=100;traversal.flight_cooldown=0;traversal.grapple_cooldown=0
	check("actual player is active and grounded",world.player.active and world.player.is_on_floor())
	await update()
	var report_before:Dictionary=traversal.report()
	check("idle retains energy range and both current actions without tutorial repetition",idle_copy(),{"heading":world.ability_label.text,"prompt":world.goal_label.text})
	check("idle normal card is reduced and removes duplicate percentage",world.hud.get_node("TraversalStatus").size.y<116 and not world.energy_bar.show_percentage,{"size":str(world.hud.get_node("TraversalStatus").size)})
	check("idle labels and bar remain inside visible normal card",fit(world.ability_label,world.hud.get_node("TraversalStatus")) and fit(world.goal_label,world.hud.get_node("TraversalStatus")) and world.hud.get_node("TraversalStatus").get_global_rect().encloses(world.energy_bar.get_global_rect()))
	check("presentation leaves traversal authority exact",traversal.report()==report_before)
	var saved:=true
	for step in [["fly",KEY_T],["sprint",KEY_F],["fly",KEY_SHIFT],["grapple",KEY_Y],["jump",KEY_G],["grapple",KEY_SPACE]]:
		saved=saved and Bindings.set_binding(step[0],step[1]).ok
	Bindings.install("user://idle-hud-fixture.cfg")
	await update()
	check("long supported keys save reload and appear in idle copy",saved and Bindings.label("fly")=="Shift" and Bindings.label("grapple")=="Space" and idle_copy())
	check("long actual remap text wraps within normal card without shrinking type",fit(world.goal_label,world.hud.get_node("TraversalStatus")) and world.goal_label.get_theme_font_size("font_size")==14,{"prompt":world.goal_label.text,"size":str(world.hud.get_node("TraversalStatus").size)})
	root.content_scale_factor=2.0;await frames()
	await update()
	check("200 uses existing compact summary and hides normal traversal card",not world.hud.get_node("TraversalStatus").is_visible_in_tree() and world.compact_world_card.is_visible_in_tree())
	check("200 idle summary shares energy range and saved keys",world.compact_world_labels[2].text==world.ability_label.text and world.compact_world_labels[3].text==world.goal_label.text)
	check("200 all four summary rows fit actual text",world.compact_world_labels.all(func(row):return fit(row,world.compact_world_card)))
	traversal.energy=17;traversal.flight_cooldown=4;traversal.grapple_cooldown=1.2
	await update()
	check("cooldown energy and refill survive compact transition",world.compact_world_labels[2].text.contains("Energy 17/100") and world.compact_world_labels[2].text.contains("Flight 4.0s") and world.compact_world_labels[2].text.contains("Tether 1.2s") and world.compact_world_labels[3].text.contains("refill"))
	root.content_scale_factor=1.0;await frames();await update()
	check("nonidle normal card restores original footprint percentage and cooldown detail",world.hud.get_node("TraversalStatus").size.y>=116 and world.energy_bar.show_percentage and world.goal_label.text.contains("Flight 4.0s · Tether 1.2s"))
	traversal.mode="flight";await update()
	check("flight retains ascend descend land and refill guidance",world.goal_label.text.contains("%s rise" % Bindings.label("jump")) and world.goal_label.text.contains("%s descend" % Bindings.label("descend")) and world.goal_label.text.contains("refills"))
	traversal.mode="grapple";await update()
	check("tether retains bound release and flight actions",world.goal_label.text=="%s release tether · %s flight" % [Bindings.label("grapple"),Bindings.label("fly")])
	traversal.mode="ground";traversal.energy=100;traversal.flight_cooldown=0;traversal.grapple_cooldown=0
	world.army.siege_drill=true;await update()
	check("drill keeps contextual instructions and original card",world.goal_label.text.contains("Enemy") and world.hud.get_node("TraversalStatus").size.y>=116 and world.energy_bar.show_percentage)
	world.army.siege_drill=false;world.army.winner="sun";await update()
	check("terminal keeps outcome pause and restart copy",world.goal_label.text=="Round ended · %s pause · %s restart" % [Bindings.label("pause_game"),Bindings.label("world_respawn")])
	world.army.winner="";await update()
	check("return to ready state restores condensed copy",idle_copy() and not world.energy_bar.show_percentage)
	# Pure formatter boundary probes accompany the real active/nonactive presentation above.
	var boundary_ok:=true
	if world.has_method("_idle_traversal_copy"):
		var ready:Dictionary=traversal.report()
		boundary_ok=world._idle_traversal_copy(ready,{},false).is_empty()
		for delta in [{"enabled":false},{"energy":99.9},{"flight_cooldown":0.001},{"grapple_cooldown":0.001},{"candidate":{"id":"ring","position":Vector3.ZERO}},{"mode":"flight"},{"status":"No clear anchor"},{"status":"Aim at a gold ring"}]:
			var staged:Dictionary=ready.duplicate(true);staged.merge(delta,true)
			boundary_ok=boundary_ok and world._idle_traversal_copy(staged,{},true).is_empty()
	check("airborne disabled partial energy cooldown or target cannot enter idle shortcut",boundary_ok)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"world_script":world_script,"sources":{},"scope":"Real world controls/native canvas100→200→100, real persisted supported key remaps; fixture-staged authority values, not action timing or pixel acceptance."}
	for path in [world_script,"res://scripts/player.gd","res://scripts/player_traversal.gd","res://scripts/input_bindings.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty():FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	current_scene=null;world.queue_free();await frames(8)
	await create_timer(.08,true,false,true).timeout
	quit(0 if result.passed else 1)
