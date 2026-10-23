extends SceneTree
## Actual detailed-collider fixture, not a gameplay or visual acceptance claim.
const Builder=preload("res://scripts/traversal_landmarks.gd")
var checks: Array[Dictionary]=[]
var report_path:=""
func _initialize()->void:call_deferred("run")
func check(label:String,passed:bool,detail:Variant=null)->void:
	checks.append({"name":label,"passed":passed,"detail":detail})
func mesh_signature(node:Node)->String:
	var rows:=[]
	for child in node.get_children():
		if child is MeshInstance3D:
			var surfaces:=[]
			for index in child.mesh.get_surface_count():surfaces.append(child.mesh.surface_get_arrays(index))
			rows.append([child.position,child.rotation,child.scale,surfaces])
	return var_to_bytes(rows).hex_encode().sha256_text()
func ray(space:PhysicsDirectSpaceState3D,at:Vector3,to:Vector3)->Dictionary:
	return space.intersect_ray(PhysicsRayQueryParameters3D.create(at,to,1))
func capsule(space:PhysicsDirectSpaceState3D,at:Vector3)->Array[Dictionary]:
	# The actual native Confluence hero uses manifest radius .65, height1.8.
	var shape:=CapsuleShape3D.new();shape.radius=.65;shape.height=1.8
	var query:=PhysicsShapeQueryParameters3D.new();query.shape=shape;query.transform=Transform3D(Basis.IDENTITY,at);query.collision_mask=1
	return space.intersect_shape(query,8)
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var data:Dictionary=manifest.traversal
	var seal:=JSON.stringify(data).sha256_text()
	var baseline:=Node3D.new();baseline.name="Baseline";root.add_child(baseline)
	var baseline_report:Dictionary=Builder.new().build(baseline,data)
	var actual:=Node3D.new();actual.name="Candidate";root.add_child(actual)
	var builder=Builder.new()
	var actual_report:Dictionary=builder.build(actual,data,{"wind_court_pilot":true})
	var old:Node3D=baseline.get_node("TraversalRelics")
	var current:Node3D=actual.get_node("TraversalRelics")
	var target:Node3D=current.get_node("sun-lift-west")
	var origin:=target.global_position
	check("default build remains legacy",not baseline_report.wind_court_pilot.enabled and old.get_node("sun-lift-west").has_node("SolidLandingDeck"))
	check("one pilot replaces one visual deck",actual_report.wind_court_pilot.enabled and not target.has_node("SolidLandingDeck"))
	check("input manifest unchanged",seal==JSON.stringify(data).sha256_text())
	var untouched:=0
	for entry in data.landmarks:
		if entry.id=="sun-lift-west":continue
		untouched+=1
		check("unchanged other deck "+entry.id,mesh_signature(old.get_node(entry.id))==mesh_signature(current.get_node(entry.id)))
	check("exactly seven other decks compared",untouched==7)
	for anchor in data.anchors:
		var a:Node3D=old.get_node(anchor.id);var b:Node3D=current.get_node(anchor.id)
		check("unchanged anchor "+anchor.id,a.position==b.position and a.rotation==b.rotation and var_to_bytes(a.mesh.surface_get_arrays(0))==var_to_bytes(b.mesh.surface_get_arrays(0)))
	var old_roof:=Node3D.new();var new_roof:=Node3D.new()
	for child in old.get_node("sun-lift-west").get_children():
		if child is MeshInstance3D and (child.name=="ClearLandingMedallion" or str(child.name).begins_with("DiyaEmber") or child.mesh is SphereMesh and child.position.y>8):old_roof.add_child(child.duplicate())
	for child in target.get_children():
		if child is MeshInstance3D and (child.name=="ClearLandingMedallion" or str(child.name).begins_with("DiyaEmber") or child.mesh is SphereMesh and child.position.y>8):new_roof.add_child(child.duplicate())
	check("medallion and six roof embers unchanged",old_roof.get_child_count()==7 and new_roof.get_child_count()==7 and mesh_signature(old_roof)==mesh_signature(new_roof))
	old_roof.free();new_roof.free()
	var bounds:=AABB(Vector3(-4,0,-4),Vector3(8,8,8))
	var contained:=true
	for part in builder.wind_court_parts():
		var box:=AABB(part.at-part.size*.5,part.size)
		contained=contained and bounds.grow(.00001).encloses(box)
	check("all architecture stays inside eight metre envelope",contained)
	var near:MeshInstance3D=target.get_node("WindCourtNear")
	var mid:MeshInstance3D=target.get_node("WindCourtMid")
	check("three merged opaque architecture surfaces at each LOD",near.mesh.get_surface_count()==3 and mid.mesh.get_surface_count()==3)
	check("near and mid triangle budgets",actual_report.wind_court_pilot.near_triangles<=2500 and actual_report.wind_court_pilot.mid_triangles<=1000,actual_report.wind_court_pilot)
	check("immutable material family reused",actual_report.materials==baseline_report.materials)
	check("no old flat-box collider in fixture",not target.has_node("SolidLandingDeck") and target.get_node("WindCourtDetailedCollision").get_child_count()>1)
	await physics_frame;await physics_frame
	var space:=target.get_world_3d().direct_space_state
	var hit:=ray(space,origin+Vector3(0,12,0),origin+Vector3(0,-1,0))
	check("roof support stays exactly y8",not hit.is_empty() and is_equal_approx(hit.position.y,origin.y+8),hit.get("position"))
	for sign_ in [-1.0,1.0]:
		for axis in range(2):
			var start:=Vector3(sign_*6,3,1.05) if axis==0 else Vector3(1.05,3,sign_*6)
			var finish:=Vector3(0,3,1.05) if axis==0 else Vector3(1.05,3,0)
			hit=ray(space,origin+start,origin+finish)
			var distance_:float=absf((hit.position-origin).x if axis==0 else (hit.position-origin).z) if not hit.is_empty() else -1
			check("closed bay collider matches visible core "+str(axis)+":"+str(sign_),absf(distance_-3.32)<.001,distance_)
			start=Vector3(sign_*6,3,0) if axis==0 else Vector3(0,3,sign_*6)
			finish=Vector3(0,3,0)
			hit=ray(space,origin+start,origin+finish)
			distance_=absf((hit.position-origin).x if axis==0 else (hit.position-origin).z) if not hit.is_empty() else -1
			check("engaged pier collider matches visible support "+str(axis)+":"+str(sign_),absf(distance_-3.84)<.001,distance_)
	check("actual hero capsule has no invisible old blocker across bay",capsule(space,origin+Vector3(1.025,3.7,-4.0)).is_empty())
	check("actual hero capsule detects the real closed bay surface",not capsule(space,origin+Vector3(1.025,3.7,-3.94)).is_empty())
	check("capsule clears actual landing roof above",capsule(space,origin+Vector3(0,8.92,0)).is_empty())
	check("capsule detects actual landing roof contact",not capsule(space,origin+Vector3(0,8.85,0)).is_empty())
	check("outside footprint has no added roof blocker",ray(space,origin+Vector3(4.05,12,0),origin+Vector3(4.05,.7,0)).is_empty())
	var passed:=checks.all(func(item):return item.passed)
	var report:={"passed":passed,"checks":checks,"pilot":actual_report.wind_court_pilot,"source_sha256":FileAccess.get_sha256("res://scripts/traversal_landmarks.gd"),"manifest_sha256":FileAccess.get_sha256("res://assets/world/confluence-map.json"),"scope":"Actual native fixture physics and resource checks; baseline manifest flat box deliberately omitted. No full-world, visual, authority or hardware acceptance.","canonical_enabled":false}
	if not report_path.is_empty():FileAccess.open(report_path,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size(),"pilot":actual_report.wind_court_pilot}))
	quit(0 if passed else 1)
