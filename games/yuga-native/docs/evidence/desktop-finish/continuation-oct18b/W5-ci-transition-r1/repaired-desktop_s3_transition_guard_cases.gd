extends "res://tests/graphics_g2_support_cases.gd"
## Actual imported skin, isolated guard boundaries from the native failing pose.
const WITNESS := "res://docs/evidence/desktop-finish/S3/W5/guard-witness.json"
var witness:Dictionary

class GuardDisabled:
	extends "res://scripts/rama_motion.gd"
	func _protect_transition_floor() -> void:
		pass

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

func same_stream(a:Array,b:Array) -> bool:
	if a.size()!=b.size():return false
	for index in a.size():
		if a[index].keys()!=b[index].keys():return false
		for key in a[index]:
			if key=="poses":
				if not unchanged(a[index][key],b[index][key]):return false
			elif a[index][key]!=b[index][key]:return false
	return true

func stream_hash(value:Variant) -> String:
	var context:=HashingContext.new();context.start(HashingContext.HASH_SHA256)
	context.update(var_to_bytes(value));return context.finish().hex_encode()

func never_grounded() -> void:
	var streams:=[];var nonleg_streams:=[];var premise:=true
	for variant in 3:
		var body:=CharacterBody3D.new();root.add_child(body);body.position.y=.05
		var model:Node3D=load("res://assets/heroes/rama-hero.glb").instantiate();body.add_child(model)
		var m=GuardDisabled.new() if variant==2 else load(baseline_path if variant==0 else candidate_path).new()
		assert(m.configure(model,find_kind(model,"AnimationPlayer")));m.active=false
		var frames:=[];var historical:=[]
		# No grounded warmup: current-vs-current isolates only this guard.
		# Historical whole fall poses intentionally differ after authored descent.
		for unused in 18:
			m.update_motion(1.0/60,{"grounded":false,"floor_y":0.0,"velocity":Vector3(0,-1,0),"traversal":"ground"});m.evaluate_pose()
			var poses:=capture(m);var upper:Array[Transform3D]=[]
			for index in poses.size():
				var name_:String=m.rig.get_bone_name(index)
				if not (name_.begins_with("upperleg") or name_.begins_with("lowerleg") or name_.begins_with("foot") or name_.begins_with("toe")):upper.append(poses[index])
			var state:={"poses":poses,"root":body.transform,"clocks":[m.phase,m.locomotion_age,m.action_elapsed,m.transition_age,m.transition_duration,m.release_count,m.cancel_count,m.pending_delta],"anchors":m.foot_targets.duplicate(),"locks":m.foot_locks.duplicate(),"grounded":m.grounded,"locomotion":m.locomotion}
			var old_comparable:Dictionary=state.duplicate(true);old_comparable.poses=upper;historical.append(old_comparable)
			if variant>0:
				state["support"]={"seen":m.measured_support_seen,"y":m.descent_support_y.duplicate(true),"xz":m.descent_support_xz.duplicate(true),"transform":m.descent_support_transform,"owner":m.descent_support_owner.duplicate(true),"owner_transform":m.descent_support_owner_transform.duplicate(true),"shape":m.descent_support_shape.duplicate(true)}
				premise=premise and not m.grounded and not m.measured_support_seen and m.descent_support_y.is_empty() and not m.foot_locks.L and not m.foot_locks.R
			frames.append(state)
		streams.append(frames);nonleg_streams.append(historical);body.free()
	var same:=same_stream(streams[1],streams[2])
	var old_upper_same:=same_stream(nonleg_streams[0],nonleg_streams[1])
	var pose_negative:Array=streams[2].duplicate(true)
	var changed:Transform3D=pose_negative[9].poses[4];changed.origin.y+=.001;pose_negative[9].poses[4]=changed
	var clock_negative:Array=streams[2].duplicate(true);clock_negative[9].clocks[0]+=1.0/60
	check("never-grounded current guard preserves all164 bones root clocks anchors and support for18 updates",premise and same,{"premise":premise,"frames":18,"current_sha256":stream_hash(streams[1]),"guard_disabled_sha256":stream_hash(streams[2]),"pose_tolerance":"existing Transform3D.is_equal_approx; all other fields exact"})
	check("never-grounded historical nonleg root clocks and anchors remain unchanged",old_upper_same,{"nonleg_bones":nonleg_streams[0][0].poses.size(),"old_sha256":stream_hash(nonleg_streams[0]),"current_sha256":stream_hash(nonleg_streams[1]),"scope":"Historical whole-leg fall pose equality is intentionally superseded; all54 direct guard cases and their thresholds remain unchanged."})
	check("never-grounded comparator rejects lowerleg correction and clock mutation",same and not same_stream(streams[1],pose_negative) and not same_stream(streams[1],clock_negative),{"lowerleg_correction_m":.001,"clock_mutation_s":1.0/60,"scope":"Only copied control records mutated; runtime poses and clocks remain untouched."})

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
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":source_pins,"trials":trials,"scope":"Actual imported near/mid/far skin on the retained native failure pose; direct guard boundary injection isolates eligibility and write ownership. Never-grounded case uses full update/evaluate from first submission against same-current motion with only the guard disabled, plus historical nonleg/authority comparison and copied-record negatives. No native input/render/temporal acceptance."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(result)+"\n")
	for unused in 4:await process_frame
	quit(0 if result.passed else 1)
