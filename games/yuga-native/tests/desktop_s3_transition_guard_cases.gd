extends "res://tests/graphics_g2_support_cases.gd"
## Actual imported skin, isolated guard boundaries from the native failing pose.
const WITNESS := "res://docs/evidence/desktop-finish/S3/W5/guard-witness.json"
var witness:Dictionary

func unpack(values:Array) -> Transform3D:
	return Transform3D(Basis(Quaternion(values[3],values[4],values[5],values[6])),Vector3(values[0],values[1],values[2]))

func capture(m:Node) -> Array[Transform3D]:
	var result:Array[Transform3D]=[]
	for index in m.rig.get_bone_count():result.append(m.rig.get_bone_global_pose(index))
	return result

func difference(a:Array,b:Array) -> Dictionary:
	var position:=0.0;var rotation:=0.0
	for index in a.size():
		position=maxf(position,a[index].origin.distance_to(b[index].origin))
		rotation=maxf(rotation,a[index].basis.get_rotation_quaternion().angle_to(b[index].basis.get_rotation_quaternion()))
	return {"position_m":position,"rotation_rad":rotation}

func unchanged(a:Array,b:Array) -> bool:
	for index in a.size():
		if not a[index].is_equal_approx(b[index]):return false
	return true

func restore(m:Node) -> void:
	m.rig.global_transform=unpack(witness.row.rig)
	for index in m.rig.get_bone_count():
		var global_:Transform3D=unpack(witness.row.poses[index])
		var parent:int=m.rig.get_bone_parent(index)
		var local:Transform3D=unpack(witness.row.poses[parent]).affine_inverse()*global_ if parent>=0 else global_
		m.rig.set_bone_pose_position(index,local.origin)
		m.rig.set_bone_pose_rotation(index,local.basis.get_rotation_quaternion())
		m.rig.set_bone_pose_scale(index,Vector3.ONE)
	m.grounded=true;m.traversal="ground";m.locomotion="walk"
	m.transition_age=.08;m.transition_duration=.16;m.floor_y=witness.row.floor_input_y
	m.action="";m.action_stage="none"
	m.foot_locks={"L":false,"R":false}
	m.foot_targets={"L":Vector3(3,4,5),"R":Vector3(-3,4,5)}
	m.last_globals=capture(m)

func one_asset(asset:String) -> void:
	var body:=CharacterBody3D.new();root.add_child(body)
	var model:Node3D=load(asset).instantiate();body.add_child(model)
	var m=load(candidate_path).new();assert(m.configure(model,find_kind(model,"AnimationPlayer")));m.active=false
	var selected:=soles(model,m.rig)
	var original_rids:Array[RID]=m.support_exclude.duplicate()
	var leg_names:=[]
	for index in m.rig.get_bone_count():
		var name_:String=m.rig.get_bone_name(index)
		if name_.contains("leg") or name_.begins_with("foot") or name_.begins_with("toe"):leg_names.append(index)
	for scenario in ["clearance","age_zero","age_end","age_after","airborne","flight","grapple","jump","fall","dash","death","step_windup","step_recovery","preview","below_threshold","above_threshold","above_bound","freeze"]:
		restore(m);m.support_exclude=original_rids.duplicate()
		if scenario=="age_zero":m.transition_age=0.0
		elif scenario=="age_end":m.transition_age=.16
		elif scenario=="age_after":m.transition_age=.16001
		elif scenario=="airborne":m.grounded=false
		elif scenario in ["flight","grapple"]:m.traversal=scenario
		elif scenario in ["jump","fall","dash"]:m.locomotion=scenario
		elif scenario=="death":m.action="death";m.action_stage="recovery"
		elif scenario.begins_with("step_"):m.action="measured_step";m.action_stage=scenario.trim_prefix("step_")
		elif scenario=="preview":m.support_exclude.clear()
		elif scenario in ["below_threshold","above_threshold","above_bound"]:
			var foot:int=m.rig.find_bone("foot.L")
			var height:float=(m.rig.global_transform*m.rig.get_bone_global_pose(foot).origin).y
			var lift:=.0009 if scenario=="below_threshold" else .0011 if scenario=="above_threshold" else .0801
			m.floor_y=height-m.rest_globals[foot].origin.y+lift
		var before:=capture(m);var before_skin:=measure(m,selected,0);before_skin.erase("positions")
		var targets:Dictionary=m.foot_targets.duplicate();var root_before:=body.transform
		var clocks:=[m.phase,m.action_elapsed,m.transition_age,m.release_count,m.cancel_count,m.pending_delta]
		m._protect_transition_floor();var after:=capture(m);m.last_globals=after
		var skin:=measure(m,selected,0);skin.erase("positions")
		var upper_equal:=true
		for index in before.size():
			if index not in leg_names:upper_equal=upper_equal and before[index].is_equal_approx(after[index])
		var boundaries_equal:bool=targets==m.foot_targets and body.transform==root_before and clocks==[m.phase,m.action_elapsed,m.transition_age,m.release_count,m.cancel_count,m.pending_delta] and upper_equal
		var passed:bool=boundaries_equal
		if scenario in ["clearance","freeze"]:
			passed=passed and skin.L.minimum_m>=-.005 and skin.R.minimum_m>=-.005 and not unchanged(before,after)
			if scenario=="freeze":
				for unused in 5:m._protect_transition_floor()
				passed=passed and unchanged(after,capture(m))
		elif scenario in ["below_threshold","above_threshold","above_bound"]:
			var foot:int=m.rig.find_bone("foot.L")
			var equal:bool=before[foot].is_equal_approx(after[foot])
			passed=passed and (not equal if scenario=="above_threshold" else equal)
		else:passed=passed and unchanged(before,after)
		var detail:={"asset":asset,"scenario":scenario,"vertices":selected.size(),"before_soles":before_skin,"after_soles":skin,"pose_difference":difference(before,after),"root_clocks_anchors_upper_equal":boundaries_equal}
		trials.append(detail)
		check(asset.get_file()+" "+scenario,passed,detail)
	body.free()

func never_grounded() -> void:
	var streams:=[]
	for path in [baseline_path,candidate_path]:
		var body:=CharacterBody3D.new();root.add_child(body);body.position.y=.05
		var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();body.add_child(model)
		var m=load(path).new();assert(m.configure(model,find_kind(model,"AnimationPlayer")));m.active=false
		var frames:=[]
		# First submitted state and every later state are airborne: no grounded warmup.
		for unused in 18:
			m.update_motion(1.0/60,{"grounded":false,"floor_y":0.0,"velocity":Vector3(0,-1,0),"traversal":"ground"});m.evaluate_pose();frames.append(capture(m))
		streams.append(frames);body.free()
	var same:=true
	for index in streams[0].size():same=same and unchanged(streams[0][index],streams[1][index])
	check("never-grounded actual imported actor remains baseline-equal for18 updates",same)

func run() -> void:
	baseline_path="res://docs/evidence/desktop-finish/S3/W5/baseline/rama_motion.gd"
	witness=JSON.parse_string(FileAccess.get_file_as_string(WITNESS))
	source_pins=pins();source_pins[WITNESS]=FileAccess.get_sha256(WITNESS);source_pins[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	for asset in ["res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb"]:one_asset(asset)
	check("all54 declared imported boundary cases executed",trials.size()==54)
	never_grounded()
	var stable:=true
	for path in source_pins:stable=stable and FileAccess.get_sha256(path)==source_pins[path]
	check("guard fixture and exact imported inputs remain stable",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":source_pins,"trials":trials,"scope":"Actual imported near/mid/far skin on the retained native failure pose; direct guard boundary injection isolates eligibility and write ownership. Never-grounded case uses full update/evaluate from first submission. No native input/render/temporal acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	for unused in 4:await process_frame
	quit(0 if result.passed else 1)
