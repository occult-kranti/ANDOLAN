extends SceneTree
## Actual remap/rule transitions distinguish pause from restart; no InputMap overrides.
const Bindings=preload("res://scripts/input_bindings.gd")
var output:="/tmp/desktop-d08-shortcuts.json"
var checks:Array[Dictionary]=[]
var source:=""
var world:Node3D
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func frames(n:=5)->void:
	for unused in n:await process_frame
func key(code:Key)->void:
	for down in [true,false]:
		var event:=InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event);await frames(2)
func check(label:String,passed:bool,details:Dictionary={})->void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func run()->void:
	source=FileAccess.get_sha256("res://scripts/confluence_world.gd")
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=2.0
	world=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(world);current_scene=world
	await frames()
	world.set_process(false);world.set_physics_process(false);world.army.set_physics_process(false);world.player.set_physics_process(false);world.rama_hud.set_process(false)
	world.rama_runtime.set_volume(0)
	var changed:Dictionary=Bindings.set_binding("reload",KEY_T)
	world._update_practice_hud()
	check("Real supported remap updates live reload help",changed.ok and world.help_labels[0].text.contains("T reload"))
	var bytes:=FileAccess.get_sha256(Bindings.config_path)
	var rejected:=true
	for action in ["pause_game","reset_training","world_respawn"]:rejected=rejected and not Bindings.set_binding(action,KEY_J).ok
	check("Pause and restart remain fixed rather than fabricated user remaps",rejected and FileAccess.get_sha256(Bindings.config_path)==bytes and Bindings.label("pause_game")=="Escape" and Bindings.label("world_respawn")=="F5")
	var vitals:Node=world.rama_runtime.vitals
	var hit:Dictionary=vitals.receive_damage(1000,"D08 actual defeat",vitals.generation,0)
	world.rama_hud._process(.001)
	check("Real defeat shows timed returning rather than restart instruction",hit.get("accepted",false) and not vitals.alive and world.rama_hud.note.text.begins_with("RETURNING IN"))
	for unused in 62:world.army.step_simulation(.05)
	world.rama_hud._process(.001)
	check("Army time alone restores the defeated hero",vitals.alive and world.player.active and world.rama_hud.life.value==300)
	for winner in ["sun","moon","draw"]:
		world._restart_army()
		world.army.cores={"sun":0.0 if winner in ["moon","draw"] else 100.0,"moon":0.0 if winner in ["sun","draw"] else 100.0}
		world.army.step_simulation(.05);world._update_practice_hud()
		check(winner+" real terminal tick opens outcome pause",world.army.winner==winner and world.paused and paused and world.outcome_summary.visible)
		await key(KEY_ESCAPE);world._update_practice_hud()
		var objective:String=world.compact_world_labels[1].text
		check(winner+" visible outcome copy separates pause and direct restart",world.compact_world_card.visible and objective.contains(Bindings.label("pause_game")+" pause") and objective.contains(Bindings.label("world_respawn")+" restart"),{"objective":objective,"goal":world.goal_label.text})
		var authority:Dictionary=world.army.report()
		for unused in 3:world._update_practice_hud()
		await key(KEY_ESCAPE)
		check(winner+" Escape opens pause without restarting outcome",world.paused and world.army.report()==authority)
		await key(KEY_ESCAPE);await key(KEY_F5);world._update_practice_hud()
		check(winner+" F5 really restarts lane practice and clears terminal copy",not world.paused and world.army.winner.is_empty() and not world.army.siege_drill and world.compact_world_labels[1].text.contains("Escort Sun troops"))
	var drill:bool=world._start_siege_practice()
	for unit in world.army.units.duplicate():
		if is_instance_valid(unit) and unit.alive and unit.team=="moon" and unit.role in ["cannon_cart","royal_chariot"]:unit.take_hit(1000)
	world._update_practice_hud()
	check("Cleared drill copy names opening pause for restart choices",drill and world.goal_label.text.contains("Enemy engines cleared") and world.goal_label.text.contains(Bindings.label("pause_game")+" opens pause"),{"goal":world.goal_label.text,"relay":world.relay_hint.text})
	await key(KEY_ESCAPE)
	check("Drill Escape opens choices without resetting drill",world.paused and world.army.siege_drill)
	await key(KEY_ESCAPE);await key(KEY_F5);world._update_practice_hud()
	check("Drill F5 starts lane practice instead of restarting drill",not world.army.siege_drill and not world.paused and world.army.winner.is_empty())
	check("Observed caller source stayed stable",source==FileAccess.get_sha256("res://scripts/confluence_world.gd"))
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":{"res://scripts/confluence_world.gd":source,"res://scripts/input_bindings.gd":FileAccess.get_sha256("res://scripts/input_bindings.gd"),get_script().resource_path:FileAccess.get_sha256(get_script().resource_path)},"scope":"Actual supported ReloadT save, rejected fixed remaps, real vitals/army time, terminal core fixtures through actual ticks, actual siege-unit damage and native Escape/F5 mode transitions. UI formatting clocks held only by test processing controls; no runtime authority changes, InputMap overrides, pixels or OS input."},"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(8);quit(0 if passed else 1)
