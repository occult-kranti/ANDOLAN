extends SceneTree
## Actual imported-rig checks for bounded gait hysteresis. Optional historical
## script comparison demonstrates the original transition/contact starvation.
const MOTION := preload("res://scripts/rama_motion.gd")
const HERO := "res://assets/heroes/rama-hero.glb"
var checks: Array[Dictionary] = []
var report_path := "/tmp/rama-motion-polish.json"
var baseline_script := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--baseline-script="): baseline_script=arg.trim_prefix("--baseline-script=")
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

func create(script: Script=MOTION) -> Array:
	var model: Node3D=load(HERO).instantiate()
	root.add_child(model)
	var motion=script.new()
	var configured: bool=motion.configure(model,find_node(model,"AnimationPlayer"))
	return [model,motion,configured]

func tick(model: Node3D, motion: Node, delta: float, state: Dictionary) -> void:
	model.position+=Vector3(state.get("velocity",Vector3.ZERO))*delta
	motion.update_motion(delta,state)
	motion.evaluate_pose()

func jitter(fixture: Array, boundary: float, start_speed: float, hz:=60.0) -> Dictionary:
	var model: Node3D=fixture[0]
	var motion=fixture[1]
	model.position=Vector3.ZERO
	motion.cancel()
	for frame in int(hz*.5): tick(model,motion,1/hz,{"velocity":Vector3(0,0,start_speed),"floor_y":0.0})
	var previous: String=motion.locomotion
	var switches:=0
	var support_frames:=0
	var settled_frames:=0
	var all_finite:=true
	var input_unchanged:=true
	var rows: Array[Dictionary]=[]
	motion.max_contact_error=0.0
	for frame in int(hz*2):
		var speed:=boundary+(.04 if frame%2==0 else -.04)
		var velocity:=Vector3(0,0,speed)
		tick(model,motion,1/hz,{"velocity":velocity,"floor_y":0.0})
		if motion.locomotion!=previous: switches+=1
		previous=motion.locomotion
		if motion.foot_locks.L or motion.foot_locks.R: support_frames+=1
		if motion.transition_age>=motion.transition_duration: settled_frames+=1
		all_finite=all_finite and motion.finite
		input_unchanged=input_unchanged and motion.world_velocity==velocity and motion.local_velocity==velocity and is_equal_approx(motion.movement_speed,speed)
		var left: Vector3=motion.last_globals[motion.rig.find_bone("foot.L")].origin
		var right: Vector3=motion.last_globals[motion.rig.find_bone("foot.R")].origin
		rows.append({"frame":frame,"gait":motion.locomotion,"phase":motion.phase,"transition_age":motion.transition_age,"support":motion.foot_locks.duplicate(),"foot_local_m":{"L":[left.x,left.y,left.z],"R":[right.x,right.y,right.z]}})
	return {"boundary_mps":boundary,"initial_speed_mps":start_speed,"hz":hz,"frames":rows.size(),"gait_switches":switches,"support_frames":support_frames,"settled_frames":settled_frames,"finite":all_finite,"velocity_unchanged":input_unchanged,"maximum_contact_error_m":motion.max_contact_error,"pose_samples":rows}

func run() -> void:
	check("run acceleration starts at its original threshold",MOTION.ground_gait(2.99,"walk")=="walk" and MOTION.ground_gait(3.0,"walk")=="walk" and MOTION.ground_gait(3.001,"walk")=="run")
	check("run retains authored gait within the walk exit band",MOTION.ground_gait(2.96,"run")=="run" and MOTION.ground_gait(2.8,"run")=="run" and MOTION.ground_gait(2.799,"run")=="walk")
	check("sprint acceleration starts at its original threshold",MOTION.ground_gait(6.99,"run")=="run" and MOTION.ground_gait(7.0,"run")=="run" and MOTION.ground_gait(7.001,"run")=="sprint")
	check("sprint retains authored gait within the run exit band",MOTION.ground_gait(6.96,"sprint")=="sprint" and MOTION.ground_gait(6.75,"sprint")=="sprint" and MOTION.ground_gait(6.749,"sprint")=="run")
	check("start and landing select the original appropriate gait",MOTION.ground_gait(3.01,"idle")=="run" and MOTION.ground_gait(7.01,"land")=="sprint" and MOTION.ground_gait(2.99,"flight")=="walk")
	check("large speed changes bypass intermediate gaits",MOTION.ground_gait(9,"walk")=="sprint" and MOTION.ground_gait(1,"sprint")=="walk")
	check("stop remains immediate in every gait",MOTION.ground_gait(0,"sprint")=="idle" and MOTION.ground_gait(.12,"run")=="idle" and MOTION.ground_gait(.121,"walk")=="walk")
	var fixture:=create()
	check("unchanged actual 164-bone hero and animation library configure",fixture[2] and fixture[1].rig.get_bone_count()==164 and fixture[1].library.get_animation_list().size()==23)
	if not fixture[2]:
		fixture[0].free()
		finish([])
		return
	var model: Node3D=fixture[0]
	var motion=fixture[1]
	tick(model,motion,1.0/60,{"velocity":Vector3(0,0,6)})
	tick(model,motion,1.0/60,{"velocity":Vector3(0,0,2.8)})
	var at_exit: bool=motion.locomotion=="run"
	tick(model,motion,1.0/60,{"velocity":Vector3(0,0,2.799)})
	check("actual float32 speed retains the inclusive downshift boundary",at_exit and motion.locomotion=="walk")
	var trials: Array[Dictionary]=[]
	for params in [[3.0,2.9],[3.0,3.1],[7.0,6.9],[7.0,7.1]]:
		var result:=jitter(fixture,params[0],params[1])
		trials.append(result)
		check("actual gait settles and supports feet at %s m/s from %s"%[params[0],params[1]],result.gait_switches<=1 and result.support_frames>20 and result.settled_frames>=result.frames-10 and result.finite and result.maximum_contact_error_m<.002,{"gait_switches":result.gait_switches,"support_frames":result.support_frames,"frames":result.frames,"maximum_contact_error_m":result.maximum_contact_error_m})
	var velocity_ok:=true
	for result in trials: velocity_ok=velocity_ok and result.velocity_unchanged
	check("presentation preserves every input velocity and movement speed",velocity_ok)
	var clocks: Array[Dictionary]=[]
	for hz in [30.0,60.0,120.0]:
		model.position=Vector3.ZERO; motion.cancel()
		for frame in int(hz): tick(model,motion,1/hz,{"velocity":Vector3(0,0,6),"floor_y":0.0})
		clocks.append({"hz":hz,"phase":motion.phase,"gait":motion.locomotion,"position_z":model.position.z})
	check("unchanged distance phase matches 30 60 and 120 Hz",absf(clocks[0].phase-clocks[2].phase)<.00001 and absf(clocks[0].position_z-clocks[2].position_z)<.00001 and clocks[0].gait==clocks[2].gait,{"samples":clocks})
	var stable_clocks:=true
	for hz in [30.0,120.0]:
		var result:=jitter(fixture,3.0,2.9,hz)
		stable_clocks=stable_clocks and result.gait_switches<=1 and result.support_frames>0 and result.finite
	check("threshold jitter remains stable across simulation clocks",stable_clocks)
	motion.cancel(); model.position=Vector3.ZERO
	tick(model,motion,1.0/60,{"velocity":Vector3(0,0,2.9)})
	var requested: bool=motion.request_action("kodanda",.18,.22)
	for frame in 60: tick(model,motion,1.0/60,{"velocity":Vector3(0,0,3.0+(.04 if frame%2==0 else -.04)),"floor_y":0.0})
	check("gait smoothing cannot synthesize combat release",requested and motion.action_stage=="hold" and motion.release_count==0 and motion.nocked and is_equal_approx(motion.windup,.18) and is_equal_approx(motion.recovery,.22))
	var string_error: float=motion.socket_global("string_nock").origin.distance_to(motion.socket_global("draw_hand").origin)
	check("held draw preserves exact posed string contact",string_error<.0001,{"error_m":string_error})
	var released: bool=motion.release_action("kodanda")
	var duplicate: bool=motion.release_action("kodanda")
	for frame in 10: tick(model,motion,1.0/60,{"velocity":Vector3(0,0,3)})
	var recovery_active: bool=motion.action_stage=="recovery"
	for frame in 4: tick(model,motion,1.0/60,{"velocity":Vector3(0,0,3)})
	check("authoritative release and recovery times remain unchanged",released and not duplicate and recovery_active and motion.action_stage=="fade" and motion.release_count==1 and not motion.nocked)
	motion.cancel_action("polish cancellation probe")
	for frame in 12: tick(model,motion,1.0/60,{"velocity":Vector3(0,0,3)})
	check("cancellation finishes without stale nock or combat event",motion.action_stage=="none" and not motion.nocked and motion.release_count==1 and motion.finite)
	var traversal_ok:=true
	for state in [{"velocity":Vector3(0,0,3),"grounded":false,"traversal":"flight"},{"velocity":Vector3(0,0,7),"grounded":false,"traversal":"grapple"},{"velocity":Vector3(0,5,3),"grounded":false},{"velocity":Vector3(0,-5,7),"grounded":false},{"velocity":Vector3(0,0,6),"grounded":true}]:
		tick(model,motion,1.0/60,state)
		traversal_ok=traversal_ok and motion.finite and motion.locomotion in ["flight","grapple","jump","fall","land"]
	check("air traversal and landing bypass ground gait hysteresis",traversal_ok)
	motion.cancel(); tick(model,motion,1.0/60,{})
	check("reset clears gait history and invalid input remains rejected",motion.locomotion=="idle" and not motion.update_motion(NAN,{}) and motion.action_stage=="none")
	if not baseline_script.is_empty():
		var baseline_resource=load(baseline_script)
		check("historical comparison script loads",baseline_resource is Script)
		if baseline_resource is Script:
			var baseline:=create(baseline_resource)
			check("historical comparison configures the same actual rig",baseline[2])
			if baseline[2]:
				for boundary in [3.0,7.0]:
					var old:=jitter(baseline,boundary,boundary-.1)
					var improved:=jitter(fixture,boundary,boundary-.1)
					trials.append({"baseline":old,"candidate":improved})
					check("actual %s m/s pose comparison restores support instead of restarting each frame"%boundary,old.gait_switches==old.frames and old.support_frames==0 and old.settled_frames==0 and improved.gait_switches==1 and improved.support_frames>20,{"baseline_switches":old.gait_switches,"candidate_switches":improved.gait_switches,"baseline_support_frames":old.support_frames,"candidate_support_frames":improved.support_frames})
			baseline[0].free()
	model.free()
	finish(trials)

func finish(trials: Array) -> void:
	var passed:=true
	for row in checks: passed=passed and row.passed
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"pose_trials":trials,"source_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"test_sha256":FileAccess.get_sha256("res://tests/rama_motion_polish_cases.gd"),"hero_sha256":FileAccess.get_sha256(HERO),"library_sha256":FileAccess.get_sha256(MOTION.LIBRARY_PATH),"scope":"Actual imported 164-bone numerical pose/contact and authority tests. Continuous render and human feel remain separate."}
	if not baseline_script.is_empty(): report.baseline_script_sha256=FileAccess.get_sha256(baseline_script)
	var output:=FileAccess.open(report_path,FileAccess.WRITE)
	if output==null:
		push_error("Cannot write motion polish report: "+report_path)
		quit(2)
		return
	output.store_string(JSON.stringify(report,"  ")+"\n")
	quit(0 if passed else 1)
