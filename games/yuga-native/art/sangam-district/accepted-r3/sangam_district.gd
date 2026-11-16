extends RefCounted
## Original authored district installed into the actual offline Confluence world.
## Ground cover is shared with the local army; overhead collision stays 3D-only.
const ASSET := "res://assets/world/sangam-district.glb"
const SPEC := "res://assets/world/sangam-district.json"
const SOURCE_MAP := "res://assets/world/confluence-map.json"
const ROOT_NAME := "SangamDistrict"

static func _vector(value: Array) -> Vector3:
	return Vector3(float(value[0]), float(value[1]), float(value[2]))

static func build(world: Node3D) -> Dictionary:
	if not is_instance_valid(world) or not world.is_inside_tree() or world.global_transform != Transform3D.IDENTITY or world.has_node(ROOT_NAME): return {"ok":false,"reason":"invalid_or_duplicate_world"}
	if not FileAccess.file_exists(SPEC) or not ResourceLoader.exists(ASSET): return {"ok":false,"reason":"authored_asset_missing"}
	var specification = JSON.parse_string(FileAccess.get_file_as_string(SPEC))
	if not specification is Dictionary or specification.get("schema_version") != 1 or specification.get("modules", []).size() != 8 or specification.get("ground_footprints", []).size() != 4:
		return {"ok":false,"reason":"asset_contract"}
	if FileAccess.get_sha256(SOURCE_MAP) != specification.get("source_map_sha256", ""): return {"ok":false,"reason":"source_map_hash"}
	var ground_contract := _validated_ground(specification.ground_footprints)
	if not ground_contract.ok: return ground_contract
	# A source checkout can hash raw GLB; exported PCKs may remap it to a scene.
	if FileAccess.file_exists(ASSET) and FileAccess.get_sha256(ASSET) != specification.get("asset_sha256", ""):
		return {"ok":false,"reason":"asset_hash"}
	var resource = load(ASSET)
	if not resource is PackedScene: return {"ok":false,"reason":"packed_scene_required"}
	var root := resource.instantiate() as Node3D
	if root == null: return {"ok":false,"reason":"scene_required"}
	root.name = ROOT_NAME
	var restored_nodes: Array = []
	var restored_shapes: Array = []
	var restored_layers: Array = []
	# Preserve old sources and node identity. The eight full solids remain the
	# declared gameplay footprints; the old one-off inset frontage is superseded.
	for module in specification.modules:
		var id := String(module.id)
		var old := world.get_node_or_null("CityArt/" + id) as Node3D
		var body := world.get_node_or_null("authority-solid-" + id.trim_prefix("block-")) as StaticBody3D
		var dimensions := _vector(module.inherited_ground_size)
		var holder: CollisionShape3D
		if body:
			for child in body.get_children():
				if child is CollisionShape3D:
					holder = child
					break
		if old == null or body == null or holder == null or not old.scale.is_equal_approx(dimensions) or not body.position.is_equal_approx(_vector(module.position) + Vector3.UP * dimensions.y * .5):
			root.free()
			return {"ok":false,"reason":"inherited_ground_contract","module":id}
		var replacement := BoxShape3D.new()
		replacement.size = dimensions
		restored_shapes.append({"holder":weakref(holder),"shape":holder.shape,"transform":holder.transform,"replacement":replacement})
	var triangle_count := 0
	var surface_count := 0
	var overhead_triangles := 0
	var materials := {}
	var overhead_bodies := 0
	var meshes := root.find_children("*", "MeshInstance3D", true, false)
	for visual: MeshInstance3D in meshes:
		if visual.mesh == null:
			root.free()
			return {"ok":false,"reason":"mesh_missing"}
		var faces := visual.mesh.get_faces()
		triangle_count += faces.size() / 3
		surface_count += visual.mesh.get_surface_count()
		for index in visual.mesh.get_surface_count():
			var material := visual.mesh.surface_get_material(index)
			if material: materials[material.get_instance_id()] = true
		if String(visual.name).begins_with("SOLID_Overhead_") or String(visual.name).begins_with("SOLID_AvenueGallery_"):
			var body := StaticBody3D.new()
			body.name = "ExactOverheadCollision"
			body.collision_layer = 1
			body.collision_mask = 0
			body.set_meta("native_only", true)
			var shape := ConcavePolygonShape3D.new()
			shape.backface_collision = true
			shape.set_faces(faces)
			var holder := CollisionShape3D.new()
			holder.shape = shape
			body.add_child(holder)
			visual.add_child(body)
			overhead_bodies += 1
			overhead_triangles += faces.size() / 3
	if meshes.size() != int(specification.mesh_objects) or triangle_count != int(specification.triangles) or overhead_bodies != 10 or materials.size() > 8:
		root.free()
		return {"ok":false,"reason":"imported_budget","meshes":meshes.size(),"triangles":triangle_count,"overhead_bodies":overhead_bodies,"materials":materials.size()}
	for cover in specification.ground_footprints:
		var dimensions := _vector(cover.size)
		if not dimensions.is_equal_approx(Vector3(3, 2.7, 6)):
			root.free()
			return {"ok":false,"reason":"ground_cover_dimensions"}
		var body := StaticBody3D.new()
		body.name = String(cover.id)
		body.position = _vector(cover.position) + Vector3.UP * dimensions.y * .5
		body.collision_layer = 1
		body.collision_mask = 0
		body.set_meta("native_only", true)
		var shape := BoxShape3D.new()
		shape.size = dimensions
		var holder := CollisionShape3D.new()
		holder.shape = shape
		body.add_child(holder)
		root.add_child(body)
	# Publish only once complete imported geometry/collision has passed its bounds.
	for path in specification.hide_original_nodes:
		var original := world.get_node_or_null(path) as Node3D
		if original:
			restored_nodes.append({"node":weakref(original),"visible":original.visible})
			original.hide()
			for collision in original.find_children("*", "CollisionObject3D", true, false):
				restored_layers.append({"node":weakref(collision),"layer":collision.collision_layer,"mask":collision.collision_mask})
				collision.collision_layer = 0
				collision.collision_mask = 0
	for saved in restored_shapes:
		var holder: CollisionShape3D = saved.holder.get_ref()
		holder.shape = saved.replacement
		holder.transform = Transform3D.IDENTITY
	root.set_meta("original_nodes", restored_nodes)
	root.set_meta("original_shapes", restored_shapes)
	root.set_meta("original_layers", restored_layers)
	root.set_meta("ground_footprints", specification.ground_footprints.duplicate(true))
	root.tree_exiting.connect(_restore.bind(weakref(root)), CONNECT_ONE_SHOT)
	world.add_child(root)
	return {"ok":true,"root":root,"report":{"enabled":true,"id":specification.id,"asset_sha256":specification.asset_sha256,"specification_sha256":FileAccess.get_sha256(SPEC),"triangles":triangle_count,"mesh_instances":meshes.size(),"surfaces":surface_count,"material_resources":materials.size(),"new_lights":0,"overhead_bodies":overhead_bodies,"overhead_triangles":overhead_triangles,"ground_cover_bodies":4,"ground_footprints":specification.ground_footprints.duplicate(true),"replaced_buildings":8,"native_only":true,"scope":"Authored full district with exact overhead collision and four planar ground covers; unchanged original eight footprints and lanes. No online, elevated combat, hardware or full quality acceptance."}}

static func prepare_army_manifest(original: Dictionary, district: Node3D) -> Dictionary:
	if not is_instance_valid(district) or not district.is_inside_tree() or district.global_transform != Transform3D.IDENTITY or not district.has_meta("ground_footprints"): return {"ok":false,"reason":"district_required"}
	if not original.get("traversal") is Dictionary or not original.traversal.get("native_collision_boxes", []) is Array:
		return {"ok":false,"reason":"army_manifest_contract"}
	var boxes: Array = district.get_meta("ground_footprints")
	var ground_contract := _validated_ground(boxes)
	if not ground_contract.ok: return ground_contract
	for box in original.traversal.get("native_collision_boxes", []):
		if not box is Dictionary: return {"ok":false,"reason":"army_manifest_contract"}
		if String(box.get("id", "")).begins_with("sangam-cover-"): return {"ok":false,"reason":"duplicate_ground_cover"}
	var copy := original.duplicate(true)
	# The army is planar and ignores Y: NEVER append the overhead geometry here.
	for box in boxes:
		copy.traversal.native_collision_boxes.append({"id":box.id,"position":box.position.duplicate(),"size":box.size.duplicate(),"anchor":"base_center","native_only":true})
	return {"ok":true,"manifest":copy,"added_ground_footprints":4,"overhead_added":0}

static func _validated_ground(value: Variant) -> Dictionary:
	if not value is Array or value.size() != 4: return {"ok":false,"reason":"ground_footprint_count"}
	var expected := {"sangam-cover-West_South":Vector3(-8,0,-60),"sangam-cover-West_North":Vector3(-8,0,60),"sangam-cover-East_South":Vector3(8,0,-60),"sangam-cover-East_North":Vector3(8,0,60)}
	var seen := {}
	for box in value:
		if not box is Dictionary or not expected.has(box.get("id", "")) or seen.has(box.get("id", "")): return {"ok":false,"reason":"ground_footprint_identity"}
		for key in ["position", "size"]:
			if not box.get(key) is Array or box[key].size() != 3: return {"ok":false,"reason":"ground_footprint_vector"}
			for component in box[key]:
				if not (component is float or component is int) or not is_finite(float(component)): return {"ok":false,"reason":"ground_footprint_finite"}
		if not _vector(box.position).is_equal_approx(expected[box.id]) or not _vector(box.size).is_equal_approx(Vector3(3,2.7,6)): return {"ok":false,"reason":"ground_footprint_geometry"}
		seen[box.id] = true
	return {"ok":true}

static func remove(world: Node3D) -> void:
	var root := world.get_node_or_null(ROOT_NAME)
	if root == null: return
	_restore(weakref(root))
	world.remove_child(root)
	root.free()

static func _restore(reference: WeakRef) -> void:
	var root: Node = reference.get_ref()
	if not is_instance_valid(root): return
	for saved in root.get_meta("original_shapes", []):
		var holder: CollisionShape3D = saved.holder.get_ref()
		if is_instance_valid(holder) and holder.shape == saved.replacement:
			holder.shape = saved.shape
			holder.transform = saved.transform
	for saved in root.get_meta("original_nodes", []):
		var node: Node3D = saved.node.get_ref()
		if is_instance_valid(node): node.visible = saved.visible
	for saved in root.get_meta("original_layers", []):
		var node: CollisionObject3D = saved.node.get_ref()
		if is_instance_valid(node):
			node.collision_layer = saved.layer
			node.collision_mask = saved.mask
