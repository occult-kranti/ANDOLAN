extends Node3D
## Original expanded native lane practice and traversal. Eight center boxes retain
## browser-source dimensions; all extended bounds, platforms and army state are local.

const PlayerScript = preload("res://scripts/player.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const WorldLighting = preload("res://scripts/world_lighting.gd")
const Landmarks = preload("res://scripts/traversal_landmarks.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const ControlsOverlay = preload("res://scripts/controls_overlay.gd")
const TraversalAudio = preload("res://scripts/traversal_audio.gd")
const SiegeEffects = preload("res://scripts/siege_effects.gd")
const RUNTIME_MANIFEST := "res://assets/world/confluence-map.json"
const SOURCE_MANIFEST := "res://art/world/confluence-map.json"
const CREAM := Color("f0e5d0")
const GOLD := Color("dfb96e")
const TEAL := Color("6cb9c1")

var manifest: Dictionary = {}
var manifest_path := ""
var world: Node3D
var player: CharacterBody3D
var floor_body: StaticBody3D
var authority_bodies: Array[StaticBody3D] = []
var native_platform_bodies: Array[StaticBody3D] = []
var landmark_report: Dictionary = {}
var army: Node3D
var audio: Node
var siege_effects: Node3D
var siege_practice_button: Button
var practice_mode_label: Label
var practice_hint_label: Label
var practice_error := ""
var pause_actions: Array[Control] = []
var pause_scroll: ScrollContainer
var controls_overlay: Control
var controls_return_to_pause := false
var energy_bar: ProgressBar
var ability_label: Label
var score_label: Label
var goal_label: Label
var help_labels: Array[Label] = []
var volume_label: Label
var traversal_seen := false
var last_gold := 0
var props_root: Node3D
var projectiles: Node3D
var effects: Node3D
var world_environment: WorldEnvironment
var sun: DirectionalLight3D
var lighting: RefCounted
var ui: CanvasLayer
var hud: Control
var pause_panel: PanelContainer
var location_label: Label
var status_label: Label
var phase_label: Label
var map_control: Control
var review_camera: Camera3D
var world_ready := false
var paused := false
var night := false
var phase := 0.0
var target_phase := 0.0
var phase_clock := 0.0
var ui_clock := 0.0
var imported_prop_count := 0
var fallback_prop_count := 0
var builtin_prop_count := 0
var missing_presets: Array[String] = []
var kit_hashes: Dictionary = {}
var kit_templates: Dictionary = {}
var material_cache: Dictionary = {}
var start_position := Vector3(0, 0.05, -112)
var overview := false

class Atlas extends Control:
	var data: Dictionary = {}
	var hero_position := Vector3.ZERO
	var units: Array = []
	var footer_height := 70.0
	func project(point: Vector3) -> Vector2:
		var bounds: Array=data.get("bounds",{}).get("nominal_xz",[-70,70,-130,130])
		return Vector2(12+(point.x-bounds[0])/(bounds[1]-bounds[0])*(size.x-24),12+(point.z-bounds[2])/(bounds[3]-bounds[2])*(size.y-24-footer_height))
	func _draw() -> void:
		draw_style_box(_background(),Rect2(Vector2.ZERO,size))
		if data.is_empty(): return
		for solid in data.authority_collision_boxes:
			var p:=Vector3(solid.position[0],0,solid.position[2])
			var half:=Vector3(solid.size[0]/2,0,solid.size[2]/2)
			draw_rect(Rect2(project(p-half),project(p+half)-project(p-half)),Color("52676d"))
		for lane in data.lanes:
			for i in range(lane.points.size()-1):
				var a: Array=lane.points[i]
				var b: Array=lane.points[i+1]
				draw_line(project(Vector3(a[0],0,a[2])),project(Vector3(b[0],0,b[2])),Color("cfa964"),2,true)
		for camp in data.camps:
			draw_circle(project(Vector3(camp.position[0],0,camp.position[2])),3,Color("7ac6bd"))
		for objective in data.objectives:
			draw_circle(project(Vector3(objective.position[0],0,objective.position[2])),3,Color("efba70") if objective.team=="sun" else Color("88bded"))
		for anchor in data.get("traversal",{}).get("anchors",[]):
			var p:=project(Vector3(anchor.position[0],0,anchor.position[2]))
			draw_polyline(PackedVector2Array([p+Vector2(0,-3),p+Vector2(3,0),p+Vector2(0,3),p+Vector2(-3,0),p+Vector2(0,-3)]),Color("e9c877"),1,true)
		for unit in units:
			var p:=project(unit.position)
			if unit.get("role","") in ["cannon_cart","royal_chariot"]:
				draw_circle(p,5.5,Color("efba70") if unit.team=="sun" else Color("88bded"),false,1.5,true)
			if unit.team=="sun": draw_colored_polygon(PackedVector2Array([p+Vector2(0,-2.5),p+Vector2(2,2),p+Vector2(-2,2)]),Color("efba70"))
			else: draw_rect(Rect2(p-Vector2(1.7,1.7),Vector2(3.4,3.4)),Color("88bded"))
		draw_circle(project(hero_position),5,Color.WHITE)
		draw_circle(project(hero_position),8,Color(1,1,1,.4),false,1,true)
	func _background() -> StyleBoxFlat:
		var style:=StyleBoxFlat.new()
		style.bg_color=Color(0.025,0.065,0.085,.90)
		style.border_color=Color(0.61,0.76,0.75,.35)
		style.set_border_width_all(1)
		style.set_corner_radius_all(12)
		return style

func _ready() -> void:
	process_mode=Node.PROCESS_MODE_ALWAYS
	process_physics_priority=100
	Bindings.install()
	manifest_path=RUNTIME_MANIFEST if FileAccess.file_exists(RUNTIME_MANIFEST) else SOURCE_MANIFEST
	var parsed=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
	if not parsed is Dictionary or parsed.get("schema_version",0)!=1:
		push_error("Confluence map manifest is missing or has an unsupported schema.")
		return
	manifest=parsed
	world=Node3D.new()
	world.name="World"
	world.process_mode=Node.PROCESS_MODE_PAUSABLE
	add_child(world)
	_build_floor()
	_build_collisions()
	_build_traversal_landmarks()
	_load_kits()
	_build_props()
	_build_objectives()
	_build_water()
	_build_lighting()
	_build_player()
	if not _build_army_audio() or not player.traversal_report().get("enabled",false):
		push_error("Confluence requires a configured army and traversal controller.")
		return
	_build_ui()
	for template in kit_templates.values(): template.free()
	kit_templates.clear()
	get_window().focus_exited.connect(_focus_lost)
	world_ready=true
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	print("YUGA_CONFLUENCE_READY ",JSON.stringify(build_report()))

func _v(data: Array) -> Vector3:
	return Vector3(float(data[0]),float(data[1]),float(data[2]))

func _material(color: Color, metal: float=0.0, emission: float=0.0) -> StandardMaterial3D:
	var key:=str(color)+":"+str(metal)+":"+str(emission)
	if material_cache.has(key): return material_cache[key]
	var material:=StandardMaterial3D.new()
	material.albedo_color=color
	material.metallic=metal
	material.roughness=.75 if metal==0 else .35
	material.emission_enabled=emission>0
	material.emission=color
	material.emission_energy_multiplier=emission
	material_cache[key]=material
	return material

func _mesh(parent: Node3D, mesh: Mesh, position_: Vector3, material: Material, name_: String="Detail") -> MeshInstance3D:
	var node:=MeshInstance3D.new()
	node.name=name_
	node.mesh=mesh
	node.position=position_
	node.material_override=material
	parent.add_child(node)
	return node

func _box(parent: Node3D, position_: Vector3, size_: Vector3, material: Material, name_: String="Masonry") -> MeshInstance3D:
	var mesh:=BoxMesh.new()
	mesh.size=size_
	return _mesh(parent,mesh,position_,material,name_)

func _cylinder(parent: Node3D, position_: Vector3, radius: float, height: float, material: Material, top_radius: float=-1.0) -> MeshInstance3D:
	var mesh:=CylinderMesh.new()
	mesh.bottom_radius=radius
	mesh.top_radius=radius if top_radius<0 else top_radius
	mesh.height=height
	mesh.radial_segments=16
	return _mesh(parent,mesh,position_,material)

func _collision(id: String, base: Vector3, size_: Vector3, floor_: bool=false, native_: bool=false) -> StaticBody3D:
	var body:=StaticBody3D.new()
	body.name=id
	body.collision_layer=1
	body.collision_mask=0
	body.position=base+Vector3.UP*size_.y*.5
	body.set_meta("authority_id",id)
	body.set_meta("position_base",base)
	body.set_meta("dimensions",size_)
	body.add_to_group("confluence_floor" if floor_ else ("confluence_native_platform" if native_ else "confluence_authority_blocker"))
	body.set_meta("native_only",native_)
	var shape:=CollisionShape3D.new()
	var box:=BoxShape3D.new()
	box.size=size_
	shape.shape=box
	body.add_child(shape)
	world.add_child(body)
	return body

func _build_floor() -> void:
	var bounds: Array=manifest.bounds.nominal_size_xz
	floor_body=_collision("AuthorityFloor",Vector3(0,-.5,0),Vector3(bounds[0],.5,bounds[1]),true)
	# Visual apron supports the distant skyline; it creates no walkable collider.
	var art_bounds: Array=manifest.bounds.art_xz
	var apron:=PlaneMesh.new()
	apron.size=Vector2(art_bounds[1]-art_bounds[0],art_bounds[3]-art_bounds[2])
	_mesh(world,apron,Vector3((art_bounds[0]+art_bounds[1])*.5,-.18,(art_bounds[2]+art_bounds[3])*.5),_material(Color("525f55")),"NoncollidingTerrainApron")
	var floor_mesh:=PlaneMesh.new()
	floor_mesh.size=Vector2(bounds[0],bounds[1])
	var material:=ShaderMaterial.new()
	material.shader=load("res://scripts/world_ground.gdshader")
	_configure_paving(material)
	_mesh(world,floor_mesh,Vector3.ZERO,material,"FlatCityPaving")
	# A quiet retaining edge marks the actor limit without introducing colliders.
	var perimeter:=_material(Color("b5ae95"))
	for x in [-float(bounds[0])*.5+1,float(bounds[0])*.5-1]: _box(world,Vector3(x,.08,0),Vector3(.4,.16,bounds[1]-2),perimeter,"PerimeterInlay")
	for z in [-float(bounds[1])*.5+1,float(bounds[1])*.5-1]: _box(world,Vector3(0,.08,z),Vector3(bounds[0]-2,.16,.4),perimeter,"PerimeterInlay")

func _configure_paving(material: ShaderMaterial) -> void:
	material.set_shader_parameter("arrival_court_z",112.0)
	var lanes:=_route_segments(manifest.lanes)
	var rotations:=_route_segments(manifest.get("rotations",[]))
	material.set_shader_parameter("lane_count",mini(lanes.size(),8))
	material.set_shader_parameter("rotation_count",mini(rotations.size(),20))
	lanes.resize(8)
	rotations.resize(20)
	material.set_shader_parameter("lane_segments",lanes)
	material.set_shader_parameter("rotation_segments",rotations)

func _route_segments(routes: Array) -> PackedVector4Array:
	var result:=PackedVector4Array()
	for route in routes:
		for index in range(route.points.size()-1):
			var a: Array=route.points[index]
			var b: Array=route.points[index+1]
			result.append(Vector4(a[0],a[2],b[0],b[2]))
		if route.get("closed",false) and route.points.size()>1:
			var a: Array=route.points[-1]
			var b: Array=route.points[0]
			result.append(Vector4(a[0],a[2],b[0],b[2]))
	return result

func _build_collisions() -> void:
	for entry in manifest.authority_collision_boxes:
		authority_bodies.append(_collision(entry.id,_v(entry.position),_v(entry.size)))

func _build_traversal_landmarks() -> void:
	var specification: Dictionary=manifest.get("traversal",{})
	for entry in specification.get("native_collision_boxes",[]):
		native_platform_bodies.append(_collision(entry.id,_v(entry.position),_v(entry.size),false,true))
	landmark_report=Landmarks.new().build(world,specification)
	# Quiet signs on the ground explain lane identity without resembling pickups.
	for lane in manifest.lanes:
		for z in [-96.0,-48.0,48.0,96.0]:
			var sign_:=Label3D.new()
			sign_.text=lane.name.to_upper()
			sign_.font_size=32
			sign_.pixel_size=.016
			sign_.modulate=Color("c5baa0")
			sign_.outline_modulate=Color("394a45")
			sign_.position=Vector3(lane.center_x,.025,z)
			sign_.rotation_degrees=Vector3(-90,180 if z>0 else 0,0)
			world.add_child(sign_)

func _traversal_bounds() -> AABB:
	var bounds: Array=manifest.bounds.get("actor_xz",manifest.bounds.authority_xz)
	var radius: float=manifest.bounds.hero_radius
	return AABB(Vector3(bounds[0]+radius,0,bounds[2]+radius),Vector3(bounds[1]-bounds[0]-2*radius,float(manifest.bounds.get("altitude_ceiling",24)),bounds[3]-bounds[2]-2*radius))

func _build_army_audio() -> bool:
	audio=Node.new()
	audio.set_script(TraversalAudio)
	audio.name="TraversalAudio"
	world.add_child(audio)
	# Audio owns loading the saved value; do not overwrite it with a second default.
	audio.configure(audio.volume)
	siege_effects=SiegeEffects.new()
	siege_effects.name="SiegeEffects"
	world.add_child(siege_effects)
	siege_effects.configure(audio.volume)
	if player.has_signal("traversal_event"):
		player.traversal_event.connect(func(kind: String,position_: Vector3): audio.play_event(kind,position_))
	var army_script=load("res://scripts/lane_army.gd")
	if army_script is Script and army_script.can_instantiate():
		army=Node3D.new()
		army.set_script(army_script)
		army.name="LaneArmy"
		world.add_child(army)
		army.gold_changed.connect(_gold_changed)
		army.outcome.connect(_army_outcome)
		army.siege_event.connect(siege_effects.handle_event)
		return army.configure(manifest,player)
	return false

func _gold_changed(value: int) -> void:
	if audio and value>last_gold: audio.play_event("coin",player.global_position)
	last_gold=value

func _army_outcome(team: String) -> void:
	if goal_label: goal_label.text="%s core victory · Restart lane practice from pause" % ("SUN" if team=="sun" else "MOON")
	set_paused(true)

func _start_siege_practice() -> bool:
	# Validate the drill before disturbing current practice. Army owns gameplay.
	if not army or not army.has_method("start_siege_drill") or not army.start_siege_drill():
		practice_error="Siege practice unavailable; the current round is unchanged."
		if practice_hint_label: practice_hint_label.text=practice_error
		return false
	practice_error=""
	last_gold=0
	_clear_combat_presentation()
	teleport_to(Vector3(7,.05,-15),-25)
	set_paused(false)
	_update_practice_hud()
	return true

func _clear_combat_presentation() -> void:
	if siege_effects: siege_effects.clear()
	for parent in [projectiles,effects]:
		if not parent: continue
		for child in parent.get_children(): child.queue_free()

func _restart_army() -> void:
	practice_error=""
	last_gold=0
	_clear_combat_presentation()
	if army: army.reset()
	visit_anchor("sun-spawn")
	set_paused(false)

func _load_kits() -> void:
	var sources: Array=manifest.get("kit_sources",[{"id":"architecture","asset":"res://assets/world/architecture.glb"},{"id":"nature","asset":"res://assets/world/nature.glb"}])
	for source in sources:
		var path:=String(source.asset)
		if ResourceLoader.exists(path):
			var resource=load(path)
			if resource is PackedScene:
				kit_templates[source.id]=resource.instantiate()
				# PCK exports remap GLB to imported scenes and need not include raw GLB.
				kit_hashes[source.id]=FileAccess.get_sha256(path) if FileAccess.file_exists(path) else ""

func _find_preset(node: Node, preset: String) -> Node3D:
	if String(node.name)==preset and node is Node3D: return node
	for child in node.get_children():
		var found:=_find_preset(child,preset)
		if found: return found
	return null

func _strip_colliders(node: Node) -> void:
	for child in node.get_children():
		if child is CollisionObject3D or child is CollisionShape3D:
			node.remove_child(child)
			child.free()
		else: _strip_colliders(child)

func _build_props() -> void:
	props_root=Node3D.new()
	props_root.name="CityArt"
	world.add_child(props_root)
	for entry in manifest.props:
		var node: Node3D
		for template in kit_templates.values():
			var preset:=_find_preset(template,entry.preset)
			if preset:
				node=preset.duplicate()
				imported_prop_count+=1
				break
		if node==null:
			node=_fallback_prop(entry)
			fallback_prop_count+=1
			if manifest.get("builtin_presets",{}).get(entry.kit,[]).has(entry.preset): builtin_prop_count+=1
			elif not missing_presets.has(entry.preset): missing_presets.append(entry.preset)
		_strip_colliders(node)
		node.name=entry.id
		node.position=_v(entry.position)
		node.rotation=Vector3(0,deg_to_rad(entry.yaw_degrees),0)
		node.scale=_v(entry.scale)
		node.set_meta("preset",entry.preset)
		node.set_meta("visual_collision",entry.collision)
		props_root.add_child(node)
		if entry.kit=="skyline":
			var dimensions:=_v(entry.scale)
			_box(world,_v(entry.position)+Vector3.DOWN*.09,Vector3(dimensions.x,.18,dimensions.z),_material(Color("838a77")),"NoncollidingSkylineFooting")

func _fallback_prop(entry: Dictionary) -> Node3D:
	var root_ := Node3D.new()
	var modern:=String(entry.preset).contains("modern") or String(entry.preset).contains("transit") or String(entry.preset).contains("garden")
	var stone:=_material(Color("9fa9a4") if modern else Color("b2a083"))
	var trim:=_material(Color("344f61") if modern else Color("d2b47b"),.25)
	if entry.kit=="ground_inlay":
		var ring:=TorusMesh.new()
		ring.inner_radius=.40
		ring.outer_radius=.49
		ring.rings=32
		ring.ring_segments=8
		_mesh(root_,ring,Vector3(0,.2,0),_material(TEAL if modern else GOLD,.5))
	elif entry.kit=="lamp":
		_cylinder(root_,Vector3(0,.5,0),.12,1,trim)
		_cylinder(root_,Vector3(0,.65,0),.27,.35,_material(GOLD,0,2))
	elif entry.kit=="roof_detail":
		for tier in 4:
			var width:=.95-float(tier)*.19
			_box(root_,Vector3(0,.125+float(tier)*.25,0),Vector3(width,.22,width),trim)
	else:
		_box(root_,Vector3(0,.44,0),Vector3(.96,.88,.96),stone)
		for level in 5:
			var y:=.13+float(level)*.17
			_box(root_,Vector3(0,y,0),Vector3(1,.025,1),trim)
			for side in [-1.0,1.0]:
				for column in [-.3,0.0,.3]:
					_box(root_,Vector3(column,y+.07,side*.484),Vector3(.10,.09,.015),_material(Color("233e49")))
		_box(root_,Vector3(0,.94,0),Vector3(.8,.12,.8),trim)
	return root_

func _build_objectives() -> void:
	var landmarks:=Node3D.new()
	landmarks.name="VisualObjectives"
	world.add_child(landmarks)
	for objective in manifest.objectives:
		var node:=Node3D.new()
		node.name=objective.id
		node.position=_v(objective.position)
		node.set_meta("visual_only",true)
		landmarks.add_child(node)
		var color:=GOLD if objective.team=="sun" else TEAL
		var material:=_material(color,.5)
		var core: bool=objective.kind=="core"
		_cylinder(node,Vector3(0,.10,0),objective.radius,.20,_material(Color("8c9287")))
		_cylinder(node,Vector3(0,1.6 if core else 1.2,0),.7 if core else .4,2.8 if core else 2,material,.45 if core else .2)
		var sphere:=SphereMesh.new()
		sphere.radius=.65 if core else .38
		sphere.height=sphere.radius*2
		sphere.radial_segments=16
		sphere.rings=8
		_mesh(node,sphere,Vector3(0,3.2 if core else 2.4,0),_material(color,0,1.4),"Beacon")
	for camp in manifest.camps:
		var marker:=TorusMesh.new()
		marker.inner_radius=2.4
		marker.outer_radius=2.52
		marker.rings=32
		marker.ring_segments=6
		_mesh(landmarks,marker,_v(camp.position)+Vector3(0,.025,0),_material(TEAL,.2),camp.id)

func _build_water() -> void:
	for water in manifest.waters:
		var plane:=PlaneMesh.new()
		plane.size=Vector2(water.size_xz[0],water.size_xz[1])
		var style:="coast" if water.depth_appearance=="coastal" else "swamp"
		var material:=WorldLighting.water_material(style)
		if style=="swamp":
			_configure_paving(material)
			material.set_shader_parameter("swamp_overlay",true)
			material.set_shader_parameter("overlay_size",plane.size)
			material.set_shader_parameter("overlay_center",Vector2(water.position[0],water.position[2]))
		_mesh(world,plane,_v(water.position),material,water.id)

func _build_lighting() -> void:
	world_environment=WorldEnvironment.new()
	world_environment.name="CityAtmosphere"
	world_environment.environment=Environment.new()
	world.add_child(world_environment)
	sun=DirectionalLight3D.new()
	world.add_child(sun)
	lighting=WorldLighting.new()
	lighting.configure(world_environment.environment,sun,world,manifest.lights)
	set_phase(0)

func _build_player() -> void:
	projectiles=Node3D.new()
	projectiles.name="Projectiles"
	world.add_child(projectiles)
	effects=Node3D.new()
	effects.name="TransientEffects"
	world.add_child(effects)
	player=CharacterBody3D.new()
	player.set_script(PlayerScript)
	player.name="Rama"
	world.add_child(player)
	var settings: Dictionary=Bindings.read_config()
	if settings.ok:
		var saved: ConfigFile=settings.config
		var sensitivity_value: Variant=saved.get_value("controls","sensitivity",1.0)
		if typeof(sensitivity_value) in [TYPE_INT,TYPE_FLOAT] and is_finite(float(sensitivity_value)):
			player.sensitivity=.0024*clampf(float(sensitivity_value),.35,2.5)
		var invert_value: Variant=saved.get_value("controls","invert_y",false)
		if invert_value is bool: player.invert_y=invert_value
	for child in player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D: child.shape.radius=manifest.bounds.hero_radius
	player.camera.far=380
	player.fired.connect(_fire)
	player.pulse.connect(_pulse)
	player.active=true
	visit_anchor("sun-spawn")
	start_position=player.position
	var anchors: Array=[]
	for anchor in manifest.get("traversal",{}).get("anchors",[]): anchors.append({"id":anchor.id,"position":_v(anchor.position)})
	if player.has_method("configure_traversal"): player.configure_traversal(anchors,_traversal_bounds())
	review_camera=Camera3D.new()
	review_camera.name="ReviewCamera"
	review_camera.far=500
	world.add_child(review_camera)

func _build_ui() -> void:
	ui=CanvasLayer.new()
	ui.name="WorldInterface"
	ui.process_mode=Node.PROCESS_MODE_ALWAYS
	add_child(ui)
	hud=Control.new()
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter=Control.MOUSE_FILTER_IGNORE
	ui.add_child(hud)
	var title:=_card(hud,Vector2(20,20),Vector2(535,132))
	title.name="TitleCard"
	var copy:=VBoxContainer.new()
	title.add_child(copy)
	copy.add_child(_label("YUGA  /  CONFLUENCE",21,GOLD))
	location_label=_label("Surya arrival court",17,CREAM)
	copy.add_child(location_label)
	status_label=_label("OFFLINE LANE PRACTICE · 140 × 260 m",12,Color("aec2c3"))
	copy.add_child(status_label)
	score_label=_label("Wave 1 · Gold 0 · Sun core 100 · Moon core 100",13,CREAM)
	copy.add_child(score_label)
	map_control=Atlas.new()
	map_control.name="WorldAtlas"
	map_control.data=manifest
	map_control.mouse_filter=Control.MOUSE_FILTER_IGNORE
	hud.add_child(map_control)
	map_control.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	map_control.offset_left=-196
	map_control.offset_right=-20
	map_control.offset_top=20
	map_control.offset_bottom=356
	var legend:=_label("▲ Sun  ·  ■ Moon\n◇ Tether  ·  ● You\n◎ Siege engine",11,CREAM)
	legend.name="AtlasLegend"
	hud.add_child(legend)
	legend.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	legend.offset_left=-184
	legend.offset_right=-32
	legend.offset_top=292
	legend.offset_bottom=344
	var help:=_card(hud,Vector2(20,-94),Vector2(330,74))
	help.name="ControlsCard"
	help.set_anchors_preset(Control.PRESET_BOTTOM_LEFT,true)
	var bottom:=VBoxContainer.new()
	help.add_child(bottom)
	for index in range(2):
		var row:=_label("",13,CREAM if index==0 else Color("aec2c3"))
		row.clip_text=true
		row.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
		bottom.add_child(row)
		help_labels.append(row)
	phase_label=help_labels[1]
	_refresh_control_labels()
	var ability:=_card(hud,Vector2(-280,-154),Vector2(260,134))
	ability.name="TraversalStatus"
	ability.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT,true)
	var energy_column:=VBoxContainer.new()
	ability.add_child(energy_column)
	ability_label=_label("VAYU LIFT · GROUNDED",13,GOLD)
	energy_column.add_child(ability_label)
	energy_bar=ProgressBar.new()
	energy_bar.custom_minimum_size=Vector2(220,15)
	energy_bar.show_percentage=true
	energy_bar.mouse_filter=Control.MOUSE_FILTER_IGNORE
	energy_column.add_child(energy_bar)
	goal_label=_label("Aim at a gold ring · G to tether",12,CREAM)
	goal_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	goal_label.custom_minimum_size=Vector2(220,48)
	energy_column.add_child(goal_label)
	var crosshair:=_label("·",30,CREAM)
	crosshair.name="Crosshair"
	hud.add_child(crosshair)
	crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	crosshair.offset_left=-5
	crosshair.offset_top=-20
	crosshair.offset_right=5
	crosshair.offset_bottom=22
	pause_panel=PanelContainer.new()
	pause_panel.name="PausePanel"
	ui.add_child(pause_panel)
	pause_panel.add_theme_stylebox_override("panel",_panel_style())
	pause_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	pause_scroll=ScrollContainer.new()
	pause_scroll.name="MenuScroll"
	pause_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	pause_scroll.follow_focus=true
	pause_panel.add_child(pause_scroll)
	var menu:=VBoxContainer.new()
	menu.name="MenuActions"
	menu.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	menu.add_theme_constant_override("separation",6)
	pause_scroll.add_child(menu)
	menu.add_child(_label("CONFLUENCE",22,GOLD))
	practice_mode_label=_label("OFFLINE LANE PRACTICE",12,Color("aec2c3"))
	menu.add_child(practice_mode_label)
	_button(menu,"Continue practice",func():set_paused(false))
	siege_practice_button=_button(menu,"Siege practice · enter drill",_start_siege_practice)
	siege_practice_button.name="SiegePractice"
	practice_hint_label=_label("Try cannon carts and royal chariots in the central court. Blasts damage troops; your hero takes no damage.",13,CREAM)
	practice_hint_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	menu.add_child(practice_hint_label)
	_button(menu,"Day / night",func():set_night(not night))
	_button(menu,"Visit Lanka coast",func():teleport_to(Vector3(-40,.05,14),180);set_paused(false))
	_button(menu,"Visit Metro gardens",func():teleport_to(Vector3(40,.05,14),180);set_paused(false))
	_button(menu,"Controls / remap keys",_open_controls)
	_button(menu,"Restart lane practice",_restart_army)
	volume_label=_label("Sound",12,CREAM)
	menu.add_child(volume_label)
	var volume:=HSlider.new()
	volume.name="WorldVolume"
	volume.min_value=0
	volume.max_value=1
	volume.step=.05
	volume.custom_minimum_size.y=24
	volume.value=audio.volume if audio else .35
	menu.add_child(volume)
	pause_actions.append(volume)
	volume.value_changed.connect(_set_volume)
	_set_volume(volume.value,false)
	_button(menu,"Return to courtyard",return_to_courtyard)
	_button(menu,"Quit game",func():get_tree().quit())
	pause_panel.visible=false
	controls_overlay=Control.new()
	controls_overlay.set_script(ControlsOverlay)
	ui.add_child(controls_overlay)
	controls_overlay.closed.connect(_close_controls)
	controls_overlay.bindings_changed.connect(_refresh_control_labels)
	_wire_pause_focus()
	_layout_pause_panel()

func _refresh_control_labels() -> void:
	if help_labels.size()!=2: return
	var mode: String=String(player.traversal_report().get("mode","grounded")) if player and player.has_method("traversal_report") else "grounded"
	if mode=="flight": help_labels[0].text="%s rise · %s descend" % [Bindings.label("jump"),Bindings.label("descend")]
	elif mode=="grapple": help_labels[0].text="%s release tether" % Bindings.label("grapple")
	else: help_labels[0].text="LMB fire · %s pulse · %s dash" % [Bindings.label("pulse"),Bindings.label("dash")]
	help_labels[1].text="F2 controls & remap · Esc pause"

func _open_controls() -> void:
	controls_return_to_pause=paused
	set_paused(true)
	pause_panel.hide()
	controls_overlay.open()

func _close_controls() -> void:
	_refresh_control_labels()
	set_paused(controls_return_to_pause)

func _set_volume(value: float,save: bool=true) -> void:
	if audio: audio.set_volume(value)
	if siege_effects: siege_effects.set_volume(value)
	if volume_label: volume_label.text="Sound · muted" if value<=0 else "Sound · %d%%" % roundi(value*100)
	if save:
		var result: Dictionary=Bindings.merge_settings({"audio":{"volume":value}})
		if not result.ok and volume_label: volume_label.text="Sound · active now; save unavailable"

func _panel_style() -> StyleBoxFlat:
	var style:=StyleBoxFlat.new()
	style.bg_color=Color(0.025,.065,.085,.94)
	style.border_color=Color(.6,.75,.72,.35)
	style.set_border_width_all(1)
	style.set_corner_radius_all(12)
	style.content_margin_left=18
	style.content_margin_right=18
	style.content_margin_top=14
	style.content_margin_bottom=14
	return style

func _card(parent: Control, position_: Vector2, size_: Vector2) -> PanelContainer:
	var panel:=PanelContainer.new()
	panel.position=position_
	panel.custom_minimum_size=size_
	panel.mouse_filter=Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel",_panel_style())
	parent.add_child(panel)
	return panel

func _label(text_: String, font_size: int, color: Color) -> Label:
	var label:=Label.new()
	label.text=text_
	label.add_theme_font_size_override("font_size",font_size)
	label.add_theme_color_override("font_color",color)
	label.mouse_filter=Control.MOUSE_FILTER_IGNORE
	return label

func _button(parent: Control, text_: String, callback: Callable) -> Button:
	var button:=Button.new()
	button.text=text_
	button.custom_minimum_size=Vector2(0,40)
	button.add_theme_font_size_override("font_size",14)
	button.add_theme_color_override("font_color",CREAM)
	for state in ["normal","hover","pressed","focus"]:
		var style:=StyleBoxFlat.new()
		style.bg_color=Color("20444a") if state!="normal" else Color("17343a")
		style.border_color=GOLD if state=="focus" else Color("537873")
		style.set_border_width_all(2 if state=="focus" else 1)
		style.content_margin_left=10
		style.content_margin_right=10
		button.add_theme_stylebox_override(state,style)
	button.pressed.connect(callback)
	parent.add_child(button)
	pause_actions.append(button)
	return button

func _wire_pause_focus() -> void:
	for index in range(pause_actions.size()):
		var control:=pause_actions[index]
		control.focus_mode=Control.FOCUS_ALL
		control.focus_next=control.get_path_to(pause_actions[(index+1)%pause_actions.size()])
		control.focus_previous=control.get_path_to(pause_actions[posmod(index-1,pause_actions.size())])

func _layout_pause_panel() -> void:
	if not pause_panel: return
	var screen:=get_viewport().get_visible_rect().size
	var size_:=Vector2(minf(480,screen.x-32),minf(600,screen.y-32))
	pause_panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	pause_panel.size=size_
	pause_panel.position=(screen-pause_panel.size)/2

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.echo: return
	if controls_overlay and controls_overlay.visible: return
	if event.is_action_pressed("help_controls"):
		_open_controls()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("pause_game"):
		set_paused(not paused)
		get_viewport().set_input_as_handled()
	elif not paused and event.is_action_pressed("world_night"): set_night(not night)
	elif not paused and event.is_action_pressed("world_respawn"): _restart_army()
	elif not paused and event.is_action_pressed("world_overview"): set_overview(not overview)

func _process(delta: float) -> void:
	if not world_ready: return
	if paused: _layout_pause_panel()
	if not paused and not is_equal_approx(phase,target_phase):
		phase=move_toward(phase,target_phase,delta*.45)
		phase_clock+=delta
		if phase_clock>.08 or is_equal_approx(phase,target_phase):
			lighting.set_phase(phase)
			phase_clock=0
	ui_clock+=delta
	if ui_clock>.12:
		ui_clock=0
		location_label.text=district_at(player.position)
		var drill: bool=army.report().get("siege_drill",false) if army else false
		status_label.text="OFFLINE %s · %s · %d / 12 arrows" % ["SIEGE DRILL" if drill else "PRACTICE","Moonlight" if phase>.5 else "Golden hour",player.ammo]
		_update_practice_hud()
		map_control.hero_position=player.position
		map_control.queue_redraw()

func _physics_process(_delta: float) -> void:
	if not world_ready or paused: return
	if not player.position.is_finite():
		visit_anchor("sun-spawn")
		return
	var bounds: Array=manifest.bounds.get("actor_xz",manifest.bounds.authority_xz)
	var radius: float=manifest.bounds.hero_radius
	var clamped:=player.position
	clamped.x=clampf(clamped.x,bounds[0]+radius,bounds[1]-radius)
	clamped.z=clampf(clamped.z,bounds[2]+radius,bounds[3]-radius)
	clamped.y=minf(clamped.y,float(manifest.bounds.get("altitude_ceiling",24)))
	if clamped.x!=player.position.x: player.velocity.x=0
	if clamped.z!=player.position.z: player.velocity.z=0
	player.position=clamped
	if player.position.y<-.5: visit_anchor("sun-spawn")

func _update_practice_hud() -> void:
	_refresh_control_labels()
	var siege_drill:=false
	var enemy_siege:=0
	if army:
		var battle: Dictionary=army.report()
		var cores: Dictionary=battle.get("cores",{})
		siege_drill=battle.get("siege_drill",false)
		if army.has_method("minimap_units"): map_control.units=army.minimap_units()
		for unit in map_control.units:
			if unit.get("team","")=="moon" and unit.get("role","") in ["cannon_cart","royal_chariot"]: enemy_siege+=1
		if siege_drill:
			var roles: Dictionary=battle.get("roles_alive",{})
			score_label.text="Enemy siege %d · Cannons %d · Chariots %d · Gold %d" % [enemy_siege,roles.get("cannon_cart",0),roles.get("royal_chariot",0),battle.get("gold",0)]
		else:
			score_label.text="Wave %d · Gold %d · Sun core %d · Moon core %d" % [battle.get("waves",0),battle.get("gold",0),cores.get("sun",100),cores.get("moon",100)]
		if practice_mode_label: practice_mode_label.text="OFFLINE SIEGE DRILL" if siege_drill else "OFFLINE LANE PRACTICE"
		if siege_practice_button: siege_practice_button.text="Siege practice · restart drill" if siege_drill else "Siege practice · enter drill"
		if practice_hint_label:
			practice_hint_label.text=practice_error if not practice_error.is_empty() else ("Break enemy engines before impact to protect Sun troops. Your hero takes no damage. Restart lane practice exits this drill." if siege_drill else "Try cannon carts and royal chariots in the central court. Blasts damage troops; your hero takes no damage.")
		if not String(battle.get("winner","")).is_empty():
			goal_label.text="%s wins · Restart lane practice in pause" % String(battle.winner).to_upper()
			return
	if not player.has_method("traversal_report"): return
	var report: Dictionary=player.traversal_report()
	var mode: String=String(report.get("mode","grounded"))
	var energy: float=float(report.get("energy",100))
	energy_bar.max_value=float(report.get("max_energy",100))
	energy_bar.value=energy
	ability_label.text="VAYU LIFT · %s · %dm" % [mode.to_upper(),roundi(player.position.y)]
	var flight_cd: float=float(report.get("flight_cooldown",0))
	var grapple_cd: float=float(report.get("grapple_cooldown",0))
	var candidate: Dictionary=report.get("candidate",{})
	if mode=="grapple" or mode=="grappling":
		traversal_seen=true
		goal_label.text="%s release tether · %s flight" % [Bindings.label("grapple"),Bindings.label("fly")]
	elif mode=="flight" or mode=="flying":
		traversal_seen=true
		goal_label.text="%s rise · %s descend · %s land\nEnergy refills on the ground" % [Bindings.label("jump"),Bindings.label("descend"),Bindings.label("fly")]
	elif siege_drill:
		goal_label.text="Break enemy engines to cancel shots.\nBlast marks affect troops only." if enemy_siege>0 else "Enemy engines cleared.\nEsc: restart drill or lane practice."
	elif not candidate.is_empty():
		var distance: float=player.global_position.distance_to(candidate.position)
		var availability:="Tether ready" if grapple_cd<=0 else "Tether cooling %.1fs" % grapple_cd
		if energy<18: availability="Needs 18 energy · land to refill"
		goal_label.text="%s · GOLD RING · %.0f m\n%s" % [Bindings.label("grapple"),distance,availability]
	elif flight_cd>0 or grapple_cd>0:
		goal_label.text="Flight %.1fs · Tether %.1fs\n%s" % [flight_cd,grapple_cd,String(report.get("status","Aim at a gold ring"))]
	else:
		var context:="Push a lane; finish foes for gold" if traversal_seen else "Optional: reach a raised landing court"
		if energy<18: context="Land to refill traversal energy"
		elif String(report.get("status","")).begins_with("Aim at"): context="No clear anchor in your aim"
		goal_label.text="%s tether: aim at a gold ring ≤36m\n%s" % [Bindings.label("grapple"),context]

func district_at(position_: Vector3) -> String:
	var selected:="Confluence streets"
	for district in manifest.districts:
		var bounds: Array=district.bounds_xz
		if position_.x>=bounds[0] and position_.x<=bounds[1] and position_.z>=bounds[2] and position_.z<=bounds[3]: selected=district.name
	return selected

func set_phase(value: float) -> void:
	phase=clampf(value,0,1)
	target_phase=phase
	night=phase>.5
	if lighting: lighting.set_phase(phase)

func set_review_phase(value: float) -> void:
	set_phase(value)

func set_night(value: bool) -> void:
	night=value
	target_phase=1.0 if value else 0.0

func release_actions() -> void:
	Bindings.release_gameplay()
	if player:
		if player.has_method("cancel_traversal"): player.cancel_traversal("world transition")
		player.velocity=Vector3.ZERO
		player.dash_time=0
		player.dash_direction=Vector3.ZERO

func set_paused(value: bool) -> void:
	paused=value
	release_actions()
	get_tree().paused=value
	if pause_panel: pause_panel.visible=value
	if player: player.active=not value and not overview
	if audio: audio.set_suspended(value or overview)
	if siege_effects: siege_effects.set_suspended(value or overview)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if value or overview else Input.MOUSE_MODE_CAPTURED
	if not value: get_viewport().gui_release_focus()
	if value and pause_panel:
		_layout_pause_panel()
		_update_practice_hud()
		var buttons:=pause_panel.find_children("*","Button",true,false)
		if not buttons.is_empty(): buttons[0].grab_focus()

func _focus_lost() -> void:
	if not world_ready: return
	if controls_overlay and controls_overlay.visible:
		controls_overlay.cancel_capture()
		controls_return_to_pause=true
	set_paused(true)
	if controls_overlay and controls_overlay.visible: pause_panel.hide()

func teleport_to(position_: Vector3, yaw_degrees: float=180.0) -> void:
	if not position_.is_finite() or not is_finite(yaw_degrees): return
	if overview: set_overview(false)
	release_actions()
	player.reset()
	var bounds:=_traversal_bounds()
	player.position=Vector3(clampf(position_.x,bounds.position.x,bounds.end.x),clampf(position_.y,.05,bounds.end.y),clampf(position_.z,bounds.position.z,bounds.end.z))
	var facing:=wrapf(yaw_degrees,-180,180)
	player.yaw=deg_to_rad(facing-180)
	player.visual.rotation.y=deg_to_rad(facing)
	player._update_camera()
	player.reset_physics_interpolation()
	for projectile in projectiles.get_children(): projectile.queue_free()

func visit_anchor(id: String) -> bool:
	for entries in [manifest.spawns,manifest.camps,manifest.objectives]:
		for anchor in entries:
			if anchor.id==id:
				teleport_to(_v(anchor.position)+Vector3.UP*.05,anchor.get("yaw_degrees",180.0))
				return true
	return false

func set_overview(value: bool) -> void:
	overview=value
	release_actions()
	if army: army.process_mode=Node.PROCESS_MODE_DISABLED if value else Node.PROCESS_MODE_PAUSABLE
	if audio: audio.set_suspended(value or paused)
	if siege_effects: siege_effects.set_suspended(value or paused)
	player.active=not value and not paused
	if value:
		review_camera.position=Vector3(118,155,195)
		review_camera.look_at(Vector3(0,0,0))
		review_camera.current=true
	else: player.camera.current=true
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if value or paused else Input.MOUSE_MODE_CAPTURED

func get_review_camera_views() -> Array:
	return [
		{"id":"city-overview","position":[126,166,198],"target":[0,0,0],"phase":0.0,"fov":60},
		{"id":"sun-landing-courts","position":[0,4,-112],"target":[-20,10,-88],"phase":0.0,"fov":65},
		{"id":"central-capture-court","position":[-9,9,12],"target":[0,4,-22],"phase":0.0,"fov":65},
		{"id":"temple-avenue","position":[-3,3.6,57],"target":[-3,4,-8],"phase":0.0,"fov":65},
		{"id":"lanka-coast","position":[-47,4.6,46],"target":[-58,5,-12],"phase":0.0,"fov":65},
		{"id":"metro-gardens","position":[42,4.2,48],"target":[34,7,-22],"phase":0.0,"fov":65},
		{"id":"west-reed-court","position":[-48,2.8,8],"target":[-61,1,0],"phase":0.0,"fov":65},
		{"id":"moonlit-confluence","position":[-5,3.4,48],"target":[-8,4,-20],"phase":1.0,"fov":65},
		{"id":"night-swamp","position":[-48,2.8,8],"target":[-61,1,0],"phase":1.0,"fov":65}
	]

func _fire(origin: Vector3, direction: Vector3, empowered: bool) -> void:
	if projectiles.get_child_count()>=32: return
	var projectile:=Node3D.new()
	projectile.set_script(ProjectileScript)
	projectile.position=origin
	projectile.direction=direction
	projectile.damage=35 if empowered else 25
	projectile.ignore.append(player.get_rid())
	projectile.impacted.connect(func(point: Vector3,target: Node):
		_impact(point)
		if audio and is_instance_valid(target) and target.is_in_group("lane_enemy"): audio.play_event("minion_hit",point)
	)
	projectiles.add_child(projectile)

func _impact(point: Vector3) -> void:
	if effects.get_child_count()>=24: return
	var sphere:=SphereMesh.new()
	sphere.radius=.12
	sphere.height=.24
	sphere.radial_segments=8
	sphere.rings=4
	var spark:=_mesh(effects,sphere,point,_material(GOLD,0,2),"ArrowSpark")
	var tween:=spark.create_tween()
	tween.tween_property(spark,"scale",Vector3.ONE*.01,.22)
	tween.tween_callback(spark.queue_free)

func _pulse(origin: Vector3) -> void:
	if army:
		var hits: int=army.pulse(origin,6.0,45)
		if hits>0 and audio: audio.play_event("minion_hit",origin)
	if effects.get_child_count()>=24: return
	var torus:=TorusMesh.new()
	torus.inner_radius=.45
	torus.outer_radius=.5
	torus.rings=32
	torus.ring_segments=6
	var ring:=_mesh(effects,torus,Vector3(origin.x,.10,origin.z),_material(GOLD,0,1),"SunPulse")
	var tween:=ring.create_tween()
	tween.tween_property(ring,"scale",Vector3(12,.1,12),.6)
	tween.tween_callback(ring.queue_free)

func build_report() -> Dictionary:
	return {"ready":world_ready,"manifest_path":manifest_path,"manifest_sha256":FileAccess.get_sha256(manifest_path),"manifest_revision":manifest.get("revision",0),"authority_boxes":authority_bodies.size(),"native_platforms":native_platform_bodies.size(),"native_bounds":manifest.bounds.get("actor_xz",[]),"landmarks":landmark_report,"army":army.report() if army else {},"traversal":player.traversal_report() if player and player.has_method("traversal_report") else {},"audio":audio.get_diagnostics() if audio else {},"siege_effects":siege_effects.report() if siege_effects else {},"siege_ui":{"pause_rect":str(pause_panel.get_global_rect()) if pause_panel else "","focus_targets":pause_actions.size(),"practice_label":practice_mode_label.text if practice_mode_label else ""},"floor_bodies":1,"props":manifest.get("props",[]).size(),"imported_props":imported_prop_count,"procedural_props":fallback_prop_count,"builtin_procedural_props":builtin_prop_count,"missing_presets":missing_presets,"kit_sha256":kit_hashes,"kit_hash_scope":"Raw source hashes when available; empty for remapped exported scene resources.","hero_model_ready":player.model_ready if player else false,"hero_radius":manifest.get("bounds",{}).get("hero_radius",0),"lanes":manifest.get("lanes",[]).size(),"camps":manifest.get("camps",[]).size(),"objectives":manifest.get("objectives",[]).size(),"lighting":lighting.diagnostics() if lighting else {},"scope":"Offline 140×260m native lane practice with raised decks, limited flight and tether relics. Eight central boxes retain browser dimensions; expanded bounds/platforms/local army do not share browser authority. No online-match or commercial visual-parity claim."}

func get_build_report() -> Dictionary:
	return build_report()

func return_to_courtyard() -> void:
	release_actions()
	_clear_combat_presentation()
	get_tree().paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	get_tree().change_scene_to_file("res://scenes/courtyard.tscn")

func _exit_tree() -> void:
	if get_tree(): get_tree().paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
