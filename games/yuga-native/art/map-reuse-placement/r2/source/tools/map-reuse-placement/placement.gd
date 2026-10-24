extends RefCounted
## Reuses whole connected triangles from the existing CC0 courtyard GLB.
## Source mesh attributes and materials remain unchanged; only rigid placement.
const Intake=preload("res://tools/map-reuse-intake/map_loader.gd")
const SOURCE_SHA:="1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
const TRANSLATION:=Vector3(-40,0,-29.2)
const TRIANGLES:=17862
const COLLISION_TRIANGLES:=6706
const SURFACES:=11
static func build(path:String,selection:Dictionary)->Dictionary:
	if not FileAccess.file_exists(path) or FileAccess.get_sha256(path)!=SOURCE_SHA:return {"ok":false,"reason":"source_hash"}
	if not Intake.inspect(FileAccess.get_file_as_bytes(path)).ok:return {"ok":false,"reason":"source_container"}
	if selection.get("schema")!=1 or selection.get("source_sha256")!=SOURCE_SHA or selection.get("placement_translation")!=[-40.0,0.0,-29.2] or not selection.get("selected") is Array or selection.selected.size()!=SURFACES:return {"ok":false,"reason":"selection_contract","schema":selection.get("schema"),"sha":selection.get("source_sha256"),"translation":selection.get("placement_translation"),"count":selection.selected.size() if selection.get("selected") is Array else null,"expected_surfaces":SURFACES}
	var document:=GLTFDocument.new();var state:=GLTFState.new()
	if document.append_from_file(path,state)!=OK:return {"ok":false,"reason":"native_parse"}
	var imported:=document.generate_scene(state)
	if imported==null:return {"ok":false,"reason":"native_scene"}
	var node:=Node3D.new();node.name="LankaGateReuseCandidate";node.set_meta("review_only",true)
	var collision_faces:=PackedVector3Array();var report_surfaces:Array=[];var seen:Array=[];var count:=0;var vertices:=0
	for row in selection.selected:
		if not row is Dictionary or not row.get("node") is String or not row.get("source_triangle_ids") is Array or row.get("surface")!=0 or row.node in seen:
			imported.free();node.free();return {"ok":false,"reason":"selection_row"}
		seen.append(row.node)
		var matches:=imported.find_children(row.node,"MeshInstance3D",true,false)
		if matches.size()!=1:imported.free();node.free();return {"ok":false,"reason":"unique_source_node"}
		var source:MeshInstance3D=matches[0]
		if source.transform!=Transform3D.IDENTITY or source.mesh.get_surface_count()!=1:imported.free();node.free();return {"ok":false,"reason":"source_transform"}
		var arrays:Array=source.mesh.surface_get_arrays(0);var src:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var ids:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
		var dest:Array=[];dest.resize(Mesh.ARRAY_MAX)
		var pos:=PackedVector3Array();var normals:=PackedVector3Array();var uv:=PackedVector2Array();var tangents:=PackedFloat32Array();var indices:=PackedInt32Array();var remap:Dictionary={};var selected_ids:Array=[];var last:=-1
		for raw_id in row.source_triangle_ids:
			if not (raw_id is int or raw_id is float) or not is_finite(raw_id) or raw_id!=floor(raw_id) or raw_id<=last or raw_id<0 or raw_id*3+2>=ids.size():imported.free();node.free();return {"ok":false,"reason":"ordered_unique_source_triangles"}
			var ti:=int(raw_id);last=ti;selected_ids.append(ti)
			for corner in 3:
				var si:int=ids[ti*3+corner];var point:Vector3=src[si]
				if not point.is_finite() or point.x< -13.201 or point.x>13.201 or point.y<-.051 or point.y>17.001 or point.z< -30.001 or point.z> -18.799:imported.free();node.free();return {"ok":false,"reason":"source_region"}
				if not remap.has(si):
					remap[si]=pos.size();pos.append(point);normals.append(arrays[Mesh.ARRAY_NORMAL][si]);uv.append(arrays[Mesh.ARRAY_TEX_UV][si])
					for k in 4:tangents.append(arrays[Mesh.ARRAY_TANGENT][si*4+k])
				indices.append(remap[si])
				if row.node.begins_with("COL_"):collision_faces.append(point+TRANSLATION)
		if bool(row.get("collision",false))!=row.node.begins_with("COL_"):imported.free();node.free();return {"ok":false,"reason":"collision_scope"}
		dest[Mesh.ARRAY_VERTEX]=pos;dest[Mesh.ARRAY_NORMAL]=normals;dest[Mesh.ARRAY_TEX_UV]=uv;dest[Mesh.ARRAY_TANGENT]=tangents;dest[Mesh.ARRAY_INDEX]=indices
		var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,dest);mesh.surface_set_material(0,source.mesh.surface_get_material(0))
		var visual:=MeshInstance3D.new();visual.name=row.node;visual.mesh=mesh;visual.position=TRANSLATION;node.add_child(visual)
		count+=selected_ids.size();vertices+=pos.size()
		report_surfaces.append({"node":row.node,"triangles":selected_ids.size(),"vertices":pos.size(),"material":str(mesh.surface_get_material(0).resource_name),"source_triangle_ids_sha256":var_to_bytes(selected_ids).hex_encode().sha256_text(),"collision":row.node.begins_with("COL_")})
	imported.free()
	if count!=TRIANGLES or collision_faces.size()!=COLLISION_TRIANGLES*3:node.free();return {"ok":false,"reason":"exact_triangle_budget"}
	var body:=StaticBody3D.new();body.name="SourceTriangleCollision";body.collision_layer=1;body.collision_mask=0
	var shape:=ConcavePolygonShape3D.new();shape.backface_collision=true;shape.set_faces(collision_faces)
	var holder:=CollisionShape3D.new();holder.shape=shape;body.add_child(holder);node.add_child(body)
	return {"ok":true,"root":node,"body":body,"shape":shape,"faces":collision_faces,"report":{"source_sha256":SOURCE_SHA,"triangles":count,"collision_triangles":COLLISION_TRIANGLES,"surfaces":SURFACES,"compacted_vertices":vertices,"instances":SURFACES,"collision_bodies":1,"collision_shapes":1,"translation":[TRANSLATION.x,TRANSLATION.y,TRANSLATION.z],"surfaces_detail":report_surfaces,"units":"metres +Y up; rigid translation; preserved source UV/normals/tangents/material resources","geometry_generated":false,"canonical_enabled":false}}
