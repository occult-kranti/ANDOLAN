extends Node3D
## Original Blender map-design prototype. No Confluence combat or authority state.
const MAP = preload("res://assets/world/studio-relay-foundry.glb")
const SPAWN := Vector3(0, 0.15, 79)
const WALK_SPEED := 8.0
const RUN_SPEED := 13.0
var walker: CharacterBody3D
var pivot: Node3D
var camera: Camera3D
var overview: Camera3D
var status: Label
var yaw := 0.0
var pitch := -0.36
var orbiting := false
var verify_mode := false
var collider_count := 0
var box_count := 0
var ramp_count := 0

func _ready() -> void:
	name = "RelayFoundryMapStudy"
	verify_mode = "--verify-map" in OS.get_cmdline_user_args()
	var map := MAP.instantiate()
	add_child(map)
	_add_colliders(map)
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_COLOR
	environment.environment.background_color = Color("182b3b")
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color("c5d7df")
	environment.environment.ambient_light_sky_contribution = 0.0
	environment.environment.ambient_light_energy = 0.22
	# Keep this blockout within SDR lighting range in both native renderers.
	# FILMIC at its default white point doubled exposure and clipped these flats.
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	environment.environment.tonemap_exposure = 0.9
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48, -25, 0)
	sun.light_color = Color("ffe3b1")
	sun.light_energy = 0.65
	sun.shadow_enabled = true
	add_child(sun)
	_build_walker()
	_build_ui()
	if "--map-overview" in OS.get_cmdline_user_args(): overview.make_current()
	if verify_mode: call_deferred("_verify_map")

func _add_colliders(node: Node) -> void:
	if node is MeshInstance3D and node.mesh:
		var is_box := String(node.name).begins_with("COL_BOX_")
		var is_ramp := String(node.name).begins_with("COL_RAMP_")
		if is_box or is_ramp:
			var body := StaticBody3D.new()
			body.name = "MapCollision"
			var shape := CollisionShape3D.new()
			if is_box:
				var box := BoxShape3D.new()
				var bounds: AABB = node.mesh.get_aabb()
				box.size = bounds.size
				shape.shape = box
				shape.position = bounds.get_center()
				box_count += 1
			else:
				shape.shape = node.mesh.create_convex_shape()
				ramp_count += 1
			body.add_child(shape)
			node.add_child(body)
			collider_count += 1
	# Copy the original children: newly attached bodies need no recursive processing.
	for child in node.get_children():
		if not child is StaticBody3D: _add_colliders(child)

func _build_walker() -> void:
	walker = CharacterBody3D.new()
	walker.name = "MapWalker"
	walker.floor_snap_length = 0.45
	walker.floor_max_angle = deg_to_rad(45)
	walker.safe_margin = 0.03
	add_child(walker)
	walker.position = SPAWN
	var collision := CollisionShape3D.new()
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.8
	capsule.radius = 0.4
	collision.shape = capsule
	collision.position.y = 0.9
	walker.add_child(collision)
	var mesh := MeshInstance3D.new()
	var body := CapsuleMesh.new()
	body.height = 1.8
	body.radius = 0.4
	mesh.mesh = body
	mesh.position.y = 0.9
	var paint := StandardMaterial3D.new()
	paint.albedo_color = Color("f1d79a")
	paint.roughness = 0.65
	mesh.material_override = paint
	walker.add_child(mesh)
	pivot = Node3D.new()
	add_child(pivot)
	pivot.position = walker.position + Vector3.UP * 1.5
	pivot.rotation = Vector3(pitch, yaw, 0)
	var spring := SpringArm3D.new()
	spring.spring_length = 9
	spring.margin = 0.3
	spring.add_excluded_object(walker.get_rid())
	pivot.add_child(spring)
	camera = Camera3D.new()
	camera.fov = 65
	camera.far = 400
	spring.add_child(camera)
	camera.make_current()
	overview = Camera3D.new()
	overview.position = Vector3(125, 130, 155)
	overview.far = 600
	overview.fov = 58
	add_child(overview)
	overview.look_at(Vector3(0, 0, 0))

func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)
	var panel := PanelContainer.new()
	panel.position = Vector2(20, 20)
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.025, 0.05, 0.08, 0.94)
	style.border_color = Color("c9974a")
	style.border_width_left = 3
	for edge in [SIDE_LEFT, SIDE_RIGHT, SIDE_TOP, SIDE_BOTTOM]: style.set_content_margin(edge, 14)
	panel.add_theme_stylebox_override("panel", style)
	canvas.add_child(panel)
	var copy := VBoxContainer.new()
	copy.add_theme_constant_override("separation", 7)
	panel.add_child(copy)
	var title := Label.new()
	title.text = "RELAY FOUNDRY  /  MAP STUDY"
	title.add_theme_font_size_override("font_size", 24)
	title.add_theme_color_override("font_color", Color("f0d69d"))
	copy.add_child(title)
	var instructions := Label.new()
	instructions.text = "WASD walk · Shift run · Space jump\nHold RMB to orbit · O overview · R spawn · Esc quit"
	instructions.add_theme_font_size_override("font_size", 16)
	copy.add_child(instructions)
	status = Label.new()
	status.add_theme_font_size_override("font_size", 15)
	status.add_theme_color_override("font_color", Color("a8c4d0"))
	copy.add_child(status)
	var scope := Label.new()
	scope.text = "Original Blender blockout · Three lanes + raised crossover\nExploration prototype · Relay landmarks have no capture/combat authority"
	scope.add_theme_font_size_override("font_size", 14)
	scope.add_theme_color_override("font_color", Color("ccd4d9"))
	copy.add_child(scope)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.button_index == MOUSE_BUTTON_RIGHT:
		orbiting = event.pressed
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED if orbiting else Input.MOUSE_MODE_VISIBLE
	if event is InputEventMouseMotion and orbiting:
		yaw -= event.relative.x * 0.003
		pitch = clampf(pitch - event.relative.y * 0.003, -1.15, 0.15)
	if event is InputEventKey and event.pressed and not event.echo:
		match event.physical_keycode:
			KEY_ESCAPE: get_tree().quit()
			KEY_R: walker.position = SPAWN; walker.velocity = Vector3.ZERO
			KEY_O:
				if overview.current: camera.make_current()
				else: overview.make_current()
			KEY_SPACE:
				if walker.is_on_floor(): walker.velocity.y = 7.5

func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		orbiting = false
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE

func _physics_process(delta: float) -> void:
	if verify_mode: return
	var axis := Vector2(float(Input.is_physical_key_pressed(KEY_D))-float(Input.is_physical_key_pressed(KEY_A)), float(Input.is_physical_key_pressed(KEY_S))-float(Input.is_physical_key_pressed(KEY_W)))
	var direction := Vector3(axis.x, 0, axis.y).rotated(Vector3.UP, yaw).normalized()
	var speed := RUN_SPEED if Input.is_physical_key_pressed(KEY_SHIFT) else WALK_SPEED
	_move_walker(direction * speed, delta)
	if walker.position.y < -10: walker.position = SPAWN; walker.velocity = Vector3.ZERO
	pivot.position = pivot.position.lerp(walker.position+Vector3.UP*1.5, 1-exp(-delta*12))
	pivot.rotation = Vector3(pitch, yaw, 0)
	status.text = "HEIGHT %.1f m  ·  %s  ·  %d collision solids" % [walker.position.y, "MAP VIEW" if overview.current else "WALK VIEW", collider_count]

func _move_walker(horizontal: Vector3, delta: float) -> void:
	walker.velocity.x = horizontal.x
	walker.velocity.z = horizontal.z
	if not walker.is_on_floor(): walker.velocity.y -= 18 * delta
	elif walker.velocity.y < 0: walker.velocity.y = 0
	walker.move_and_slide()

func _ray(from: Vector3, to: Vector3) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(from, to, 1, [walker.get_rid()])
	return get_world_3d().direct_space_state.intersect_ray(query)

func _verify_map() -> void:
	for unused in 4: await get_tree().physics_frame
	var checks := []
	checks.append({"name":"Imported two wedge ramps and bounded collision set", "passed":ramp_count==2 and box_count>50, "colliders":collider_count})
	for point in [Vector3(0, 15, 0), Vector3(-40, 15, 0), Vector3(40, 15, 0)]:
		var hit := _ray(point, point-Vector3.UP*20)
		checks.append({"name":"Crossover deck collision at x="+str(point.x), "passed":not hit.is_empty() and absf(hit.position.y-6)<0.06})
	var under := _ray(Vector3(-44,4,0), Vector3(-44,-2,0))
	checks.append({"name":"Ground lane remains below the crossover", "passed":not under.is_empty() and absf(under.position.y)<0.06})
	walker.position = Vector3(0,0.15,38)
	walker.velocity = Vector3.ZERO
	for unused in 330:
		await get_tree().physics_frame
		_move_walker(Vector3(0,0,-7),1.0/60)
	checks.append({"name":"Actual capsule walks south ramp onto six-metre deck", "passed":walker.position.z<5 and absf(walker.position.y-6)<0.25 and walker.is_on_floor(),"position":str(walker.position)})
	for unused in 330:
		await get_tree().physics_frame
		_move_walker(Vector3(0,0,7),1.0/60)
	checks.append({"name":"Actual capsule walks down ramp to ground", "passed":walker.position.z>35 and absf(walker.position.y)<0.25 and walker.is_on_floor(),"position":str(walker.position)})
	var jump := InputEventKey.new()
	jump.physical_keycode = KEY_SPACE
	jump.pressed = true
	_unhandled_input(jump)
	var peak := walker.position.y
	for unused in 75:
		await get_tree().physics_frame
		_move_walker(Vector3.ZERO,1.0/60)
		peak = maxf(peak,walker.position.y)
	checks.append({"name":"Actual jump input rises and returns to ground", "passed":peak>1.2 and absf(walker.position.y)<0.25 and walker.is_on_floor(), "peak_height":peak})
	var boundary := _ray(Vector3(-60,1,0),Vector3(-70,1,0))
	checks.append({"name":"Visible perimeter has collision", "passed":not boundary.is_empty()})
	var passed := checks.all(func(row: Dictionary): return row.passed)
	var report := "res://art/studio-map/native-collision.json"
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): report=argument.trim_prefix("--report=")
	var result := {"passed":passed,"checks":checks,"source_sha256":FileAccess.get_sha256("res://scripts/studio_map_study.gd"),"asset_sha256":FileAccess.get_sha256("res://assets/world/studio-relay-foundry.glb"),"scope":"Actual imported geometry and physics traversal; no art/match/hardware acceptance"}
	FileAccess.open(report,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	print("STUDIO_MAP_VERIFICATION ", JSON.stringify(result))
	get_tree().quit(0 if passed else 1)
