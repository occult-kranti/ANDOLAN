extends SceneTree
const MOTION := preload("/workspace/ANDOLAN/scratch/visual-round4/role-05/rama_motion.release-r4.gd")
var hero_path := "res://assets/heroes/rama-hero.glb"
var checks: Array[Dictionary] = []
var sk: Skeleton3D
var fingers: Array[Dictionary] = []
var soles: Array[Dictionary] = []
var draw_fingers: Array[Dictionary] = []
var report_path := "/tmp/rama-motion-study/motion-tests.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path=arg.trim_prefix("--report=")
		elif arg.begins_with("--asset="): hero_path=arg.trim_prefix("--asset=")
	call_deferred("run")
func find_node(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result:=find_node(child,kind)
		if result: return result
	return null
func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)
func tick(motion: Node, frames: int, state: Dictionary={}, hz:=60.0) -> void:
	for frame in frames:
		motion.update_motion(1/hz,state)
		motion.evaluate_pose()
func create() -> Array:
	var model=load(hero_path).instantiate()
	root.add_child(model)
	var motion=MOTION.new()
	var ok=motion.configure(model,find_node(model,"AnimationPlayer"))
	return [model,motion,ok]
func collect(node: Node) -> void:
	if node is MeshInstance3D and node.skin:
		var binds: Array[Dictionary] = []
		for index in node.skin.get_bind_count():
			var name_ := String(node.skin.get_bind_name(index))
			var bone: int = sk.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array = node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
			var stride: int = joints.size()/vertices.size()
			for index in vertices.size():
				var influences: Array[Dictionary] = []
				var dominant := -1
				var largest := 0.0
				for slot in stride:
					var weight := weights[index*stride+slot]
					if weight<=0.0: continue
					var bind: Dictionary = binds[joints[index*stride+slot]]
					influences.append({"bone":bind.bone,"point":bind.inverse*vertices[index],"weight":weight})
					if weight>largest:
						largest=weight
						dominant=bind.bone
				var name_ := String(sk.get_bone_name(dominant)) if dominant>=0 else ""
				if name_.begins_with("finger") and name_.ends_with("-3.R"):
					fingers.append({"name":name_,"influences":influences})
				elif name_.begins_with("finger") and name_.ends_with("-3.L"):
					draw_fingers.append({"name":name_,"influences":influences})
				elif name_.begins_with("foot") or name_.begins_with("toe"):
					soles.append({"name":name_,"influences":influences})
	for child in node.get_children(): collect(child)

func vertices(points: Array[Dictionary]) -> PackedVector3Array:
	var transforms: Array[Transform3D] = []
	for bone in sk.get_bone_count(): transforms.append(sk.get_bone_global_pose(bone))
	var result := PackedVector3Array()
	for vertex in points:
		var point := Vector3.ZERO
		for influence in vertex.influences: point+=(transforms[influence.bone]*influence.point)*influence.weight
		result.append(point)
	return result

func grip() -> Dictionary:
	var inverse := sk.get_bone_global_pose(sk.find_bone("wrist.R")).affine_inverse()
	var points := vertices(fingers)
	var gaps := {}
	var penetrations := {}
	var penetration := 0.0
	var finite := true
	for index in points.size():
		var point: Vector3 = inverse*points[index]-MOTION.GRIP_CENTER
		var radial := Vector2(point.y,point.z).length()-MOTION.GRIP_RADIUS
		var axial := absf(point.x)-MOTION.GRIP_HALF_LENGTH
		var signed_distance := Vector2(maxf(radial,0.0),maxf(axial,0.0)).length()+minf(maxf(radial,axial),0.0)
		var name_: String = fingers[index].name
		gaps[name_]=minf(float(gaps.get(name_,INF)),absf(signed_distance))
		penetrations[name_]=maxf(float(penetrations.get(name_,0.0)),-signed_distance)
		penetration=maxf(penetration,-signed_distance)
		finite=finite and point.is_finite()
	var mean := 0.0
	for value in gaps.values(): mean+=value/gaps.size()
	return {"finite":finite,"distal_surface_gap_by_finger_m":gaps,"distal_penetration_by_finger_m":penetrations,"mean_gap_m":mean,"max_penetration_m":penetration,"sampled_vertices":points.size()}

func run() -> void:
	var fixture:=create()
	var model: Node3D=fixture[0]
	var motion=fixture[1]
	sk=find_node(model,"Skeleton3D")
	collect(model)
	check("complete rig and library configure",fixture[2])
	check("duplicate configure rejected",not motion.configure(model))
	var changed_rig=load(hero_path).instantiate()
	root.add_child(changed_rig)
	var changed_skeleton: Skeleton3D=find_node(changed_rig,"Skeleton3D")
	var rest:=changed_skeleton.get_bone_rest(0)
	rest.origin.x+=.05
	changed_skeleton.set_bone_rest(0,rest)
	var rejected=MOTION.new()
	check("matching bone count with altered rest rig rejected",not rejected.configure(changed_rig) and rejected.get_parent()==null)
	rejected.free(); changed_rig.free()
	check("23 distinct original clips",motion.library.get_animation_list().size()==23)
	var dense_finite:=true
	var max_seam:=0.0
	for clip in motion.library.get_animation_list():
		for frame in 61:
			var sampled: Dictionary=motion._sample(String(clip),float(frame)/60)
			for index in sampled.positions.size(): dense_finite=dense_finite and sampled.positions[index].is_finite() and sampled.rotations[index].is_finite()
		var anim: Animation=motion.library.get_animation(clip)
		if anim.loop_mode==Animation.LOOP_LINEAR:
			var first: Dictionary=motion._sample(String(clip),0)
			var last: Dictionary=motion._sample(String(clip),1)
			for index in first.positions.size(): max_seam=maxf(max_seam,first.positions[index].distance_to(last.positions[index]))
	check("all clip samples finite and position loops close",dense_finite and max_seam<.0001,{"samples":23*61,"maximum_seam_m":max_seam})
	tick(motion,20)
	check("neutral pose finite",motion.finite)
	var grip_result:=grip()
	check("actual distal vertices wrap handle",grip_result.mean_gap_m<.002 and grip_result.max_penetration_m<.002,grip_result)
	var sole_points:=vertices(soles)
	var min_sole:=INF
	for point in sole_points: min_sole=minf(min_sole,point.y)
	check("standing sole reaches ground without sinking",min_sole>-.012 and min_sole<.015,{"minimum_sole_y":min_sole,"vertices":sole_points.size()})
	var initial: Transform3D=motion.socket_global("bow_grip")
	check("bow hand is lowered ready carry",initial.origin.y>.8 and initial.origin.y<1.3,{"position":str(initial.origin)})
	check("request primary accepted",motion.request_action("kodanda",.18,.22))
	tick(motion,60)
	check("windup holds pending authoritative release",motion.action_stage=="hold" and motion.release_count==0 and motion.nocked)
	var string_socket: Transform3D=motion.socket_global("string_nock")
	var hand: Transform3D=motion.socket_global("draw_hand")
	check("draw fingertips contact deforming string",string_socket.origin.distance_to(hand.origin)<.0001,{"error":string_socket.origin.distance_to(hand.origin)})
	var nearest_skin:=INF
	var nearest_point:=Vector3.ZERO
	var inverse_hand:=sk.get_bone_global_pose(sk.find_bone("wrist.L")).affine_inverse()
	for point in vertices(draw_fingers):
		if point.distance_to(string_socket.origin)<nearest_skin:
			nearest_skin=point.distance_to(string_socket.origin); nearest_point=inverse_hand*point
	check("string touches actual draw finger surface",nearest_skin<.006,{"nearest_skin_m":nearest_skin,"nearest_local":str(nearest_point)})
	check("draw raises bow visibly",motion.socket_global("bow_grip").origin.y>initial.origin.y+.20)
	var arrow_forward: Vector3=(motion.socket_global("bow_grip").origin-string_socket.origin).normalized()
	check("nocked arrow follows model aim",arrow_forward.dot(Vector3.BACK)>.995,{"direction":str(arrow_forward)})
	tick(motion,30,{"aim_pitch":.3})
	var elevated_arrow: Vector3=(motion.socket_global("bow_grip").origin-motion.socket_global("string_nock").origin).normalized()
	check("camera positive pitch lifts model positive-Z aim",elevated_arrow.y>.25,{"direction":str(elevated_arrow)})
	check("wrong release id rejected",not motion.release_action("dawn_volley"))
	check("authoritative release consumed exactly once",motion.release_action("kodanda") and not motion.release_action("kodanda") and motion.release_count==1 and not motion.nocked)
	tick(motion,30)
	check("recovery returns to locomotion",motion.action_stage=="none")
	var action_results:=[]
	for id in MOTION.ACTIONS:
		motion.cancel()
		motion.request_action(id,.35,.25)
		tick(motion,25,{"velocity":Vector3(0,0,6),"grounded":true})
		var held: bool=motion.finite and motion.action_stage=="hold"
		motion.release_action(id)
		tick(motion,30)
		action_results.append({"id":id,"finite":held and motion.finite,"stage":motion.action_stage})
	var all_actions:=true
	for item in action_results: all_actions=all_actions and item.finite
	check("all abilities and reactions finite",all_actions,{"actions":action_results})
	motion.cancel()
	motion.request_action("kodanda",.18,.22)
	tick(motion,4)
	motion.cancel_action("interrupted")
	tick(motion,20)
	check("interruption clears nock without release",not motion.nocked and motion.action_stage=="none" and motion.release_count==9)
	var modes:=[]
	for state in [{"velocity":Vector3(0,0,2)},{"velocity":Vector3(0,0,6)},{"velocity":Vector3(0,0,9)},{"velocity":Vector3(4,0,0),"aiming":true},{"velocity":Vector3(0,5,3),"grounded":false},{"velocity":Vector3(0,-5,3),"grounded":false},{"grounded":true},{"traversal":"flight","grounded":false},{"traversal":"grapple","grounded":false}]:
		tick(motion,30,state)
		modes.append({"state":motion.locomotion,"finite":motion.finite})
	var modes_finite:=true
	for mode in modes: modes_finite=modes_finite and mode.finite
	check("ground and traversal states finite",modes_finite,{"modes":modes})
	motion.cancel()
	motion.phase=0
	motion.max_contact_error=0
	var max_sole_clearance:=0.0
	var deepest_sole:=0.0
	var max_support_slide:=0.0
	var prior_centers:={}
	var prior_targets:={}
	for frame in 120:
		model.position.z+=6.0/60
		motion.update_motion(1.0/60,{"velocity":Vector3(0,0,6),"floor_y":0.0})
		motion.evaluate_pose()
		var points:=vertices(soles)
		for side in ["L","R"]:
			if not motion.foot_locks[side]:
				prior_centers.erase(side); continue
			var minimum:=INF
			var center:=Vector3.ZERO
			var count:=0
			for index in points.size():
				if not String(soles[index].name).ends_with("."+side): continue
				var point: Vector3=model.global_transform*points[index]
				minimum=minf(minimum,point.y); center+=point; count+=1
			center/=count
			max_sole_clearance=maxf(max_sole_clearance,minimum)
			deepest_sole=minf(deepest_sole,minimum)
			if prior_centers.has(side) and prior_targets[side].distance_to(motion.foot_targets[side])<.00001:
				max_support_slide=maxf(max_support_slide,center.distance_to(prior_centers[side]))
			prior_centers[side]=center; prior_targets[side]=motion.foot_targets[side]
	check("actual translated support soles remain grounded",max_sole_clearance<.015 and deepest_sole>-.015,{"max_clearance_m":max_sole_clearance,"minimum_y":deepest_sole})
	check("actual support skin avoids visible sliding",max_support_slide<.012,{"maximum_per_frame_m":max_support_slide})
	check("translated run contact IK reaches support targets",motion.max_contact_error<.002,{"maximum_error_m":motion.max_contact_error})
	motion.cancel()
	motion.phase=0
	motion.max_contact_error=0
	max_sole_clearance=0.0
	deepest_sole=0.0
	max_support_slide=0.0
	prior_centers={}
	prior_targets={}
	model.position=Vector3.ZERO
	var crossed_midline:=0.0
	var unexpected_replants:=0
	for frame in 120:
		model.position.x+=4.0/60
		motion.update_motion(1.0/60,{"velocity":Vector3(4,0,0),"aiming":true,"floor_y":0.0})
		motion.evaluate_pose()
		for side in ["L","R"]:
			var foot_local:=sk.get_bone_global_pose(sk.find_bone("foot."+side)).origin
			crossed_midline=maxf(crossed_midline,-foot_local.x if side=="L" else foot_local.x)
		var points=vertices(soles)
		for side in ["L","R"]:
			if not motion.foot_locks[side]:
				prior_centers.erase(side); continue
			var minimum=INF
			var center=Vector3.ZERO
			var count=0
			for index in points.size():
				if not String(soles[index].name).ends_with("."+side): continue
				var point: Vector3=model.global_transform*points[index]
				minimum=minf(minimum,point.y); center+=point; count+=1
			center/=count
			max_sole_clearance=maxf(max_sole_clearance,minimum)
			deepest_sole=minf(deepest_sole,minimum)
			if prior_centers.has(side):
				if prior_targets[side].distance_to(motion.foot_targets[side])>.00001: unexpected_replants+=1
				max_support_slide=maxf(max_support_slide,center.distance_to(prior_centers[side]))
			prior_centers[side]=center; prior_targets[side]=motion.foot_targets[side]
	check("actual translated strafe support soles remain grounded",max_sole_clearance<.015 and deepest_sole>-.015,{"max_clearance_m":max_sole_clearance,"minimum_y":deepest_sole})
	check("actual strafe support skin avoids visible sliding",max_support_slide<.012,{"maximum_per_frame_m":max_support_slide})
	check("translated strafe contact IK reaches support targets",motion.max_contact_error<.002,{"maximum_error_m":motion.max_contact_error})
	check("dedicated strafe feet avoid crossing body center",crossed_midline<.025,{"maximum_crossing_m":crossed_midline})
	check("steady strafe holds each support without replants",unexpected_replants==0,{"midstance_replants":unexpected_replants})
	var phases:=[]
	for hz in [30.0,60.0,120.0]:
		var f:=create()
		var m=f[1]
		tick(m,int(hz),{"velocity":Vector3(0,0,6),"aiming":true,"aim_pitch":.3},hz)
		phases.append({"phase":m.phase,"aim":m.aim_weight,"pitch":m.aim_pitch})
		f[0].free()
	check("distance phase and exponential aim match across clocks",absf(phases[0].phase-phases[2].phase)<.00001 and absf(phases[0].aim-phases[2].aim)<.00001 and absf(phases[0].pitch-phases[2].pitch)<.00001,{"samples":phases})
	var other_fixture:=create()
	var other=other_fixture[1]
	motion.cancel(); other.cancel()
	model.position=Vector3.ZERO
	tick(motion,25,{"velocity":Vector3(0,0,6)})
	tick(other,25,{"velocity":Vector3(0,0,6)})
	motion.request_action("kodanda",.18,.22)
	var lower_error:=0.0
	var lower_rotation_error:=0.0
	for frame in 16:
		tick(motion,1,{"velocity":Vector3(0,0,6)})
		tick(other,1,{"velocity":Vector3(0,0,6)})
		for index in motion.upper.size():
			if not motion.upper[index]:
				lower_error=maxf(lower_error,motion.last_positions[index].distance_to(other.last_positions[index]))
				lower_rotation_error=maxf(lower_rotation_error,motion.last_rotations[index].angle_to(other.last_rotations[index]))
	check("bow draw preserves lower-body locomotion",lower_error<.0001 and lower_rotation_error<.002,{"maximum_difference_m":lower_error,"maximum_rotation_difference_radians":lower_rotation_error})
	other_fixture[0].free()
	motion.cancel()
	var largest_wrist_step:=0.0
	var worst_wrist_frame:={}
	tick(motion,30)
	var previous_wrist: Vector3=motion.socket_global("bow_grip").origin
	for shot in 10:
		motion.request_action("kodanda",.18,.22)
		for frame in 24:
			if frame==11: motion.release_action("kodanda")
			tick(motion,1)
			var wrist: Vector3=motion.socket_global("bow_grip").origin
			if wrist.distance_to(previous_wrist)>largest_wrist_step: worst_wrist_frame={"shot":shot,"frame":frame,"stage":motion.action_stage,"warm":motion.warm_bow}
			largest_wrist_step=maxf(largest_wrist_step,wrist.distance_to(previous_wrist)); previous_wrist=wrist
	check("ten rapid cycles have bounded wrist travel",largest_wrist_step<.16,{"max_per_60Hz_frame_m":largest_wrist_step,"worst":worst_wrist_frame})
	var aimed_state:={"aiming":true,"aim_pitch":.3,"aim_yaw":.5}
	motion.cancel()
	tick(motion,90,aimed_state)
	motion.request_action("kodanda",.18,.22)
	tick(motion,60,aimed_state)
	var prior: Vector3=motion.socket_global("bow_grip").origin
	motion.cancel_action("aimed cancel")
	tick(motion,1,aimed_state)
	var cancel_jump: float=prior.distance_to(motion.socket_global("bow_grip").origin)
	tick(motion,60,aimed_state)
	prior=motion.socket_global("bow_grip").origin
	motion.request_action("kodanda",.18,.22)
	tick(motion,1,aimed_state)
	var retrigger_jump: float=prior.distance_to(motion.socket_global("bow_grip").origin)
	tick(motion,60,aimed_state)
	prior=motion.socket_global("bow_grip").origin
	aimed_state.velocity=Vector3(0,0,6)
	tick(motion,1,aimed_state)
	var run_jump: float=prior.distance_to(motion.socket_global("bow_grip").origin)
	check("nonzero aim is applied once across cancellation and transitions",maxf(cancel_jump,maxf(retrigger_jump,run_jump))<.025,{"cancel_wrist_m":cancel_jump,"retrigger_wrist_m":retrigger_jump,"start_run_wrist_m":run_jump})
	motion.cancel()
	check("nonfinite update rejected",not motion.update_motion(NAN,{}) and motion.rejected_states==1)
	check("nonfinite velocity rejected",not motion.update_motion(.016,{"velocity":Vector3(INF,0,0)}))
	check("invalid action duration rejected",not motion.request_action("kodanda",NAN,.2))
	check("unknown action rejected",not motion.request_action("unknown"))
	motion.cancel(); motion.cancel()
	tick(motion,20)
	check("idempotent reset gives finite idle",motion.finite and motion.locomotion=="idle" and motion.action_stage=="none")
	var passed:=true
	for item in checks: passed=passed and item.passed
	var report={"passed":passed,"checks":checks,"count":checks.size(),"source_sha256":FileAccess.get_sha256("res://scripts/rama_motion.gd"),"library_sha256":FileAccess.get_sha256(MOTION.LIBRARY_PATH),"hero_sha256":FileAccess.get_sha256(hero_path),"scope":"Headless pose/authority/contact tests. Visual animation acceptance requires continuous rendered sequence."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	model.free()
	quit(0 if passed else 1)
