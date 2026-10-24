extends "res://tools/map-reuse-placement/capture.gd"
## Actual canonical caller, old-node identities and all map routes; no renderer.
func route_sweeps()->Array:
	var failures:Array=[];var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var capsule:CapsuleShape3D
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D:capsule=child.shape.duplicate()
	var routes:Array=scene.manifest.lanes.duplicate(true);routes.append_array(scene.manifest.rotations)
	for route in routes:
		var points:Array=route.points.duplicate(true)
		if route.get("closed",false):points.append(points[0])
		for i in range(points.size()-1):
			var a:Array=points[i];var b:Array=points[i+1];var start:=Vector3(a[0],.95,a[2]);var finish:=Vector3(b[0],.95,b[2])
			var q:=PhysicsShapeQueryParameters3D.new();q.shape=capsule;q.transform=Transform3D(Basis.IDENTITY,start);q.motion=finish-start;q.margin=.001;q.collision_mask=1
			var cast:=space.cast_motion(q)
			if cast.size()!=2 or cast[0]<.9999:failures.append({"route":route.id,"segment":i,"fraction":cast[0] if cast.size()==2 else null})
	return failures
func node_ids()->Dictionary:
	var result:Dictionary={}
	for node in scene.authority_bodies+scene.native_platform_bodies:result[str(node.get_path())]=node.get_instance_id()
	var relics:Node3D=scene.world.get_node("TraversalRelics")
	for anchor in scene.manifest.traversal.anchors:result[anchor.id]=relics.get_node(NodePath(anchor.id)).get_instance_id()
	return result
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	if not output.is_absolute_path() or FileAccess.file_exists(output):push_error("Fresh absolute integration report required");quit(1);return
	var Helper:Script=load("res://scripts/lanka_lane_gate.gd")
	if Helper==null:push_error("Canonical helper not yet integrated");quit(1);return
	scene=load("res://scenes/confluence_world.tscn").instantiate();scene.set("lanka_lane_gate_enabled",false);scene.set("lanka_water_garden_enabled",false);root.add_child(scene);current_scene=scene
	await physics_frame;await physics_frame
	check("explicit legacy opt-out retains ready original world",scene.world_ready and not scene.world.has_node("LankaLaneGate") and not scene.lanka_lane_gate_report.enabled)
	scene.set_paused(false);scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world)
	var original_ids:=node_ids();gather_bodies(scene.world,original_body_ids)
	placement_result=Helper.build(scene.world)
	check("actual production helper builds one accepted native gate",placement_result.get("enabled",false),placement_result.get("report",{}))
	if not placement_result.get("enabled",false):await finish_integrated();return
	var army_before:Dictionary=scene.manifest.duplicate(true)
	var prepared:Dictionary=Helper.prepare_army_manifest(scene.manifest,placement_result.root)
	check("army copy includes10ground footprints and original manifest stays unchanged",prepared.get("ok",false) and prepared.get("boxes",[]).size()==10 and scene.manifest==army_before)
	check("existing army configure uses copied pier footprints",prepared.get("ok",false) and scene.army.configure(prepared.manifest,scene.player))
	hold_callbacks(scene.world)
	await process_frame;await physics_frame;await physics_frame
	original_body_ids.clear();gather_bodies(scene.world,original_body_ids);original_body_ids.erase(placement_result.body.get_instance_id())
	check("offline army pier cover blocks and aperture stays clear",not scene.army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)) and scene.army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)))
	await context_probe()
	var space:PhysicsDirectSpaceState3D=scene.world.get_world_3d().direct_space_state
	var actual_army_failures:Array=[];var actual_army_samples:=0
	for role in Unit.STATS:
		for x in [-41.2,-40.0,-38.8]:
			for step in 41:
				var z:float=-64+step*.5;actual_army_samples+=1
				if not capsule_hits(space,x,z,Unit.STATS[role].radius,Unit.STATS[role].height).is_empty():actual_army_failures.append([role,x,z])
	check("all existing role radii at actual1.2metre formation offsets clear section",actual_army_failures.is_empty(),{"samples":actual_army_samples,"failures":actual_army_failures})
	var camera_failed:Array=[];var camera_samples:=0
	var actual_camera_shape:Shape3D=scene.player.spring.shape.duplicate()
	for direction in [-1,1]:
		for step in 73:
			var z:float=-72+step*.5;var q:=PhysicsShapeQueryParameters3D.new();q.shape=actual_camera_shape;q.transform=Transform3D(Basis.IDENTITY,Vector3(-40+direction*.65,1.54,z));q.motion=Vector3(0,.349416,direction*3.482513);q.collision_mask=1
			var cast:=space.cast_motion(q);camera_samples+=1
			if cast[0]<.999:camera_failed.append([direction,z,cast[0]])
	check("actual SpringArm0.18sphere and3.5metre shoulder path clear bothdirections",camera_failed.is_empty(),{"samples":camera_samples,"sphere_radius":actual_camera_shape.radius,"failures":camera_failed})
	check("eight authority/decks and ten anchor instances remain exactly unchanged",original_ids==node_ids() and scene.authority_bodies.size()==8 and scene.native_platform_bodies.size()==8)
	var failures:=route_sweeps();check("actual full-map capsule sweeps clear all three lanes and every rotation",failures.is_empty(),failures)
	var old:=StaticBody3D.new();var holder:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(26,11,10);holder.shape=box;old.position=Vector3(-40,5.5,-54);old.add_child(holder);scene.world.add_child(old)
	await physics_frame;await physics_frame
	failures=route_sweeps();check("negative broad gate AABB breaks full-map west lane sweep",not failures.is_empty() and failures.any(func(row):return row.route==0),failures)
	old.free();await physics_frame;await physics_frame
	check("all map capsule routes restored after negative removal",route_sweeps().is_empty())
	var report:Dictionary=placement_result.report.duplicate(true);placement_result.clear();scene.queue_free();await process_frame;await process_frame;await physics_frame
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene;await physics_frame;await physics_frame
	check("fresh default canonical caller enables exact one gate and report",scene.world_ready and scene.lanka_lane_gate_enabled and scene.lanka_lane_gate_report==report and scene.world.has_node("LankaLaneGate") and scene.world.get_node("LankaLaneGate").find_children("*","StaticBody3D",true,false).size()==1)
	check("default canonical construction retains original authority and deck arrays",scene.authority_bodies.size()==8 and scene.native_platform_bodies.size()==8)
	check("default caller retains gate10/garden4/relay9 private footprints without mutating manifest",scene.army.boxes.size()==scene.manifest.authority_collision_boxes.size()+scene.manifest.traversal.native_collision_boxes.size()+10+4+scene.relays.art.collision_boxes().size() and scene.manifest.traversal.native_collision_boxes.size()==8 and not scene.army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)) and scene.army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)),{"army_boxes":scene.army.boxes.size(),"source_native_boxes":scene.manifest.traversal.native_collision_boxes.size(),"pier_clear":scene.army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)),"opening_clear":scene.army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38))})
	check("duplicate canonical configure cannot add another body",not Helper.build(scene.world).enabled and scene.world.get_node("LankaLaneGate").get_child_count()==12)
	scene.set_paused(false);scene.set_process(false);scene.set_physics_process(false);hold_callbacks(scene.world);await physics_frame
	check("fresh default integration preserves all full-map routes",route_sweeps().is_empty())
	await finish_integrated()
func finish_integrated()->void:
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"schema":1,"passed":passed,"checks":checks,"engine":Engine.get_version_info(),"helper_sha256":FileAccess.get_sha256("res://scripts/lanka_lane_gate.gd"),"world_sha256":FileAccess.get_sha256("res://scripts/confluence_world.gd"),"asset_sha256":FileAccess.get_sha256("res://assets/world/lanka-lane-gate.scn"),"scope":"Actual canonical caller and opt-out, all three lane and rotation capsule sweeps, preserved8authority/8deck/10anchor identity, native body/cache duplication, all-role probes and injected broad-box counterexample. Headless, no rendering/online/performance claim."},"  ")+"\n")
	if is_instance_valid(scene):scene.queue_free()
	for unused in 8:await process_frame
	print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
