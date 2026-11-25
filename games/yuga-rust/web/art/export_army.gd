extends SceneTree
## Bake the native articulated unit meshes into one vertex-coloured draw per
## role/team. Each GPU morph is sampled from the same Godot poses as native play.
## Run from repo root (Godot 4.6.3):
## godot --headless --path games/yuga-native --script ../yuga-rust/web/art/export_army.gd -- /absolute/path/army-vehicles.glb
const Infantry = preload("res://scripts/lane_infantry_art.gd")
const Vehicles = preload("res://scripts/lane_vehicle_art.gd")
const POSES := ["stride_a", "stride_b", "windup", "release"]
var material := StandardMaterial3D.new()
var source_surfaces := {}

func _init() -> void:
	call_deferred("export_library")

func sample_pose(art: Dictionary, role: String, pose: String) -> void:
	var walk := pose.begins_with("stride")
	var time := PI / (2.0 * 8.8) if pose == "stride_a" else 3.0 * PI / (2.0 * 8.8)
	var attack := 0.0
	if role in Vehicles.ROLES:
		var duration := 1.2 if role == "cannon_cart" else 1.0
		var impact := 0.40 if role == "cannon_cart" else 0.45
		if pose == "windup": attack = impact + 0.04
		if pose == "release": attack = impact - 0.05
		art.last_time = time
		art.wheel_angle = (PI / 8.0 if pose == "stride_a" else -PI / 8.0) if walk else 0.0
		Vehicles.pose(art, role, time, 0.16 if walk else 0.0, attack, 0.0, true, 0.0)
	else:
		if pose == "windup": attack = 0.42 if role == "bow_guard" else 0.38
		if pose == "release": attack = 0.32 if role == "bow_guard" else 0.31
		Infantry.pose(art, time, 0.16 if walk else 0.0, attack, 0.0, true, 0)

func collect(root: Node3D, node: Node3D, parts: Array) -> void:
	if node is MeshInstance3D and node.mesh and node.visible:
		for s in node.mesh.get_surface_count():
			var key := Vector2i(node.mesh.get_instance_id(), s)
			if not source_surfaces.has(key):
				var surface := SurfaceTool.new()
				surface.create_from(node.mesh, s)
				surface.index()
				source_surfaces[key] = surface.commit_to_arrays()
			var input: Array = source_surfaces[key]
			var mat: Material = node.get_active_material(s)
			var color: Color = mat.albedo_color if mat is BaseMaterial3D else Color.WHITE
			parts.append([root.get_path_to(node), input, color.srgb_to_linear()])
	for child in node.get_children():
		if child is Node3D: collect(root, child, parts)

func world_transforms(node: Node3D, tx: Transform3D, result: Dictionary) -> void:
	result[node] = tx
	for child in node.get_children():
		if child is Node3D: world_transforms(child, tx * child.transform, result)

func geometry(art: Dictionary, parts: Array, base: bool) -> Array:
	var positions := PackedVector3Array()
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	var transforms := {}
	world_transforms(art.root, Transform3D.IDENTITY, transforms)
	for piece in parts:
		var tx: Transform3D = transforms[art.root.get_node(piece[0])]
		var normal_matrix := tx.basis.inverse().transposed()
		var input: Array = piece[1]
		var offset := positions.size()
		var source: PackedVector3Array = input[Mesh.ARRAY_VERTEX]
		var directions: PackedVector3Array = input[Mesh.ARRAY_NORMAL]
		for i in source.size():
			positions.append(tx * source[i])
			normals.append((normal_matrix * directions[i]).normalized())
			if base: colors.append(piece[2])
		if base:
			var faces: PackedInt32Array = input[Mesh.ARRAY_INDEX]
			for i in faces: indices.append(i + offset)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = positions
	arrays[Mesh.ARRAY_NORMAL] = normals
	if base:
		arrays[Mesh.ARRAY_COLOR] = colors
		arrays[Mesh.ARRAY_INDEX] = indices
	return arrays

# Reduce the native geometry with Godot's built-in meshoptimizer LOD generator.
# Keep separate coloured seams and normals when compacting the far index buffer.
func distant(base: Array, key: String) -> MeshInstance3D:
	var importer := ImporterMesh.new()
	importer.add_surface(Mesh.PRIMITIVE_TRIANGLES, base)
	importer.generate_lods(25, 60, [])
	var topology: PackedInt32Array = base[Mesh.ARRAY_INDEX]
	for i in importer.get_surface_lod_count(0):
		var lod := importer.get_surface_lod_indices(0, i)
		if abs(lod.size() - 2600) < abs(topology.size() - 2600): topology = lod
	var geometry_source := importer.get_surface_arrays(0)
	var used := {}
	var positions := PackedVector3Array()
	var normals := PackedVector3Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	for ix in topology:
		if not used.has(ix):
			used[ix] = positions.size()
			positions.append(geometry_source[Mesh.ARRAY_VERTEX][ix])
			normals.append(geometry_source[Mesh.ARRAY_NORMAL][ix])
			colors.append(geometry_source[Mesh.ARRAY_COLOR][ix])
		indices.append(used[ix])
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = positions
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_INDEX] = indices
	var far_mesh := ArrayMesh.new()
	far_mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	far_mesh.surface_set_material(0, material)
	var far_node := MeshInstance3D.new()
	far_node.name = key + "_lod"
	far_node.mesh = far_mesh
	return far_node

func bake(library: Node3D, team: String, role: String) -> void:
	var art = Vehicles.build(team, role) if role in Vehicles.ROLES else Infantry.build(team, role)
	sample_pose(art, role, "idle")
	var parts := []
	collect(art.root, art.root, parts)
	var base := geometry(art, parts, true)
	var mesh := ArrayMesh.new()
	mesh.blend_shape_mode = Mesh.BLEND_SHAPE_MODE_NORMALIZED
	var morphs: Array[Array] = []
	for pose in POSES:
		mesh.add_blend_shape(pose)
		sample_pose(art, role, pose)
		morphs.append(geometry(art, parts, false))
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, base, morphs)
	mesh.surface_set_material(0, material)
	art.root.free()
	var instance := MeshInstance3D.new()
	instance.name = team + "_" + role
	instance.mesh = mesh
	library.add_child(instance)
	library.add_child(distant(base, instance.name))

# The Godot writer may leave alignment bytes between binary buffer views
# uninitialised. Canonicalise only these unreferenced bytes for repeatable builds.
func clear_alignment_bytes(path: String) -> void:
	var file := FileAccess.open(path, FileAccess.READ_WRITE)
	file.seek(12)
	var json_size := file.get_32()
	file.get_32()
	var document: Dictionary = JSON.parse_string(file.get_buffer(json_size).get_string_from_utf8())
	var base := 28 + json_size
	var cursor := 0
	var views: Array = document.bufferViews
	views.sort_custom(func(a, b): return a.get("byteOffset", 0) < b.get("byteOffset", 0))
	for v in views:
		var start := int(v.get("byteOffset",0))
		if start > cursor:
			file.seek(base + cursor)
			for _i in range(start - cursor): file.store_8(0)
		cursor = maxi(cursor, start + int(v.byteLength))
	file.seek(base + cursor)
	while file.get_position() < file.get_length(): file.store_8(0)
	file.close()

func export_library() -> void:
	var args := OS.get_cmdline_user_args()
	if args.size() != 1 or not args[0].is_absolute_path():
		push_error("Provide an absolute output GLB path after --")
		quit(1); return
	material.resource_name = "Native army palette"
	material.vertex_color_use_as_albedo = true
	material.roughness = 0.77
	material.metallic = 0.08
	var library := Node3D.new()
	library.name = "ConfluenceArmy"
	for team in ["sun", "moon"]:
		for role in Infantry.ROLES + Vehicles.ROLES:
			bake(library, team, role)
	var doc := GLTFDocument.new()
	var state := GLTFState.new()
	var code := doc.append_from_scene(library, state)
	if code == OK: code = doc.write_to_filesystem(state, args[0])
	library.free()
	if code == OK: clear_alignment_bytes(args[0])
	if code != OK: push_error("GLB export failed: " + str(code))
	quit(0 if code == OK else 1)
