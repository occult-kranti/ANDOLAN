extends "/workspace/ANDOLAN/games/yuga-native/tests/graphics_g2_support_cases.gd"
## Imported-rig component descent; prescribed shared roots, not native gameplay.
const OWNER := "/workspace/ANDOLAN/games/yuga-native/docs/evidence/desktop-finish/continuation-oct18/W5-motion-r1/"

func signature(value: Variant) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256); context.update(var_to_bytes(value))
	return context.finish().hex_encode()

func descent(path: String, hz: int, support_y: float, height: float) -> Array:
	var support := StaticBody3D.new(); support.collision_layer=1
	var shape_node := CollisionShape3D.new(); var box := BoxShape3D.new(); box.size=Vector3(4,.2,4);shape_node.shape=box
	support.add_child(shape_node);root.add_child(support);support.position.y=support_y-.1
	var actor := CharacterBody3D.new();actor.collision_layer=2;root.add_child(actor)
	var model: Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();actor.add_child(model)
	var motion=load(path).new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	var selected := soles(model,motion.rig)
	var dt := 1.0/hz;var stride := maxi(1,hz/30);var base_y:=support_y+.0008394047617912292
	actor.position.y=base_y
	var state := {"grounded":true,"floor_y":base_y,"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"traversal":"ground"}
	await physics_frame
	for tick in int(hz*.3): motion.update_motion(dt,state);motion.evaluate_pose()
	actor.position.y=base_y+height
	var speed := -2.0 if height>.2 else -1.0
	var rows:Array=[];var previous_skin:Array=[];var previous_velocity:Array=[]
	for tick in int(hz*.8):
		if actor.position.y>base_y:
			speed-=18.0*dt;actor.position.y=maxf(base_y,actor.position.y+speed*dt)
		state.grounded=actor.position.y<=base_y
		state.floor_y=actor.position.y;state.velocity=Vector3(0,0 if state.grounded else speed,0);state.local_velocity=state.velocity
		motion.update_motion(dt,state)
		if (tick+1)%stride!=0:continue
		motion.evaluate_pose()
		var nonleg:Array=[];var leg_rotations:Dictionary={};var feet:Dictionary={}
		for index in motion.rig.get_bone_count():
			var bone_name:String=motion.rig.get_bone_name(index)
			if bone_name.begins_with("upperleg") or bone_name.begins_with("lowerleg") or bone_name.begins_with("foot") or bone_name.begins_with("toe"):
				if bone_name.begins_with("upperleg") or bone_name.begins_with("lowerleg") or bone_name.begins_with("foot"):
					var q:Quaternion=motion.rig.get_bone_pose_rotation(index);leg_rotations[bone_name]=[q.x,q.y,q.z,q.w]
			else:nonleg.append([motion.rig.get_bone_pose(index),motion.last_globals[index]])
		for side in ["L","R"]:feet[side]=vec(motion.rig.global_transform*motion.last_globals[motion.rig.find_bone("foot."+side)].origin)
		var row:={"tick":tick,"grounded":state.grounded,"root_y":actor.position.y,"velocity":vec(state.velocity),"nonleg_sha256":signature(nonleg),"clocks":[motion.phase,motion.locomotion_age,motion.transition_age,motion.transition_duration,motion.action_elapsed,motion.release_count,motion.cancel_count],"locks":motion.foot_locks.duplicate(),"targets":signature(motion.foot_targets),"feet":feet,"leg_rotations":leg_rotations}
		if actor.position.y-support_y<.6:
			var skin:=measure(motion,selected,support_y);var skin_positions:Array=skin.positions;skin.erase("positions")
			var max_step:=Vector3.ZERO;var max_accel:=Vector3.ZERO;var velocities:Array=[]
			if not previous_skin.is_empty():
				for index in skin_positions.size():
					var delta:Vector3=skin_positions[index]-previous_skin[index];max_step=max_step.max(delta.abs())
					var velocity_:Vector3=delta/(dt*stride);velocities.append(velocity_)
					if not previous_velocity.is_empty():max_accel=max_accel.max(((velocity_-previous_velocity[index])/(dt*stride)).abs())
			row["skin"]={"L":skin.L,"R":skin.R,"max_axis_step_m":vec(max_step),"max_axis_velocity_change_mps2":vec(max_accel),"cadence_s":dt*stride}
			previous_skin=skin_positions;previous_velocity=velocities
		rows.append(row)
	actor.free();support.free();await process_frame
	return rows

func run() -> void:
	var cases:=[{"name":"ordinary30","hz":30,"support":0.0,"height":1.5},{"name":"ordinary60","hz":60,"support":0.0,"height":1.5},{"name":"ordinary120","hz":120,"support":0.0,"height":1.5},{"name":"elevated60","hz":60,"support":.7,"height":1.5},{"name":"low60","hz":60,"support":0.0,"height":.12}]
	var cases_rows:Array=[]
	for item in cases:
		var a:Array=await descent("/workspace/ANDOLAN/games/yuga-native/scripts/rama_motion.gd",item.hz,item.support,item.height)
		var b:Array=await descent(OWNER+"rama_motion.gd",item.hz,item.support,item.height)
		var first:int=-1;var controls:=true;var nonleg:=true;var locks:=true;var floor_safe:=true;var amin:=INF;var bmin:=INF
		for i in b.size():
			if first<0 and b[i].grounded:first=i
			for key in ["tick","grounded","root_y","velocity","clocks"]:controls=controls and a[i][key]==b[i][key]
			nonleg=nonleg and a[i].nonleg_sha256==b[i].nonleg_sha256
			locks=locks and a[i].locks==b[i].locks
			if b[i].has("skin"):
				for side in ["L","R"]:
					amin=minf(amin,a[i].skin[side].minimum_m);bmin=minf(bmin,b[i].skin[side].minimum_m)
					floor_safe=floor_safe and b[i].skin[side].minimum_m>=-.005
		check(item.name+" first grounded imported soles within5mm",first>=0 and b[first].skin.L.minimum_m<=.005 and b[first].skin.R.minimum_m<=.005,{"first":first,"baseline":a[first],"candidate":b[first]})
		check(item.name+" root clocks nonleg poses and anchor admission exact",controls and nonleg and locks,{"controls":controls,"nonleg":nonleg,"lock_schedule":locks})
		check(item.name+" actual skin retains floor and no deeper minimum",floor_safe and bmin>=amin,{"baseline_min_m":amin,"candidate_min_m":bmin})
		cases_rows.append({"case":item,"baseline":a,"candidate":b})
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"cases":cases_rows,"source":{"baseline":FileAccess.get_sha256("/workspace/ANDOLAN/games/yuga-native/scripts/rama_motion.gd"),"candidate":FileAccess.get_sha256(OWNER+"rama_motion.gd"),"fixture":FileAccess.get_sha256(get_script().resource_path)},"scope":"Actual imported near-rig skinned geometry, prescribed identical ballistic root states at30/60/120physics with30Hz evaluation. Component timing only; no native collision authority, rendered smoothness or actual first-contact acceptance. Every sampled near-ground foot step/leg quaternion retained."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	quit(0 if result.passed else 1)
