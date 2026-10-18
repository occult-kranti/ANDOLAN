extends SceneTree
## Source-only tiny army resource review: no map, Rama, imported assets or audio.
const Army = preload("res://scripts/lane_army.gd")
const Unit = preload("res://scripts/lane_minion.gd")
var destination := ""
var preflight := false
var checks: Array[Dictionary] = []
var units: Array = []
var world: Node3D
var army: Node3D
var camera: Camera3D
var light: DirectionalLight3D
var atmosphere: WorldEnvironment

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): destination=arg.trim_prefix("--output=")
		if arg=="--preflight": preflight=true
	call_deferred("run")

func check(label: String, value: bool) -> void:
	checks.append({"name":label,"passed":value})

func hash_value(value: Variant) -> String:
	var h:=HashingContext.new()
	h.start(HashingContext.HASH_SHA256)
	h.update(var_to_bytes(value))
	return h.finish().hex_encode()

func material_state(material: Material) -> Dictionary:
	if material==null:return {}
	var result: Dictionary={"class":material.get_class()}
	for property in material.get_property_list():
		if (int(property.usage)&PROPERTY_USAGE_STORAGE)==0:continue
		var value: Variant=material.get(property.name)
		if typeof(value)==TYPE_OBJECT and value!=null:
			if value is Resource:
				value={"class":value.get_class(),"path":value.resource_path,"sha256":FileAccess.get_sha256(value.resource_path) if FileAccess.file_exists(value.resource_path) else ""}
			else:
				check("material property has supported resource transport",false)
				value={"unsupported_class":value.get_class()}
		result[property.name]=value
	return result

func ordered_path(node: Node,parent: Node) -> Array:
	var result: Array=[]
	while node!=parent:
		result.push_front(node.get_index())
		node=node.get_parent()
	return result

func graph_state(unit: Node3D) -> Array:
	var rows: Array=[]
	for node in [unit]+unit.find_children("*","Node3D",true,false):
		var row: Dictionary={"path":ordered_path(node,unit),"class":node.get_class(),"name":node.get_class() if String(node.name).begins_with("@") else String(node.name),"transform":node.transform,"visible":node.visible}
		if node is CollisionShape3D:
			row.shape={"class":node.shape.get_class(),"radius":node.shape.radius,"height":node.shape.height}
		if node is MeshInstance3D:
			var surfaces: Array=[]
			for index in node.mesh.get_surface_count():
				surfaces.append({"arrays_sha256":hash_value(node.mesh.surface_get_arrays(index)),"material":material_state(node.get_active_material(index))})
			row.mesh={"class":node.mesh.get_class(),"aabb":node.mesh.get_aabb(),"surfaces":surfaces}
			row.override=material_state(node.material_override)
			row.overlay=material_state(node.material_overlay)
			row.cast_shadow=node.cast_shadow
			row.visibility_end=node.visibility_range_end
			row.visibility_margin=node.visibility_range_end_margin
		rows.append(row)
	return rows

func state() -> Dictionary:
	var records: Array=[]
	for unit in units:
		records.append({"team":unit.team,"role":unit.role,"health":unit.health,"max_health":unit.max_health,"shield":unit.shield,"shield_until":unit.shield_until,"attack_time":unit.attack_time,"attack_target":unit.attack_target,"alive":unit.alive,"graph":graph_state(unit)})
	return {"units":records,"army_elapsed":army.elapsed,"army_configured":army.configured,"army_accumulator":army._accumulator,"camera_transform":camera.transform,"camera_fov":camera.fov,"camera_near":camera.near,"camera_far":camera.far,"light_transform":light.transform,"light_energy":light.light_energy,"light_color":light.light_color,"light_shadow":light.shadow_enabled,"environment":{"background_mode":atmosphere.environment.background_mode,"background_color":atmosphere.environment.background_color,"ambient_color":atmosphere.environment.ambient_light_color,"ambient_energy":atmosphere.environment.ambient_light_energy,"ambient_source":atmosphere.environment.ambient_light_source},"viewport":root.size}

func frames(count: int) -> void:
	for i in count:
		await process_frame
		if not preflight:await RenderingServer.frame_post_draw

func run() -> void:
	if destination.is_empty():quit(2);return
	DirAccess.make_dir_recursive_absolute(destination)
	root.size=Vector2i(960,540)
	root.content_scale_size=root.size
	world=Node3D.new()
	world.name="ArmyResourceReview"
	root.add_child(world)
	army=Army.new()
	world.add_child(army)
	army.set_physics_process(false)
	for index in 2:
		var unit=Unit.new()
		unit.setup(army,100+index,"sun" if index==0 else "moon","spearman" if index==0 else "bow_guard",1)
		unit.position=Vector3(-1.1 if index==0 else 1.1,0,0)
		army.add_child(unit)
		unit.set_process(false)
		unit.receive_damage(20,"army")
		unit.receive_heal(5)
		unit.apply_shield(30,2)
		unit._update_health_bar()
		if index==1:
			unit.start_attack(unit.position+Vector3(.1,1.3,3))
			unit.attack_time=.32
		unit.update_pose(1.25,1.0)
		units.append(unit)
	var ground:=MeshInstance3D.new()
	var plane:=PlaneMesh.new()
	plane.size=Vector2(12,12)
	ground.mesh=plane
	ground.position.y=-.025
	var stone:=StandardMaterial3D.new()
	stone.albedo_color=Color("5d6868")
	stone.roughness=.9
	ground.material_override=stone
	world.add_child(ground)
	atmosphere=WorldEnvironment.new()
	atmosphere.environment=Environment.new()
	atmosphere.environment.background_mode=Environment.BG_COLOR
	atmosphere.environment.background_color=Color("172039")
	atmosphere.environment.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR
	atmosphere.environment.ambient_light_color=Color("ccd3e1")
	atmosphere.environment.ambient_light_energy=.65
	world.add_child(atmosphere)
	light=DirectionalLight3D.new()
	light.rotation_degrees=Vector3(-48,-28,0)
	light.light_energy=1.15
	light.shadow_enabled=false
	world.add_child(light)
	camera=Camera3D.new()
	world.add_child(camera)
	camera.position=Vector3(4,3.1,6)
	camera.look_at(Vector3(0,1.1,.2))
	camera.fov=36
	camera.near=.1
	camera.far=60
	camera.current=true
	await frames(4)
	check("exact two posed roles with held army clock",units.size()==2 and army.elapsed==0.0 and not army.is_physics_processing())
	check("both health and shield states remain visible",units[0].health==60 and units[1].health==40 and units[0].shield_fill.visible and units[1].shield_fill.visible)
	check("bow arrow is visible in the held released pose",units[1].arrow.visible and units[1].attack_time==.32)
	var projected_ok:=true
	for unit in units:
		for p in [unit.global_position+Vector3.UP*.1,unit.health_fill.global_position+Vector3(.45,.1,0),unit.global_position+Vector3.UP*2.35]:
			projected_ok=projected_ok and not camera.is_position_behind(p) and Rect2(Vector2(12,12),Vector2(936,516)).has_point(camera.unproject_position(p))
	check("body and status sample bounds fit actual viewport",projected_ok)
	var controls:=state()
	var shot: Dictionary={"id":"00-army","file":"00-army.png" if not preflight else "","controls":controls,"controls_sha256":hash_value(controls)}
	var ids: Dictionary={}
	for unit in units:
		for p in [unit.health_fill.get_parent().get_child(0),unit.health_fill,unit.shield_fill]:ids[p.mesh.get_instance_id()]=true
		if unit.arrow:ids[unit.arrow.mesh.get_instance_id()]=true
	shot.status_unique_meshes=ids.size()
	if not preflight:
		var picture:=root.get_texture().get_image()
		picture.convert(Image.FORMAT_RGBA8)
		check("actual screenshot saved",picture.save_png(destination+"/00-army.png")==OK)
		shot.sha256=FileAccess.get_sha256(destination+"/00-army.png")
	check("synchronous image readback preserves complete controls",hash_value(state())==shot.controls_sha256)
	var sources: Dictionary={}
	for path in ["res://scripts/lane_army.gd","res://scripts/lane_minion.gd","res://scripts/lane_infantry_art.gd","res://scripts/lane_vehicle_art.gd","res://scripts/world_render_resources.gd",get_script().resource_path]:sources[path]=FileAccess.get_sha256(path)
	world.free()
	units=[]
	await frames(2)
	var report: Dictionary={"complete":checks.all(func(row):return row.passed),"preflight":preflight,"shots":[shot],"checks":checks,"source_sha256":sources,"scope":"Tiny source-created fixed soldier/bow graph and status-resource pixel comparison. Real unconfigured army owns resource pool; simulation is held. No full-map/Rama/164-bone/authority/gamefeel/GPU/FPS/art-quality claim. No audio nodes."}
	FileAccess.open(destination+("/preflight.json" if preflight else "/capture.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	quit(0 if report.complete else 1)
