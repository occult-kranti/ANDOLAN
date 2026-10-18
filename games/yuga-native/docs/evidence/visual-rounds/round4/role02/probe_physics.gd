extends SceneTree
var scene: Node3D
var player: CharacterBody3D
var samples: Array = []
var controls: Array = []
var checks: Array = []
var sources: Dictionary = {}
var output := "/tmp/r4-ground-physics.json"
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
	var hit := player.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(player.global_position+Vector3.UP*3,player.global_position-Vector3.UP*5,1,[player.get_rid()]))
	var ray := {}
	if not hit.is_empty(): ray = {"point":vec(hit.position),"normal":vec(hit.normal),"collider":str(hit.collider.name)}
	var contacts: Array=[]
	for i in player.get_slide_collision_count():
		var contact:=player.get_slide_collision(i);var collider:=contact.get_collider()
		contacts.append({"position":vec(contact.get_position()),"normal":vec(contact.get_normal()),"collider":str(collider.name) if is_instance_valid(collider) else "missing"})
	samples.append({"slide_contacts":contacts,"native_spring_hit_length_m":player.spring.get_hit_length(),"native_camera_position":vec(player.camera.global_position),"fixture":fixture,"tick":tick,"physics_frame":Engine.get_physics_frames(),"position":vec(player.global_position),"velocity":vec(player.velocity),"on_floor":player.is_on_floor(),"floor_normal":vec(player.get_floor_normal()) if player.is_on_floor() else [],"collision_count":player.get_slide_collision_count(),"down_ray":ray,"traversal_mode":player.traversal.mode,"jump_count":player.jump_count})
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
func free_scene() -> void:
	release_all();scene.queue_free();await process_frame;await process_frame;await process_frame
func pin(path: String) -> void:
	if FileAccess.file_exists(path):sources[path]=FileAccess.get_sha256(path)
func run() -> void:
	for path in ["res://scripts/player.gd","res://scripts/player_traversal.gd","res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/rama_motion.gd","res://assets/heroes/rama-hero.glb","res://assets/environment/lanka_courtyard.glb","res://assets/world/confluence-map.json",get_script().resource_path]:pin(path)
	for asset in ["res://assets/heroes/rama-hero.glb","res://assets/environment/lanka_courtyard.glb"]:
		var cfg:=ConfigFile.new();var fresh:=false
		if cfg.load(asset+".import")==OK:
			var cache:String=cfg.get_value("remap","path","");var md5:=cache.get_basename()+".md5";pin(cache);pin(md5);pin(asset+".import")
			var regex:=RegEx.new();regex.compile("source_md5=\"([a-f0-9]+)\"")
			var match_:RegExMatch=regex.search(FileAccess.get_file_as_string(md5)) if FileAccess.file_exists(md5) else null
			fresh=match_!=null and match_.get_string(1)==FileAccess.get_md5(asset)
		check("existing import fresh "+asset,fresh)
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
	var passed:=checks.all(func(item):return item.passed)
	var report:={"task":"R4-02","passed":passed,"checks":checks,"samples":samples,"controls":controls,"source_sha256":sources,"physics_hz":Engine.physics_ticks_per_second,"scope":"Actual native scene CharacterBody collisions with real Input actions and normal physics. Initial fixture placement only; no per-step root/velocity/pose correction. No rendering, imported skin contact, sloped-ground, continuous visual quality or hardware performance claim."}
	var file:=FileAccess.open(output,FileAccess.WRITE);file.store_string(JSON.stringify(report,"  ")+"\n");print("R4_GROUND ",JSON.stringify({"passed":passed,"checks":checks.size(),"samples":samples.size()}));quit(0 if passed else 1)
