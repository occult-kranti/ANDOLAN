extends RefCounted
## Original old-kingdom infantry, authored as shared rigid mesh assemblies.
## No textures, imported models, lights, colliders or independent simulation clock.
## Pose is a pure sample of the existing lane-unit army clock/attack state.

const ROLES := ["spearman", "bow_guard", "commander"]
const UPPER := .29
const LOWER := .28
const NEAR_DISTANCE := 42.0
static var mesh_cache: Dictionary = {}
static var material_cache: Dictionary = {}
static var primitive_cache: Dictionary = {}

static func _material(key: String, color: String, metal := 0.0) -> StandardMaterial3D:
	if not material_cache.has(key):
		var material := StandardMaterial3D.new()
		material.albedo_color = Color(color)
		material.metallic = metal
		material.roughness = .57 if metal > 0 else .88
		material_cache[key] = material
	return material_cache[key]

static func _primitive(kind: String, size: Vector3) -> Mesh:
	var key := kind + str(size)
	if primitive_cache.has(key): return primitive_cache[key]
	var mesh: Mesh
	if kind == "box":
		var shape := BoxMesh.new()
		shape.size = size
		mesh = shape
	elif kind == "sphere":
		var shape := SphereMesh.new()
		shape.radius = size.x
		shape.height = size.y
		shape.radial_segments = 16
		shape.rings = 8
		mesh = shape
	else:
		var shape := CylinderMesh.new()
		shape.top_radius = size.x
		shape.height = size.y
		shape.bottom_radius = size.z
		shape.radial_segments = 12
		mesh = shape
	primitive_cache[key] = mesh
	return mesh

static func _profile(key: String, rings: Array, segments := 16, pleat := 0.0) -> Mesh:
	if primitive_cache.has(key): return primitive_cache[key]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	# Each ring is width, height, depth; varying rings shape chest/waist and calves.
	for row in range(rings.size()-1):
		for index in range(segments):
			var points: Array[Vector3] = []
			for corner in [Vector2i(row,index), Vector2i(row,index+1), Vector2i(row+1,index), Vector2i(row+1,index+1)]:
				var ring: Vector3 = rings[corner.x]
				var angle := float(corner.y)*TAU/segments
				var fold := 1.0 + (pleat if corner.y % 2 == 0 else -pleat)
				points.append(Vector3(cos(angle)*ring.x*fold,ring.y,sin(angle)*ring.z*fold))
			for vertex in [0,2,1,1,2,3]: surface.add_vertex(points[vertex])
	for row in [0,rings.size()-1]:
		var ring: Vector3 = rings[row]
		for index in range(segments):
			var angles := [float(index)*TAU/segments, float(index+1)*TAU/segments]
			var points: Array[Vector3] = [Vector3(0,ring.y,0)]
			for angle in angles: points.append(Vector3(cos(angle)*ring.x,ring.y,sin(angle)*ring.z))
			for vertex in ([0,2,1] if row == 0 else [0,1,2]): surface.add_vertex(points[vertex])
	surface.generate_normals()
	var mesh := surface.commit()
	primitive_cache[key] = mesh
	return mesh

static func _tube(key: String, points: Array, radius: float, sides := 8) -> Mesh:
	if primitive_cache.has(key): return primitive_cache[key]
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(points.size()-1):
		var a: Vector3 = points[i]
		var b: Vector3 = points[i+1]
		var axis := (b-a).normalized()
		var across := axis.cross(Vector3.RIGHT).normalized()
		if across.length_squared() < .01: across = Vector3.FORWARD
		var up := axis.cross(across).normalized()
		for side in range(sides):
			var angle := float(side)*TAU/sides
			var next := float(side+1)*TAU/sides
			var p := (cos(angle)*across+sin(angle)*up)*radius
			var q := (cos(next)*across+sin(next)*up)*radius
			for vertex in [a+p,a+q,b+p,a+q,b+q,b+p]: surface.add_vertex(vertex)
	surface.generate_normals()
	var mesh := surface.commit()
	primitive_cache[key] = mesh
	return mesh

static func _leaf() -> Mesh:
	if primitive_cache.has("spear_leaf"): return primitive_cache.spear_leaf
	var surface := SurfaceTool.new()
	surface.begin(Mesh.PRIMITIVE_TRIANGLES)
	var points := [Vector3(0,.21,0),Vector3(-.064,-.04,0),Vector3(0,-.17,0),Vector3(.064,-.04,0),Vector3(0,0,.023),Vector3(0,0,-.023)]
	for face in [[0,4,1],[1,4,2],[2,4,3],[3,4,0],[0,1,5],[1,2,5],[2,3,5],[3,0,5]]:
		for index in face: surface.add_vertex(points[index])
	surface.generate_normals()
	var mesh := surface.commit()
	primitive_cache.spear_leaf = mesh
	return mesh

static func _spec(mesh: Mesh, material: Material, at := Vector3.ZERO, scale_value := Vector3.ONE, rotation_value := Vector3.ZERO) -> Dictionary:
	return {"mesh":mesh,"material":material,"transform":Transform3D(Basis.from_euler(rotation_value).scaled(scale_value),at)}

static func _shape(kind: String, size: Vector3, material: Material, at := Vector3.ZERO, scale_value := Vector3.ONE, rotation_value := Vector3.ZERO) -> Dictionary:
	return _spec(_primitive(kind,size),material,at,scale_value,rotation_value)

static func _batch(parent: Node3D, key: String, parts: Array, detail := false) -> MeshInstance3D:
	if not mesh_cache.has(key):
		var grouped := {}
		for part in parts:
			var id: int = part.material.get_instance_id()
			if not grouped.has(id): grouped[id] = []
			grouped[id].append(part)
		var mesh := ArrayMesh.new()
		for entries in grouped.values():
			var surface := SurfaceTool.new()
			surface.begin(Mesh.PRIMITIVE_TRIANGLES)
			for entry in entries: surface.append_from(entry.mesh,0,entry.transform)
			surface.set_material(entries[0].material)
			surface.index()
			surface.commit(mesh)
		mesh_cache[key] = mesh
	var node := MeshInstance3D.new()
	node.name = key.get_slice("/",0)
	node.mesh = mesh_cache[key]
	node.visibility_range_end = NEAR_DISTANCE if detail else 155.0
	node.visibility_range_end_margin = 4.0
	node.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if detail else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(node)
	return node

static func _joint(parent: Node3D, label: String, at: Vector3) -> Node3D:
	var node := Node3D.new()
	node.name = label
	node.position = at
	parent.add_child(node)
	return node

static func build(team: String, role: String) -> Dictionary:
	var root := Node3D.new()
	root.name = "OldKingdomInfantry"
	if team not in ["sun","moon"] or role not in ROLES:
		return {"root":root,"joints":{},"valid":false}
	var cloth := _material(team+"cloth","823c24" if team == "sun" else "234b60")
	var edge := _material(team+"edge","c29044" if team == "sun" else "9eb1b4",.48)
	var linen := _material("linen","c5b38c")
	var skin := _material("skin","986448")
	var leather := _material("leather","402d20")
	var hair := _material("hair","211e1b")
	var iron := _material("iron","707a78",.68)
	var wood := _material("wood","68502f")
	var suffix := "/"+team
	var torso := _joint(root,"Torso",Vector3(0,1.04,0))
	var head := _joint(torso,"Head",Vector3(0,.56,0))
	var joints := {"torso":torso,"head":head}
	var body := _profile("fitted_tunic",[Vector3(.19,-.20,.13),Vector3(.21,-.08,.145),Vector3(.255,.18,.16),Vector3(.25,.30,.145),Vector3(.105,.39,.09)])
	var drape := _profile("pleated_wrap",[Vector3(.215,-.18,.145),Vector3(.265,-.37,.17),Vector3(.235,-.53,.16)],24,.045)
	_batch(torso,"FittedCuirass"+suffix,[_spec(body,cloth),_spec(drape,linen),_shape("cylinder",Vector3(.072,.15,.08),skin,Vector3(0,.43,0)),_shape("cylinder",Vector3(.219,.07,.212),leather,Vector3(0,-.16,0),Vector3(1,1,.70))])
	var trim: Array = [_shape("box",Vector3(.085,.52,.023),edge,Vector3(.025,.13,.168),Vector3.ONE,Vector3(0,0,-.42)),_shape("sphere",Vector3(.051,.075,.051),edge,Vector3(.04,-.16,.17),Vector3(1,1,.35))]
	for side in [-1,1]:
		# Overlapping broad lamellar plates are geometry, not painted fake shading.
		for row in range(3):
			trim.append(_shape("box",Vector3(.145,.065,.025),leather,Vector3(side*.12,.06+row*.075,.153),Vector3.ONE,Vector3(0,side*.12,side*.04)))
		trim.append(_shape("box",Vector3(.065,.31,.026),cloth,Vector3(side*.145,-.34,.159),Vector3.ONE,Vector3(0,0,side*.12)))
	_batch(torso,"LamellarSashAndBelt"+suffix,trim,true)
	var face := _profile("shaped_face",[Vector3(.065,-.13,.067),Vector3(.099,-.08,.09),Vector3(.118,.03,.105),Vector3(.105,.13,.091)],16)
	_batch(head,"FaceAndWrap"+suffix,[_spec(face,skin),_shape("sphere",Vector3(.143,.18,.143),cloth,Vector3(0,.115,-.013),Vector3(1.08,1,.95)),_shape("sphere",Vector3(.057,.10,.057),cloth,Vector3(.13,.13,-.02),Vector3(.75,1,1)),_shape("sphere",Vector3(.026,.073,.026),skin,Vector3(0,-.003,.107),Vector3(.73,1,.95))])
	var facial: Array = []
	for side in [-1,1]:
		facial.append(_shape("sphere",Vector3(.024,.055,.024),skin,Vector3(side*.115,.005,0),Vector3(.6,1,.72)))
		facial.append(_shape("box",Vector3(.044,.012,.013),hair,Vector3(side*.052,.042,.094),Vector3.ONE,Vector3(0,side*.12,side*.10)))
		facial.append(_shape("sphere",Vector3(.034,.026,.034),hair,Vector3(side*.027,-.047,.099),Vector3(1,.75,.3)))
	for row in range(3):
		facial.append(_shape("cylinder",Vector3(.148,.023,.146),linen,Vector3(0,.088+row*.043,-.014),Vector3(1.06,1,.95),Vector3(.05,0,-.09+row*.05)))
	_batch(head,"BrowsMoustacheWrapFolds"+suffix,facial,true)
	for side in [-1,1]:
		var label := "left" if side < 0 else "right"
		var shoulder := _joint(torso,label+"Shoulder",Vector3(side*.275,.31,0))
		var upper := _profile("sleeved_upper_arm",[Vector3(.074,0,.078),Vector3(.088,-.06,.082),Vector3(.066,-UPPER,.065)],12)
		_batch(shoulder,"Sleeve"+suffix,[_spec(upper,cloth),_shape("sphere",Vector3(.10,.135,.10),edge,Vector3(0,-.02,0),Vector3(1,1,.9))])
		var elbow := _joint(shoulder,label+"Elbow",Vector3(0,-UPPER,0))
		var forearm := _profile("shaped_forearm",[Vector3(.058,.02,.062),Vector3(.065,-.08,.066),Vector3(.045,-LOWER,.041)],12)
		_batch(elbow,"ForearmAndBracer"+suffix,[_spec(forearm,skin),_shape("cylinder",Vector3(.062,.125,.052),leather,Vector3(0,-.19,0)),_shape("cylinder",Vector3(.061,.022,.061),edge,Vector3(0,-.135,0))])
		var hand := _joint(elbow,label+"Hand",Vector3(0,-LOWER,0))
		_batch(hand,"GraspingHand",[_shape("sphere",Vector3(.057,.105,.057),skin,Vector3(0,-.012,0),Vector3(.85,1,.75))])
		var hip := _joint(root,label+"Hip",Vector3(side*.135,.77,0))
		var thigh := _profile("wrapped_thigh",[Vector3(.115,0,.10),Vector3(.104,-.12,.09),Vector3(.075,-.35,.072)],12,.025)
		_batch(hip,"WrappedThigh",[_spec(thigh,linen)])
		var knee := _joint(hip,label+"Knee",Vector3(0,-.35,0))
		var shin := _profile("shaped_calf",[Vector3(.073,0,.071),Vector3(.078,-.11,.073),Vector3(.047,-.29,.048)],12)
		_batch(knee,"CalfAndSandal"+suffix,[_spec(shin,skin),_shape("sphere",Vector3(.069,.085,.069),leather,Vector3(0,-.36,.052),Vector3(1.05,1,1.8)),_shape("cylinder",Vector3(.061,.10,.054),leather,Vector3(0,-.25,0)),_shape("cylinder",Vector3(.057,.025,.057),edge,Vector3(0,-.29,0))])
		joints[label+"_shoulder"] = shoulder
		joints[label+"_elbow"] = elbow
		joints[label+"_hand"] = hand
		joints[label+"_hip"] = hip
		joints[label+"_knee"] = knee
	var weapon := _joint(joints.left_hand if role == "bow_guard" else joints.right_hand,"Weapon",Vector3.ZERO)
	joints.weapon = weapon
	if role == "bow_guard":
		var bow_points: Array = []
		for index in range(25):
			var y := -.60+float(index)*.05
			bow_points.append(Vector3(0,y,.14*sin(absf(y)/.60*PI)-.05*pow(absf(y)/.60,3)))
		_batch(weapon,"RecurveBow",[_spec(_tube("continuous_recurve",bow_points,.021),wood),_shape("cylinder",Vector3(.025,.15,.025),leather)])
		joints.cords = []
		for side in [-1,1]:
			joints.cords.append(_batch(weapon,"BowCord",[_shape("cylinder",Vector3(.0035,1,.0035),linen)],true))
		var nock := _joint(weapon,"NockedArrow",Vector3.ZERO)
		_batch(nock,"NockedShaft",[_shape("cylinder",Vector3(.009,.67,.009),wood,Vector3(0,0,.32),Vector3.ONE,Vector3(PI/2,0,0)),_shape("box",Vector3(.028,.005,.09),linen,Vector3(0,0,.04))])
		joints.nock = nock
		var quiver_parts: Array = [_shape("cylinder",Vector3(.085,.47,.065),leather,Vector3(.10,.13,-.23),Vector3.ONE,Vector3(.12,0,-.18)),_shape("cylinder",Vector3(.09,.04,.09),edge,Vector3(.14,.35,-.25))]
		for index in range(3):
			quiver_parts.append(_shape("cylinder",Vector3(.009,.34,.009),wood,Vector3(.10+index*.03,.44,-.25)))
			quiver_parts.append(_shape("box",Vector3(.031,.10,.006),linen,Vector3(.10+index*.03,.58,-.25)))
		_batch(torso,"QuiverAndFletching"+suffix,quiver_parts)
	else:
		_batch(weapon,"LeafSpear"+suffix,[_shape("cylinder",Vector3(.022,1.68,.022),wood,Vector3(0,.44,0)),_spec(_leaf(),iron,Vector3(0,1.43,0)),_shape("cylinder",Vector3(.029,.16,.029),edge,Vector3(0,1.18,0)),_shape("cylinder",Vector3(.025,.18,.025),leather)])
		var shield := _joint(joints.left_hand,"DhalShield",Vector3(0,.02,.055))
		var dome := _profile("domed_shield",[Vector3(.29,0,.29),Vector3(.24,.055,.24),Vector3(.08,.092,.08),Vector3(0,.108,0)],24)
		_batch(shield,"DhalFace"+suffix,[_spec(dome,cloth,Vector3.ZERO,Vector3.ONE,Vector3(PI/2,0,0))])
		var relief: Array = [_shape("sphere",Vector3(.066,.10,.066),edge,Vector3(0,0,.108),Vector3(1,1,.6))]
		var rim_points: Array = []
		for index in range(33):
			var angle := float(index)*TAU/32
			rim_points.append(Vector3(cos(angle)*.281,sin(angle)*.281,.018))
		relief.append(_spec(_tube("shield_rim",rim_points,.012),edge))
		for index in range(8):
			var angle := float(index)*TAU/8
			relief.append(_shape("sphere",Vector3(.018,.036,.018),edge,Vector3(cos(angle)*.21,sin(angle)*.21,.062),Vector3(1,1,.4)))
		_batch(shield,"ShieldBossRimAndStuds"+suffix,relief,true)
		joints.shield = shield
	if role == "commander":
		root.scale = Vector3.ONE*1.12
		var crown: Array = [_shape("cylinder",Vector3(.163,.06,.16),edge,Vector3(0,.19,-.01),Vector3(1,1,.94))]
		for index in range(5):
			var angle := float(index)*TAU/5
			crown.append(_spec(_leaf(),edge,Vector3(cos(angle)*.135,.27,sin(angle)*.125),Vector3(.38,.48,.4)))
		_batch(head,"RoyalCrest"+suffix,crown)
		_batch(torso,"StandardPole",[_shape("cylinder",Vector3(.018,1.70,.018),wood,Vector3(-.17,.59,-.24))])
		var banner := _joint(torso,"Banner",Vector3(-.17,1.28,-.24))
		var cloth_points := [Vector3(0,0,0),Vector3(.22,-.02,.02),Vector3(.48,-.05,0)]
		# Layered folds retain a broad readable split-tail commander silhouette.
		var banner_parts: Array = []
		for index in range(3):
			banner_parts.append(_shape("box",Vector3(.18,.36 if index != 1 else .27,.02),cloth,cloth_points[index]+Vector3(.08,-.14,0),Vector3.ONE,Vector3(0,-.14+index*.14,0)))
		banner_parts.append(_shape("sphere",Vector3(.08,.15,.08),edge,Vector3(.28,-.12,.034),Vector3(1,1,.2)))
		_batch(banner,"SplitRoyalStandard"+suffix,banner_parts)
		joints.banner = banner
	var art := {"root":root,"joints":joints,"team":team,"role":role,"valid":true,"provenance":"Original Godot-authored geometry; shared rigid assemblies; no external content"}
	pose(art,0,0,0,0,true,0)
	return art

static func _arm(joints: Dictionary, side: String, target: Vector3) -> void:
	var shoulder: Node3D = joints[side+"_shoulder"]
	var elbow: Node3D = joints[side+"_elbow"]
	var hand: Node3D = joints[side+"_hand"]
	var vector := target-shoulder.position
	var distance := clampf(vector.length(),.06,UPPER+LOWER-.001)
	var direction := vector.normalized()
	var outward := Vector3(-1 if side == "left" else 1,0,-.4)
	var pole := (outward-direction*outward.dot(direction)).normalized()
	var along := (UPPER*UPPER-LOWER*LOWER+distance*distance)/(2*distance)
	var bend := sqrt(maxf(0,UPPER*UPPER-along*along))
	var elbow_point := shoulder.position+direction*along+pole*bend
	shoulder.quaternion = Quaternion(Vector3.DOWN,(elbow_point-shoulder.position).normalized())
	elbow.quaternion = Quaternion(Vector3.DOWN,shoulder.basis.inverse()*(shoulder.position+direction*distance-elbow_point).normalized())
	hand.basis = (shoulder.basis*elbow.basis).inverse()

static func pose(art: Dictionary, time: float, moved: float, attack_time: float, hit_time: float, alive: bool, identity: int) -> void:
	if not art.get("valid",false): return
	for value in [time,moved,attack_time,hit_time]:
		if not is_finite(value): return
	var joints: Dictionary = art.joints
	var safe_time := fposmod(time,10000.0)
	var stride := sin(safe_time*8.8+float(posmod(identity,5))*.12)*clampf(moved/.14,0,1) if alive else 0.0
	var remaining := clampf(attack_time,0,.52) if alive else 0.0
	var phase := (.52-remaining)/.52
	var active := remaining > 0.0
	var lunge := sin(clampf(phase/.35,0,1)*PI*.5) if active and phase < .35 else (maxf(0,1-(phase-.35)/.65) if active else 0.0)
	joints.torso.position = Vector3(0,1.04+absf(stride)*.012,0)
	joints.torso.rotation = Vector3(-clampf(hit_time,0,.3)*.7,0,-stride*.035)
	joints.head.rotation = Vector3(0,stride*.035,0)
	for side in ["left","right"]:
		var sign_value := 1.0 if side == "left" else -1.0
		joints[side+"_hip"].rotation.x = stride*.42*sign_value
		joints[side+"_knee"].rotation.x = maxf(0,-stride*sign_value)*.5
	if art.role == "bow_guard":
		var draw := clampf((.52-remaining)/.26,0,1) if active and remaining > .26 else 0.0
		var released := active and remaining <= .26
		var left := Vector3(-.08,.30,.46) if active else Vector3(-.19,-.05,.20)
		var right := Vector3(.04,.30,.35-draw*.28) if active else Vector3(.21,-.19,.08)
		if released: right = Vector3(.14,.30,.02+(.26-remaining)*.35)
		_arm(joints,"left",left)
		_arm(joints,"right",right)
		joints.weapon.rotation = Vector3.ZERO
		var middle := right-left if active and not released else Vector3(0,0,-.05)
		for index in range(2):
			var tip := Vector3(0,-.60 if index == 0 else .60,-.05)
			var direction := middle-tip
			var cord: MeshInstance3D = joints.cords[index]
			cord.position = (middle+tip)*.5
			cord.quaternion = Quaternion(Vector3.UP,direction.normalized())
			cord.scale = Vector3(1,direction.length(),1)
		joints.nock.position = middle
		joints.nock.visible = active and not released
	else:
		_arm(joints,"left",Vector3(-.25,.01,.27))
		_arm(joints,"right",Vector3(.24,.01+lunge*.12,.07+lunge*.32))
		joints.weapon.rotation = Vector3(.32+lunge*1.13,0,-.06)
		joints.shield.rotation = Vector3(-.08,-.15,0)
		joints.torso.rotation.y = -lunge*.12
	if joints.has("banner"):
		joints.banner.rotation = Vector3(sin(safe_time*2.1)*.025,sin(safe_time*2.7)*.09,0)
