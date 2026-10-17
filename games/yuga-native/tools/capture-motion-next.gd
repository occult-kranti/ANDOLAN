extends "res://tools/capture-hero.gd"
## Native lower-body clips with the optional carry overlay. Actual renderer only.
const CarryPose := preload("res://scripts/hero_pose.gd")
var carry: SkeletonModifier3D
var pins := {}
var sample_hz := 24.0
var modified_hand := Vector3.ZERO
var sequence := [
	{"clip":"idle","seconds":1.5,"close":false},
	{"clip":"run","seconds":1.7,"close":false},
	{"clip":"fire","seconds":0.95,"close":false,"trigger_frames":[0,6,12]},
	{"clip":"idle","seconds":1.35,"close":false},
	{"clip":"idle","seconds":1.5,"close":true},
]

func _run() -> void:
	width=640
	height=640
	timeout_seconds=600.0
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output_path=arg.trim_prefix("--output=")
		elif arg.begins_with("--asset="): asset_path=arg.trim_prefix("--asset=")
		else: failure="Unknown argument: "+arg
	if not failure.is_empty() or not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path):
		push_error("Require a new absolute output directory and known arguments. "+failure)
		quit(1)
		return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name()=="headless" or not _validate_import():
		failure="Require actual renderer and current imported hero. "+failure
		_finish(false)
		return
	for path in [asset_path,"res://scripts/hero_pose.gd","res://scripts/player.gd","res://tools/capture-motion-next.gd","res://tools/capture-hero.gd"]:
		pins[path]=FileAccess.get_sha256(path)
	source_sha_before=pins[asset_path]
	root.size=Vector2i(width,height)
	root.content_scale_size=root.size
	root.msaa_3d=Viewport.MSAA_2X
	root.title="YUGA / Native Carry and Grip Review"
	root.show()
	_make_studio()
	hero=load(asset_path).instantiate()
	studio.add_child(hero)
	animator=_find_animation(hero)
	_collect_skeletons(hero)
	carry=CarryPose.new()
	if not animator or skeletons.is_empty() or not carry.configure(hero,animator):
		failure="Cannot configure native carry overlay."
		if carry.get_parent()==null: carry.free()
		_finish(false)
		return
	animator.callback_mode_process=AnimationMixer.ANIMATION_CALLBACK_MODE_PROCESS_MANUAL
	carry.modification_processed.connect(_capture_hand)
	for name_: StringName in animator.get_animation_list():
		var simple := String(name_).get_file().to_lower()
		clips[simple]=name_
		# Match player.gd: imported GLB clips do not declare Godot loop mode.
		if simple in ["idle","run"]: animator.get_animation(name_).loop_mode=Animation.LOOP_LINEAR
	for spec in sequence:
		if not clips.has(spec.clip):
			failure="Missing original native clip: "+spec.clip
			_finish(false)
			return
	camera.position=Vector3(sin(deg_to_rad(33.0))*STUDIO_CAMERA_DISTANCE,1.10,cos(deg_to_rad(33.0))*STUDIO_CAMERA_DISTANCE)
	camera.look_at(STUDIO_CAMERA_TARGET)
	await _draw_frames(3)
	var index := 0
	var current_clip := ""
	for part in sequence.size():
		var spec: Dictionary=sequence[part]
		var last_trigger := -100
		if spec.close:
			# Camera is static for this complete grip take, avoiding tracking jitter.
			var hand := modified_hand
			camera.position=hand+Vector3(-.75,.10,1.0)
			camera.look_at(hand+Vector3(0,-.04,.03))
			camera.fov=32.0
		for frame in range(ceili(spec.seconds*sample_hz)):
			var triggered: bool=frame in spec.get("trigger_frames",[])
			if triggered: last_trigger=frame
			var action_active: bool=spec.clip=="fire" and (frame-last_trigger)/sample_hz<.32
			var clip: String=spec.clip if spec.clip!="fire" or action_active else "idle"
			if current_clip!=clip:
				var blend := 0.055 if clip=="fire" else (0.16 if clip=="run" else 0.20)
				animator.play(clips[clip],0.0 if current_clip.is_empty() else blend)
				current_clip=clip
			if triggered: animator.seek(0.0,true)
			carry.set_state(clip,1.0/sample_hz,"ground",action_active)
			animator.advance(0.0 if index==0 or triggered else 1.0/sample_hz)
			footer.text="Original %s / carry %.2f / %s\n24 Hz sequential poses; native legs; visual review required" % [clip,carry.weight,"grip detail" if spec.close else "full body"]
			await _draw_frames(1)
			if Time.get_ticks_msec()-started_ms>timeout_seconds*1000.0:
				failure="Capture exceeded wall-time budget."
				_finish(false)
				return
			var pixels:=root.get_texture().get_image()
			var file_name:="frame-%05d.png" % index
			if pixels.is_empty() or pixels.save_png(output_path.path_join(file_name))!=OK:
				failure="Failed to save actual frame."
				_finish(false)
				return
			shots.append({"file":file_name,"sha256":FileAccess.get_sha256(output_path.path_join(file_name)),"segment":part,"clip":clip,
				"close":spec.close,"sample_time_seconds":frame/sample_hz,"animation_seconds":animator.current_animation_position,"triggered":triggered,"action_active":action_active,
				"carry":carry.diagnostics(),"camera_position":_vector(camera.position),"rendered_frame_counter":Engine.get_frames_drawn(),
				"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
				"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),
				"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)})
			index+=1
	for path in pins:
		if FileAccess.get_sha256(path)!=pins[path]: failure="Source changed during capture: "+path
	_finish(failure.is_empty())

func _capture_hand() -> void:
	var skeleton: Skeleton3D=skeletons[0]
	modified_hand=skeleton.global_transform*skeleton.get_bone_global_pose(skeleton.find_bone("wrist.R")).origin

func _finish(success: bool) -> void:
	if completed: return
	completed=true
	if output_path.is_absolute_path() and DirAccess.dir_exists_absolute(output_path):
		var report:={"complete":success,"failure":failure,"sources":pins,"imported_resource":imported_resource,
			"engine":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),
			"display":DisplayServer.get_name(),"sample_hz":sample_hz,"width":width,"height":height,"sequence":sequence,"frames":shots,
			"scope":"Actual sequential native idle-run-fire-idle upper-body carry trial plus grip close-up. Native lower-body clips preserved; TPS run is not used. Manual24Hz poses, not hardware FPS, gameplay-speed foot locking, listening or human acceptance."}
		var file:=FileAccess.open(output_path.path_join("motion-next-render-review.json"),FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
	print("MOTION_NEXT_CAPTURE ","PASS" if success else "FAIL"," ",shots.size()," frames ",failure)
	quit(0 if success else 1)
