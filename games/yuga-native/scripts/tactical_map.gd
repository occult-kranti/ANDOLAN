extends Node3D
## Original tactical encounter layout; immutable Sangam art is reused locally.
const DATA_PATH := "res://assets/tactical/map.json"
const FINISH = preload("res://shaders/tactical_architecture.gdshader")
const DETAIL_KIT = preload("res://scripts/tactical_architecture_details.gd")
var sites: Dictionary = {"A":Vector3(-29,0,8), "B":Vector3(29,0,8)}
var site_radius := 5.0
var bounds := Rect2(-50,-65,100,130)
var _data: Dictionary = {}
var _barriers: Array[StaticBody3D] = []
var _barrier_visuals: Array[MeshInstance3D] = []
var _materials: Dictionary = {}
var _metrics := {"ready":false,"buildings":0,"reused_meshes":0,"triangles":0,"collision_bodies":0,"buy_barriers":true,"errors":[]}
var _stone: Material
var _indigo: Material
var _brass: Material

func _ready() -> void:
	_data = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if _data.is_empty() or _data.get("schema_version") != 1:
		_fail("map_contract"); return
	for site in ["A","B"]: sites[site] = _v(_data.sites[site])
	site_radius = float(_data.site_radius)
	bounds = Rect2(_data.bounds_xz[0],_data.bounds_xz[1],_data.bounds_xz[2],_data.bounds_xz[3])
	for path in _data.reused_sources:
		var resource_path: String = "res://" + path
		if FileAccess.file_exists(resource_path) and FileAccess.get_sha256(resource_path) != _data.reused_sources[path]:
			_fail("changed_reused_source:" + path); return
	var packed = load("res://assets/world/sangam-district.glb")
	if not packed is PackedScene:
		_fail("sangam_asset_unavailable"); return
	var library: Node3D = packed.instantiate()
	var specification: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/sangam-district.json"))
	_stone = _architecture_material(Color(.69,.59,.46),0)
	_indigo = _architecture_material(Color(.17,.25,.32),2)
	_brass = _plain(Color(.69,.49,.20),.55)
	for mesh: MeshInstance3D in library.find_children("*", "MeshInstance3D", true, false):
		for surface in mesh.mesh.get_surface_count():
			var original := mesh.mesh.surface_get_material(surface)
			if original and original.resource_name.to_lower().contains("sandstone"):
				_stone = _finish(original)
	for building in _data.buildings:
		var module: Dictionary = specification.modules[int(building.module)]
		var source_center := _v(module.position)
		var scale_ := _v(building.size) / _v(module.inherited_ground_size)
		for mesh_name in [module.base_mesh, module.overhead_mesh]:
			var source := library.find_child(mesh_name,true,false) as MeshInstance3D
			if source == null: library.free(); _fail("missing_module:" + mesh_name); return
			_copy_mesh(source,_v(building.position),source_center,scale_,true)
		_metrics.buildings += 1
	var source_cover := library.find_child("SOLID_Cover_West_South",true,false) as MeshInstance3D
	for cover in _data.covers:
		if cover.kind == "monument":
			_copy_mesh(source_cover,_v(cover.position),Vector3(-8,0,-60),_v(cover.size)/Vector3(3,2.7,6),true)
		else:
			_crate(String(cover.id),_v(cover.position),_v(cover.size))
	for partition in _data.partitions:
		var base := _v(partition.position)
		var dimensions := _v(partition.size)
		var partition_visual:=_box(partition.id,base+Vector3.UP*dimensions.y*.5,dimensions,_stone,true)
		partition_visual.mesh=DETAIL_KIT.beveled_box(dimensions-Vector3(.08,0,0),.045)
		for offset in [-.61,.61]:
			_box("PartitionFrieze",base+Vector3(offset,2.9,0),Vector3(.03,.45,dimensions.z),_indigo,false)
		_box("PartitionCap",base+Vector3.UP*(dimensions.y+.1),Vector3(dimensions.x+.2,.2,dimensions.z+.2),_stone,false)
	# Background facades sit outside physical bounds; they never masquerade as exits.
	for x in [-61.0,61.0]:
		var source := library.find_child("BASE_Block_2",true,false) as MeshInstance3D
		var module: Dictionary = specification.modules[2]
		for z in [-37.0,0.0,37.0]:
			_copy_mesh(source,Vector3(x,-1,z),_v(module.position),Vector3(.9,1.4,1.5),false)
	# Continuous inhabited facades frame the arena; their ground stays outside play.
	for side in [-1.0,1.0]:
		var source := library.find_child("VISTA_West" if side<0 else "VISTA_East",true,false) as MeshInstance3D
		_copy_mesh(source,Vector3(side*53.4,0,0),Vector3(side*77,0,0),Vector3(.5,.8,.65),false)
		var end_source := library.find_child("VISTA_SouthCourt" if side<0 else "VISTA_NorthCourt",true,false) as MeshInstance3D
		_copy_mesh(end_source,Vector3(0,0,side*68),Vector3(0,0,side*145),Vector3(.7,.75,.55),false)
	for z in [-24.0,24.0]:
		var gallery := library.find_child("SOLID_AvenueGallery_South",true,false) as MeshInstance3D
		_copy_mesh(gallery,Vector3(0,0,z),Vector3(0,0,-28),Vector3(.72,.72,1),true)
	library.free()
	var paving := ShaderMaterial.new()
	paving.shader = FINISH
	paving.set_shader_parameter("surface_kind",3)
	paving.set_shader_parameter("sangam_paving",true)
	paving.set_shader_parameter("arrival_court_z",54.0)
	paving.set_shader_parameter("lane_count",3)
	var streets := PackedVector4Array([Vector4(-32,-44,-32,40),Vector4(32,-44,32,40),Vector4(0,-44,0,38)])
	streets.resize(8)
	paving.set_shader_parameter("lane_segments",streets)
	_box("Paving",Vector3(0,-.25,0),Vector3(100,.5,130),paving,true)
	for x in [-50.5,50.5]:
		var wall:=_box("CourtyardWall",Vector3(x,2.8,0),Vector3(1,5.6,132),_stone,true)
		wall.mesh=DETAIL_KIT.beveled_box(Vector3(.92,5.6,132),.03)
	for z in [-65.5,65.5]:
		var wall:=_box("EndWall",Vector3(0,3.2,z),Vector3(102,6.4,1),_stone,true)
		wall.mesh=DETAIL_KIT.beveled_box(Vector3(102,6.4,.92),.03)
	# A restrained upper frieze and piers give walls human-scale rhythm.
	for x in [-49.8,49.8]:
		_box("IndigoFrieze",Vector3(x,4.9,0),Vector3(.18,.6,130),_indigo,false)
		for z in range(-60,61,12):
			_box("WallPier",Vector3(x,2.8,z),Vector3(.45,5.6,.55),_stone,false)
	_street_art()
	var carved_trim:=_architecture_material(Color(.77,.71,.59),4)
	var relief=DETAIL_KIT.new().build(_data,[_stone,_indigo,carved_trim])
	add_child(relief)
	_metrics["decorative_relief_triangles"]=int(relief.get_meta("triangles"))
	_metrics["decorative_material_batches"]=int(relief.get_meta("material_batches"))
	for site in sites:
		_site_mark(site,sites[site])
	for z in _data.buy_barrier_z: _buy_barrier(float(z))
	_label("SOUTH COURT",Vector3(0,3,-64.8),0,Color(.91,.72,.38))
	_label("NORTH COURT",Vector3(0,3,64.8),PI,Color(.55,.77,.92))
	_lighting()
	_metrics.ready = true
	set_buy_barriers(true)

func _fail(reason: String) -> void:
	_metrics.errors.append(reason)
	push_error("Tactical map: " + reason)

static func _v(value: Array) -> Vector3:
	return Vector3(float(value[0]),float(value[1]),float(value[2]))

func _plain(color: Color, roughness: float) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.roughness = roughness
	return material

func _architecture_material(tint:Color,kind:int)->ShaderMaterial:
	var material:=ShaderMaterial.new()
	material.shader=FINISH
	material.set_shader_parameter("mineral_tint",tint)
	material.set_shader_parameter("surface_kind",kind)
	material.set_shader_parameter("minimum_roughness",.58 if kind==2 else .78)
	if kind==4:
		material.set_shader_parameter("joint_gain",0.0)
		material.set_shader_parameter("variation_gain",.05)
	return material

func _finish(source: Material) -> Material:
	if not source is StandardMaterial3D: return source
	var id := source.get_instance_id()
	if _materials.has(id): return _materials[id]
	var label := source.resource_name.to_lower()
	var tint: Color
	var kind:=0
	if label.contains("sandstone"): tint = Color(.69,.59,.46)
	elif label.contains("limestone"): tint = Color(.80,.76,.65);kind=1
	elif label.contains("indigo"): tint = Color(.17,.25,.32);kind=2
	else: return source
	var material := _architecture_material(tint,kind)
	material.set_shader_parameter("source_maps",true)
	material.set_shader_parameter("source_albedo",source.albedo_texture)
	material.set_shader_parameter("source_roughness",source.roughness_texture)
	var channel := Vector4.ZERO
	if source.roughness_texture_channel < 4: channel[source.roughness_texture_channel] = 1.0
	else: channel = Vector4(.333333,.333333,.333333,0)
	material.set_shader_parameter("roughness_channel",channel)
	_materials[id] = material
	return material

func _copy_mesh(source: MeshInstance3D, destination: Vector3, origin: Vector3, scale_: Vector3, collision: bool) -> void:
	var visual := MeshInstance3D.new()
	visual.name = source.name
	visual.mesh = source.mesh # Shared immutable imported geometry/material inputs.
	visual.position = destination - origin * scale_
	visual.scale = scale_
	for surface in visual.mesh.get_surface_count():
		visual.set_surface_override_material(surface,_finish(visual.mesh.surface_get_material(surface)))
	add_child(visual)
	_metrics.reused_meshes += 1
	var faces := visual.mesh.get_faces()
	_metrics.triangles += faces.size()/3
	if collision:
		# Bake transform into triangle data: no non-uniform physics-body scale.
		for i in faces.size(): faces[i] = visual.transform * faces[i]
		var shape := ConcavePolygonShape3D.new()
		shape.backface_collision = true
		shape.set_faces(faces)
		_body("ArtCollision",shape,Vector3.ZERO)

func _body(label: String, shape: Shape3D, center: Vector3) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = label
	body.position = center
	body.collision_layer = 1
	body.collision_mask = 0
	var holder := CollisionShape3D.new()
	holder.shape = shape
	body.add_child(holder)
	add_child(body)
	_metrics.collision_bodies += 1
	return body

func _box(label: String, center: Vector3, dimensions: Vector3, material: Material, collision: bool) -> MeshInstance3D:
	var visual := MeshInstance3D.new()
	visual.name = label
	var mesh := BoxMesh.new()
	mesh.size = dimensions
	visual.mesh = mesh
	visual.material_override = material
	visual.position = center
	add_child(visual)
	if collision:
		var shape := BoxShape3D.new()
		shape.size = dimensions
		_body(label + "Collision",shape,center)
	return visual

func _crate(label: String, base: Vector3, dimensions: Vector3) -> void:
	var core:=_box(label,base+Vector3.UP*dimensions.y*.5,dimensions,_indigo,true)
	core.mesh=DETAIL_KIT.beveled_box(dimensions-Vector3(.04,0,.04),.045)
	for z in [-.36,.36]:
		_box("BrassBand",base+Vector3(0,dimensions.y+.012,z*dimensions.z),Vector3(dimensions.x,.025,.08),_brass,false)
	for x in [-.5,.5]:
		_box("EdgeFrame",base+Vector3(x*dimensions.x,dimensions.y*.5,0),Vector3(.06,dimensions.y,dimensions.z+.04),_brass,false)

func _street_art() -> void:
	var timber := _plain(Color("32271d"),.95)
	var cloth := [_plain(Color("20374c"),1),_plain(Color("b3a58c"),1),_plain(Color("795144"),1)]
	var nature_scene: PackedScene = load("res://assets/world/nature.glb")
	var nature: Node3D = nature_scene.instantiate()
	var lantern := nature.find_child("transit_lantern",true,false) as MeshInstance3D
	var reed := nature.find_child("reed_cluster",true,false) as MeshInstance3D
	# Awning stalls hug existing facades; main/flank corridors remain unobstructed.
	var stall_index := 0
	for side in [-1.0,1.0]:
		for z in [-31.0,-17.0,17.0,31.0]:
			var x: float = side*24.0
			_box("MarketCounter",Vector3(x,.425,z),Vector3(1.6,.85,4.2),_stone,false)
			_box("WorkedTimberCountertop",Vector3(x,.9,z),Vector3(1.8,.1,4.4),timber,false)
			for stripe in 4:
				var panel := _box("WovenAwning",Vector3(side*24.1,3.05,z-1.8+stripe*1.2),Vector3(3.8,.045,1.19),cloth[(stripe+stall_index)%3],false)
				panel.rotation.z = side*.085
				_box("AwningValance",Vector3(side*25.9,2.72,z-1.8+stripe*1.2),Vector3(.05,.34,1.19),cloth[(stripe+stall_index)%3],false)
			for end in [-2.25,2.25]:
				_box("StallPost",Vector3(side*25.7,1.5,z+end),Vector3(.14,3,.14),timber,false)
			_copy_mesh(lantern,Vector3(side*25.5,2.02,z+1.75),Vector3.ZERO,Vector3(.38,.7,.38),false)
			# Small storage pieces belong under the canopy, below the sightline.
			for end in [-1.25,1.25]:
				_box("DisplayChest",Vector3(x,1.12,z+end),Vector3(.6,.36,.7),timber,false)
			stall_index += 1
	var soil := _plain(Color("2e2d23"),1)
	var planter_points: Array[Vector3] = []
	for side in [-1.0,1.0]:
		for z in [-34.0,-12.0,14.0,36.0]: planter_points.append(Vector3(side*47.4,0,z))
		for z in [-58.0,58.0]: planter_points.append(Vector3(side*16,0,z))
	var clusters: Array = [[],[],[]]
	for index in planter_points.size():
		var point: Vector3 = planter_points[index]
		_box("GardenPlanter",point+Vector3.UP*.34,Vector3(2.6,.68,3.8),_stone,false)
		_box("PlanterSoil",point+Vector3.UP*.69,Vector3(2.25,.025,3.45),soil,false)
		for lip in [-1.3,1.3]:
			_box("PlanterStoneLip",point+Vector3(lip,.72,0),Vector3(.16,.15,3.95),_stone,false)
		for k in 5:
			var offset := Vector3(sin(float(k)*2.4)*.65,.95+float(k%3)*.24,cos(float(k)*2.4)*1.12)
			clusters[(index+k)%3].append(Transform3D(Basis.from_scale(Vector3(.9+float(k%2)*.2,.9+float(k%3)*.16,.9)),point+offset))
		_copy_mesh(reed,point+Vector3(-.8,.7,.8),Vector3.ZERO,Vector3(.7,1.25,.7),false)
		_copy_mesh(reed,point+Vector3(.7,.7,-.9),Vector3.ZERO,Vector3(.7,1.1,.7),false)
	# Three shared leaf batches give variation without one node/draw per leaf clump.
	var greens := [Color("344b2a"),Color("465d31"),Color("526a39")]
	for index in 3:
		var mesh := SphereMesh.new()
		mesh.radius = .65
		mesh.height = 1.3
		mesh.radial_segments = 12
		mesh.rings = 6
		mesh.material = _plain(greens[index],1)
		var instances := MultiMesh.new()
		instances.transform_format = MultiMesh.TRANSFORM_3D
		instances.mesh = mesh
		instances.instance_count = clusters[index].size()
		for k in clusters[index].size(): instances.set_instance_transform(k,clusters[index][k])
		var batch := MultiMeshInstance3D.new()
		batch.name = "GardenLeafBatch"
		batch.multimesh = instances
		add_child(batch)
	nature.free()
	var architecture_scene: PackedScene = load("res://assets/world/architecture.glb")
	var architecture: Node3D = architecture_scene.instantiate()
	_copy_mesh(architecture.find_child("lanka_shikhara",true,false),Vector3(0,-2,83),Vector3.ZERO,Vector3(22,38,22),false)
	_copy_mesh(architecture.find_child("lanka_watchtower",true,false),Vector3(-29,-1,80),Vector3.ZERO,Vector3(11,23,11),false)
	_copy_mesh(architecture.find_child("lanka_watchtower",true,false),Vector3(29,-1,80),Vector3.ZERO,Vector3(11,23,11),false)
	_copy_mesh(architecture.find_child("transit_tower",true,false),Vector3(0,-1,-80),Vector3.ZERO,Vector3(14,30,14),false)
	architecture.free()
	# Hanging textiles stay above player height and never resemble danger warnings.
	for z in [-24.0,24.0]:
		for x in [-4.5,4.5]:
			_box("GalleryPennant",Vector3(x,4.7,z),Vector3(.85,1.5,.035),cloth[0],false)
			_box("PennantBrassHem",Vector3(x,4.0,z),Vector3(.86,.08,.05),_brass,false)
	# Shared ground-solid data also drives minimap footprints; overhead stays clear.
	for detail in _data.get("static_details",[]):
		var size_ := _v(detail.size)
		var shape := BoxShape3D.new()
		shape.size = size_
		_body(String(detail.id),shape,_v(detail.position)+Vector3.UP*size_.y*.5)
	_metrics["static_details"] = _data.get("static_details",[]).size()
	_metrics["street_stalls"] = 8
	_metrics["planters"] = planter_points.size()
	_metrics["leaf_batches"] = 3
	_metrics["continuous_vistas"] = 4
	_metrics["overhead_connectors"] = 2

func _site_mark(id: String, point: Vector3) -> void:
	var color := Color(.19,.69,.68) if id == "A" else Color(.91,.53,.24)
	var material := _plain(color,.9)
	for offset in [-5.0,5.0]:
		_box("Site"+id,point+Vector3(offset,.012,0),Vector3(.12,.024,10),material,false)
		_box("Site"+id,point+Vector3(0,.012,offset),Vector3(10,.024,.12),material,false)
	# Text sits above solid cover, not in the central objective interaction space.
	_label(id,point+Vector3(0,3.8,8),0,color)

func _label(text_: String, position_: Vector3, yaw: float, color: Color) -> void:
	var label := Label3D.new()
	label.text = text_
	label.font_size = 64
	label.pixel_size = .015
	label.modulate = color
	label.outline_modulate = Color(.025,.035,.045)
	label.outline_size = 10
	label.position = position_
	label.rotation.y = yaw
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	add_child(label)

func _buy_barrier(z: float) -> void:
	var material := _plain(Color(.31,.65,.88,.035),.8)
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	_barrier_visuals.append(_box("BuyBarrierVisual",Vector3(0,3,z),Vector3(100,6,.2),material,false))
	var edge := _plain(Color(.38,.67,.77),.8)
	edge.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	for y in [.08,5.95]:
		_barrier_visuals.append(_box("BuyBarrierEdge",Vector3(0,y,z),Vector3(100,.06,.08),edge,false))
	var shape := BoxShape3D.new()
	shape.size = Vector3(100,12,.4)
	_barriers.append(_body("BuyBarrier",shape,Vector3(0,6,z)))

func _lighting() -> void:
	var environment := WorldEnvironment.new()
	environment.environment = Environment.new()
	environment.environment.background_mode = Environment.BG_SKY
	var sky := ProceduralSkyMaterial.new()
	sky.sky_top_color = Color("245e85")
	sky.sky_horizon_color = Color("b8c9cd")
	sky.ground_bottom_color = Color("34464c")
	sky.ground_horizon_color = Color("94a6aa")
	sky.sky_curve = .43
	sky.ground_curve = .2
	sky.sky_energy_multiplier = .82
	sky.ground_energy_multiplier = .45
	sky.sun_angle_max = .8
	sky.sun_curve = .08
	environment.environment.sky = Sky.new()
	environment.environment.sky.sky_material = sky
	environment.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.environment.ambient_light_color = Color("c1cddb")
	environment.environment.ambient_light_energy = .28
	environment.environment.ambient_light_sky_contribution = 0.0
	environment.environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.environment.ssao_enabled = RenderingServer.get_current_rendering_method()=="forward_plus"
	environment.environment.ssao_radius = .7
	environment.environment.ssao_intensity = 1.05
	environment.environment.ssao_power = 1.15
	environment.environment.ssao_detail = .55
	environment.environment.ssao_light_affect = .12
	environment.environment.fog_enabled = true
	environment.environment.fog_mode = Environment.FOG_MODE_DEPTH
	environment.environment.fog_depth_begin = 42
	environment.environment.fog_depth_end = 180
	environment.environment.fog_depth_curve = 1.55
	environment.environment.fog_density = .0008
	environment.environment.fog_light_color = Color("9bb3c0")
	environment.environment.fog_light_energy = .35
	environment.environment.fog_sky_affect = .06
	add_child(environment)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-48,-28,0)
	sun.light_color = Color("fff0df")
	sun.light_energy = 1.05
	sun.shadow_enabled = true
	sun.shadow_bias = .08
	sun.shadow_normal_bias = .25
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_4_SPLITS
	sun.directional_shadow_max_distance = 100
	sun.directional_shadow_blend_splits = true
	add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.rotation_degrees = Vector3(-55,137,0)
	fill.light_color = Color("a8c7e5")
	fill.light_energy = .14
	fill.shadow_enabled = false
	fill.sky_mode = DirectionalLight3D.SKY_MODE_LIGHT_ONLY
	add_child(fill)

func set_buy_barriers(enabled: bool) -> void:
	_metrics.buy_barriers = enabled
	for body in _barriers: body.collision_layer = 1 if enabled else 0
	for visual in _barrier_visuals: visual.visible = enabled

func spawn(team: String, index: int, attack_team: String) -> Vector3:
	var offset: Array = _data.get("spawn_offsets_x",[0,-3,3,-6,6])
	var role := "attack" if team==attack_team else "defend"
	return Vector3(float(offset[posmod(index,5)]),.08,float(_data.get("spawn_z",{"attack":-54,"defend":54})[role]))

func route(team: String, index: int, attack_team: String, target_site: String) -> Array[Vector3]:
	var result: Array[Vector3] = []
	if not sites.has(target_site) or not _data.has("routes") or team not in ["sun","moon"] or attack_team not in ["sun","moon"]: return result
	result.append(spawn(team,index,attack_team))
	var role := "attack" if team==attack_team else "defend"
	for point in _data.routes[target_site][role][posmod(index,3)]: result.append(Vector3(point[0],.08,point[1]))
	return result

func is_buy_zone(pos: Vector3, team: String, attack_team: String) -> bool:
	if not pos.is_finite() or team not in ["sun","moon"] or attack_team not in ["sun","moon"]: return false
	if not bounds.has_point(Vector2(pos.x,pos.z)) or absf(pos.y)>2.0: return false
	var limit := float(_data.get("buy_zone_min_abs_z",45))
	return pos.z <= -limit if team==attack_team else pos.z >= limit

func callout(pos: Vector3) -> String:
	if not pos.is_finite() or not bounds.has_point(Vector2(pos.x,pos.z)): return "Outside arena"
	if pos.z < -44: return "South Court"
	if pos.z > 44: return "North Court"
	if pos.distance_to(sites.A)<12: return "A / Lotus Court"
	if pos.distance_to(sites.B)<12: return "B / Indigo Yard"
	if absf(pos.x)>39: return "West Arcade" if pos.x<0 else "East Arcade"
	if absf(pos.x)<8: return "Mid / Sundial"
	return "Lotus Approach" if pos.x<0 else "Indigo Approach"

func report() -> Dictionary:
	var result := _metrics.duplicate(true)
	result["id"] = "sangam-crossing-tactical-v1"
	result["sites"] = sites.duplicate(true)
	result["triangles_scope"] = "Reused imported geometry only; procedural boxes excluded. Not a GPU performance measurement."
	result["scope"] = "Original offline tactical map, two sites, physical cover/barriers, immutable Sangam art. No MOBA armies, online or hardware-performance claim."
	return result
