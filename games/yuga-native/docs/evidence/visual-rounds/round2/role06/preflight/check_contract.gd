extends "res://tools/visual-rounds/capture.gd"
## Cheap actual-runtime check before spending the owned renderer lane.
func run() -> void:
	var report_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	for index in 8: await physics_frame
	player = scene.player
	scene.start_training()
	for index in 8: await physics_frame
	paused = true
	scene.set_process(false); scene.set_physics_process(false)
	review_camera = Camera3D.new(); scene.add_child(review_camera)
	face_camera("three-quarter-left"); review_camera.make_current()
	player.pitch = -.25; player.yaw = 0.0; player.pivot.rotation = Vector3(player.pitch,player.yaw,0)
	player.rama_face.reset("capture preflight")
	for tick in 181: player.rama_face.update_facial(1.0/60.0,{"alive":true,"paused":false,"effort":0.0})
	scene.rama_runtime.combat_event.connect(record_event)
	paused = false
	var kodanda: Dictionary = scene.rama_runtime.cast_ability("kodanda")
	var piercing: Dictionary = {}
	var cancelled := false
	var minimum_facing := 1.0
	var max_blink := 0.0
	for tick in 72:
		if tick == 30: piercing = scene.rama_runtime.cast_ability("piercing_dawn")
		if tick == 48: cancelled = scene.rama_runtime.kit.cancel_windup("round2_face_probe")
		await physics_frame
		minimum_facing = minf(minimum_facing,player.visual.global_basis.z.dot((review_camera.global_position-player.global_position).normalized()))
		max_blink = maxf(max_blink,player.rama_face.report().weights.rama_blink_left)
	var complete: bool = kodanda.get("accepted",false) and piercing.get("accepted",false) and cancelled and minimum_facing>=.25 and max_blink>=.98
	var report := {"complete":complete,"kodanda":normal(kodanda),"piercing":normal(piercing),"cancelled":cancelled,"minimum_facing_dot":minimum_facing,"max_blink":max_blink,"final_face":player.rama_face.report(),"events":events,"scope":"Headless runtime fixture preflight only; original framebuffer review remains required."}
	if not report_path.is_empty(): FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	print("VISUAL_CONTRACT_PREFLIGHT ",complete," facing=",minimum_facing," blink=",max_blink)
	scene.queue_free()
	for index in 3: await process_frame
	quit(0 if complete else 1)
