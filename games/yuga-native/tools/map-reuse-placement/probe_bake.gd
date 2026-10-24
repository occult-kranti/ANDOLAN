extends SceneTree
const Placement=preload("res://tools/map-reuse-placement/placement.gd")
const Gate=preload("res://tools/map-reuse-placement/runtime_gate.gd")
var checks:Array[Dictionary]=[]
var asset:="";var selection_path:="";var output:="";var reference_only:=false;var reference_asset:=""
func _initialize()->void:call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func material_value(mat:StandardMaterial3D)->Dictionary:
	var fields:Dictionary={}
	for property in mat.get_property_list():
		var name:String=property.name
		if not property.usage&PROPERTY_USAGE_STORAGE or name.begins_with("resource_") or name in ["script","metadata/_gltf_index"]:continue
		var value:Variant=mat.get(name)
		if value is Texture2D:
			var image:Image=value.get_image();fields[name]={"width":image.get_width(),"height":image.get_height(),"format":image.get_format(),"bytes_sha256":image.get_data().hex_encode().sha256_text()}
		elif not value is Resource:fields[name]=value
	return fields
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--asset="):asset=arg.trim_prefix("--asset=")
		elif arg.begins_with("--selection="):selection_path=arg.trim_prefix("--selection=")
		elif arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--reference-only":reference_only=true
		elif arg.begins_with("--reference-asset="):reference_asset=arg.trim_prefix("--reference-asset=")
	var source:Dictionary=Placement.build("res://assets/environment/lanka_courtyard.glb",JSON.parse_string(FileAccess.get_file_as_string(selection_path)))
	check("original reviewed selection builds",source.get("ok",false))
	var packed:PackedScene=ResourceLoader.load(asset,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE)
	check("baked native PackedScene reloads without import",packed!=null)
	if packed==null:quit(1);return
	var baked:Node3D=packed.instantiate();var correspondence:=true;var failures:Array=[]
	for original in source.root.get_children():
		if not original is MeshInstance3D:continue
		var copy:MeshInstance3D=baked.get_node_or_null(NodePath(original.name))
		if copy==null:correspondence=false;failures.append(str(original.name));continue
		if copy.position!=Vector3(0,0,24.8) or copy.mesh.get_surface_count()!=original.mesh.get_surface_count():correspondence=false;failures.append(str(original.name)+"transform/surface")
		for i in original.mesh.get_surface_count():
			var a:Array=original.mesh.surface_get_arrays(i);var b:Array=copy.mesh.surface_get_arrays(i)
			for slot in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_NORMAL,Mesh.ARRAY_TANGENT,Mesh.ARRAY_TEX_UV,Mesh.ARRAY_INDEX]:
				if a[slot]!=b[slot]:correspondence=false;failures.append(str(original.name)+" slot"+str(slot))
			if material_value(original.mesh.surface_get_material(i))!=material_value(copy.mesh.surface_get_material(i)):correspondence=false;failures.append(str(original.name)+" material")
	check("all eleven surface positions normals tangents UV indices and stored native materials/images exactly match source",correspondence,failures)
	check("self-contained scene has zero external dependencies",ResourceLoader.get_dependencies(asset).is_empty(),ResourceLoader.get_dependencies(asset))
	var exact:PackedVector3Array=baked.get_meta("source_collision_faces");var drift:=0.0
	for i in exact.size():drift=maxf(drift,(exact[i]+Gate.POSITION).distance_to(source.faces[i]))
	check("baked original collision metadata matches reviewed world source within1e-5metre",drift<.00001,drift)
	if not reference_asset.is_empty():
		var reference:PackedScene=ResourceLoader.load(reference_asset,"PackedScene",ResourceLoader.CACHE_MODE_IGNORE);var reference_node:Node3D=reference.instantiate()
		check("fresh rebuild source-collision and ten ground-footprint metadata exactly match qualified artifact",baked.get_meta("source_collision_faces")==reference_node.get_meta("source_collision_faces") and baked.get_meta("army_ground_footprints")==reference_node.get_meta("army_ground_footprints"))
		reference_node.free();reference=null
	baked.free();packed=null
	if reference_only:
		var passed:=checks.all(func(row):return row.passed)
		FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"asset_sha256":FileAccess.get_sha256(asset),"scope":"Independent clean rebuild retains all source mesh attributes, native materials and embedded image bytes, original collision and zero external dependencies. ResourceSaver IDs/whole-file bytes may differ; not a cache/runtime hash acceptance for a different artifact."},"  ")+"\n");source.root.free();print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1);return
	var a:=Node3D.new();var b:=Node3D.new();root.add_child(a);root.add_child(b)
	var first:Dictionary=Gate.build(a,asset);var second:Dictionary=Gate.build(b,asset)
	check("two independent instances share one scene cache",first.get("enabled",false) and second.get("enabled",false) and Gate.cache_report().entries==1)
	var mesh_shared:=true;var materials_shared:=true
	for child in first.root.get_children():
		if not child is MeshInstance3D:continue
		var peer:MeshInstance3D=second.root.get_node(NodePath(child.name));mesh_shared=mesh_shared and child.mesh==peer.mesh
		for i in child.mesh.get_surface_count():materials_shared=materials_shared and child.mesh.surface_get_material(i)==peer.mesh.surface_get_material(i)
	check("mesh and material resources reused across instances",mesh_shared and materials_shared)
	check("body and collision shape are separately owned",first.body!=second.body and first.shape!=second.shape and first.shape.get_faces()==second.shape.get_faces())
	check("same parent duplicate refused without adding nodes",not Gate.build(a,asset).enabled and a.get_child_count()==1)
	await physics_frame;await physics_frame
	var source_faces:PackedVector3Array=source.faces;var baked_faces:PackedVector3Array=first.shape.get_faces();var error:=0.0
	if source_faces.size()==baked_faces.size():
		for i in source_faces.size():error=maxf(error,source_faces[i].distance_to(first.root.position+baked_faces[i]))
	else:error=INF
	check("all6706 structural triangles retain original world collision coordinates",error<.00001,error if is_finite(error) else null)
	var body_ref:WeakRef=weakref(first.body);var shape_ref:WeakRef=weakref(first.shape)
	first.root.free();first.clear();await physics_frame;await physics_frame
	check("first instance body and shape release cleanly",body_ref.get_ref()==null and shape_ref.get_ref()==null)
	check("peer retains actual physics after first teardown",not root.world_3d.direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(-49,1.6,-70),Vector3(-49,1.6,-38),1)).is_empty())
	var absent:Dictionary=Gate.build(a,"/not-an-asset.scn");check("missing/wrong native resource fails closed",not absent.enabled and absent.reason=="asset_hash" and a.get_child_count()==0)
	var valid_cache:PackedScene=Gate._scene_cache[asset]
	var broken:Node3D=valid_cache.instantiate();broken.get_child(0).free()
	var malformed:=PackedScene.new();malformed.pack(broken);broken.free();Gate._scene_cache[asset]=malformed
	var rejected:Dictionary=Gate.build(a,asset)
	check("negative cached scene missing a source mesh is refused",not rejected.enabled and rejected.reason=="exact_source_budget" and a.get_child_count()==0)
	broken=valid_cache.instantiate();broken.remove_meta("source_collision_faces");malformed=PackedScene.new();malformed.pack(broken);broken.free();Gate._scene_cache[asset]=malformed
	rejected=Gate.build(a,asset)
	check("negative cached scene missing original collision is refused",not rejected.enabled and rejected.reason=="source_collision_required" and a.get_child_count()==0)
	Gate._scene_cache[asset]=valid_cache
	var restored:Dictionary=Gate.build(a,asset)
	check("restored verified cache still builds one valid owned body",restored.enabled and a.get_child_count()==1)
	restored.root.free();restored.clear();valid_cache=null;malformed=null
	second.root.free();second.clear();a.free();b.free();source.root.free();source.clear();Gate.clear_cache()
	check("explicit cache teardown releases all cached scenes",Gate.cache_report().entries==0)
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"asset_sha256":FileAccess.get_sha256(asset),"asset_bytes":FileAccess.get_file_as_bytes(asset).size(),"scope":"Native source-correspondence, embedded materials/image byte equality, exact collision equivalence, cache sharing and resource lifecycle. Not a new render or export acceptance."},"  ")+"\n");print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
