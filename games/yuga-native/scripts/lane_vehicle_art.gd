extends RefCounted
## Original fantasy siege vehicles; cached meshes/materials, no external assets.
## Root translation/heading belong to lane_minion. Pose touches child joints only.

static var mesh_cache: Dictionary = {}
static var material_cache: Dictionary = {}
const ROLES := ["cannon_cart", "royal_chariot"]
const WHEEL_RADIUS := {"cannon_cart":.22,"royal_chariot":.25}

static func _material(key: String, color: String, metallic := 0.0) -> StandardMaterial3D:
	if not material_cache.has(key):
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(color)
		material.metallic = metallic
		material.roughness = .66 if metallic > 0 else .9
		material_cache[key] = material
	return material_cache[key]

static func _mesh(kind: String, size: Vector3) -> Mesh:
	var key := kind+str(size)
	if mesh_cache.has(key):return mesh_cache[key]
	var result: Mesh
	if kind == "box":
		var mesh := BoxMesh.new()
		mesh.size = size
		result = mesh
	elif kind == "sphere":
		var mesh := SphereMesh.new()
		mesh.radius = size.x
		mesh.height = size.y
		mesh.radial_segments = 12
		mesh.rings = 6
		result = mesh
	else:
		var mesh := CylinderMesh.new()
		mesh.top_radius = size.x
		mesh.height = size.y
		mesh.bottom_radius = size.z
		mesh.radial_segments = 12
		mesh.rings = 1
		result = mesh
	mesh_cache[key] = result
	return result

static func _part(parent: Node3D, label: String, mesh: Mesh, material: Material, at: Vector3) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = label
	part.mesh = mesh
	part.material_override = material
	part.position = at
	part.visibility_range_end = 155
	part.visibility_range_end_margin = 5
	parent.add_child(part)
	return part

static func _primitive(parent: Node3D, label: String, kind: String, size: Vector3, at: Vector3, material: Material) -> MeshInstance3D:
	return _part(parent,label,_mesh(kind,size),material,at)

static func _joint(parent: Node3D, label: String, at: Vector3) -> Node3D:
	var node := Node3D.new()
	node.name = label
	node.position = at
	parent.add_child(node)
	return node

static func _wheel(radius: float) -> Mesh:
	var key := "wheel"+str(radius)
	if mesh_cache.has(key):return mesh_cache[key]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Beveled outer edges and eight spokes retain the exact wheel/contact radius.
	for i in range(24):
		var a := float(i)*TAU/24
		var b := float(i+1)*TAU/24
		var rings: Array = []
		for spec in [Vector2(-.045,radius*.96),Vector2(-.03,radius),Vector2(.03,radius),Vector2(.045,radius*.96),Vector2(.045,radius*.78),Vector2(-.045,radius*.78)]:
			rings.append([Vector3(spec.x,cos(a)*spec.y,sin(a)*spec.y),Vector3(spec.x,cos(b)*spec.y,sin(b)*spec.y)])
		for side in range(rings.size()):
			var next := (side+1)%rings.size()
			for point in [rings[side][0],rings[side][1],rings[next][0],rings[side][1],rings[next][1],rings[next][0]]:surface.add_vertex(point)
	# Spokes belong to the shared mesh, not extra scene nodes.
	for i in range(8):
		var angle := float(i)*TAU/8
		var spoke := BoxMesh.new()
		spoke.size = Vector3(.07,radius*.82,.035)
		var basis := Basis(Vector3.RIGHT,angle)
		for point in spoke.get_faces():
			surface.add_vertex(basis*(point+Vector3(0,radius*.39,0)))
	surface.generate_normals()
	var result := surface.commit()
	mesh_cache[key] = result
	return result

static func _deck() -> Mesh:
	if mesh_cache.has("joined_deck"):return mesh_cache.joined_deck
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for index in range(7):
		var board := _mesh("box",Vector3(.137,.13,.94))
		surface.append_from(board,0,Transform3D(Basis.IDENTITY,Vector3((index-3)*.142,0,0)))
	var mesh := surface.commit()
	mesh_cache.joined_deck = mesh
	return mesh

static func _barrel() -> Mesh:
	if mesh_cache.has("turned_barrel"):return mesh_cache.turned_barrel
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Turned reinforce bands are part of one shared cast-bronze barrel mesh.
	var rings := [Vector2(-.54,.16),Vector2(-.44,.16),Vector2(-.42,.145),Vector2(-.23,.14),Vector2(-.21,.158),Vector2(-.16,.158),Vector2(-.14,.138),Vector2(.27,.128),Vector2(.29,.148),Vector2(.34,.148),Vector2(.36,.127),Vector2(.54,.13)]
	for ring in range(rings.size()-1):
		for index in range(20):
			var points: Array = []
			for corner in [Vector2i(ring,index),Vector2i(ring,index+1),Vector2i(ring+1,index),Vector2i(ring+1,index+1)]:
				var spec: Vector2 = rings[corner.x]
				var angle := float(corner.y)*TAU/20
				points.append(Vector3(cos(angle)*spec.y,sin(angle)*spec.y,spec.x))
			for vertex in [0,1,2,1,3,2]:surface.add_vertex(points[vertex])
	surface.generate_normals()
	var mesh := surface.commit()
	mesh_cache.turned_barrel = mesh
	return mesh

static func _joinery(role: String) -> Mesh:
	var key := "joinery_"+role
	if mesh_cache.has(key):return mesh_cache[key]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for side in [-1,1]:
		for z in [-.36,0,.36]:
			var bolt := _mesh("cylinder",Vector3(.023,.014,.023))
			surface.append_from(bolt,0,Transform3D(Basis(Vector3.FORWARD,PI/2),Vector3(side*.513,.49,z)))
		# Diagonal corner straps make the rail construction legible at close range.
		for end in [-1,1]:
			var strap := _mesh("box",Vector3(.016,.055,.23))
			surface.append_from(strap,0,Transform3D(Basis(Vector3.RIGHT,end*.35),Vector3(side*.511,.49,end*.29)))
	if role == "royal_chariot":
		for index in range(8):
			var angle := float(index)*TAU/8
			var petal := _mesh("sphere",Vector3(.038,.15,.038))
			var basis := Basis(Vector3.FORWARD,angle).scaled(Vector3(1,1,.35))
			surface.append_from(petal,0,Transform3D(basis,Vector3(sin(-angle)*.12,.9+cos(angle)*.12,-.295)))
	var mesh := surface.commit()
	mesh_cache[key] = mesh
	return mesh

static func _tube(points: Array, radius: float, key: String) -> Mesh:
	if mesh_cache.has(key):return mesh_cache[key]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(points.size()-1):
		var start: Vector3 = points[i]
		var finish: Vector3 = points[i+1]
		var direction := (finish-start).normalized()
		var right := direction.cross(Vector3.UP).normalized()
		if right.length_squared() < .01:right = Vector3.RIGHT
		var up := direction.cross(right).normalized()
		for j in range(8):
			var a := float(j)*TAU/8
			var b := float(j+1)*TAU/8
			var x := (right*cos(a)+up*sin(a))*radius
			var y := (right*cos(b)+up*sin(b))*radius
			for point in [start+x,finish+x,start+y,start+y,finish+x,finish+y]:surface.add_vertex(point)
	surface.generate_normals()
	var result := surface.commit()
	mesh_cache[key] = result
	return result

static func _banner() -> Mesh:
	if mesh_cache.has("banner"):return mesh_cache.banner
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# A small closed pennant gives both faces thickness, avoiding coincident faces.
	var points := [Vector3(-.20,.19,0),Vector3(.20,.19,0),Vector3(.20,-.19,0),Vector3(0,-.09,0),Vector3(-.20,-.19,0)]
	for z in [-.009,.009]:
		for face in [[0,1,3],[1,2,3],[0,3,4]]:
			var order: Array = face if z < 0 else [face[2],face[1],face[0]]
			for index in order:surface.add_vertex(points[index]+Vector3(0,0,z))
	for i in range(points.size()):
		var j := (i+1)%points.size()
		for point in [points[i]+Vector3(0,0,-.009),points[j]+Vector3(0,0,-.009),points[i]+Vector3(0,0,.009),points[j]+Vector3(0,0,-.009),points[j]+Vector3(0,0,.009),points[i]+Vector3(0,0,.009)]:surface.add_vertex(point)
	surface.generate_normals()
	var result := surface.commit()
	mesh_cache.banner = result
	return result

static func build(team: String, role: String) -> Dictionary:
	var root := Node3D.new()
	root.name = "OriginalSiegeVehicle"
	if role not in ROLES or team not in ["sun","moon"]:return {"root":root,"joints":{},"valid":false}
	var wood := _material("wood","503e2c")
	var light_wood := _material("wood_edges","806341")
	var dark := _material("iron","262f32",.25)
	var brass := _material(team+"brass","b59150" if team == "sun" else "8cabb4",.45)
	var cloth := _material(team+"cloth","88432c" if team == "sun" else "285f70")
	var rope := _material("rope","b7a27a")
	var chassis := _joint(root,"Chassis",Vector3.ZERO)
	var joints := {"chassis":chassis,"wheels":[]}
	var wheel_rest: Array = []
	var radius: float = WHEEL_RADIUS[role]
	var wheel_x := .54 if role == "cannon_cart" else .59
	var wheel_z := .32 if role == "cannon_cart" else .35
	for side in [-1,1]:
		for end in [-1,1]:
			var wheel := _joint(chassis,"Wheel_%d_%d"%[side,end],Vector3(side*wheel_x,radius,end*wheel_z))
			_part(wheel,"CarvedWoodRim",_wheel(radius),wood,Vector3.ZERO)
			_primitive(wheel,"AxleCap","cylinder",Vector3(.065,.12,.065),Vector3.ZERO,brass).rotation.z = PI/2
			joints.wheels.append(wheel)
			wheel_rest.append(wheel.position)
	for end in [-1,1]:
		_primitive(chassis,"CrossAxle%d"%end,"cylinder",Vector3(.045,wheel_x*2,.045),Vector3(0,radius,end*wheel_z),dark).rotation.z = PI/2
	_part(chassis,"JoinedDeckPlanks",_deck(),wood,Vector3(0,.42,0))
	for side in [-1,1]:
		_primitive(chassis,"CarvedRail%d"%side,"box",Vector3(.09,.16,1.02),Vector3(side*.46,.49,0),light_wood)
	var fittings := _part(chassis,"RailJoineryAndRoyalRosette",_joinery(role),brass,Vector3.ZERO)
	fittings.visibility_range_end = 42
	fittings.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var weapon := _joint(chassis,"WeaponCradle",Vector3(0,.99,0))
	joints.weapon = weapon
	if role == "cannon_cart":
		for side in [-1,1]:
			_primitive(chassis,"TrunnionStand%d"%side,"box",Vector3(.12,.38,.30),Vector3(side*.23,.70,0),wood)
			_primitive(weapon,"Trunnion%d"%side,"cylinder",Vector3(.10,.14,.10),Vector3(side*.19,0,0),brass).rotation.z = PI/2
		_part(weapon,"TurnedBronzeBarrel",_barrel(),brass,Vector3(0,0,.025))
		_primitive(weapon,"MuzzleRing","cylinder",Vector3(.17,.075,.17),Vector3(0,0,.59),brass).rotation.x = PI/2
		_primitive(weapon,"DarkBore","cylinder",Vector3(.119,.008,.119),Vector3(0,0,.632),dark).rotation.x = PI/2
		_primitive(weapon,"Breech","sphere",Vector3(.15,.28,.15),Vector3(0,0,-.53),dark)
		_primitive(chassis,"PowderChest","box",Vector3(.53,.25,.24),Vector3(0,.61,-.34),cloth)
		_primitive(chassis,"ChestStrap","box",Vector3(.08,.27,.25),Vector3(0,.61,-.34),brass)
		_primitive(chassis,"PullYoke","box",Vector3(.58,.08,.10),Vector3(0,.40,.61),wood)
	else:
		weapon.position.y = 1.23
		_primitive(chassis,"RoyalBackboard","box",Vector3(.84,.60,.10),Vector3(0,.86,-.36),cloth)
		for side in [-1,1]:
			_primitive(chassis,"BackPillar%d"%side,"cylinder",Vector3(.055,1.20,.065),Vector3(side*.42,1.02,-.35),brass)
			_primitive(chassis,"LotusFinial%d"%side,"sphere",Vector3(.085,.19,.085),Vector3(side*.42,1.68,-.35),brass)
		_primitive(chassis,"CrownArch","box",Vector3(.91,.10,.13),Vector3(0,1.57,-.35),brass)
		for i in [-1,0,1]:
			_primitive(chassis,"CrownPoint%d"%i,"cylinder",Vector3(0,.23 if i == 0 else .16,.075),Vector3(i*.23,1.74,-.35),brass)
		_primitive(chassis,"BallistaColumn","cylinder",Vector3(.10,.62,.14),Vector3(0,.83,.05),wood)
		_primitive(weapon,"BallistaStock","box",Vector3(.18,.14,1.02),Vector3(0,0,.03),wood)
		var bow_points := [Vector3(-.65,0,.27),Vector3(-.49,0,.12),Vector3(-.27,0,.02),Vector3.ZERO,Vector3(.27,0,.02),Vector3(.49,0,.12),Vector3(.65,0,.27)]
		_part(weapon,"HeavyBowLimbs",_tube(bow_points,.042,"heavy_bow"),brass,Vector3.ZERO)
		var string := _joint(weapon,"DrawString",Vector3.ZERO)
		joints.string = string
		joints.cords = []
		for side in [-1,1]:
			joints.cords.append(_primitive(string,"TensionCord%d"%side,"cylinder",Vector3(.011,1,.011),Vector3.ZERO,rope))
		_primitive(weapon,"LoadedBolt","cylinder",Vector3(.025,.85,.025),Vector3(0,.10,.10),dark).rotation.x = PI/2
		_primitive(weapon,"BoltPoint","cylinder",Vector3(0,.18,.055),Vector3(0,.10,.61),brass).rotation.x = PI/2
	var banner_x := .30 if role == "cannon_cart" else .0
	var banner_y := 1.65 if role == "cannon_cart" else 2.17
	_primitive(chassis,"BannerMast","cylinder",Vector3(.018,banner_y-.45,.018),Vector3(banner_x,(banner_y+.45)*.5,-.38),wood)
	var banner := _joint(chassis,"TeamPennant",Vector3(banner_x,banner_y,-.38))
	_part(banner,"ThickNotchedStandard",_banner(),cloth,Vector3.ZERO)
	_primitive(banner,"StandardSeal","sphere",Vector3(.055,.11,.055),Vector3(0,.025,.025),brass).scale.z = .25
	joints.banner = banner
	var art := {"root":root,"joints":joints,"role":role,"team":team,"valid":true,"last_time":-1.0,"wheel_angle":0.0,"weapon_rest":weapon.position,"banner_rest":banner.position,"wheel_rest":wheel_rest}
	pose(art,role,0,0,0,0,true,0)
	return art

static func pose(art: Dictionary, role: String, time: float, moved: float, attack_time: float, hit_time: float, alive: bool, dead_age: float) -> void:
	if role not in ROLES or not art.get("valid",false) or role != art.get("role",""):return
	if not is_finite(time) or not is_finite(moved) or not is_finite(attack_time) or not is_finite(hit_time) or not is_finite(dead_age):return
	var joints: Dictionary = art.joints
	var last: float = art.get("last_time",-1.0)
	if time < last or last < 0:
		art.wheel_angle = 0.0
	var delta := clampf(time-maxf(last,0),0,.1) if time >= last else 0.0
	art.last_time = time
	var speed := clampf(absf(moved)*20,0,8) if alive else 0.0
	art.wheel_angle = fposmod(float(art.wheel_angle)+speed*delta/float(WHEEL_RADIUS[role]),TAU)
	var travel := minf(speed/3,1)
	var safe_time := fposmod(time,10000.0)
	joints.chassis.position = Vector3(0,sin(safe_time*13)*.008*travel,0)
	joints.chassis.rotation = Vector3(0,0,sin(safe_time*9)*.012*travel)
	joints.weapon.position = art.weapon_rest
	joints.weapon.rotation = Vector3.ZERO
	joints.banner.position = art.banner_rest
	joints.banner.rotation = Vector3(0,sin(safe_time*2.2)*.08,0)
	var impact_remaining := .40 if role == "cannon_cart" else .45
	var remaining := clampf(attack_time,0,1.20 if role == "cannon_cart" else 1.0)
	var firing := 1.0-clampf((impact_remaining-remaining)/.22,0,1) if remaining > 0 and remaining <= impact_remaining else 0.0
	joints.weapon.position.z -= firing*(.13 if role == "cannon_cart" else .09)
	joints.weapon.rotation.x = -.035*firing
	joints.chassis.rotation.x = clampf(hit_time,0,.3)*.10
	if joints.has("string"):
		var draw := clampf((1.0-remaining)/.55,0,1) if remaining > impact_remaining else 0.0
		var middle := Vector3(0,0,-.23-draw*.09)
		for i in range(2):
			var tip := Vector3(-.64 if i == 0 else .64,0,.27)
			var direction := middle-tip
			var cord: MeshInstance3D = joints.cords[i]
			cord.position = (middle+tip)*.5
			cord.quaternion = Quaternion(Vector3.UP,direction.normalized())
			cord.scale = Vector3(1,direction.length(),1)
	if not alive:
		var fall := clampf(dead_age/.8,0,1)
		joints.chassis.position = Vector3(0,-fall*.12,0)
		joints.chassis.rotation = Vector3(fall*.035,0,0)
		joints.weapon.rotation.x = fall*.10
		joints.banner.rotation.x = fall*.08

	# Suspension moves the carriage, while wheel contact remains on the lane plane.
	var inverse: Transform3D = joints.chassis.transform.affine_inverse()
	for i in range(joints.wheels.size()):
		var wheel: Node3D = joints.wheels[i]
		wheel.position = inverse*art.wheel_rest[i]
		wheel.basis = inverse.basis*Basis(Vector3.RIGHT,float(art.wheel_angle))
