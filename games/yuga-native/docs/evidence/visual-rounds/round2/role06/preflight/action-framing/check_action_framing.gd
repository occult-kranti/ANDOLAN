extends "res://tools/visual-rounds/capture.gd"
## No renderer/import: exercise real casts, then project actual skinned geometry.
func run() -> void:
	var report_path := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	root.size = SIZE; root.content_scale_size = SIZE
	scene = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	for index in 8: await physics_frame
	player = scene.player
	scene.start_training()
	for index in 8: await physics_frame
	scene.set_process(false); scene.set_physics_process(false)
	review_camera = Camera3D.new(); scene.add_child(review_camera)
	var results := []
	var complete := true
	for id in ABILITY_IDS:
		paused = true
		scene.reset_training(); scene.start_training()
		player.pitch = -.25; player.yaw = 0.0
		player.pivot.rotation = Vector3(player.pitch,player.yaw,0)
		review_camera.fov = 32.0
		face_camera("three-quarter-left"); review_camera.make_current()
		paused = false
		var cast: Dictionary = scene.rama_runtime.cast_ability(id)
		var windup_ticks: int = {"kodanda":6,"piercing_dawn":36,"measured_step":4,"guardian_circle":30,"dawn_volley":54}[id]
		for tick in windup_ticks: await physics_frame
		paused = true
		var previous := face_neck_bounds(review_camera)
		action_camera()
		var bounds := face_neck_bounds(review_camera)
		complete = complete and cast.get("accepted",false) and bounds.passed and player.rama_motion.diagnostics().stage == "windup"
		results.append({"id":id,"cast":normal(cast),"old_camera_bounds":previous,"corrected_camera_bounds":bounds,"camera":{"transform":normal(review_camera.global_transform),"fov":review_camera.fov},"motion":player.rama_motion.diagnostics()})
		print("ACTION_FRAME_PREFLIGHT ",id," ",bounds)
	var report := {"complete":complete,"results":results,"asset_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"harness_sha256":FileAccess.get_sha256("res://tools/visual-rounds/capture.gd"),"scope":"Headless real cast and actual imported skin projection; every rendered frame must repeat gate and still needs original-pixel review."}
	FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ",true,true)+"\n")
	paused = false; scene.queue_free()
	for index in 3: await process_frame
	quit(0 if complete else 1)
