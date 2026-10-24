extends RefCounted
## Original closed four-face civic frontage using the existing world material kit.
## Matching closed local3D collision detail; planar authority bounds remain unchanged.
const TARGET := "CityArt/block-2"
const BODY := "authority-solid-2"
const ROOT := "ReviewBlock2Frontage"
const DATA := "res://assets/world/block2-frontage.json"
const DIMENSIONS := Vector3(18,15,18)
const MATERIAL_NAMES := ["Confluence_warm_ivory","Confluence_opaque_blue_glass","Confluence_transit_indigo"]
const TRIANGLE_LIMIT := 4944

static func configure(world: Node3D, lod: String = "near") -> Dictionary:
	if not is_instance_valid(world) or world.get_node_or_null(ROOT): return {"ok":false,"reason":"invalid_or_already_present"}
	var old := world.get_node_or_null(TARGET) as Node3D
	var body := world.get_node_or_null(BODY) as StaticBody3D
	if old==null or body==null or not old.visible or not old.scale.is_equal_approx(DIMENSIONS): return {"ok":false,"reason":"target_contract"}
	var holder: CollisionShape3D
	for child in body.get_children():
		if child is CollisionShape3D and child.shape is BoxShape3D: holder=child
	if holder==null or holder.disabled or not holder.shape.size.is_equal_approx(DIMENSIONS): return {"ok":false,"reason":"old_box_contract"}
	var owners:=body.get_shape_owners()
	if owners.size()!=1 or body.shape_owner_get_owner(owners[0])!=holder or body.shape_owner_get_shape_count(owners[0])!=1: return {"ok":false,"reason":"ambiguous_shape_ownership"}
	if body.get_meta("authority_id","")!=BODY or not old.position.is_equal_approx(Vector3(20,0,-28)) or not body.position.is_equal_approx(old.position+Vector3.UP*7.5) or body.basis!=Basis.IDENTITY or holder.transform!=Transform3D.IDENTITY: return {"ok":false,"reason":"authority_transform_contract"}
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	if not data.get("geometry",{}).has(lod): return {"ok":false,"reason":"unknown_lod"}
	var materials: Array[Material] = []
	var meshes := old.find_children("*","MeshInstance3D",true,false)
	if old is MeshInstance3D: meshes.push_front(old)
	for name in MATERIAL_NAMES:
		var material: Material
		for node in meshes:
			if node.mesh==null: continue
			for index in node.mesh.get_surface_count():
				var imported: Material = node.mesh.surface_get_material(index)
				if imported!=null and imported.resource_name==name: material=node.get_active_material(index)
		if material==null: return {"ok":false,"reason":"missing_existing_material","name":name}
		materials.append(material)
	var geometry: Dictionary = data.geometry[lod]
	if geometry.triangle_count>TRIANGLE_LIMIT or geometry.surfaces.size()!=3: return {"ok":false,"reason":"budget"}
	var combined := ArrayMesh.new()
	var faces := PackedVector3Array()
	for index in geometry.surfaces.size():
		if geometry.surfaces[index].material!=MATERIAL_NAMES[index]: return {"ok":false,"reason":"material_slot"}
		var tool := SurfaceTool.new()
		tool.begin(Mesh.PRIMITIVE_TRIANGLES)
		for triangle in geometry.surfaces[index].triangles:
			var a:=_v(triangle[0]);var b:=_v(triangle[1]);var c:=_v(triangle[2])
			var normal:=(b-a).cross(c-a).normalized()
			if not normal.is_finite() or normal.is_zero_approx(): return {"ok":false,"reason":"degenerate_geometry"}
			for point in [a,b,c]:
				if not point.is_finite() or point.x< -9 or point.x>9 or point.y<0 or point.y>15 or point.z< -9 or point.z>9: return {"ok":false,"reason":"envelope"}
				tool.set_normal(normal)
				tool.set_uv(Vector2(point.x,point.y)*.25 if absf(normal.z)>.5 else Vector2(point.z,point.y)*.25 if absf(normal.x)>.5 else Vector2(point.x,point.z)*.25)
				tool.add_vertex(point)
				# Body origin is base+Y7.5; exact same triangles in its local space.
				faces.append(body.to_local(old.global_position+old.global_basis.orthonormalized()*point))
		tool.generate_tangents()
		tool.set_material(materials[index])
		tool.commit(combined)
	var root := Node3D.new();root.name=ROOT
	root.set_meta("review_only",true);root.set_meta("old_shape",holder.shape);root.set_meta("old_visible",old.visible)
	root.set_meta("old_holder",weakref(holder));root.set_meta("old_mesh",weakref(old))
	world.add_child(root)
	root.global_transform=Transform3D(old.global_basis.orthonormalized(),old.global_position)
	var instance := MeshInstance3D.new();instance.name="ClosedCivicFrontage";instance.mesh=combined;root.add_child(instance)
	var replacement := ConcavePolygonShape3D.new();replacement.backface_collision=true;replacement.set_faces(faces)
	# Publish only after complete mesh/material/shape construction; keep body identity.
	root.set_meta("published_shape",replacement)
	root.tree_exiting.connect(_restore_on_exit.bind(weakref(root)),CONNECT_ONE_SHOT)
	holder.shape=replacement
	old.hide()
	return {"ok":true,"root":root,"mesh":instance,"body":body,"shape":replacement,"old_shape":root.get_meta("old_shape"),"triangles":faces.size()/3,"materials":materials,"new_materials":0,"new_textures":0,"new_lights":0,"surface_draws_max_per_pass":3,"automatic_lod":false,"lod":lod,"detailed_3d_collision_delta":true,"planar_authority_metadata_changed":false,"scope":"Closed frontage only; no new interior route or runtime quality acceptance."}

static func remove(world: Node3D) -> void:
	var root:=world.get_node_or_null(ROOT)
	if root==null or not root.get_meta("review_only",false): return
	_restore_on_exit(weakref(root))
	world.remove_child(root);root.free()

static func _restore_on_exit(reference: WeakRef) -> void:
	var root: Node=reference.get_ref()
	if not is_instance_valid(root): return
	var holder: CollisionShape3D=root.get_meta("old_holder").get_ref()
	var old: Node3D=root.get_meta("old_mesh").get_ref()
	if is_instance_valid(holder) and holder.shape==root.get_meta("published_shape"): holder.shape=root.get_meta("old_shape")
	if is_instance_valid(old): old.visible=root.get_meta("old_visible")

static func _v(value: Array) -> Vector3:
	return Vector3(value[0],value[1],value[2])
