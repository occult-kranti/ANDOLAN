extends RefCounted
## Original, batched scenic sculpture. No collision, lights or gameplay outcomes.
## The river loom and hanging lotus lamps are invented motifs, not reconstructions.

const ROOT_NAME := "MythicEnvironment"
const MAX_MESHES := 6
const MAX_TRIANGLES := 18000
const RIVER_LOOM_ORIGIN := Vector3(-88.0, 0.0, -18.0)
const PALETTE := {
	"basalt": Color("233d49"), "sandstone": Color("a5926d"),
	"brass": Color("a47b3f"), "patina": Color("386970"),
	"wick": Color("ffc88a"), "inlay": Color("d3c6a7")
}
var surfaces: Dictionary = {}
var motif_count := 0

static func configure(world: Node3D, district: String) -> Node3D:
	if not is_instance_valid(world) or district not in ["courtyard", "confluence"]:
		return null
	var existing := world.get_node_or_null(ROOT_NAME) as Node3D
	if existing != null:
		return existing
	var node := Node3D.new()
	node.name = ROOT_NAME
	node.set_meta("district", district)
	node.set_meta("visual_only", true)
	world.add_child(node)
	var builder = new()
	if district == "courtyard": builder._courtyard()
	else: builder._confluence()
	builder._finish(node)
	set_phase(world, 0.0)
	return node

static func set_phase(world: Node3D, value: float) -> void:
	if not is_instance_valid(world): return
	var node := world.get_node_or_null(ROOT_NAME)
	if node == null: return
	var phase := clampf(value, 0.0, 1.0) if is_finite(value) else 0.0
	node.set_meta("phase", phase)
	for child in node.get_children():
		if child is MeshInstance3D:
			var material := child.material_override as StandardMaterial3D
			if material != null and child.name == "wick":
				material.emission_energy_multiplier = lerpf(0.65, 1.3, phase)

static func diagnostics(world: Node3D) -> Dictionary:
	var node := world.get_node_or_null(ROOT_NAME) if is_instance_valid(world) else null
	var report := {"meshes":0,"triangles":0,"lights":0,"collision_objects":0,
		"motifs":0,"phase":0.0,"mesh_budget":MAX_MESHES,"triangle_budget":MAX_TRIANGLES}
	if node == null: return report
	report.motifs = node.get_meta("motif_count", 0)
	report.phase = node.get_meta("phase", 0.0)
	for child in node.get_children():
		if child is MeshInstance3D:
			report.meshes += 1
			report.triangles += child.mesh.get_faces().size() / 3
		if child is Light3D: report.lights += 1
		if child is CollisionObject3D: report.collision_objects += 1
	return report

func _courtyard() -> void:
	# Lamps hang above existing gallery passages, not across the training lane.
	for side in [-1.0, 1.0]:
		for z in [-13.0, -7.0, -1.0, 5.0, 11.0]:
			var p := Vector3(side * 16.3, 4.5, z)
			_lotus_lamp(p, 0.52, 1.25)
			motif_count += 1
	# Seven rays rise from an open dawn crest behind the existing gate crown.
	# Its deliberately incomplete fan cannot read as a combat ground circle.
	var origin := Vector3(0, 12.1, -26.3)
	for i in range(7):
		var angle := deg_to_rad(25.0 + i * 21.6667)
		var direction := Vector3(cos(angle), sin(angle), 0)
		var a := origin + direction * 0.9
		var b := origin + direction * (3.7 if i % 2 == 0 else 3.1)
		_tube("brass", a, b, 0.085, 8)
		_lozenge("inlay", b, direction, Vector3.FORWARD, 0.38, 0.14)
	motif_count += 1

func _confluence() -> void:
	# The river loom stands beyond the west boundary (x=-70). It is a skyline
	# anchor, with no reachable false cover and no extra broadphase body.
	var centre := RIVER_LOOM_ORIGIN
	_box("basalt", centre + Vector3(0, 0.45, 0), Vector3(2.0, 0.9, 8.2))
	_box("sandstone", centre + Vector3(0, 1.0, 0), Vector3(1.7, 0.2, 7.8))
	for rib in range(7):
		var spread := (rib - 3) * 1.0
		var points: Array[Vector3] = []
		for step in range(13):
			var t := float(step) / 12.0
			points.append(centre + Vector3(-sin(t * PI) * 1.0, 1.1 + t * (8.3 - absf(spread) * 0.55),
				spread * (0.16 + sin(t * PI * 0.68) * 1.1)))
		for step in range(points.size() - 1):
			_tube("patina", points[step], points[step + 1], 0.15, 8)
		var tip: Vector3 = points.back()
		_lozenge("brass", tip, Vector3.UP, Vector3.RIGHT, 0.54, 0.23)
		_lotus_lamp(tip - Vector3(0, 1.0, 0), 0.28, 0.65)
	motif_count += 1
	# Twin outboard ghat lantern boats sit beyond the playable west edge.
	for z in [-13.0, 17.0]:
		var boat := Vector3(-73.2, 0.18, z)
		_box("basalt", boat, Vector3(1.5, 0.18, 3.8))
		for offset in [-1.0, 0.0, 1.0]:
			_lotus_lamp(boat + Vector3(0, 0.4, offset), 0.34, 0.0)
		motif_count += 1
	# Roof-level signs: sparse lotus kite silhouettes on the temple gallery,
	# kept out of the centre lane and all grounded target silhouettes.
	for x in [-22.0, 22.0]:
		for z in [-24.0, 24.0]:
			var p := Vector3(x, 15.4, z)
			_tube("brass", p - Vector3(0, 1.8, 0), p + Vector3(0, 1.0, 0), 0.065, 8)
			_lozenge("inlay", p, Vector3.UP, Vector3.FORWARD, 1.1, 0.5)
			_lozenge("patina", p + Vector3(0, 0, -0.02), Vector3.UP, Vector3.FORWARD, 0.68, 0.28)
			motif_count += 1

func _lotus_lamp(p: Vector3, radius: float, chain_height: float) -> void:
	if chain_height > 0.0:
		_tube("brass", p + Vector3.UP * 0.16, p + Vector3.UP * chain_height, 0.018, 5)
	for i in range(8):
		var angle := i * TAU / 8.0
		var direction := Vector3(cos(angle), 0.45, sin(angle)).normalized()
		_lozenge("brass", p + Vector3(cos(angle), 0.0, sin(angle)) * radius * 0.45,
			direction, Vector3(-sin(angle), 0, cos(angle)), radius * 0.54, radius * 0.22)
	_tube("wick", p + Vector3.UP * 0.02, p + Vector3.UP * radius * 0.46, radius * 0.065, 6)

func _box(material: String, centre: Vector3, size: Vector3) -> void:
	var mesh := BoxMesh.new()
	mesh.size = size
	_append_mesh(material, mesh, Transform3D(Basis.IDENTITY, centre))

func _tube(material: String, a: Vector3, b: Vector3, radius: float, segments: int) -> void:
	var direction := b - a
	if direction.length_squared() < 0.000001: return
	var mesh := CylinderMesh.new()
	mesh.top_radius = radius
	mesh.bottom_radius = radius
	mesh.height = direction.length()
	mesh.radial_segments = segments
	mesh.rings = 1
	var up := direction.normalized()
	var right := up.cross(Vector3.FORWARD).normalized()
	if right.length_squared() < 0.01: right = Vector3.RIGHT
	var forward := right.cross(up).normalized()
	_append_mesh(material, mesh, Transform3D(Basis(right, up, forward), (a + b) * 0.5))

func _lozenge(material: String, p: Vector3, axis: Vector3, normal: Vector3, length: float, width: float) -> void:
	var long_axis := axis.normalized()
	var side := normal.cross(long_axis).normalized()
	var raised := normal.normalized() * 0.07
	var points := [p + long_axis * length, p + side * width,
		p - long_axis * length, p - side * width, p + raised, p - raised]
	for index in range(4):
		_triangle(material, points[index], points[(index + 1) % 4], points[4])
		_triangle(material, points[(index + 1) % 4], points[index], points[5])

func _append_mesh(material: String, mesh: PrimitiveMesh, transform: Transform3D) -> void:
	var arrays := mesh.get_mesh_arrays()
	var vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
	var indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
	for i in range(0, indices.size(), 3):
		_triangle(material, transform * vertices[indices[i]], transform * vertices[indices[i + 1]], transform * vertices[indices[i + 2]])

func _triangle(material: String, a: Vector3, b: Vector3, c: Vector3) -> void:
	if not surfaces.has(material): surfaces[material] = {"vertices":PackedVector3Array(),"normals":PackedVector3Array()}
	# Godot front faces are clockwise; reverse the mathematical CCW normal.
	var normal := (c - a).cross(b - a).normalized()
	if normal.length_squared() < 0.01: return
	surfaces[material].vertices.append_array(PackedVector3Array([a, b, c]))
	surfaces[material].normals.append_array(PackedVector3Array([normal, normal, normal]))

func _finish(root: Node3D) -> void:
	root.set_meta("motif_count", motif_count)
	for key in surfaces:
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = surfaces[key].vertices
		arrays[Mesh.ARRAY_NORMAL] = surfaces[key].normals
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var material := StandardMaterial3D.new()
		material.albedo_color = PALETTE[key]
		material.metallic = 0.65 if key in ["brass", "patina"] else 0.0
		material.roughness = 0.52 if key in ["brass", "patina"] else 0.84
		if key == "wick":
			material.emission_enabled = true
			material.emission = PALETTE[key]
		var instance := MeshInstance3D.new()
		instance.name = key
		instance.mesh = mesh
		instance.material_override = material
		# Original facade geometry still casts the grounded scene shadows.
		# These fine ornaments do not need extra high-frequency shadow detail.
		instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(instance)
