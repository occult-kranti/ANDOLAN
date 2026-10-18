extends SceneTree
## Actual cached world, actual native capsule/rays; isolated candidate only.
const Frontage = preload("res://art/world-finish/lane-frontage-r1/candidate.gd")
const DATA = "res://art/world-finish/lane-frontage-r1/candidate-mesh.json"
var output: String
var checks: Array[Dictionary] = []
var source_before: Dictionary = {}
var scene: Node3D
var target: StaticBody3D

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(name: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":name,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",name)
func flush() -> void:
	await physics_frame;await process_frame;await physics_frame;await process_frame
func frames(count: int = 8) -> void:
	for unused in count: await process_frame
func ray(from: Vector3,to: Vector3) -> Dictionary:
	return scene.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1,[scene.player.get_rid()]))
func ray_receipt(hit: Dictionary) -> Dictionary:
	return {"hit":not hit.is_empty(),"body":String(hit.collider.name) if not hit.is_empty() else "","position":str(hit.position) if not hit.is_empty() else ""}
func sweep(from: Vector3,to: Vector3) -> Dictionary:
	var collision:=KinematicCollision3D.new()
	var transform: Transform3D=scene.player.global_transform;transform.origin=from
	var blocked: bool=scene.player.test_move(transform,to-from,collision,.001)
	return {"blocked":blocked,"body":String(collision.get_collider().name) if blocked else "","travel_z":collision.get_travel().z if blocked else to.z-from.z,"normal":str(collision.get_normal()) if blocked else ""}
func bodies(exclude_target: bool) -> Dictionary:
	var result: Dictionary = {}
	for node in scene.world.find_children("*","CollisionObject3D",true,false):
		if exclude_target and node==target: continue
		var shapes: Array = []
		for child in node.get_children():
			if not child is CollisionShape3D: continue
			var shape: Shape3D=child.shape
			var row: Dictionary={"class":shape.get_class(),"instance":shape.get_instance_id(),"transform":str(child.transform),"disabled":child.disabled}
			if shape is BoxShape3D: row.dimensions=str(shape.size)
			if shape is ConcavePolygonShape3D: row.faces_sha256=var_to_bytes(shape.get_faces()).hex_encode().sha256_text()
			shapes.append(row)
		result[String(node.get_path())]={"instance":node.get_instance_id(),"transform":str(node.global_transform),"layer":node.collision_layer,"mask":node.collision_mask,"shapes":shapes}
	return result
func actual_materials(original: Node3D) -> Array:
	var found: Array = []
	var meshes:=original.find_children("*","MeshInstance3D",true,false)
	if original is MeshInstance3D: meshes.push_front(original)
	for name in Frontage.MATERIAL_NAMES:
		var material: Material
		for node in meshes:
			for index in node.mesh.get_surface_count():
				var imported: Material=node.mesh.surface_get_material(index)
				if imported and imported.resource_name==name: material=node.get_active_material(index)
		found.append(material)
	return found
func shape_matches_visible(result: Dictionary) -> bool:
	var instance: MeshInstance3D=result.mesh
	var shape: ConcavePolygonShape3D=result.shape
	var faces:=shape.get_faces();var offset:=0
	for surface in instance.mesh.get_surface_count():
		var arrays:=instance.mesh.surface_get_arrays(surface)
		var positions: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		for point in positions:
			if offset>=faces.size() or not (target.global_transform*faces[offset]).is_equal_approx(instance.global_transform*point): return false
			offset+=1
	return offset==faces.size()
func assert_contacts(lod: String) -> void:
	for sample in [{"name":"closed-door","x":20.0,"y":1.4,"z":-36.35},{"name":"closed-window","x":26.0,"y":2.1,"z":-36.55},{"name":"upper-window","x":22.7,"y":6.3,"z":-36.55},{"name":"pier","x":23.95,"y":2.1,"z":-37.0}]:
		var hit:=ray(Vector3(sample.x,sample.y,-40),Vector3(sample.x,sample.y,-16))
		check(lod+" native ray meets visible "+sample.name,not hit.is_empty() and hit.collider==target and absf(hit.position.z-sample.z)<.002,ray_receipt(hit))
	var clear:=sweep(Vector3(20,.05,-40),Vector3(20,.05,-37.1))
	var contact:=sweep(Vector3(20,.05,-40),Vector3(20,.05,-34))
	check(lod+" real hero capsule approaches recess and stops at closed back",not clear.blocked and contact.blocked and contact.body=="authority-solid-2" and absf((-40+contact.travel_z)-(-36.35-.29))<.012,{"approach":clear,"closed_back":contact,"expected_center_contact_z":-36.64})
	var all_closed:=true
	for x in [-8.8,-6.0,-4.0,-2.0,0.0,2.0,4.0,6.0,8.8]:
		for y in [.1,1.4,3.6,6.3,10.3,14.8]:
			var hit:=ray(Vector3(20+x,y,-40),Vector3(20+x,y,-16))
			all_closed=all_closed and not hit.is_empty() and hit.collider==target
	check(lod+" sampled projectile/tether straight rays find closed solid with no new through opening",all_closed,{"rays":54,"scope":"Actual native ray obstruction only; not ability/event authority or all approach coverage."})
	var roof:=ray(Vector3(20,20,-20),Vector3(20,12,-20))
	check(lod+" uncovered body roof support remains Y15",not roof.is_empty() and roof.collider==target and absf(roof.position.y-15)<.002,ray_receipt(roof))

func run() -> void:
	if output.is_empty() or FileAccess.file_exists(output): quit(2);return
	for path in ["res://scripts/confluence_world.gd","res://scripts/player.gd","res://scripts/world_roof_loggia.gd","res://scripts/environment_surface_finish.gd","res://assets/world/confluence-map.json","res://art/world-finish/lane-frontage-r1/candidate.gd",DATA,get_script().resource_path]: source_before[path]=FileAccess.get_sha256(path)
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	await frames()
	scene.set_overview(true);await flush()
	target=scene.world.get_node("authority-solid-2")
	var original: Node3D=scene.world.get_node("CityArt/block-2")
	var holder: CollisionShape3D=target.get_child(0)
	var old_shape: Shape3D=holder.shape
	var old_id:=target.get_instance_id();var manifest_hash:=JSON.stringify(scene.manifest).sha256_text()
	var other_bodies:=bodies(true);var all_bodies:=bodies(false)
	var old_materials:=actual_materials(original)
	var authority_state: Dictionary=scene.army.report()
	var roof_root: Node3D=scene.world.get_node("ReviewBlock2RoofLoggia")
	var roof_identity:=roof_root.get_instance_id()
	var root_count:=scene.world.get_child_count()
	var original_shape_nodes:=scene.world.find_children("*","CollisionShape3D",true,false).size()
	var radius:=-1.0;var height:=-1.0
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D: radius=child.shape.radius;height=child.shape.height
	check("uses real configured hero capsule",is_equal_approx(radius,.29) and is_equal_approx(height,1.8),{"radius":radius,"height":height})
	var before:=ray(Vector3(20,1.4,-40),Vector3(20,1.4,-16));var old_sweep:=sweep(Vector3(20,.05,-40),Vector3(20,.05,-37.1))
	check("baseline flat box really stops ray/capsule before proposed back",not before.is_empty() and before.collider==target and absf(before.position.z+37)<.002 and old_sweep.blocked,{"ray":ray_receipt(before),"capsule":old_sweep})
	for lod in ["near","mid"]:
		var result: Dictionary=Frontage.configure(scene.world,lod)
		check(lod+" review-only installation succeeds",result.get("ok",false),{"reason":result.get("reason",""),"triangles":result.get("triangles",0)})
		if not result.get("ok",false): await finish();return
		await flush()
		check(lod+" effective materials reused by actual resource identity",result.materials==old_materials and result.mesh.mesh.get_surface_count()==3 and result.materials.all(func(value):return value!=null) and result.new_materials==0 and result.new_textures==0 and result.new_lights==0)
		check(lod+" actual collision vertices equal visible world vertices",shape_matches_visible(result),{"faces":result.shape.get_faces().size()/3})
		check(lod+" existing body ID transform metadata and exact broad AABB preserved",target.get_instance_id()==old_id and target.name=="authority-solid-2" and target.collision_layer==1 and target.collision_mask==0 and target.position==Vector3(20,7.5,-28) and target.get_meta("dimensions")==Vector3(18,15,18) and result.shape.get_debug_mesh().get_aabb().is_equal_approx(AABB(Vector3(-9,-7.5,-9),Vector3(18,15,18))))
		check(lod+" other native bodies nav manifest and accepted roof untouched",bodies(true)==other_bodies and JSON.stringify(scene.manifest).sha256_text()==manifest_hash and roof_root.get_instance_id()==roof_identity)
		var duplicate: Dictionary=Frontage.configure(scene.world,lod)
		check(lod+" duplicate configure rejected without allocations",not duplicate.get("ok",false) and scene.world.get_child_count()==root_count+1 and scene.world.find_children("*","CollisionShape3D",true,false).size()==original_shape_nodes)
		assert_contacts(lod)
		# Genuine old-shape corruption: retained exact flat box must expose ghost standoff.
		holder.shape=old_shape;await flush()
		var wrong:=ray(Vector3(20,1.4,-40),Vector3(20,1.4,-16));var wrong_capsule:=sweep(Vector3(20,.05,-40),Vector3(20,.05,-37.1))
		check(lod+" old box negative detects invisible standoff and earlier capsule stop",not wrong.is_empty() and wrong.collider==target and absf(wrong.position.z+37)<.002 and absf(wrong.position.z-(-36.35))>.6 and wrong_capsule.blocked,{"old_ray":ray_receipt(wrong),"capsule":wrong_capsule})
		holder.shape=result.shape;await flush()
		# Lost collision layer must not be admitted as a closed recess.
		target.collision_layer=0;await flush()
		var missing:=ray(Vector3(20,1.4,-40),Vector3(20,1.4,-16))
		check(lod+" disabled solid negative rejects missing blocker",missing.is_empty() or missing.collider!=target,ray_receipt(missing))
		target.collision_layer=1;await flush()
		Frontage.remove(scene.world);await flush()
		var restored:=ray(Vector3(20,1.4,-40),Vector3(20,1.4,-16))
		check(lod+" remove restores exact old resources visibility bodies and ray",holder.shape==old_shape and original.visible and scene.world.get_node_or_null(Frontage.ROOT)==null and scene.world.get_child_count()==root_count and bodies(false)==all_bodies and not restored.is_empty() and restored.collider==target and absf(restored.position.z+37)<.002)
		result.clear()
	check("actual army/nav authority remains held across all disposable controls",scene.army.report()==authority_state and JSON.stringify(scene.manifest).sha256_text()==manifest_hash)
	await finish()
func finish() -> void:
	var after: Dictionary={}
	for path in source_before: after[path]=FileAccess.get_sha256(path)
	check("all owned runtime/candidate sources unchanged by native fixture",source_before==after)
	paused=false;current_scene=null;scene.queue_free();scene=null
	await frames()
	var started:=Time.get_ticks_usec();var previous:=AudioServer.get_time_since_last_mix();var ticks:=0
	while ticks<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1);var now:=AudioServer.get_time_since_last_mix()
		if now+.0002<previous:ticks+=1
		previous=now
	var elapsed:=Time.get_ticks_usec()-started
	await frames()
	check("bounded real mixer cleanup after scene disposal",ticks==2 and elapsed<=250000,{"ticks":ticks,"wait_usec":elapsed})
	var result:={"passed":checks.all(func(item):return item.passed),"count":checks.size(),"checks":checks,"source_before":source_before,"source_after":after,"scope":"Actual native current world, imported effective materials, native hero predictive capsule/rays, exact visible/collision triangles, unchanged planar manifest/other bodies/roof, restoration and finite cleanup. No editor/import, raster, full flight/tether action, online authority, GPU/performance or finished-art acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
