extends "res://tests/graphics_g2_support_cases.gd"
## Fresh native scene transition evidence, with compact full-pose rows.
var hz:=60
var summary_report:=false
var rows:Array=[]
var events:Array=[]
var label:="title_preroll"
var motion:Node
var cohorts:Dictionary={}
var names:Array=[]

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--hz="):hz=int(arg.trim_prefix("--hz="))
		elif arg=="--summary-report":summary_report=true
	Engine.physics_ticks_per_second=hz
	call_deferred("run")

func packed_transform(t:Transform3D) -> Array:
	var q:=t.basis.get_rotation_quaternion()
	return [t.origin.x,t.origin.y,t.origin.z,q.x,q.y,q.z,q.w]

func observed() -> void:
	var level:int=scene.player.rama_lod.level
	if not cohorts.has(level):cohorts[level]=soles(scene.player.visual,motion.rig)
	var skin:=measure(motion,cohorts[level],0);skin.erase("positions")
	var poses:=[];var error:=0.0
	for bone in motion.rig.get_bone_count():
		var tr:Transform3D=motion.rig.get_bone_global_pose(bone)
		poses.append(packed_transform(tr));error=maxf(error,tr.origin.distance_to(motion.last_globals[bone].origin))
	var sockets:={}
	for name_ in ["arrow_muzzle","bow_grip","string_nock","draw_hand"]:sockets[name_]=packed_transform(motion.socket_global(name_))
	rows.append({"label":label,"physics":Engine.get_physics_frames(),"process":Engine.get_process_frames(),"root":packed_transform(scene.player.global_transform),"rig":packed_transform(motion.rig.global_transform),"velocity":vec(scene.player.velocity),"grounded":motion.grounded,"physical_grounded":scene.player.is_on_floor(),"traversal":motion.traversal,"floor_input_y":motion.floor_y,"transition_age":motion.transition_age,"transition_duration":motion.transition_duration,"motion":motion.diagnostics(),"targets":{"L":vec(motion.foot_targets.L),"R":vec(motion.foot_targets.R)},"kit":scene.rama_runtime.kit.report(),"army_elapsed":scene.practice_army.elapsed,"poses":poses,"sockets":sockets,"soles":skin,"lod":level,"cohort_vertices":cohorts[level].size(),"cache_error_m":error})

func ticks(count_:int) -> void:
	for unused in int(ceil(count_*hz/60.0)):await physics_frame;await process_frame

func count_events(kind:String) -> int:
	return events.filter(func(event):return event.kind==kind).size()

func min_sole(label_:String, ground_only:=true) -> float:
	var result:=INF
	for row in rows:
		if row.label!=label_ or (ground_only and not row.grounded):continue
		for side in ["L","R"]:result=minf(result,row.soles[side].minimum_m)
	return result

func run() -> void:
	baseline_path="res://docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd"
	source_pins=pins()
	for path in [get_script().resource_path,"res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_practice_army.gd","res://scripts/rama_lod_binding.gd"]:source_pins[path]=FileAccess.get_sha256(path)
	scene=load("res://scenes/courtyard.tscn").instantiate();root.add_child(scene);current_scene=scene
	motion=scene.player.rama_motion
	for bone in motion.rig.get_bone_count():names.append(motion.rig.get_bone_name(bone))
	motion.modification_processed.connect(observed)
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event:Dictionary):events.append(event.duplicate(true)))
	await ticks(20)
	scene.start_training();label="training_entry";await ticks(24)
	check("grounded training entry soles stay above existing minus5mm gate",min_sole(label)>=-.005,{"minimum_m":min_sole(label)})
	for move in ["move_forward","move_back","move_left"]:
		label="return_before_"+move;scene.return_to_menu();await ticks(22)
		scene.start_training();Input.action_press(move);label="reset_"+move
		await ticks(14)
		check(move+" grounded reset transition soles stay above minus5mm",min_sole(label)>=-.005,{"minimum_m":min_sole(label)})
		Input.action_release(move);label="stop_"+move;await ticks(30)
		check(move+" actual player stops with finite pose",scene.player.velocity.length()<.001 and motion.finite)
	scene.reset_training();label="reset_before_cancel";await ticks(25)
	var accepted:Dictionary=scene.cast_rama_ability("piercing_dawn");label="bow_cancel_entry";await ticks(2)
	scene.rama_runtime.kit.cancel_windup("S3 transition public cancel");label="bow_cancel_fade";await ticks(16)
	check("real bow cancellation cannot produce a delayed release",accepted.get("accepted",false) and count_events("release")==0 and not motion.nocked,{"response":accepted})
	scene.reset_training();label="reset_before_step";await ticks(25)
	accepted=scene.cast_rama_ability("measured_step");label="protected_measured_step";await ticks(20)
	check("real protected fullbody action releases once",accepted.get("accepted",false) and count_events("release")==1 and motion.release_count==1,{"response":accepted,"events":events})
	check("actual modifier cache agrees with every native full pose",not rows.is_empty() and rows.all(func(row):return row.cache_error_m<.000001 and row.motion.finite and row.poses.size()==164))
	var stable:=true
	for path in source_pins:stable=stable and FileAccess.get_sha256(path)==source_pins[path]
	check("scene motion fixture and actual imported resources stay stable",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"hz":hz,"source_sha256":source_pins,"bone_names":names,"rows":rows,"events":events,"scope":"Actual native courtyard callbacks with public scene/kit calls and Input action press/release. All qualifying foot/toe vertices of each observed visible LOD are CPU-skinned; full poses compactly retained. Fixed-rate headless geometry and lifecycle, not render/hardware/feel acceptance."}
	var raw:=JSON.stringify(result)+"\n"
	if summary_report:
		var trace_path:=report_path+".trace.json.gz"
		var compressed:=raw.to_utf8_buffer().compress(FileAccess.COMPRESSION_GZIP)
		FileAccess.open(trace_path,FileAccess.WRITE).store_buffer(compressed)
		var summary:Dictionary=result.duplicate(false)
		summary.erase("rows");summary.erase("bone_names")
		summary["trace"]={"path":trace_path.get_file(),"encoding":"gzip","sha256":FileAccess.get_sha256(trace_path),"bytes":compressed.size(),"uncompressed_sha256":raw.sha256_text(),"uncompressed_bytes":raw.to_utf8_buffer().size(),"rows":rows.size(),"bones":names.size()}
		FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(summary)+"\n")
	else:FileAccess.open(report_path,FileAccess.WRITE).store_string(raw)
	paused=false;current_scene=null;scene.queue_free()
	for unused in 6:await process_frame
	quit(0 if result.passed else 1)
