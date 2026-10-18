extends "res://tests/graphics_g2_support_cases.gd"
## Actual native player descent interrupted through courtyard's public pause API.
var motion:Node

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	Engine.physics_ticks_per_second=120
	call_deferred("run")

func pose_state() -> Dictionary:
	var poses:=[]
	for t in motion.last_globals:
		var q:Quaternion=t.basis.get_rotation_quaternion()
		poses.append([t.origin.x,t.origin.y,t.origin.z,q.x,q.y,q.z,q.w])
	return {"root":str(scene.player.global_transform),"poses":poses,"kit":scene.rama_runtime.kit.report(),"army":scene.practice_army.elapsed,"gait":motion.locomotion,"age":motion.locomotion_age,"phase":motion.phase,"transition":motion.transition_age,"action_age":motion.action_elapsed,"anchors":{"L":vec(motion.foot_targets.L),"R":vec(motion.foot_targets.R)},"locks":motion.foot_locks.duplicate()}

func run() -> void:
	baseline_path="res://docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd"
	source_pins=pins();source_pins[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	motion=scene.player.rama_motion
	for unused in 24:await physics_frame;await process_frame
	scene.start_training()
	for unused in 2:await physics_frame;await process_frame
	var before:=pose_state();var physics_before:=Engine.get_physics_frames()
	check("public pause interrupts actual descending native player",motion.locomotion=="fall" and not scene.player.is_on_floor() and scene.player.velocity.y<0)
	scene.set_paused(true)
	var paused_entry:=pose_state()
	for unused in 12:await process_frame
	var held:=pose_state();var physics_held:=Engine.get_physics_frames()
	check("paused descent holds complete pose root anchors and authority",paused_entry==held and paused,{"physics_before":physics_before,"physics_held":physics_held})
	scene.set_paused(false);await physics_frame;await process_frame
	var resumed:=pose_state()
	check("first resumed update advances one physics delta without catchup",absf(float(resumed.age)-float(held.age)-1.0/120)<1e-10 and not paused,{"held_age":held.age,"resumed_age":resumed.age})
	var stable:=true
	for path in source_pins:stable=stable and FileAccess.get_sha256(path)==source_pins[path]
	check("pause witness uses unchanged actual imported sources",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":source_pins,"before":before,"paused_entry":paused_entry,"held":held,"resumed":resumed,"scope":"Actual native courtyard public pause/resume during descent; headless full-pose/authority hold, no raster or human-feel claim."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	current_scene=null;scene.queue_free()
	for unused in 5:await process_frame
	quit(0 if result.passed else 1)
