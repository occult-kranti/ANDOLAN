extends SceneTree
var scene: Node3D
var player: CharacterBody3D
var samples: Array = []
var controls: Array = []
var checks: Array = []
var sources: Dictionary = {}
var output := "/tmp/r4-imported-contact.json"
var geometry: Array = []
var live_parts: Array = []
var pose_sample: Dictionary = {}
var signal_count := 0
var rig: Skeleton3D
var geometry_sets: Array = []
var geometry_set := -1
var fixture := ""
var tick := 0
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func vec(v: Vector3) -> Array: return [v.x,v.y,v.z]
func check(label: String, condition: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":condition,"details":details})
	print("PASS " if condition else "FAIL ",label," ",JSON.stringify(details))
func record() -> void:
	if pose_sample.is_empty(): return
	var hit := player.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(player.global_position+Vector3.UP*3,player.global_position-Vector3.UP*5,1,[player.get_rid()]))
	var ray := {}
	if not hit.is_empty(): ray = {"point":vec(hit.position),"normal":vec(hit.normal),"collider":str(hit.collider.name)}
	var contacts: Array=[]
	for i in player.get_slide_collision_count():
		var contact:=player.get_slide_collision(i);var collider:=contact.get_collider()
		contacts.append({"position":vec(contact.get_position()),"normal":vec(contact.get_normal()),"collider":str(collider.name) if is_instance_valid(collider) else "missing"})
	samples.append({"final_pose":pose_sample.duplicate(true),"geometry_set":geometry_set,"record_physics_frame":Engine.get_physics_frames(),"slide_contacts":contacts,"native_spring_hit_length_m":player.spring.get_hit_length(),"native_camera_position":vec(player.camera.global_position),"fixture":fixture,"tick":tick,"physics_frame":Engine.get_physics_frames(),"position":vec(player.global_position),"velocity":vec(player.velocity),"on_floor":player.is_on_floor(),"floor_normal":vec(player.get_floor_normal()) if player.is_on_floor() else [],"collision_count":player.get_slide_collision_count(),"down_ray":ray,"traversal_mode":player.traversal.mode,"jump_count":player.jump_count})
func advance(count: int) -> void:
	for _i in count:
		await physics_frame
		await process_frame
		tick+=1
		record()
func release_all() -> void:
	for action in ["move_forward","move_back","move_left","move_right","jump","sprint","fire"]:Input.action_release(action)
func press(action: String) -> void:
	Input.action_press(action);controls.append({"fixture":fixture,"tick":tick,"kind":"press","action":action})
func release(action: String) -> void:
	Input.action_release(action);controls.append({"fixture":fixture,"tick":tick,"kind":"release","action":action})
func position_actor(position_: Vector3) -> void:
	release_all();player.global_position=position_;player.velocity=Vector3.ZERO;player.yaw=0;player.pitch=0;player._update_camera();player.last_finite_position=position_;player.reset_physics_interpolation();player.visual.reset_physics_interpolation()
	controls.append({"fixture":fixture,"tick":tick,"kind":"initial_position","position":vec(position_)})
func route_leg(action: String, axis: int, threshold: float, direction: float) -> void:
	press(action)
	var reached := false
	for _i in 180:
		await advance(1)
		if (player.global_position[axis]-threshold)*direction>=0:
			reached=true;break
	release(action)
	await advance(20)
	check(fixture+" route "+action+" reaches threshold and stops",reached and Vector2(player.velocity.x,player.velocity.z).length()<.01 and player.is_on_floor(),{"position":vec(player.global_position),"velocity":vec(player.velocity),"floor_normal":vec(player.get_floor_normal())})
func jump_case(support: float) -> void:
	var old_count: int=player.jump_count
	press("jump");await advance(1);release("jump")
	var maximum := player.global_position.y
	var airborne := not player.is_on_floor()
	for _i in 90:
		await advance(1);maximum=maxf(maximum,player.global_position.y);airborne=airborne or not player.is_on_floor()
	check(fixture+" real jump lands on expected support",airborne and player.jump_count==old_count+1 and maximum-support>1.0 and player.is_on_floor() and absf(player.global_position.y-support)<.002 and player.get_floor_normal().dot(Vector3.UP)>.9999,{"maximum_root_y":maximum,"apex_above_support_m":maximum-support,"landing":vec(player.global_position),"floor_normal":vec(player.get_floor_normal()),"jump_count_delta":player.jump_count-old_count})
func load_scene(path: String) -> void:
	scene=load(path).instantiate();root.add_child(scene)
	await process_frame;await process_frame;await process_frame
	player=scene.player
	rig=player.rama_motion.rig
	cache_imported_geometry()
	player.rama_motion.modification_processed.connect(observe_final_pose)
func free_scene() -> void:
	release_all();scene.queue_free();await process_frame;await process_frame;await process_frame
func pin(path: String) -> void:
	if FileAccess.file_exists(path):sources[path]=FileAccess.get_sha256(path)
func matrix(t: Transform3D) -> Array: return [vec(t.basis.x),vec(t.basis.y),vec(t.basis.z),vec(t.origin)]
func cache_imported_geometry() -> void:
	geometry=[];live_parts=[];pose_sample={}
	for node in player.visual.find_children("*","MeshInstance3D",true,false):
		if not node.mesh or not node.skin: continue
		var binds: Array=[]
		for index in node.skin.get_bind_count():
			var name_: String=String(node.skin.get_bind_name(index))
			var bone: int=rig.find_bone(name_)
			if bone<0: bone=node.skin.get_bind_bone(index);name_=String(rig.get_bone_name(bone))
			binds.append({"name":name_,"bone":bone,"inverse":matrix(node.skin.get_bind_pose(index))})
		for surface in node.mesh.get_surface_count():
			var arrays: Array=node.mesh.surface_get_arrays(surface)
			var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
			var bones: Variant=arrays[Mesh.ARRAY_BONES]
			var weights: Variant=arrays[Mesh.ARRAY_WEIGHTS]
			if bones==null or weights==null: continue
			var slots: int=bones.size()/vertices.size()
			var colors: Variant=arrays[Mesh.ARRAY_COLOR]
			var material: Material=node.get_active_material(surface)
			var selected: Array=[]
			for index in vertices.size():
				if vertices[index].y>=.30: continue
				var bw: Array=[];var sums:={"L":0.0,"R":0.0}
				for slot in slots:
					var weight: float=weights[index*slots+slot]
					var bind: int=bones[index*slots+slot]
					bw.append([bind,weight])
					var name_: String=binds[bind].name
					if name_.begins_with("foot") or name_.begins_with("toe"):
						for side in ["L","R"]:
							if name_.ends_with("."+side): sums[side]+=weight
				var side: String="L" if sums.L>.5 else "R" if sums.R>.5 else ""
				if side.is_empty(): continue
				selected.append({"index":index,"side":side,"rest":vec(vertices[index]),"bind_weights":bw,"alpha":colors[index].a if colors!=null else 0.0})
			if selected.is_empty(): continue
			geometry.append({"node":String(player.visual.get_path_to(node)),"surface":surface,"material":material.resource_name,"material_class":material.get_class(),"binds":binds,"selected":selected,"blend_shape_count":node.mesh.get_blend_shape_count(),"mesh_to_rig":matrix(rig.global_transform.affine_inverse()*node.global_transform)})
			live_parts.append({"node":node,"material":material})
	geometry_sets.append(geometry.duplicate(true));geometry_set=geometry_sets.size()-1
func observe_final_pose() -> void:
	var poses: Dictionary={}
	for index in rig.get_bone_count(): poses[String(rig.get_bone_name(index))]=matrix(rig.get_bone_global_pose(index))
	var parts: Array=[]
	for part in live_parts:
		var secondary:=Vector3.ZERO
		if part.material is ShaderMaterial:
			var value: Variant=part.material.get_shader_parameter("secondary_offset")
			if value is Vector3: secondary=value
		parts.append({"visible":part.node.is_visible_in_tree(),"secondary_offset":vec(secondary)})
	var targets: Dictionary={}
	for side in ["L","R"]:targets[side]=vec(player.rama_motion.foot_targets[side])
	var capsules: Array=[]
	for child in player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:
			capsules.append({"transform":matrix(child.global_transform),"radius":child.shape.radius,"height":child.shape.height})
	pose_sample={"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames(),"rig_global":matrix(rig.global_transform),"player_global":matrix(player.global_transform),"bones":poses,"parts":parts,"motion":player.rama_motion.diagnostics(),"foot_targets":targets,"capsules":capsules,"lod":player.rama_lod.report(),"camera_transform":matrix(player.camera.global_transform),"camera_fov":player.camera.fov,"camera_near":player.camera.near,"viewport":[root.size.x,root.size.y]}
	signal_count+=1
func run() -> void:
	root.size=Vector2i(1280,960);root.content_scale_size=Vector2i(1280,960)
	for path in ["res://scripts/player.gd","res://scripts/player_traversal.gd","res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/rama_motion.gd","res://scripts/rama_secondary_motion.gd","res://scripts/rama_surface_materials.gd","res://scripts/rama_surface_finish.gd","res://scripts/rama_lod_binding.gd","res://scripts/rama_visual_lod.gd","res://shaders/rama_secondary_cloth.gdshader","res://assets/animations/rama_hero_motion.tres","res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb","res://assets/environment/lanka_courtyard.glb","res://assets/world/confluence-map.json",get_script().resource_path]:pin(path)
	for asset in ["res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero-mid.glb","res://assets/heroes/rama-hero-far.glb","res://assets/environment/lanka_courtyard.glb"]:
		var cfg:=ConfigFile.new();var fresh:=false
		if cfg.load(asset+".import")==OK:
			var cache:String=cfg.get_value("remap","path","");var md5:=cache.get_basename()+".md5";pin(cache);pin(md5);pin(asset+".import")
			var regex:=RegEx.new();regex.compile("source_md5=\"([a-f0-9]+)\"")
			var match_:RegExMatch=regex.search(FileAccess.get_file_as_string(md5)) if FileAccess.file_exists(md5) else null
			fresh=match_!=null and match_.get_string(1)==FileAccess.get_md5(asset)
		check("existing import fresh "+asset,fresh)
		if not fresh: quit(2);return
	await load_scene("res://scenes/courtyard.tscn");scene.start_training();scene.ui.hide();fixture="courtyard-ground-route";position_actor(Vector3(0,.0001,12));await advance(12)
	check(fixture+" initial grounding",player.is_on_floor() and absf(player.global_position.y)<.002)
	await route_leg("move_forward",2,6,-1)
	await route_leg("move_right",0,3,1)
	await route_leg("move_back",2,9,1)
	fixture="courtyard-gallery-jump";scene.reset_training();scene.start_training();position_actor(Vector3(19,.4400999976,-1));await advance(12)
	check(fixture+" initial grounding",player.is_on_floor() and absf(player.global_position.y-.44)<.002,{"position":vec(player.global_position),"floor_normal":vec(player.get_floor_normal())})
	await jump_case(.44);await free_scene()
	await load_scene("res://scenes/confluence_world.tscn");scene.set_paused(false);fixture="confluence-west-deck-fall-jump";scene.teleport_to(Vector3(-20,9.5001,-88),0);player.active=true;await advance(70)
	check(fixture+" actual gravity landing at8m",player.is_on_floor() and absf(player.global_position.y-8)<.002 and player.get_floor_normal().dot(Vector3.UP)>.9999,{"position":vec(player.global_position),"floor_normal":vec(player.get_floor_normal())})
	await jump_case(8);await free_scene()
	var stable:=true
	for path in sources:stable=stable and FileAccess.get_sha256(path)==sources[path]
	check("source and imported cache bytes unchanged",stable)
	check("final modifier callbacks supplied every sample",signal_count>samples.size() and samples.size()>400,{"signals":signal_count,"samples":samples.size()})
	check("sample poses share current physics frame",samples.all(func(x):return x.final_pose.physics_frame==x.record_physics_frame))
	var passed:=checks.all(func(item):return item.passed)
	var report:={"task":"R4-12","geometry_sets":geometry_sets,"signal_count":signal_count,"engine":Engine.get_version_info(),"renderer":RenderingServer.get_current_rendering_method(),"passed":passed,"checks":checks,"samples":samples,"controls":controls,"source_sha256":sources,"physics_hz":Engine.physics_ticks_per_second,"scope":"Actual existing imported arrays and final modifier snapshots with real Input and native physics. Actual GPU vertices, framebuffer feet/shadows, slope contact, full transition lifecycle and hardware FPS remain unmeasured. No pose/root/velocity corrections."}
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");print("R4_IMPORTED_CONTACT ",JSON.stringify({"passed":passed,"checks":checks.size(),"samples":samples.size()}));quit(0 if passed else 1)
