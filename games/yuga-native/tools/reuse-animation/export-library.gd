extends SceneTree
## Read the existing library through Godot; write neutral audit data, never assets.

func _initialize() -> void:
	var input := ""
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--input="): input = arg.trim_prefix("--input=")
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	if not input.is_absolute_path() or not output.is_absolute_path() or FileAccess.file_exists(output):
		fail("Use an absolute input and a fresh absolute output JSON path.")
		return
	# A lexical outside-repository path is insufficient when a parent is a link.
	var directory := DirAccess.open("/")
	var component := output.simplify_path()
	while component != "/" and not component.is_empty():
		if directory.is_link(component):
			fail("Output and its parent directories must not be symbolic links.")
			return
		component = component.get_base_dir()
	var repository := ProjectSettings.globalize_path("res://../..").simplify_path().trim_suffix("/")
	if output.simplify_path().begins_with(repository + "/") or output.get_extension() != "json":
		fail("Audit output must be JSON outside the repository.")
		return
	var before := FileAccess.get_sha256(input)
	var library = load(input)
	if not library is AnimationLibrary:
		fail("Input must be an AnimationLibrary.")
		return
	var clips := []
	for clip_name in library.get_animation_list():
		var clip: Animation = library.get_animation(clip_name)
		var tracks := []
		for index in clip.get_track_count():
			var type: int = clip.track_get_type(index)
			if type not in [Animation.TYPE_ROTATION_3D, Animation.TYPE_POSITION_3D]:
				fail("Unsupported track type; event/method/scale tracks require a separate adapter.")
				return
			var times := []
			var values := []
			var transitions := []
			for key in clip.track_get_key_count(index):
				times.append(clip.track_get_key_time(index, key))
				transitions.append(clip.track_get_key_transition(index, key))
				var value = clip.track_get_key_value(index, key)
				values.append([value.x, value.y, value.z, value.w] if type == Animation.TYPE_ROTATION_3D else [value.x, value.y, value.z])
			tracks.append({"index": index, "path": str(clip.track_get_path(index)),
				"kind": "rotation" if type == Animation.TYPE_ROTATION_3D else "position",
				"interpolation": clip.track_get_interpolation_type(index),
				"loop_wrap": clip.track_get_interpolation_loop_wrap(index),
				"enabled": clip.track_is_enabled(index), "times": times,
				"values": values, "transitions": transitions})
		clips.append({"name": str(clip_name), "length": clip.length,
			"loop_mode": clip.loop_mode, "tracks": tracks})
	if FileAccess.get_sha256(input) != before:
		fail("Input changed during extraction.")
		return
	var file := FileAccess.open(output, FileAccess.WRITE)
	if file == null:
		fail("Cannot create output.")
		return
	file.store_string(JSON.stringify({"schema": 1, "engine": Engine.get_version_info(),
		"input_path": input, "input_sha256": before,
		"extractor_sha256": FileAccess.get_sha256(get_script().resource_path),
		"scope": "Godot resource extraction only; no rendering or candidate playback.", "clips": clips}, "  ") + "\n")
	file.close()
	print(JSON.stringify({"passed": true, "clips": clips.size(), "output": output, "input_sha256": before}))
	quit(0)

func fail(message: String) -> void:
	printerr(message)
	quit(2)
