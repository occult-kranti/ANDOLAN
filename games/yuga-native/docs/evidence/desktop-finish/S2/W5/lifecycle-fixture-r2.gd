extends "res://tests/graphics_g2_support_cases.gd"
## Fresh real-scene lifecycle observations. No manual animation clock or pose calls.
var rows: Array=[]
var moments: Array=[]
var events: Array=[]
var label := "create_title"
var motion: Node
var selected: Array=[]
var last_points: Array=[]
var callback_start := 0

func snapshot() -> Dictionary:
	var player: CharacterBody3D=scene.player
	var kit: Dictionary=scene.rama_runtime.kit.report()
	return {"label":label,"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames(),"in_physics":Engine.is_in_physics_frame(),"tree_paused":paused,"player_active":player.active,"root":vec(player.global_position),"velocity":vec(player.velocity),"presentation_suspended":player.presentation_suspended,"motion":motion.diagnostics(),"transition_age":motion.transition_age,"locomotion_age":motion.locomotion_age,"support_ready":motion.idle_support_ready,"support_y":motion.idle_support_y.duplicate(),"targets":{"L":vec(motion.foot_targets.L),"R":vec(motion.foot_targets.R)},"kit":kit,"army_elapsed":scene.practice_army.elapsed,"hud":scene.rama_hud.note.text}

func observed() -> void:
	var row:=snapshot()
	var points:=[];var poses:=[];var error:=0.0;var step:=0.0;var worst:=""
	for index in motion.rig.get_bone_count():
		var transform:Transform3D=motion.rig.get_bone_global_pose(index)
		var q:=transform.basis.get_rotation_quaternion()
		poses.append({"p":vec(transform.origin),"q":[q.x,q.y,q.z,q.w]})
		points.append(transform.origin)
		error=maxf(error,transform.origin.distance_to(motion.last_globals[index].origin))
		if not last_points.is_empty():
			var distance:=transform.origin.distance_to(last_points[index])
			if distance>step:step=distance;worst=motion.rig.get_bone_name(index)
	row["callback_cache_error_m"]=error
	row["adjacent_rig_origin_step_m"]=step;row["worst_bone"]=worst
	row["poses"]=poses
	# All visible foot/toe-dominated source vertices; combined weights, no sampling.
	var skin:=measure(motion,selected,0);skin.erase("positions")
	row["soles"]=skin
	rows.append(row);last_points=points

func mark(name_: String) -> Dictionary:
	label=name_
	var result:=snapshot();moments.append(result)
	return result

func ticks(number: int) -> void:
	for unused in number:await physics_frame;await process_frame

func wait_stage(stage: String, limit:=45) -> bool:
	for unused in limit:
		if motion.action_stage==stage:return true
		await ticks(1)
	return motion.action_stage==stage

func event_count(kind: String) -> int:
	return events.filter(func(event):return event.kind==kind).size()

func run() -> void:
	baseline_path="res://docs/evidence/desktop-finish/S2/W5/baseline/rama_motion.gd"
	source_pins=pins()
	for path in [get_script().resource_path,"res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_action_buffer.gd","res://scripts/rama_practice_army.gd"]:source_pins[path]=FileAccess.get_sha256(path)
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	motion=scene.player.rama_motion
	callback_start=motion.modified_samples
	motion.modification_processed.connect(observed)
	selected=soles(scene.player.visual,motion.rig)
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event: Dictionary):events.append(event.duplicate(true)))
	mark("create_title")
	await ticks(14)
	var title:=mark("settled_title")
	check("observer attaches before the first native modifier sample",callback_start==0,{"samples_before_connect":callback_start,"callbacks":rows.size()})
	check("actual title remains inactive with idle animation and no combat time",title.player_active==false and title.motion.phase>0 and title.kit.elapsed==0 and title.motion.stage=="none",title)
	check("real modifier observes the same cached164-bone pose",rows.size()>0 and rows.all(func(row):return row.poses.size()==164 and row.callback_cache_error_m<.000001))
	var ready_rows:=rows.filter(func(row):return row.support_ready and row.motion.foot_locks.L and row.motion.foot_locks.R)
	check("first scene settles both visible soles on actual zero-height courtyard floor",not ready_rows.is_empty() and ready_rows[-1].soles.L.minimum_m>=0 and ready_rows[-1].soles.L.minimum_m<.005 and ready_rows[-1].soles.R.minimum_m>=0 and ready_rows[-1].soles.R.minimum_m<.005)
	scene.start_training();mark("training_entry");await ticks(14)
	var accepted:Dictionary=scene.cast_rama_ability("measured_step")
	# Pause immediately at the genuine accepted boundary. A headless skin
	# observer may cost enough wall time to produce several native catch-up ticks.
	mark("step_before_pause")
	scene.set_paused(true)
	var before_pause:=mark("step_paused")
	for unused in 8:await process_frame
	var after_pause:=snapshot()
	check("native Measured Step windup pauses before release",accepted.get("accepted",false) and before_pause.motion.stage in ["windup","hold"] and event_count("release")==0,{"accepted":accepted,"before":before_pause})
	check("tree pause holds fullbody phase pose and authority",before_pause.motion==after_pause.motion and before_pause.kit==after_pause.kit and before_pause.army_elapsed==after_pause.army_elapsed,{"before":before_pause,"after":after_pause})
	scene.reset_training();var reset:=mark("reset_while_paused")
	for unused in 6:await process_frame
	check("paused reset retires the action without advancing the replacement generation",motion.action_stage=="none" and not motion.nocked and not scene.rama_runtime.kit.report().action_locked and scene.rama_runtime.kit.elapsed==0 and not scene.player.active and paused,{"reset":reset,"after":snapshot()})
	scene.set_paused(false);mark("reset_resume");await ticks(22)
	check("resume after paused reset cannot release the old cast",event_count("release")==0 and motion.action_stage=="none" and not motion.nocked and scene.player.active,snapshot())
	accepted=scene.cast_rama_ability("measured_step");mark("step_native_resume")
	var reached_recovery:=await wait_stage("recovery")
	check("fresh fullbody action releases once after reset",accepted.get("accepted",false) and reached_recovery and event_count("release")==1,{"accepted":accepted,"state":snapshot(),"events":events})
	scene.return_to_menu();var returned:=mark("return_from_fullbody_recovery")
	await ticks(24)
	var title_after:=mark("returned_title_settled")
	check("title return resets authority and keeps intentional inactive idle animated",not scene.started and not scene.player.active and title_after.kit.elapsed==0 and title_after.kit.generation>returned.kit.generation-1 and motion.action_stage=="none" and not motion.nocked and title_after.motion.phase>returned.motion.phase,{"return":returned,"settled":title_after})
	check("title return reacquires fixed support without stale dash",motion.locomotion=="idle" and motion.movement_speed<.0001 and motion.foot_locks.L and motion.foot_locks.R,snapshot())
	scene.start_training();mark("reentry_after_fullbody");await ticks(16)
	accepted=scene.cast_rama_ability("piercing_dawn");await ticks(2)
	scene.rama_runtime.kit.cancel_windup("S2 native lifecycle public cancel");mark("public_cancel")
	var release_before:=event_count("release")
	scene.return_to_menu();mark("return_after_cancel");await ticks(20)
	check("cancel then title return cannot revive a nocked arrow or delayed release",accepted.get("accepted",false) and motion.action_stage=="none" and not motion.nocked and event_count("release")==release_before and scene.rama_runtime.kit.report().casts.is_empty(),snapshot())
	var stable:=true
	for path in source_pins:stable=stable and FileAccess.get_sha256(path)==source_pins[path]
	check("source bytes and imported rig resources remain unchanged",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":source_pins,"scope":"Actual imported courtyard scene, native physics callbacks and modification_processed observations. Public scene lifecycle and kit calls, no direct animation clock/pose writes. Headless software observer only; no first-drawable frame or visible pop acceptance.","selected_visible_sole_vertices":selected.size(),"callback_samples_before_connect":callback_start,"rows":rows,"moments":moments,"events":events}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	paused=false;current_scene=null;scene.queue_free()
	for unused in 6:await process_frame
	quit(0 if result.passed else 1)
