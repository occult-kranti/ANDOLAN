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
const RelaySession = preload("res://scripts/relay_session.gd")
const MythicEnvironment = preload("res://scripts/mythic_environment.gd")
const UltimateSession = preload("res://scripts/ultimate_session.gd")
const UltimateEffects = preload("res://scripts/ultimate_effects.gd")
const InvocationPanel = preload("res://scripts/invocation_panel.gd")
const InvocationAudio = preload("res://scripts/invocation_audio.gd")
const RamaRuntime = preload("res://scripts/rama_hero_runtime.gd")
const RamaPanel = preload("res://scripts/rama_hero_panel.gd")
const RamaHUD = preload("res://scripts/rama_hero_hud.gd")
const HeroUI = preload("res://scripts/hero_ui_theme.gd")
const Atlas = preload("res://scripts/world_atlas.gd")
const WorldOutcome = preload("res://scripts/world_outcome_summary.gd")
const RUNTIME_MANIFEST := "res://assets/world/confluence-map.json"
const SOURCE_MANIFEST := "res://art/world/confluence-map.json"
const CREAM := Color("f0e5d0")
const GOLD := Color("dfb96e")
const TEAL := Color("6cb9c1")

var rama_runtime: Node3D
var rama_kit: Node3D
var rama_effects: Node3D
var rama_panel: Control
var rama_hud: Control
var rama_return_to_pause := false
var rama_return_focus: WeakRef
var rama_button: Button
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
var relays: Node3D
var invocations: Node
var ultimate_fx: Node3D
var invocation_audio: Node
var invocation_panel: Control
var invocation_button: Button
var invocation_label: Label
var invocation_detail: Label
var invocation_return_to_pause := false
var invocation_return_focus: WeakRef
var invocation_notice := ""
var relay_labels: Array[Label] = []
var relay_hint: Label
var siege_practice_button: Button
var practice_mode_label: Label
var practice_hint_label: Label
var practice_error := ""
var pause_actions: Array[Control] = []
var pause_scroll: ScrollContainer
var controls_overlay: Control
var controls_return_to_pause := false
var controls_return_focus: WeakRef
var continue_practice_button: Button
var restart_practice_button: Button
var energy_bar: ProgressBar
var ability_label: Label
var score_label: Label
var objective_label: Label
var lane_label: Label
var outcome_summary: VBoxContainer
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
var atlas_guide: PanelContainer
var atlas_guide_scroll: ScrollContainer
var atlas_guide_return: Label
var atlas_live_details: Label
var compact_world_card: Panel
var compact_world_labels: Array[Label] = []
var _constrained_world := false
var _traversal_idle := false
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
var _overview_copy: VBoxContainer
var _overview_heading: Label
var _overview_content_rect:=Rect2()
var _overview_geometry_points:=PackedVector3Array()
var _overview_layout_busy:=false


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
	MythicEnvironment.configure(world, "confluence")
	_build_lighting()
	load("res://scripts/world_roof_loggia.gd").configure(world)
	var frontage_install: Dictionary = load("res://scripts/world_lane_frontage.gd").configure(world)
	if not frontage_install.get("ok",false):
		push_error("Confluence frontage could not configure: "+String(frontage_install.get("reason","unknown")))
		return
	_build_player()
	if not _build_army_audio() or not player.traversal_report().get("enabled",false):
		push_error("Confluence requires a configured army and traversal controller.")
		return
	relays=RelaySession.new()
	relays.name="TriadRelays"
	world.add_child(relays)
	relays.configure(army,player)
	if not _build_invocations():
		push_error("Confluence invocation practice could not be configured.")
		return
	rama_runtime = RamaRuntime.new()
	world.add_child(rama_runtime)
	if not rama_runtime.configure(player, army):
		push_error("Rama hero kit could not be configured")
		return
	rama_kit = rama_runtime.kit
	rama_effects = rama_runtime.effects
	_build_ui()
	for template in kit_templates.values(): template.free()
	kit_templates.clear()
	get_window().focus_exited.connect(_focus_lost)
	world_ready=true
	Input.mouse_mode=Input.MOUSE_MODE_CAPTURED
	print("YUGA_CONFLUENCE_READY ",JSON.stringify(build_report()))

func _build_invocations() -> bool:
	invocations = UltimateSession.new()
	invocations.name = "InvocationPractice"
	world.add_child(invocations)
	if not invocations.configure(army): return false
	ultimate_fx = UltimateEffects.new()
	ultimate_fx.name = "InvocationEffects"
	world.add_child(ultimate_fx)
	invocation_audio = InvocationAudio.new()
	invocation_audio.name = "InvocationAudio"
	world.add_child(invocation_audio)
	invocation_audio.set_volume(audio.volume if audio else .35)
	if not invocation_audio.report().get("ready", false): return false
	invocations.invocation_event.connect(_invocation_event)
	return true

func _invocation_event(event: Dictionary) -> void:
	if ultimate_fx: ultimate_fx.consume_event(event)
	if invocation_audio: invocation_audio.consume_event(event)
	if not player: return
	var kind: String = event.get("kind", "")
	if kind == "begin":
		invocation_notice = "Preparing · aim locked"
		var hero: String = event.get("hero_id", "rama")
		var clip := "cast3" if hero in ["sita", "draupadi", "chitrangada", "ulupi"] else ("cast2" if hero in ["rama", "arjuna", "meghnad"] else "cast1")
		player.begin_invocation(float(event.get("timing", {}).get("windup_s", .8)), clip)
	elif kind in ["release", "cancel", "reset"]:
		player.finish_invocation_pose()
	if kind in ["impact", "tick"]:
		var receipts: Array = event.get("receipts", [])
		if not receipts.is_empty(): invocation_notice = "%d troop effects applied" % receipts.size()
	elif kind == "cancel": invocation_notice = String(event.get("reason", "Invocation cancelled"))
	elif kind == "release": invocation_notice = "Released · movement restored"
	elif kind == "end": invocation_notice = "Invocation ended"
	elif kind == "reset": invocation_notice = "Ready · aim, then cast"

func cast_invocation() -> Dictionary:
	var reason := ""
	if not world_ready or not invocations: reason = "Invocation practice is loading."
	elif paused or overview or get_tree().paused or not player.active: reason = "Return to practice to cast."
	elif not player.is_on_floor() or player.traversal.mode != "ground" or player.position.y > .35: reason = "Land on the street to cast."
	elif player.reload_remaining > 0: reason = "Finish reloading before casting."
	elif player.invocation_preparing: reason = "An invocation is preparing."
	if not reason.is_empty():
		invocation_notice = reason
		return {"accepted":false,"reason":reason}
	var state: Dictionary = invocations.report()
	var distance := clampf(float(state.get("selected_range_m", 8.0)), 1.0, 32.0)
	var forward: Vector3 = -player.pivot.global_basis.z
	forward.y = 0
	if forward.length_squared() < .001: forward = Vector3.FORWARD
	forward = forward.normalized()
	var target: Vector3 = player.global_position + forward * distance
	var centre := get_viewport().get_visible_rect().size * .5
	var start: Vector3 = player.camera.project_ray_origin(centre)
	var direction: Vector3 = player.camera.project_ray_normal(centre)
	var hit := get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(start, start + direction * 80.0, 1, [player.get_rid()]))
	if not hit.is_empty():
		var offset: Vector3 = hit.position - player.global_position
		offset.y = 0
		target = player.global_position + offset.limit_length(distance)
	target.y = 0
	var result: Dictionary = invocations.request_cast(player.global_position, forward, target)
	invocation_notice = "Preparing · aim locked" if result.get("accepted", false) else String(result.get("reason", "Cannot cast here."))
	_update_invocation_hud()
	return result

func _open_invocations() -> void:
	if not world_ready or not invocation_panel or invocation_panel.visible: return
	invocation_return_to_pause = paused
	invocation_return_focus = _remember_pause_focus()
	set_paused(true)
	pause_panel.hide()
	invocation_panel.update_session(invocations.report())
	invocation_panel.open()

func _close_invocations() -> void:
	set_paused(invocation_return_to_pause)
	if invocation_return_to_pause: _restore_pause_focus(invocation_return_focus)
	invocation_return_focus = null

func _select_invocation(hero: String) -> void:
	if not invocations.select_invocation(hero):
		invocation_panel.set_notice("This invocation is unavailable.", true)
		return
	invocation_notice = "Aim, then cast · affects lane troops"
	invocation_panel.update_session(invocations.report())
	invocation_panel.close()
	_update_invocation_hud()

func _update_invocation_hud() -> void:
	if not invocations or not invocation_label: return
	var state: Dictionary = invocations.report()
	var hero := String(state.get("selected_hero", "rama")).capitalize()
	var cooldown := float(state.get("cooldown_remaining", 0.0))
	invocation_label.text = "%s  /  %s" % [hero.to_upper(), "%.1fs" % cooldown if cooldown > 0 else "READY"]
	invocation_detail.text = "%s cast · %s choose\n%s" % [Bindings.label("ultimate"), Bindings.label("open_invocations"), invocation_notice if not invocation_notice.is_empty() else "Channel a legend through Rama"]
	if invocation_panel and invocation_panel.visible: invocation_panel.update_session(state)

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
	if goal_label: goal_label.text=WorldOutcome.headline(team)+" · %s pause · %s restart" % [Bindings.label("pause_game"),Bindings.label("world_respawn")]
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
	if relays: relays.reset()
	teleport_to(Vector3(7,.05,-15),-25)
	set_paused(false)
	_update_practice_hud()
	return true

func _clear_combat_presentation() -> void:
	if siege_effects: siege_effects.clear()
	if invocations: invocations.cancel_active("Practice changed.")
	if ultimate_fx: ultimate_fx.reset()
	if rama_runtime: rama_runtime.reset("practice changed")
	if invocation_audio: invocation_audio.reset()
	for parent in [projectiles,effects]:
		if not parent: continue
		for child in parent.get_children(): child.queue_free()

func _restart_army() -> void:
	practice_error=""
	last_gold=0
	_clear_combat_presentation()
	if army: army.reset()
	if relays: relays.reset()
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
		if entry.id in ["lane-0-mid-inlay","lane-1-mid-inlay","lane-2-mid-inlay"]:
			# These old reflective circles obscure the functional relay's progress
			# paving. Keep their authored identity; relay_art owns presentation here.
			node.visible=false
			node.set_meta("superseded_by","TriadRelays")
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
	hud.theme = HeroUI.create()
	ui.add_child(hud)
	var title:=_card(hud,Vector2(20,20),Vector2(370,154))
	title.name="TitleCard"
	title.resized.connect(_layout_world_hud)
	var copy:=VBoxContainer.new()
	copy.add_theme_constant_override("separation",HeroUI.SPACE_XS)
	title.add_child(copy)
	copy.add_child(_label("YUGA  /  CONFLUENCE",HeroUI.TYPE_HUD_TITLE,GOLD))
	location_label=_label("Surya arrival court",HeroUI.TYPE_HUD,CREAM)
	copy.add_child(location_label)
	status_label=_label("OFFLINE LANE PRACTICE",HeroUI.TYPE_HUD_DETAIL,HeroUI.MIST)
	copy.add_child(status_label)
	score_label=_label("Lane status unavailable",HeroUI.TYPE_HUD,HeroUI.CREAM)
	score_label.clip_text=true
	score_label.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	copy.add_child(score_label)
	lane_label=_label("",HeroUI.TYPE_HUD_DETAIL,HeroUI.MIST)
	lane_label.name="LanePopulation"
	lane_label.clip_text=true
	lane_label.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	copy.add_child(lane_label)
	objective_label=_label("",HeroUI.TYPE_HUD,HeroUI.CREAM)
	objective_label.name="LaneObjective"
	objective_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	objective_label.max_lines_visible=2
	objective_label.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	copy.add_child(objective_label)
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
	var legend:=_label("",HeroUI.TYPE_HUD_DETAIL,HeroUI.CREAM)
	legend.name="AtlasLegend"
	map_control.add_child(legend)
	legend.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	legend.offset_left=12
	legend.offset_right=-12
	legend.offset_top=-78
	legend.offset_bottom=-8
	_build_atlas_guide()
	_build_compact_world()
	var relay_card:=_card(hud,Vector2(20,186),Vector2(370,82))
	relay_card.name="RelayStatus"
	var relay_column:=VBoxContainer.new()
	relay_column.add_theme_constant_override("separation",6)
	relay_card.add_child(relay_column)
	var relay_row:=HBoxContainer.new()
	relay_row.add_theme_constant_override("separation",10)
	relay_column.add_child(relay_row)
	for index in 3:
		var label:=_label("",HeroUI.TYPE_HUD_DETAIL,CREAM)
		label.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		label.clip_text=true
		label.max_lines_visible=2
		label.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
		relay_row.add_child(label)
		relay_labels.append(label)
	relay_hint=_label("Hold a relay: supplies every 5s · Contest stops supply",HeroUI.TYPE_HUD_DETAIL,HeroUI.MIST)
	relay_hint.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	relay_hint.max_lines_visible=3
	relay_hint.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
	relay_column.add_child(relay_hint)
	var help:=_card(hud,Vector2(20,-214),Vector2(238,72))
	help.name="ControlsCard"
	help.resized.connect(_layout_world_hud)
	help.set_anchors_preset(Control.PRESET_BOTTOM_LEFT,true)
	var bottom:=VBoxContainer.new()
	bottom.add_theme_constant_override("separation",6)
	help.add_child(bottom)
	for index in range(2):
		var row:=_label("",HeroUI.TYPE_HUD_DETAIL,CREAM if index==0 else HeroUI.MIST)
		row.clip_text=true
		row.text_overrun_behavior=TextServer.OVERRUN_TRIM_ELLIPSIS
		bottom.add_child(row)
		help_labels.append(row)
	phase_label=help_labels[1]
	_refresh_control_labels()
	var ability:=_card(hud,Vector2(-252,-254),Vector2(232,116))
	ability.name="TraversalStatus"
	ability.resized.connect(_layout_world_hud)
	ability.set_anchors_preset(Control.PRESET_BOTTOM_RIGHT,true)
	var energy_column:=VBoxContainer.new()
	energy_column.add_theme_constant_override("separation",5)
	ability.add_child(energy_column)
	ability_label=_label("VAYU LIFT · GROUNDED",HeroUI.TYPE_HUD_DETAIL,GOLD)
	energy_column.add_child(ability_label)
	energy_bar=ProgressBar.new()
	energy_bar.custom_minimum_size=Vector2(200,14)
	energy_bar.show_percentage=true
	energy_bar.mouse_filter=Control.MOUSE_FILTER_IGNORE
	energy_column.add_child(energy_bar)
	goal_label=_label("Aim at a gold ring · G to tether",HeroUI.TYPE_HUD_DETAIL,CREAM)
	goal_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	goal_label.custom_minimum_size=Vector2(200,42)
	energy_column.add_child(goal_label)
	var invocation_card := _card(hud, Vector2(20,-206), Vector2(330,100))
	invocation_card.name = "InvocationStatus"
	invocation_card.visible = false
	invocation_card.set_anchors_preset(Control.PRESET_BOTTOM_LEFT, true)
	var invocation_column := VBoxContainer.new()
	invocation_card.add_child(invocation_column)
	invocation_label = _label("RAMA / READY", 14, GOLD)
	invocation_column.add_child(invocation_label)
	invocation_detail = _label("", 12, CREAM)
	invocation_detail.custom_minimum_size = Vector2(290,48)
	invocation_detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	invocation_column.add_child(invocation_detail)
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
	pause_panel.theme = HeroUI.create()
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
	outcome_summary=WorldOutcome.new()
	menu.add_child(outcome_summary)
	continue_practice_button = _button(menu,"Continue practice",func():set_paused(false))
	restart_practice_button = _button(menu,"Restart lane practice",_restart_army)
	rama_button = _button(menu,"Rama · abilities and controls",_open_rama_panel)
	invocation_button = _button(menu,"Legacy invocation studies",_open_invocations)
	invocation_button.name = "ChooseInvocation"
	siege_practice_button=_button(menu,"Siege practice · enter drill",_start_siege_practice)
	siege_practice_button.name="SiegePractice"
	practice_hint_label=_label("Try cannon carts and royal chariots in the central court. Blasts damage troops; enemy siege blasts damage Rama.",13,CREAM)
	practice_hint_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	menu.add_child(practice_hint_label)
	_button(menu,"Day / night",func():set_night(not night))
	_button(menu,"Visit Lotus relay",func():teleport_to(Vector3(0,.05,-7),0);set_paused(false))
	_button(menu,"Visit Lanka coast",func():teleport_to(Vector3(-40,.05,14),180);set_paused(false))
	_button(menu,"Visit Metro gardens",func():teleport_to(Vector3(40,.05,14),180);set_paused(false))
	_button(menu,"Controls / remap keys",_open_controls)
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
	invocation_panel = InvocationPanel.new()
	invocation_panel.name = "InvocationSelection"
	ui.add_child(invocation_panel)
	if not invocation_panel.configure(): push_error("Invocation selector could not load its catalogue.")
	invocation_panel.invocation_selected.connect(_select_invocation)
	invocation_panel.closed.connect(_close_invocations)
	invocation_panel.effects_options_changed.connect(func(options: Dictionary): ultimate_fx.set_options(options))
	ultimate_fx.set_options(invocation_panel.options())
	rama_panel = RamaPanel.new()
	ui.add_child(rama_panel)
	rama_panel.configure_effects(rama_effects)
	rama_panel.closed.connect(_close_rama_panel)
	rama_hud = RamaHUD.new()
	hud.add_child(rama_hud)
	rama_hud.configure(rama_runtime)
	hud.resized.connect(_layout_world_hud)
	rama_hud.resized.connect(_layout_world_hud)
	_layout_world_hud()
	call_deferred("_settle_world_hud")
	_update_invocation_hud()
	_wire_pause_focus()
	_layout_pause_panel()

func _refresh_control_labels() -> void:
	if is_instance_valid(map_control) and map_control.get_node("AtlasLegend").text!=_atlas_key_text():
		_layout_atlas()
	if help_labels.size()!=2: return
	var mode: String=String(player.traversal_report().get("mode","grounded")) if player and player.has_method("traversal_report") else "grounded"
	if mode=="flight": help_labels[0].text="%s rise · %s descend" % [Bindings.label("jump"),Bindings.label("descend")]
	elif mode=="grapple": help_labels[0].text="%s release tether" % Bindings.label("grapple")
	else: help_labels[0].text="%s reload  ·  %s abilities" % [Bindings.label("reload"),Bindings.label("open_invocations")]
	help_labels[1].text="%s controls  ·  %s pause" % [Bindings.label("help_controls"),Bindings.label("pause_game")]

func _open_controls() -> void:
	controls_return_to_pause=paused
	controls_return_focus = _remember_pause_focus()
	set_paused(true)
	pause_panel.hide()
	controls_overlay.open()

func _close_controls() -> void:
	_refresh_control_labels()
	set_paused(controls_return_to_pause)
	if controls_return_to_pause: _restore_pause_focus(controls_return_focus)
	controls_return_focus = null

func _set_volume(value: float,save: bool=true) -> void:
	if audio: audio.set_volume(value)
	if siege_effects: siege_effects.set_volume(value)
	if rama_runtime: rama_runtime.set_volume(value)
	if invocation_audio: invocation_audio.set_volume(value)
	if volume_label: volume_label.text="Sound · muted" if value<=0 else "Sound · %d%%" % roundi(value*100)
	if save:
		var result: Dictionary=Bindings.merge_settings({"audio":{"volume":value}})
		if not result.ok and volume_label: volume_label.text="Sound · active now; save unavailable"

func _panel_style() -> StyleBoxFlat:
	return HeroUI.panel_style(true, 18)

func _card(parent: Control, position_: Vector2, size_: Vector2) -> PanelContainer:
	var panel:=PanelContainer.new()
	panel.position=position_
	panel.custom_minimum_size=size_
	panel.mouse_filter=Control.MOUSE_FILTER_IGNORE
	panel.add_theme_stylebox_override("panel",HeroUI.hud_panel_style(&"quiet",HeroUI.SPACE_MD))
	parent.add_child(panel)
	return panel

func _label(text_: String, font_size: int, color: Color) -> Label:
	return HeroUI.label(text_, font_size, color)

func _button(parent: Control, text_: String, callback: Callable) -> Button:
	var button:=Button.new()
	button.text=text_
	button.custom_minimum_size=Vector2(0,40)
	button.add_theme_font_size_override("font_size",14)
	HeroUI.button(button)
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

func _layout_world_hud() -> void:
	if not is_inside_tree() or not is_instance_valid(hud) or not is_instance_valid(rama_hud): return
	if overview:
		_layout_overview_composition()
		return
	rama_hud.show()
	_restore_overview_map_parent()
	var screen := get_viewport().get_visible_rect().size
	var compact := screen.x < 1100
	_constrained_world=screen.x<900 or screen.y<500
	var margin := float(HeroUI.SPACE_LG)
	var column_width := 320 if compact else 370
	# At the smallest logical canvas, prioritize location, cores and the live
	# objective. Phase and population remain available in the expanded layout.
	status_label.visible = not compact
	_refresh_lane_visibility()
	var title: Control = hud.get_node("TitleCard")
	var relay: Control = hud.get_node("RelayStatus")
	var controls: Control = hud.get_node("ControlsCard")
	var traversal: Control = hud.get_node("TraversalStatus")
	for control in [title,relay,controls,traversal]: control.visible=not _constrained_world
	for control in [title, relay, controls, traversal, map_control]:
		control.set_anchors_preset(Control.PRESET_TOP_LEFT)
	title.custom_minimum_size = Vector2(column_width,144 if compact else 154)
	title.size = title.custom_minimum_size
	title.position = Vector2(margin,margin)
	relay.custom_minimum_size = Vector2(column_width,82)
	relay.size = relay.custom_minimum_size
	relay.position = Vector2(margin,title.position.y+title.size.y+HeroUI.SPACE_MD)
	controls.custom_minimum_size = Vector2(238,72)
	controls.size = controls.custom_minimum_size
	var combat_top := screen.y+ rama_hud.offset_top
	controls.position = Vector2(margin,combat_top-HeroUI.SPACE_MD-controls.size.y)
	traversal.custom_minimum_size = Vector2(232,88 if _traversal_idle else 116)
	traversal.size = traversal.custom_minimum_size
	traversal.position = Vector2(screen.x-margin-traversal.size.x,combat_top-HeroUI.SPACE_MD-traversal.size.y)
	_layout_atlas()

func _refresh_lane_visibility(battle: Dictionary={}) -> void:
	# Native resize callbacks and periodic HUD refresh share this rule; a
	# compact title must not grow again when the next army report arrives.
	if battle.is_empty() and army: battle=army.report()
	lane_label.visible=get_viewport().get_visible_rect().size.x>=1100 and not bool(battle.get("siege_drill",false)) and String(battle.get("winner","")).is_empty()

func _atlas_key_text() -> String:
	var key:=Bindings.label("world_overview")
	return "%s Map & key" % key if _constrained_world else "● You · □ Relay\n%s Map & key" % key

func _build_atlas_guide() -> void:
	# Overview is a suspended, keyboard-discoverable view. Keep the complete
	# key here instead of spending the live plot on a repeated four-line key.
	atlas_guide=PanelContainer.new()
	atlas_guide.name="AtlasGuide"
	atlas_guide.z_index=1
	atlas_guide.add_theme_stylebox_override("panel",HeroUI.hud_panel_style(&"quiet",HeroUI.SPACE_MD))
	hud.add_child(atlas_guide)
	atlas_guide_scroll=ScrollContainer.new()
	atlas_guide_scroll.name="KeyScroll"
	atlas_guide_scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED
	atlas_guide_scroll.focus_mode=Control.FOCUS_ALL
	atlas_guide_scroll.gui_input.connect(_atlas_guide_input)
	atlas_guide.add_child(atlas_guide_scroll)
	var copy:=VBoxContainer.new()
	_overview_copy=copy
	copy.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	copy.add_theme_constant_override("separation",HeroUI.SPACE_SM)
	atlas_guide_scroll.add_child(copy)
	_overview_heading=_label("TACTICAL KEY",HeroUI.TYPE_SECTION,HeroUI.GOLD)
	copy.add_child(_overview_heading)
	atlas_guide_return=_label("",HeroUI.TYPE_HUD_DETAIL,HeroUI.MIST)
	atlas_guide_return.name="ReturnHint"
	atlas_guide_return.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	copy.add_child(atlas_guide_return)
	var symbols:=_label("▲ Sun troops · ■ Moon troops\n◎ Siege: cannon cart or chariot\n□ Relay · crossed: contested\n◇ Tether anchor\nOutlined tile: raised landing deck\nSolid block: street cover\nLarge ring: faction core\n● You · arrow: your heading",HeroUI.TYPE_HUD_DETAIL,HeroUI.CREAM)
	symbols.name="Symbols"
	symbols.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	copy.add_child(symbols)
	atlas_live_details=_label("",HeroUI.TYPE_HUD_DETAIL,HeroUI.CREAM)
	atlas_live_details.name="WorldDetails"
	atlas_live_details.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	copy.add_child(atlas_live_details)
	atlas_guide.hide()

func _layout_atlas() -> void:
	if not is_inside_tree() or not is_instance_valid(map_control) or not is_instance_valid(rama_hud): return
	if overview:
		_layout_overview_composition()
		return
	_restore_overview_map_parent()
	var screen:=get_viewport().get_visible_rect().size
	var compact:=screen.x<1100
	var margin:=float(HeroUI.SPACE_MD if _constrained_world else HeroUI.SPACE_LG)
	var traversal: Control=hud.get_node("TraversalStatus")
	var legend: Label=map_control.get_node("AtlasLegend")
	legend.text=_atlas_key_text()
	# Grow the card horizontally for a long active key label or larger text;
	# never shorten/remap the displayed action merely to fit a fixed width.
	var key_width:=0.0
	for line in legend.text.split("\n"):
		key_width=maxf(key_width,legend.get_theme_font("font").get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,legend.get_theme_font_size("font_size")).x)
	var width:=152.0 if _constrained_world else maxf(152 if compact else 166,key_width+24)
	width=minf(width,maxf(1,screen.x-margin*2))
	var available:=screen.y+rama_hud.offset_top-margin*2 if _constrained_world else traversal.position.y-margin-HeroUI.SPACE_MD
	var map_height:=maxf(1,minf(300 if compact else 316,available))
	map_control.size=Vector2(width,map_height)
	map_control.position=Vector2(screen.x-margin-width,margin)
	legend.visible=true
	map_control.footer_height=legend.get_combined_minimum_size().y+HeroUI.SPACE_MD
	legend.offset_top=-map_control.footer_height
	legend.offset_bottom=-HeroUI.SPACE_SM
	map_control.queue_redraw()
	if not is_instance_valid(atlas_guide): return
	atlas_guide_return.text="%s Return · %s pause · %s keys\nArrow keys / PgUp / PgDn scroll · Home / End\n%s restarts lane practice" % [Bindings.label("world_overview"),Bindings.label("pause_game"),Bindings.label("help_controls"),Bindings.label("world_respawn")]
	var title: Control=hud.get_node("TitleCard")
	var left:=title.position.x+title.size.x+margin
	var gap:=map_control.position.x-margin-left
	var guide_width:=minf(360,gap) if gap>=260 else minf(360,screen.x-margin*2)
	atlas_guide.size=Vector2(guide_width,minf(344,maxf(1,screen.y-margin*2)))
	atlas_guide.position=Vector2(left if gap>=260 else (screen.x-guide_width)*.5,margin)
	# First constrained entry must measure populated rows, not the empty labels
	# retained while the expanded title/relay cards were in use.
	_refresh_compact_world()
	if _constrained_world:
		var summary_width:=maxf(1,map_control.position.x-margin*2)
		compact_world_card.position=Vector2(margin,margin)
		# A plain Panel keeps wrapped child minima from inflating the background
		# during a live resize. Measure text at the target width, not its stale
		# container minimum from the previous viewport.
		var summary_height:=float(HeroUI.SPACE_SM*2+2*(compact_world_labels.size()-1))
		for row in compact_world_labels:
			summary_height+=row.get_theme_font("font").get_multiline_string_size(row.text,HORIZONTAL_ALIGNMENT_LEFT,summary_width-HeroUI.SPACE_SM*2,row.get_theme_font_size("font_size")).y
		compact_world_card.size=Vector2(summary_width,summary_height)
		atlas_guide.position=compact_world_card.position
		atlas_guide.size=Vector2(summary_width,map_height)
	compact_world_card.visible=_constrained_world and not overview and not paused
	atlas_guide.visible=overview and not paused

func _atlas_guide_input(event: InputEvent) -> void:
	# ScrollContainer has mouse-wheel support but does not read focused arrow
	# keys here. Handle navigation only in this visible suspended overview.
	if not overview or paused or not atlas_guide.visible or not event is InputEventKey or not event.pressed: return
	if event.is_action_pressed("world_overview") or event.is_action_pressed("pause_game") or event.is_action_pressed("help_controls") or event.is_action_pressed("open_invocations"): return
	if event.ctrl_pressed or event.alt_pressed or event.meta_pressed: return
	var bar:=atlas_guide_scroll.get_v_scroll_bar()
	var maximum:=maxf(0,bar.max_value-bar.page)
	var line:=HeroUI.text_font().get_height(HeroUI.TYPE_HUD_DETAIL)+HeroUI.SPACE_SM
	var offset:=float(atlas_guide_scroll.scroll_vertical)
	match event.keycode:
		KEY_UP: offset-=line
		KEY_DOWN: offset+=line
		KEY_PAGEUP: offset-=maxf(line,bar.page*.8)
		KEY_PAGEDOWN: offset+=maxf(line,bar.page*.8)
		KEY_HOME: offset=0
		KEY_END: offset=maximum
		_: return
	atlas_guide_scroll.scroll_vertical=roundi(clampf(offset,0,maximum))
	atlas_guide_scroll.accept_event()

func _build_compact_world() -> void:
	compact_world_card=Panel.new()
	compact_world_card.name="CompactWorldState"
	compact_world_card.mouse_filter=Control.MOUSE_FILTER_IGNORE
	compact_world_card.clip_contents=true
	compact_world_card.add_theme_stylebox_override("panel",HeroUI.hud_panel_style(&"quiet",HeroUI.SPACE_SM))
	hud.add_child(compact_world_card)
	var rows:=VBoxContainer.new()
	rows.add_theme_constant_override("separation",2)
	compact_world_card.add_child(rows)
	rows.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rows.offset_left=HeroUI.SPACE_SM
	rows.offset_right=-HeroUI.SPACE_SM
	rows.offset_top=HeroUI.SPACE_SM
	rows.offset_bottom=-HeroUI.SPACE_SM
	for index in 4:
		var row:=_label("",HeroUI.TYPE_HUD_DETAIL,HeroUI.GOLD if index==2 else HeroUI.CREAM)
		row.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
		rows.add_child(row)
		compact_world_labels.append(row)
	compact_world_card.hide()

func _refresh_compact_world(battle: Dictionary={}) -> void:
	if compact_world_labels.size()!=4 or not is_instance_valid(goal_label) or not player or not army: return
	if not _constrained_world and not overview: return
	if battle.is_empty(): battle=army.report()
	var report: Dictionary=player.traversal_report()
	var energy:=float(report.get("energy",0))
	var flight_cd:=float(report.get("flight_cooldown",0))
	var tether_cd:=float(report.get("grapple_cooldown",0))
	var mode:=String(report.get("mode","ground"))
	var idle_copy:=_idle_traversal_copy(report,battle,player.active and player.is_on_floor())
	compact_world_labels[0].text="%s · %s" % [district_at(player.position),score_label.text.trim_prefix("Cores · ")]
	var objective:="Escort Sun troops to the Moon core."
	if not String(battle.get("winner","")).is_empty(): objective=WorldOutcome.headline(battle.winner)+" · %s pause · %s restart" % [Bindings.label("pause_game"),Bindings.label("world_respawn")]
	elif battle.get("siege_drill",false): objective="Siege drill: step outside enemy blast rings."
	elif relays:
		var rules=RelaySession.ControlRules
		for site in relays.sites():
			var distance:=Vector2(player.position.x-site.position.x,player.position.z-site.position.z).length()
			if distance>rules.SUPPLY_RADIUS: continue
			if site.contested: objective="Relay contested: clear enemies for supplies."
			elif site.owner!="neutral" and site.pressure_team not in ["neutral",site.owner]: objective="Relay under pressure: clear enemy soldiers."
			elif absf(player.position.y-site.position.y)>rules.HEIGHT_TOLERANCE: objective="Land in the relay zone to capture."
			elif distance>rules.CAPTURE_RADIUS: objective="Enter relay zone · %.0fm to centre" % distance
			elif site.owner=="sun": objective="Sun relay held · supply in %.1fs" % maxf(0,rules.SUPPLY_PERIOD-float(site.supply_clock))
			elif site.owner=="moon": objective="Enemy relay: neutralize, then secure."
			else: objective="Capture relay: stay in the marked zone."
			break
	compact_world_labels[1].text=objective
	compact_world_labels[2].text=idle_copy.energy if not idle_copy.is_empty() else "%s %dm · Energy %d/%d · Flight %.1fs · Tether %.1fs" % [mode.capitalize(),roundi(player.position.y),energy,report.get("max_energy",100),flight_cd,tether_cd]
	var prompt:String=idle_copy.prompt if not idle_copy.is_empty() else "%s tether ≤36m · %s flight" % [Bindings.label("grapple"),Bindings.label("fly")]
	if not report.get("enabled",false): prompt="Traversal unavailable in this scene."
	elif mode in ["flight","flying"]: prompt="%s rise · %s descend · %s land to refill" % [Bindings.label("jump"),Bindings.label("descend"),Bindings.label("fly")]
	elif mode in ["grapple","grappling"]: prompt="%s release tether · %s flight" % [Bindings.label("grapple"),Bindings.label("fly")]
	elif energy<18: prompt="Land to refill traversal energy · tether needs 18."
	elif not report.get("candidate",{}).is_empty():
		prompt="%s tether %.0fm · %s" % [Bindings.label("grapple"),player.global_position.distance_to(report.candidate.position),"ready" if tether_cd<=0 else "cooling"]
	elif flight_cd>0 or tether_cd>0: prompt=String(report.get("status","Traversal cooling"))
	elif String(report.get("status","")).begins_with("Aim at") or String(report.get("status","")).begins_with("No clear"): prompt+=" · no clear ring"
	compact_world_labels[3].text=prompt
	if is_instance_valid(atlas_live_details):
		var detail_rows:PackedStringArray=["WORLD DETAILS",location_label.text,score_label.text,lane_label.text,objective_label.text,relay_hint.text,ability_label.text,"Energy %d / %d" % [energy,report.get("max_energy",100)],goal_label.text]
		for relay in relay_labels: detail_rows.append(relay.text.replace("\n",": "))
		for help in help_labels: detail_rows.append(help.text)
		if overview: detail_rows.insert(1,"Rama health "+rama_hud.life_text.text)
		if overview: detail_rows.append("Reading: ↑ / ↓ · PgUp / PgDn · Home / End")
		atlas_live_details.text="\n".join(detail_rows)

func _layout_pause_panel() -> void:
	if not pause_panel: return
	var before := pause_panel.get_global_rect()
	var screen:=get_viewport().get_visible_rect().size
	var size_:=Vector2(minf(480,screen.x-32),minf(600,screen.y-32))
	pause_panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
	pause_panel.size=size_
	pause_panel.position=(screen-pause_panel.size)/2
	if not before.is_equal_approx(pause_panel.get_global_rect()):
		call_deferred("_reveal_pause_focus")

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.echo: return
	if controls_overlay and controls_overlay.visible: return
	if invocation_panel and invocation_panel.visible: return
	if rama_panel and rama_panel.visible: return
	if event.is_action_pressed("open_invocations"):
		_open_rama_panel()
		get_viewport().set_input_as_handled()
		return
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
			if relays and relays.art: relays.art.set_night_blend(phase)
			phase_clock=0
	ui_clock+=delta
	if ui_clock>.12:
		ui_clock=0
		location_label.text=district_at(player.position)
		var drill: bool=army.report().get("siege_drill",false) if army else false
		status_label.text="OFFLINE %s · %s" % ["SIEGE DRILL" if drill else "PRACTICE","Moonlight" if phase>.5 else "Golden hour"]
		_update_practice_hud()
		_update_invocation_hud()
		map_control.hero_position=player.position
		# The authored hero faces +Z; the CharacterBody root only translates.
		map_control.hero_forward=player.visual.global_basis.z
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
	_step_relays(_delta)

func _step_relays(delta: float) -> void:
	if not world_ready or paused or get_tree().paused or overview or not army or not relays: return
	if army.siege_drill or not army.winner.is_empty(): return
	relays.advance(delta)

func _update_relay_hud() -> void:
	if not relays or relay_labels.size()!=3: return
	map_control.relays=[] if army.siege_drill else relays.sites()
	var nearest:=99.0
	var close_site: Dictionary={}
	var rules = RelaySession.ControlRules
	for site in relays.sites():
		var label:=relay_labels[site.id]
		var short_name: String=String(site.label).trim_suffix(" Relay")
		var secured: bool = absf(site.progress) >= rules.CAPTURE_REQUIRED-rules.EPSILON
		var state:="Contested" if site.contested else (String(site.owner).capitalize() if secured else "%d%%" % roundi(absf(site.progress)/rules.CAPTURE_REQUIRED*100))
		if not site.contested and absf(site.progress)>.001 and not secured:
			state="%s %d%%" % ["▲" if site.capture_team=="sun" else "■",roundi(absf(site.progress)/rules.CAPTURE_REQUIRED*100)]
		if not site.contested and site.owner=="neutral" and absf(site.progress)<.001: state="Open"
		label.text="%s\n%s" % [short_name,state]
		label.modulate=Color.WHITE
		label.add_theme_color_override("font_color",HeroUI.GOLD if site.owner=="sun" else (HeroUI.MIST if site.owner=="moon" else HeroUI.CREAM))
		var distance: float=Vector2(player.position.x-site.position.x,player.position.z-site.position.z).length()
		if distance<nearest: nearest=distance;close_site=site
	if army.siege_drill:
		relay_hint.text="Relays inactive during siege drill · %s restarts lane practice" % Bindings.label("world_respawn")
		for label in relay_labels: label.text="—"
	elif not army.winner.is_empty(): relay_hint.text="Round ended · Relay capture and supplies stopped"
	elif nearest<=rules.SUPPLY_RADIUS and not close_site.is_empty():
		if close_site.contested: relay_hint.text="Contested · Clear enemies to capture and receive supplies"
		elif close_site.owner!="neutral" and close_site.pressure_team not in ["neutral",close_site.owner]: relay_hint.text="Under pressure · Clear enemy soldiers to keep this relay and restore supply"
		elif absf(player.position.y-close_site.position.y)>rules.HEIGHT_TOLERANCE: relay_hint.text="Land within the marked zone to contribute to capture"
		elif nearest>rules.CAPTURE_RADIUS: relay_hint.text="Enter the marked zone · %.0fm to relay centre" % nearest
		elif close_site.owner=="sun": relay_hint.text="Held · next supply in %.1fs\n+3 arrows / +6 troop health · Enemy pressure stops supply" % maxf(0,rules.SUPPLY_PERIOD-float(close_site.supply_clock))
		elif close_site.owner=="moon": relay_hint.text="Neutralize enemy control, then secure this relay · Soldiers help"
		else: relay_hint.text="Capture: stay in the zone · %ds solo, %ds with support" % [rules.CAPTURE_REQUIRED,rules.CAPTURE_REQUIRED/rules.MAX_CONTRIBUTORS]
	else: relay_hint.text="Hold lane relays for supplies · ▲ Sun · ■ Moon · X Contested"

func _update_practice_hud() -> void:
	_refresh_control_labels()
	_update_relay_hud()
	var siege_drill:=false
	var enemy_siege:=0
	var battle: Dictionary={}
	if army:
		battle=army.report()
		outcome_summary.present(battle)
		var cores: Dictionary=battle.get("cores",{})
		siege_drill=battle.get("siege_drill",false)
		_refresh_lane_visibility(battle)
		if army.has_method("minimap_units"): map_control.units=army.minimap_units()
		for unit in map_control.units:
			if unit.get("team","")=="moon" and unit.get("role","") in ["cannon_cart","royal_chariot"]: enemy_siege+=1
		if siege_drill:
			score_label.text="Siege %d enemies · Gold %d" % [enemy_siege,battle.get("gold",0)]
			objective_label.text="Break enemy engines before their shots land.\nStep outside the blast warning rings."
		else:
			score_label.text="Cores · Sun %d / Moon %d · Gold %d" % [cores.get("sun",0),cores.get("moon",0),battle.get("gold",0)]
			var nearest_lane: Dictionary = {}
			var lane_distance := INF
			var here := Vector2(player.position.x,player.position.z)
			for lane in manifest.lanes:
				for index in range(lane.points.size()-1):
					var a: Array = lane.points[index]
					var b: Array = lane.points[index+1]
					var closest := Geometry2D.get_closest_point_to_segment(here,Vector2(a[0],a[2]),Vector2(b[0],b[2]))
					var distance := here.distance_squared_to(closest)
					if distance < lane_distance:
						lane_distance = distance
						nearest_lane = lane
			var troops: Array = battle.get("alive_by_lane",[])
			var lane_id: int = nearest_lane.get("id",-1)
			var lane_status := "%s · %d troops" % [nearest_lane.name,troops[lane_id]] if lane_id>=0 and lane_id<troops.size() else "Three lanes"
			lane_label.text="%s · Wave %d" % [lane_status,battle.get("waves",0)]
			objective_label.text="Escort Sun troops to the Moon core."
		if practice_mode_label: practice_mode_label.text="OFFLINE SIEGE DRILL" if siege_drill else "OFFLINE LANE PRACTICE"
		if siege_practice_button: siege_practice_button.text="Siege practice · restart drill" if siege_drill else "Siege practice · enter drill"
		if practice_hint_label:
			practice_hint_label.text=practice_error if not practice_error.is_empty() else ("Break enemy engines before impact to protect Sun troops. Enemy siege blasts damage Rama; step out of the warning ring. Restart lane practice exits this drill." if siege_drill else "Try cannon carts and royal chariots in the central court. Blasts damage troops; enemy siege blasts damage Rama.")
		if not String(battle.get("winner","")).is_empty():
			objective_label.text=WorldOutcome.headline(battle.winner)+"\nRestart lane practice from the pause menu."
			_set_traversal_idle(false)
			goal_label.text="Round ended · %s pause · %s restart" % [Bindings.label("pause_game"),Bindings.label("world_respawn")]
			_refresh_compact_world(battle)
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
	var idle_copy:=_idle_traversal_copy(report,battle,player.active and player.is_on_floor())
	if not idle_copy.is_empty():
		ability_label.text=idle_copy.energy
		goal_label.text=idle_copy.prompt
	elif mode=="grapple" or mode=="grappling":
		traversal_seen=true
		goal_label.text="%s release tether · %s flight" % [Bindings.label("grapple"),Bindings.label("fly")]
	elif mode=="flight" or mode=="flying":
		traversal_seen=true
		goal_label.text="%s rise · %s descend · %s land\nEnergy refills on the ground" % [Bindings.label("jump"),Bindings.label("descend"),Bindings.label("fly")]
	elif siege_drill:
		goal_label.text="Break enemy engines to cancel shots.\nEnemy blast marks also hurt Rama." if enemy_siege>0 else "Enemy engines cleared.\n%s opens pause for drill or lane restart." % Bindings.label("pause_game")
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

	_set_traversal_idle(not idle_copy.is_empty())
	_refresh_compact_world(battle)

func _idle_traversal_copy(report:Dictionary,battle:Dictionary,grounded:bool)->Dictionary:
	# Presentation only: consume authority values without changing traversal state.
	if not grounded or not report.get("enabled",false) or String(report.get("mode","")) not in ["ground","grounded"]: return {}
	var maximum:=float(report.get("max_energy",100))
	if maximum<=0 or float(report.get("energy",0))<maximum or float(report.get("flight_cooldown",0))>0 or float(report.get("grapple_cooldown",0))>0: return {}
	if String(report.get("status","")).begins_with("Aim at") or String(report.get("status","")).begins_with("No clear"): return {}
	if not report.get("candidate",{}).is_empty() or battle.get("siege_drill",false) or not String(battle.get("winner","")).is_empty(): return {}
	return {"energy":"Energy %d / %d" % [report.energy,maximum],"prompt":"%s flight · %s tether ≤%dm" % [Bindings.label("fly"),Bindings.label("grapple"),report.get("max_range",36)]}

func _set_traversal_idle(value:bool)->void:
	if _traversal_idle==value: return
	_traversal_idle=value
	goal_label.custom_minimum_size.y=0 if value else 42
	energy_bar.show_percentage=not value
	_layout_world_hud()

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
	if relays and relays.art: relays.art.set_night_blend(phase)

func set_review_phase(value: float) -> void:
	set_phase(value)

func set_night(value: bool) -> void:
	night=value
	target_phase=1.0 if value else 0.0

func release_actions(cancel_movement := true) -> void:
	Bindings.release_gameplay()
	if player:
		if player.has_method("cancel_traversal"): player.cancel_traversal("world transition")
		player.velocity=Vector3.ZERO
		if cancel_movement:
			player.dash_time=0
			player.dash_direction=Vector3.ZERO

func set_paused(value: bool) -> void:
	paused=value
	if is_instance_valid(atlas_guide): atlas_guide.visible=overview and not value
	if is_instance_valid(compact_world_card): compact_world_card.visible=_constrained_world and not overview and not value
	release_actions(false)
	get_tree().paused=value
	if pause_panel: pause_panel.visible=value and not (rama_panel and rama_panel.visible)
	if player: player.active=not value and not overview and (not player.vitals or player.vitals.alive)
	if rama_runtime: rama_runtime.set_suspended(value or overview)
	if audio: audio.set_suspended(value or overview)
	if siege_effects: siege_effects.set_suspended(value or overview)
	if invocations: invocations.set_suspended(value or overview)
	if ultimate_fx: ultimate_fx.set_suspended(value or overview)
	if invocation_audio: invocation_audio.set_suspended(value or overview)
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE if value or overview else Input.MOUSE_MODE_CAPTURED
	if not value:
		if overview and is_instance_valid(atlas_guide_scroll): atlas_guide_scroll.grab_focus()
		else: get_viewport().gui_release_focus()
	if value and pause_panel:
		_layout_pause_panel()
		_update_practice_hud()
		if not (controls_overlay and controls_overlay.visible) and not (invocation_panel and invocation_panel.visible) and not (rama_panel and rama_panel.visible):
			_refresh_pause_actions()
			_restore_pause_focus(null)
			call_deferred("_reveal_pause_focus")

func _refresh_pause_actions() -> void:
	# The army remains the sole outcome authority. Returning to the world after
	# a finished round is exploration; only the existing restart starts a round.
	var ended: bool = army != null and not army.winner.is_empty()
	continue_practice_button.text = "Return to world" if ended else "Continue practice"
	HeroUI.button(continue_practice_button, not ended)
	HeroUI.button(restart_practice_button, ended)

func _remember_pause_focus() -> WeakRef:
	var opener := get_viewport().gui_get_focus_owner()
	return weakref(opener) if paused and is_instance_valid(opener) and pause_panel.is_ancestor_of(opener) else null

func _restore_pause_focus(previous_ref: WeakRef) -> void:
	var previous: Control = previous_ref.get_ref() if previous_ref else null
	if is_instance_valid(previous) and pause_panel.is_ancestor_of(previous) and previous.is_visible_in_tree() and previous.focus_mode == Control.FOCUS_ALL:
		if (not previous is BaseButton or not previous.disabled) and (not previous is Slider or previous.editable):
			previous.grab_focus()
			call_deferred("_reveal_pause_focus")
			return
	var preferred: Button = restart_practice_button if army != null and not army.winner.is_empty() else continue_practice_button
	if is_instance_valid(preferred) and preferred.is_visible_in_tree() and not preferred.disabled:
		preferred.grab_focus()
		return
	for action in pause_actions:
		if not is_instance_valid(action) or not action.is_visible_in_tree() or action.focus_mode != Control.FOCUS_ALL: continue
		if action is BaseButton and action.disabled: continue
		if action is Slider and not action.editable: continue
		action.grab_focus()
		return

func _reveal_pause_focus() -> void:
	# Focus can predate the visible container's final sort, or already belong to
	# an offscreen button. Reveal after layout without stealing a newer focus.
	if not is_inside_tree() or is_queued_for_deletion(): return
	await get_tree().process_frame
	if not is_inside_tree() or is_queued_for_deletion(): return
	if not paused or not pause_panel.visible: return
	if controls_overlay and controls_overlay.visible: return
	if invocation_panel and invocation_panel.visible: return
	if rama_panel and rama_panel.visible: return
	var focus:=get_viewport().gui_get_focus_owner()
	if focus in pause_actions:
		# Fresh entry must keep the title/outcome above the primary action.
		# A late focus scroll can otherwise clip the heading even at scroll 0.
		if focus in [continue_practice_button,restart_practice_button] and focus.position.y + focus.size.y <= pause_scroll.size.y:
			pause_scroll.scroll_vertical = 0
		else:
			pause_scroll.ensure_control_visible(focus)

func _focus_lost() -> void:
	if is_instance_valid(_return_transition) and _return_transition.visible: return
	if not world_ready: return
	if controls_overlay and controls_overlay.visible:
		controls_overlay.cancel_capture()
		controls_return_to_pause=true
	set_paused(true)
	if controls_overlay and controls_overlay.visible: pause_panel.hide()
	if invocation_panel and invocation_panel.visible:
		invocation_return_to_pause = true
		pause_panel.hide()
	if rama_panel and rama_panel.visible:
		rama_return_to_pause = true
		pause_panel.hide()

func teleport_to(position_: Vector3, yaw_degrees: float=180.0) -> void:
	if not position_.is_finite() or not is_finite(yaw_degrees): return
	if invocations: invocations.cancel_active("Travel cancelled the invocation.")
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
	_layout_atlas()
	if value and not paused and is_instance_valid(atlas_guide_scroll): atlas_guide_scroll.grab_focus()
	player.presentation_suspended=value
	release_actions()
	if army: army.process_mode=Node.PROCESS_MODE_DISABLED if value else Node.PROCESS_MODE_PAUSABLE
	if relays: relays.process_mode=Node.PROCESS_MODE_DISABLED if value else Node.PROCESS_MODE_PAUSABLE
	if relays and relays.art: relays.art.process_mode=Node.PROCESS_MODE_DISABLED if value else Node.PROCESS_MODE_PAUSABLE
	if audio: audio.set_suspended(value or paused)
	if siege_effects: siege_effects.set_suspended(value or paused)
	if invocations: invocations.set_suspended(value or paused)
	if ultimate_fx: ultimate_fx.set_suspended(value or paused)
	if invocation_audio: invocation_audio.set_suspended(value or paused)
	player.active=not value and not paused and (not player.vitals or player.vitals.alive)
	if rama_runtime: rama_runtime.set_suspended(value or paused)
	if value:
		review_camera.position=Vector3(118,155,195)
		review_camera.look_at(Vector3(0,0,0))
		review_camera.current=true
	else: player.camera.current=true
	_layout_world_hud()
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
	return {"ready":world_ready,"manifest_path":manifest_path,"manifest_sha256":FileAccess.get_sha256(manifest_path),"manifest_revision":manifest.get("revision",0),"authority_boxes":authority_bodies.size(),"native_platforms":native_platform_bodies.size(),"native_bounds":manifest.bounds.get("actor_xz",[]),"landmarks":landmark_report,"army":army.report() if army else {},"traversal":player.traversal_report() if player and player.has_method("traversal_report") else {},"audio":audio.get_diagnostics() if audio else {},"siege_effects":siege_effects.report() if siege_effects else {},"relays":relays.report() if relays else {},"invocations":invocations.report() if invocations else {},"ultimate_effects":ultimate_fx.report() if ultimate_fx else {},"invocation_ui":invocation_panel.report() if invocation_panel else {},"invocation_audio":invocation_audio.report() if invocation_audio else {},"siege_ui":{"pause_rect":str(pause_panel.get_global_rect()) if pause_panel else "","focus_targets":pause_actions.size(),"practice_label":practice_mode_label.text if practice_mode_label else ""},"floor_bodies":1,"props":manifest.get("props",[]).size(),"imported_props":imported_prop_count,"procedural_props":fallback_prop_count,"builtin_procedural_props":builtin_prop_count,"missing_presets":missing_presets,"kit_sha256":kit_hashes,"kit_hash_scope":"Raw source hashes when available; empty for remapped exported scene resources.","rama_hero":rama_runtime.report() if rama_runtime else {},"hero_model_ready":player.model_ready if player else false,"hero_radius":manifest.get("bounds",{}).get("hero_radius",0),"lanes":manifest.get("lanes",[]).size(),"camps":manifest.get("camps",[]).size(),"objectives":manifest.get("objectives",[]).size(),"lighting":lighting.diagnostics() if lighting else {},"scope":"Offline 140×260m native lane practice with raised decks, limited flight and tether relics. Eight central boxes retain browser dimensions; expanded bounds/platforms/local army do not share browser authority. No online-match or commercial visual-parity claim."}

func get_build_report() -> Dictionary:
	return build_report()

func return_to_courtyard() -> void:
	var loader: Control = load("res://scripts/scene_transition.gd").ensure_for_tree(get_tree())
	if loader.is_busy() or loader.phase == &"error": return
	var opener := get_viewport().gui_get_focus_owner()
	if not loader.cancelled.is_connected(_on_return_cancelled):
		loader.cancelled.connect(_on_return_cancelled)
	if not loader.begin(&"courtyard", self, opener): return
	_return_transition = loader
	_return_process_modes.clear()
	_isolate_return_children(self)
	release_actions()

var _return_transition: Control
var _return_process_modes: Array[Dictionary] = []

func _isolate_return_children(parent: Node) -> void:
	for child in parent.get_children():
		if child.process_mode not in [Node.PROCESS_MODE_INHERIT, Node.PROCESS_MODE_DISABLED]:
			_return_process_modes.append({"node":weakref(child), "mode":child.process_mode})
			child.process_mode = Node.PROCESS_MODE_DISABLED
		_isolate_return_children(child)

func _on_return_cancelled(_destination: StringName) -> void:
	for state in _return_process_modes:
		var node: Node = state.node.get_ref()
		if is_instance_valid(node): node.process_mode = state.mode
	_return_process_modes.clear()
	_return_transition = null

func _exit_tree() -> void:
	if get_tree(): get_tree().paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE

func cast_rama_ability(id: String) -> Dictionary:
	return rama_runtime.cast_ability(id) if rama_runtime else {"accepted":false,"reason":"Hero unavailable"}

func _open_rama_panel() -> void:
	if not world_ready or not rama_panel or rama_panel.visible: return
	rama_return_to_pause = paused
	rama_return_focus = _remember_pause_focus()
	set_paused(true)
	pause_panel.hide()
	rama_panel.open("confluence")

func _close_rama_panel() -> void:
	set_paused(rama_return_to_pause)
	if rama_return_to_pause: _restore_pause_focus(rama_return_focus)
	rama_return_focus = null

func _settle_world_hud() -> void:
	# Word wrapping is shaped after the first container sort. Reapply preferred
	# sizes after that minimum shrinks; this also covers the startup resolution.
	for pass_index in 2:
		if not is_inside_tree(): return
		var tree := get_tree()
		await tree.process_frame
		if not is_inside_tree() or get_tree() != tree or not is_instance_valid(hud): return
		_layout_world_hud()

func _restore_overview_map_parent() -> void:
	if not is_instance_valid(map_control) or not is_instance_valid(hud): return
	if map_control.get_parent()!=hud: map_control.reparent(hud,false)
	map_control.custom_minimum_size=Vector2.ZERO
	map_control.size_flags_horizontal=Control.SIZE_FILL
	if is_instance_valid(_overview_heading): _overview_heading.text="TACTICAL KEY"

func _layout_overview_composition() -> void:
	if _overview_layout_busy or not is_instance_valid(atlas_guide) or not is_instance_valid(_overview_copy): return
	_overview_layout_busy=true
	var screen:=get_viewport().get_visible_rect().size
	var margin:=12.0
	var column:=minf(300,maxf(208,screen.x*.26))
	column=minf(column,maxf(1,screen.x-margin*2))
	for name in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus"]: hud.get_node(name).hide()
	rama_hud.hide()
	compact_world_card.hide()
	atlas_guide.visible=not paused
	_overview_heading.text="OVERVIEW"
	atlas_guide_return.text="Health %s\n%s back · %s pause\n%s keys · ↑↓ read" % [rama_hud.life_text.text,Bindings.label("world_overview"),Bindings.label("pause_game"),Bindings.label("help_controls")]
	_refresh_compact_world()
	if map_control.get_parent()!=_overview_copy:
		map_control.reparent(_overview_copy,false)
		_overview_copy.move_child(map_control,2)
	map_control.get_node("AtlasLegend").text=_atlas_key_text()
	map_control.get_node("AtlasLegend").hide()
	map_control.footer_height=0
	var inner_width:=maxf(1,column-HeroUI.SPACE_MD*2-16)
	var heading_height:=float(_overview_heading.get_theme_font("font").get_height(_overview_heading.get_theme_font_size("font_size")))
	var hint_height:=atlas_guide_return.get_theme_font("font").get_multiline_string_size(atlas_guide_return.text,HORIZONTAL_ALIGNMENT_LEFT,inner_width,atlas_guide_return.get_theme_font_size("font_size")).y
	var available_height:=maxf(80,screen.y-margin*2-HeroUI.SPACE_MD*2-heading_height-hint_height-HeroUI.SPACE_SM*3-32)
	var plot_width:=maxf(1,minf(196,inner_width-24))
	var plot_height:=minf(plot_width*260.0/140.0,available_height)
	plot_width=plot_height*140.0/260.0
	map_control.custom_minimum_size=Vector2(plot_width+24,plot_height+32)
	map_control.size_flags_horizontal=Control.SIZE_SHRINK_CENTER
	map_control.queue_redraw()
	# Shrink child minima before assigning the parent rectangle on live resize.
	atlas_guide.reset_size()
	atlas_guide.size=Vector2(column,screen.y-margin*2)
	atlas_guide.position=Vector2(screen.x-margin-atlas_guide.size.x,margin)
	_overview_content_rect=Rect2(Vector2(margin,margin),Vector2(maxf(1,atlas_guide.position.x-margin*2),maxf(1,screen.y-margin*2)))
	if review_camera.current: _fit_overview_camera(_overview_content_rect.grow(-12))
	_overview_layout_busy=false

func _overview_points() -> PackedVector3Array:
	if not _overview_geometry_points.is_empty(): return _overview_geometry_points
	# Exact visual prop extents plus existing nominal floor, solid decks and anchors.
	# No new map reconstruction or cached simulation state is created.
	var bounds:Array=manifest.bounds.nominal_xz
	for x in [bounds[0],bounds[1]]:
		for z in [bounds[2],bounds[3]]: _overview_geometry_points.append(Vector3(x,0,z))
	for entry in manifest.authority_collision_boxes+manifest.traversal.native_collision_boxes:
		var base:=_v(entry.position)
		var dimensions:=_v(entry.size)
		var box:=AABB(base-Vector3(dimensions.x*.5,0,dimensions.z*.5),dimensions)
		for index in 8: _overview_geometry_points.append(box.get_endpoint(index))
	for entry in manifest.traversal.anchors: _overview_geometry_points.append(_v(entry.position))
	for node in props_root.find_children("*","MeshInstance3D",true,false):
		var mesh:=node as MeshInstance3D
		if mesh.mesh==null or not mesh.is_visible_in_tree(): continue
		var box:=mesh.get_aabb()
		for index in 8: _overview_geometry_points.append(mesh.global_transform*box.get_endpoint(index))
	return _overview_geometry_points

func _overview_projection_bounds() -> Rect2:
	return _overview_projection_state().rect

func _overview_projection_state() -> Dictionary:
	var result:=Rect2()
	var first:=true
	var edge_depths:=Vector4.ONE
	var inverse:=review_camera.get_camera_transform().affine_inverse()
	for point in _overview_points():
		var projected:=review_camera.unproject_position(point)
		var depth:=maxf(.1,-(inverse*point).z)
		if first:
			result=Rect2(projected,Vector2.ZERO);first=false
			edge_depths=Vector4(depth,depth,depth,depth)
		else:
			if projected.x<result.position.x:edge_depths.x=depth
			if projected.x>result.end.x:edge_depths.y=depth
			if projected.y<result.position.y:edge_depths.z=depth
			if projected.y>result.end.y:edge_depths.w=depth
			result=result.expand(projected)
	return {"rect":result,"x_depth":2.0/(1.0/edge_depths.x+1.0/edge_depths.y),"y_depth":2.0/(1.0/edge_depths.z+1.0/edge_depths.w)}

func _fit_overview_camera(free_rect:Rect2) -> void:
	var points:=_overview_points()
	if points.is_empty() or free_rect.size.x<32 or free_rect.size.y<32: return
	var bounds:=AABB(points[0],Vector3.ZERO)
	for point in points: bounds=bounds.expand(point)
	var centre:=bounds.get_center()
	var orientation:=review_camera.global_basis.orthonormalized()
	var distance:=Vector3(118,155,195).length()
	var shift:=Vector2.ZERO
	var screen:=get_viewport().get_visible_rect().size
	# A bounded project-and-fit solve keeps the existing oblique orientation.
	# Camera translates only; no world/hero pose or control changes occur.
	for unused in 20:
		review_camera.global_transform=Transform3D(orientation,centre+orientation.z*distance+orientation.x*shift.x+orientation.y*shift.y)
		var projection:=_overview_projection_state()
		var projected:Rect2=projection.rect
		var ratio:=maxf(projected.size.x/free_rect.size.x,projected.size.y/free_rect.size.y)
		var error:=projected.get_center()-free_rect.get_center()
		# Pan sensitivity is set by the actual depth of each projected edge,
		# not the city's centre depth (which oversteers a nearby skyline).
		var middle:=review_camera.project_position(screen*.5,1.0)
		var x_pixel:float=middle.distance_to(review_camera.project_position(screen*.5+Vector2.RIGHT,1.0))
		var y_pixel:float=middle.distance_to(review_camera.project_position(screen*.5+Vector2.DOWN,1.0))
		shift+=Vector2(error.x*x_pixel*projection.x_depth,-error.y*y_pixel*projection.y_depth)*.7
		distance=clampf(distance*sqrt(clampf(ratio*1.025,.5,2.0)),100,400)
	review_camera.global_transform=Transform3D(orientation,centre+orientation.z*distance+orientation.x*shift.x+orientation.y*shift.y)
	review_camera.set_meta("overview_free_rect",free_rect)
	review_camera.set_meta("overview_projected_geometry",_overview_projection_bounds())
