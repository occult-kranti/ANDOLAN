extends RefCounted
## One existing CC0 Lanka gate, baked to native resources; no runtime GLTF parse.
const ASSET:="res://assets/world/lanka-lane-gate.scn"
const ASSET_SHA:="e895e0aaef172901e445aa1e782b7ecbfbdf6b021cf13f1c311db3c60cae7d25"
const SOURCE_SHA:="1454e03627e9a7708557f64122cf8f170d0f8365256e69fa7689e94cd3585c33"
const ROOT_NAME:="LankaLaneGate"
const POSITION:=Vector3(-40,0,-54)
static var _scene_cache:Dictionary={}
static func clear_cache()->void:_scene_cache.clear()
static func cache_report()->Dictionary:return {"entries":_scene_cache.size(),"policy":"one cached immutable native PackedScene per verified asset path; per-instance nodes and collision shape"}
static func build(parent:Node3D,path:String=ASSET)->Dictionary:
	if not is_instance_valid(parent):return {"enabled":false,"reason":"parent_required"}
	if parent.has_node(ROOT_NAME):return {"enabled":false,"reason":"duplicate_placement"}
	if not FileAccess.file_exists(path) or FileAccess.get_sha256(path)!=ASSET_SHA:return {"enabled":false,"reason":"asset_hash"}
	if not _scene_cache.has(path):
		var loaded:=ResourceLoader.load(path,"PackedScene",ResourceLoader.CACHE_MODE_REUSE)
		if not loaded is PackedScene:return {"enabled":false,"reason":"native_scene_required"}
		_scene_cache[path]=loaded
	var node:Node3D=_scene_cache[path].instantiate()
	if node==null:return {"enabled":false,"reason":"native_instance_required"}
	var faces:=PackedVector3Array();var count:=0;var surfaces:=0;var material_ids:Dictionary={};var mesh_ids:Dictionary={}
	for child in node.get_children():
		if not child is MeshInstance3D or child.mesh==null:node.free();return {"enabled":false,"reason":"static_visual_only"}
		if not child.transform.basis.is_equal_approx(Basis.IDENTITY):node.free();return {"enabled":false,"reason":"source_transform"}
		var mesh:Mesh=child.mesh;count+=mesh.get_faces().size()/3;surfaces+=mesh.get_surface_count();mesh_ids[mesh.get_instance_id()]=true
		for i in mesh.get_surface_count():material_ids[mesh.surface_get_material(i).get_instance_id()]=true
		if String(child.name).begins_with("COL_"):
			for point in mesh.get_faces():faces.append(child.transform*point)
	if count!=17862 or surfaces!=11 or faces.size()!=6706*3 or material_ids.size()!=6:node.free();return {"enabled":false,"reason":"exact_source_budget"}
	if not node.has_meta("source_collision_faces"):node.free();return {"enabled":false,"reason":"source_collision_required"}
	var exact_faces:Variant=node.get_meta("source_collision_faces")
	if not exact_faces is PackedVector3Array or exact_faces.size()!=6706*3:node.free();return {"enabled":false,"reason":"source_collision_required"}
	for point in exact_faces:
		if not point.is_finite():node.free();return {"enabled":false,"reason":"source_collision_finite"}
	var body:=StaticBody3D.new();body.name="SourceTriangleCollision";body.collision_layer=1;body.collision_mask=0;body.set_meta("native_only",true);body.set_meta("source_sha256",SOURCE_SHA)
	var shape:=ConcavePolygonShape3D.new();shape.backface_collision=true;shape.set_faces(exact_faces)
	var holder:=CollisionShape3D.new();holder.shape=shape;body.add_child(holder);node.add_child(body)
	node.name=ROOT_NAME;node.position=POSITION;node.set_meta("source_sha256",SOURCE_SHA);node.set_meta("native_only",true);node.set_meta("review_only",false);parent.add_child(node)
	return {"enabled":true,"root":node,"body":body,"shape":shape,"report":{"enabled":true,"source_sha256":SOURCE_SHA,"asset_sha256":ASSET_SHA,"triangles":count,"collision_triangles":6706,"mesh_instances":11,"mesh_resources":mesh_ids.size(),"opaque_surfaces":surfaces,"material_resources":material_ids.size(),"collision_bodies":1,"collision_shapes":1,"army_ground_footprints":10,"position":[-40,0,-54],"units":"metres Y-up; original gate-centered geometry","native_only":true,"scope":"One reused original CC0 gate; existing open lane retained; no online/map-wide quality claim."}}

static func ground_footprints(gate:Node3D)->Dictionary:
	if not is_instance_valid(gate) or not gate.has_meta("army_ground_footprints"):return {"ok":false,"reason":"source_ground_footprints_required"}
	var boxes:Variant=gate.get_meta("army_ground_footprints")
	if not boxes is Array or boxes.size()!=10:return {"ok":false,"reason":"ground_footprint_budget"}
	var ids:Array=[]
	for box in boxes:
		if not box is Dictionary or not box.get("id") is String or box.id in ids or not box.get("position") is Array or box.position.size()!=3 or not box.get("size") is Array or box.size.size()!=3:return {"ok":false,"reason":"ground_footprint_contract"}
		ids.append(box.id)
		for value in box.position+box.size:
			if not (value is int or value is float) or not is_finite(value):return {"ok":false,"reason":"ground_footprint_finite"}
		var x:float=box.position[0];var half:float=box.size[0]*.5
		if box.size[0]<=0 or box.size[1]!=2.4 or box.size[2]<=0 or (x-half< -35.2 and x+half> -44.8):return {"ok":false,"reason":"ground_aperture_budget"}
	return {"ok":true,"boxes":boxes.duplicate(true),"actor_band_m":[0,2.4],"scope":"Ten conservative original whole-component offline army ground footprints only; original manifest and native3D collider unchanged."}

static func prepare_army_manifest(original:Dictionary,gate:Node3D)->Dictionary:
	var traversal:Variant=original.get("traversal")
	if not traversal is Dictionary or not traversal.get("native_collision_boxes",[]) is Array:return {"ok":false,"reason":"army_manifest_contract"}
	var derived:=ground_footprints(gate)
	if not derived.ok:return derived
	for existing in traversal.get("native_collision_boxes",[]):
		if not existing is Dictionary:return {"ok":false,"reason":"army_manifest_contract"}
		if String(existing.get("id","")).begins_with("lanka-gate-ground-"):return {"ok":false,"reason":"duplicate_army_footprint"}
	var copy:=original.duplicate(true)
	copy.traversal.native_collision_boxes=copy.traversal.get("native_collision_boxes",[]).duplicate(true)
	copy.traversal.native_collision_boxes.append_array(derived.boxes.duplicate(true))
	return {"ok":true,"manifest":copy,"boxes":derived.boxes,"scope":derived.scope}
