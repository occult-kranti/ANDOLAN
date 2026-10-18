extends SkeletonModifier3D
## Complete original Rama presentation controller. Combat owns every release.
## Locomotion is distance-driven; actions occupy the upper body unless explicitly
## full-body. No collision, velocity, ammo, cooldown or damage is changed here.
const LIBRARY_PATH := "res://assets/animations/rama_hero_motion.tres"
const GRIP_CENTER := Vector3(0,.105,.025)
const GRIP_RADIUS := .022
const GRIP_HALF_LENGTH := .046
const STRING_CONTACT := Vector3(.012613,.114969,-.042728)
# Speed hysteresis prevents minor controller/network correction noise from
# restarting the whole-body blend and dropping both support-foot locks every
# frame. These are presentation thresholds, never movement or combat rules.
const WALK_RUN_ENTER_MPS := 3.0
const WALK_RUN_EXIT_MPS := 2.8
const RUN_SPRINT_ENTER_MPS := 7.0
const RUN_SPRINT_EXIT_MPS := 6.75
# Late walking stance can need more than 10 cm of hip compression while both
# feet remain planted. Keep a bounded allowance instead of stretching the leg
# or silently moving its locked world-space target to satisfy the solver.
const MAX_PELVIS_COMPRESSION_M := .14
const ACTIONS := {
	"kodanda":["draw","release",false],
	"piercing_dawn":["piercing_draw","piercing_release",false],
	"guardian_circle":["circle_draw","circle_release",false],
	"dawn_volley":["volley_draw","volley_release",false],
	"measured_step":["dash","dash",true],
	"hit":["hit","hit",true], "death":["death","death",true],
	"respawn":["respawn","respawn",true],
}
var nocked_arrow: Node3D
var configured := false
var rig: Skeleton3D
var library: AnimationLibrary
var rest_positions: Array[Vector3] = []
var rest_rotations: Array[Quaternion] = []
var rest_globals: Array[Transform3D] = []
var track_maps := {}
var upper: Array[bool] = []
var last_positions: Array[Vector3] = []
var last_rotations: Array[Quaternion] = []
var last_globals: Array[Transform3D] = []
var blend_positions: Array[Vector3] = []
var blend_rotations: Array[Quaternion] = []
var transition_positions: Array[Vector3] = []
var transition_rotations: Array[Quaternion] = []
var transition_age := 1.0
var transition_duration := .16
var locomotion := "idle"
var phase := 0.0
var locomotion_age := 0.0
var movement_speed := 0.0
var local_velocity := Vector3.ZERO
var world_velocity := Vector3.ZERO
var grounded := true
var traversal := "ground"
var aim_pitch := 0.0
var aim_yaw := 0.0
var aim_weight := 0.0
var aim_target := 0.0
var action := ""
var action_stage := "none"
var action_elapsed := 0.0
var windup := .18
var recovery := .22
var action_blend := 0.0
var action_fade := 0.0
var cancelled_pose := false
var cancel_positions: Array[Vector3] = []
var cancel_rotations: Array[Quaternion] = []
var action_from_positions: Array[Vector3] = []
var action_from_rotations: Array[Quaternion] = []
var nocked := false
var warm_bow := false
var release_count := 0
var cancel_count := 0
var rejected_states := 0
var modified_samples := 0
var finite := true
var floor_y := 0.0
var foot_locks := {"L":false,"R":false}
var foot_targets := {"L":Vector3.ZERO,"R":Vector3.ZERO}
var max_contact_error := 0.0
var max_string_error := 0.0
var pending_delta := 0.0
var last_reason := ""
# Presentation-only continuation state, integrated once per accepted update.
var stride_direction := Vector2(0,1)
var foot_continuity := {}
var contact_modes := {"L":"swing","R":"swing"}
var plant_ids := {"L":0,"R":0}
var plant_serial := 0
var pelvis_compression := 0.0
var continuity_dt := 0.0
var contact_events: Array[Dictionary] = []

func _find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := _find(child,kind)
		if found: return found
	return null

func configure(visual: Node, animator: AnimationPlayer = null) -> bool:
	if configured or visual==null or get_parent()!=null: return false
	var skeleton: Skeleton3D=_find(visual,"Skeleton3D")
	if not skeleton or skeleton.get_bone_count()!=164 or not ResourceLoader.exists(LIBRARY_PATH): return false
	for bone_name in ["root","spine05","spine03","spine01","head","bowstring","wrist.L","wrist.R","upperleg01.L","upperleg02.L","lowerleg01.L","lowerleg02.L","foot.L","upperleg01.R","upperleg02.R","lowerleg01.R","lowerleg02.R","foot.R"]:
		if skeleton.find_bone(bone_name)<0: return false
	var candidate=load(LIBRARY_PATH)
	if not candidate is AnimationLibrary: return false
	if not candidate.has_meta("rama_rig_rest") or not candidate.has_meta("rama_rig_names") or not candidate.has_meta("rama_rig_parents"): return false
	var expected_rest: Array=candidate.get_meta("rama_rig_rest")
	var expected_names: Array=candidate.get_meta("rama_rig_names")
	var expected_parents: PackedInt32Array=candidate.get_meta("rama_rig_parents")
	if expected_rest.size()!=skeleton.get_bone_count(): return false
	for index in skeleton.get_bone_count():
		if skeleton.get_bone_name(index)!=expected_names[index] or skeleton.get_bone_parent(index)!=expected_parents[index]: return false
		var actual:=skeleton.get_bone_rest(index)
		var expected: Transform3D=expected_rest[index]
		if actual.origin.distance_to(expected.origin)>.0001: return false
		if actual.basis.x.distance_to(expected.basis.x)>.0001 or actual.basis.y.distance_to(expected.basis.y)>.0001 or actual.basis.z.distance_to(expected.basis.z)>.0001: return false
	for clip in ["idle","walk","run","sprint","draw","release","flight","grapple","aim"]:
		if not candidate.has_animation(clip): return false
	rig=skeleton
	library=candidate
	for index in rig.get_bone_count():
		var rest:=rig.get_bone_rest(index)
		rest_positions.append(rest.origin)
		rest_rotations.append(rest.basis.get_rotation_quaternion().normalized())
		rest_globals.append(rig.get_bone_global_rest(index))
		var name_:=String(rig.get_bone_name(index))
		upper.append(not (name_=="root" or name_.begins_with("pelvis") or name_.contains("leg") or name_.begins_with("foot") or name_.begins_with("toe")))
	for clip in library.get_animation_list():
		var rows:=[]
		var anim:=library.get_animation(clip)
		for track in anim.get_track_count():
			var path:=anim.track_get_path(track)
			if path.get_subname_count()!=1: continue
			var index:=rig.find_bone(String(path.get_subname(0)))
			if index>=0: rows.append({"bone":index,"track":track,"type":anim.track_get_type(track)})
		track_maps[String(clip)]=rows
	last_positions=rest_positions.duplicate()
	last_rotations=rest_rotations.duplicate()
	last_globals=rest_globals.duplicate()
	blend_positions=rest_positions.duplicate()
	blend_rotations=rest_rotations.duplicate()
	if animator: animator.pause()
	rig.add_child(self)
	name="RamaMotion"
	configured=true
	_make_arrow()
	floor_y=rig.global_position.y
	return true

func _smooth(value: float) -> float:
	var t:=clampf(value,0,1)
	return t*t*(3-2*t)

func _transition(duration := .16) -> void:
	transition_positions=blend_positions.duplicate()
	transition_rotations=blend_rotations.duplicate()
	transition_age=0
	transition_duration=duration

static func ground_gait(speed: float, previous: String) -> String:
	if speed<=.12: return "idle"
	# Keep the authored acceleration thresholds; hysteresis only delays downshift.
	# In particular, never extend the short walk stride above its 3 m/s envelope.
	if previous=="walk" and speed<=WALK_RUN_ENTER_MPS: return "walk"
	# Vector lengths use float32; 2.8 arrives as 2.79999995. Compare against the
	# same representation so an exact input at the boundary does not downshift.
	if previous=="run" and speed>=Vector2(WALK_RUN_EXIT_MPS,0).x and speed<=RUN_SPRINT_ENTER_MPS: return "run"
	if previous=="sprint" and speed>=RUN_SPRINT_EXIT_MPS: return "sprint"
	# A start, landing or large speed change picks the appropriate gait directly.
	if speed>7: return "sprint"
	if speed>3: return "run"
	return "walk"

func update_motion(delta: float, state: Dictionary) -> bool:
	if not configured: return false
	if not is_finite(delta) or delta<=0 or delta>.1:
		rejected_states+=1
		cancel("invalid delta")
		return false
	var velocity_: Vector3=state.get("velocity",Vector3.ZERO)
	var local_: Vector3=state.get("local_velocity",rig.global_basis.inverse()*velocity_)
	var pitch_: float=state.get("aim_pitch",0.0)
	var yaw_: float=state.get("aim_yaw",0.0)
	var floor_: float=state.get("floor_y",rig.global_position.y)
	if not velocity_.is_finite() or not local_.is_finite() or not is_finite(pitch_) or not is_finite(yaw_) or not is_finite(floor_):
		rejected_states+=1
		cancel("invalid pose input")
		return false
	world_velocity=velocity_; local_velocity=local_
	var requested_direction:=Vector2(local_.x,local_.z)
	if requested_direction.length()>.12:
		stride_direction=stride_direction.move_toward(requested_direction.normalized(),10.0*delta)
	continuity_dt=delta
	movement_speed=Vector2(local_.x,local_.z).length()
	floor_y=floor_
	var was_grounded:=grounded
	grounded=bool(state.get("grounded",true))
	traversal=String(state.get("traversal","ground"))
	if traversal not in ["ground","flight","grapple"]: traversal="ground"
	aim_target=1.0 if bool(state.get("aiming",false)) else 0.0
	aim_pitch=lerpf(aim_pitch,clampf(pitch_,-.85,.65),1-exp(-16*delta))
	aim_yaw=lerp_angle(aim_yaw,clampf(yaw_,-.70,.70),1-exp(-14*delta))
	aim_weight=lerpf(aim_weight,aim_target,1-exp(-12*delta))
	var next:="idle"
	if traversal!="ground": next=traversal
	elif bool(state.get("dash",false)): next="dash"
	elif not grounded:
		next="jump" if velocity_.y>1.0 else "fall"
	elif not was_grounded: next="land"
	elif locomotion=="land" and locomotion_age<.22: next="land"
	else: next=ground_gait(movement_speed,locomotion)
	if next!=locomotion:
		_transition(.10 if next=="land" else .16)
		locomotion=next
		locomotion_age=0
	locomotion_age+=delta
	transition_age+=delta
	var stride:=1.45 if locomotion=="walk" else (3.25 if locomotion=="sprint" else 2.96)
	var lateral:=absf(local_velocity.x)/movement_speed if movement_speed>.12 else 0.0
	stride=lerpf(stride,1.6,lateral*lateral)
	if locomotion in ["walk","run","sprint"]:
		phase=fposmod(phase+delta*movement_speed/stride,1)
	else: phase=fposmod(phase+delta*.45,1)
	if action_stage in ["windup","hold"]:
		action_elapsed+=delta
		if action_elapsed>=windup: action_stage="hold"
		action_blend=minf(1,action_blend+delta/.10)
	elif action_stage=="recovery":
		action_elapsed+=delta
		action_blend=1.0
		if action_elapsed>=recovery and action!="death":
			action_stage="fade"
			action_fade=0
	elif action_stage=="fade":
		action_fade+=delta
		action_blend=1-_smooth(action_fade/.16)
		if action_fade>=.16:
			action=""; action_stage="none"; action_blend=0
	pending_delta=delta
	return true

func request_action(ability_id: String, duration := .18, recovery_seconds := .22) -> bool:
	if not configured or not ACTIONS.has(ability_id) or not is_finite(duration) or not is_finite(recovery_seconds) or duration<=0 or recovery_seconds<=0 or duration>5 or recovery_seconds>5: return false
	if action=="death" and ability_id!="respawn": return false
	if action_stage in ["windup","hold"] and ability_id not in ["hit","death","respawn"]: return false
	warm_bow=ability_id=="kodanda" and (aim_weight>.5 or (action in ["kodanda","piercing_dawn","dawn_volley"] and action_stage!="none"))
	action_from_positions=blend_positions.duplicate()
	action_from_rotations=blend_rotations.duplicate()
	action=ability_id
	action_stage="windup"
	action_elapsed=0
	windup=duration; recovery=recovery_seconds
	action_blend=1; action_fade=0; cancelled_pose=false
	nocked=ability_id in ["kodanda","piercing_dawn","dawn_volley"]
	if ability_id=="death": foot_locks={"L":false,"R":false}
	return true

func release_action(ability_id: String) -> bool:
	if not configured or ability_id!=action or action_stage not in ["windup","hold"]: return false
	action_stage="recovery"
	action_elapsed=0
	action_blend=1
	nocked=false
	if is_instance_valid(nocked_arrow): nocked_arrow.visible=false
	release_count+=1
	return true

func cancel_action(reason := "cancelled") -> void:
	if action_stage!="none":
		action_stage="fade"; action_fade=0; cancel_count+=1
		cancelled_pose=true
		cancel_positions=blend_positions.duplicate(); cancel_rotations=blend_rotations.duplicate()
	nocked=false
	if is_instance_valid(nocked_arrow): nocked_arrow.visible=false
	last_reason=reason

func cancel(reason := "reset") -> void:
	cancel_action(reason)
	action=""; action_stage="none"; action_blend=0
	phase=0; locomotion="idle"; locomotion_age=0
	aim_weight=0; aim_target=0; aim_pitch=0; aim_yaw=0
	foot_locks={"L":false,"R":false}
	foot_continuity.clear()
	contact_modes={"L":"swing","R":"swing"}
	pelvis_compression=0.0
	stride_direction=Vector2(0,1)
	continuity_dt=0.0
	if configured: _transition(.16)

func _sample(clip: String, normalized: float) -> Dictionary:
	var positions:=rest_positions.duplicate()
	var rotations:=rest_rotations.duplicate()
	var anim:=library.get_animation(clip)
	var time:=clampf(normalized,0,1)*anim.length
	for row in track_maps[clip]:
		if row.type==Animation.TYPE_ROTATION_3D: rotations[row.bone]=anim.rotation_track_interpolate(row.track,time).normalized()
		elif row.type==Animation.TYPE_POSITION_3D: positions[row.bone]=anim.position_track_interpolate(row.track,time)
	return {"positions":positions,"rotations":rotations}

func _mix_pose(base: Dictionary, overlay: Dictionary, weight: float, full_body := false) -> void:
	for index in rest_positions.size():
		if not full_body and not upper[index]: continue
		base.positions[index]=base.positions[index].lerp(overlay.positions[index],weight)
		base.rotations[index]=base.rotations[index].slerp(overlay.rotations[index],weight).normalized()

func _global_rotate(index: int, desired: Quaternion) -> void:
	var parent:=rig.get_bone_parent(index)
	var parent_q:=rig.get_bone_global_pose(parent).basis.get_rotation_quaternion() if parent>=0 else Quaternion.IDENTITY
	rig.set_bone_pose_rotation(index,(parent_q.inverse()*desired).normalized())

func _aim_bone(index: int, direction: Vector3) -> void:
	var rest:=rest_globals[index].basis.orthonormalized()
	var q:=Quaternion(rest.y.normalized(),direction.normalized())*rest.get_rotation_quaternion()
	_global_rotate(index,q.normalized())

func _solve_leg(side: String, target: Vector3) -> void:
	var n1:=rig.find_bone("upperleg01."+side)
	var n2:=rig.find_bone("upperleg02."+side)
	var n3:=rig.find_bone("lowerleg01."+side)
	var n4:=rig.find_bone("lowerleg02."+side)
	var end:=rig.find_bone("foot."+side)
	var a:=rest_positions[n2].length()+rest_positions[n3].length()
	var c:=rest_positions[n4].length()+rest_positions[end].length()
	var origin:=rig.get_bone_global_pose(n1).origin
	var offset:=target-origin
	var d:=clampf(offset.length(),absf(a-c)+.002,a+c-.004)
	var direction:=offset.normalized()
	var bend:=Vector3(0,.15,1)
	bend=(bend-direction*bend.dot(direction)).normalized()
	var along:=(a*a-c*c+d*d)/(2*d)
	var joint:=origin+direction*along+bend*sqrt(maxf(0,a*a-along*along))
	for index in [n1,n2]: _aim_bone(index,joint-origin)
	for index in [n3,n4]: _aim_bone(index,origin+direction*d-joint)
	_global_rotate(end,rest_globals[end].basis.get_rotation_quaternion().normalized())

func _apply_aim() -> void:
	var weight:=maxf(aim_weight,action_blend if action in ["kodanda","piercing_dawn","dawn_volley"] else 0)
	if weight<.001: return
	# Rotate the complete shoulder frame, preserving arm/string relationship.
	var index:=rig.find_bone("spine03")
	var current:=rig.get_bone_global_pose(index).basis.get_rotation_quaternion()
	var delta:=Quaternion(Vector3.UP,aim_yaw*weight)*Quaternion(Vector3.RIGHT,-aim_pitch*weight)
	_global_rotate(index,(delta*current).normalized())

func _apply_contact() -> void:
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
		if support:
			var prospective:=foot_targets[side] if foot_locks[side] else Vector3(current.x,ground_height,current.z)
			var local_anchor: Vector3=inverse*prospective
			var horizontal:=Vector2(hip.x-local_anchor.x,hip.z-local_anchor.z).length_squared()
			var available_height:=sqrt(maxf(.01,length*length-horizontal))
			requested_compression=maxf(requested_compression,hip.y-local_anchor.y-available_height)
	# Compression also has history; stance exit cannot drop the pelvis instantly.
	pelvis_compression=maxf(clampf(requested_compression,0,MAX_PELVIS_COMPRESSION_M),move_toward(pelvis_compression,0,.9*dt))
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
		if foot_locks[side] and hip.distance_to(inverse*foot_targets[side])>length:
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
			if support and not state.blocked:
				var anchor:=Vector3(desired.x,ground_height,desired.z)
				if hip.distance_to(inverse*anchor)<=length:
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

func evaluate_pose() -> void:
	if not configured: return
	var normalized:=phase
	if locomotion in ["jump","land","dash"]: normalized=clampf(locomotion_age/library.get_animation(locomotion).length,0,1)
	var pose:=_sample(locomotion,normalized)
	# Sidestep/backpedal trajectories preserve facing while moving feet along
	# local velocity. Contact correction below retains planted world positions.
	var direction_angle:=atan2(stride_direction.x,stride_direction.y) if stride_direction.length()>.01 else 0.0
	if aim_weight>.05 and movement_speed>.12:
		var hip_twist:=Quaternion(Vector3.UP,clampf(direction_angle,-.7,.7)*aim_weight*.3)
		for side in ["L","R"]:
			var index:=rig.find_bone("pelvis."+side)
			pose.rotations[index]=(pose.rotations[index]*hip_twist).normalized()
	if aim_weight>.001: _mix_pose(pose,_sample("aim",phase),aim_weight)
	if not action.is_empty() and action_blend>0:
		var pair: Array=ACTIONS[action]
		var clip: String=pair[1] if action_stage in ["recovery","fade"] else pair[0]
		if warm_bow and action=="kodanda" and action_stage in ["windup","hold"]: clip="ready_draw"
		var p:=clampf(action_elapsed/(recovery if action_stage in ["recovery","fade"] else windup),0,1)
		if action_stage=="fade": p=1
		var action_pose:=_sample(clip,p)
		if cancelled_pose and action_stage=="fade": action_pose={"positions":cancel_positions.duplicate(),"rotations":cancel_rotations.duplicate()}
		# Every new attack begins from the last evaluated pose, including rapid
		# release-to-draw retriggers, instead of snapping back to a rest key.
		if (action_stage=="windup" or (action_stage=="recovery" and bool(pair[2]))) and action_elapsed<.10 and not action_from_positions.is_empty():
			var previous:={"positions":action_from_positions.duplicate(),"rotations":action_from_rotations.duplicate()}
			_mix_pose(previous,action_pose,_smooth(action_elapsed/.10),true)
			action_pose=previous
		var planted_action:=action in ["piercing_dawn","guardian_circle","dawn_volley"] and grounded and traversal=="ground" and movement_speed<.12
		_mix_pose(pose,action_pose,action_blend,bool(pair[2]) or planted_action)
	if transition_age<transition_duration and not transition_positions.is_empty():
		var transition:={"positions":transition_positions.duplicate(),"rotations":transition_rotations.duplicate()}
		_mix_pose(transition,pose,_smooth(transition_age/transition_duration),true)
		pose=transition
	finite=true
	for index in rest_positions.size():
		if not pose.positions[index].is_finite() or not pose.rotations[index].is_finite():
			finite=false; continue
		rig.set_bone_pose_position(index,pose.positions[index])
		rig.set_bone_pose_rotation(index,pose.rotations[index])
	var aim_bone:=rig.find_bone("spine03")
	var before_aim:=rig.get_bone_pose_rotation(aim_bone)
	_apply_aim()
	if locomotion in ["walk","run","sprint"] and absf(direction_angle)>.15:
		var lateral:=absf(sin(direction_angle))
		var lateral_blend:=lateral*lateral
		var direction_blend:=_smooth(transition_age/transition_duration)
		# Sidesteps use a low-clearance shuffle and short traveling support arc.
		# Rotating the full forward stride sideways crossed the legs and folded
		# the thigh-skinned front cloth through itself.
		for name_ in ["pelvis.L","pelvis.R","spine05"]:
			var index:=rig.find_bone(name_)
			var parent:=rig.get_bone_parent(index)
			var up:=rig.get_bone_global_pose(parent).basis.inverse()*Vector3(0,(.02 if locomotion=="walk" else .07)*lateral_blend*direction_blend,0)
			rig.set_bone_pose_position(index,rig.get_bone_pose_position(index)+up)
		for side in ["L","R"]:
			var index:=rig.find_bone("foot."+side)
			var point:=rig.get_bone_global_pose(index).origin
			var travel:=Basis(Vector3.UP,direction_angle)*Vector3(0,0,point.z)
			var x:=.19 if side=="L" else -.19
			var forward_target:=Vector3(x+travel.x,point.y,travel.z)
			var gait_phase:=fposmod(phase+(.5 if side=="R" else 0),1)
			var duty:=.29
			var reach:=1.6*duty*.5
			var offset:=lerpf(reach,-reach,gait_phase/duty)
			var clearance:=0.0
			if gait_phase>=duty:
				var swing:=(gait_phase-duty)/(1-duty)
				offset=lerpf(-reach,reach,_smooth(swing))
				clearance=sin(swing*PI)*.07
			var side_target:=Vector3((.24 if side=="L" else -.24)+stride_direction.x*offset,rest_globals[index].origin.y+clearance,0)
			_solve_leg(side,point.lerp(forward_target.lerp(side_target,lateral_blend),direction_blend))
	_apply_contact()
	# During hold, position the deforming string at the actual posed fingertips.
	# Release uses the authored returning string and preserves finger followthrough.
	if nocked and action_stage in ["windup","hold"]:
		var tension:=_smooth(clampf((action_elapsed/windup-.18)/.82,0,1))*action_blend
		var wrist:=rig.get_bone_global_pose(rig.find_bone("wrist.R"))
		var hand:=rig.get_bone_global_pose(rig.find_bone("wrist.L"))
		var target:=(wrist*rest_positions[rig.find_bone("bowstring")]).lerp(hand*STRING_CONTACT,tension)
		rig.set_bone_pose_position(rig.find_bone("bowstring"),wrist.affine_inverse()*target)
		if tension>.999: max_string_error=maxf(max_string_error,rig.get_bone_global_pose(rig.find_bone("bowstring")).origin.distance_to(hand*STRING_CONTACT))
	for index in rest_positions.size():
		last_positions[index]=rig.get_bone_pose_position(index)
		last_rotations[index]=rig.get_bone_pose_rotation(index)
		last_globals[index]=rig.get_bone_global_pose(index)
	# Blends operate before aim. Socket/render caches retain the final posed
	# transform; feeding those rotations back would apply pitch/yaw twice.
	blend_positions=last_positions.duplicate()
	blend_rotations=last_rotations.duplicate()
	blend_rotations[aim_bone]=before_aim
	_update_arrow()
	modified_samples+=1

func _process_modification() -> void: evaluate_pose()

func _make_arrow() -> void:
	nocked_arrow=Node3D.new()
	nocked_arrow.name="NockedArrow"
	rig.add_child(nocked_arrow)
	var wood:=StandardMaterial3D.new()
	wood.albedo_color=Color(.34,.19,.07); wood.roughness=.6
	var metal:=StandardMaterial3D.new()
	metal.albedo_color=Color(.78,.71,.45); metal.metallic=.8; metal.roughness=.32
	var shaft:=MeshInstance3D.new()
	var cylinder:=CylinderMesh.new()
	cylinder.top_radius=.003; cylinder.bottom_radius=.003; cylinder.height=.72
	cylinder.radial_segments=6; cylinder.rings=1
	shaft.mesh=cylinder; shaft.material_override=wood; shaft.position.y=.36
	nocked_arrow.add_child(shaft)
	var tip:=MeshInstance3D.new()
	var cone:=CylinderMesh.new()
	cone.top_radius=0; cone.bottom_radius=.012; cone.height=.065
	cone.radial_segments=4; cone.rings=1
	tip.mesh=cone; tip.material_override=metal; tip.position.y=.7525
	nocked_arrow.add_child(tip)
	nocked_arrow.visible=false

func _update_arrow() -> void:
	if not is_instance_valid(nocked_arrow): return
	nocked_arrow.visible=nocked
	if not nocked: return
	var start:=socket_global("string_nock").origin
	var target:=socket_global("bow_grip").origin
	var y:=(target-start).normalized()
	if y.length_squared()<.1: return
	var x:=Vector3.UP.cross(y).normalized()
	if x.length_squared()<.1: x=Vector3.RIGHT
	var z:=x.cross(y).normalized()
	nocked_arrow.global_transform=Transform3D(Basis(x,y,z),start)

func socket_global(socket_name: String) -> Transform3D:
	if not configured: return Transform3D.IDENTITY
	var bone_name:="wrist.R"
	var offset:=GRIP_CENTER
	if socket_name=="string_nock": bone_name="bowstring"; offset=Vector3.ZERO
	elif socket_name=="draw_hand": bone_name="wrist.L"; offset=STRING_CONTACT
	elif socket_name=="arrow_muzzle": offset=GRIP_CENTER+Vector3(0,.055,0)
	elif socket_name=="head": bone_name="head"; offset=Vector3(0,.10,0)
	var tr:=rig.global_transform*last_globals[rig.find_bone(bone_name)]
	tr.origin=tr*offset
	return tr

func diagnostics() -> Dictionary:
	return {"configured":configured,"locomotion":locomotion,"phase":phase,"action":action,"stage":action_stage,"action_elapsed":action_elapsed,"windup":windup,"recovery":recovery,"aim_weight":aim_weight,"nocked":nocked,"release_count":release_count,"cancel_count":cancel_count,"rejected_states":rejected_states,"finite":finite,"modified_samples":modified_samples,"foot_locks":foot_locks.duplicate(),"contact_modes":contact_modes.duplicate(),"plant_ids":plant_ids.duplicate(),"max_contact_error_m":max_contact_error,"max_string_error_m":max_string_error,"last_reason":last_reason,"clip_count":library.get_animation_list().size() if library else 0,"scope":"Original full-body clips with layered authority-driven actions and support-foot IK; continuous rendered review remains separate."}
