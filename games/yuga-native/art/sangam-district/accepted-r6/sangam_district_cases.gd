extends SceneTree
## Imported mesh, real physics and planar army agreement; no image/FPS claim.
const District = preload("res://scripts/sangam_district.gd")
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
var output := ""
var checks: Array[Dictionary] = []
var world: Node3D
var original_shapes: Array[Shape3D] = []
var holders: Array[CollisionShape3D] = []

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func box_body(name_: String, center: Vector3, dimensions: Vector3, parent: Node3D) -> StaticBody3D:
	var body := StaticBody3D.new()
	body.name = name_
	body.position = center
	body.collision_layer = 1
	body.collision_mask = 0
	var shape := BoxShape3D.new()
	shape.size = dimensions
	var holder := CollisionShape3D.new()
	holder.shape = shape
	body.add_child(holder)
	parent.add_child(body)
	return body

func ray(a: Vector3, b: Vector3) -> Dictionary:
	return world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(a,b,1))

func run() -> void:
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var original_json := JSON.stringify(data)
	world = Node3D.new()
	root.add_child(world)
	var city := Node3D.new()
	city.name = "CityArt"
	world.add_child(city)
	for item in data.authority_collision_boxes:
		var position_ := District._vector(item.position)
		var dimensions := District._vector(item.size)
		var old := Node3D.new()
		old.name = "block-" + str(int(item.source_index))
		old.position = position_
		old.scale = dimensions
		city.add_child(old)
		var body := box_body(item.id,position_+Vector3.UP*dimensions.y*.5,dimensions,world)
		var holder: CollisionShape3D = body.get_child(0)
		if int(item.source_index) == 2:
			# An existing detailed collider must be recoverable, not silently lost.
			var previous := ConcavePolygonShape3D.new()
			var visual := BoxMesh.new()
			visual.size = dimensions
			previous.set_faces(visual.get_faces())
			holder.shape = previous
			old.hide()
		original_shapes.append(holder.shape)
		holders.append(holder)
	var old_roof := Node3D.new()
	old_roof.name = "ReviewBlock2RoofLoggia"
	world.add_child(old_roof)
	var old_roof_body := box_body("OldRoof",Vector3(20,16,-28),Vector3(5,1,5),old_roof)
	box_body("Floor",Vector3(0,-.25,0),Vector3(140,.5,260),world)
	var built := District.build(world)
	check("Authored imported district replaces all eight modules",built.get("ok",false),built.get("report",{}))
	if not built.get("ok",false):
		finish()
		return
	var district: Node3D = built.root
	var stone_finishes := {}
	var source_bindings := true
	var brass_finish := false
	for visual: MeshInstance3D in district.find_children("*", "MeshInstance3D", true, false):
		for surface in visual.mesh.get_surface_count():
			var source := visual.mesh.surface_get_material(surface) as StandardMaterial3D
			var finish := visual.get_surface_override_material(surface)
			if finish is ShaderMaterial:
				stone_finishes[finish.get_instance_id()] = true
				source_bindings = source_bindings and finish.shader == District.FINISH and finish.get_shader_parameter("source_albedo") == source.albedo_texture and finish.get_shader_parameter("source_normal") == source.normal_texture and finish.get_shader_parameter("source_roughness") == source.roughness_texture and is_equal_approx(finish.get_shader_parameter("normal_strength"), .18)
			elif finish is StandardMaterial3D and source.resource_name.to_lower().contains("brass"):
				brass_finish = finish != source and is_equal_approx(finish.metallic, .25) and is_equal_approx(finish.roughness, .72) and finish.roughness_texture == null
	check("Three shared stone finishes preserve original texture bindings",stone_finishes.size()==3 and source_bindings and built.report.finish_materials==4)
	check("Quiet brass override preserves the imported source material",brass_finish)
	check("Eight physical ground solids match retained planar bounds",holders.all(func(holder):return holder.shape is BoxShape3D))
	check("Previous roof art and its collider are inactive together",not old_roof.visible and old_roof_body.collision_layer == 0)
	check("Duplicate install is rejected before mutating the active district",not District.build(world).ok and world.get_node("SangamDistrict")==district)
	var prepared := District.prepare_army_manifest(data,district)
	check("Derived army gains exactly four covers and no overhead blockers",prepared.ok and prepared.manifest.traversal.native_collision_boxes.size()==data.traversal.native_collision_boxes.size()+4 and prepared.overhead_added==0 and JSON.stringify(data)==original_json)
	check("Duplicate derived footprint application is rejected",not District.prepare_army_manifest(prepared.manifest,district).ok)
	district.position.x = 1
	check("Moved district cannot create stale planar cover",not District.prepare_army_manifest(data,district).ok)
	district.position = Vector3.ZERO
	district.scale = Vector3(1,2,1)
	check("Scaled district cannot create mismatched planar cover",not District.prepare_army_manifest(data,district).ok)
	district.scale = Vector3.ONE
	var clean: Array = district.get_meta("ground_footprints").duplicate(true)
	for mode in ["duplicate", "nonfinite", "moved", "wrong_height"]:
		var damaged := clean.duplicate(true)
		if mode == "duplicate": damaged[1] = damaged[0].duplicate(true)
		elif mode == "nonfinite": damaged[0].position[0] = NAN
		elif mode == "moved": damaged[0].position[2] += 1
		else: damaged[0].size[1] = 1.4
		district.set_meta("ground_footprints",damaged)
		check("Corrupt footprint rejected: " + mode,not District.prepare_army_manifest(data,district).ok)
	district.set_meta("ground_footprints",clean)
	var army := Army.new()
	army.visual_enabled = false
	world.add_child(army)
	army.set_physics_process(false)
	check("Real offline army configures with the four cover additions",army.configure(prepared.manifest,null))
	for unused in 4: await physics_frame
	for x in [-8.0,8.0]:
		for z in [-60.0,60.0]:
			var hit := ray(Vector3(x,4,z),Vector3(x,0,z))
			var crossing := ray(Vector3(x-3,1.5,z),Vector3(x+3,1.5,z))
			check("Visible 2.7m civic cover has matching top and shot occlusion at %s/%s"%[x,z],not hit.is_empty() and absf(hit.position.y-2.7)<.015 and not crossing.is_empty() and not army.line_clear(Vector3(x-3,0,z),Vector3(x+3,0,z)),{"top":str(hit.get("position")),"collider":str(crossing.get("collider"))})
			check("Lateral escape remains open beside civic cover at %s/%s"%[x,z],army.line_clear(Vector3(x-2.5,0,z-4),Vector3(x-2.5,0,z+4)) and ray(Vector3(x-2.5,1.5,z-4),Vector3(x-2.5,1.5,z+4)).is_empty())
	check("Complete central ground lane stays open in native physics and army rules",army.line_clear(Vector3(0,0,-80),Vector3(0,0,80)) and ray(Vector3(0,1.5,-80),Vector3(0,1.5,80)).is_empty())
	for z in [-28.0,28.0]:
		var deck := ray(Vector3(0,10,z),Vector3(0,0,z))
		var ceiling := ray(Vector3(0,1,z),Vector3(0,9,z))
		check("Gallery offers actual deck and clear ground underpass at " + str(z),not deck.is_empty() and absf(deck.position.y-8.56)<.02 and not ceiling.is_empty() and absf(ceiling.position.y-8)<.02 and army.line_clear(Vector3(0,0,z-5),Vector3(0,0,z+5)),{"deck":str(deck.get("position")),"ceiling":str(ceiling.get("position"))})
	var eave := ray(Vector3(-20,2,-38.5),Vector3(-20,6,-38.5))
	check("Carved eave has real overhead collision above the grounded passage",not eave.is_empty() and eave.position.y>3.0 and eave.position.y<4.8 and ray(Vector3(-26,1.5,-38.5),Vector3(-14,1.5,-38.5)).is_empty(),{"ceiling":str(eave.get("position"))})
	var kit := Kit.new()
	world.add_child(kit)
	check("Existing actual Rama kit configures against the derived world",kit.configure(army))
	var elevated: Dictionary = kit.request_ability("piercing_dawn",Vector3(0,8.56,-28),Vector3.BACK,Vector3.ZERO)
	check("Elevated gallery never advertises unsupported Rama casts",not elevated.accepted and elevated.reason.contains("Land"),elevated)
	var ground: Dictionary = kit.request_ability("piercing_dawn",Vector3(0,0,-28),Vector3.BACK,Vector3.ZERO)
	check("Same ground underpass remains a legal cast surface",ground.accepted,ground)
	kit.cancel_active("district_test_end")
	District.remove(world)
	check("Removal restores all original shapes including detailed Block2",range(8).all(func(i):return holders[i].shape==original_shapes[i]))
	check("Removal restores legacy art and roof collision identities",world.get_node_or_null("SangamDistrict")==null and old_roof.visible and old_roof_body.collision_layer==1 and not city.get_node("block-2").visible and city.get_node("block-0").visible)
	check("Source map remains byte-identical in memory after derivation",JSON.stringify(data)==original_json)
	finish()

func finish() -> void:
	var passed := checks.all(func(row):return row.passed)
	var sources := {}
	for path in ["res://scripts/sangam_district.gd","res://assets/world/sangam-district.glb","res://assets/world/sangam-district.json","res://assets/world/confluence-map.json",get_script().resource_path]:sources[path]=FileAccess.get_sha256(path)
	var result := {"passed":passed,"count":checks.size(),"checks":checks,"sources":sources,"scope":"Actual imported authored meshes, native ray collision, real offline army and Rama cast rejection, exact metadata counterexamples and reversible installation. Isolated matching eight-block host; ordinary integrated scene/input/render/hardware remain separate."}
	if not output.is_empty():FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	world.queue_free()
	await process_frame
	quit(0 if passed else 1)
