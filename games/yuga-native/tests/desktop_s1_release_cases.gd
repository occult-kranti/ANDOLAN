extends "res://tests/graphics_g1_motion_cases.gd"
## New S1 full-body release boundary; inherited helpers only, no G1 run.

func snapshot(motion: Node) -> Dictionary:
	var bones := []
	for index in motion.last_globals.size():
		var transform: Transform3D = motion.last_globals[index]
		var q := transform.basis.get_rotation_quaternion().normalized()
		bones.append({"name":motion.rig.get_bone_name(index),"position":[transform.origin.x,transform.origin.y,transform.origin.z],"rotation":[q.x,q.y,q.z,q.w]})
	return {"clock":clock(motion),"bones":bones,"locks":motion.foot_locks.duplicate(),"targets":motion.foot_targets.duplicate()}

func release_trial(script: Script, hz: int, condition: String) -> Dictionary:
	var model: Node3D = load(HERO).instantiate()
	root.add_child(model)
	var motion: Node = script.new()
	assert(motion.configure(model,find_node(model,"AnimationPlayer")))
	var dt := 1.0/hz
	var state := {"velocity":Vector3.ZERO,"local_velocity":Vector3.ZERO,"grounded":true,"floor_y":0.0,"aiming":false,"aim_pitch":-.2,"aim_yaw":.35}
	if condition == "moving": state.velocity=Vector3(0,0,2);state.local_velocity=state.velocity
	for unused in hz: motion.update_motion(dt,state);motion.evaluate_pose()
	var ability := "kodanda" if condition == "bow_control" else "measured_step"
	var duration := .18 if ability == "kodanda" else .1
	var entry := snapshot(motion)
	assert(motion.request_action(ability,duration,.25))
	for unused in ceili(duration*hz): motion.update_motion(dt,state);motion.evaluate_pose()
	if condition == "held":
		for unused in ceili(.13*hz):motion.update_motion(dt,state);motion.evaluate_pose()
	var current := snapshot(motion)
	var before := points(motion)
	if condition == "reset": motion.cancel("S1 before release");motion.evaluate_pose();before=points(motion)
	elif condition == "cancel": motion.cancel_action("S1 before release");motion.evaluate_pose();before=points(motion)
	var released: bool = motion.release_action(ability)
	motion.evaluate_pose()
	var released_pose := snapshot(motion)
	var boundary := difference(before,points(motion),motion)
	var duplicate_clock := clock(motion)
	var duplicate_before := points(motion)
	var duplicate_rejected: bool = not motion.release_action(ability)
	motion.evaluate_pose()
	var duplicate_stable: bool = duplicate_clock == clock(motion) and float(difference(duplicate_before,points(motion),motion).distance_m)<.00001
	var frozen := snapshot(motion)
	for unused in 5:motion.evaluate_pose()
	var freeze_ok: bool = frozen == snapshot(motion)
	var previous := points(motion)
	var maximum := {"distance_m":0.0}
	var first_recovery := {}
	var rows := []
	for frame in ceili(.45*hz):
		motion.update_motion(dt,state);motion.evaluate_pose()
		if frame == 0:first_recovery=snapshot(motion)
		var step := difference(previous,points(motion),motion)
		if float(step.distance_m)>float(maximum.distance_m):maximum=step.duplicate();maximum.frame=frame
		previous=points(motion)
		rows.append({"clock":clock(motion),"points":previous,"locks":motion.foot_locks.duplicate(),"targets":motion.foot_targets.duplicate()})
	var result := {"hz":hz,"condition":condition,"released":released,"entry":entry,"current":current,"release":released_pose,"first_recovery":first_recovery,"boundary":boundary,"maximum_recovery_step":maximum,"duplicate_rejected":duplicate_rejected,"duplicate_stable":duplicate_stable,"frozen":freeze_ok,"rows":rows}
	model.free()
	return result

func run() -> void:
	var pins := source_pins()
	pins[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	var baseline: Script = load(baseline_path)
	var candidate: Script = load(candidate_path)
	var continuity := true
	var late_steps := true
	var clocks := true
	var lifecycle := true
	var controls := true
	for hz in [30,60,120]:
		for condition in ["idle","moving","held","reset","cancel","bow_control"]:
			var a := release_trial(baseline,hz,condition)
			var b := release_trial(candidate,hz,condition)
			if condition in ["idle","moving","held"]:
				continuity=continuity and float(b.boundary.distance_m)<.00001
				late_steps=late_steps and float(b.maximum_recovery_step.distance_m)<=float(a.maximum_recovery_step.distance_m)+.00001
			for frame in a.rows.size():
				clocks=clocks and a.rows[frame].clock == b.rows[frame].clock
				if condition in ["bow_control","reset","cancel"]:
					for bone in a.rows[frame].points.size(): controls=controls and Vector3(a.rows[frame].points[bone]).distance_to(b.rows[frame].points[bone])<.00001
			clocks=clocks and a.current.clock==b.current.clock and a.release.clock==b.release.clock
			lifecycle=lifecycle and b.duplicate_rejected and b.duplicate_stable and b.frozen and b.released==(condition not in ["reset","cancel"])
			a.erase("rows");b.erase("rows")
			trials.append({"baseline":a,"candidate":b})
	check("full-body release begins at the outgoing pose at30/60/120",continuity)
	check("following recovery joint-step maximum does not increase",late_steps)
	check("release cancel gait and recovery clocks match baseline exactly",clocks)
	check("duplicate release reset cancel and frozen reevaluation remain stable",lifecycle)
	check("bow-only reset and cancelled trajectories remain baseline-equal",controls)
	var stable := true
	for path in pins:stable=stable and FileAccess.get_sha256(path)==pins[path]
	check("raw imported library controller and fixture bytes stay stable",stable)
	var passed := checks.all(func(row):return row.passed)
	DirAccess.make_dir_recursive_absolute(report_path.get_base_dir())
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"trials":trials,"sources":pins,"godot":Engine.get_version_info(),"scope":"Fresh actual imported164-bone rig, release boundary and first recovery full-pose snapshots. Manual presentation scheduling at30/60/120; no authoritative movement, SceneTree freeze or rendering acceptance."},"  ")+"\n")
	quit(0 if passed else 1)
