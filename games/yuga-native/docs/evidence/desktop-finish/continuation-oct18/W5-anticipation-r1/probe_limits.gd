extends "/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd"
const CANDIDATE := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W5-anticipation-r1/rama_motion.gd"
var rows:Array=[]

func poses(m:Node) -> Array:
	var values:Array=[]
	for i in m.rig.get_bone_count():
		var t:Transform3D=m.rig.get_bone_global_pose(i)
		values.append([vec(t.origin),vec(t.basis.x),vec(t.basis.y),vec(t.basis.z)])
	return values

func trial(kind:String,height:float,speed:float) -> void:
	var floor_body:=StaticBody3D.new();floor_body.collision_layer=1
	var shape_node:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape_node.shape=box
	floor_body.add_child(shape_node);root.add_child(floor_body);floor_body.position.y=-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load(CANDIDATE).new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var state:={"grounded":true,"floor_y":.05,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	actor.position.y=.05;await physics_frame
	for tick in 24:motion.update_motion(1.0/30,state);motion.evaluate_pose()
	actor.position.y=height;state.grounded=false;state.floor_y=height;state.velocity=Vector3(0,-speed,0);state.local_velocity=state.velocity
	# Settle the authored falling pose with preparation disabled, then observe
	# the first newly admitted fresh support. This is an entry seam component.
	motion.measured_support_seen=false
	for tick in 24:motion.update_motion(1.0/30,state);motion.evaluate_pose()
	if kind=="fresh_moved":floor_body.position.y=0.0
	if kind=="slope_rejected":floor_body.rotation.z=.02
	if kind=="edge_exit":
		var point:Vector3=motion._support_foot_world("L",motion._motion_pose())
		box.size.x=.02;floor_body.position.x=point.x
	await physics_frame
	motion.measured_support_seen=true;motion.update_motion(1.0/30,state)
	var acquired:Dictionary=motion.descent_support_y.duplicate()
	motion.descent_support_y.clear();motion.evaluate_pose();motion.descent_support_y=acquired
	if kind=="edge_exit":
		var hip:int=motion.rig.find_bone("upperleg01.L")
		motion.rig.set_bone_pose_position(hip,motion.rig.get_bone_pose_position(hip)+Vector3(.04,0,0))
	var before:=poses(motion);var foot:int=motion.rig.find_bone("foot.L");var before_y:float=motion.rig.get_bone_global_pose(foot).origin.y
	motion._prepare_landing_legs();var after:=poses(motion);var extension:float=before_y-motion.rig.get_bone_global_pose(foot).origin.y
	var valid:bool=motion._landing_probe_depth()<=1.2 and motion.foot_locks=={"L":false,"R":false}
	if kind in ["beyond_cap","slow_miss","slope_rejected"]:valid=valid and acquired.is_empty() and before==after
	elif kind=="edge_exit":valid=valid and acquired.has("L") and before[foot]==after[foot]
	elif kind=="fresh_moved":valid=valid and acquired.size()==2 and absf(float(acquired.L)-.1)<.000001 and extension>0 and extension<=.16001
	else:valid=valid and acquired.size()==2 and extension>0 and extension<=.16001
	var detail:={"case":kind,"height":height,"speed":speed,"probe_depth":motion._landing_probe_depth(),"acquired":acquired,"first_entry_left_extension_m":extension,"before":before,"after":after}
	check(kind+" fresh geometry/cap/footprint contract",valid,detail);rows.append(detail)
	actor.free();floor_body.free();await process_frame

func run() -> void:
	await trial("inside_cap",1.19,20)
	await trial("beyond_cap",1.21,20)
	await trial("slow_miss",.12,.1)
	await trial("fresh_moved",.22,6)
	await trial("slope_rejected",.12,6)
	await trial("edge_exit",.12,6)
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"rows":rows,"motion_sha256":FileAccess.get_sha256(CANDIDATE),"fixture_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Actual imported near-rig and native fresh support queries under prescribed component states. First cap-entry extension measured, not accepted as smooth. No native trajectory/raster."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n");quit(0 if result.passed else 1)
