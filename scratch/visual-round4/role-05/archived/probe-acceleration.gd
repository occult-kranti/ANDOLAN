extends SceneTree
## Independent differential review of presentation timing on the actual rig.
## Headless pose/contact evidence only; no rendered or human-feel acceptance.
var MOTION: Script
var candidate_path := ""
const HERO := "res://assets/heroes/rama-hero.glb"
var report_path := "/tmp/rama-motion-adversarial.json"
var baseline_path := ""
var checks: Array[Dictionary] = []
var trials: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--baseline-script="): baseline_path=arg.trim_prefix("--baseline-script=")
		elif arg.begins_with("--candidate-script="): candidate_path=arg.trim_prefix("--candidate-script=")
	MOTION=load(candidate_path)
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found:=find_node(child,kind)
		if found: return found
	return null

func scenario_state(name_: String, frame: int, hz: float) -> Dictionary:
	var t:=float(frame)/hz
	var state:={"velocity":Vector3.ZERO,"floor_y":0.0,"grounded":true}
	if name_=="start_stop":
		var speed:=0.0
		if t>=.2 and t<.4: speed=2.0
		elif t>=.4 and t<.6: speed=9.0
		elif t>=.6 and t<.8: speed=6.0
		elif t>=.8 and t<1.0: speed=2.0
		elif t>=1.2: speed=9.0
		state.velocity=Vector3(0,0,speed)
	elif name_=="traversal":
		state.velocity=Vector3(0,0,9)
		if t<.2:
			state.traversal="flight"; state.grounded=false
		elif t<.4:
			state.traversal="grapple"; state.grounded=false
		elif t<.6:
			state.velocity=Vector3(0,5,6); state.grounded=false
		elif t<.8:
			state.velocity=Vector3(0,-5,6); state.grounded=false
	elif name_ in ["reversal","accelerated_reversal"]:
		var choices:=[Vector3(0,0,6),Vector3(0,0,-6),Vector3(6,0,0),Vector3(-6,0,0)]
		state.velocity=choices[(frame/int(hz*(.4 if name_=="accelerated_reversal" else .2)))%choices.size()]
		state.aiming=true; state.aim_yaw=.2; state.aim_pitch=.15
	elif name_=="action_cancel":
		state.velocity=Vector3(0,0,6)
		state.aiming=true
	elif name_.begins_with("jitter_"):
		var boundary:=3.0 if name_=="jitter_3" else 7.0
		var speed:=boundary-.1 if t<.5 else boundary+(.04 if frame%2==0 else -.04)
		state.velocity=Vector3(0,0,speed)
	elif name_=="brake_band":
		var speed:=9.0 if t<.3 else (6.75 if t<.6 else (6.749 if t<.9 else (2.8 if t<1.2 else 2.799)))
		state.velocity=Vector3(0,0,speed)
	return state

func execute(script: Script, name_: String, hz: float) -> Dictionary:
	var model: Node3D=load(HERO).instantiate()
	root.add_child(model)
	var motion=script.new()
	var configured: bool=motion.configure(model,find_node(model,"AnimationPlayer"))
	if not configured:
		motion.free(); model.free()
		return {"configured":false,"name":name_,"hz":hz,"rows":[]}
	var rows: Array[Dictionary]=[]
	var integrated_velocity:=Vector3.ZERO
	var previous_targets:={}
	var maximum_anchor_drift:=0.0
	var total_anchor_drift:=0.0
	var finite:=true
	var input_exact:=true
	var maximum_joint_step:=0.0
	var maximum_joint_step_detail:={}
	var maximum_support_error:=0.0
	var support_frames:=0
	var switches:=0
	var previous_gait: String=motion.locomotion
	var previous_positions: Array[Vector3]=[]
	var semantic_ok:=true
	var request_ok:=true
	var duration:=2.5 if name_.begins_with("jitter_") else 1.6
	for frame in int(hz*duration):
		var state:=scenario_state(name_,frame,hz)
		if name_=="accelerated_reversal":
			integrated_velocity.x=move_toward(integrated_velocity.x,Vector3(state.velocity).x,38.0/hz)
			integrated_velocity.z=move_toward(integrated_velocity.z,Vector3(state.velocity).z,38.0/hz)
			state.velocity=integrated_velocity
		if name_=="action_cancel":
			if frame==int(hz*.2): request_ok=request_ok and motion.request_action("kodanda",.18,.22)
			if frame==int(hz*.3): motion.cancel_action("independent windup interruption")
			if frame==int(hz*.5): request_ok=request_ok and motion.request_action("piercing_dawn",.18,.22)
			if frame==int(hz*.9):
				request_ok=request_ok and motion.release_action("piercing_dawn")
				request_ok=request_ok and not motion.release_action("piercing_dawn")
		model.position+=Vector3(state.velocity)/hz
		var updated: bool=motion.update_motion(1.0/hz,state)
		motion.evaluate_pose()
		finite=finite and updated and motion.finite
		input_exact=input_exact and motion.world_velocity==state.velocity and motion.local_velocity==state.velocity
		var positions: Array[Vector3]=[]
		for transform in motion.last_globals:
			finite=finite and transform.origin.is_finite() and transform.basis.is_finite()
			positions.append(transform.origin)
		if not previous_positions.is_empty():
			for index in positions.size():
				var step: float=positions[index].distance_to(previous_positions[index])
				if step>maximum_joint_step:
					maximum_joint_step=step
					maximum_joint_step_detail={"bone":motion.rig.get_bone_name(index),"frame":frame,"t":float(frame+1)/hz,"from":str(previous_positions[index]),"to":str(positions[index])}
		previous_positions=positions
		if name_=="start_stop":
			var expected:="idle"
			var speed: float=Vector3(state.velocity).length()
			if speed==2.0: expected="walk"
			elif speed==6.0: expected="run"
			elif speed==9.0: expected="sprint"
			semantic_ok=semantic_ok and motion.locomotion==expected
		elif name_ in ["reversal","accelerated_reversal"]: semantic_ok=semantic_ok and motion.locomotion=="run"
		elif name_=="action_cancel":
			if frame>=int(hz*.3) and frame<int(hz*.5): semantic_ok=semantic_ok and not motion.nocked and motion.release_count==0
			if frame>=int(hz*.7) and frame<int(hz*.9): semantic_ok=semantic_ok and motion.action_stage=="hold" and motion.release_count==0
			if frame>=int(hz*.9): semantic_ok=semantic_ok and not motion.nocked and motion.release_count==1
		var measured:=not name_.begins_with("jitter_") or frame>=int(hz*.5)
		if measured:
			if motion.locomotion!=previous_gait: switches+=1
			if motion.foot_locks.L or motion.foot_locks.R: support_frames+=1
		previous_gait=motion.locomotion
		var feet:={}
		var contact_errors:={}
		var contact_failures:={}
		var anchor_drift:={} 
		for side in ["L","R"]:
			var point: Vector3=motion.rig.global_transform*motion.last_globals[motion.rig.find_bone("foot."+side)].origin
			feet[side]=[point.x,point.y,point.z]
			if motion.foot_locks[side]:
				if previous_targets.has(side):
					var drift: float=motion.foot_targets[side].distance_to(previous_targets[side])
					maximum_anchor_drift=maxf(maximum_anchor_drift,drift)
					total_anchor_drift+=drift
					anchor_drift[side]=drift
				previous_targets[side]=motion.foot_targets[side]
				var error:=point.distance_to(motion.foot_targets[side])
				contact_errors[side]=error
				maximum_support_error=maxf(maximum_support_error,error)
				if error>=.002:
					var hip: Vector3=motion.last_globals[motion.rig.find_bone("upperleg01."+side)].origin
					var target: Vector3=motion.rig.global_transform.affine_inverse()*motion.foot_targets[side]
					var solver_reach:=0.0
					for segment in ["upperleg02.","lowerleg01.","lowerleg02.","foot."]:
						solver_reach+=Vector3(motion.rest_positions[motion.rig.find_bone(segment+side)]).length()
					solver_reach-=.004
					contact_failures[side]={"target_world_m":[motion.foot_targets[side].x,motion.foot_targets[side].y,motion.foot_targets[side].z],"post_compression_hip_target_distance_m":hip.distance_to(target),"solver_maximum_reach_m":solver_reach,"unreachable_distance_m":maxf(0,hip.distance_to(target)-solver_reach)}
			if not motion.foot_locks[side]: previous_targets.erase(side)
		rows.append({"frame":frame,"t":float(frame+1)/hz,"gait":motion.locomotion,"phase":motion.phase,"transition_age":motion.transition_age,"action":motion.action,"stage":motion.action_stage,"elapsed":motion.action_elapsed,"nocked":motion.nocked,"releases":motion.release_count,"support":motion.foot_locks.duplicate(),"feet_world_m":feet,"support_error_m":contact_errors,"anchor_drift_m":anchor_drift,"contact_failures":contact_failures,"positions":positions})
	var result:={"configured":true,"name":name_,"hz":hz,"rows":rows,"finite":finite,"input_exact":input_exact,"semantic_ok":semantic_ok,"requests_ok":request_ok,"support_frames":support_frames,"gait_switches":switches,"maximum_joint_step_m":maximum_joint_step,"maximum_joint_step_detail":maximum_joint_step_detail,"maximum_support_error_m":maximum_support_error,"maximum_anchor_drift_per_frame_m":maximum_anchor_drift,"total_anchor_drift_m":total_anchor_drift}
	model.free()
	return result

func compare(candidate: Dictionary, baseline: Dictionary) -> Dictionary:
	var clocks_equal: bool=candidate.rows.size()==baseline.rows.size()
	var maximum_position_difference:=0.0
	for index in mini(candidate.rows.size(),baseline.rows.size()):
		var a: Dictionary=candidate.rows[index]
		var b: Dictionary=baseline.rows[index]
		for key in ["gait","phase","transition_age","action","stage","elapsed","nocked","releases"]:
			clocks_equal=clocks_equal and a[key]==b[key]
		for bone in a.positions.size(): maximum_position_difference=maxf(maximum_position_difference,a.positions[bone].distance_to(b.positions[bone]))
	return {"event_clocks_exact":clocks_equal,"maximum_bone_position_difference_m":maximum_position_difference}

func compact(result: Dictionary) -> Dictionary:
	for row in result.rows: row.erase("positions")
	return result

func run() -> void:
	var baseline: Script=load(baseline_path)
	for hz in [30.0,60.0,120.0]:
		for name_ in ["accelerated_reversal","reversal"]:
			var candidate:=execute(MOTION,name_,hz)
			var old:=execute(baseline,name_,hz)
			var difference:=compare(candidate,old)
			check("%s %s Hz finite and velocity"%[name_,hz],candidate.finite and candidate.input_exact)
			check("%s %s Hz unchanged event clocks"%[name_,hz],difference.event_clocks_exact)
			trials.append({"candidate":compact(candidate),"baseline":compact(old),"comparison":difference})
	var passed:=true
	for row in checks: passed=passed and row.passed
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"trials":trials,"source_sha256":FileAccess.get_sha256(candidate_path),"baseline_sha256":FileAccess.get_sha256(baseline_path),"test_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Scratch-only measured actual-pose comparison; no art or continuous motion acceptance."}
	var output:=FileAccess.open(report_path,FileAccess.WRITE)
	output.store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if passed else 1)
