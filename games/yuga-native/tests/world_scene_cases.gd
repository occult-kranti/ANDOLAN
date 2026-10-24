extends SceneTree
## Headless Godot physics proof for the actual world scene. No renderer/FPS claim.
## godot --headless --path games/yuga-native --script res://tests/world_scene_cases.gd -- --report=/tmp/world-physics.json

class StepDriver extends Node:
	signal stepped
	var pending: Callable
	func _physics_process(_delta: float) -> void:
		if pending.is_valid():
			var work := pending
			pending = Callable()
			work.call()
			stepped.emit()

var scene: Node3D
var driver: StepDriver
var checks: Array[Dictionary] = []
var manifest: Dictionary
var before: Dictionary = {}
var capsule: CapsuleShape3D
var rama_fire_events: Array[Dictionary] = []
const FRONTAGE_DATA := "res://assets/world/block2-frontage.json"
const FRONTAGE_DATA_SHA256 := "67950a68d7b6384b8b114987a27efff1f113d44f8fb1b7df8632f3e9217406a2"

func _initialize() -> void:
	call_deferred("_run")

func _run() -> void:
	for path in ["res://art/world/confluence-map.json", "res://assets/world/confluence-map.json", "res://scripts/confluence_world.gd", "res://scripts/player.gd", "res://scripts/projectile.gd", "res://scripts/world_lighting.gd", "res://scripts/traversal_landmarks.gd", "res://scripts/traversal_stone.gdshader", "res://scripts/world_ground_common.gdshaderinc", "res://scripts/player_traversal.gd", "res://scripts/lane_army.gd", "res://scenes/confluence_world.tscn", "res://tests/world_scene_cases.gd", "res://scripts/relay_control.gd", "res://scripts/relay_art.gd", "res://scripts/relay_session.gd"]:
		before[path] = FileAccess.get_sha256(path)
	for path in ["res://scripts/rama_ability_kit.gd","res://scripts/rama_ability_effects.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_vitals.gd","res://assets/design/rama-ability-kit.json"]:
		before[path] = FileAccess.get_sha256(path)
	for path in ["res://scripts/world_lane_frontage.gd","res://scripts/world_lane_frontage.gd.uid",FRONTAGE_DATA]:
		before[path] = FileAccess.get_sha256(path)
	manifest = JSON.parse_string(FileAccess.get_file_as_string("res://art/world/confluence-map.json"))
	var packed = load("res://scenes/confluence_world.tscn")
	if not packed is PackedScene:
		_record("scene resource loads", false, {})
		_finish()
		return
	scene = packed.instantiate()
	# Retained pre-gate/garden floor-envelope regression. The mandatory W4 integrated
	# suite exercises the default gate, its occupied piers and full-map routes.
	scene.set("lanka_lane_gate_enabled",false)
	scene.set("lanka_water_garden_enabled",false)
	root.add_child(scene)
	driver = StepDriver.new()
	driver.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(driver)
	await process_frame
	if not scene.has_method("set_paused") or not scene.has_method("teleport_to") or not is_instance_valid(scene.get("player")) or not scene.world_ready:
		_record("world traversal API is ready", false, {})
		_finish()
		return
	var army_ready: bool=scene.army!=null and scene.army.has_method("report") and scene.army.report().get("configured",false)
	var traversal_ready: bool=scene.player.traversal_report().get("enabled",false) and scene.player.traversal_report().get("anchor_count",0)==10
	_record("offline army and traversal initialized",army_ready and traversal_ready,{"army":army_ready,"traversal":traversal_ready})
	_record("loaded runtime manifest equals canonical source", scene.manifest == manifest, {"loaded_path":scene.manifest_path,"loaded_sha256":FileAccess.get_sha256(scene.manifest_path),"canonical_sha256":before["res://art/world/confluence-map.json"]})
	var blockers := get_nodes_in_group("confluence_authority_blocker").size()
	var floors := get_nodes_in_group("confluence_floor").size()
	var platforms := get_nodes_in_group("confluence_native_platform").size()
	_record("world collision groups", blockers == 8 and floors == 1 and platforms==8, {"blockers":blockers,"floors":floors,"native_platforms":platforms})
	if blockers != 8 or floors != 1 or platforms!=8:
		_finish()
		return
	scene.set_paused(false)
	scene.player.active = false
	scene.player.set_physics_process(false)
	await _ready_physics()
	capsule = CapsuleShape3D.new()
	capsule.radius = float(manifest.bounds.hero_radius)
	capsule.height = 1.8
	await _query(func():
		var errors := _box_errors()
		_record("actual authority box surfaces", errors.is_empty(), {"rays":40, "errors":errors})
		var frontage_errors := _frontage_errors()
		_record("reviewed frontage installed shape owner and data",frontage_errors.is_empty(),{"errors":frontage_errors,"data_sha256":FileAccess.get_sha256(FRONTAGE_DATA)})
		var floor_errors := _floor_errors()
		_record("actual floor covers open arena", floor_errors.is_empty(), {"grid_spacing_metres":2.0, "sample_count":_floor_sample_count(), "errors":floor_errors})
		var failures := _route_errors()
		_record("capsule sweeps all lane and rotation segments", failures.is_empty(), {"hero_radius":capsule.radius,"hero_height":capsule.height,"errors":failures})
		var anchors := _anchor_errors()
		_record("spawns camps and review objectives stand on floor", anchors.is_empty(), {"anchors":manifest.spawns.size()+manifest.camps.size()+manifest.objectives.size(),"errors":anchors})
		var landing_errors := _landing_errors()
		_record("eight real landing decks match native specification",landing_errors.is_empty(),{"errors":landing_errors})
		var radius := _player_radius()
		_record("world player uses authority radius", abs(radius-float(manifest.bounds.hero_radius))<0.0001, {"native_radius":radius,"authority_radius":manifest.bounds.hero_radius})
	)
	# The former flat box must fail both the explicit reviewed surface positions
	# and the installed-shape ownership contract; restore the exact resource.
	var frontage: Node3D=scene.world.get_node_or_null("ReviewBlock2Frontage")
	var frontage_body: StaticBody3D=scene.world.get_node_or_null("authority-solid-2")
	var frontage_holder: CollisionShape3D
	if frontage_body:
		for child in frontage_body.get_children():
			if child is CollisionShape3D: frontage_holder=child
	if frontage and frontage_holder:
		var reviewed_shape: Shape3D=frontage_holder.shape
		frontage_holder.shape=frontage.get_meta("old_shape")
		await _ready_physics()
		await _query(func():
			var errors := _box_errors()
			var target_errors := errors.filter(func(item):return item.id=="authority-solid-2")
			_record("negative former frontage box detected before restoration",target_errors.size()==4 and not _frontage_errors().is_empty(),{"surface_errors":target_errors,"contract_errors":_frontage_errors()})
		)
		frontage_holder.shape=reviewed_shape
		await _ready_physics()
	else:
		_record("negative former frontage box detected before restoration",false,{"reason":"reviewed frontage missing"})
	# Deliberately break physics state in this isolated instance; each checker must
	# detect it before restoration. These changes never touch project assets.
	var victim: StaticBody3D = get_nodes_in_group("confluence_authority_blocker")[0]
	var old_layer := victim.collision_layer
	victim.collision_layer = 0
	await _ready_physics()
	await _query(func():
		var errors := _box_errors()
		_record("negative missing blocker detected by real rays", not errors.is_empty(), {"errors_detected":errors.size()})
	)
	victim.collision_layer = old_layer
	var floor_body: StaticBody3D = get_nodes_in_group("confluence_floor")[0]
	old_layer = floor_body.collision_layer
	floor_body.collision_layer = 0
	await _ready_physics()
	await _query(func():
		_record("negative missing floor detected", not _anchor_errors().is_empty(), {})
	)
	floor_body.collision_layer = old_layer
	var obstruction := StaticBody3D.new()
	obstruction.collision_layer = 1
	obstruction.collision_mask = 0
	obstruction.position = Vector3(0, 1, 0)
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2, 2, 2)
	shape.shape = box
	obstruction.add_child(shape)
	scene.add_child(obstruction)
	await _ready_physics()
	await _query(func():
		_record("negative accidental prop blocker detected", not _route_errors().is_empty(), {})
	)
	obstruction.queue_free()
	await _ready_physics()
	for point in [Vector3(200,0,200),Vector3(-200,0,-200),Vector3(200,0,-200),Vector3(-200,0,200)]:
		scene.teleport_to(point, 0.0)
		await _ready_physics()
		var position: Vector3 = scene.player.global_position
		_record("player bounded after external displacement " + str(point), abs(position.x)<=67.3501 and abs(position.z)<=127.3501 and position.is_finite(), {"position":_xyz(position)})
	await _query(func():
		_record("restored scene collision passes after mutations", _box_errors().is_empty() and _frontage_errors().is_empty() and _anchor_errors().is_empty() and _route_errors().is_empty(), {})
	)
	await _check_layout_and_state()
	var unchanged := true
	for path in before:
		unchanged = unchanged and before[path] == FileAccess.get_sha256(path)
	_record("sources unchanged during run", unchanged, {})
	_finish()

func _finish() -> void:
	paused=false
	if is_instance_valid(scene):
		scene.queue_free()
		await process_frame
		await process_frame
	if is_instance_valid(driver): driver.queue_free()
	# Fixed-fps headless frames can finish before AudioServer processes its stop
	# queue. Allow one real mixer buffer to retire after all world nodes are freed.
	OS.delay_msec(80)
	await process_frame
	var passed := true
	for check in checks:
		passed = passed and check.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"sources":before,"checks":checks,
		"scope":"Real headless Godot physics queries in _physics_process against instantiated native world. Expanded140×260m floor, seven unchanged box surfaces plus one reviewed closed frontage within its preserved browser-source broadbounds, eight native landing decks, capsule route sweeps and native-only bounds. Army state is offline; tower markers remain nonblocking. Detailed frontage3D collision is not old-box or browser-authority parity. UI rectangles at two logical viewport sizes and injected actions/button signals are checked, not OS input. No renderer, AI, online match, continuous exhaustive proof or performance claim."}
	print("YUGA_WORLD_PHYSICS ",JSON.stringify(report))
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file:
				file.store_string(JSON.stringify(report,"\t")+"\n")
			else:
				passed=false
	quit(0 if passed else 1)

func _query(work: Callable) -> void:
	driver.pending=work
	await driver.stepped

func _ready_physics() -> void:
	await physics_frame
	await physics_frame

func _v(values: Array) -> Vector3:
	return Vector3(values[0],values[1],values[2])

func _xyz(value: Vector3) -> Array:
	return [value.x,value.y,value.z]

func _ray(start: Vector3, finish: Vector3) -> Dictionary:
	var query := PhysicsRayQueryParameters3D.create(start,finish,1)
	return scene.get_world_3d().direct_space_state.intersect_ray(query)

func _box_errors() -> Array:
	var errors := []
	for item in manifest.authority_collision_boxes:
		var base := _v(item.position)
		var size := _v(item.size)
		var rays := [[base+Vector3(0,size.y+2,0),base+Vector3(0,-1,0),base+Vector3(0,size.y,0)]]
		for direction in [Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK]:
			var half := size.x*0.5 if direction.x != 0 else size.z*0.5
			var expected_surface: Vector3=base+Vector3.UP+direction*half
			if str(item.id)=="authority-solid-2":
				# Reviewed closed r2 surface atY1: localX +/-8.76,
				# localZ -8.35/+8.76. Broadbounds/ray origins stay +/-9.
				var inset: float=.65 if direction==Vector3.FORWARD else .24
				expected_surface-=direction*inset
			rays.append([base+Vector3.UP+direction*(half+2),base+Vector3.UP,expected_surface])
		for ray in rays:
			var hit := _ray(ray[0],ray[1])
			if hit.is_empty() or hit.position.distance_to(ray[2]) > 0.02 or str(hit.collider.get_meta("authority_id", "")) != str(item.id):
				errors.append({"id":item.id,"expected":_xyz(ray[2]),"actual":_xyz(hit.position) if not hit.is_empty() else []})
	return errors

func _frontage_errors() -> Array:
	var errors := []
	if FileAccess.get_sha256(FRONTAGE_DATA)!=FRONTAGE_DATA_SHA256: errors.append("reviewed frontage data bytes")
	var body:=scene.world.get_node_or_null("authority-solid-2") as StaticBody3D
	var frontage:=scene.world.get_node_or_null("ReviewBlock2Frontage") as Node3D
	var original:=scene.world.get_node_or_null("CityArt/block-2") as Node3D
	if body==null or frontage==null or original==null:
		errors.append("installed frontage nodes");return errors
	if body.position!=Vector3(20,7.5,-28) or body.collision_layer!=1 or body.collision_mask!=0 or body.get_meta("authority_id","")!="authority-solid-2" or body.get_meta("position_base",null)!=Vector3(20,0,-28) or body.get_meta("dimensions",null)!=Vector3(18,15,18): errors.append("preserved body identity metadata and broadbounds")
	var owners:=body.get_shape_owners()
	if owners.size()!=1 or body.shape_owner_get_shape_count(owners[0])!=1:
		errors.append("sole native shape owner");return errors
	var holder:=body.shape_owner_get_owner(owners[0]) as CollisionShape3D
	if holder==null or holder.disabled or holder.transform!=Transform3D.IDENTITY or not holder.shape is ConcavePolygonShape3D:
		errors.append("enabled reviewed ConcavePolygonShape3D");return errors
	var shape:=holder.shape as ConcavePolygonShape3D
	if shape!=frontage.get_meta("published_shape",null) or not frontage.get_meta("old_holder") is WeakRef or frontage.get_meta("old_holder").get_ref()!=holder: errors.append("published shape and holder ownership")
	if shape.get_faces().size()!=4824*3 or not shape.backface_collision or not shape.get_debug_mesh().get_aabb().is_equal_approx(AABB(Vector3(-9,-7.5,-9),Vector3(18,15,18))): errors.append("reviewed closed triangle count and broadbounds")
	var mesh:=frontage.get_node_or_null("ClosedCivicFrontage") as MeshInstance3D
	if original.visible or mesh==null or not mesh.is_visible_in_tree() or mesh.mesh==null or mesh.mesh.get_surface_count()!=3: errors.append("reviewed visible mesh replaces original")
	return errors

func _landing_errors() -> Array:
	var errors := []
	for item in manifest.traversal.native_collision_boxes:
		var base:=_v(item.position)
		var dimensions:=_v(item.size)
		var court: Node3D=scene.world.get_node("TraversalRelics/"+String(item.landmark_id))
		var is_pilot: bool=item.landmark_id==scene.Landmarks.WIND_COURT_ID and scene.landmark_report.get("wind_court_pilot",{}).get("enabled",false)
		var visual:=court.get_node_or_null("WindCourtNear" if is_pilot else "SolidLandingDeck") as MeshInstance3D
		if visual==null:
			errors.append(item.id+" visible architecture missing")
			continue
		if is_pilot:
			var detailed:=court.get_node_or_null("WindCourtDetailedCollision") as StaticBody3D
			if scene.world.has_node(scene.Landmarks.WIND_COURT_COLLISION_ID) or court.has_node("SolidLandingDeck") or visual.mesh.get_surface_count()!=3 or detailed==null or detailed.get_child_count()!=36 or not detailed.is_in_group("confluence_native_platform"):
				errors.append(item.id+" reviewed detailed collision replacement")
		var material: Material=visual.get_active_material(0)
		if not material is ShaderMaterial or material.shader.resource_path!="res://scripts/traversal_stone.gdshader" or not is_equal_approx(float(material.get_shader_parameter("deck_height")),dimensions.y) or not is_equal_approx(float(material.get_shader_parameter("deck_width")),dimensions.x):
			errors.append(item.id+" facade material contract")
		for offset in [Vector3.ZERO,Vector3(1.5,0,1.5),Vector3(-1.5,0,-1.5)]:
			var hit:=_ray(base+offset+Vector3.UP*(dimensions.y+2),base+offset+Vector3.UP*(dimensions.y-1))
			if hit.is_empty() or abs(hit.position.y-(base.y+dimensions.y))>.002 or not hit.collider.is_in_group("confluence_native_platform"):
				errors.append(item.id)
	return errors

func _static_blocked(x: float,z: float) -> bool:
	for item in manifest.authority_collision_boxes+manifest.traversal.native_collision_boxes:
		if abs(x-float(item.position[0])) <= float(item.size[0])*0.5+0.05 and abs(z-float(item.position[2])) <= float(item.size[2])*0.5+0.05:
			return true
	# Plinth tops are deliberately solid. Open-floor sampling excludes only their
	# exact footprints; the independent route sweeps still detect misplaced props.
	for item in scene.relays.art.collision_boxes():
		if absf(x-item.position.x)<=item.size.x*.5+.05 and absf(z-item.position.z)<=item.size.z*.5+.05:
			return true
	return false

func _floor_sample_count() -> int:
	var count := 0
	for x in range(-66,67,2):
		for z in range(-126,127,2):
			if not _static_blocked(x,z):
				count+=1
	return count

func _floor_errors() -> Array:
	var errors := []
	for x in range(-66,67,2):
		for z in range(-126,127,2):
			if _static_blocked(x,z):
				continue
			var hit := _ray(Vector3(x,1,z),Vector3(x,-1,z))
			if hit.is_empty() or abs(hit.position.y)>0.002 or not hit.collider.is_in_group("confluence_floor"):
				if errors.size()<20:
					errors.append([x,z])
	return errors

func _route_errors() -> Array:
	var errors := []
	var routes: Array = manifest.lanes.duplicate()
	routes.append_array(manifest.rotations)
	for route in routes:
		var points: Array = route.points.duplicate()
		if route.get("closed",false):
			points.append(points[0])
		for i in range(points.size()-1):
			var start := _v(points[i])+Vector3(0,0.95,0)
			var finish := _v(points[i+1])+Vector3(0,0.95,0)
			var query := PhysicsShapeQueryParameters3D.new()
			query.shape=capsule
			query.transform=Transform3D(Basis.IDENTITY,start)
			query.motion=finish-start
			query.collision_mask=1
			query.margin=0.001
			var result := scene.get_world_3d().direct_space_state.cast_motion(query)
			if result.size()!=2 or result[0]<0.9999:
				errors.append({"route":route.id,"segment":i,"safe_fraction":result[0] if result.size()==2 else -1})
	return errors

func _anchor_errors() -> Array:
	var errors := []
	var anchors: Array = manifest.spawns.duplicate()
	anchors.append_array(manifest.camps)
	anchors.append_array(manifest.objectives)
	for item in anchors:
		var p := _v(item.position)
		var hit := _ray(p+Vector3.UP,p-Vector3.UP)
		if hit.is_empty() or abs(hit.position.y)>0.002 or not hit.collider.is_in_group("confluence_floor"):
			errors.append(item.id)
	return errors

func _player_radius() -> float:
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:
			return child.shape.radius
	return -1.0

func _record(label: String, passed: bool, details: Dictionary) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _frames(count: int) -> void:
	for _i in count:
		await physics_frame

func _visible_rect(control: Control) -> Array:
	var rect := control.get_global_rect()
	return [rect.position.x, rect.position.y, rect.size.x, rect.size.y]

func _crosshair() -> Control:
	var named: Node = scene.hud.find_child("Crosshair", true, false)
	if named is Control: return named
	for item in scene.hud.find_children("*", "Label", true, false):
		if item.text == "·": return item
	return null

func _button_named(label: String) -> Button:
	for item in scene.pause_panel.find_children("*", "Button", true, false):
		if item.text == label: return item
	return null

func _key(code: Key) -> void:
	var down := InputEventKey.new()
	down.physical_keycode=code
	down.keycode=code
	down.pressed=true
	Input.parse_input_event(down)
	Input.flush_buffered_events()
	await _frames(2)
	var up := InputEventKey.new()
	up.physical_keycode=code
	up.keycode=code
	up.pressed=false
	Input.parse_input_event(up)
	Input.flush_buffered_events()
	await _frames(2)

func _horizontal_distance(a: Vector3,b: Vector3) -> float:
	return Vector2(a.x,a.z).distance_to(Vector2(b.x,b.z))

func _check_layout_and_state() -> void:
	# Both dimensions are explicit logical canvas sizes. The production window
	# stretch mode is a separate OS/windowing concern covered by root captures.
	for dimensions in [Vector2i(1280,720),Vector2i(960,600)]:
		root.size=dimensions
		root.content_scale_size=dimensions
		scene.set_paused(true)
		await _frames(4)
		var viewport_rect := root.get_visible_rect()
		var visual_controls: Array[Control] = [scene.map_control,scene.pause_panel,scene.rama_hud]
		for card_name in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus","InvocationStatus","AtlasLegend"]:
			var card: Node = scene.hud.find_child(card_name,true,false)
			if card is Control: visual_controls.append(card)
		var crosshair := _crosshair()
		if is_instance_valid(crosshair): visual_controls.append(crosshair)
		var failures := []
		var rectangles := {}
		for control in visual_controls:
			rectangles[str(control.name)]=_visible_rect(control)
			if not viewport_rect.encloses(control.get_global_rect()): failures.append(str(control.name))
		var buttons: Array[Node] = scene.pause_panel.find_children("*","Button",true,false)
		var scroll_rect: Rect2=scene.pause_scroll.get_global_rect()
		if not scene.pause_panel.get_global_rect().encloses(scroll_rect): failures.append("menu scroll outside panel")
		var focus_reachable:=true
		# A scroll menu deliberately clips inactive rows. Every keyboard target
		# must scroll fully into view when focused, including the volume slider.
		for action in scene.pause_actions:
			action.grab_focus()
			await _frames(4)
			var action_rect: Rect2=action.get_global_rect()
			var label: String=action.text if action is Button else str(action.name)
			rectangles[label]=_visible_rect(action)
			if not viewport_rect.encloses(action_rect) or not scroll_rect.grow(1).encloses(action_rect):
				failures.append(label+" not fully visible on focus")
			if action is Button and action.size.y<40: failures.append(label+" small target")
			focus_reachable=focus_reachable and action.has_focus() and action.focus_mode==Control.FOCUS_ALL
		var overlaps := []
		for i in range(buttons.size()):
			for j in range(i+1,buttons.size()):
				if buttons[i].get_global_rect().intersects(buttons[j].get_global_rect()): overlaps.append([buttons[i].text,buttons[j].text])
			# Check the visible clipped part against the HUD; off-screen rows are
			# intentionally hidden by ScrollContainer and are not UI overlap.
			var visible_part: Rect2=buttons[i].get_global_rect().intersection(scroll_rect)
			if visible_part.has_area() and visible_part.intersects(scene.map_control.get_global_rect()): overlaps.append([buttons[i].text,"atlas"])
		var centered := is_instance_valid(crosshair) and crosshair.get_global_rect().get_center().distance_to(viewport_rect.get_center())<24
		var continue_button := _button_named("Continue practice")
		if is_instance_valid(continue_button): continue_button.grab_focus()
		await _frames(4)
		var focus_ready := is_instance_valid(continue_button) and continue_button.has_focus() and scroll_rect.grow(1).encloses(continue_button.get_global_rect())
		_record("UI inside viewport and focused controls separated " + str(dimensions), failures.is_empty() and overlaps.is_empty() and buttons.size()==12 and scene.pause_actions.size()==13 and is_instance_valid(scene.invocation_button) and scene.rama_button in scene.pause_actions and focus_reachable and centered and focus_ready,
			{"logical_viewport":[viewport_rect.size.x,viewport_rect.size.y],"outside_or_small":failures,"overlaps":overlaps,"crosshair_near_center":centered,"resume_keyboard_focus":focus_ready,"all_targets_reachable":focus_reachable,"focused_rectangles":rectangles})
	# Resume the actual character controller, then use input actions rather than
	# assigning a fake position to prove held movement had an effect before pause.
	scene.set_paused(false)
	scene.player.set_physics_process(true)
	scene.teleport_to(Vector3(0,.05,55),180)
	await _frames(8)
	var initial: Vector3=scene.player.position
	var initial_ammo: int=scene.player.ammo
	var effects_accepted: int=scene.rama_effects.report().counts.accepted
	scene.rama_kit.ability_event.connect(_on_rama_fire_event)
	Input.action_press("move_forward")
	Input.action_press("fire")
	await _frames(20)
	var moved := _horizontal_distance(initial,scene.player.position)
	var draws := {}
	var releases := {}
	var unique_releases := true
	for event in rama_fire_events:
		var identity := "%s:%s" % [event.generation,event.cast_id]
		if event.kind=="begin": draws[identity]=true
		elif event.kind=="release":
			unique_releases=unique_releases and draws.has(identity) and not releases.has(identity) and event.get("effect_release_observed",false)
			releases[identity]=true
	var fire_state: Dictionary=scene.rama_kit.report()
	var presentation: Dictionary=scene.rama_effects.report()
	_record("held fire reserves ammo and routes unique Rama releases into presentation", not draws.is_empty() and not releases.is_empty() and unique_releases and scene.player.shots_fired==draws.size() and initial_ammo-scene.player.ammo==draws.size() and fire_state.release_count>=releases.size() and presentation.counts.accepted>effects_accepted and presentation.generation==fire_state.generation and scene.projectiles.get_child_count()==0,
		{"shots":scene.player.shots_fired,"accepted_draws":draws.size(),"release_receipts":releases.size(),"unique_releases":unique_releases,"ammo_reserved":initial_ammo-scene.player.ammo,"accepted_effect_events":presentation.counts.accepted-effects_accepted,"legacy_projectile_nodes":scene.projectiles.get_child_count()})
	await _key(KEY_ESCAPE)
	var stopped: Vector3=scene.player.position
	var shots: int=scene.player.shots_fired
	var remaining: float=scene.player.fire_remaining
	var paused_kit: Dictionary=scene.rama_kit.report()
	await _frames(30)
	var frozen_kit: Dictionary=scene.rama_kit.report()
	_record("pause freezes held movement and fire", moved>.5 and scene.paused and paused and _horizontal_distance(stopped,scene.player.position)<.00001 and shots==scene.player.shots_fired and is_equal_approx(remaining,scene.player.fire_remaining) and frozen_kit.elapsed==paused_kit.elapsed and frozen_kit.cooldowns==paused_kit.cooldowns and frozen_kit.release_count==paused_kit.release_count,
		{"movement_before_pause":moved,"movement_during_pause":_horizontal_distance(stopped,scene.player.position),"shots_before":shots,"shots_after":scene.player.shots_fired})
	var resume := _button_named("Continue practice")
	if is_instance_valid(resume): resume.pressed.emit()
	await _frames(15)
	_record("resume button clears stale actions", not scene.paused and not paused and not Input.is_action_pressed("move_forward") and not Input.is_action_pressed("fire") and _horizontal_distance(stopped,scene.player.position)<.02 and scene.player.shots_fired==shots and scene.rama_kit.report().accepted_casts==paused_kit.accepted_casts,
		{"movement_after_resume":_horizontal_distance(stopped,scene.player.position),"shots_after":scene.player.shots_fired})
	# A dash is deliberately in progress when the real F1 action is dispatched.
	var had_dash: bool=await _begin_real_step()
	await _key(KEY_F1)
	var overview_position: Vector3=scene.player.position
	await _frames(10)
	_record("F1 overview clears live dash and movement", had_dash and scene.overview and not scene.player.active and scene.player.dash_time==0 and scene.player.dash_direction==Vector3.ZERO and Vector2(scene.player.velocity.x,scene.player.velocity.z).length()<.00001 and not Input.is_action_pressed("move_forward") and not Input.is_action_pressed("dash") and _horizontal_distance(overview_position,scene.player.position)<.00001,
		{"dash_was_active":had_dash,"overview":scene.overview,"movement_during_overview":_horizontal_distance(overview_position,scene.player.position)})
	await _key(KEY_F1)
	await _frames(8)
	_record("F1 returns active camera with neutral movement", not scene.overview and scene.player.active and scene.player.camera.current and _horizontal_distance(overview_position,scene.player.position)<.02,{})
	for label in ["Visit Lanka coast","Visit Metro gardens"]:
		# Reset the actual kit, then await its real step release before transition.
		var step_started: bool=await _begin_real_step()
		if label=="Visit Lanka coast": await _key(KEY_F1)
		var from_overview: bool=scene.overview
		scene.set_paused(true)
		var button := _button_named(label)
		if is_instance_valid(button): button.pressed.emit()
		await _frames(8)
		var expected:=Vector3(-40 if label=="Visit Lanka coast" else 40,0,14)
		_record(label+" button arrives neutral", step_started and is_instance_valid(button) and not scene.paused and not paused and not scene.overview and scene.player.active and scene.player.camera.current and _horizontal_distance(expected,scene.player.position)<.02 and scene.player.dash_time==0 and scene.player.dash_direction==Vector3.ZERO and Vector2(scene.player.velocity.x,scene.player.velocity.z).length()<.00001 and not Input.is_action_pressed("move_forward") and not Input.is_action_pressed("dash"),
			{"position":_xyz(scene.player.position),"expected_xz":[expected.x,expected.z],"from_overview":from_overview,"returned_to_walking":scene.player.active and not scene.overview})
	scene.release_actions()
	scene.rama_kit.ability_event.disconnect(_on_rama_fire_event)

func _on_rama_fire_event(event: Dictionary) -> void:
	if event.get("ability_id")=="kodanda" and rama_fire_events.size()<64:
		var observed := event.duplicate(true)
		if event.kind=="release":
			# Runtime was connected first; inspect its actual event consumer at the
			# release boundary instead of sampling an arbitrary later arrow frame.
			var presentation: Dictionary=scene.rama_effects.report()
			observed.effect_release_observed=presentation.generation==event.generation and presentation.casts.any(func(cast): return cast.cast_id==event.cast_id and cast.ability_id==event.ability_id and cast.released)
		rama_fire_events.append(observed)

func _begin_real_step() -> bool:
	scene.release_actions()
	scene.rama_runtime.reset("transition fixture")
	var releases_before: int=scene.rama_kit.report().release_count
	Input.action_press("move_forward")
	Input.action_press("dash")
	# Measured Step has an actual 0.1-second draw on the 20 Hz authority clock.
	# A bounded wait observes its release instead of assigning dash state.
	for unused in range(18):
		await _frames(1)
		if scene.player.dash_time>0:
			return scene.rama_kit.report().release_count==releases_before+1
	return false
