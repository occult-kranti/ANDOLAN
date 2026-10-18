extends "res://tests/graphics_g2_support_cases.gd"
## A frozen initial overview may have no presentation update before its draw.
func initial(script: Script) -> Dictionary:
	var body:=CharacterBody3D.new();root.add_child(body);body.position.y=.05
	var model: Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();body.add_child(model)
	var motion=script.new();assert(motion.configure(model,find_kind(model,"AnimationPlayer")));motion.active=false
	motion.evaluate_pose()
	var points:=[]
	for transform in motion.last_globals:points.append(transform.origin)
	var skin:=measure(motion,soles(model,motion.rig),0);skin.erase("positions")
	for repeat in 10:motion.evaluate_pose()
	var drift:=0.0
	for bone in points.size():drift=maxf(drift,Vector3(points[bone]).distance_to(motion.last_globals[bone].origin))
	var result:={"points":points,"skin":skin,"reevaluation_drift_m":drift,"locks":motion.foot_locks.duplicate()}
	body.free();return result
func run() -> void:
	var a:=initial(load(baseline_path));var b:=initial(load(candidate_path));var difference:=0.0
	for bone in a.points.size():difference=maxf(difference,Vector3(a.points[bone]).distance_to(b.points[bone]))
	a.erase("points");b.erase("points")
	check("pre-physics pose preserves baseline while waiting for safe plane query",difference<.00001,{"maximum_joint_origin_difference_m":difference,"baseline":a,"candidate":b})
	check("frozen pre-physics reevaluation stays stable",b.reevaluation_drift_m<.00001)
	var passed:=checks.all(func(x):return x.passed)
	var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"source_sha256":pins(),"fixture_sha256":FileAccess.get_sha256("res://tests/graphics_g2_initial_pose_cases.gd")},"\t")+"\n");file.close()
	quit(0 if passed else 1)
