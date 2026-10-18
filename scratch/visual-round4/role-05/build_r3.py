from pathlib import Path
p=Path('scratch/visual-round4/role-05')
s=(p/'rama_motion.baseline.gd').read_text()
s=s.replace('var last_reason := ""','''var last_reason := ""
var stride_heading := 0.0
var foot_continuity := {}
var contact_modes := {"L":"swing","R":"swing"}
var plant_ids := {"L":0,"R":0}
var plant_serial := 0
var pelvis_compression := 0.0
var continuity_dt := 0.0
var contact_events: Array[Dictionary] = []''')
s=s.replace('\tfoot_locks={"L":false,"R":false}\n\nstatic func ground_gait','\nstatic func ground_gait')
s=s.replace('\tworld_velocity=velocity_; local_velocity=local_','''\tworld_velocity=velocity_; local_velocity=local_
	if Vector2(local_.x,local_.z).length()>.12:
		var requested_heading:=atan2(local_.x,local_.z)
		stride_heading+=clampf(angle_difference(stride_heading,requested_heading),-10.0*delta,10.0*delta)
	continuity_dt=delta''')
s=s.replace('\tif configured: _transition(.16)','''\tfoot_continuity.clear()
	contact_modes={"L":"swing","R":"swing"}
	pelvis_compression=0.0
	stride_heading=0.0
	continuity_dt=0.0
	if configured: _transition(.16)''')
s=s.replace('var direction_angle:=atan2(local_velocity.x,local_velocity.z) if movement_speed>.12 else 0.0','var direction_angle:=stride_heading')
s=s.replace('signf(local_velocity.x)*offset','sin(direction_angle)*offset')
a=s.index('func _apply_contact() -> void:')
b=s.index('\nfunc evaluate_pose()',a)
s=s[:a]+'''func _apply_contact() -> void:
	var dt:=continuity_dt
	if dt<=0: return
	continuity_dt=0.0
	var contact_allowed:=transition_age>=transition_duration and grounded and traversal=="ground" and locomotion in ["idle","walk","run","sprint","land"] and action!="death" and not (action=="measured_step" and action_stage!="none")
	var targets:={}
	var compression:=0.0
	var inverse:=rig.global_transform.affine_inverse()
	for side in ["L","R"]:
		var foot:=rig.find_bone("foot."+side)
		var current:=rig.global_transform*rig.get_bone_global_pose(foot).origin
		if not foot_continuity.has(side):
			foot_continuity[side]={"point":current,"velocity":Vector3.ZERO,"raw":current,"age":1.0,"offset":Vector3.ZERO,"offset_velocity":Vector3.ZERO,"blocked":false}
		var state: Dictionary=foot_continuity[side]
		state.age+=dt
		var gait_phase:=fposmod(phase+(.5 if side=="R" else 0),1)
		var duty:=.62 if locomotion=="walk" else .29
		var lateral:=absf(local_velocity.x)/movement_speed if movement_speed>.12 else 0.0
		duty=lerpf(duty,.29,lateral*lateral)
		var eligible:=contact_allowed and (locomotion in ["idle","land"] or gait_phase<duty)
		if not eligible: state.blocked=false
		var support:=eligible and not state.blocked
		if support and not foot_locks[side] and state.age<.10: support=false
		if support:
			if not foot_locks[side]:
				foot_targets[side]=Vector3(current.x,floor_y+rest_globals[foot].origin.y,current.z)
				foot_locks[side]=true
				plant_serial+=1; plant_ids[side]=plant_serial
				contact_events.append({"sample":modified_samples,"side":side,"event":"plant","plant_id":plant_ids[side],"anchor":foot_targets[side]})
			var local_target: Vector3=inverse*foot_targets[side]
			var hip:=rig.get_bone_global_pose(rig.find_bone("upperleg01."+side)).origin
			var length:=0.0
			for segment in ["upperleg02.","lowerleg01.","lowerleg02.","foot."]: length+=rest_positions[rig.find_bone(segment+side)].length()
			length-=.006
			var horizontal:=Vector2(hip.x-local_target.x,hip.z-local_target.z).length_squared()
			var available_height:=sqrt(maxf(.01,length*length-horizontal))
			var need:=maxf(0,hip.y-local_target.y-available_height)
			if need>MAX_PELVIS_COMPRESSION_M or horizontal>length*length:
				support=false; state.blocked=true
			else:
				targets[side]=local_target
				compression=maxf(compression,need)
		if not support and foot_locks[side]:
			foot_locks[side]=false
			state.age=0.0
			var raw_velocity: Vector3=(current-state.raw)/dt
			state.offset=state.point+state.velocity*dt-current
			state.offset_velocity=state.velocity-raw_velocity
			contact_modes[side]="release"
			contact_events.append({"sample":modified_samples,"side":side,"event":"reach release" if state.blocked else "stance exit","plant_id":plant_ids[side],"anchor":foot_targets[side],"point":state.point,"velocity":state.velocity})
		state.raw=current
	# Support gets the required bounded compression; release retains a bounded
	# continuation instead of deleting the complete correction in one sample.
	pelvis_compression=maxf(clampf(compression,0,MAX_PELVIS_COMPRESSION_M),move_toward(pelvis_compression,0,.9*dt))
	if pelvis_compression>.00001:
		for name_ in ["pelvis.L","pelvis.R","spine05"]:
			var index:=rig.find_bone(name_)
			var parent:=rig.get_bone_parent(index)
			var down:=rig.get_bone_global_pose(parent).basis.inverse()*Vector3(0,-pelvis_compression,0)
			rig.set_bone_pose_position(index,rig.get_bone_pose_position(index)+down)
	for side in ["L","R"]:
		var state: Dictionary=foot_continuity[side]
		var foot:=rig.find_bone("foot."+side)
		if foot_locks[side]:
			_solve_leg(side,targets[side])
			contact_modes[side]="support"
		elif state.age<.10:
			var u: float=state.age/.10
			var fade:=1-10*u*u*u+15*pow(u,4)-6*pow(u,5)
			var tangent:=u-6*u*u*u+8*pow(u,4)-3*pow(u,5)
			var target: Vector3=state.raw+state.offset*fade+state.offset_velocity*.10*tangent
			_solve_leg(side,inverse*target)
			contact_modes[side]="release"
		else: contact_modes[side]="swing"
		var actual:=rig.global_transform*rig.get_bone_global_pose(foot).origin
		if foot_locks[side]: max_contact_error=maxf(max_contact_error,actual.distance_to(foot_targets[side]))
		state.velocity=(actual-state.point)/dt
		state.point=actual
''' +s[b:]
s=s.replace('"foot_locks":foot_locks.duplicate(),','"foot_locks":foot_locks.duplicate(),"contact_modes":contact_modes.duplicate(),"plant_ids":plant_ids.duplicate(),')
(p/'rama_motion.release-r3.gd').write_text(s)
