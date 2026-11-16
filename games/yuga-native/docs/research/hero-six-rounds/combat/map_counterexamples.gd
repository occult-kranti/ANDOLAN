extends SceneTree
## Independent proposal probes, not acceptance of the unbuilt district.
const Army = preload("res://scripts/lane_army.gd")
var checks: Array=[]
func _initialize() -> void:call_deferred("run")
func check(label: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	if not passed:push_error("MAP PROPOSAL REVIEW: "+label)
func run() -> void:
	var map: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var baseline:=JSON.stringify(map)
	var derived:=map.duplicate(true)
	for x in [-8.0,8.0]:
		for z in [-60.0,60.0]:
			derived.traversal.native_collision_boxes.append({"id":"proposal_planter_%s_%s"%[x,z],"position":[x,0,z],"size":[3,1.4,6]})
	var army=Army.new();army.visual_enabled=false;root.add_child(army);army.set_physics_process(false)
	check("four_planters_preserve_actual_lane_configuration",army.configure(derived,null))
	check("proposal_does_not_mutate_base_manifest",JSON.stringify(map)==baseline and derived.authority_collision_boxes==map.authority_collision_boxes)
	check("center_lane_remains_clear_between_planters",army.line_clear(Vector3(0,0,-70),Vector3(0,0,70),.65))
	check("planter_blocks_ground_cross_shot",not army.line_clear(Vector3(4,1,-60),Vector3(12,1,-60),.22))
	var upper_from:=Vector3(4,2.0,-60);var upper_to:=Vector3(12,2.0,-60)
	var planar_stops: bool=not army.line_clear(upper_from,upper_to,.22)
	var world:=Node3D.new();root.add_child(world)
	var body:=StaticBody3D.new();body.position=Vector3(8,.7,-60);body.collision_layer=1;body.collision_mask=0
	var holder:=CollisionShape3D.new();var shape:=BoxShape3D.new();shape.size=Vector3(3,1.4,6);holder.shape=shape;body.add_child(holder);world.add_child(body)
	await physics_frame;await physics_frame
	var upper_hit: Dictionary=world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(upper_from,upper_to,1))
	var lower_hit: Dictionary=world.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(Vector3(4,1,-60),Vector3(12,1,-60),1))
	check("low_cover_counterexample_is_real",planar_stops and upper_hit.is_empty() and not lower_hit.is_empty(),{"planar_army_stops_at_2m":planar_stops,"native_ray_at_2m_hits":not upper_hit.is_empty(),"native_ray_at_1m_hits":not lower_hit.is_empty(),"meaning":"Low cover needs visually solid height matching current planar shot behavior; this does not approve the1.4m proposal."})
	var overhead:=derived.duplicate(true)
	overhead.traversal.native_collision_boxes.append({"id":"proposal_overhead_wrong_army_admission","position":[0,8,-28],"size":[22,1,4]})
	var negative=Army.new();negative.visual_enabled=false;root.add_child(negative);negative.set_physics_process(false)
	check("overhead_in_planar_manifest_rejected_by_real_army",not negative.configure(overhead,null),{"meaning":"Overhead must stay native-physics-only; Y does not exempt its planar footprint."})
	var source_sha256: Dictionary={}
	for path in [get_script().resource_path,"res://scripts/lane_army.gd","res://scripts/rama_ability_kit.gd","res://assets/world/confluence-map.json"]:source_sha256[path]=FileAccess.get_sha256(path)
	var passed:=checks.all(func(row):return row.passed)
	var report:={"task_id":"YUGA-HERO-6R","round":5,"passed":passed,"checks":checks,"source_sha256":source_sha256,"scope":"Independent proposed-geometry counterexamples with actual army and Godot physics. Does not accept an unbuilt district, camera, art or human route design."}
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path:=argument.trim_prefix("--report=");DirAccess.make_dir_recursive_absolute(path.get_base_dir());FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("Map proposal counterexamples: %d/%d"%[checks.filter(func(row):return row.passed).size(),checks.size()])
	negative.free();army.free();world.free();quit(0 if passed else 1)
