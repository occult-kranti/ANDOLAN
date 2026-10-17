extends SceneTree
## Reconstructed numerical QA after cloud replacement. Numerical and CPU-skinning
## evidence only; actual carry rendering is a separate acceptance gate.
const HERO := "res://assets/heroes/rama-production.glb"
const ORIGINAL := "res://assets/heroes/rama.glb"
const ORIGINAL_SHA := "a366dc927cb34208742e5617decefb2580e1cdab97f946ed4eb14687dc7abfbc"
const SOURCE_SHA := "16b783ec2e19245d034326d401796b9bd2635de75f4e38917854316abeee4f9c"
const SPECS := {"tps_idle":{"length":15.0,"loop":true},"tps_run":{"length":0.833333313,"loop":true},"tps_aim_up":{"length":0.5,"loop":false}}
const ACTIVE_CARRY := ["root","spine05","spine03","spine01","upperleg01.L","lowerleg01.L","foot.L","upperleg01.R","lowerleg01.R","foot.R"]
var library_path := "res://assets/animations/tps_rama_motion_library.tres"
var manifest_path := "res://art/motion/motion-retarget-manifest.json"
var contacts_path := "res://art/motion/support-contact-samples.json"
var output := "res://tests/evidence/motion-retarget-recovered-support.json"
var skeleton: Skeleton3D
var animator: AnimationPlayer
var hero: Node3D
var checks := []
var measurements := {}
var samples := []
var sole_samples := []
var passed := true
var started := Time.get_ticks_msec()
var validated_bake_target := ""
const COMPATIBILITY := "res://art/motion/compatible-targets.json"

func target_binding(target_sha: String, manifest: Dictionary, compatibility: Dictionary) -> bool:
	if target_sha==manifest.target.sha256: return true
	if compatibility.get("base_target_sha256")!=manifest.target.sha256 or compatibility.get("library_sha256")!=manifest.library.sha256: return false
	for entry in compatibility.get("compatible_targets",[]):
		if not entry is Dictionary or entry.get("sha256")!=target_sha: continue
		var proof_path: String=entry.get("proof","")
		if not proof_path.begins_with("res://art/production/") or ".." in proof_path or not proof_path.ends_with(".json"): return false
		if FileAccess.get_sha256(proof_path)!=entry.get("proof_sha256",""): return false
		var proof=JSON.parse_string(FileAccess.get_file_as_string(proof_path))
		if not proof is Dictionary or proof.get("passed")!=true or proof.get("asset_sha256")!=target_sha: return false
		if not proof.get("checks") is Array or proof.checks.size()<5: return false
		for item in proof.checks:
			if not item is Dictionary or item.get("passed")!=true: return false
		return true
	return false

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--library="): library_path=arg.trim_prefix("--library=")
		elif arg.begins_with("--manifest="): manifest_path=arg.trim_prefix("--manifest=")
		elif arg.begins_with("--contacts="): contacts_path=arg.trim_prefix("--contacts=")
		elif arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func record(name_: String, ok: bool, data: Dictionary = {}) -> void:
	checks.append({"name":name_,"passed":ok,"details":data})
	passed=passed and ok

func find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var result:=find(child,kind)
		if result: return result
	return null

func error_transform(a: Transform3D, b: Transform3D) -> float:
	var result:=0.0
	for axis in 3:
		result=maxf(result,absf(a.origin[axis]-b.origin[axis]))
		for component in 3: result=maxf(result,absf(a.basis[axis][component]-b.basis[axis][component]))
	return result

func quat_error(a: Quaternion, b: Quaternion) -> float:
	if a.dot(b)<0: a=-a
	return maxf(maxf(absf(a.x-b.x),absf(a.y-b.y)),maxf(absf(a.z-b.z),absf(a.w-b.w)))

func current() -> Dictionary:
	skeleton.force_update_all_bone_transforms()
	var globals:=[]
	var rotations:=[]
	var positions:=[]
	for bone in skeleton.get_bone_count():
		globals.append(skeleton.get_bone_global_pose(bone))
		rotations.append(skeleton.get_bone_pose_rotation(bone))
		positions.append(skeleton.get_bone_pose_position(bone))
	return {"global":globals,"rotation":rotations,"position":positions}

func at_time(time: float) -> Dictionary:
	animator.seek(time,true)
	animator.advance(0)
	return current()

func begin(clip: String, reset: bool=true) -> void:
	if reset:
		animator.stop()
		skeleton.reset_bone_poses()
	animator.play(clip,0)

func skin_collect(node: Node, stats: Dictionary) -> void:
	if node is MeshInstance3D and node.skin:
		var binds:=[]
		for index in node.skin.get_bind_count():
			var name_:=String(node.skin.get_bind_name(index))
			var bone: int = skeleton.find_bone(name_) if not name_.is_empty() else node.skin.get_bind_bone(index)
			binds.append({"bone":bone,"inverse":node.skin.get_bind_pose(index)})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var points: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var joints: PackedInt32Array=arrays[Mesh.ARRAY_BONES]
			var weights: PackedFloat32Array=arrays[Mesh.ARRAY_WEIGHTS]
			var stride: int = joints.size()/points.size()
			for vi in points.size():
				var influences:=[]
				var point:=Vector3.ZERO
				var weight_sum:=0.0
				var largest:=-1.0
				var dominant:=-1
				for slot in stride:
					var weight:=weights[vi*stride+slot]
					if weight<=0: continue
					var bind: Dictionary=binds[joints[vi*stride+slot]]
					if bind.bone<0 or not is_finite(weight):
						stats.invalid+=1
						continue
					var local: Vector3=bind.inverse*points[vi]
					influences.append({"bone":bind.bone,"local":local,"weight":weight})
					point+=(skeleton.get_bone_global_rest(bind.bone)*local)*weight
					weight_sum+=weight
					if weight>largest:
						largest=weight
						dominant=bind.bone
				stats.weight_error=maxf(stats.weight_error,absf(weight_sum-1))
				stats.rest_error=maxf(stats.rest_error,(skeleton.global_transform*point).distance_to(node.global_transform*points[vi]))
				var name_:=String(skeleton.get_bone_name(dominant)) if dominant>=0 else ""
				var foot:=name_.begins_with("foot") or name_.begins_with("toe")
				if foot:
					sole_samples.append({"influences":influences,"foot":"L" if name_.ends_with(".L") else "R"})
				if stats.vertices%127==0 or (foot and vi%7==0):
					samples.append({"influences":influences,"foot":("L" if name_.ends_with(".L") else "R") if foot else ""})
				stats.vertices+=1
	for child in node.get_children(): skin_collect(child,stats)

func skinned(pose: Dictionary) -> Dictionary:
	var result:={"finite":true,"minimum_y":INF,"max_radius":0.0,"left_min_y":INF,"right_min_y":INF}
	for point in samples:
		var vertex:=Vector3.ZERO
		for influence in point.influences: vertex+=(pose.global[influence.bone]*influence.local)*influence.weight
		vertex=skeleton.global_transform*vertex
		result.finite=result.finite and vertex.is_finite()
		result.minimum_y=minf(result.minimum_y,vertex.y)
		result.max_radius=maxf(result.max_radius,vertex.length())
		if point.foot=="L": result.left_min_y=minf(result.left_min_y,vertex.y)
		if point.foot=="R": result.right_min_y=minf(result.right_min_y,vertex.y)
	return result

func all_soles(pose: Dictionary) -> Dictionary:
	var result:={"finite":true,"left_min_y":INF,"right_min_y":INF}
	for point in sole_samples:
		var vertex:=Vector3.ZERO
		for influence in point.influences: vertex+=(pose.global[influence.bone]*influence.local)*influence.weight
		vertex=skeleton.global_transform*vertex
		result.finite=result.finite and vertex.is_finite()
		if point.foot=="L": result.left_min_y=minf(result.left_min_y,vertex.y)
		if point.foot=="R": result.right_min_y=minf(result.right_min_y,vertex.y)
	return result

func inspect_run_support() -> void:
	# Diagnostic labels come from the source-height inference. Re-evaluate EVERY
	# target sole vertex from the loaded library; never reuse the baker's heights.
	var evidence=JSON.parse_string(FileAccess.get_file_as_string(contacts_path))
	if not evidence is Dictionary or not evidence.has("clips"):
		record("run_support_evidence_resolves",false)
		return
	var source: Dictionary=evidence.clips.tps_run
	var clip:=animator.get_animation("qa/tps_run")
	begin("qa/tps_run")
	var timeline:=[]
	var finite:=true
	var minimum_left:=INF
	var minimum_right:=INF
	var maximum_both:=-INF
	var maximum_both_time:=0.0
	var maximum_support:=-INF
	var maximum_support_time:=0.0
	var support_count:=0
	var support_near_floor_count:=0
	var near_floor_left:=0
	var near_floor_right:=0
	var both_airborne_count:=0
	var max_baker_difference:=0.0
	var max_time_difference:=0.0
	var near_floor_threshold:=0.015
	for index in source.samples.size():
		var candidate: Dictionary=source.samples[index]
		var seconds: float=clip.length*index/(source.samples.size()-1)
		var sole:=all_soles(at_time(seconds))
		finite=finite and sole.finite
		max_time_difference=maxf(max_time_difference,absf(seconds-candidate.seconds))
		max_baker_difference=maxf(max_baker_difference,maxf(absf(sole.left_min_y-candidate.left_min_y),absf(sole.right_min_y-candidate.right_min_y)))
		minimum_left=minf(minimum_left,sole.left_min_y)
		minimum_right=minf(minimum_right,sole.right_min_y)
		var both: float=minf(sole.left_min_y,sole.right_min_y)
		if both>maximum_both:
			maximum_both=both
			maximum_both_time=seconds
		if candidate.source_support_candidate:
			support_count+=1
			if both>maximum_support:
				maximum_support=both
				maximum_support_time=seconds
			if both<=near_floor_threshold: support_near_floor_count+=1
		if sole.left_min_y<=near_floor_threshold: near_floor_left+=1
		if sole.right_min_y<=near_floor_threshold: near_floor_right+=1
		if both>near_floor_threshold: both_airborne_count+=1
		timeline.append({"seconds":seconds,"left_min_sole_y":sole.left_min_y,"right_min_sole_y":sole.right_min_y,"both_feet_clearance":both,"source_inferred_support":candidate.source_support_candidate})
	var metrics:={"kind":"all-foot-and-toe-dominant-vertices-reconstructed-from-loaded-library","sole_vertex_count":sole_samples.size(),"samples_including_duplicate_endpoint":timeline.size(),"sample_hz":60,"near_floor_threshold_metres":near_floor_threshold,"minimum_left_sole_y":minimum_left,"minimum_right_sole_y":minimum_right,"maximum_both_feet_clearance":maximum_both,"maximum_both_feet_clearance_seconds":maximum_both_time,"source_inferred_support_samples":support_count,"source_inferred_support_near_floor_samples":support_near_floor_count,"maximum_support_sample_clearance":maximum_support,"maximum_support_sample_clearance_seconds":maximum_support_time,"left_near_floor_samples":near_floor_left,"right_near_floor_samples":near_floor_right,"both_feet_above_near_floor_samples":both_airborne_count,"max_difference_from_baker_all_sole_heights":max_baker_difference,"max_source_sample_time_difference":max_time_difference,"scope":"Support labels are inferred from source bone heights, not authored contact events. Near-floor counts are vertical-clearance diagnostics, not horizontal foot lock, plausible flight, physical contact, or art acceptance.","timeline":timeline}
	measurements.run_support_diagnostic=metrics
	record("run_support_evidence_resolves",finite and sole_samples.size()==source.sole_vertex_count and source.samples.size()==51 and evidence.target_sha256==validated_bake_target and max_baker_difference<=0.002 and max_time_difference<=0.00001,{"sole_vertices":sole_samples.size(),"samples":timeline.size(),"max_baker_difference_metres":max_baker_difference,"max_time_difference_seconds":max_time_difference,"recorded_bake_target":evidence.target_sha256,"validated_bake_target":validated_bake_target})
	var neutral_pose:=at_time(0)
	var neutral:=all_soles(neutral_pose)
	for bone in neutral_pose.global.size(): neutral_pose.global[bone].origin.y+=0.1
	var lifted:=all_soles(neutral_pose)
	record("all_sole_diagnostic_detects_artificial_hover",absf(lifted.left_min_y-neutral.left_min_y-0.1)<0.00001 and absf(lifted.right_min_y-neutral.right_min_y-0.1)<0.00001)

func derivative(clip: String, duration: float, delta: float) -> Dictionary:
	begin(clip)
	var first:=at_time(0)
	var after:=at_time(delta)
	var before:=at_time(duration-delta)
	var last:=at_time(duration)
	var largest:=0.0
	var root_y:=0.0
	var worst:=""
	for bone in skeleton.get_bone_count():
		var incoming: Vector3=(last.global[bone].origin-before.global[bone].origin)/delta
		var outgoing: Vector3=(after.global[bone].origin-first.global[bone].origin)/delta
		var error:=incoming.distance_to(outgoing)
		if error>largest:
			largest=error
			worst=skeleton.get_bone_name(bone)
		if skeleton.get_bone_name(bone)=="root": root_y=absf(incoming.y-outgoing.y)
	return {"delta_seconds":delta,"root_y_velocity_mismatch":root_y,"worst_joint_velocity_mismatch":largest,"worst_bone":worst}

func fixtures() -> void:
	var valid:=Transform3D.IDENTITY
	var broken:=valid
	broken.origin.x=NAN
	record("finite_detector_rejects_nan",valid.is_finite() and not broken.is_finite())
	record("rest_axis_detector_rejects_changed_basis",error_transform(valid,Transform3D(Basis(Vector3.UP,0.3),Vector3.ZERO))>0.00005)
	var arm:=skeleton.get_bone_rest(skeleton.find_bone("upperarm01.R")).basis.get_rotation_quaternion()
	record("carry_detector_rejects_borrowed_arm_rotation",quat_error(arm,arm)<0.000002 and quat_error(arm,arm*Quaternion(Vector3.RIGHT,0.3))>0.000002)
	var broken_clip:=Animation.new()
	broken_clip.length=1.0
	var track:=broken_clip.add_track(Animation.TYPE_POSITION_3D)
	broken_clip.track_set_path(track,NodePath("YugaHeroRig/Skeleton3D:root"))
	var rest_root:=skeleton.get_bone_rest(skeleton.find_bone("root")).origin
	broken_clip.position_track_insert_key(track,0,rest_root)
	broken_clip.position_track_insert_key(track,0.5,rest_root+Vector3.UP*0.1)
	broken_clip.position_track_insert_key(track,1,rest_root)
	var fixture_library:=AnimationLibrary.new()
	fixture_library.add_animation("closed_bad_velocity",broken_clip)
	animator.add_animation_library("fixture",fixture_library)
	var probe:=derivative("fixture/closed_bad_velocity",1,0.001)
	record("actual_animation_c1_detector_rejects_closed_pose_bad_velocity",probe.root_y_velocity_mismatch>0.05 and probe.worst_joint_velocity_mismatch>0.25,probe)
	animator.stop()
	# Retain the private fixture until model disposal: stop() keeps its assigned
	# animation name, so removing it here makes the next stop() seek a missing clip.

func inspect_clip(name_: String, clip: Animation) -> void:
	var spec: Dictionary=SPECS[name_]
	record(name_+"_duration_and_loop",absf(clip.length-spec.length)<0.0001 and (clip.loop_mode!=Animation.LOOP_NONE)==spec.loop)
	var invalid_paths:=[]
	var types:={}
	for track in clip.get_track_count():
		var path:=clip.track_get_path(track)
		var type:=clip.track_get_type(track)
		types[str(type)]=types.get(str(type),0)+1
		var allowed:=type==Animation.TYPE_ROTATION_3D or (type==Animation.TYPE_POSITION_3D and path.get_subname_count()==1 and path.get_subname(0)=="root")
		if not allowed or path.get_subname_count()!=1 or skeleton.find_bone(path.get_subname(0))<0 or animator.get_node(animator.root_node).get_node_or_null(NodePath(path.get_concatenated_names()))!=skeleton:
			invalid_paths.append(str(path))
	record(name_+"_target_tracks_and_allowlist",invalid_paths.is_empty() and clip.get_track_count()==165,{"invalid":invalid_paths,"types":types})
	# Never let automatic loop wrapping hide a bad authored endpoint.
	clip.loop_mode=Animation.LOOP_NONE
	begin("qa/"+name_)
	var steps:=ceili(clip.length*60)
	var first:=at_time(0)
	var prior:=first
	var last:=first
	var invalid:=0
	var stretch:=0.0
	var drift:=0.0
	var step_angle:=0.0
	var carry_error:=0.0
	var geometry_finite:=true
	var min_geometry:=INF
	var max_geometry:=0.0
	var foot_l:=INF
	var foot_r:=INF
	var mesh_frames:=0
	for frame in steps+1:
		var pose:=at_time(clip.length*frame/steps)
		for bone in skeleton.get_bone_count():
			var transform_: Transform3D=pose.global[bone]
			if not transform_.is_finite() or absf(transform_.basis.determinant())<0.000001: invalid+=1
			var parent:=skeleton.get_bone_parent(bone)
			if parent>=0:
				var rest_length:=skeleton.get_bone_rest(bone).origin.length()
				var length: float=transform_.origin.distance_to(pose.global[parent].origin)
				stretch=maxf(stretch,absf(rest_length-length))
			if frame>0: step_angle=maxf(step_angle,prior.rotation[bone].normalized().angle_to(pose.rotation[bone].normalized()))
			var bone_name:=String(skeleton.get_bone_name(bone))
			if spec.loop and not ACTIVE_CARRY.has(bone_name):
				carry_error=maxf(carry_error,quat_error(pose.rotation[bone],skeleton.get_bone_rest(bone).basis.get_rotation_quaternion()))
		var root_index:=skeleton.find_bone("root")
		var delta: Vector3=pose.global[root_index].origin-first.global[root_index].origin
		drift=maxf(drift,Vector2(delta.x,delta.z).length())
		if frame%4==0 or frame==steps:
			var mesh:=skinned(pose)
			geometry_finite=geometry_finite and mesh.finite
			min_geometry=minf(min_geometry,mesh.minimum_y)
			max_geometry=maxf(max_geometry,mesh.max_radius)
			foot_l=minf(foot_l,mesh.left_min_y)
			foot_r=minf(foot_r,mesh.right_min_y)
			mesh_frames+=1
		prior=pose
		last=pose
	var seam_position:=0.0
	var seam_rotation:=0.0
	for bone in skeleton.get_bone_count():
		seam_position=maxf(seam_position,first.global[bone].origin.distance_to(last.global[bone].origin))
		seam_rotation=maxf(seam_rotation,first.rotation[bone].normalized().angle_to(last.rotation[bone].normalized()))
	var metrics:={"bone_samples":(steps+1)*164,"finite_failures":invalid,"max_segment_error_metres":stretch,"root_xz_metres":drift,"max_step_radians":step_angle,"max_carry_rest_component_error":carry_error,"loop_position_error_metres":seam_position,"loop_angle_error_radians":seam_rotation,"mesh_frames":mesh_frames,"vertices_per_mesh_sample":samples.size(),"min_sampled_geometry_y":min_geometry,"max_sampled_geometry_radius":max_geometry,"left_min_sole_y":foot_l,"right_min_sole_y":foot_r}
	record(name_+"_dense_bone_range_and_lengths",invalid==0 and stretch<=0.002 and drift<=0.002 and step_angle<=PI/3,metrics)
	record(name_+"_actual_skinned_geometry",geometry_finite and min_geometry>=-0.005 and max_geometry<=4.0 and foot_l<0.04 and foot_r<0.04,metrics)
	if spec.loop:
		record(name_+"_rest_carry_preserved",carry_error<=0.000002,{"max_quaternion_component_error":carry_error})
		record(name_+"_honest_loop_endpoint",seam_position<=0.03 and seam_rotation<=0.15,metrics)
		var derivatives:=[]
		for delta in [1.0/60,1.0/240,0.001]: derivatives.append(derivative("qa/"+name_,clip.length,delta))
		metrics.endpoint_derivatives=derivatives
		record(name_+"_c1_root_velocity",derivatives[-1].root_y_velocity_mismatch<=0.05,derivatives[-1])
		record(name_+"_c1_joint_velocity",derivatives[-1].worst_joint_velocity_mismatch<=0.25,derivatives[-1])
	measurements[name_]=metrics

func transition(source: String, source_fraction: float, destination: String, seconds: float) -> void:
	begin("qa/"+destination)
	var clean:=at_time(seconds)
	begin(source)
	at_time(animator.get_animation(source).length*source_fraction)
	begin("qa/"+destination,false)
	var transitioned:=at_time(seconds)
	var error:=0.0
	for bone in skeleton.get_bone_count(): error=maxf(error,clean.position[bone].distance_to(transitioned.position[bone]))
	record(source+"_to_"+destination+"_no_translation_leak_without_reset",error<=0.00005,{"max_local_translation_error":error,"scope":"zero-blend actual AnimationPlayer; blended quality needs renderer"})

func run() -> void:
	var source_hashes:={}
	for path in [HERO,ORIGINAL,library_path,manifest_path,contacts_path]: source_hashes[path]=FileAccess.get_sha256(path)
	var manifest=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not manifest is Dictionary:
		record("manifest_exists",false)
		finish(source_hashes)
		return
	var compatibility := {}
	if FileAccess.file_exists(COMPATIBILITY):
		var parsed=JSON.parse_string(FileAccess.get_file_as_string(COMPATIBILITY))
		if parsed is Dictionary: compatibility=parsed
		source_hashes[COMPATIBILITY]=FileAccess.get_sha256(COMPATIBILITY)
		for entry in compatibility.get("compatible_targets",[]):
			if entry is Dictionary and String(entry.get("proof","")).begins_with("res://art/production/") and not ".." in entry.proof:
				source_hashes[entry.proof]=FileAccess.get_sha256(entry.proof)
	var binding_valid: bool=manifest.source.sha256==SOURCE_SHA and target_binding(source_hashes[HERO],manifest,compatibility) and manifest.library.sha256==source_hashes[library_path]
	if binding_valid: validated_bake_target=manifest.target.sha256
	record("exact_source_target_library_binding",binding_valid,{"bake_target":manifest.target.sha256,"tested_target":source_hashes[HERO],"compatible_derivative":source_hashes[HERO]!=manifest.target.sha256})
	record("unregistered_target_is_rejected",not target_binding("unregistered-target",manifest,compatibility))
	var changed_proof: Dictionary=compatibility.duplicate(true)
	for entry in changed_proof.get("compatible_targets",[]): entry.proof_sha256="changed-proof"
	if source_hashes[HERO]!=manifest.target.sha256: record("changed_compatibility_proof_is_rejected",not target_binding(source_hashes[HERO],manifest,changed_proof))
	record("original_rama_bytes_preserved",source_hashes[ORIGINAL]==ORIGINAL_SHA)
	hero=load(HERO).instantiate()
	var original: Node3D=load(ORIGINAL).instantiate()
	root.add_child(hero)
	root.add_child(original)
	await process_frame
	skeleton=find(hero,"Skeleton3D")
	animator=find(hero,"AnimationPlayer")
	var reference: Skeleton3D=find(original,"Skeleton3D")
	animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	var rests:=0.0
	var hierarchy_ok:=skeleton.get_bone_count()==164 and reference.get_bone_count()==164
	for bone in skeleton.get_bone_count():
		var name_:=skeleton.get_bone_name(bone)
		var other:=reference.find_bone(name_)
		if other<0:
			hierarchy_ok=false
			continue
		rests=maxf(rests,error_transform(skeleton.get_bone_global_rest(bone),reference.get_bone_global_rest(other)))
		var parent:=skeleton.get_bone_parent(bone)
		var other_parent:=reference.get_bone_parent(other)
		hierarchy_ok=hierarchy_ok and (skeleton.get_bone_name(parent) if parent>=0 else "")== (reference.get_bone_name(other_parent) if other_parent>=0 else "")
	record("original_rest_hierarchy_and_axes",hierarchy_ok and rests<=0.00005,{"max_rest_component_error":rests})
	record("original_nine_clips_available",animator.get_animation_list().size()==9,{"names":animator.get_animation_list()})
	var skin_stats:={"invalid":0,"rest_error":0.0,"weight_error":0.0,"vertices":0}
	skin_collect(hero,skin_stats)
	record("actual_full_rest_skin_reconstruction",skin_stats.invalid==0 and skin_stats.rest_error<=0.0002 and skin_stats.weight_error<=0.0002 and skin_stats.vertices>0,skin_stats)
	fixtures()
	var library: AnimationLibrary=load(library_path).duplicate(true)
	var names:=PackedStringArray(library.get_animation_list())
	var expected:=PackedStringArray(SPECS.keys())
	names.sort()
	expected.sort()
	record("declared_three_clips_only",names==expected)
	animator.add_animation_library("qa",library)
	for name_ in SPECS:
		if library.has_animation(name_): inspect_clip(name_,library.get_animation(name_))
	inspect_run_support()
	transition("fire",0.25,"tps_idle",0.125)
	transition("defeat",0.85,"tps_run",0.21)
	var stable:=true
	for path in source_hashes: stable=stable and source_hashes[path]==FileAccess.get_sha256(path)
	record("source_files_unchanged",stable)
	original.free()
	hero.free()
	finish(source_hashes)

func finish(hashes: Dictionary) -> void:
	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output.get_base_dir()))
	var file:=FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify({"passed":passed,"checks":checks,"measurements":measurements,"source_sha256":hashes,"test_sha256":FileAccess.get_sha256("res://tests/motion_retarget_cases.gd"),"godot":Engine.get_version_info(),"elapsed_seconds":(Time.get_ticks_msec()-started)/1000.0,"scope":"Reconstructed numerical QA by the baker implementation agent, with dense numerical and actual CPU-skinned geometry tests. Root agent provides separate rendered review. No rendered-quality, foot-lock, grip, gameplay-speed or hardware-performance acceptance."},"  ")+"\n")
	print("MOTION_QA ",JSON.stringify({"passed":passed,"checks":checks.size(),"report":output}))
	quit(0 if passed else 1)
