extends SceneTree
## Real receiver defeat/army-clock respawn; traversal UI availability only.
const Bindings=preload("res://scripts/input_bindings.gd")
var output:=""
var world_script:="res://scripts/confluence_world.gd"
var world:Node3D
var checks:Array[Dictionary]=[]
var observations:Array[Dictionary]=[]
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
		if arg.begins_with("--world-script="):world_script=arg.trim_prefix("--world-script=")
	call_deferred("run")
func frames(count:=8)->void:
	for unused in count:await process_frame
func check(label:String,passed:bool,detail:Dictionary={})->void:
	checks.append({"name":label,"passed":passed,"detail":detail});print("PASS " if passed else "FAIL ",label)
func refresh()->void:
	world._update_practice_hud();world.rama_hud._refresh();await frames()
func current_copy()->String:
	return world.compact_world_labels[3].text if world._constrained_world else world.goal_label.text
func offers_action(text:String)->bool:
	return text.contains(Bindings.label("fly")+" flight") or text.contains(Bindings.label("grapple")+" tether") or text.contains(Bindings.label("grapple")+" release")
func observe(label:String)->Dictionary:
	var result:={"stage":label,"scale":root.content_scale_factor,"vitals":world.player.vitals.report(),"player_active":world.player.active,"notice":world.rama_hud.note.text,"heading":world.ability_label.text,"prompt":current_copy(),"rows":world.compact_world_labels.map(func(row):return row.text),"traversal":world.player.traversal_report()}
	observations.append(result);return result
func fit()->bool:
	var card:Control=world.compact_world_card if world._constrained_world else world.hud.get_node("TraversalStatus")
	if not root.get_visible_rect().encloses(card.get_global_rect()) or card.get_global_rect().intersects(world.rama_hud.get_global_rect()):return false
	var labels:Array=[]
	if world._constrained_world:labels=world.compact_world_labels
	else:labels=[world.ability_label,world.goal_label]
	for row:Label in labels:
		var text_size:Vector2=row.get_theme_font("font").get_multiline_string_size(row.text,HORIZONTAL_ALIGNMENT_LEFT,row.size.x,row.get_theme_font_size("font_size"))
		if not row.is_visible_in_tree() or not card.get_global_rect().encloses(row.get_global_rect()) or row.size.y+1<text_size.y:return false
	return true
func run()->void:
	Engine.max_fps=60
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	world=load(world_script).new();root.add_child(world);current_scene=world;await frames(20)
	world.set_process(false);world.set_physics_process(false);world.player.set_physics_process(false);world.army.set_physics_process(false)
	world.player.traversal.anchors.clear()
	await refresh()
	check("ready initial state retains idle energy and current traversal keys",world.player.active and world.player.vitals.alive and world.ability_label.text=="Energy 100 / 100" and offers_action(current_copy()))
	world.player.traversal.energy=17;world.player.traversal.flight_cooldown=4;world.player.traversal.grapple_cooldown=1.2
	world.set_paused(true);await refresh()
	check("living paused actor retains cooldowns without actionable traversal prompts",world.player.vitals.alive and not world.player.active and not offers_action(current_copy()) and world.ability_label.text.contains("PAUSED") and world.goal_label.text.contains("Flight 4.0s · Tether 1.2s") and fit(),observe("living-paused"))
	world.set_paused(false);world.player.traversal.energy=100;world.player.traversal.flight_cooldown=0;world.player.traversal.grapple_cooldown=0;await refresh()
	check("resume restores original idle energy and bound actions",world.player.active and world.ability_label.text=="Energy 100 / 100" and offers_action(current_copy()))
	var damage:Dictionary=world.player.vitals.receive_damage(1000,"availability_fixture",world.player.vitals.generation,1)
	check("real receiver defeat disables traversal actor",damage.accepted and not world.player.vitals.alive and not world.player.active)
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale;await frames();await refresh()
		var before:Dictionary=world.player.vitals.report();var snapshot:=observe("returning")
		check("returning combat notice remains authoritative at"+str(scale),world.rama_hud.note.text.begins_with("RETURNING IN") and world.rama_hud.life.value==0)
		check("returning traversal does not offer unavailable bound actions at"+str(scale),not offers_action(current_copy()) and current_copy().to_lower().contains("respawn"),snapshot)
		check("returning copy fits existing panel at"+str(scale),fit())
		await refresh();check("presentation does not advance respawn or mutate receiver at"+str(scale),world.player.vitals.report()==before)
	world.set_paused(true)
	var remaining:float=world.player.vitals.report().respawn_remaining;await frames()
	world.set_paused(false);await refresh()
	check("pause resume does not revive defeated actor or consume respawn delay",not world.player.active and not world.player.vitals.alive and world.player.vitals.report().respawn_remaining==remaining)
	# Explicit winner assignment is a presentation precedence fixture, not a played victory.
	world.army.winner="sun"
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale;await frames();await refresh()
		var terminal:=observe("terminal")
		check("terminal availability overrides returning and bound actions at"+str(scale),world.rama_hud.note.text.begins_with("Round ended") and world.ability_label.text.contains("ROUND ENDED") and not offers_action(current_copy()) and (world.goal_label.text.contains("restart") if scale==1.0 else world.compact_world_labels[1].text.contains("victory")),terminal)
	world.army.winner=""
	for unused in 61:world.army.step_simulation(.05)
	world.player.set_physics_process(true)
	for unused in 8:await physics_frame
	world.player.set_physics_process(false)
	root.content_scale_factor=1.0;await frames();await refresh()
	check("real army-clock respawn restores active idle traversal affordance",world.player.active and world.player.vitals.alive and world.ability_label.text=="Energy 100 / 100" and offers_action(current_copy()),observe("respawned"))
	check("accepted idle footprint remains88logical pixels",world.hud.get_node("TraversalStatus").size.y==88 and not world.energy_bar.show_percentage)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"observations":observations,"world_script":world_script,"sources":{},"scope":"Actual receiver lethal damage, paused death, army-clock respawn and native100/200/100 canvas; staged terminalwinner only for UI precedence. No continuous played defeat or pixel claim."}
	for path in [world_script,"res://scripts/rama_vitals.gd","res://scripts/rama_hero_runtime.gd","res://scripts/player_traversal.gd","res://scripts/input_bindings.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty():FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(8);await create_timer(.08,true,false,true).timeout
	quit(0 if result.passed else 1)
