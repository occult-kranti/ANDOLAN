extends SceneTree
const Placement=preload("res://tools/map-reuse-placement/placement.gd")
var checks:Array[Dictionary]=[]
var output:="res://physics-report.json"
func _initialize()->void:call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func query_capsule(space:PhysicsDirectSpaceState3D,x:float,z:float)->Array[Dictionary]:
	var capsule:=CapsuleShape3D.new();capsule.radius=.65;capsule.height=1.8
	var q:=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.transform=Transform3D(Basis.IDENTITY,Vector3(x,.93,z));q.collision_mask=1
	return space.intersect_shape(q,16)
func route_free(space:PhysicsDirectSpaceState3D)->Dictionary:
	var failed:Array=[];var samples:=0
	for x in [-44.0,-43.0,-40.0,-37.0,-36.0]:
		for step in 73:
			var z:float=-72.0+step*.5;samples+=1
			if not query_capsule(space,x,z).is_empty():failed.append([x,z])
	return {"ok":failed.is_empty(),"samples":samples,"failed":failed}
func ray(space:PhysicsDirectSpaceState3D,a:Vector3,b:Vector3)->Dictionary:return space.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1))
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	var selection:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://selection.json"))
	var source:="res://assets/environment/lanka_courtyard.glb"
	var original_hash:=FileAccess.get_sha256(source)
	var loaded:Dictionary=Placement.build(source,selection);check("actual pinned whole source pieces load",loaded.ok)
	if not loaded.ok:print(JSON.stringify(loaded));quit(1);return
	root.add_child(loaded.root)
	check("exact scoped source geometry cost",loaded.report.triangles==17862 and loaded.report.surfaces==11 and loaded.report.instances==11 and loaded.report.collision_triangles==6706,loaded.report)
	check("one truthful collider uses identical selected structural triangles",loaded.root.find_children("*","StaticBody3D",true,false).size()==1 and loaded.shape.get_faces()==loaded.faces)
	var bounds:=AABB(loaded.faces[0],Vector3.ZERO)
	for p in loaded.faces:bounds=bounds.expand(p)
	check("gate remains native metres and local footprint",bounds.position.x>=-53.201 and bounds.end.x<=-26.799 and bounds.position.z>=-59.201 and bounds.end.z<=-47.999 and bounds.size.y>15, {"min":bounds.position,"max":bounds.end})
	await physics_frame;await physics_frame
	var space:=root.world_3d.direct_space_state
	var route:=route_free(space);check("five continuous width traces keep entire eight metre lane clear for conservative manifest .65m capsule",route.ok,route)
	var collisions:=0
	for x in [-49.0,-31.0]:
		if not query_capsule(space,x,-54).is_empty():collisions+=1
	check("stone pier interiors really block capsule",collisions==2,collisions)
	check("eye level line of sight through real gate opening",ray(space,Vector3(-40,1.6,-70),Vector3(-40,1.6,-38)).is_empty())
	check("pier provides real cover at eye height",not ray(space,Vector3(-49,1.6,-70),Vector3(-49,1.6,-38)).is_empty())
	check("arch crown blocks elevated line of sight",not ray(space,Vector3(-40,10.9,-70),Vector3(-40,10.9,-38)).is_empty())
	var camera_clear:=true;var camera_samples:=0
	var sphere:=SphereShape3D.new();sphere.radius=.18
	for step in 73:
		var z:float=-72+step*.5;var q:=PhysicsShapeQueryParameters3D.new();q.shape=sphere;q.transform=Transform3D(Basis.IDENTITY,Vector3(-39.35,1.85,z+3.5));q.motion=Vector3(0,0,-3.5);q.collision_mask=1
		var cast:=space.cast_motion(q);camera_samples+=1
		if cast[0]<.999:camera_clear=false
	check("ordinary3.5m shoulder camera sphere stays clear through central route",camera_clear,{"samples":camera_samples,"sphere_radius":.18,"shoulder":.65})
	var tested:=0;var hit_count:=0
	for i in range(0,loaded.faces.size(),maxi(3,int(loaded.faces.size()/80.0)/3*3)):
		if i+2>=loaded.faces.size():break
		var a:Vector3=loaded.faces[i];var b:Vector3=loaded.faces[i+1];var c:Vector3=loaded.faces[i+2];var n:Vector3=(b-a).cross(c-a)
		if n.length()<.00001:continue
		n=n.normalized();var center:Vector3=(a+b+c)/3;var h:=ray(space,center+n*.02,center-n*.02);tested+=1
		if not h.is_empty() and h.collider==loaded.body and h.position.distance_to(center)<.021:hit_count+=1
	check("actual selected surface rays match collision",tested>=70 and tested==hit_count,{"rays":tested,"hits":hit_count})
	# Prove route checks catch the common stale flat authority blocker failure.
	var old:=StaticBody3D.new();var holder:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(26,11,10);holder.shape=box;old.position=Vector3(-40,5.5,-54);old.add_child(holder);root.add_child(old)
	await physics_frame;await physics_frame
	var blocked:=route_free(space);check("negative stale full AABB closes passage and is detected",not blocked.ok and not blocked.failed.is_empty(),blocked.failed.size())
	old.free();await physics_frame;await physics_frame
	check("removing injected duplicate restores original route",route_free(space).ok)
	var malformed:=selection.duplicate(true);malformed.selected[0].source_triangle_ids[1]=malformed.selected[0].source_triangle_ids[0]
	check("duplicate source face refused",Placement.build(source,malformed).get("reason")=="ordered_unique_source_triangles")
	malformed=selection.duplicate(true);malformed.selected[0].collision=true
	check("decorative collision injection refused",Placement.build(source,malformed).get("reason")=="collision_scope")
	malformed=selection.duplicate(true);malformed.placement_translation=[-40,0,-29.3]
	check("unreviewed placement refused",Placement.build(source,malformed).get("reason")=="selection_contract")
	malformed=selection.duplicate(true);malformed.selected[0].source_triangle_ids[0]=INF
	check("nonfinite source index refused",Placement.build(source,malformed).get("reason")=="ordered_unique_source_triangles")
	for invalid in [null,false,"not-an-array",{}]:
		malformed=selection.duplicate(true);malformed.selected=invalid
		var refused:Dictionary=Placement.build(source,malformed)
		check("malformed selected field rejected without script error type"+str(typeof(invalid)),not refused.get("ok",true) and refused.get("reason")=="selection_contract")
	check("protected courtyard source remains byte identical",FileAccess.get_sha256(source)==original_hash and original_hash==Placement.SOURCE_SHA)
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"costs":loaded.report,"canonical_enabled":false,"scope":"Actual isolated manifest-envelope .65m capsule, shoulder camera sphere, LOS and triangle collision tests. No full map/runtime integration or visual quality acceptance."},"  ")+"\n")
	loaded.root.free();print(JSON.stringify({"passed":passed,"checks":checks.size(),"output":output}));quit(0 if passed else 1)
