extends "res://tests/graphics_g1_motion_cases.gd"
## Narrow adversary: cancelling an existing fade must not double its aim weight.
func probe(script: Script) -> Dictionary:
	var model: Node3D=load(HERO).instantiate()
	root.add_child(model)
	var motion=script.new()
	assert(motion.configure(model,find_node(model,"AnimationPlayer")))
	var state:={"grounded":true,"floor_y":0.0,"aiming":false,"aim_pitch":-.45,"aim_yaw":.6}
	for frame in 60:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	assert(motion.request_action("piercing_dawn",.65,.22))
	for frame in 2:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	motion.cancel_action("first")
	for frame in 2:motion.update_motion(1.0/60,state);motion.evaluate_pose()
	var before:=points(motion)
	var before_clock:=clock(motion)
	motion.cancel_action("repeated")
	motion.evaluate_pose()
	var result:={"boundary":difference(before,points(motion),motion),"upper_boundary":difference(before,points(motion),motion,true),"before_clock":before_clock,"after_clock":clock(motion)}
	model.free()
	return result

func run() -> void:
	var before:=source_pins()
	var a:=probe(load(baseline_path))
	var b:=probe(load(candidate_path))
	check("repeated cancel does not add an upper-body boundary",float(b.upper_boundary.distance_m)<=float(a.upper_boundary.distance_m)+.00001,{"baseline":a,"candidate":b})
	check("repeated cancel preserves clock/reset semantics",a.before_clock==b.before_clock and a.after_clock==b.after_clock)
	check("sources unchanged",source_pins()==before)
	var passed:=true
	for item in checks:passed=passed and item.passed
	var file:=FileAccess.open(report_path,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"source_sha256":before,"fixture_sha256":FileAccess.get_sha256("res://tests/graphics_g1_repeated_cancel_cases.gd")},"\t")+"\n");file.close()
	quit(0 if passed else 1)
