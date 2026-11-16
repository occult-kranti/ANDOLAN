extends SceneTree
const Map = preload("res://scripts/tactical_map.gd")
var checks: Array = []
var source_sha256 := {}

func _initialize() -> void:
	call_deferred("run")

func check(id: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"name":id,"passed":passed,"evidence":evidence})
	if not passed: print("FAIL ",id," ",evidence)

func ray(map: Node3D, from: Vector3, to: Vector3) -> Dictionary:
	return map.get_world_3d().direct_space_state.intersect_ray(PhysicsRayQueryParameters3D.create(from,to,1))

func run() -> void:
	for path in ["res://scripts/tactical_map.gd","res://assets/tactical/map.json","res://tests/tactical/map_cases.gd","res://assets/world/sangam-district.glb","res://assets/world/sangam-district.json","res://shaders/sangam_masonry.gdshader"]:
		source_sha256[path] = FileAccess.get_sha256(path)
	var map := Map.new()
	root.add_child(map)
	await physics_frame
	await physics_frame
	check("map_builds_original_two_site_layout",map.report().ready and map.sites.size()==2,map.report())
	check("rich_imported_geometry_present",map.report().buildings==4 and map.report().reused_meshes>=17 and map.report().triangles>100000)
	check("legacy_army_not_instantiated",map.find_children("*Army*","",true,false).is_empty())
	check("buy_barrier_blocks_bullet",not ray(map,Vector3(0,1.6,-46),Vector3(0,1.6,-42)).is_empty())
	var capsule := CapsuleShape3D.new()
	capsule.height = 1.8
	capsule.radius = .4
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = capsule
	query.collision_mask = 1
	query.margin = .01
	query.transform = Transform3D(Basis.IDENTITY,Vector3(0,.98,-46))
	query.motion = Vector3(0,0,4)
	check("buy_barrier_blocks_player_sweep",map.get_world_3d().direct_space_state.cast_motion(query)[0]<.999)
	map.set_buy_barriers(false)
	await physics_frame
	check("live_barrier_releases_bullet",ray(map,Vector3(0,1.6,-46),Vector3(0,1.6,-42)).is_empty())
	check("live_barrier_releases_player_sweep",map.get_world_3d().direct_space_state.cast_motion(query)[0]>.999)
	check("spawn_to_spawn_sightline_has_real_cover",not ray(map,Vector3(0,1.6,-54),Vector3(0,1.6,54)).is_empty())
	var route_lengths := {}
	for attack_team in ["sun","moon"]:
		for team in ["sun","moon"]:
			for index in 5:
				var start: Vector3 = map.spawn(team,index,attack_team)
				check("spawn_valid_%s_%s_%d"%[attack_team,team,index],start.is_finite() and map.bounds.has_point(Vector2(start.x,start.z)) and map.is_buy_zone(start,team,attack_team))
				query.transform = Transform3D(Basis.IDENTITY,start+Vector3.UP*.9)
				query.motion = Vector3.ZERO
				check("spawn_capsule_clear_%s_%s_%d"%[attack_team,team,index],map.get_world_3d().direct_space_state.intersect_shape(query).is_empty())
				for site in ["A","B"]:
					var points: Array[Vector3] = map.route(team,index,attack_team,site)
					var id := "%s_%s_%d_%s"%[attack_team,team,index,site]
					check("route_ends_at_site_"+id,points.size()>=4 and Vector2(points[-1].x,points[-1].z).distance_to(Vector2(map.sites[site].x,map.sites[site].z))<.01)
					var length := 0.0
					for j in range(1,points.size()):
						query.transform = Transform3D(Basis.IDENTITY,points[j-1]+Vector3.UP*.9)
						query.motion = points[j]-points[j-1]
						var collision: PackedFloat32Array = map.get_world_3d().direct_space_state.cast_motion(query)
						check("route_body_clear_%s_%d"%[id,j],collision[0]>.999,{"from":str(points[j-1]),"to":str(points[j]),"fraction":collision[0]})
						length += query.motion.length()
					route_lengths[id] = length
	for site in ["A","B"]:
		query.transform = Transform3D(Basis.IDENTITY,map.sites[site]+Vector3.UP*.98)
		query.motion = Vector3.ZERO
		check("site_center_body_clear_"+site,map.get_world_3d().direct_space_state.intersect_shape(query).is_empty())
		check("site_has_real_floor_"+site,not ray(map,map.sites[site]+Vector3.UP,map.sites[site]-Vector3.UP).is_empty())
	check("plant_centers_do_not_directly_sight_each_other",not ray(map,Vector3(-29,1.6,8),Vector3(29,1.6,8)).is_empty())
	var rotation := [Vector3(-29,.08,8),Vector3(-6,.08,8),Vector3(-6,.08,15),Vector3(6,.08,15),Vector3(6,.08,8),Vector3(29,.08,8)]
	for j in range(1,rotation.size()):
		query.transform = Transform3D(Basis.IDENTITY,rotation[j-1]+Vector3.UP*.9)
		query.motion = rotation[j]-rotation[j-1]
		check("site_rotation_clear_%d"%j,map.get_world_3d().direct_space_state.cast_motion(query)[0]>.999)
	check("main_and_flank_have_solid_separator",not ray(map,Vector3(-32,1.6,-20),Vector3(-43,1.6,-20)).is_empty())
	check("full_height_cover_stops_head_shot",not ray(map,Vector3(-40,1.6,8),Vector3(-29,1.6,8)).is_empty())
	check("low_cover_is_not_invisible_head_wall",ray(map,Vector3(-30,1.6,15),Vector3(-22,1.6,15)).is_empty())
	check("low_cover_stops_lower_shot",not ray(map,Vector3(-30,.5,15),Vector3(-22,.5,15)).is_empty())
	check("outside_and_foreign_buy_rejected",not map.is_buy_zone(Vector3(60,0,-54),"sun","sun") and not map.is_buy_zone(Vector3(0,0,54),"sun","sun") and not map.is_buy_zone(Vector3(0,0,-54),"other","sun"))
	check("invalid_route_rejected",map.route("sun",0,"sun","NO_SITE").is_empty() and map.route("other",0,"sun","A").is_empty())
	check("nonfinite_map_queries_reject",not map.is_buy_zone(Vector3(NAN,0,0),"sun","sun") and map.callout(Vector3(INF,0,0))=="Outside arena")
	map.set_buy_barriers(true)
	await physics_frame
	check("next_round_restores_real_barrier",not ray(map,Vector3(0,1.6,46),Vector3(0,1.6,42)).is_empty())
	var stable := true
	for path in source_sha256: stable = stable and source_sha256[path]==FileAccess.get_sha256(path)
	check("sources_unchanged_during_test",stable)
	var passed := true
	for row in checks: passed = passed and row.passed
	var report := {"passed":passed,"checks":checks,"route_lengths_m":route_lengths,"map":map.report(),"source_sha256":source_sha256,"scope":"Actual Godot headless static-physics capsule sweeps and bullet rays for all40 team/side/site routes; no rendering, human input, live-network or hardware-performance claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(path.get_base_dir())
			FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size(),"map":map.report()}))
	map.queue_free()
	quit(0 if passed else 1)
