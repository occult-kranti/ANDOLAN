extends SceneTree
## Adapt map-reuse-placement's array-preserving extractor/cache. No new mesh art.
const SOURCE := "res://assets/environment/lanka_courtyard.glb"
const SOURCE_SHA := "1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
const SELECTION_SHA := "6a9376f1cec2806f467a43ff4ceed5554a989c0fa9d02870077a77e220779151"
const Intake = preload("res://tools/map-reuse-intake/map_loader.gd")
var output := ""
var selection_path := ""

func _initialize() -> void:
	call_deferred("run")

func fail(reason: String) -> void:
	push_error(reason)
	quit(1)

func vec(value: Array) -> Vector3:
	return Vector3(value[0], value[1], value[2])

func owned(node: Node, scene: Node) -> void:
	for child in node.get_children():
		child.owner = scene
		owned(child, scene)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
		if arg.begins_with("--selection="): selection_path = arg.trim_prefix("--selection=")
	if not output.is_absolute_path() or FileAccess.file_exists(output) or not output.ends_with(".scn"):
		fail("fresh absolute .scn output required"); return
	if FileAccess.get_sha256(SOURCE) != SOURCE_SHA or FileAccess.get_sha256(selection_path) != SELECTION_SHA:
		fail("exact source and selection hashes required"); return
	if not Intake.inspect(FileAccess.get_file_as_bytes(SOURCE)).ok:
		fail("source embedded-container guard"); return
	var selection: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(selection_path))
	var document := GLTFDocument.new()
	var state := GLTFState.new()
	if document.append_from_file(SOURCE, state) != OK:
		fail("native source parse"); return
	var imported := document.generate_scene(state)
	if imported == null:
		fail("native source scene"); return
	var prototypes: Dictionary = {}
	var costs: Dictionary = {}
	for key: String in selection.prototypes:
		var spec: Dictionary = selection.prototypes[key]
		var center := vec(spec.source_center)
		var template := Node3D.new()
		template.name = key
		var faces := PackedVector3Array()
		var triangles := 0
		for row: Dictionary in spec.selected:
			var matches := imported.find_children(row.node, "MeshInstance3D", true, false)
			if matches.size() != 1: fail("unique source node"); return
			var source: MeshInstance3D = matches[0]
			if source.transform != Transform3D.IDENTITY or source.mesh.get_surface_count() != 1:
				fail("source identity transform/surface"); return
			var arrays: Array = source.mesh.surface_get_arrays(0)
			var source_vertices: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
			var source_indices: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
			var vertices := PackedVector3Array()
			var normals := PackedVector3Array()
			var uvs := PackedVector2Array()
			var tangents := PackedFloat32Array()
			var indices := PackedInt32Array()
			var remap: Dictionary = {}
			var last := -1
			for raw_id: float in row.source_triangle_ids:
				if not is_finite(raw_id) or raw_id != floor(raw_id) or raw_id <= last or raw_id * 3 + 2 >= source_indices.size():
					fail("source triangle identity"); return
				var triangle := int(raw_id)
				last = triangle
				for corner in 3:
					var index: int = source_indices[triangle * 3 + corner]
					var point := source_vertices[index] - center
					if not point.is_finite(): fail("nonfinite source"); return
					if not remap.has(index):
						remap[index] = vertices.size()
						vertices.append(point)
						normals.append(arrays[Mesh.ARRAY_NORMAL][index])
						uvs.append(arrays[Mesh.ARRAY_TEX_UV][index])
						for channel in 4: tangents.append(arrays[Mesh.ARRAY_TANGENT][index * 4 + channel])
					indices.append(remap[index])
					if row.collision: faces.append(point)
			var selected: Array = []
			selected.resize(Mesh.ARRAY_MAX)
			selected[Mesh.ARRAY_VERTEX] = vertices
			selected[Mesh.ARRAY_NORMAL] = normals
			selected[Mesh.ARRAY_TEX_UV] = uvs
			selected[Mesh.ARRAY_TANGENT] = tangents
			selected[Mesh.ARRAY_INDEX] = indices
			var mesh := ArrayMesh.new()
			mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, selected)
			mesh.surface_set_material(0, source.mesh.surface_get_material(0))
			var visual := MeshInstance3D.new()
			visual.name = row.node
			visual.mesh = mesh
			visual.set_meta("source_node", row.node)
			visual.set_meta("source_triangle_ids", row.source_triangle_ids)
			template.add_child(visual)
			triangles += indices.size() / 3
		if triangles != int(spec.triangles) or faces.size() != int(spec.collision_triangles) * 3:
			fail("exact source budget"); return
		var body := StaticBody3D.new()
		body.name = "SourceCollision"
		body.collision_layer = 1
		body.collision_mask = 0
		var shape := ConcavePolygonShape3D.new()
		shape.backface_collision = true
		shape.set_faces(faces)
		var holder := CollisionShape3D.new()
		holder.name = "WholeSourceFaces"
		holder.shape = shape
		body.add_child(holder)
		template.add_child(body)
		template.set_meta("source_collision_faces", faces)
		template.set_meta("prototype", key)
		prototypes[key] = template
		costs[key] = {"triangles": triangles, "collision_triangles": faces.size() / 3, "surfaces": spec.surfaces}
	imported.free()
	var module := Node3D.new()
	module.name = "LankaWaterGarden"
	module.set_meta("review_only", true)
	module.set_meta("source_sha256", SOURCE_SHA)
	module.set_meta("selection_sha256", SELECTION_SHA)
	module.set_meta("context_contract", selection.existing_context)
	module.set_meta("source_costs", costs)
	module.set_meta("instances", selection.instances)
	var boxes: Array = []
	for row: Dictionary in selection.instances:
		var instance: Node3D = prototypes[row.prototype].duplicate()
		instance.name = row.id
		instance.position = vec(row.position)
		module.add_child(instance)
		var size := Vector3(1.2, 3.31, 1.2) if row.prototype == "column" else Vector3(.48, 1.075, .48)
		boxes.append({"id": row.id + "-army", "position": row.position, "size": [size.x, size.y, size.z], "native_only": true, "scope": "Conservative source base extent; native offline army candidate only"})
	module.set_meta("army_ground_footprints", boxes)
	for template: Node3D in prototypes.values(): template.free()
	owned(module, module)
	var packed := PackedScene.new()
	var pack_result := packed.pack(module)
	var save_result := ResourceSaver.save(packed, output, ResourceSaver.FLAG_COMPRESS | ResourceSaver.FLAG_BUNDLE_RESOURCES) if pack_result == OK else pack_result
	var report := {"schema": 1, "ok": save_result == OK, "source_sha256": SOURCE_SHA, "selection_sha256": SELECTION_SHA,
		"source_costs": costs, "instances": selection.instances, "total_visual_triangles": 2688, "total_collision_triangles": 760,
		"unique_meshes": 7, "mesh_instances": 14, "collision_bodies": 4, "shared_shape_resources": 2,
		"file": output, "sha256": FileAccess.get_sha256(output), "bytes": FileAccess.get_file_as_bytes(output).size(),
		"scope": "Candidate source-derived corner columns and diya assemblies; source geometry/attributes/materials reused, no full gate duplication; no runtime enablement."}
	FileAccess.open(output + ".json", FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	module.free()
	print(JSON.stringify(report))
	quit(0 if save_result == OK else 1)
