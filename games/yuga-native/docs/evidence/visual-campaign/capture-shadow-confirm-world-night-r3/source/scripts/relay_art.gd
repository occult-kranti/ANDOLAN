extends Node3D
## Original civic Triad relays. Presentation only; ownership comes from relay_session.
## setup() once, set_states() at10Hz, collision_boxes() for shared army authority.

const SITE_X := [-40.0,0.0,40.0]
const STATION_X := [-34.0,-6.0,34.0]
const STATION_Z := 4.0
const SITE_NAMES := ["Reed","Lotus","Sky"]
const OWNERS := ["neutral","sun","moon"]
const PLINTH_STEPS := [Vector3(1.5,.28,1.5),Vector3(1.16,.15,1.16),Vector3(.88,.13,.88)]
const PROGRESS_SEGMENTS := 8
var _built := false
var _sites: Array = []
var _states: Array = []
var _meshes: Dictionary = {}
var _materials: Dictionary = {}
var _solid_shapes: Array = []
var _elapsed := 0.0
var _night := 0.0
var _invalid_states := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE

func _material(key: String, color: String, metallic := 0.0, emission := 0.0) -> StandardMaterial3D:
	if _materials.has(key):return _materials[key]
	var material := StandardMaterial3D.new()
	material.albedo_color = Color(color)
	material.metallic = metallic
	material.roughness = .72 if metallic > 0 else .9
	if emission > 0:
		material.emission_enabled = true
		material.emission = Color(color)
		material.emission_energy_multiplier = emission
	_materials[key] = material
	return material

func _mesh(kind: String, size: Vector3) -> Mesh:
	var key := kind+str(size)
	if _meshes.has(key):return _meshes[key]
	var mesh: Mesh
	if kind == "box":
		var box := BoxMesh.new()
		box.size = size
		mesh = box
	else:
		var cylinder := CylinderMesh.new()
		cylinder.top_radius = size.x
		cylinder.height = size.y
		cylinder.bottom_radius = size.z
		cylinder.radial_segments = 12
		cylinder.rings = 1
		mesh = cylinder
	_meshes[key] = mesh
	return mesh

func _polygon(key: String, points: PackedVector2Array, depth := .035) -> Mesh:
	if _meshes.has(key):return _meshes[key]
	var indices := Geometry2D.triangulate_polygon(points)
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for side in [-1,1]:
		for i in range(0,indices.size(),3):
			var order := [indices[i],indices[i+1],indices[i+2]] if side == -1 else [indices[i+2],indices[i+1],indices[i]]
			for index in order:
				var p := points[index]
				surface.add_vertex(Vector3(p.x,p.y,side*depth*.5))
	for i in range(points.size()):
		var a := points[i]
		var b := points[(i+1)%points.size()]
		for point in [Vector3(a.x,a.y,-depth*.5),Vector3(a.x,a.y,depth*.5),Vector3(b.x,b.y,-depth*.5),Vector3(b.x,b.y,-depth*.5),Vector3(a.x,a.y,depth*.5),Vector3(b.x,b.y,depth*.5)]:surface.add_vertex(point)
	surface.generate_normals()
	var mesh := surface.commit()
	_meshes[key] = mesh
	return mesh

func _part(parent: Node3D, label: String, mesh: Mesh, at: Vector3, material: Material, casts := true) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = label
	part.mesh = mesh
	part.position = at
	part.material_override = material
	part.visibility_range_end = 160
	part.visibility_range_end_margin = 5
	if not casts:part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(part)
	return part

func _box(parent: Node3D, label: String, size: Vector3, at: Vector3, material: Material, casts := true) -> MeshInstance3D:
	return _part(parent,label,_mesh("box",size),at,material,casts)

func _node(parent: Node3D, label: String, at: Vector3) -> Node3D:
	var node := Node3D.new()
	node.name = label
	node.position = at
	parent.add_child(node)
	return node

func _owner_mesh(owner: String) -> Mesh:
	if owner == "sun":
		var sun := PackedVector2Array()
		for i in range(16):
			var angle := float(i)*TAU/16
			var radius := .29 if i%2 == 0 else .17
			sun.append(Vector2(cos(angle),sin(angle))*radius)
		return _polygon("sun_star",sun)
	if owner == "moon":
		return _polygon("moon_crescent",PackedVector2Array([Vector2(.16,.28),Vector2(-.06,.26),Vector2(-.24,.12),Vector2(-.27,-.08),Vector2(-.13,-.25),Vector2(.09,-.28),Vector2(.23,-.15),Vector2(.02,-.15),Vector2(-.10,-.04),Vector2(-.09,.11),Vector2(.03,.23)]))
	return _polygon("neutral_diamond",PackedVector2Array([Vector2(0,.24),Vector2(.20,0),Vector2(0,-.24),Vector2(-.20,0)]))

func setup() -> bool:
	if _built:return true
	process_mode = Node.PROCESS_MODE_PAUSABLE
	_material("stone","938774")
	_material("edge_stone","b2a185")
	_material("brass","a78a51",.42)
	_material("dark","273b41")
	_material("cloth","756c55")
	_material("tile","706f64")
	_material("neutral","b9b7a8")
	_material("sun","d6a34f",.15)
	_material("moon","66a9bb",.15)
	_material("progress_sun","e3b45d",.0,.28)
	_material("progress_moon","73b8c9",.0,.28)
	_material("progress_neutral","96998f")
	_material("lantern","ffbe73",.0,.75)
	for id in range(3):
		var site := _node(self,"%sRelay"%SITE_NAMES[id],Vector3.ZERO)
		var ground := _node(site,"CaptureTiles",Vector3(SITE_X[id],0,0))
		var tiles: Array = []
		# Four broken angular corners are paving, not an expanding warning circle.
		for x in [-1,1]:
			for z in [-1,1]:
				var corner := Vector3(x*3.20,.014,z*3.20)
				tiles.append(_box(ground,"CornerX_%d_%d"%[x,z],Vector3(1.10,.018,.16),corner+Vector3(-x*.36,0,0),_materials.tile,false))
				tiles.append(_box(ground,"CornerZ_%d_%d"%[x,z],Vector3(.16,.018,1.10),corner+Vector3(0,0,-z*.36),_materials.tile,false))
		var progress_parts: Array = []
		for end in [-1,1]:
			for index in range(PROGRESS_SEGMENTS):
				progress_parts.append(_box(ground,"Progress_%d_%d"%[end,index],Vector3(.39,.016,.22),Vector3((index-3.5)*.50,.026,end*2.95),_materials.tile,false))
		var motif := _part(ground,"Inlaid%sMark"%SITE_NAMES[id],_site_motif(id),Vector3(0,.024,0),_materials.edge_stone,false)
		motif.rotation.x = -PI/2
		var station := _node(site,"RelayStation",Vector3(STATION_X[id],0,STATION_Z))
		station.add_to_group("relay_station")
		var body := StaticBody3D.new()
		body.name = "VisiblePlinthBody"
		body.collision_layer = 1
		body.collision_mask = 0
		body.add_to_group("relay_plinth")
		station.add_child(body)
		var base_y := 0.0
		for step in range(PLINTH_STEPS.size()):
			var size: Vector3 = PLINTH_STEPS[step]
			var center := Vector3(0,base_y+size.y*.5,0)
			var visual := _box(body,"VisibleStep%d"%step,size,center,_materials.stone if step == 0 else _materials.edge_stone)
			var shape := CollisionShape3D.new()
			shape.name = "MatchingStep%d"%step
			shape.position = center
			var box := BoxShape3D.new()
			box.size = size
			shape.shape = box
			shape.set_meta("matching_visual",visual.get_path())
			body.add_child(shape)
			_solid_shapes.append(shape)
			base_y += size.y
		_part(station,"BrassSocket",_mesh("cylinder",Vector3(.24,.16,.32)),Vector3(0,.64,0),_materials.brass)
		_part(station,"MechanismMast",_mesh("cylinder",Vector3(.06,1.45,.08)),Vector3(0,1.40,0),_materials.dark)
		var rotor := _node(station,"%sVanes"%SITE_NAMES[id],Vector3(0,1.20,0))
		_build_rotor(rotor,id)
		var badge := _node(station,"OwnershipBadge",Vector3(0,2.12,0))
		_box(badge,"DarkEnamelBacking",Vector3(.78,.66,.09),Vector3.ZERO,_materials.dark)
		var symbols := {}
		for owner in OWNERS:
			var symbol := _node(badge,"Owner_%s"%owner,Vector3.ZERO)
			for side in [-1,1]:
				_part(symbol,"RaisedSymbol%d"%side,_owner_mesh(owner),Vector3(0,0,side*.068),_materials[owner])
			symbols[owner] = symbol
		var contested_flags := _node(station,"ContestedCrossedFlags",Vector3(0,1.94,0))
		for side in [-1,1]:
			var flag := _box(contested_flags,"CaptureFlag%d"%side,Vector3(.23,.14,.035),Vector3(side*.50,0,0),_materials.sun if side == -1 else _materials.moon)
			flag.rotation.z = side*.20
			_part(contested_flags,"FlagStaff%d"%side,_mesh("cylinder",Vector3(.012,.48,.012)),Vector3(side*.42,-.10,0),_materials.brass)
		for side in [-1,1]:
			var lamp := _node(station,"Lantern%d"%side,Vector3(side*.48,.77,0))
			_part(lamp,"CarvedBase",_mesh("cylinder",Vector3(.09,.06,.12)),Vector3.ZERO,_materials.brass)
			_box(lamp,"WarmWindow",Vector3(.11,.18,.11),Vector3(0,.12,0),_materials.lantern,false)
			_part(lamp,"LanternCrown",_mesh("cylinder",Vector3(0,.09,.12)),Vector3(0,.255,0),_materials.brass)
		_sites.append({"root":site,"ground":ground,"station":station,"body":body,"tiles":tiles,"progress":progress_parts,"rotor":rotor,"symbols":symbols,"flags":contested_flags})
	_built = true
	reset()
	return true

func _site_motif(id: int) -> Mesh:
	if id == 0:
		return _polygon("reed_ground",PackedVector2Array([Vector2(-.42,-.48),Vector2(-.27,.12),Vector2(-.10,-.30),Vector2(0,.58),Vector2(.12,-.28),Vector2(.30,.22),Vector2(.42,-.48)]),.008)
	if id == 1:
		return _polygon("lotus_ground",PackedVector2Array([Vector2(-.55,-.28),Vector2(-.43,.25),Vector2(-.17,.05),Vector2(0,.60),Vector2(.17,.05),Vector2(.43,.25),Vector2(.55,-.28),Vector2(0,-.48)]),.008)
	return _polygon("sky_ground",PackedVector2Array([Vector2(-.58,-.28),Vector2(-.58,.08),Vector2(0,.48),Vector2(.58,.08),Vector2(.58,-.28),Vector2(0,.13)]),.008)

func _build_rotor(rotor: Node3D, id: int) -> void:
	var petal := _polygon("relay_leaf",PackedVector2Array([Vector2(0,-.25),Vector2(-.11,.0),Vector2(0,.35),Vector2(.11,.0)]),.035)
	var sail := _polygon("relay_sail",PackedVector2Array([Vector2(-.15,-.22),Vector2(-.15,.25),Vector2(.22,.10),Vector2(.05,-.05)]),.035)
	var count := 3 if id != 1 else 6
	for i in range(count):
		var angle := float(i)*TAU/count
		var vane := _node(rotor,"Vane%d"%i,Vector3(sin(angle)*.30,0,cos(angle)*.30))
		vane.rotation.y = angle
		if id == 0:
			_part(vane,"ReedStem",_mesh("cylinder",Vector3(.018,.65,.024)),Vector3(0,-.10,0),_materials.brass)
			_part(vane,"ReedBlade",petal,Vector3(0,.12,0),_materials.cloth)
		elif id == 1:
			var leaf := _part(vane,"LotusPetal",petal,Vector3.ZERO,_materials.brass)
			leaf.rotation.x = -.38
		else:
			_part(vane,"WindSail",sail,Vector3.ZERO,_materials.cloth)

func reset() -> void:
	if not _built:return
	_elapsed = 0.0
	set_states([{"id":0,"owner":"neutral","contested":false,"progress":0.0,"capture_team":"neutral"},{"id":1,"owner":"neutral","contested":false,"progress":0.0,"capture_team":"neutral"},{"id":2,"owner":"neutral","contested":false,"progress":0.0,"capture_team":"neutral"}])
	_animate()

func set_states(states: Array) -> bool:
	if not _built or states.size() != 3:
		_invalid_states += 1
		return false
	var candidate: Array = []
	var ids: Array = []
	for state in states:
		if not state is Dictionary or typeof(state.get("id")) != TYPE_INT or state.id not in [0,1,2] or ids.has(state.id):
			_invalid_states += 1
			return false
		var owner = state.get("owner","neutral")
		var capture_team = state.get("capture_team","neutral")
		var progress = state.get("progress",0.0)
		var contested = state.get("contested",false)
		if owner not in OWNERS or capture_team not in OWNERS or typeof(contested) != TYPE_BOOL or typeof(progress) not in [TYPE_INT,TYPE_FLOAT] or not is_finite(float(progress)) or float(progress)<0 or float(progress)>1:
			_invalid_states += 1
			return false
		ids.append(state.id)
		candidate.append({"id":state.id,"owner":owner,"capture_team":capture_team,"progress":float(progress),"contested":contested})
	candidate.sort_custom(func(a,b):return a.id<b.id)
	_states = candidate
	for state in _states:
		var site: Dictionary = _sites[state.id]
		for owner in OWNERS:site.symbols[owner].visible = owner == state.owner
		for tile in site.tiles:tile.material_override = _materials[state.owner] if state.owner != "neutral" else _materials.tile
		var active := int(floor(state.progress*PROGRESS_SEGMENTS+.000001))
		for index in range(site.progress.size()):
			var lit := index%PROGRESS_SEGMENTS<active
			site.progress[index].material_override = _materials["progress_"+state.capture_team] if lit else _materials.tile
		site.flags.visible = state.contested
	return true

func set_night_blend(value: float) -> bool:
	if not _built or not is_finite(value):return false
	_night = clampf(value,0,1)
	_materials.lantern.emission_energy_multiplier = lerpf(.75,1.35,_night)
	return true

func _process(delta: float) -> void:
	if not _built or not is_finite(delta) or delta<=0 or not can_process():return
	var ancestor := get_parent()
	while ancestor != null:
		if ancestor.process_mode == Node.PROCESS_MODE_DISABLED:return
		ancestor = ancestor.get_parent()
	_elapsed = fposmod(_elapsed+minf(delta,.1),10000.0)
	_animate()

func _animate() -> void:
	for id in range(_sites.size()):
		var site: Dictionary = _sites[id]
		site.rotor.rotation = Vector3(0,_elapsed*(.18 if id == 1 else .12)+id*.6,0)
		# Quiet physical cloth motion; contested indicators stay steady and never flash.
		site.flags.rotation.z = sin(_elapsed*1.1)*.025

func collision_boxes() -> Array:
	var result: Array = []
	for shape in _solid_shapes:
		var size: Vector3 = shape.shape.size
		var bounds: AABB = shape.global_transform*AABB(-size*.5,size)
		result.append({"position":Vector3(bounds.get_center().x,bounds.position.y,bounds.get_center().z),"size":bounds.size})
	return result

func report() -> Dictionary:
	var pending: Array = [self]
	var nodes := 0
	var meshes := 0
	var finite := true
	while not pending.is_empty():
		var node: Node = pending.pop_back()
		nodes += 1
		pending.append_array(node.get_children())
		if node is Node3D:finite = finite and node.transform.is_finite()
		if node is MeshInstance3D:meshes += 1
	return {"ready":_built,"sites":_sites.size(),"nodes":nodes,"mesh_instances":meshes,"cached_meshes":_meshes.size(),"materials":_materials.size(),"static_bodies":_sites.size(),"collision_shapes":_solid_shapes.size(),"states":_states.duplicate(true),"finite":finite,"animation_seconds":_elapsed,"invalid_states":_invalid_states,"night_blend":_night,"scope":"Original offline relay presentation; state/damage authority belongs to relay_session. Flat capture tiles are non-solid; stepped plinths share explicit collision boxes."}
