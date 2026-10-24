extends SceneTree
## Matched actual native motion, normal advancing60Hz samples, no event resample.
const HERO:="res://assets/heroes/rama-hero.glb"
const BASELINE:="res://docs/research/reuse-next-ten/W5/source/rama_motion.baseline.gd"
const CANDIDATE:="res://tools/hero-family-reuse/rama_motion_warm_entry_candidate.gd"
const Production=preload("res://scripts/production_lighting.gd")
const Surface=preload("res://scripts/rama_surface_materials.gd")
const Secondary=preload("res://scripts/rama_secondary_motion.gd")
const Finish=preload("res://scripts/rama_surface_finish.gd")
const Face=preload("res://scripts/rama_facial_performance.gd")
var output:=""
var frame_count:=36
var actors:=[]
var motions:=[]
var frames:=[]
var source_hashes:={}
var world: Node3D
var camera: Camera3D
var labels: Label
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--frames="):frame_count=int(arg.trim_prefix("--frames="))
	call_deferred("run")
func find_node(node: Node,kind: String) -> Node:
	if node.is_class(kind):return node
	for child in node.get_children():
		var found:=find_node(child,kind)
		if found:return found
	return null
func sources() -> Dictionary:
	var paths:=[HERO,BASELINE,CANDIDATE,"res://assets/animations/rama_hero_motion.tres",get_script().resource_path]
	var manifest=JSON.parse_string(FileAccess.get_file_as_string("res://docs/research/hero-family-reuse-oct23/rama-family-manifest.json"))
	for reference in manifest.source_pins:
		if reference.res_path not in paths:paths.append(reference.res_path)
	for path in ["res://scripts/production_lighting.gd","res://scripts/ground_shadow_policy.gd","res://scripts/environment_surface_finish.gd"]:
		if path not in paths:paths.append(path)
	var result:={}
	for path in paths:result[path]=FileAccess.get_sha256(path)
	return result
func draw() -> void:
	await process_frame
	await RenderingServer.frame_post_draw
func configure_actor(x: float,script_path: String) -> bool:
	var actor: Node3D=load(HERO).instantiate();world.add_child(actor);actor.position.x=x
	var motion=load(script_path).new()
	if not motion.configure(actor,find_node(actor,"AnimationPlayer")):actor.free();return false
	# One manual simulation evaluation only; automatic modifier passes are off.
	motion.active=false
	for component in [Surface.new(),Secondary.new(),Finish.new(),Face.new()]:
		actor.add_child(component)
		if not component.configure(actor):return false
	actors.append(actor);motions.append(motion);return true
func advance() -> void:
	for motion in motions:
		motion.update_motion(1.0/60,{"velocity":Vector3.ZERO,"grounded":true,"floor_y":0.,"aiming":true,"aim_pitch":.45,"aim_yaw":.3})
		motion.evaluate_pose()
func serial_vector(v: Vector3) -> Array:return [v.x,v.y,v.z]
func actual_pose_signature(motion: Node) -> String:
	var values:=[]
	for index in motion.rig.get_bone_count():
		var pose: Transform3D=motion.rig.get_bone_global_pose(index)
		values.append([pose.origin.x,pose.origin.y,pose.origin.z,pose.basis.x.x,pose.basis.x.y,pose.basis.x.z,pose.basis.y.x,pose.basis.y.y,pose.basis.y.z,pose.basis.z.x,pose.basis.z.y,pose.basis.z.z])
	return JSON.stringify(values,"",true,true).sha256_text()
func motion_row(index: int) -> Dictionary:
	var motion=motions[index];var nock: Vector3=motion.socket_global("string_nock").origin;var hand: Vector3=motion.socket_global("draw_hand").origin
	return {"source":BASELINE if index==0 else CANDIDATE,"action":motion.action,"stage":motion.action_stage,"elapsed":motion.action_elapsed,"nocked":motion.nocked,"releases":motion.release_count,"finite":motion.finite,"nock":serial_vector(nock-actors[index].global_position),"draw_hand":serial_vector(hand-actors[index].global_position),"nock_hand_gap_m":nock.distance_to(hand)}
func run() -> void:
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):printerr("Usefreshabsoluteoutputdirectory");quit(2);return
	if frame_count not in [8,36]:printerr("Use8previewor36fullframes");quit(2);return
	if DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus":printerr("ActualForward+displayrequired");quit(2);return
	DirAccess.make_dir_recursive_absolute(output);source_hashes=sources();Engine.physics_ticks_per_second=60
	root.size=Vector2i(1024,640);root.content_scale_size=root.size;root.msaa_3d=Viewport.MSAA_2X;root.show()
	world=Node3D.new();root.add_child(world)
	var environment:=WorldEnvironment.new();environment.environment=Environment.new();world.add_child(environment)
	var sun:=DirectionalLight3D.new();world.add_child(sun);Production.apply(environment.environment,sun,world,false,true)
	if not configure_actor(-.62,BASELINE) or not configure_actor(.62,CANDIDATE):printerr("Actorcontractfailed");quit(2);return
	camera=Camera3D.new();world.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=1.30;camera.position=Vector3(0,1.46,3.5);camera.look_at(Vector3(0,1.46,0));camera.make_current()
	var canvas:=CanvasLayer.new();root.add_child(canvas);labels=Label.new();canvas.add_child(labels);labels.position=Vector2(18,14);labels.add_theme_font_size_override("font_size",18);labels.text="BASELINE: existing string entry                 CANDIDATE: cached warm entry\nAccepted Rama donor · same rig, clips, materials, light and camera";labels.add_theme_color_override("font_shadow_color",Color.BLACK);labels.add_theme_constant_override("shadow_offset_x",1);labels.add_theme_constant_override("shadow_offset_y",1)
	for tick in 60:advance()
	for warm in 3:await draw()
	var previous_engine_tick:=Engine.get_physics_frames();var start_draw:=Engine.get_frames_drawn()
	for frame in frame_count:
		var requested:=[];var released:=[]
		if frame==5:
			for motion in motions:requested.append(motion.request_action("kodanda",.18,.22))
		if frame==17:
			for motion in motions:released.append(motion.release_action("kodanda"))
		advance();advance()
		var before_draw:=[actual_pose_signature(motions[0]),actual_pose_signature(motions[1])]
		await draw()
		var after_draw:=[actual_pose_signature(motions[0]),actual_pose_signature(motions[1])]
		if before_draw!=after_draw:printerr("Unexpectedautomaticposeadvance");quit(2);return
		var path:=output.path_join("frame-%05d.png"%frame);var image:=root.get_texture().get_image()
		if image.is_empty() or image.save_png(path)!=OK:printerr("Actualcapturefailed");quit(2);return
		var tick:=Engine.get_physics_frames();var actor_rows:=[motion_row(0),motion_row(1)]
		frames.append({"index":frame,"simulation_time_s":float(frame+1)/30,"manual_pose_updates":2,"engine_physics_tick_delta":tick-previous_engine_tick,"render_frame":Engine.get_frames_drawn(),"actual_pose_sha256":after_draw,"requested":requested,"released":released,"actors":actor_rows,"image":{"file":path.get_file(),"sha256":FileAccess.get_sha256(path),"width":image.get_width(),"height":image.get_height(),"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)}})
		previous_engine_tick=tick
		print("WARM_ENTRY_FRAME ",frame," gaps=",actor_rows[0].nock_hand_gap_m,"/",actor_rows[1].nock_hand_gap_m)
	var report:={"schema_version":1,"scope":"Consecutive actual Forward+ native frames with two independently posed accepted Rama donor instances; warm-primary entry comparison only, not a newhero or humanplay/physicalGPUbenchmark.","preview":frame_count==8,"fps":30,"pose_hz":60,"width":1024,"height":640,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"camera":{"position":serial_vector(camera.position),"target":[0,1.46,0],"orthographic_size":camera.size},"frames":frames,"render_frames_advanced":Engine.get_frames_drawn()-start_draw,"sources":source_hashes,"source_after":sources(),"sources_unchanged":source_hashes==sources(),"automatic_modifiers_disabled":true,"runtime_promoted":false}
	var file:=FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");file.close();print("WARM_ENTRY_CAPTURE_COMPLETE ",frames.size());quit(0 if report.sources_unchanged else 1)
