extends SceneTree
## Imports the exact GLB through Godot's runtime importer; no asset byte swap.
const FACE := preload("res://scripts/rama_facial_performance.gd")
var output := ""
var asset := ""
var studio: Node3D
var hero: Node3D
var camera: Camera3D
var face: MeshInstance3D
var driver: Node
var pins := {}
var shots: Array[Dictionary] = []

func _initialize() -> void: call_deferred("run")

func find_kind(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := find_kind(child,kind)
		if found: return found
	return null

func find_face(node: Node) -> MeshInstance3D:
	if node is MeshInstance3D and node.name=="RamaFace": return node
	for child in node.get_children():
		var found := find_face(child)
		if found: return found
	return null

func light(position_: Vector3, target: Vector3, energy: float, color: Color) -> void:
	var lamp := DirectionalLight3D.new()
	lamp.position = position_
	lamp.light_energy = energy
	lamp.light_color = color
	studio.add_child(lamp)
	lamp.look_at(target)
	lamp.shadow_enabled = true

func shot(name_: String, details := {}) -> bool:
	await process_frame
	await RenderingServer.frame_post_draw
	var png := output.path_join(name_+".png")
	var image := root.get_texture().get_image()
	if image.is_empty() or image.save_png(png)!=OK: return false
	shots.append({"file":name_+".png","sha256":FileAccess.get_sha256(png),"camera_transform":str(camera.global_transform),"orthographic_size":camera.size,"details":details,"rendered_frame":Engine.get_frames_drawn()})
	return true

func run() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output = argument.trim_prefix("--output=")
		elif argument.begins_with("--asset="): asset = argument.trim_prefix("--asset=")
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output) or not FileAccess.file_exists(asset) or DisplayServer.get_name()=="headless":
		push_error("Require new absolute output, existing GLB and actual display renderer")
		quit(1); return
	DirAccess.make_dir_recursive_absolute(output)
	for path in [asset,"res://scripts/rama_facial_performance.gd",get_script().resource_path]: pins[path] = FileAccess.get_sha256(path)
	root.size = Vector2i(640,800)
	root.content_scale_size = root.size
	root.msaa_3d = Viewport.MSAA_2X
	root.show()
	studio = Node3D.new()
	root.add_child(studio)
	current_scene = studio
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color(.055,.065,.082)
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color(.66,.72,.81)
	environment.environment.ambient_light_energy = .42
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	studio.add_child(environment)
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(asset,state)!=OK: quit(1); return
	hero = document.generate_scene(state)
	studio.add_child(hero)
	var animator: AnimationPlayer = find_kind(hero,"AnimationPlayer")
	if animator:
		animator.stop()
		animator.active = false
	var rig: Skeleton3D = find_kind(hero,"Skeleton3D")
	rig.reset_bone_poses()
	face = find_face(hero)
	if face==null or rig.get_bone_count()!=164: quit(1); return
	driver = FACE.new()
	hero.add_child(driver)
	if not driver.configure(hero): quit(1); return
	var eye_left := rig.global_transform*rig.get_bone_global_rest(rig.find_bone("eye.L")).origin
	var eye_right := rig.global_transform*rig.get_bone_global_rest(rig.find_bone("eye.R")).origin
	var target := (eye_left+eye_right)*.5 + Vector3(0,-.015,.006)
	light(target+Vector3(-1.2,1.4,2),target,1.45,Color(1,.91,.81))
	light(target+Vector3(1.5,.4,1),target,.65,Color(.75,.83,1))
	light(target+Vector3(0,.8,-2),target,1.1,Color(.83,.9,1))
	camera = Camera3D.new()
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = .265
	camera.near = .02
	camera.far = 20
	studio.add_child(camera)
	camera.make_current()
	var success := true
	for view in [{"name":"front","offset":Vector3(0,.008,.8)},{"name":"three-quarter","offset":Vector3(.32,.025,.7)},{"name":"profile","offset":Vector3(.65,.015,.24)}]:
		camera.position = target+view.offset
		camera.look_at(target)
		for sample in [{"name":"open","weight":0.0},{"name":"half","weight":.5},{"name":"closed","weight":1.0}]:
			for index in face.get_blend_shape_count(): face.set_blend_shape_value(index,sample.weight)
			success = await shot(view.name+"-"+sample.name,{"morph_weight":sample.weight}) and success
	camera.position = target+Vector3(0,.008,.8)
	camera.look_at(target)
	driver.reset("sequential blink")
	for unused in 186: driver.update_facial(1.0/60,{})
	for frame in 30:
		driver.update_facial(1.0/60,{})
		success = await shot("blink-%03d"%frame,driver.report()) and success
	for path in pins: success = success and FileAccess.get_sha256(path)==pins[path]
	var report := {"complete":success,"sources":pins,"engine":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"display":DisplayServer.get_name(),"resolution":[640,800],"eye_origins":[str(eye_left),str(eye_right)],"frames":shots,"sample_hz":60,"scope":"Exact GLB runtime-imported Godot static open/half/closed and 30 sequential blink samples. Rest rig, neutral authored studio illumination. Fixed sample rate is not achieved hardware FPS or gameplay integration."}
	FileAccess.open(output.path_join("capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	driver.release()
	studio.queue_free()
	await process_frame
	print("RAMA_FACE_CAPTURE ",success," ",shots.size())
	quit(0 if success else 1)
