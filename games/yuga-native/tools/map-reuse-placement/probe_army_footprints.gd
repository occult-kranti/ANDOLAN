extends SceneTree
const Gate=preload("res://tools/map-reuse-placement/runtime_gate.gd")
const Army=preload("res://scripts/lane_army.gd")
var checks:Array[Dictionary]=[]
func _initialize()->void:call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func contains(box:Dictionary,p:Vector3)->bool:
	return absf(p.x-box.position[0])<=box.size[0]*.5+.00002 and absf(p.z-box.position[2])<=box.size[2]*.5+.00002
func run()->void:
	var asset:="";var output:=""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--asset="):asset=arg.trim_prefix("--asset=")
		elif arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	var parent:=Node3D.new();root.add_child(parent)
	var result:Dictionary=Gate.build(parent,asset);check("qualified native gate builds",result.get("enabled",false))
	if not result.get("enabled",false):quit(1);return
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"));var before:=manifest.duplicate(true)
	var prepared:Dictionary=Gate.prepare_army_manifest(manifest,result.root)
	check("source-derived10ground components prepare",prepared.get("ok",false) and prepared.get("boxes",[]).size()==10,prepared.get("boxes",[]))
	if not prepared.get("ok",false):quit(1);return
	check("original source manifest and all authority/deck boxes unchanged",manifest==before and prepared.manifest.authority_collision_boxes==manifest.authority_collision_boxes and prepared.manifest.traversal.native_collision_boxes.size()==manifest.traversal.native_collision_boxes.size()+10)
	var copy:Dictionary=prepared.manifest.duplicate(true);copy.traversal.native_collision_boxes[0].size[0]+=123
	check("deep-copy mutation cannot affect original manifest",manifest==before and copy.traversal.native_collision_boxes!=manifest.traversal.native_collision_boxes)
	check("repeated footprint append fails closed",Gate.prepare_army_manifest(prepared.manifest,result.root).get("reason")=="duplicate_army_footprint")
	var uncovered:=0;var ground_triangles:=0;var faces:PackedVector3Array=result.root.get_meta("source_collision_faces")
	for i in range(0,faces.size(),3):
		var a:Vector3=faces[i];var b:Vector3=faces[i+1];var c:Vector3=faces[i+2]
		if minf(a.y,minf(b.y,c.y))>2.4:continue
		ground_triangles+=1
		for p in [a,b,c]:
			var world:Vector3=p+Gate.POSITION
			if not prepared.boxes.any(func(box):return contains(box,world)):uncovered+=1
	check("every source structural triangle touching0..2.4m band has contained ground projection",uncovered==0 and ground_triangles>500,{"triangles":ground_triangles,"uncovered_vertices":uncovered})
	await physics_frame;await physics_frame
	var space:=parent.get_world_3d().direct_space_state
	var false_solid:Array=[];var samples:=0
	var capsule:=CapsuleShape3D.new();capsule.radius=.39;capsule.height=1.8
	for box in prepared.boxes:
		var x0:float=box.position[0]-box.size[0]*.5+.02;var z0:float=box.position[2]-box.size[2]*.5+.02
		for xi in maxi(2,ceili(box.size[0]/.4)):
			for zi in maxi(2,ceili(box.size[2]/.4)):
				var x:float=lerpf(x0,box.position[0]+box.size[0]*.5-.02,float(xi)/float(maxi(2,ceili(box.size[0]/.4))-1));var z:float=lerpf(z0,box.position[2]+box.size[2]*.5-.02,float(zi)/float(maxi(2,ceili(box.size[2]/.4))-1))
				var q:=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.transform=Transform3D(Basis.IDENTITY,Vector3(x,.94,z));q.collision_mask=1;samples+=1
				if not space.intersect_shape(q,8).any(func(hit):return hit.collider==result.body):false_solid.append([x,z])
	check("all conservatively blocked ground samples have actual solid contact for smallest army0.39capsule",false_solid.is_empty(),{"samples":samples,"false_solid":false_solid})
	var army:=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	check("existing unchanged army configure accepts copied native footprints",army.configure(prepared.manifest,null))
	check("cross-pier attacks blocked and central aperture remains clear",not army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)) and not army.line_clear(Vector3(-31,0,-70),Vector3(-31,0,-38)) and army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)))
	var route_bad:Array=[]
	for role in Army.Unit.STATS:
		for offset in [-2.2,-1.2,0.0,1.2,2.2]:
			if not army.line_clear(Vector3(-40+offset,0,-70),Vector3(-40+offset,0,-38),Army.Unit.STATS[role].radius):route_bad.append([role,offset])
	check("all5roles actual and margin offset routes remain clear",route_bad.is_empty(),route_bad)
	army.reset();check("existing army reset preserves cover and one footprint set",army.boxes.size()==manifest.authority_collision_boxes.size()+manifest.traversal.native_collision_boxes.size()+10 and not army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)))
	var again:Dictionary=Gate.prepare_army_manifest(manifest,result.root)
	check("fresh source reconfigure is idempotent and preserves clear aperture",army.configure(again.manifest,null) and army.boxes.size()==26 and army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)))
	var baseline:=Army.new();baseline.visual_enabled=false;root.add_child(baseline);baseline.set_physics_process(false);baseline.configure(manifest,null)
	check("negative omitted footprint copy reproduces shooting through native pier",baseline.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)))
	check("original JSON and source manifest remain untouched after configure/reset",manifest==before)
	army.queue_free();baseline.queue_free();parent.queue_free();for unused in 8:await process_frame
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"asset_sha256":Gate.ASSET_SHA,"lane_army_sha256":FileAccess.get_sha256("res://scripts/lane_army.gd"),"scope":"Original unchanged army configure consumes a deep manifest copy with10exact-source conservative ground footprints. Native source containment/capsule coverage, aperture/ranks/attacks, duplicates, reset/reconfigure and omitted-footprint negative. Offline planar approximation only."},"  ")+"\n");print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
