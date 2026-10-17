extends SceneTree
const POSE := preload("res://scripts/hero_pose.gd")
const HERO := "res://assets/heroes/rama-production.glb"
var checks: Array[Dictionary] = []
var output := ""
var sk: Skeleton3D
var ap: AnimationPlayer
var fingers: Array[Dictionary] = []
var soles: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result := find(child,kind)
		if result: return result
	return null

func sample(clip: String, time: float) -> void:
	ap.stop()
	sk.reset_bone_poses()
	ap.play(clip,0.0)
	ap.seek(time,true)
	ap.advance(0.0)
	ap.pause()
	sk.force_update_all_bone_transforms()

func snapshot() -> Array[Transform3D]:
	var result: Array[Transform3D] = []
	for bone in sk.get_bone_count(): result.append(sk.get_bone_pose(bone))
	return result

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
		var point: Vector3 = inverse*points[index]-POSE.GRIP_CENTER
		var radial := Vector2(point.y,point.z).length()-POSE.GRIP_RADIUS
		var axial := absf(point.x)-POSE.GRIP_HALF_LENGTH
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
	var hashes := {}
	for path in [HERO,"res://scripts/hero_pose.gd","res://scripts/player.gd","res://assets/animations/tps_rama_motion_library.tres"]: hashes[path]=FileAccess.get_sha256(path)
	var hero: Node3D = load(HERO).instantiate()
	root.add_child(hero)
	sk=find(hero,"Skeleton3D")
	ap=find(hero,"AnimationPlayer")
	ap.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var native_names := ap.get_animation_list()
	var poses = POSE.new()
	check("configure resolves original arm finger and string contracts",poses.configure(hero,ap) and poses.mapping.size()==29 and sk.get_bone_parent(poses.bowstring)==sk.find_bone("wrist.R"))
	poses.active=false # Deterministic direct application; engine lifecycle checked below.
	check("reconfigure cannot duplicate modifiers or mappings",not poses.configure(hero,ap) and poses.mapping.size()==29)
	var missing := POSE.new()
	var empty := Node3D.new()
	check("missing skeleton or animator fails without attachment",not missing.configure(empty,ap) and missing.get_parent()==null and not missing.configure(hero,null))
	missing.free()
	empty.free()
	collect(hero)
	check("grip and contact probes use actual weighted skin vertices",fingers.size()>100 and soles.size()>1000,{"distal_finger_vertices":fingers.size(),"sole_vertices":soles.size()})
	ap.add_animation_library("candidate",load("res://assets/animations/tps_rama_motion_library.tres"))
	sample("candidate/tps_idle",.7)
	var open_grip := grip()
	for i in range(15): poses.set_state("tps_idle",1.0/60.0)
	poses._process_modification()
	sk.force_update_all_bone_transforms()
	var closed_grip := grip()
	check("authored grip materially reduces actual distal surface gap",closed_grip.finite and closed_grip.mean_gap_m<open_grip.mean_gap_m*.5 and closed_grip.mean_gap_m<.015,{"before":open_grip,"after":closed_grip})
	check("calibrated distal skin stays within two millimetres of handle surface",closed_grip.max_penetration_m<.002 and closed_grip.distal_surface_gap_by_finger_m.values().max()<.002,closed_grip)
	var allowed := {}
	for entry in poses.mapping: allowed[entry.bone]=true
	var protected := true
	var finite := true
	var positions := true
	var contact_error := 0.0
	var carry_gap_drift := 0.0
	var initial_gap := -1.0
	var loop_error := 0.0
	for clip in ["idle","run","candidate/tps_idle","candidate/tps_run"]:
		var animation := ap.get_animation(clip)
		var loop_before := animation.loop_mode
		animation.loop_mode=Animation.LOOP_NONE
		var first: Array[Transform3D] = []
		for index in range(13):
			sample(clip,animation.length*index/12.0)
			var before := snapshot()
			var feet_before := vertices(soles)
			poses._process_modification()
			sk.force_update_all_bone_transforms()
			var after := snapshot()
			for bone in sk.get_bone_count():
				finite=finite and after[bone].is_finite()
				if not allowed.has(bone) and bone!=poses.bowstring: protected=protected and before[bone].is_equal_approx(after[bone])
				if bone!=poses.bowstring: positions=positions and before[bone].origin.is_equal_approx(after[bone].origin)
				positions=positions and before[bone].basis.get_scale().is_equal_approx(after[bone].basis.get_scale())
			var feet_after := vertices(soles)
			for vertex in feet_before.size(): contact_error=maxf(contact_error,feet_before[vertex].distance_to(feet_after[vertex]))
			var contact := grip()
			if initial_gap<0.0: initial_gap=contact.mean_gap_m
			carry_gap_drift=maxf(carry_gap_drift,absf(contact.mean_gap_m-initial_gap))
			if index==0: first=after
			if index==12:
				for bone in allowed: loop_error=maxf(loop_error,first[bone].basis.get_rotation_quaternion().angle_to(after[bone].basis.get_rotation_quaternion()))
		animation.loop_mode=loop_before
	check("dense native and candidate carry samples remain finite",finite)
	check("all spine root lower-body and unmapped bone poses remain unchanged",protected)
	check("all scales and body translations stay animation-owned",positions)
	check("actual skinned soles are unchanged by upper-body carry",contact_error<.00001,{"maximum_vertex_delta_m":contact_error})
	check("grip remains wrist-relative through native and candidate motion",carry_gap_drift<.00001,{"maximum_mean_gap_drift_m":carry_gap_drift})
	check("carry upper-body poses close at exact clip endpoints",loop_error<.002,{"max_local_angle_radians":loop_error})
	var suppressed_valid := true
	for mode in ["fire","cast","cast1","cast2","cast3","jump","defeat"]:
		for i in range(15): poses.set_state("idle",1.0/60.0)
		for i in range(15): poses.set_state(mode,1.0/60.0)
		sample(mode,ap.get_animation(mode).length*.25)
		var original := snapshot()
		poses._process_modification()
		suppressed_valid=suppressed_valid and poses.weight==0.0 and snapshot()==original
	check("all original actions regain exact pose ownership after fade",suppressed_valid)
	var first_tick_owned := true
	for action in ["fire","cast","cast1","cast2","cast3"]:
		for i in range(15): poses.set_state("idle",1.0/60.0)
		sample(action,0.0)
		var original := snapshot()
		poses.set_state(action,1.0/60.0,"ground",true)
		poses._process_modification()
		first_tick_owned=first_tick_owned and poses.weight==0.0 and snapshot()==original
	check("first fire and cast tick retain exact arms and string ownership",first_tick_owned)
	var retriggers_valid := true
	for trigger in range(10):
		poses.set_state("idle",.1)
		poses.set_state("idle",.1)
		ap.play("fire",.055)
		ap.seek(0.0,true)
		ap.advance(0.0)
		var original := snapshot()
		poses.set_state("fire",1.0/60.0,"ground",true)
		poses._process_modification()
		retriggers_valid=retriggers_valid and poses.weight==0.0 and snapshot()==original
		ap.advance(.24)
	check("ten rapid fire retriggers cannot inherit carry arm or string pose",retriggers_valid)
	var guards := true
	for mode in ["flight","grapple","invalid"]:
		for i in range(15): poses.set_state("run",1.0/60.0)
		for i in range(15): poses.set_state("run",1.0/60.0,mode)
		guards=guards and poses.weight==0.0
	for i in range(15): poses.set_state("idle",1.0/60.0)
	for i in range(15): poses.set_state("idle",1.0/60.0,"ground",true)
	check("action and traversal guards fade carry to zero",guards and poses.weight==0.0)
	for value in [NAN,INF,-1.0,.2]:
		poses.set_state("idle",.1)
		poses.set_state("idle",value)
		check("invalid delta cancels safely "+str(value),poses.weight==0.0 and is_finite(poses.weight))
	# Exercise real modifier restoration, without resampling animation every frame.
	sample("idle",.5)
	for i in range(15): poses.set_state("idle",1.0/60.0)
	poses.active=true
	var extrema: Array[Vector3] = []
	var callback := func(): extrema.append(sk.get_bone_global_pose(sk.find_bone("wrist.R")).origin)
	poses.modification_processed.connect(callback)
	for frame in range(30): await process_frame
	var accumulation := 0.0
	for point in extrema: accumulation=maxf(accumulation,point.distance_to(extrema[0]))
	check("engine restores base pose between repeated modifier frames",extrema.size()>=20 and accumulation<.00001,{"callbacks":extrema.size(),"wrist_drift_m":accumulation})
	var callback_count := extrema.size()
	paused=true
	await create_timer(.04,true).timeout
	check("scene pause stops pose callbacks",extrema.size()==callback_count)
	paused=false
	poses.cancel()
	poses.cancel()
	await process_frame
	check("cancel is idempotent and restores zero contribution",poses.weight==0.0)
	poses.modification_processed.disconnect(callback)
	var stable := true
	for path in hashes: stable=stable and FileAccess.get_sha256(path)==hashes[path]
	check("source asset library and native clips remain unchanged",stable and native_names.size()==9)
	hero.free()
	await process_frame
	var passed := true
	for entry in checks: passed=passed and entry.passed
	var report := {"passed":passed,"checks":checks,"sources":hashes,"test_sha256":FileAccess.get_sha256(get_script().resource_path),"engine":Engine.get_version_info().string,
		"scope":"Actual upper-body modifier and CPU-skinned finger/sole probes. Cylinder distances are geometric proxies, not tactile grip or full skin penetration acceptance. Original lower-body animation is unchanged; flawed candidate run remains unpromoted. Rendered motion, moving-ground foot locking and performance are separate gates."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed=false
	print("YUGA_HERO_POSE_CASES ",JSON.stringify({"passed":passed,"checks":checks.size(),"report":output}))
	quit(0 if passed else 1)
