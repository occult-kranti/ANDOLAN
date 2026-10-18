extends SceneTree
## I1 explicit overview presentation hold. Actual imported rig and native physics.
var output:="/tmp/ui-i1-overview-presentation.json"
var checks:Array[Dictionary]=[]
var events:Array[Dictionary]=[]
var source_start:={}
func _initialize()->void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--report="):output=a.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,ok:bool,detail:Dictionary={})->void:
	checks.append({"name":label,"passed":ok,"detail":detail});print("PASS " if ok else "FAIL ",label)
func frames(n:int=4)->void:
	for i in n:await process_frame
func physics(n:int)->void:
	for i in n:await physics_frame
	await process_frame
func presentation(p:Node)->Dictionary:
	var m:Node=p.rama_motion
	return {"phase":m.phase,"age":m.locomotion_age,"action_elapsed":m.action_elapsed,"stage":m.action_stage,"nocked":m.nocked,"releases":m.release_count,"secondary":p.rama_secondary.report(),"face":p.rama_face.report()}
func release_count()->int:return events.filter(func(e):return e.kind=="release").size()
func run()->void:
	for path in ["res://scripts/player.gd","res://scripts/confluence_world.gd","res://scripts/courtyard.gd","res://scripts/rama_motion.gd","res://scripts/rama_secondary_motion.gd","res://assets/heroes/rama-hero.glb","res://.godot/imported/rama-hero.glb-e90b8f8a0719fdd1ab2b89459efcbdac.scn",get_script().resource_path]:source_start[path]=FileAccess.get_sha256(path)
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(world);current_scene=world;await frames()
	world.set_process(false);world.set_physics_process(false);world.army.set_physics_process(false);world.rama_effects.set_process(false);world.rama_hud.set_process(false);world.rama_runtime.set_volume(0)
	world.teleport_to(Vector3(-40,.05,-10),0);world.player.yaw=PI;world.player.pitch=-.32;world.player._update_camera();world.player.set_physics_process(true);await physics(8);world.player.set_physics_process(false)
	world.army._decision_clock=10000;world.army._next_wave=10000
	world.rama_runtime.combat_event.connect(func(e:Dictionary):events.append(e.duplicate(true)))
	var accepted:Dictionary=world.cast_rama_ability("kodanda");world.player.rama_motion.evaluate_pose()
	check("real grounded Kodanda starts in windup",accepted.get("accepted",false) and world.player.rama_motion.action_stage=="windup")
	world.set_overview(true);world.player.rama_motion.evaluate_pose();world.player.set_physics_process(true);world.army.set_physics_process(true)
	var before:=presentation(world.player);var kit:Dictionary=world.rama_runtime.kit.report();var army_age:float=world.army.elapsed;var body:Transform3D=world.player.global_transform;var pose:Array=world.player.rama_motion.last_globals.duplicate()
	await physics(45)
	var after:=presentation(world.player)
	check("45 native physics frames hold action phase and presentation clock",before.phase==after.phase and before.age==after.age and before.action_elapsed==after.action_elapsed and before.stage==after.stage and before.nocked==after.nocked,{"before":before,"after":after})
	check("overview also holds secondary and face presentation",before.secondary==after.secondary and before.face==after.face)
	check("overview preserves body transform and evaluated rig pose",body==world.player.global_transform and pose==world.player.rama_motion.last_globals)
	check("overview keeps authoritative kit army and release count unchanged",kit==world.rama_runtime.kit.report() and army_age==world.army.elapsed and release_count()==0)
	world.set_paused(true);await frames(5);world.set_paused(false);await physics(12)
	check("closing nested pause keeps overview presentation suspended",world.overview and presentation(world.player)==before and world.rama_runtime.kit.report()==kit)
	world.set_overview(false);await physics(32)
	check("native resume advances authority and releases exactly once",not world.overview and world.player.active and world.army.elapsed>army_age and world.rama_runtime.kit.elapsed>kit.elapsed and release_count()==1 and world.player.rama_motion.release_count==before.releases+1,{"events":events})
	world.player.set_physics_process(false);world.army.set_physics_process(false)
	var second:Dictionary=world.cast_rama_ability("kodanda");world.player.set_physics_process(true);world.army.set_physics_process(true);await physics(2)
	check("second actual action starts after resumed cooldown",second.get("accepted",false) and world.player.rama_motion.action_stage=="windup")
	world.set_overview(true);var held:float=world.player.rama_motion.action_elapsed;var releases_before:=release_count();await physics(30);world.set_overview(true);await physics(5)
	check("repeated overview entry is idempotent during a partial windup",is_equal_approx(world.player.rama_motion.action_elapsed,held) and release_count()==releases_before)
	world.set_overview(false);await physics(2)
	var resume_age:float=world.player.rama_motion.action_elapsed
	check("resume adds current physics time without paused-time catchup",resume_age>held and resume_age-held<.06,{"held":held,"resumed":resume_age})
	world.set_overview(true);world.teleport_to(Vector3(-40,.05,-10),0);await physics(5)
	check("existing teleport reset exits overview without sticky suspension",not world.overview and world.player.active and not bool(world.player.get("presentation_suspended")) and world.player.rama_motion.action_stage=="none")
	current_scene=null;world.queue_free();await frames(8)
	var court:Node3D=load("res://scenes/courtyard.tscn").instantiate();root.add_child(court);current_scene=court;await frames(5)
	var title_before:float=court.player.rama_motion.locomotion_age;var title_stage:String=court.player.rama_motion.action_stage;await physics(12)
	check("inactive courtyard title intentionally continues idle presentation",not court.player.active and not court.started and court.main_panel.visible and not bool(court.player.get("presentation_suspended")) and court.player.rama_motion.locomotion_age>title_before and court.player.rama_motion.action_stage==title_stage,{"before_age":title_before,"after_age":court.player.rama_motion.locomotion_age})
	court.start_training();await physics(8);var idle_before:float=court.player.rama_motion.locomotion_age;await physics(8)
	check("ordinary active idle still advances after title start",court.player.active and court.player.rama_motion.locomotion_age>idle_before)
	var stable:=true
	for path in source_start:stable=stable and source_start[path]==FileAccess.get_sha256(path)
	check("sources and actual imported R7 resource unchanged during execution",stable)
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"source_before":source_start,"scope":"Actual native physics frames with accepted runtime casts and imported R7 scene. Long overview, nested real tree pause, resume, idempotent entry, teleport reset, actual inactive courtyard title and active idle. No render, OS input or R4 motion-quality approval."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n");paused=false;current_scene=null;court.queue_free();await frames(8);quit(0 if result.passed else 1)
