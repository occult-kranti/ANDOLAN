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
	if name_=="plane":
		var boundary:=WorldBoundaryShape3D.new();boundary.plane=Plane(Vector3.UP,.1);floor_nodes[0].get_child(0).shape=boundary
	elif name_=="unsupported_shape":
		var convex:=ConvexPolygonShape3D.new();var points:=PackedVector3Array()
		for xsign in [-1,1]:
			for ysign in [-1,1]:
				for zsign in [-1,1]:points.append(Vector3(xsign*2,ysign*.1,zsign*2))
		convex.points=points;floor_nodes[0].get_child(0).shape=convex
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
	var ray_point:Vector3=motion.rig.global_transform*motion.last_globals[motion.rig.find_bone("foot.L")].origin
	var actual_hit:=actor.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(ray_point.x,plane+.08,ray_point.z),Vector3(ray_point.x,plane-.08,ray_point.z),1,[actor.get_rid()]))
	var ray_debug:={"hit":not actual_hit.is_empty(),"position":vec(actual_hit.position) if not actual_hit.is_empty() else [],"normal":vec(actual_hit.normal) if not actual_hit.is_empty() else [],"floor_transform":str(floor_nodes[0].global_transform),"shape_class":floor_nodes[0].get_child(0).shape.get_class(),"plane":str(floor_nodes[0].get_child(0).shape.plane) if floor_nodes[0].get_child(0).shape is WorldBoundaryShape3D else "n/a"}
	var skin:=measure(motion,chosen,plane);skin.erase("positions")
	if name_=="flat" and motion.has_method("_motion_pose"):
		var untouched:=[motion.phase,motion.transition_age,motion.aim_weight,motion.action_elapsed,motion.modified_samples,pose_rows(motion)]
		var sampled:Dictionary=motion._motion_pose()
		for side in ["L","R"]:motion._support_foot_world(side,sampled)
		check("shared pose query is pure across clocks aim transitions and skeleton",untouched==[motion.phase,motion.transition_age,motion.aim_weight,motion.action_elapsed,motion.modified_samples,pose_rows(motion)])
	if name_=="stale_teleport":actor.position.x=1000
	elif name_=="moved_owner":floor_nodes[0].position.y-=.5
	elif name_=="moved_shape":floor_nodes[0].get_child(0).position.y-=.05
	elif name_=="excluded_layer":floor_nodes[0].collision_layer=2
	elif name_=="disabled_shape":floor_nodes[0].get_child(0).disabled=true
	elif name_=="removed_shape":floor_nodes[0].get_child(0).shape=null
	elif name_=="changed_shape":floor_nodes[0].get_child(0).shape.size.y=.1
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
	var detail:={"case":name_,"ray_debug":ray_debug,"query_in_physics":physics_query,"support_seen":motion.measured_support_seen,"acquired":acquired,"current_support":motion.descent_support_y.duplicate(),"skin_before_interrupt":skin,"source_vertices":chosen.size(),"before_pose":before_pose,"isolated":isolated}
	if name_ in ["flat","elevated","plane"]:
		check(name_+" measured support is actual floor elevation",physics_query and acquired.size()==2 and absf(float(acquired.get("L",INF))-plane)<.00001 and absf(float(acquired.get("R",INF))-plane)<.00001,detail)
		check(name_+" descended sole stays above existing minus5mm gate",skin.L.minimum_m>=-.005 and skin.R.minimum_m>=-.005,{"skin":skin})
		check(name_+" repeated paused evaluation holds pose root anchors and clocks",pose_rows(motion)==before_pose and actor.transform==before_root and motion.foot_targets==before_targets and [motion.phase,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]==clock)
	else:
		var meaningful:=acquired.size()==2 if name_ in ["moved_shape","excluded_layer","disabled_shape","removed_shape","changed_shape"] else true
		check(name_+" cannot apply a stale or ineligible descent correction",meaningful and bool(isolated.equal),detail)
	samples.append(detail)
	if name_=="moved_owner":floor_nodes[0].position.y+=.5
	elif name_=="moved_shape":floor_nodes[0].get_child(0).position.y+=.05
	elif name_=="excluded_layer":floor_nodes[0].collision_layer=1
	elif name_=="disabled_shape":floor_nodes[0].get_child(0).disabled=false
	elif name_ in ["removed_shape","plane","unsupported_shape"]:
		var replacement:=BoxShape3D.new();replacement.size=Vector3(4,.2,4);floor_nodes[0].get_child(0).shape=replacement
	elif name_=="changed_shape":floor_nodes[0].get_child(0).shape.size.y=.2
	actor.free()
	await process_frame

func narrow_edge() -> void:
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor);actor.position=Vector3(0,.05,0)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load("res://scripts/rama_motion.gd").new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var state:={"grounded":true,"floor_y":.05,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	for tick in 24:motion.update_motion(1.0/120,state);motion.evaluate_pose()
	var foot:int=motion.rig.find_bone("foot.L")
	var old_point:Vector3=motion.last_globals[foot].origin
	make_floor(30+old_point.x,0)
	var pad:StaticBody3D=floor_nodes[-1];pad.position.z=old_point.z
	pad.get_child(0).shape.size=Vector3(.02,.2,.02)
	actor.position=Vector3(30,.005,0);state.grounded=false;state.floor_y=.005;state.velocity=Vector3(0,-1.2,0);state.local_velocity=state.velocity
	await physics_frame
	motion.update_motion(1.0/120,state);motion.evaluate_pose()
	var before_root:=actor.transform
	# Inject a final animated leg pose after the safe physics query. This is a
	# component boundary, not a claim that a recorded authored clip did this.
	var hip:int=motion.rig.find_bone("upperleg01.L")
	motion.rig.set_bone_pose_position(hip,motion.rig.get_bone_pose_position(hip)+Vector3(.04,-.02,0))
	var before:Transform3D=motion.rig.get_bone_global_pose(foot)
	var point:Vector3=motion.rig.global_transform*before.origin
	var hit:=actor.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(point.x,.08,point.z),Vector3(point.x,-.08,point.z),1,[actor.get_rid()]))
	var cached:Dictionary=motion.descent_support_y.duplicate()
	motion._protect_transition_floor()
	var after:Transform3D=motion.rig.get_bone_global_pose(foot)
	var detail:={"root_unchanged":actor.transform==before_root,"current_foot_ray_misses":hit.is_empty(),"cached_support":cached,"current_world":vec(point),"before":str(before),"after":str(after),"scope":"Actual imported leg/bind hierarchy and a20mm real support pad; final leg pose deliberately translated40mm sideways/20mm downward after query, without moving root."}
	check("narrow support cannot correct a different final animated footprint",hit.is_empty() and before==after and actor.transform==before_root,detail)
	samples.append(detail)
	# Reacquire at the original footprint, then queue the supporting collider
	# for disposal before the modifier consumes its safe-physics hit.
	motion.rig.set_bone_pose_position(hip,motion.rig.get_bone_pose_position(hip)-Vector3(.04,-.02,0))
	motion.update_motion(1.0/120,state);motion.evaluate_pose()
	pad.queue_free()
	var removed:=guard_difference(motion)
	check("queued supporting collider cannot retain correction ownership",removed.cache.has("L") and bool(removed.equal),removed)
	actor.free();await process_frame

func run() -> void:
	make_floor(0,0);make_floor(10,2);make_floor(20,2,.12)
	await narrow_edge()
	for case_ in ["flat","elevated","plane","unsupported_shape","never_grounded","stale_teleport","moved_owner","moved_shape","excluded_layer","disabled_shape","removed_shape","changed_shape","fresh_miss","slope","out_of_range","rise_interrupt","flight_interrupt","grapple_interrupt","reset_pending","death","measured_step"]:await trial(case_)
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,"count":checks.size(),"samples":samples,"motion_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"fixture_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Injected120Hz component states, real physics ray queries, actual imported near skin and one manual pose writer. Native scene/capture is separate; no raster/feel acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	for node in floor_nodes:
		if is_instance_valid(node):node.free()
	quit(0 if result.passed else 1)
