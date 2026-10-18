extends "/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd"
## Private candidate's downward preparation, with actual imported rig and physics.
var rows:Array=[]

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	Engine.physics_ticks_per_second=60
	call_deferred("run")

func pose_rows(m:Node) -> Array:
	var result:Array=[]
	for index in m.rig.get_bone_count():
		var t:Transform3D=m.rig.get_bone_global_pose(index)
		result.append([vec(t.origin),vec(t.basis.x),vec(t.basis.y),vec(t.basis.z)])
	return result

func trial(kind:String) -> void:
	var floor_body:=StaticBody3D.new();floor_body.collision_layer=1
	var shape_node:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(4,.2,4);shape_node.shape=box
	floor_body.add_child(shape_node);root.add_child(floor_body);floor_body.position.y=-.1
	var actor:=CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load("res://scripts/rama_motion.gd").new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var state:={"grounded":true,"floor_y":.05,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	actor.position.y=.05
	await physics_frame
	for tick in 24:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	actor.position.y=.12;state.grounded=false;state.floor_y=.12;state.velocity=Vector3(0,-6,0);state.local_velocity=state.velocity
	for tick in 24:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	var acquired:Dictionary=motion.descent_support_y.duplicate()
	# Restore the same sampled pose without either descent solver, retaining the
	# fresh query fields, so each mutation challenges a meaningful preparation.
	motion.descent_support_y.clear();motion.evaluate_pose();motion.descent_support_y=acquired
	var before:=pose_rows(motion)
	var before_local:Array=[]
	for index in motion.rig.get_bone_count():before_local.append(motion.rig.get_bone_pose(index))
	var clocks:=[motion.phase,motion.transition_age,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]
	var roots:=actor.transform;var targets:Dictionary=motion.foot_targets.duplicate();var locks:Dictionary=motion.foot_locks.duplicate()
	if kind=="owner_moved":floor_body.position.y-=.1
	elif kind=="shape_moved":shape_node.position.x+=.1
	elif kind=="shape_disabled":shape_node.disabled=true
	elif kind=="shape_removed":shape_node.shape=null
	elif kind=="shape_changed":box.size.y=.1
	elif kind=="layer_removed":floor_body.collision_layer=2
	elif kind=="owner_queued":floor_body.queue_free()
	elif kind=="root_moved":actor.position.x+=.1
	elif kind=="action_started":motion.request_action("kodanda",.18,.22)
	elif kind=="aim_started":motion.aim_weight=.5
	elif kind=="footprint_changed":
		var hip:int=motion.rig.find_bone("upperleg01.L")
		motion.rig.set_bone_pose_position(hip,motion.rig.get_bone_pose_position(hip)+Vector3(.04,0,0))
		before=pose_rows(motion)
	# Intentional action/aim activation is the input; preparation itself must not advance clocks.
	clocks=[motion.phase,motion.transition_age,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]
	var foot:int=motion.rig.find_bone("foot.L")
	var before_y:float=motion.rig.get_bone_global_pose(foot).origin.y
	motion._prepare_landing_legs()
	var after:=pose_rows(motion);var after_y:float=motion.rig.get_bone_global_pose(foot).origin.y
	var different:=before!=after
	var valid:=acquired.size()==2
	if kind=="valid":
		var unchanged_nonleg:=true
		for index in motion.rig.get_bone_count():
			var name_:String=motion.rig.get_bone_name(index)
			if name_.begins_with("upperleg") or name_.begins_with("lowerleg") or name_.begins_with("foot") or name_.begins_with("toe"):continue
			unchanged_nonleg=unchanged_nonleg and before[index]==after[index] and before_local[index]==motion.rig.get_bone_pose(index)
		valid=valid and different and before_y-after_y>.05 and unchanged_nonleg and actor.transform==roots and motion.foot_targets==targets and motion.foot_locks==locks
	elif kind=="footprint_changed":valid=valid and before[foot]==after[foot]
	else:valid=valid and not different
	valid=valid and clocks==[motion.phase,motion.transition_age,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]
	var detail:={"case":kind,"acquired":acquired,"left_extension_m":before_y-after_y,"pose_changed":different,"before":before,"after":after,"same_clocks":clocks==[motion.phase,motion.transition_age,motion.locomotion_age,motion.action_elapsed,motion.release_count,motion.cancel_count]}
	check(kind+" fresh descent preparation ownership",valid,detail);rows.append(detail)
	actor.free()
	if is_instance_valid(floor_body):floor_body.free()
	await process_frame

func run() -> void:
	for kind in ["valid","owner_moved","shape_moved","shape_disabled","shape_removed","shape_changed","layer_removed","owner_queued","root_moved","footprint_changed","action_started","aim_started"]:await trial(kind)
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"motion_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"fixture_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Injected60Hz component states; actual imported164-bone rig and real support queries. No native trajectory or rendered acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	quit(0 if result.passed else 1)
