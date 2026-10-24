extends SceneTree
## Root's integrated native gate must retain routes and detect stale full boxes.
var output := ""
var checks := []
var scene: Node3D
var capsule_shape: CapsuleShape3D
var source_before := {}
const SOURCES := ["res://scripts/confluence_world.gd","res://scripts/lanka_lane_gate.gd","res://assets/world/lanka-lane-gate.scn","res://scripts/lane_minion.gd","res://scripts/lane_army.gd","res://assets/world/confluence-map.json"]
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,value:bool,detail:Variant=null)->void:checks.append({"name":label,"passed":value,"detail":detail})
func query(space:PhysicsDirectSpaceState3D,x:float,z:float)->Array[Dictionary]:
	var q:=PhysicsShapeQueryParameters3D.new();q.shape=capsule_shape
	q.transform=Transform3D(Basis.IDENTITY,Vector3(x,capsule_shape.height*.5+.04,z));q.collision_mask=1
	return space.intersect_shape(q,16)
func shape_query(space:PhysicsDirectSpaceState3D,shape:CapsuleShape3D,offset:float,x:float,z:float)->Array[Dictionary]:
	var q:=PhysicsShapeQueryParameters3D.new();q.shape=shape
	q.transform=Transform3D(Basis.IDENTITY,Vector3(x,offset+.04,z));q.collision_mask=1
	return space.intersect_shape(q,16)
func source_hashes()->Dictionary:
	var result:={}
	for path in SOURCES:
		result[path]=FileAccess.get_sha256(path) if FileAccess.file_exists(path) else "MISSING"
	return result
func run()->void:
	source_before=source_hashes()
	check("all reviewed integration sources exist",not "MISSING" in source_before.values())
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	for unused in 12:await process_frame
	scene.set_process(false);scene.set_physics_process(false);scene.player.set_physics_process(false);scene.army.set_physics_process(false)
	check("canonical native world is ready",scene.world_ready)
	var gate:Node3D=scene.world.get_node_or_null("LankaLaneGate")
	check("one canonical reused gate exists at reviewed position",gate!=null and gate.position.is_equal_approx(Vector3(-40,0,-54)))
	if gate==null:await finish();return
	var body:StaticBody3D=gate.get_node_or_null("SourceTriangleCollision")
	check("source gate remains explicitly native only",gate.get_meta("native_only",false) and body!=null and body.get_meta("native_only",false))
	if body==null:await finish();return
	var shapes:=body.find_children("*","CollisionShape3D",true,false)
	check("one exact structural triangle collider",shapes.size()==1 and shapes[0].shape is ConcavePolygonShape3D and shapes[0].shape.get_faces().size()==6706*3)
	var meshes:=gate.find_children("*","MeshInstance3D",true,false);var faces:=0
	for mesh in meshes:faces+=mesh.mesh.get_faces().size()/3
	check("eleven original source surfaces retain17862 triangles",meshes.size()==11 and faces==17862)
	check("eight raised decks and all authority boxes retained",scene.native_platform_bodies.size()==8 and scene.authority_bodies.size()==scene.manifest.authority_collision_boxes.size())
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:capsule_shape=child.shape.duplicate()
	check("query clones actual Confluence0.65metre capsule",capsule_shape!=null and is_equal_approx(capsule_shape.radius,.65) and is_equal_approx(capsule_shape.height,1.8))
	if capsule_shape==null:await finish();return
	await physics_frame;await physics_frame
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var blocked:=[]
	for x in [-44.0,-40.0,-36.0]:
		for z in [-64.0,-59.5,-54.0,-48.5,-44.0]:
			if not query(space,x,z).is_empty():blocked.append([x,z])
	check("canonical eight metre lane passage clears real player",blocked.is_empty(),blocked)
	check("canonical source piers provide actual cover",not query(space,-49,-54).is_empty() and not query(space,-31,-54).is_empty())
	var fake:=StaticBody3D.new();fake.name="W1InjectedObsoleteWholeGateBox";fake.collision_layer=1;fake.collision_mask=0
	var holder:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(26,11,10);holder.shape=box;fake.add_child(holder);fake.position=Vector3(-40,5.5,-54);scene.world.add_child(fake)
	await physics_frame;await physics_frame
	check("negative obsolete whole box really closes passage",not query(space,-40,-54).is_empty())
	fake.free();await physics_frame;await physics_frame
	check("removing negative restores original clear passage",query(space,-40,-54).is_empty() and is_instance_valid(body))
	var actual_shapes:={};var dimensions:={};var minion_blocked:=[];var tested:=0
	var Unit=load("res://scripts/lane_minion.gd")
	for role in ["spearman","bow_guard","commander","cannon_cart","royal_chariot"]:
		var unit=Unit.new();unit.render_art=false;unit.setup(scene.army,90000+actual_shapes.size(),"sun",role,0);root.add_child(unit)
		var shape:CapsuleShape3D=unit.shape.shape.duplicate();var offset:float=unit.shape.position.y
		actual_shapes[role]={"shape":shape,"offset":offset};dimensions[role]={"radius_m":shape.radius,"height_m":shape.height,"offset_m":offset}
		unit.free()
		for x in [-41.2,-40.0,-38.8]:
			for zi in 41:
				var z:float=-64.0+zi*.5;tested+=1
				if not shape_query(space,shape,offset,x,z).is_empty():minion_blocked.append({"role":role,"x":x,"z":z})
	check("five actual role collider shapes clear 615 formation route probes",tested==615 and minion_blocked.is_empty(),{"dimensions":dimensions,"blocked":minion_blocked,"queries":tested})
	check("actual tall royal and commander dimensions are exercised",is_equal_approx(dimensions.royal_chariot.height_m,2.4) and is_equal_approx(dimensions.commander.height_m,2.13) and is_equal_approx(dimensions.spearman.height_m,1.9))
	var overhead:=StaticBody3D.new();overhead.name="W1HeightSensitiveLowCeiling";overhead.collision_layer=1;overhead.collision_mask=0
	var overhead_holder:=CollisionShape3D.new();var overhead_box:=BoxShape3D.new();overhead_box.size=Vector3(4,.2,4);overhead_holder.shape=overhead_box;overhead.add_child(overhead_holder);overhead.position=Vector3(-40,2.05,-54);scene.world.add_child(overhead)
	await physics_frame;await physics_frame
	check("low ceiling negative leaves real 1.8m player clear",query(space,-40,-54).is_empty())
	var royal:Dictionary=actual_shapes.royal_chariot;var commander:Dictionary=actual_shapes.commander
	check("low ceiling negative blocks actual 2.4m royal and 2.13m commander",not shape_query(space,royal.shape,royal.offset,-40,-54).is_empty() and not shape_query(space,commander.shape,commander.offset,-40,-54).is_empty())
	overhead.free();await physics_frame;await physics_frame
	check("removing low ceiling restores actual royal route",shape_query(space,royal.shape,royal.offset,-40,-54).is_empty())
	await finish()
func finish()->void:
	var source_after:=source_hashes()
	check("source files remain unchanged during independent probe",source_before==source_after,{"before":source_before,"after":source_after})
	var passed:=checks.all(func(row):return row.passed)
	var report:={"schema":2,"passed":passed,"checks":checks,"scope":"Actual canonical assembly, source costs, live player and five complete minion capsules, cover, obsolete whole-box and height-sensitive low-ceiling negatives. No new render, online authority, full-map or hardware acceptance.","source_before":source_before,"source_after":source_after}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	current_scene=null;scene.queue_free()
	for unused in 8:await process_frame
	quit(0 if passed else 1)
