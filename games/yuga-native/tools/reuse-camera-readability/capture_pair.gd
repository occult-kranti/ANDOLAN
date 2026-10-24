extends "res://tools/reuse-next-screens/measure_hud.gd"
## Explicit staged same-pose comparison, not an ordinary-input or exact R1 replay.
const Visibility = preload("res://scripts/friendly_camera_visibility.gd")
var visibility = Visibility.new()
var matched_camera: Camera3D

func freeze(node: Node) -> void:
	node.process_mode = Node.PROCESS_MODE_DISABLED
	if node is AnimationPlayer: node.pause()
	for child in node.get_children(): freeze(child)

func pose_signature() -> Dictionary:
	var units: Array = []
	for unit in world.army.units:
		units.append({"id":unit.unit_id,"team":unit.team,"health":unit.health,"alive":unit.alive,
			"transform":str(unit.global_transform),"visual":str(unit.visual.global_transform),"layer":unit.collision_layer})
	var bones: Array = []
	var rig: Skeleton3D = world.player.rama_motion.rig
	for index in rig.get_bone_count(): bones.append(str(rig.get_bone_pose(index)))
	return {"hero":str(world.player.global_transform),"hero_visual":str(world.player.visual.global_transform),
		"rig_pose":bones,"camera":str(matched_camera.global_transform),"camera_fov":matched_camera.fov,
		"units":units,"army":world.army.report(),"kit":world.rama_runtime.kit.report()}

func save_view(id: String) -> Dictionary:
	progress("capture "+id)
	await frames(2)
	var path := output.path_join(id+".png")
	var error := root.get_texture().get_image().save_png(path)
	var row := {"id":id,"png":path,"save_error":error,"sha256":FileAccess.get_sha256(path),
		"pose_signature":pose_signature(),"visibility":visibility.report(true)}
	FileAccess.open(output.path_join(id+".json"),FileAccess.WRITE).store_string(JSON.stringify(row,"\t")+"\n")
	return row

func run() -> void:
	if not output.is_absolute_path() or not DirAccess.dir_exists_absolute(output) or not capture:
		printerr("Fresh existing absolute output and --capture required"); quit(2); return
	if DisplayServer.get_name() != "X11" or RenderingServer.get_current_rendering_method() != "forward_plus":
		printerr("Actual X11 Forward+ capture required"); quit(2); return
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.content_scale_size = Vector2i(1280,720); root.size = Vector2i(960,540)
	root.msaa_3d = Viewport.MSAA_2X; root.show()
	var paths := ["res://scripts/confluence_world.gd","res://scripts/lane_minion.gd","res://scripts/lane_army.gd","res://scripts/player.gd","res://scripts/friendly_camera_visibility.gd",get_script().resource_path]
	var pins := {}; for path in paths: pins[path] = FileAccess.get_sha256(path)
	world = load("res://scenes/confluence_world.tscn").instantiate(); root.add_child(world); current_scene = world
	progress("world instantiated"); await frames(8)
	while not world.world_ready or not world.player.model_ready: await process_frame
	world._restart_army(); for unused in 6: await physics_frame
	freeze(world)
	world.player.global_position = Vector3(-40.7999572753906,.000107422471046448,-63.2007255554199)
	world.player.visual.rotation.y = 0.0
	matched_camera = world.player.camera.duplicate() as Camera3D
	matched_camera.name = "MatchedReadabilityCamera"; world.add_child(matched_camera)
	matched_camera.global_position = Vector3(-41.4499626159668,1.84952437877655,-66.6832427978516)
	matched_camera.look_at(matched_camera.global_position+Vector3(-.0000000869860272700862,-.0998334214091301,.995004177093506))
	matched_camera.current = true
	var chosen: Node3D
	for unit in world.army.units:
		if unit.team == "sun" and unit.role == "spearman" and unit.lane_id == 0: chosen = unit; break
	if chosen == null: printerr("Existing ally unavailable"); quit(2); return
	# Preserve every unit. Reposition one actual existing spearman to expose the
	# known obstruction; this is disclosed staging, never ordinary gameplay proof.
	chosen.global_position = matched_camera.global_position.lerp(world.player.global_position+Vector3.UP*1.25,.43)
	chosen.global_position.y = .000107422471046448
	chosen.previous_position = chosen.position; chosen.heading = 0.0; chosen.previous_yaw = 0.0
	chosen.update_pose(16.25,1.0)
	world._update_practice_hud(); world.rama_hud._refresh()
	await frames(3)
	var baseline: Dictionary = await save_view("01-baseline")
	for index in range(15): visibility.update(matched_camera,world.player,world.army.units,1.0/60.0)
	var candidate: Dictionary = await save_view("02-friendly-fade")
	visibility.reset()
	var restored: Dictionary = await save_view("03-restored")
	var stable: bool = paths.all(func(path):return pins[path] == FileAccess.get_sha256(path))
	var unchanged: bool = baseline.pose_signature == candidate.pose_signature and baseline.pose_signature == restored.pose_signature
	var report := {"passed":stable and unchanged and candidate.visibility.faded_units == 1 and restored.visibility.faded_units == 0,
		"scope":"Staged actual Confluence/Rama/spearman with matched frozen poses and recorded R1 camera; not exact old unit placement or ordinary-input proof",
		"source_sha256":pins,"sources_unchanged":stable,"poses_and_authority_unchanged":unchanged,
		"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),
		"unit_id":chosen.unit_id,"unit_count":world.army.units.size(),"views":[baseline,candidate,restored]}
	FileAccess.open(output.path_join("report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	current_scene = null; world.queue_free(); await frames(2)
	quit(0 if report.passed else 1)
