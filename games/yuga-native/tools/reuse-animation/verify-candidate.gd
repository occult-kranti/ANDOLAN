extends SceneTree
## In-memory Godot interpolation comparison; no candidate resource is saved.

func _initialize() -> void:
	var args := {}
	for item in OS.get_cmdline_user_args():
		var pair := item.trim_prefix("--").split("=", true, 1)
		if pair.size() == 2: args[pair[0]] = pair[1]
	for required in ["input", "candidate"]:
		if not args.has(required):
			printerr("Pass --input=/absolute/library.tres --candidate=/absolute/candidate.json")
			quit(2)
			return
	var source: AnimationLibrary = load(args.input)
	var proposed: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args.candidate))
	var expected_hash := FileAccess.get_sha256(args.input)
	if proposed.get("source_sha256", "") != expected_hash or proposed.get("runtime_ready", true):
		printerr("Candidate must be an offline proposal for this exact library.")
		quit(2)
		return
	var seen := {}
	for clip_data in proposed.clips:
		if seen.has(clip_data.name) or not source.has_animation(clip_data.name):
			printerr("Candidate clip names must be unique and match the source library exactly.")
			quit(2)
			return
		seen[clip_data.name] = true
	if seen.size() != source.get_animation_list().size():
		printerr("Candidate omits source clips.")
		quit(2)
		return
	var passed := true
	var rows := []
	var probes := 0
	var max_rotation := 0.0
	var max_position := 0.0
	for clip_data in proposed.clips:
		var original := source.get_animation(clip_data.name)
		var candidate := Animation.new()
		candidate.length = clip_data.length
		candidate.loop_mode = clip_data.loop_mode
		var clip_passed: bool = original.length == candidate.length and original.loop_mode == candidate.loop_mode and original.get_track_count() == clip_data.tracks.size()
		for track_data in clip_data.tracks:
			var index: int = track_data.index
			if not valid_track_contract(original, track_data):
				printerr("Candidate changes track kind, interpolation, loop-wrap, enabled state or key-transition contract.")
				quit(2)
				return
			var kind: int = Animation.TYPE_ROTATION_3D if track_data.kind == "rotation" else Animation.TYPE_POSITION_3D
			var destination := candidate.add_track(kind)
			clip_passed = clip_passed and index == destination and original.track_get_type(index) == kind and str(original.track_get_path(index)) == track_data.path
			candidate.track_set_path(destination, NodePath(track_data.path))
			candidate.track_set_interpolation_type(destination, track_data.interpolation)
			candidate.track_set_interpolation_loop_wrap(destination, track_data.loop_wrap)
			candidate.track_set_enabled(destination, track_data.enabled)
			for key in track_data.times.size():
				var value: Array = track_data.values[key]
				if kind == Animation.TYPE_ROTATION_3D:
					candidate.rotation_track_insert_key(destination, track_data.times[key], Quaternion(value[0],value[1],value[2],value[3]))
				else:
					candidate.position_track_insert_key(destination, track_data.times[key], Vector3(value[0],value[1],value[2]))
			var moments: Array[float] = [0.0, original.length]
			for key in original.track_get_key_count(index)-1:
				var start := original.track_get_key_time(index,key)
				var end := original.track_get_key_time(index,key+1)
				for part in range(9): moments.append(lerpf(start,end,part/8.0))
			# Exercise Godot's loop interpolation on both sides of the boundary.
			if original.loop_mode == Animation.LOOP_LINEAR:
				for fraction in [-0.00001,0.00001,0.99999,1.00001]: moments.append(original.length*fraction)
			var maximum := 0.0
			for moment in moments:
				var error := 0.0
				if kind == Animation.TYPE_ROTATION_3D:
					error = angle(original.rotation_track_interpolate(index,moment),candidate.rotation_track_interpolate(destination,moment))
					max_rotation = maxf(max_rotation,error)
				else:
					error = original.position_track_interpolate(index,moment).distance_to(candidate.position_track_interpolate(destination,moment))
					max_position = maxf(max_position,error)
				maximum = maxf(maximum,error)
				probes += 1
			var tolerance := deg_to_rad(.01) if kind == Animation.TYPE_ROTATION_3D else .00001
			clip_passed = clip_passed and is_finite(maximum) and maximum <= tolerance
		rows.append({"name":clip_data.name,"passed":clip_passed})
		passed = passed and clip_passed
	passed = passed and source.get_animation_list().size() == proposed.clips.size() and FileAccess.get_sha256(args.input) == expected_hash
	print(JSON.stringify({"schema":1,"passed":passed,"input_sha256":expected_hash,
		"candidate_sha256":FileAccess.get_sha256(args.candidate),
		"verifier_sha256":FileAccess.get_sha256(get_script().resource_path),
		"engine":Engine.get_version_info(),"clips":rows,"probes":probes,
		"max_rotation_radians":max_rotation,"max_position_m":max_position,
		"runtime_asset_changed":false,"scope":"In-memory Godot interpolation including loop-boundary probes; no skin/contact/events/render/performance acceptance."}))
	quit(0 if passed else 1)

func valid_track_contract(source: Animation, data: Dictionary) -> bool:
	var index: int = data.index
	if index < 0 or index >= source.get_track_count() or data.kind not in ["rotation", "position"]:
		return false
	var expected: int = Animation.TYPE_ROTATION_3D if data.kind == "rotation" else Animation.TYPE_POSITION_3D
	if expected != source.track_get_type(index) or data.interpolation != Animation.INTERPOLATION_LINEAR or data.interpolation != source.track_get_interpolation_type(index):
		return false
	if data.loop_wrap != source.track_get_interpolation_loop_wrap(index) or data.enabled != source.track_is_enabled(index) or not data.enabled:
		return false
	if data.transitions.size() != data.times.size() or data.values.size() != data.times.size():
		return false
	for transition in data.transitions:
		if transition != 1.0: return false
	for key in source.track_get_key_count(index):
		if source.track_get_key_transition(index, key) != 1.0: return false
	return true

func angle(a: Quaternion, b: Quaternion) -> float:
	a = a.normalized()
	b = b.normalized()
	if a.dot(b) < 0: b = -b
	var difference := sqrt(pow(a.x-b.x,2)+pow(a.y-b.y,2)+pow(a.z-b.z,2)+pow(a.w-b.w,2))
	var together := sqrt(pow(a.x+b.x,2)+pow(a.y+b.y,2)+pow(a.z+b.z,2)+pow(a.w+b.w,2))
	return 4*atan2(difference,together)
