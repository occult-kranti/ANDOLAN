extends SceneTree
## Original offline adaptation code. Source GLB and Rama's nine clips stay intact.
const SOURCE := "res://player/model/player.glb"
const TARGET := "res://target/rama.glb"
const SOURCE_SHA := "16b783ec2e19245d034326d401796b9bd2635de75f4e38917854316abeee4f9c"
const PIN := "a82f15448e9b015440d3bbdf5e10801b260c4e9f"
const FULL := {
	"root":"hips", "spine05":"spine1", "spine03":"spine2", "spine01":"chest",
	"neck01":"neck", "neck03":"neck.001", "head":"head.001",
	"clavicle.L":"shoulder.L", "upperarm01.L":"upper_arm.L", "lowerarm01.L":"forearm.L", "wrist.L":"hand.L",
	"clavicle.R":"shoulder.R", "upperarm01.R":"upper_arm.R", "lowerarm01.R":"forearm.R", "wrist.R":"hand.R",
	"upperleg01.L":"thigh.L", "lowerleg01.L":"shin.L", "foot.L":"foot.L",
	"upperleg01.R":"thigh.R", "lowerleg01.R":"shin.R", "foot.R":"foot.R",
}
const CARRY := {
	"root":"hips", "spine05":"spine1", "spine03":"spine2", "spine01":"chest",
	"upperleg01.L":"thigh.L", "lowerleg01.L":"shin.L", "foot.L":"foot.L",
	"upperleg01.R":"thigh.R", "lowerleg01.R":"shin.R", "foot.R":"foot.R",
}
var output := ""
var library_path := ""
var full_body_study := false
var ss: Skeleton3D
var ts: Skeleton3D
var sp: AnimationPlayer
var tp: AnimationPlayer
var order: Array[int] = []
var binds := {}
var soles: Array[Dictionary] = []
var checks := []
var passed := true

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		elif arg.begins_with("--library="): library_path = arg.trim_prefix("--library=")
		elif arg == "--full-body-study": full_body_study = true
	call_deferred("run")

func find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find(child, kind)
		if found: return found
	return null

func record(name_: String, ok: bool, data: Dictionary = {}) -> void:
	checks.append({"name":name_, "passed":ok, "details":data})
	passed = passed and ok

func v(value: Vector3) -> Array:
	return [value.x, value.y, value.z]

func qarray(value: Quaternion) -> Array:
	return [value.x, value.y, value.z, value.w]

func matrix(value: Transform3D) -> Array:
	return [v(value.basis.x), v(value.basis.y), v(value.basis.z), v(value.origin)]

func write_json(path: String, data: Variant) -> void:
	var file := FileAccess.open(path, FileAccess.WRITE)
	assert(file != null, "Cannot write " + path)
	file.store_string(JSON.stringify(data, "  ") + "\n")

func rest(skeleton: Skeleton3D) -> Dictionary:
	var rows := []
	for bone in skeleton.get_bone_count():
		rows.append({"name":skeleton.get_bone_name(bone), "parent":skeleton.get_bone_parent(bone), "local":matrix(skeleton.get_bone_rest(bone)), "global":matrix(skeleton.get_bone_global_rest(bone))})
	return {"sha256":JSON.stringify(rows).sha256_text(), "bones":rows, "world":matrix(skeleton.global_transform)}

func snapshot(skeleton: Skeleton3D) -> Dictionary:
	var result := {}
	for bone in skeleton.get_bone_count():
		result[skeleton.get_bone_name(bone)] = {
			"local":skeleton.get_bone_pose_rotation(bone).normalized(),
			"world":(skeleton.global_basis * skeleton.get_bone_global_pose(bone).basis).orthonormalized().get_rotation_quaternion().normalized(),
			"position":skeleton.global_transform * skeleton.get_bone_global_pose(bone).origin,
		}
	return result

func sample(player: AnimationPlayer, skeleton: Skeleton3D, clip: String, seconds: float) -> Dictionary:
	player.stop()
	skeleton.reset_bone_poses()
	player.play(clip, 0)
	player.seek(seconds, true)
	player.advance(0)
	player.pause()
	skeleton.force_update_all_bone_transforms()
	return snapshot(skeleton)

func collect_source_binds(node: Node) -> void:
	if node is MeshInstance3D and node.skin:
		for index in node.skin.get_bind_count():
			var name_ := String(node.skin.get_bind_name(index))
			if name_.is_empty(): name_ = ss.get_bone_name(node.skin.get_bind_bone(index))
			if not binds.has(name_): binds[name_] = node.global_transform * node.skin.get_bind_pose(index).affine_inverse()
	for child in node.get_children(): collect_source_binds(child)

func collect_soles(node: Node) -> void:
	if node is MeshInstance3D and node.skin:
		var skin := []
		for index in node.skin.get_bind_count():
			var name_ := String(node.skin.get_bind_name(index))
			var bone: int = ts.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			skin.append({"bone":bone, "inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array = node.mesh.surface_get_arrays(surface)
			var points: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array = arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array = arrays[Mesh.ARRAY_WEIGHTS]
			var stride: int = joints.size() / points.size()
			for vertex in points.size():
				var influences := []
				var dominant := -1
				var largest := -1.0
				for slot in stride:
					var weight := weights[vertex * stride + slot]
					if weight <= 0: continue
					var bind: Dictionary = skin[joints[vertex * stride + slot]]
					influences.append({"bone":bind.bone, "point":bind.inverse * points[vertex], "weight":weight})
					if weight > largest:
						largest = weight
						dominant = bind.bone
				var name_ := String(ts.get_bone_name(dominant))
				if name_.begins_with("foot") or name_.begins_with("toe"):
					soles.append({"influences":influences, "side":"L" if name_.ends_with(".L") else "R"})
	for child in node.get_children(): collect_soles(child)

func sort_bones() -> void:
	var pending: Array[int] = []
	for bone in ts.get_bone_count(): pending.append(bone)
	while not pending.is_empty():
		var changed := false
		for bone in pending.duplicate():
			if ts.get_bone_parent(bone) < 0 or order.has(ts.get_bone_parent(bone)):
				order.append(bone)
				pending.erase(bone)
				changed = true
		assert(changed, "Target hierarchy must be acyclic")

func solve(pose: Dictionary, source_ref: Dictionary, target_ref: Dictionary, mapping: Dictionary) -> Dictionary:
	var locals := {}
	var globals := {}
	var inverse_world := ts.global_basis.orthonormalized().get_rotation_quaternion().inverse()
	for bone in order:
		var name_ := String(ts.get_bone_name(bone))
		var parent: Quaternion = globals.get(ts.get_bone_parent(bone), Quaternion.IDENTITY)
		var local: Quaternion = target_ref[name_].local
		if mapping.has(name_):
			var source_name: String = mapping[name_]
			var bind: Quaternion = binds[source_name].basis.orthonormalized().get_rotation_quaternion()
			var delta: Quaternion = pose[source_name].world * bind.inverse()
			var reference: Quaternion = source_ref[source_name].world * bind.inverse()
			var desired: Quaternion = (inverse_world * delta * reference.inverse() * target_ref[name_].world).normalized()
			local = (parent.inverse() * desired).normalized()
		locals[bone] = local
		globals[bone] = (parent * local).normalized()
	return locals

func periodic_filter(values: Dictionary, steps: int) -> Dictionary:
	var weights := [1.0,8.0,28.0,56.0,70.0,56.0,28.0,8.0,1.0]
	var largest_filter := 0.0
	var largest_seam := 0.0
	for bone in order:
		var original: Array = values[bone].duplicate()
		var rotations := original.duplicate()
		for pass_ in 3:
			var filtered := []
			for frame in steps:
				var total := Quaternion(0,0,0,0)
				for offset in range(-4,5):
					var value: Quaternion = rotations[posmod(frame + offset, steps)]
					if value.dot(rotations[frame]) < 0: value = -value
					total += value * weights[offset + 4]
				filtered.append(total.normalized())
			filtered.append(filtered[0])
			rotations = filtered
		for frame in steps + 1: largest_filter = maxf(largest_filter, original[frame].angle_to(rotations[frame]))
		var center: Quaternion = rotations[0]
		var after: Quaternion = (center.inverse() * rotations[1]).normalized()
		var before: Quaternion = (center.inverse() * rotations[steps - 1]).normalized()
		if after.w < 0: after = -after
		if before.w < 0: before = -before
		var tangent := (after.get_axis() * after.get_angle() - before.get_axis() * before.get_angle()) * 0.5
		var delta := Quaternion.IDENTITY if tangent.length() < 0.00000001 else Quaternion(tangent.normalized(), tangent.length())
		var next := (center * delta).normalized()
		var previous := (center * delta.inverse()).normalized()
		largest_seam = maxf(largest_seam, maxf(next.angle_to(rotations[1]), previous.angle_to(rotations[steps - 1])))
		rotations[1] = next
		rotations[steps - 1] = previous
		rotations[steps] = center
		values[bone] = rotations
	return {"maximum_filter_change_radians":largest_filter, "maximum_seam_neighbor_change_radians":largest_seam}

func feet(values: Dictionary, frame: int) -> Dictionary:
	var globals := {}
	for bone in order:
		var bind := ts.get_bone_rest(bone)
		var local := Transform3D(Basis(values[bone][frame]).scaled(bind.basis.get_scale()), bind.origin)
		globals[bone] = globals.get(ts.get_bone_parent(bone), Transform3D.IDENTITY) * local
	var result := {"L":INF, "R":INF}
	for point in soles:
		var position := Vector3.ZERO
		for influence in point.influences: position += (globals[influence.bone] * influence.point) * influence.weight
		position = ts.global_transform * position
		result[point.side] = minf(result[point.side], position.y)
	return result

func support(values: Dictionary, trajectory: Array, loop: bool, leg_scale: float) -> Dictionary:
	var count := trajectory.size()
	var bounds := []
	var source_floor := INF
	for frame in count:
		bounds.append(feet(values, frame))
		source_floor = minf(source_floor, trajectory[frame].foot_min_y)
	var bob := []
	var anchors := []
	var offsets := []
	for frame in count:
		var dy: float = trajectory[frame].hip_delta_y * leg_scale
		bob.append(dy)
		if trajectory[frame].foot_min_y <= source_floor + 0.025 or not loop:
			anchors.append(frame)
			offsets.append(0.005 - minf(bounds[frame].L,bounds[frame].R) - dy)
		else: offsets.append(NAN)
	assert(not anchors.is_empty())
	var period := count - 1
	for frame in count:
		if is_finite(offsets[frame]): continue
		var before: int = anchors[-1] - period
		var after: int = anchors[0] + period
		for anchor in anchors:
			if anchor < frame: before = anchor
			elif anchor > frame:
				after = anchor
				break
		var blend := float(frame - before) / maxf(1, after - before)
		blend = blend * blend * (3 - 2 * blend)
		offsets[frame] = lerpf(offsets[posmod(before,period)], offsets[posmod(after,period)], blend)
	for frame in count: offsets[frame] = maxf(bob[frame] + offsets[frame], 0.005 - minf(bounds[frame].L,bounds[frame].R))
	var lift := 0.0
	var largest_adjustment := 0.0
	if loop:
		var tangent: float = (offsets[1] - offsets[period - 1]) * 0.5
		var center: float = offsets[0]
		var corrected := {0:center, 1:center+tangent, period-1:center-tangent, period:center}
		for frame in corrected: lift = maxf(lift, 0.005 - minf(bounds[frame].L,bounds[frame].R) - corrected[frame])
		for frame in corrected:
			largest_adjustment = maxf(largest_adjustment, absf(corrected[frame] + lift - offsets[frame]))
			offsets[frame] = corrected[frame] + lift
	var samples := []
	for frame in count:
		samples.append({"seconds":trajectory[frame].seconds, "left_min_y":bounds[frame].L + offsets[frame], "right_min_y":bounds[frame].R + offsets[frame], "root_y_correction":offsets[frame], "source_support_candidate":frame in anchors})
	return {"offsets":offsets, "samples":samples, "sole_vertex_count":soles.size(), "source_contact_candidates":anchors.size(), "source_contact_band_metres":0.025, "minimum_correction":offsets.min(), "maximum_correction":offsets.max(), "common_seam_lift_metres":lift, "maximum_seam_height_adjustment_metres":largest_adjustment}

func run() -> void:
	if output.is_empty() or library_path.is_empty():
		push_error("Pass --output and --library absolute paths")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	DirAccess.make_dir_recursive_absolute(library_path.get_base_dir())
	record("pinned_source_bytes", FileAccess.get_sha256(SOURCE) == SOURCE_SHA)
	var source: Node3D = load(SOURCE).instantiate()
	var target: Node3D = load(TARGET).instantiate()
	root.add_child(source)
	root.add_child(target)
	await process_frame
	ss = find(source,"Skeleton3D")
	ts = find(target,"Skeleton3D")
	sp = find(source,"AnimationPlayer")
	tp = find(target,"AnimationPlayer")
	for player in [sp,tp]:
		player.callback_mode_process = AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
		for clip in player.get_animation_list(): player.get_animation(clip).loop_mode = Animation.LOOP_NONE
	sort_bones()
	collect_source_binds(source)
	collect_soles(target)
	var source_rest := rest(ss)
	var target_rest := rest(ts)
	record("rig_and_sole_inventory", ss.get_bone_count()==145 and ts.get_bone_count()==164 and soles.size()>100, {"source_bones":ss.get_bone_count(), "target_bones":ts.get_bone_count(), "actual_sole_vertices":soles.size()})
	var valid_mapping := true
	var audit := []
	for name_ in FULL:
		var source_name: String = FULL[name_]
		valid_mapping = valid_mapping and ts.find_bone(name_) >= 0 and ss.find_bone(source_name) >= 0 and binds.has(source_name)
		if not binds.has(source_name): continue
		var imported := ss.global_transform * ss.get_bone_global_rest(ss.find_bone(source_name))
		audit.append({"source":source_name, "target":name_, "imported_default_world":matrix(imported), "inverse_skin_bind_world":matrix(binds[source_name]), "orientation_difference_radians":imported.basis.orthonormalized().get_rotation_quaternion().angle_to(binds[source_name].basis.orthonormalized().get_rotation_quaternion())})
	record("all_semantic_mappings_resolve", valid_mapping)
	if not passed:
		write_json(output.path_join("bake-failed.json"), checks)
		quit(1)
		return
	var source_idle := sample(sp,ss,"Idle-cycle",0)
	tp.stop()
	ts.reset_bone_poses()
	ts.force_update_all_bone_transforms()
	var target_carry := snapshot(ts)
	var target_idle := sample(tp,ts,"idle",0)
	var source_center := sample(sp,ss,"AIM-Center",0)
	var fire_time := tp.get_animation("fire").length * 0.25
	var target_aim := sample(tp,ts,"fire",fire_time)
	var leg_scale: float = target_carry.root.position.distance_to(target_carry["foot.L"].position) / source_idle.hips.position.distance_to(source_idle["foot.L"].position)
	var specs := [{"name":"tps_idle","source":"Idle-cycle","loop":true},{"name":"tps_run","source":"running_nogun-cycle","loop":true},{"name":"tps_aim_up","source":"AIM-Up","loop":false}]
	var library := AnimationLibrary.new()
	var details := []
	var trajectories := {"kind":"source-world-trajectories-not-applied-to-gameplay", "source_sha256":SOURCE_SHA, "clips":{}}
	var contacts := {"kind":"actual-all-sole-CPU-skinning", "target_sha256":FileAccess.get_sha256(TARGET), "clips":{}}
	var poses := {}
	for spec in specs:
		var name_: String = spec.name
		var aiming: bool = not spec.loop
		var source_clip: Animation = sp.get_animation(spec.source)
		var duration: float = 0.5 if aiming else source_clip.length
		var steps := 1 if aiming else ceili(duration * 60)
		var mapping: Dictionary = FULL if aiming or full_body_study else CARRY
		var source_ref: Dictionary = source_center if aiming else source_idle
		var target_ref: Dictionary = target_aim if aiming else (target_idle if full_body_study else target_carry)
		var values := {}
		for bone in order: values[bone] = []
		var trajectory := []
		for frame in steps + 1:
			var seconds := duration * frame / steps
			var source_pose := sample(sp,ss,spec.source,0 if aiming else seconds)
			var solved := solve(source_pose,source_ref,target_ref,mapping)
			for bone in order:
				var value: Quaternion = solved[bone]
				if frame > 0 and values[bone][-1].dot(value) < 0: value = -value
				values[bone].append(value)
			var floor_y: float = minf(minf(source_pose["foot.L"].position.y,source_pose["foot.R"].position.y),minf(source_pose["toe.L"].position.y,source_pose["toe.R"].position.y))
			trajectory.append({"seconds":seconds,"root_world_xyz":v(source_pose.root.position),"hips_world_xyz":v(source_pose.hips.position),"foot_min_y":floor_y,"hip_delta_y":source_pose.hips.position.y-source_idle.hips.position.y})
		var filtering := {} if aiming else periodic_filter(values,steps)
		var contact := support(values,trajectory,spec.loop,leg_scale)
		var animation := Animation.new()
		animation.resource_name = name_
		animation.resource_scene_unique_id = name_
		animation.length = duration
		animation.loop_mode = Animation.LOOP_NONE if aiming else Animation.LOOP_LINEAR
		var max_step := 0.0
		var max_norm := 0.0
		var seam := 0.0
		var carry_error := 0.0
		var all_finite := true
		for bone in order:
			var track := animation.add_track(Animation.TYPE_ROTATION_3D)
			var bone_name := String(ts.get_bone_name(bone))
			animation.track_set_path(track,NodePath("YugaHeroRig/Skeleton3D:"+bone_name))
			animation.track_set_interpolation_type(track,Animation.INTERPOLATION_LINEAR)
			var motion := 0.0
			for frame in steps + 1:
				var value: Quaternion = values[bone][frame]
				all_finite = all_finite and value.is_finite()
				max_norm = maxf(max_norm,absf(value.length()-1))
				motion = maxf(motion,values[bone][0].angle_to(value))
				if frame > 0: max_step = maxf(max_step,values[bone][frame-1].angle_to(value))
				if not aiming and not full_body_study and not mapping.has(bone_name):
					var reference: Quaternion = target_carry[bone_name].local
					var aligned: Quaternion = value if value.dot(reference)>=0 else -value
					carry_error = maxf(carry_error, maxf(maxf(absf(aligned.x-reference.x),absf(aligned.y-reference.y)),maxf(absf(aligned.z-reference.z),absf(aligned.w-reference.w))))
			if motion < 0.00001: animation.rotation_track_insert_key(track,0,values[bone][0])
			else:
				for frame in steps+1: animation.rotation_track_insert_key(track,duration*frame/steps,values[bone][frame])
			seam=maxf(seam,values[bone][0].angle_to(values[bone][-1]))
		var height := animation.add_track(Animation.TYPE_POSITION_3D)
		animation.track_set_path(height,NodePath("YugaHeroRig/Skeleton3D:root"))
		var root_rest := ts.get_bone_rest(ts.find_bone("root")).origin
		for frame in steps+1: animation.position_track_insert_key(height,duration*frame/steps,root_rest+Vector3.UP*contact.offsets[frame])
		library.add_animation(name_,animation)
		var pose_rows := []
		for frame in [0, steps/4, steps/2, 3*steps/4, steps]:
			var row := {}
			for bone in order: row[ts.get_bone_name(bone)] = qarray(values[bone][frame])
			pose_rows.append({"seconds":duration*frame/steps,"root_y_correction":contact.offsets[frame],"local_rotations_xyzw":row})
		poses[name_]=pose_rows
		trajectories.clips[name_]=trajectory
		contacts.clips[name_]=contact
		var entry: Dictionary = spec.duplicate()
		entry.merge({"duration_seconds":duration,"bake_steps":steps,"active_source_mapping":mapping,"rotation_tracks":164,"visual_root_y_tracks":1,"filtering":filtering,"maximum_step_radians":max_step,"maximum_norm_error":max_norm,"loop_local_seam_radians":seam,"carry_rest_component_error":carry_error,"root_y_range":[contact.minimum_correction,contact.maximum_correction],"target_reference":"fire25% rotations only; provisional" if aiming else ("idle0; rejected full-body study" if full_body_study else "target bind/rest lowered carry")})
		details.append(entry)
		record(name_+"_finite_unit_rotations_and_range",all_finite and max_norm<0.00001 and max_step<PI/3,entry)
		record(name_+"_loop_pose_closure",aiming or seam<0.15,{"radians":seam})
		if not aiming and not full_body_study: record(name_+"_bind_carry_preserved",carry_error<0.000002,{"max_component":carry_error,"active_source_bones":mapping.size()})
	record("native_library_saved",ResourceSaver.save(library,library_path)==OK)
	write_json(output.path_join("source-target-rig-audit.json"),{"source":source_rest,"target":target_rest,"source_bind_audit":audit})
	write_json(output.path_join("source-root-trajectories.json"),trajectories)
	write_json(output.path_join("support-contact-samples.json"),contacts)
	write_json(output.path_join("sampled-local-poses.json"),{"kind":"baked-pose-data-not-render-evidence","clips":poses})
	var manifest := {
		"schema":2,"kind":"actual-offline-motion-adaptation","full_body_study":full_body_study,"passed":passed,"godot":Engine.get_version_info(),
		"source":{"repository":"https://github.com/godotengine/tps-demo","commit":PIN,"path":"player/model/player.glb","sha256":SOURCE_SHA,"rig_rest_sha256":source_rest.sha256,"bone_count":145,"license":"CC-BY 3.0","credit":"Copyright2018 Juan Linietsky, Fernando Miguel Calabró"},
		"target":{"path":"assets/heroes/rama-production.glb","sha256":FileAccess.get_sha256(TARGET),"rig_rest_sha256":target_rest.sha256,"bone_count":164,"original_animation_names":tp.get_animation_list()},
		"library":{"path":"res://assets/animations/tps_rama_motion_library.tres","sha256":FileAccess.get_sha256(library_path),"binding_root":"AnimationPlayer.root_node=..","bone_path":"YugaHeroRig/Skeleton3D:<bone>","suggested_namespace":"tps","license":"CC-BY 3.0 adaptation"},
		"method":{"source_import_fps":24,"bake_fps":60,"rest_compensation":"relative=(P*inverse(B))*inverse(R*inverse(B)); targetGlobal=relative*calibratedTargetGlobal; targetLocal=inverse(animatedImmediateParentGlobal)*targetGlobal in topological order","carry":"Only ten hips/spine/legs source mappings; all other local rotations remain target bind/rest. The full-body-study flag preserves the earlier rejected mapping for comparison.","filter":"Three periodic binomial quaternion passes, then shared signed logarithmic endpoint-neighbor tangents. Interior interpolation remains linear/SLERP.","support":"All actual dominant foot/toe skinned vertices. Source joint-height support candidates within25mm of clip minimum; scaled hipbob and smooth offsets through flight.5mm sole clearance. Common seam-neighborhood lift preserves matching rootY tangent.","translation":"Only visual deform-rootY varies; rest translations/scales and segment lengths otherwise retained. No rootXZ, CharacterBody or network movement is changed.","aim":"AIM-Up relative to AIM-Center at0, against targetfire rotations at25%; exact target seconds recorded. Not solved archery contact.","aim_target_fire_seconds":fire_time},
		"clips":details,"checks":checks,"generator_sha256":FileAccess.get_sha256("res://bake_tps_motion.gd"),
		"status":"Unpromoted candidate: independent geometry and actual rendered carry review required",
		"limitations":["Source contact windows are inferred, not labelled ground truth.","No horizontal foot locking or gameplay-speed compensation.","Aim remains an unpromoted firearm-reference experiment.","Headless numerical samples do not prove rendered quality or real-time performance."],
	}
	write_json(output.path_join("motion-retarget-manifest.json"),manifest)
	print("MOTION_BAKE ",JSON.stringify({"passed":passed,"checks":checks.size(),"sha256":manifest.library.sha256,"full_body_study":full_body_study}))
	source.free()
	target.free()
	quit(0 if passed else 1)
