extends SceneTree
## Actual imported-rig differential evidence; no rendered-motion acceptance.
const HERO := "res://assets/heroes/rama-hero.glb"
var baseline_path := "/workspace/ANDOLAN/scratch/graphics-six/G1/motion/rama_motion.baseline.gd"
var candidate_path := "res://scripts/rama_motion.gd"
var report_path := "/tmp/graphics-g1-motion.json"
var checks: Array[Dictionary] = []
var trials: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--baseline-script="): baseline_path=arg.trim_prefix("--baseline-script=")
		elif arg.begins_with("--candidate-script="): candidate_path=arg.trim_prefix("--candidate-script=")
	call_deferred("run")

func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found:=find_node(child,kind)
		if found: return found
	return null

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func points(motion: Node) -> Array[Vector3]:
	var result: Array[Vector3] = []
	for transform in motion.last_globals: result.append(transform.origin)
	return result

func difference(a: Array[Vector3], b: Array[Vector3], motion: Node, upper_only := false) -> Dictionary:
	var result:={"distance_m":0.0,"bone":"","from":Vector3.ZERO,"to":Vector3.ZERO}
	for index in a.size():
		var name_: String=motion.rig.get_bone_name(index)
		# The string is intentionally reattached when a new nocked arrow appears.
		# Its separate existing hand/string-contact suite remains required.
		if name_=="bowstring" or (upper_only and not motion.upper[index]): continue
		var distance:=a[index].distance_to(b[index])
		if distance>result.distance_m: result={"distance_m":distance,"bone":name_,"from":a[index],"to":b[index]}
	return result

func clock(motion: Node) -> Dictionary:
	return {"action":motion.action,"stage":motion.action_stage,"age":motion.action_elapsed,"phase":motion.phase,"locomotion_age":motion.locomotion_age,"release_count":motion.release_count,"cancel_count":motion.cancel_count,"nocked":motion.nocked,"fade":motion.action_fade}

func execute(script: Script, name_: String, hz: int) -> Dictionary:
	var model: Node3D=load(HERO).instantiate()
	root.add_child(model)
	var motion=script.new()
	var configured: bool=motion.configure(model,find_node(model,"AnimationPlayer"))
	assert(configured)
	var dt:=1.0/hz
	var state:={"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"grounded":true,"floor_y":0.0,"aiming":name_=="aimed_cold","aim_pitch":-.45,"aim_yaw":.6}
	if name_=="cold_volley_minus": state.aim_pitch=.45; state.aim_yaw=-.6
	for frame in hz:
		motion.update_motion(dt,state); motion.evaluate_pose()
	var ability:="piercing_dawn"
	if name_=="cold_volley_minus": ability="dawn_volley"
	elif name_ in ["cold_kodanda_plus","warm_retrigger"]: ability="kodanda"
	var duration:=.18 if ability=="kodanda" else .65
	if name_=="warm_retrigger":
		assert(motion.request_action(ability,duration,.22))
		for frame in int(ceil(duration*hz))+1:
			motion.update_motion(dt,state);motion.evaluate_pose()
		assert(motion.release_action(ability))
		motion.update_motion(dt,state);motion.evaluate_pose()
	var before:=points(motion)
	var before_clock:=clock(motion)
	var accepted:=true
	if name_!="locomotion_control": accepted=motion.request_action(ability,duration,.22)
	motion.evaluate_pose()
	var entry:=difference(before,points(motion),motion)
	var previous:=points(motion)
	var maximum:=entry.duplicate()
	var cancel_boundary:={"distance_m":0.0}
	var retrigger_boundary:={"distance_m":0.0}
	var rows: Array[Dictionary]=[]
	var poses: Array= []
	var frozen:=true
	var finite:=true
	for frame in int(hz*1.2):
		if name_=="locomotion_control":
			var options:=[Vector3(0,0,2),Vector3(0,0,6),Vector3(0,0,-6),Vector3(6,0,0),Vector3(-6,0,0),Vector3.ZERO]
			state.velocity=options[mini(5,int(float(frame)/hz*5))];state.local_velocity=state.velocity;state.aiming=true
			model.position+=Vector3(state.velocity)*dt
		if name_ in ["early_cancel","cancel_retrigger"] and frame==maxi(1,int(hz*.033)):
			before=points(motion);motion.cancel_action("G1 early cancellation");motion.evaluate_pose()
			cancel_boundary=difference(before,points(motion),motion)
			if name_=="cancel_retrigger":
				before=points(motion);accepted=accepted and motion.request_action("kodanda",.18,.22);motion.evaluate_pose()
				retrigger_boundary=difference(before,points(motion),motion)
		if name_ not in ["early_cancel","locomotion_control"] and frame==int(hz*.9):
			accepted=accepted and motion.release_action(motion.action)
			accepted=accepted and not motion.release_action(motion.action)
		var delta:=.08 if name_=="hitch" and frame==1 else dt
		finite=motion.update_motion(delta,state) and finite
		motion.evaluate_pose()
		var current:=points(motion)
		var step:=difference(previous,current,motion)
		if float(step.distance_m)>float(maximum.distance_m):maximum=step.duplicate();maximum.frame=frame
		previous=current
		for transform in motion.last_globals:finite=finite and transform.origin.is_finite() and transform.basis.is_finite()
		if frame==maxi(1,int(hz*.05)):
			var frozen_clock:=clock(motion)
			var frozen_pose:=points(motion)
			for repeat in 12:motion.evaluate_pose()
			frozen=frozen and clock(motion)==frozen_clock and float(difference(frozen_pose,points(motion),motion).distance_m)<.00001
		var feet:={}
		for side in ["L","R"]:
			feet[side]={"point":motion.last_globals[motion.rig.find_bone("foot."+side)].origin,"target":motion.foot_targets[side],"locked":motion.foot_locks[side]}
		rows.append({"frame":frame,"clock":clock(motion),"feet":feet,"delta":delta})
		poses.append(current)
	var pre_reset: int=motion.release_count
	motion.cancel("G1 reset");motion.evaluate_pose()
	var reset_ok: bool=motion.action=="" and motion.action_stage=="none" and motion.locomotion_age==0 and motion.release_count==pre_reset and not motion.nocked
	var result:={"name":name_,"hz":hz,"configured":configured,"accepted":accepted,"finite":finite,"entry":entry,"maximum_step":maximum,"cancel_boundary":cancel_boundary,"retrigger_boundary":retrigger_boundary,"freeze":frozen,"reset":reset_ok,"before_clock":before_clock,"rows":rows,"poses":poses}
	model.free()
	return result

func run() -> void:
	var baseline: Script=load(baseline_path)
	var candidate: Script=load(candidate_path)
	var timing_exact:=true
	var feet_exact:=true
	var control_exact:=true
	var improved:=true
	var boundary_ok:=true
	var lifecycle_ok:=true
	var warm_ok:=true
	for hz in [30,60,120]:
		for name_ in ["cold_piercing_plus","cold_volley_minus","cold_kodanda_plus","early_cancel","cancel_retrigger","warm_retrigger","aimed_cold","hitch","locomotion_control"]:
			var a:=execute(baseline,name_,hz)
			var b:=execute(candidate,name_,hz)
			var maximum_foot_difference:=0.0
			var maximum_control_difference:=0.0
			for index in a.rows.size():
				timing_exact=timing_exact and a.rows[index].clock==b.rows[index].clock
				for side in ["L","R"]:
					var af: Dictionary=a.rows[index].feet[side];var bf: Dictionary=b.rows[index].feet[side]
					maximum_foot_difference=maxf(maximum_foot_difference,Vector3(af.point).distance_to(bf.point))
					feet_exact=feet_exact and af.locked==bf.locked and Vector3(af.target).distance_to(bf.target)<.00001
				if name_=="locomotion_control":
					for bone in a.poses[index].size():maximum_control_difference=maxf(maximum_control_difference,a.poses[index][bone].distance_to(b.poses[index][bone]))
			feet_exact=feet_exact and maximum_foot_difference<.00001
			control_exact=control_exact and maximum_control_difference<.00001
			if name_.begins_with("cold_"):
				improved=improved and float(a.entry.distance_m)>.02 and float(b.entry.distance_m)<.00001 and float(b.maximum_step.distance_m)<float(a.maximum_step.distance_m)
			if name_ in ["early_cancel","cancel_retrigger"]:boundary_ok=boundary_ok and float(b.cancel_boundary.distance_m)<.00001 and float(b.retrigger_boundary.distance_m)<.00001
			if name_=="warm_retrigger":warm_ok=warm_ok and float(b.entry.distance_m)<=float(a.entry.distance_m)+.00001
			lifecycle_ok=lifecycle_ok and b.configured and b.accepted and b.finite and b.freeze and b.reset
			a.erase("poses");b.erase("poses")
			trials.append({"name":name_,"hz":hz,"baseline":a,"candidate":b,"maximum_foot_difference_m":maximum_foot_difference,"maximum_control_difference_m":maximum_control_difference})
	check("cold bow shoulder entry and maximum joint steps improve at30/60/120",improved)
	check("early cancel and retrigger preserve same-time body-joint boundaries",boundary_ok)
	check("warm draw retrigger does not add a boundary step",warm_ok)
	check("existing action/release/cancel/gait clocks are exactly equal",timing_exact)
	check("feet anchors locks and endpoints remain equal",feet_exact)
	check("no-action direction/gait control poses remain equal",control_exact)
	check("valid hitch pause reevaluation and reset remain finite and bounded",lifecycle_ok)
	var pins:={}
	for path in [baseline_path,candidate_path,HERO,HERO+".import","res://assets/animations/rama_hero_motion.tres","res://tests/graphics_g1_motion_cases.gd"]:pins[path]=FileAccess.get_sha256(path)
	var imported:=ConfigFile.new()
	if imported.load(HERO+".import")==OK:
		for path in imported.get_value("deps","dest_files",[]):pins[path]=FileAccess.get_sha256(path)
	var passed:=true
	for item in checks:passed=passed and item.passed
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"trials":trials,"source_sha256":pins,"godot":Engine.get_version_info(),"scope":"Actual imported164-bone rig, same-time body-joint entry/cancel and differential30/60/120 manual presentation updates. String reattachment excluded from body-step metric; existing string/contact suite remains separate. No authoritative kit, actual tree pause, rendering or motion-quality acceptance."}
	DirAccess.make_dir_recursive_absolute(report_path.get_base_dir())
	var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t")+"\n");file.close()
	quit(0 if passed else 1)
