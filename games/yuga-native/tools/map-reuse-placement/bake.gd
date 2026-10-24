extends SceneTree
## Export selected existing pieces once, so gameplay need not parse whole courtyard.
const Placement=preload("res://tools/map-reuse-placement/placement.gd")
func _initialize()->void:call_deferred("run")
func stamp(node:Node3D)->Dictionary:
	var count:=0;var vertices:=0;var surfaces:=0;var materials:Dictionary={};var textures:Dictionary={}
	for child in node.get_children():
		if not child is MeshInstance3D:continue
		for i in child.mesh.get_surface_count():
			var arrays:Array=child.mesh.surface_get_arrays(i);vertices+=arrays[Mesh.ARRAY_VERTEX].size();count+=arrays[Mesh.ARRAY_INDEX].size()/3;surfaces+=1
			var mat:StandardMaterial3D=child.mesh.surface_get_material(i)
			if mat==null:continue
			materials[mat.get_instance_id()]=true
			for texture in [mat.albedo_texture,mat.normal_texture,mat.roughness_texture]:
				if texture!=null:textures[texture.get_instance_id()]={"width":texture.get_width(),"height":texture.get_height()}
	return {"triangles":count,"vertices":vertices,"surfaces":surfaces,"unique_materials":materials.size(),"unique_texture_resources":textures.values()}
func army_footprints(selection:Dictionary)->Array:
	var pieces:Array=[]
	for row in selection.selected:
		if not row.collision:continue
		for part in row.components:
			if part.min[1]<=2.4 and part.max[1]>=-.001:pieces.append({"node":row.node,"first_source_triangle":part.first_source_triangle,"min":part.min,"max":part.max})
	var boxes:Array=[]
	for i in pieces.size():
		var c:Dictionary=pieces[i];var contained:=false
		for j in pieces.size():
			if i==j:continue
			var p:Dictionary=pieces[j];var inside:=true;var strict:=false
			for axis in [0,2]:
				inside=inside and c.min[axis]>=p.min[axis]-.00001 and c.max[axis]<=p.max[axis]+.00001
				strict=strict or c.min[axis]>p.min[axis]+.00001 or c.max[axis]<p.max[axis]-.00001
			if inside and (strict or j<i):contained=true;break
		if contained:continue
		var low:=Vector3(c.min[0],0,c.min[2])+Placement.TRANSLATION;var high:=Vector3(c.max[0],0,c.max[2])+Placement.TRANSLATION;var middle:Vector3=(low+high)*.5
		boxes.append({"id":"lanka-gate-ground-%02d-army"%boxes.size(),"position":[middle.x,0.0,middle.z],"size":[high.x-low.x,2.4,high.z-low.z],"native_only":true,"source_node":c.node,"source_first_triangle":c.first_source_triangle,"scope":"Conservative original whole-component ground footprint; offline army only"})
	return boxes

func run()->void:
	var output:="";var selection_path:=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg.begins_with("--selection="):selection_path=arg.trim_prefix("--selection=")
	if not output.is_absolute_path() or FileAccess.file_exists(output):push_error("Fresh absolute GLB output required");quit(1);return
	var selection:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(selection_path))
	var result:Dictionary=Placement.build("res://assets/environment/lanka_courtyard.glb",selection)
	if not result.ok:push_error(JSON.stringify(result));quit(1);return
	var node:Node3D=result.root
	var source_collision:=PackedVector3Array()
	for point in result.faces:source_collision.append(point-Vector3(-40,0,-54))
	node.set_meta("source_collision_faces",source_collision)
	node.set_meta("army_ground_footprints",army_footprints(selection))
	node.remove_child(result.body);result.body.free()
	for child in node.get_children():
		if child is MeshInstance3D:child.position=Vector3(0,0,24.8)
	var costs:=stamp(node);var doc:=GLTFDocument.new();var state:=GLTFState.new()
	var append_result:=OK;var write_result:=OK
	if output.ends_with(".scn"):
		for child in node.get_children():child.owner=node
		var packed:=PackedScene.new();append_result=packed.pack(node)
		write_result=ResourceSaver.save(packed,output,ResourceSaver.FLAG_COMPRESS|ResourceSaver.FLAG_BUNDLE_RESOURCES) if append_result==OK else append_result
	else:
		append_result=doc.append_from_scene(node,state);write_result=doc.write_to_filesystem(state,output) if append_result==OK else append_result
	var report:={"ok":append_result==OK and write_result==OK,"source_sha256":Placement.SOURCE_SHA,"selection_sha256":FileAccess.get_sha256(selection_path),"output":output,"sha256":FileAccess.get_sha256(output) if FileAccess.file_exists(output) else null,"bytes":FileAccess.get_file_as_bytes(output).size() if FileAccess.file_exists(output) else 0,"costs":costs,"source_units":"native metre Y-up; gate-centered local by original source z+24.8; runtime placement(-40,0,-54)","art_created":false,"canonical_enabled":false,"append_result":append_result,"write_result":write_result}
	FileAccess.open(output+".json",FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n");node.free();print(JSON.stringify(report));quit(0 if report.ok else 1)
