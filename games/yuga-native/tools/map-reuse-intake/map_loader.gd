extends RefCounted
## Adapts the existing reuse-vfx-stage/source_loader.gd GLTFDocument path.
## Adds a pinned embedded-only contract, one named CC0 element and truthful static collision.
const EXPECTED_SOURCE := "1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
const ELEMENT := "COL_BEVEL_Warm_carved_sandstone"
const MAX_BYTES := 33554432
const MAX_TRIANGLES := 5000

static func inspect(bytes:PackedByteArray)->Dictionary:
	if bytes.size()<28 or bytes.size()>MAX_BYTES:return {"ok":false,"reason":"bounded_complete_glb"}
	if bytes.decode_u32(0)!=0x46546c67 or bytes.decode_u32(4)!=2 or bytes.decode_u32(8)!=bytes.size():return {"ok":false,"reason":"bounded_complete_glb"}
	var json_bytes:=bytes.decode_u32(12)
	if json_bytes>4194304 or json_bytes%4 or 28+json_bytes>bytes.size() or bytes.decode_u32(16)!=0x4e4f534a:return {"ok":false,"reason":"json_chunk"}
	if bytes.decode_u32(24+json_bytes)!=0x004e4942 or bytes.decode_u32(20+json_bytes)!=bytes.size()-28-json_bytes:return {"ok":false,"reason":"single_embedded_bin"}
	var document:Variant=JSON.parse_string(bytes.slice(20,20+json_bytes).get_string_from_utf8())
	if not document is Dictionary or not document.get("asset") is Dictionary:return {"ok":false,"reason":"gltf_version"}
	if document.asset.get("version","")!="2.0":return {"ok":false,"reason":"gltf_version"}
	for field in ["skins","animations","extensionsUsed","extensionsRequired"]:
		if not document.get(field,[]) is Array:return {"ok":false,"reason":"array_contract"}
	for field in ["buffers","images"]:
		if not document.get(field,[]) is Array:return {"ok":false,"reason":"array_contract"}
		for entry in document.get(field,[]):
			if not entry is Dictionary or entry.has("uri"):return {"ok":false,"reason":"external_resources"}
	if document.get("buffers",[]).size()!=1:return {"ok":false,"reason":"single_embedded_buffer"}
	var binary_length:Variant=document.buffers[0].get("byteLength")
	if not (binary_length is int or binary_length is float) or not is_finite(binary_length) or binary_length!=floor(binary_length) or binary_length<=0 or binary_length>bytes.size()-28-json_bytes or bytes.size()-28-json_bytes-binary_length>3:return {"ok":false,"reason":"embedded_buffer_length"}
	if not document.get("skins",[]).is_empty() or not document.get("animations",[]).is_empty():return {"ok":false,"reason":"static_only"}
	for field in ["extensionsUsed","extensionsRequired"]:
		var seen:=[]
		for extension in document.get(field,[]):
			if not extension is String or extension!="KHR_materials_emissive_strength" or extension in seen:return {"ok":false,"reason":"unsupported_extension"}
			if field=="extensionsRequired" and extension not in document.get("extensionsUsed",[]):return {"ok":false,"reason":"undeclared_extension"}
			seen.append(extension)
	return {"ok":true,"document":document}

static func load_element(path:String,expected_sha:String=EXPECTED_SOURCE,selector:String=ELEMENT,placement:Transform3D=Transform3D.IDENTITY)->Dictionary:
	# Only one existing licensed structural element is accepted in this prototype.
	if selector!=ELEMENT:return {"ok":false,"reason":"unapproved_element"}
	if not placement.origin.is_finite() or not placement.basis.is_finite() or not placement.basis.is_equal_approx(placement.basis.orthonormalized()) or absf(placement.basis.determinant()-1.0)>.00001:return {"ok":false,"reason":"rigid_metre_placement_required"}
	if not FileAccess.file_exists(path):return {"ok":false,"reason":"missing_source"}
	var file:=FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()>MAX_BYTES:return {"ok":false,"reason":"source_budget"}
	var bytes:=file.get_buffer(file.get_length())
	file.close()
	if expected_sha!=EXPECTED_SOURCE or FileAccess.get_sha256(path)!=expected_sha:return {"ok":false,"reason":"source_hash"}
	var intake:=inspect(bytes)
	if not intake.ok:return intake
	# Same built-in MIT-licensed Godot loader already used by the isolated VFX stage.
	var document:=GLTFDocument.new()
	var state:=GLTFState.new()
	if document.append_from_file(path,state)!=OK:return {"ok":false,"reason":"native_gltf_parse"}
	var imported:=document.generate_scene(state)
	if imported==null:return {"ok":false,"reason":"native_gltf_scene"}
	var matches:=imported.find_children(selector,"MeshInstance3D",true,false)
	if matches.size()!=1:
		imported.free()
		return {"ok":false,"reason":"unique_element_required"}
	var source:=matches[0] as MeshInstance3D
	var local_faces:=source.mesh.get_faces()
	if local_faces.is_empty() or local_faces.size()%3 or local_faces.size()/3>MAX_TRIANGLES:
		imported.free()
		return {"ok":false,"reason":"triangle_budget"}
	var local_transform:=source.transform
	var ancestor:=source.get_parent()
	while ancestor!=null and ancestor!=imported:
		if ancestor is Node3D:local_transform=ancestor.transform*local_transform
		ancestor=ancestor.get_parent()
	if imported is Node3D:local_transform=imported.transform*local_transform
	var source_faces:=PackedVector3Array()
	var final_faces:=PackedVector3Array()
	for face in local_faces:
		var point:Vector3=local_transform*face
		if not point.is_finite():
			imported.free()
			return {"ok":false,"reason":"nonfinite_geometry"}
		source_faces.append(point)
		final_faces.append(placement*point)
	var source_mesh:=source.mesh
	var source_materials:=[]
	for index in source_mesh.get_surface_count():source_materials.append(source_mesh.surface_get_material(index))
	var root:=Node3D.new()
	root.name="ReusedCourtyardElement"
	root.set_meta("review_only",true)
	var visual:=MeshInstance3D.new()
	visual.name=selector
	visual.mesh=source_mesh
	visual.transform=placement*local_transform
	root.add_child(visual)
	var body:=StaticBody3D.new()
	body.name="SourceTriangleCollision"
	body.collision_layer=1
	body.collision_mask=0
	var shape:=ConcavePolygonShape3D.new()
	shape.backface_collision=true
	shape.set_faces(final_faces)
	var holder:=CollisionShape3D.new()
	holder.shape=shape
	body.add_child(holder)
	root.add_child(body)
	imported.free()
	return {"ok":true,"root":root,"visual":visual,"body":body,"shape":shape,"source_faces":source_faces,"faces":final_faces,"materials":source_materials,"triangles":final_faces.size()/3,"placement":placement,"source_sha256":expected_sha,"units":"metres; native GLB Y-up; no axis conversion or unit rescale","runtime_promoted":false}
