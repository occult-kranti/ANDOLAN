extends "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/next-motion/W5-landing-preparation-candidate-r1/preparation_guard_cases.gd"

func run() -> void:
	var support:=StaticBody3D.new();support.collision_layer=1
	var shape:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape.shape=box;support.add_child(shape);root.add_child(support);support.position.y=-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor);actor.position.y=.05
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load("res://scripts/rama_motion.gd").new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var state:={"grounded":true,"floor_y":.05,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	for tick in 24:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	actor.position.y=.5;state.grounded=false;state.floor_y=.5;state.velocity=Vector3(0,-6,0);state.local_velocity=state.velocity
	for tick in 24:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	var foot:int=motion.rig.find_bone("foot.L");var point:Vector3=motion.rig.global_transform*motion.last_globals[foot].origin
	var hit:=actor.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(point.x,.58,point.z),Vector3(point.x,-.08,point.z),1,[actor.get_rid()]))
	var before:=pose_rows(motion);motion._prepare_landing_legs()
	check("real500mm support is beyond450mm preparation horizon",motion.measured_support_seen and not hit.is_empty() and absf(float(hit.position.y))<.00001 and motion.descent_support_y.is_empty() and before==pose_rows(motion),{"support_hit":not hit.is_empty(),"root_height":actor.position.y,"candidate_horizon":motion.LANDING_PREPARE_HEIGHT_M,"cache":motion.descent_support_y.duplicate()})
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"motion_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"fixture_sha256":FileAccess.get_sha256(get_script().resource_path)}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	actor.free();support.free();quit(0 if result.passed else 1)
