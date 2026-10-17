extends RefCounted
## Original runtime mesh workshop. No imported commercial models or animation.
## Parts share cached meshes/materials; high-frequency costume details fade at 42m.

static var mesh_cache: Dictionary = {}
static var material_cache: Dictionary = {}

static func _material(key: String, color: Color, metal := 0.0) -> StandardMaterial3D:
	if material_cache.has(key):
		return material_cache[key]
	var material := StandardMaterial3D.new()
	material.albedo_color = color
	material.metallic = metal
	material.roughness = 0.64 if metal > 0 else 0.86
	material_cache[key] = material
	return material

static func _mesh(kind: String, size: Vector3) -> Mesh:
	var key := kind + str(size)
	if mesh_cache.has(key):
		return mesh_cache[key]
	var value: Mesh
	if kind == "sphere":
		var shape := SphereMesh.new()
		shape.radius = size.x
		shape.height = size.y
		shape.radial_segments = 12
		shape.rings = 6
		value = shape
	elif kind == "box":
		var shape := BoxMesh.new()
		shape.size = size
		value = shape
	else:
		var shape := CylinderMesh.new()
		shape.top_radius = size.x
		shape.height = size.y
		shape.bottom_radius = size.z
		shape.radial_segments = 12
		value = shape
	mesh_cache[key] = value
	return value

static func _part(parent: Node3D, name_value: String, kind: String, size: Vector3, at: Vector3, material: Material, detail := false) -> MeshInstance3D:
	var part := MeshInstance3D.new()
	part.name = name_value
	part.mesh = _mesh(kind, size)
	part.material_override = material
	part.position = at
	part.visibility_range_end = 42.0 if detail else 155.0
	part.visibility_range_end_margin = 4.0
	part.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF if detail else GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	parent.add_child(part)
	return part

static func _joint(parent: Node3D, name_value: String, at: Vector3) -> Node3D:
	var joint := Node3D.new()
	joint.name = name_value
	joint.position = at
	parent.add_child(joint)
	return joint

static func build(team: String, role: String) -> Dictionary:
	var root := Node3D.new()
	root.name = "OriginalArticulatedUnit"
	var cloth := _material(team + "cloth", Color("b64a24") if team == "sun" else Color("235c8c"))
	var trim := _material(team + "trim", Color("edc87a") if team == "sun" else Color("a3d9ec"), 0.55)
	var skin := _material("skin", Color("946244"))
	var dark := _material("boots", Color("302923"))
	var steel := _material("steel", Color("92948d"), 0.65)
	var wood := _material("wood", Color("533b25"))
	var torso := _joint(root, "Torso", Vector3(0, 1.08, 0))
	_part(torso, "QuiltedCuirass", "cylinder", Vector3(.23,.58,.27), Vector3(0,.12,0), cloth)
	_part(torso, "BrassWaist", "cylinder", Vector3(.276,.09,.278), Vector3(0,-.15,0), trim, true)
	_part(torso, "ChestPlate", "box", Vector3(.33,.33,.05), Vector3(0,.17,.236), trim, true)
	_part(torso, "DhotiSkirt", "cylinder", Vector3(.26,.32,.34), Vector3(0,-.32,0), cloth)
	var head := _joint(torso, "Head", Vector3(0,.53,0))
	_part(head, "Face", "sphere", Vector3(.145,.30,.145), Vector3.ZERO, skin)
	_part(head, "Nose", "box", Vector3(.055,.08,.07), Vector3(0,.015,.143), skin, true)
	_part(head, "HeadWrap", "cylinder", Vector3(.16,.16,.17), Vector3(0,.14,-.008), cloth)
	_part(head, "WrapBand", "cylinder", Vector3(.173,.035,.173), Vector3(0,.12,-.008), trim, true)
	var joints := {"torso":torso,"head":head}
	for side in [-1,1]:
		var suffix := "left" if side == -1 else "right"
		var shoulder := _joint(torso, suffix + "Shoulder", Vector3(side*.31,.33,0))
		_part(shoulder, "UpperArm", "cylinder", Vector3(.078,.29,.066), Vector3(0,-.145,0), cloth)
		_part(shoulder, "ShoulderGuard", "sphere", Vector3(.115,.15,.115), Vector3(0,-.04,0), trim, true)
		var elbow := _joint(shoulder, suffix + "Elbow", Vector3(0,-.30,0))
		_part(elbow, "Forearm", "cylinder", Vector3(.065,.27,.05), Vector3(0,-.135,0), skin)
		_part(elbow, "Bracer", "cylinder", Vector3(.067,.15,.06), Vector3(0,-.17,0), trim, true)
		var hand := _joint(elbow, suffix + "Hand", Vector3(0,-.29,0))
		_part(hand, "Hand", "sphere", Vector3(.062,.115,.062), Vector3.ZERO, skin)
		var hip := _joint(root, suffix + "Hip", Vector3(side*.14,.79,0))
		_part(hip, "TrouserLeg", "cylinder", Vector3(.105,.35,.085), Vector3(0,-.175,0), cloth)
		var knee := _joint(hip, suffix + "Knee", Vector3(0,-.36,0))
		_part(knee, "Shin", "cylinder", Vector3(.078,.31,.065), Vector3(0,-.155,0), dark)
		_part(knee, "Boot", "box", Vector3(.15,.12,.29), Vector3(0,-.35,.065), dark)
		joints[suffix + "_shoulder"] = shoulder
		joints[suffix + "_elbow"] = elbow
		joints[suffix + "_hand"] = hand
		joints[suffix + "_hip"] = hip
		joints[suffix + "_knee"] = knee
	var weapon := _joint(joints.right_hand, "Weapon", Vector3.ZERO)
	joints.weapon = weapon
	if role == "bow_guard":
		weapon.reparent(joints.left_hand, false)
		for i in range(10):
			var angle := -1.18 + float(i)*2.36/9.0
			var point := Vector3(0, sin(angle)*.63, cos(angle)*.28)
			var segment := _part(weapon, "BowLimb%d" % i, "cylinder", Vector3(.022,.16,.022), point, wood)
			segment.rotation.x = -angle
		_part(weapon, "BowString", "cylinder", Vector3(.006,1.15,.006), Vector3(0,0,.11), trim, true)
		_part(torso, "Quiver", "cylinder", Vector3(.105,.54,.085), Vector3(.12,.18,-.30), wood)
		for i in range(3):
			_part(torso, "StoredArrow%d" % i, "cylinder", Vector3(.012,.58,.012), Vector3(.08+i*.04,.38,-.30), trim, true)
	else:
		_part(weapon, "SpearShaft", "cylinder", Vector3(.023,1.65,.023), Vector3(0,.45,0), wood)
		_part(weapon, "LeafSpearhead", "cylinder", Vector3(0,.30,.09), Vector3(0,1.42,0), steel)
		weapon.rotation.x = .38
		var shield := _part(joints.left_hand, "RoundShield", "cylinder", Vector3(.25,.07,.25), Vector3(0,.02,.08), cloth)
		shield.rotation.x = PI/2
		var boss := _part(joints.left_hand, "ShieldBoss", "sphere", Vector3(.085,.10,.085), Vector3(0,.02,.13), trim, true)
		boss.scale = Vector3(1,1,.6)
	if role == "commander":
		root.scale = Vector3.ONE*1.12
		_part(head, "CrownBand", "cylinder", Vector3(.185,.13,.18), Vector3(0,.26,0), trim)
		for i in range(5):
			var a := float(i)*TAU/5.0
			_part(head, "CrownFin%d" % i, "cylinder", Vector3(0,.20,.035), Vector3(cos(a)*.15,.40,sin(a)*.15), trim, true)
		_part(torso, "BannerPole", "cylinder", Vector3(.025,2.25,.025), Vector3(-.15,.60,-.31), wood)
		var banner := _joint(torso, "Banner", Vector3(-.15,1.43,-.31))
		_part(banner, "TeamStandard", "box", Vector3(.70,.49,.018), Vector3(.34,-.16,0), cloth)
		_part(banner, "StandardMedallion", "cylinder", Vector3(.115,.025,.115), Vector3(.34,-.16,.02), trim, true).rotation.x = PI/2
		joints.banner = banner
	var ring := _part(root, "TeamFootRing", "cylinder", Vector3(.38,.016,.38), Vector3(0,.012,0), trim)
	ring.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	return {"root":root,"joints":joints,"role":role,"team":team,"provenance":"Original procedural geometry and articulated motion; no commercial-derived content"}
