from pathlib import Path
p=Path('scratch/visual-round4/role-05')
s=(p/'rama_motion.release-r3.gd').read_text()
s=s.replace('func evaluate_pose() -> void:\n\tif not configured: return','''func evaluate_pose() -> void:
	if not configured: return
	# Reapplying a SkeletonModifier pose must not advance continuation history.
	if continuity_dt<=0 and modified_samples>0:
		for index in rest_positions.size():
			rig.set_bone_pose_position(index,last_positions[index])
			rig.set_bone_pose_rotation(index,last_rotations[index])
		return''')
(p/'rama_motion.release-r3a.gd').write_text(s)
s=(p/'archived/probe-acceleration.gd').read_text()
s=s.replace('var trials: Array[Dictionary] = []','var trials: Array[Dictionary] = []\nvar skin_points: Array[Dictionary] = []\nvar collect_count := 0')
a=s.index('func execute(')
s=s[:a]+'''func collect_skin(node: Node, skeleton: Skeleton3D) -> void:
	if node is MeshInstance3D and node.skin:
		var binds: Array[Dictionary]=[]
		for index in node.skin.get_bind_count():
			var name_:=String(node.skin.get_bind_name(index))
			var bone: int=skeleton.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			var stride: int=joints.size()/vertices.size()
			for index in range(0,vertices.size(),24):
				var influences: Array[Dictionary]=[]
				var foot:=""
				for slot in stride:
					var weight:=weights[index*stride+slot]
					if weight<=0: continue
					var bind: Dictionary=binds[joints[index*stride+slot]]
					influences.append({"bone":bind.bone,"point":bind.inverse*vertices[index],"weight":weight})
					var name_:=String(skeleton.get_bone_name(bind.bone))
					if weight>.5 and (name_.begins_with("foot") or name_.begins_with("toe")): foot="L" if name_.ends_with(".L") else "R"
				skin_points.append({"foot":foot,"influences":influences})
	for child in node.get_children(): collect_skin(child,skeleton)

func skinned(motion: Node) -> PackedVector3Array:
	var points:=PackedVector3Array()
	for vertex in skin_points:
		var point:=Vector3.ZERO
		for influence in vertex.influences: point+=(motion.last_globals[influence.bone]*influence.point)*influence.weight
		points.append(motion.rig.global_transform*point)
	return points

''' +s[a:]
s=s.replace('\tvar rows: Array[Dictionary]=[]','''	if skin_points.is_empty(): collect_skin(model,motion.rig)
	var skin_previous:=PackedVector3Array()
	var previous_feet:={}
	var previous_foot_velocities:={}
	var previous_locks:={"L":false,"R":false}
	var max_skin_step:=0.0
	var max_support_skin_step:=0.0
	var min_skin_y:=INF
	var floor_contact_frames:=0
	var support_eligible_frames:=0
	var release_steps: Array[Dictionary]=[]
	var duplicate_pose_equal:=true
	var rows: Array[Dictionary]=[]''')
s=s.replace('var duration:=2.5 if name_.begins_with("jitter_") else 1.6','var duration:=2.5 if name_.begins_with("jitter_") else 1.6')
s=s.replace('\t\tmodel.position+=Vector3(state.velocity)/hz\n\t\tvar updated: bool=motion.update_motion(1.0/hz,state)','''		if name_=="reset" and frame==int(hz*.8): motion.cancel("test reset"); model.position=Vector3.ZERO
		var dt:=.08 if name_=="hitch" and frame==int(hz*.8) else 1.0/hz
		model.position+=Vector3(state.velocity)*dt
		var updated: bool=motion.update_motion(dt,state)''')
s=s.replace('\t\tfinite=finite and updated and motion.finite','''		var pose_before: Array=motion.last_globals.duplicate()
		motion.evaluate_pose()
		for index in pose_before.size(): duplicate_pose_equal=duplicate_pose_equal and pose_before[index]==motion.last_globals[index]
		var skin_now:=skinned(motion)
		var lowest:=INF
		var near_floor:=false
		for index in skin_now.size():
			lowest=minf(lowest,skin_now[index].y)
			if skin_points[index].foot!="" and absf(skin_now[index].y)<.015: near_floor=true
			if not skin_previous.is_empty():
				var step:=skin_now[index].distance_to(skin_previous[index])
				max_skin_step=maxf(max_skin_step,step)
				var side: String=skin_points[index].foot
				if side!="" and motion.foot_locks[side] and previous_locks[side]: max_support_skin_step=maxf(max_support_skin_step,step)
		min_skin_y=minf(min_skin_y,lowest)
		if near_floor: floor_contact_frames+=1
		skin_previous=skin_now
		finite=finite and updated and motion.finite''')
s=s.replace('\t\tvar feet:={}','''		var eligible:=false
		for side in ["L","R"]:
			var gp:=fposmod(motion.phase+(.5 if side=="R" else 0),1)
			var lateral: float=absf(motion.local_velocity.x)/motion.movement_speed if motion.movement_speed>.12 else 0.0
			var duty:=lerpf(.62 if motion.locomotion=="walk" else .29,.29,lateral*lateral)
			eligible=eligible or (motion.transition_age>=motion.transition_duration and motion.grounded and motion.traversal=="ground" and motion.locomotion in ["idle","walk","run","sprint","land"] and (motion.locomotion in ["idle","land"] or gp<duty))
		if eligible: support_eligible_frames+=1
		var feet:={}''')
s=s.replace('\t\t\tfeet[side]=[point.x,point.y,point.z]','''			feet[side]=[point.x,point.y,point.z]
			if previous_feet.has(side):
				var velocity: Vector3=(point-previous_feet[side])/dt
				if previous_locks[side] and not motion.foot_locks[side]:
					release_steps.append({"frame":frame,"side":side,"step_m":point.distance_to(previous_feet[side]),"outgoing_velocity_mps":str(previous_foot_velocities.get(side,Vector3.ZERO)),"incoming_velocity_mps":str(velocity),"velocity_change_mps":velocity.distance_to(previous_foot_velocities.get(side,Vector3.ZERO)),"acceleration_mps2":velocity.distance_to(previous_foot_velocities.get(side,Vector3.ZERO))/dt})
				previous_foot_velocities[side]=velocity
			previous_feet[side]=point''')
s=s.replace('\tvar result:={"configured":true','''		previous_locks=motion.foot_locks.duplicate()
	var result:={"sampled_skin_vertices":skin_points.size(),"maximum_skin_step_m":max_skin_step,"maximum_planted_skin_step_m":max_support_skin_step,"minimum_sampled_skin_y_m":min_skin_y,"floor_contact_frames":floor_contact_frames,"support_eligible_frames":support_eligible_frames,"release_steps":release_steps,"duplicate_pose_equal":duplicate_pose_equal,"configured":true''')
s=s.replace('\telif name_=="action_cancel":\n\t\tstate.velocity', '\telif name_ in ["action_cancel","hitch","reset"]:\n\t\tstate.velocity')
s=s.replace('\treturn state\n\nfunc collect_skin','''	elif name_=="strafe": state.velocity=Vector3(4,0,0); state.aiming=true
	elif name_=="backpedal": state.velocity=Vector3(0,0,-6); state.aiming=true
	elif name_=="gradual_steer": state.velocity=Vector3(sin(t*1.4),0,cos(t*1.4))*6; state.aiming=true
	elif name_=="stationary_aim": state.aiming=true; state.aim_pitch=.3
	return state

func collect_skin''')
s=s.replace('for name_ in ["accelerated_reversal","reversal"]:', 'for name_ in ["accelerated_reversal","reversal","start_stop","traversal","strafe","backpedal","gradual_steer","stationary_aim","action_cancel","reset","hitch"]:')
s=s.replace('"test_sha256":FileAccess.get_sha256(get_script().resource_path)', '"test_sha256":FileAccess.get_sha256(get_script().resource_path),"hero_sha256":FileAccess.get_sha256(HERO),"library_sha256":FileAccess.get_sha256("res://assets/animations/rama_hero_motion.tres")')
(p/'probe-continuity.gd').write_text(s)
# Unchanged existing skin/finger/contact suite; only controller path is substituted.
t=Path('games/yuga-native/tests/rama_motion_cases.gd').read_text().replace('preload("res://scripts/rama_motion.gd")','preload("/workspace/ANDOLAN/scratch/visual-round4/role-05/rama_motion.release-r3a.gd")')
(p/'rama_motion_cases.r3a.gd').write_text(t)
