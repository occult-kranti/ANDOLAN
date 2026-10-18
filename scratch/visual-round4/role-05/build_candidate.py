from pathlib import Path
p=Path('scratch/visual-round4/role-05')
s=(p/'rama_motion.baseline.gd').read_text()
s=s.replace('var last_reason := ""','''var last_reason := ""
# Presentation-only continuation state, integrated once per accepted update.
var stride_direction := Vector2(0,1)
var foot_continuity := {}
var contact_modes := {"L":"swing","R":"swing"}
var plant_ids := {"L":0,"R":0}
var plant_serial := 0
var pelvis_compression := 0.0
var continuity_dt := 0.0
var contact_events: Array[Dictionary] = []''')
s=s.replace('\tfoot_locks={"L":false,"R":false}\n\nstatic func ground_gait','\nstatic func ground_gait')
s=s.replace('\tworld_velocity=velocity_; local_velocity=local_','''\tworld_velocity=velocity_; local_velocity=local_
	var requested_direction:=Vector2(local_.x,local_.z)
	if requested_direction.length()>.12:
		stride_direction=stride_direction.move_toward(requested_direction.normalized(),10.0*delta)
	continuity_dt=delta''')
s=s.replace('\tif configured: _transition(.16)','''\tfoot_continuity.clear()
	contact_modes={"L":"swing","R":"swing"}
	pelvis_compression=0.0
	stride_direction=Vector2(0,1)
	continuity_dt=0.0
	if configured: _transition(.16)''')
s=s.replace('var direction_angle:=atan2(local_velocity.x,local_velocity.z) if movement_speed>.12 else 0.0','var direction_angle:=atan2(stride_direction.x,stride_direction.y) if stride_direction.length()>.01 else 0.0')
s=s.replace('signf(local_velocity.x)*offset','stride_direction.x*offset')
a=s.index('func _apply_contact() -> void:')
b=s.index('\nfunc evaluate_pose()',a)
s=s[:a]+'''func _apply_contact() -> void:
	var dt:=continuity_dt
	if dt<=0: return
	continuity_dt=0.0
	var contact_allowed:=transition_age>=transition_duration and grounded and traversal=="ground" and locomotion in ["idle","walk","run","sprint","land"] and action!="death" and not (action=="measured_step" and action_stage!="none")
	var targets:={}
	var requested_compression:=0.0
	var inverse:=rig.global_transform.affine_inverse()
	for side in ["L","R"]:
		var foot:=rig.find_bone("foot."+side)
		var current:=rig.global_transform*rig.get_bone_global_pose(foot).origin
		var ground_height:=floor_y+rest_globals[foot].origin.y
		var gait_phase:=fposmod(phase+(.5 if side=="R" else 0),1)
		var duty:=.62 if locomotion=="walk" else .29
		var lateral:=absf(local_velocity.x)/movement_speed if movement_speed>.12 else 0.0
		duty=lerpf(duty,.29,lateral*lateral)
		var support:=contact_allowed and (locomotion in ["idle","land"] or gait_phase<duty)
		if not foot_continuity.has(side):
			foot_continuity[side]={"point":current,"velocity":Vector3.ZERO,"blocked":false,"was_support":false}
		var state: Dictionary=foot_continuity[side]
		if not support: state.blocked=false
		var hip:=rig.get_bone_global_pose(rig.find_bone("upperleg01."+side)).origin
		var length:=0.0
		for segment in ["upperleg02.","lowerleg01.","lowerleg02.","foot."]: length+=rest_positions[rig.find_bone(segment+side)].length()
		length-=.006
		if foot_locks[side]:
			var local_anchor: Vector3=inverse*foot_targets[side]
			var horizontal:=Vector2(hip.x-local_anchor.x,hip.z-local_anchor.z).length_squared()
			var available_height:=sqrt(maxf(.01,length*length-horizontal))
			requested_compression=maxf(requested_compression,hip.y-local_anchor.y-available_height)
	# Compression also has history; stance exit cannot drop the pelvis instantly.
	pelvis_compression=move_toward(pelvis_compression,clampf(requested_compression,0,MAX_PELVIS_COMPRESSION_M),.9*dt)
	if pelvis_compression>.00001:
		for name_ in ["pelvis.L","pelvis.R","spine05"]:
			var index:=rig.find_bone(name_)
			var parent:=rig.get_bone_parent(index)
			var down:=rig.get_bone_global_pose(parent).basis.inverse()*Vector3(0,-pelvis_compression,0)
			rig.set_bone_pose_position(index,rig.get_bone_pose_position(index)+down)
	for side in ["L","R"]:
		var foot:=rig.find_bone("foot."+side)
		var desired:=rig.global_transform*rig.get_bone_global_pose(foot).origin
		var ground_height:=floor_y+rest_globals[foot].origin.y
		var state: Dictionary=foot_continuity[side]
		var gait_phase:=fposmod(phase+(.5 if side=="R" else 0),1)
		var duty:=.62 if locomotion=="walk" else .29
		var lateral:=absf(local_velocity.x)/movement_speed if movement_speed>.12 else 0.0
		duty=lerpf(duty,.29,lateral*lateral)
		var support:=contact_allowed and (locomotion in ["idle","land"] or gait_phase<duty)
		var hip:=rig.get_bone_global_pose(rig.find_bone("upperleg01."+side)).origin
		var length:=0.0
		for segment in ["upperleg02.","lowerleg01.","lowerleg02.","foot."]: length+=rest_positions[rig.find_bone(segment+side)].length()
		length-=.006
		var reason:="stance exit"
		if foot_locks[side] and hip.distance_to(inverse*foot_targets[side])>length-.018:
			support=false; state.blocked=true; reason="reach release"
		if foot_locks[side] and not support:
			foot_locks[side]=false
			contact_modes[side]="release"
			contact_events.append({"sample":modified_samples,"side":side,"event":reason,"plant_id":plant_ids[side],"anchor":foot_targets[side],"point":state.point,"velocity":state.velocity})
		if not foot_locks[side]:
			# Exact critically damped integration for the sampled moving target.
			# Release starts from the outgoing corrected point and world velocity.
			if support and not state.blocked: desired.y=ground_height
			var omega:=30.0
			var error: Vector3=state.point-desired
			var c: Vector3=state.velocity+omega*error
			var decay:=exp(-omega*dt)
			state.point=desired+(error+c*dt)*decay
			state.velocity=(state.velocity-omega*c*dt)*decay
			state.point.y=maxf(state.point.y,ground_height) if grounded else state.point.y
			if support and not state.blocked and absf(state.point.y-ground_height)<.008:
				var anchor:=Vector3(state.point.x,ground_height,state.point.z)
				if hip.distance_to(inverse*anchor)<length-.025:
					foot_targets[side]=anchor
					foot_locks[side]=true
					plant_serial+=1; plant_ids[side]=plant_serial
					contact_events.append({"sample":modified_samples,"side":side,"event":"plant","plant_id":plant_ids[side],"anchor":anchor})
		if foot_locks[side]:
			state.point=foot_targets[side]; state.velocity=Vector3.ZERO
			contact_modes[side]="support"
		elif contact_modes[side]!="release": contact_modes[side]="swing"
		_solve_leg(side,inverse*state.point)
		var actual:=rig.global_transform*rig.get_bone_global_pose(foot).origin
		if foot_locks[side]: max_contact_error=maxf(max_contact_error,actual.distance_to(foot_targets[side]))
		# Track the actual solved outgoing pose, including reach saturation.
		state.point=actual
		state.was_support=support
''' +s[b:]
s=s.replace('"foot_locks":foot_locks.duplicate(),','"foot_locks":foot_locks.duplicate(),"contact_modes":contact_modes.duplicate(),"plant_ids":plant_ids.duplicate(),')
(p/'rama_motion.release-r1.gd').write_text(s)
