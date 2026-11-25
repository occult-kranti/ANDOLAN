extends SceneTree
## Pack Blender parent-relative samples into a native animation library.

const VISUAL := "res://assets/heroes/hanuman/hanuman.glb"
const VISUAL_SHA := "9de9e032d55685dffd51734bef98c241024283c5d23767646b5c68ca782dec7e"
const MOVE_NAMES := ["fire", "cast2", "cast1", "tail_sweep", "mountain_pulse"]


func _initialize() -> void:
	execute.call_deferred()


func fail(message: String) -> void:
	push_error(message)
	quit(1)


func execute() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 2:
		fail("Pass the Blender tracks JSON and output .tres after --.")
		return
	if FileAccess.get_sha256(VISUAL) != VISUAL_SHA:
		fail("The R5 trial visual must match its pinned Blender source.")
		return
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
	if not data is Dictionary or not data.get("clips") is Dictionary or data.clips.size() != MOVE_NAMES.size():
		fail("Expected the five Blender-authored Trial actions.")
		return
	var packed := load(VISUAL) as PackedScene
	var actor := packed.instantiate()
	root.add_child(actor)
	var mixer := actor.find_children("*", "AnimationPlayer", true, false)[0] as AnimationPlayer
	var rig := actor.find_children("*", "Skeleton3D", true, false)[0] as Skeleton3D
	var path := str(mixer.get_node(mixer.root_node).get_path_to(rig))
	var library := AnimationLibrary.new()
	var receipt := {}
	for name_ in MOVE_NAMES:
		if not mixer.has_animation(name_) or not data.clips.get(name_) is Dictionary:
			fail("Missing source or authored action: " + name_)
			return
		var source := mixer.get_animation(name_)
		var revised := source.duplicate(true) as Animation
		var move: Dictionary = data.clips[name_]
		if not replace_tracks(revised, rig, path, move):
			fail("Invalid Blender transform sample in " + name_)
			return
		revised.set_meta(&"hanuman_release_phase", float(move.release))
		if move.impact != null:
			revised.set_meta(&"hanuman_impact_phase", float(move.impact))
		if library.add_animation(name_, revised) != OK:
			fail("Could not add the packed action: " + name_)
			return
		receipt[name_] = {
			"duration_s": revised.length,
			"authored_phases": move.phases.size(),
			"source_frame_range": move.source_frames,
			"release_phase": move.release,
			"impact_phase": move.impact,
		}
	library.set_meta(&"blender_source_sha256", String(data.source_sha256))
	library.set_meta(&"visual_source_sha256", VISUAL_SHA)
	var error := ResourceSaver.save(library, args[1])
	if error != OK:
		fail("Could not save the native motion library: " + error_string(error))
		return
	print("HANUMAN_MOTION ", JSON.stringify(receipt))
	actor.queue_free()
	quit()


func replace_tracks(clip: Animation, rig: Skeleton3D, path: String, move: Dictionary) -> bool:
	var phases: Array = move.phases
	if phases.size() < 3 or float(phases.front()) != 0.0 or float(phases.back()) != 1.0:
		return false
	for key in range(1, phases.size()):
		if float(phases[key]) <= float(phases[key - 1]):
			return false
	for property: String in ["rotation", "position"]:
		var channels: Dictionary = move[property]
		var track_type := Animation.TYPE_ROTATION_3D if property == "rotation" else Animation.TYPE_POSITION_3D
		for name_: String in channels:
			var samples: Array = channels[name_]
			if name_ == "root" or rig.find_bone(name_) < 0 or samples.size() != phases.size():
				return false
			var track_path := NodePath(path + ":" + name_)
			var index := clip.find_track(track_path, track_type)
			if index < 0:
				index = clip.add_track(track_type)
				clip.track_set_path(index, track_path)
			while clip.track_get_key_count(index) > 0:
				clip.track_remove_key(index, clip.track_get_key_count(index) - 1)
			clip.track_set_interpolation_type(index, Animation.INTERPOLATION_LINEAR)
			clip.track_set_interpolation_loop_wrap(index, false)
			for key in phases.size():
				var values: Array = samples[key]
				var time := float(phases[key]) * clip.length
				if property == "rotation":
					var value := Quaternion(values[0], values[1], values[2], values[3])
					if not value.is_finite() or absf(value.length_squared() - 1.0) > .002:
						return false
					clip.rotation_track_insert_key(index, time, value.normalized())
				else:
					var value := Vector3(values[0], values[1], values[2])
					if not value.is_finite():
						return false
					clip.position_track_insert_key(index, time, value)
	return true
