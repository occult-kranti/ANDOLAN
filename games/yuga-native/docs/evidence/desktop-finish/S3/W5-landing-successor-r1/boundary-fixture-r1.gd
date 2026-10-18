extends "res://tests/graphics_g2_support_cases.gd"
## Injected boundary states on an actual imported near rig and real physics floors.
## Separate from the native player/scene landing tape; no image acceptance.
var samples:Array=[]
var floor_nodes:Array=[]

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	Engine.physics_ticks_per_second=120
	call_deferred("run")

func make_floor(x:float,y:float,angle:=0.0) -> void:
	var body:=StaticBody3D.new();body.collision_layer=1
	var shape:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape.shape=box
	body.add_child(shape);root.add_child(body);body.position=Vector3(x,y-.1,0);body.rotation.z=angle
	floor_nodes.append(body)

func pose_rows(motion:Node) -> Array:
	var result:=[]
	for t in motion.last_globals:result.append([vec(t.origin),[t.basis.x.x,t.basis.x.y,t.basis.x.z,t.basis.y.x,t.basis.y.y,t.basis.y.z,t.basis.z.x,t.basis.z.y,t.basis.z.z]])
	return result

func guard_difference(motion:Node) -> Dictionary:
	var cache:Dictionary=motion.descent_support_y.duplicate()
	motion.evaluate_pose();var guarded:=pose_rows(motion)
	motion.descent_support_y.clear();motion.evaluate_pose();var unguarded:=pose_rows(motion)
	motion.descent_support_y=cache
	motion.evaluate_pose()
	return {"equal":guarded==unguarded,"guarded":guarded,"without_descent_guard":unguarded,"cache":cache}

func trial(name_:String) -> void:
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load("res://scripts/rama_motion.gd").new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")))
	motion.active=false
	var chosen:=soles(model,motion.rig)
	var x:=10.0 if name_=="elevated" else 0.0
	var plane:=2.0 if name_=="elevated" else 0.0
	actor.position=Vector3(x,plane+.05,0)
	var state:={"grounded":true,"floor_y":actor.position.y,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	var physics_query:=Engine.is_in_physics_frame()
	if name_!="never_grounded":
		for tick in 24:motion.update_motion(1.0/120,state);motion.evaluate_pose()
	actor.position.y=plane+.005
	state.grounded=false;state.floor_y=actor.position.y;state.velocity=Vector3(0,-1.2,0);state.local_velocity=state.velocity
	motion.update_motion(1.0/120,state);motion.evaluate_pose()
	var acquired:Dictionary=motion.descent_support_y.duplicate()
	var before_root:=actor.transform;var before_targets:Dictionary=motion.foot_targets.duplicate()
	var clock:=[motion.phase,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]
	var before_pose:=pose_rows(motion)
	var skin:=measure(motion,chosen,plane);skin.erase("positions")
	if name_=="stale_teleport":actor.position.x=1000
	elif name_=="fresh_miss":
		actor.position.x=1000;state.floor_y=actor.position.y;motion.update_motion(1.0/120,state)
	elif name_=="slope":
		actor.position=Vector3(20,2.005,0);state.floor_y=actor.position.y;motion.update_motion(1.0/120,state)
	elif name_=="out_of_range":
		actor.position.y=plane+.3;state.floor_y=actor.position.y;motion.update_motion(1.0/120,state)
	elif name_=="rise_interrupt":
		state.velocity=Vector3(0,2,0);state.local_velocity=state.velocity;motion.update_motion(1.0/120,state)
	elif name_ in ["flight_interrupt","grapple_interrupt"]:
		state.traversal="flight" if name_=="flight_interrupt" else "grapple";motion.update_motion(1.0/120,state)
		state.traversal="ground";motion.update_motion(1.0/120,state)
	elif name_=="reset_pending":motion.cancel("boundary reset")
	elif name_ in ["death","measured_step"]:
		motion.request_action(name_,.2,.2);motion.update_motion(1.0/120,state)
	var isolated:=guard_difference(motion)
	var detail:={"case":name_,"query_in_physics":physics_query,"support_seen":motion.measured_support_seen,"acquired":acquired,"current_support":motion.descent_support_y.duplicate(),"skin_before_interrupt":skin,"source_vertices":chosen.size(),"before_pose":before_pose,"isolated":isolated}
	if name_ in ["flat","elevated"]:
		check(name_+" measured support is actual floor elevation",physics_query and acquired.size()==2 and absf(float(acquired.get("L",INF))-plane)<.00001 and absf(float(acquired.get("R",INF))-plane)<.00001,detail)
		check(name_+" descended sole stays above existing minus5mm gate",skin.L.minimum_m>=-.005 and skin.R.minimum_m>=-.005,{"skin":skin})
		check(name_+" repeated paused evaluation holds pose root anchors and clocks",pose_rows(motion)==before_pose and actor.transform==before_root and motion.foot_targets==before_targets and [motion.phase,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]==clock)
	else:check(name_+" cannot apply a stale or ineligible descent correction",bool(isolated.equal),detail)
	samples.append(detail)
	actor.free()
	await process_frame

func run() -> void:
	make_floor(0,0);make_floor(10,2);make_floor(20,2,.12)
	for case_ in ["flat","elevated","never_grounded","stale_teleport","fresh_miss","slope","out_of_range","rise_interrupt","flight_interrupt","grapple_interrupt","reset_pending","death","measured_step"]:await trial(case_)
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,"count":checks.size(),"samples":samples,"motion_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"fixture_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Injected120Hz component states, real physics ray queries, actual imported near skin and one manual pose writer. Native scene/capture is separate; no raster/feel acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	for node in floor_nodes:node.free()
	quit(0 if result.passed else 1)
