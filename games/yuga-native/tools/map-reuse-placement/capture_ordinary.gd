extends "res://tools/map-reuse-placement/capture.gd"
## Corrects initial held A-pose by evaluating production idle, then views carved front.
func hashes()->Dictionary:
	var result:=super.hashes();result["res://tools/map-reuse-placement/capture_ordinary.gd"]=FileAccess.get_sha256("res://tools/map-reuse-placement/capture_ordinary.gd");return result
func views()->Array[Dictionary]:return [{"id":"south-ordinary-day","phase":0.0,"ordinary":true},{"id":"south-ordinary-night","phase":1.0,"ordinary":true}]
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--selection="):selection_path=arg.trim_prefix("--selection=")
		elif arg=="--preflight":preflight=true
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or not FileAccess.file_exists(selection_path):push_error("Fresh output/selection required");quit(1);return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus"):push_error("Actual Forward+ required");quit(1);return
	source_hashes=hashes();root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS;root.msaa_3d=Viewport.MSAA_2X
	if not preflight:root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate();scene.set("lanka_lane_gate_enabled",false);root.add_child(scene);current_scene=scene
	await draw_frames(8);check("actual current canonical world ready",scene.world_ready and scene.player.model_ready)
	if not checks[-1].passed:await finish();return
	scene.set_overview(false);scene.set_paused(false);scene.set_review_phase(0);scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world)
	for water in scene.manifest.waters:
		var material:ShaderMaterial=scene.world.get_node(water.id).get_active_material(0);material.set_shader_parameter("animation_speed",0.0)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	scene.player.global_position=Vector3(-40,.04,-32);scene.player.velocity=Vector3.ZERO;scene.player.yaw=0;scene.player.pitch=-.10;scene.player._update_camera();scene.player.visual.rotation.y=PI
	var before_pose:String=freeze_state().hero_pose_sha256
	scene.player._update_rama_motion(1.0/60);scene.player.rama_motion.evaluate_pose()
	await physics_frame;await physics_frame;await draw_frames(2)
	check("production idle was actually evaluated beyond held import rest pose",freeze_state().hero_pose_sha256!=before_pose and scene.player.rama_motion.diagnostics().finite)
	ordinary_camera=scene.player.camera.global_transform
	camera=Camera3D.new();camera.fov=scene.player.camera.fov;camera.near=scene.player.camera.near;camera.far=scene.player.camera.far;scene.add_child(camera);camera.current=true
	held=freeze_state();gather_bodies(scene.world,original_body_ids);await install_candidate()
	for view in views():await capture("reused-gate",view)
	await finish()
func finish()->void:
	check("two corrected ordinary states completed",shots.size()==2)
	var after:=hashes();check("all actual sources unchanged during correction",source_hashes==after)
	var passed:=checks.all(func(row):return row.passed)
	var report:={"complete":passed,"preflight":preflight,"actual_image_count":0 if preflight else shots.size(),"shots":shots,"route_frames":[],"checks":checks,"composition":placement_result.get("report",{}),"held_state":held,"ordinary_camera":transform(ordinary_camera),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"engine":Engine.get_version_info(),"source_sha256":source_hashes,"source_after_sha256":after,"canonical_enabled":false,"scope":"Two corrected actual ordinary southbound views of same unchanged gate composition. Feet(-40,.04,-32), yaw0,pitch-.10, actual65degree3.5m shoulder camera/far380. Existing player._update_rama_motion(1/60) and rama_motion.evaluate_pose() evaluate production idle before hold; no fabricated bone pose. These are new camera views, not relabelled northbound R1 baseline pairs. Original R1 A-pose failure remains diagnostic; route72frames separate."}
	FileAccess.open(output.path_join("preflight.json" if preflight else "capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	if is_instance_valid(scene):scene.queue_free()
	for unused in 8:await process_frame
	print("LANKA_ORDINARY_CORRECTION_COMPLETE ",passed);quit(0 if passed else 1)
