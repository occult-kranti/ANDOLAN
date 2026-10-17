extends SceneTree
## Read-only, independent continuity measurements of the loaded film skeletons.
## This detects numerical pose discontinuities; it does not certify art quality.

const FILM_PATH := "res://assets/cinematics/confluence-duel.json"
const RATE := 24
const EPSILON_SECONDS := 0.00001
const BOUNDARY_POSITION_LIMIT_M := 0.001
const BOUNDARY_ANGLE_LIMIT_DEG := 0.5
const FRAME_POSITION_REVIEW_M := 0.25
const FRAME_ANGLE_REVIEW_DEG := 45.0
const EXCLUDED_BONES := ["root", "bowstring"]

var output := ""
var viewer: Node
var manifest: Dictionary
var sources: Dictionary = {}
var actor_frames: Dictionary = {}
var bone_names: Dictionary = {}
var checks: Array[Dictionary] = []
var finite_transforms := 0
var total_transforms := 0
var report: Dictionary = {}

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("_run")

func _check(name_: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name": name_, "passed": passed, "details": details})

func _run() -> void:
	manifest=JSON.parse_string(FileAccess.get_file_as_string(FILM_PATH))
	for path in [FILM_PATH, "res://scripts/combat_film.gd", "res://scripts/cinematic_actor.gd", "res://scenes/combat_film.tscn", "res://tests/combat_motion_continuity.gd"]:
		sources[path]=FileAccess.get_sha256(path)
	for spec in manifest.actors:
		for path in [spec.model_path, spec.animation_library_path]: sources[path]=FileAccess.get_sha256(path)
	viewer=load("res://scenes/combat_film.tscn").instantiate()
	root.add_child(viewer)
	await process_frame
	viewer.set_playing(false)
	_check("actual viewer ready", viewer.ready_to_play, {"errors": viewer.errors})
	if not viewer.ready_to_play:
		await _finish()
		return
	viewer.sample_time(0, true)
	var actor_info := {}
	for actor_id in viewer.actors:
		var actor: Node3D=viewer.actors[actor_id]
		var skeleton: Skeleton3D=actor.skeleton
		# Fixed scene transform preserves metric model units while removing external
		# authored actor position/yaw completely from every measured sample.
		actor_frames[actor_id]=actor.global_transform.affine_inverse()*skeleton.global_transform
		bone_names[actor_id]=[]
		for index in skeleton.get_bone_count(): bone_names[actor_id].append(String(skeleton.get_bone_name(index)))
		var frame: Transform3D=actor_frames[actor_id]
		actor_info[actor_id]={"bones": skeleton.get_bone_count(), "measured_bones": skeleton.get_bone_count()-EXCLUDED_BONES.size(), "skeleton_to_actor_scale": _v(frame.basis.get_scale())}
	_check("comparison detects synthetic translation and rotation discontinuities", _detector_fixture(), {})
	var intervals := []
	var frame_alerts := []
	var frame_summary := _empty_metrics()
	var previous := _sample(0)
	var duration: float=manifest.duration_seconds
	for index in range(1, int(round(duration*RATE))+1):
		var time := float(index)/RATE
		var current := _sample(time)
		var metrics := _compare(previous, current, float(index-1)/RATE, time)
		_merge(frame_summary, metrics)
		intervals.append(metrics)
		if metrics.position_m.value>FRAME_POSITION_REVIEW_M or metrics.angle_deg.value>FRAME_ANGLE_REVIEW_DEG or metrics.local_angle_deg.value>FRAME_ANGLE_REVIEW_DEG:
			frame_alerts.append(metrics)
		previous=current
	var boundaries := []
	var boundary_summary := _empty_metrics()
	var boundary_failures := []
	for actor_id in viewer.actors:
		var times := {}
		for action in manifest.actions:
			if action.actor_id!=actor_id: continue
			for time in [float(action.t_seconds), float(action.t_seconds+action.duration_seconds)]:
				if time>0 and time<duration: times[time]=true
		var ordered: Array=times.keys()
		ordered.sort()
		for time in ordered:
			var before := _sample(time-EPSILON_SECONDS)
			var at := _sample(time)
			var after := _sample(time+EPSILON_SECONDS)
			var left := _compare(before, at, time-EPSILON_SECONDS, time, actor_id)
			var right := _compare(at, after, time, time+EPSILON_SECONDS, actor_id)
			var across := _compare(before, after, time-EPSILON_SECONDS, time+EPSILON_SECONDS, actor_id)
			var maximum := _empty_metrics()
			for metrics in [left, right, across]: _merge(maximum, metrics)
			_merge(boundary_summary, maximum)
			var passed: bool=maximum.position_m.value<=BOUNDARY_POSITION_LIMIT_M and maximum.angle_deg.value<=BOUNDARY_ANGLE_LIMIT_DEG and maximum.local_angle_deg.value<=BOUNDARY_ANGLE_LIMIT_DEG
			var item := {"actor": actor_id, "time": time, "before_action": _action_at(actor_id,time-EPSILON_SECONDS), "after_action": _action_at(actor_id,time+EPSILON_SECONDS), "passed": passed, "left": left, "right": right, "across": across}
			boundaries.append(item)
			if not passed: boundary_failures.append(item)
	_check("all sampled included bone transforms finite", finite_transforms==total_transforms, {"finite": finite_transforms, "total": total_transforms})
	_check("all two-sided action boundary poses continuous within fixed tolerance", boundary_failures.is_empty(), {"boundaries": boundaries.size(), "failures": boundary_failures})
	var unchanged := true
	for path in sources: unchanged=unchanged and sources[path]==FileAccess.get_sha256(path)
	_check("runtime, assets, manifest, and probe source unchanged during sampling", unchanged)
	report={
		"scope": "Actual loaded skeleton pose continuity only; no gameplay physics, render beauty, cloth, or combat correctness claim.",
		"coordinate_system": "Fixed skeleton-to-actor transform in metres; external actor trajectory/yaw and all camera motion excluded. Joint angular deltas are reported both in actor space and relative to the joint parent.",
		"excluded_bones": EXCLUDED_BONES,
		"body_branch_controls": "pelvis.L, pelvis.R, and spine05 intentionally translate together during crouch; retained here because continuity, unlike rest segment length, applies to those controls.",
		"actors": actor_info, "sample_rate_hz": RATE, "sample_count": int(round(duration*RATE))+1,
		"thresholds": {
			"action_boundary_epsilon_seconds": EPSILON_SECONDS,
			"boundary_position_limit_m": BOUNDARY_POSITION_LIMIT_M,
			"boundary_angle_limit_deg": BOUNDARY_ANGLE_LIMIT_DEG,
			"boundary_reason": "A 1 mm / 0.5 degree jump across at most 20 microseconds is far above floating-point pose noise, yet below a visible authored animation pop. No actor pose cuts are declared, so this is a failure gate fixed before measurement.",
			"frame_position_review_m": FRAME_POSITION_REVIEW_M,
			"frame_angle_review_deg": FRAME_ANGLE_REVIEW_DEG,
			"frame_reason": "At 24 Hz these are 6 m/s joint travel or 1080 degrees/s rotation. Fast combat gestures can legitimately exceed them; alerts require visual review and do not by themselves establish a discontinuity. These review thresholds were set before measurement."
		},
		"successive_frame_maxima": frame_summary, "successive_frame_review_alerts": frame_alerts,
		"boundary_maxima": boundary_summary, "boundaries": boundaries,
		"successive_frame_intervals": intervals
	}
	await _finish()

func _v(vector: Vector3) -> Array:
	return [vector.x, vector.y, vector.z]

func _sample(time: float) -> Dictionary:
	viewer.sample_time(time,true)
	var result := {}
	for actor_id in viewer.actors:
		var skeleton: Skeleton3D=viewer.actors[actor_id].skeleton
		var frame: Transform3D=actor_frames[actor_id]
		skeleton.force_update_all_bone_transforms()
		var poses := []
		for index in skeleton.get_bone_count():
			if bone_names[actor_id][index] in EXCLUDED_BONES:
				poses.append(null)
				continue
			var global_pose: Transform3D=frame*skeleton.get_bone_global_pose(index)
			var local_pose: Transform3D=skeleton.get_bone_pose(index)
			total_transforms+=1
			if global_pose.is_finite() and local_pose.is_finite(): finite_transforms+=1
			poses.append({"global": global_pose, "local": local_pose})
		result[actor_id]=poses
	return result

func _empty_metrics() -> Dictionary:
	return {"position_m": {"value": 0.0}, "angle_deg": {"value": 0.0}, "local_angle_deg": {"value": 0.0}}

func _angle(a: Basis, b: Basis) -> float:
	var qa := a.orthonormalized().get_rotation_quaternion().normalized()
	var qb := b.orthonormalized().get_rotation_quaternion().normalized()
	# atan2 of the relative quaternion remains stable near zero, unlike acos(dot)
	# in Godot's single-precision Vector/Quaternion storage. abs(w) treats q and
	# -q as the same orientation and reports the shortest angular difference.
	var relative := (qa.inverse()*qb).normalized()
	var sine := Vector3(relative.x,relative.y,relative.z).length()
	return rad_to_deg(2.0*atan2(sine,absf(relative.w)))

func _compare(before: Dictionary, after: Dictionary, t0: float, t1: float, actor_filter: String="") -> Dictionary:
	var metrics := _empty_metrics()
	for actor_id in before:
		if not actor_filter.is_empty() and actor_filter!=actor_id: continue
		for index in before[actor_id].size():
			if before[actor_id][index]==null: continue
			var a: Transform3D=before[actor_id][index].global
			var b: Transform3D=after[actor_id][index].global
			var local_a: Transform3D=before[actor_id][index].local
			var local_b: Transform3D=after[actor_id][index].local
			var values := {"position_m": a.origin.distance_to(b.origin), "angle_deg": _angle(a.basis,b.basis), "local_angle_deg": _angle(local_a.basis,local_b.basis)}
			for key in values:
				if values[key]>metrics[key].value:
					metrics[key]={"value": values[key], "actor": actor_id, "bone": bone_names[actor_id][index], "from_seconds": t0, "to_seconds": t1, "from_action": _action_at(actor_id,t0), "to_action": _action_at(actor_id,t1)}
	return metrics

func _merge(destination: Dictionary, source: Dictionary) -> void:
	for key in ["position_m", "angle_deg", "local_angle_deg"]:
		if source[key].value>destination[key].value: destination[key]=source[key].duplicate(true)

func _action_at(actor_id: String, time: float) -> String:
	for action in manifest.actions:
		if action.actor_id==actor_id and time>=action.t_seconds and (time<action.t_seconds+action.duration_seconds or (time==manifest.duration_seconds and time==action.t_seconds+action.duration_seconds)):
			return action.id
	return "ready-gap"

func _detector_fixture() -> bool:
	var origin := Transform3D.IDENTITY
	var translated := Transform3D(Basis.IDENTITY, Vector3(.002,0,0))
	var rotated := Transform3D(Basis(Vector3.UP,deg_to_rad(1.0)),Vector3.ZERO)
	return origin.origin.distance_to(translated.origin)>BOUNDARY_POSITION_LIMIT_M and _angle(origin.basis,rotated.basis)>BOUNDARY_ANGLE_LIMIT_DEG and _angle(origin.basis,origin.basis)<BOUNDARY_ANGLE_LIMIT_DEG

func _finish() -> void:
	if viewer:
		viewer.set_playing(false)
		if viewer.audio_player: viewer.audio_player.stop()
		viewer.queue_free()
		await process_frame
		await create_timer(.15).timeout
	var passed := true
	for check in checks: passed=passed and check.passed
	report["schema_version"]=1
	report["passed"]=passed
	report["checks"]=checks
	report["sources_sha256"]=sources
	report["godot_version"]=Engine.get_version_info().string
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		file.store_string(JSON.stringify(report,"  ")+"\n")
	print("COMBAT_MOTION_CONTINUITY "+JSON.stringify({"passed": passed, "checks": checks.size(), "successive_frame_maxima": report.get("successive_frame_maxima",{}), "boundary_maxima": report.get("boundary_maxima",{}), "report": output}))
	quit(0 if passed else 1)
