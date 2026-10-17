extends SceneTree
## Independent scene/resource census. Dummy-renderer counters are not GPU memory or FPS.
var checks: Array = []
var report := {"schema":1,"suite":"visual_resource_budget_cases","checks":[],"cycles":[],"effects":{},"scope":"Headless scene census and five repeated lifecycle samples. No rendered acceptance, physical GPU memory, frame rate, draw-call or pixel-overdraw claim."}

func _initialize() -> void: call_deferred("run")
func check(label: String, value: bool, detail: Variant = null) -> void:
	checks.append({"name":label,"passed":value,"detail":detail})
	if not value: push_error("RESOURCE CENSUS: " + label)
func monitor() -> Dictionary:
	return {"objects":int(Performance.get_monitor(Performance.OBJECT_COUNT)),"nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),"resources":int(Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)),"orphans":int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),"engine_static_bytes":OS.get_static_memory_usage(),"rss_kib":rss()}
func rss() -> int:
	var file := FileAccess.open("/proc/self/status",FileAccess.READ)
	if file == null: return -1
	# procfs reports zero length; read lines instead of get_file_as_string().
	while not file.eof_reached():
		var line := file.get_line()
		if line.begins_with("VmRSS:"): return int(line.trim_prefix("VmRSS:").strip_edges().split(" ",false)[0])
	return -1
func triangles(mesh: Mesh, surface: int) -> int:
	if mesh is ArrayMesh:
		if mesh.surface_get_primitive_type(surface) != Mesh.PRIMITIVE_TRIANGLES: return 0
		var indices: int = mesh.surface_get_array_index_len(surface)
		return (indices if indices > 0 else mesh.surface_get_array_len(surface)) / 3
	var arrays: Array = mesh.surface_get_arrays(surface)
	var indices: Variant = arrays[Mesh.ARRAY_INDEX]
	return (indices.size() if indices != null and not indices.is_empty() else arrays[Mesh.ARRAY_VERTEX].size()) / 3
func census(owner: Node) -> Dictionary:
	var result := {"nodes":0,"mesh_instances":0,"visible_mesh_instances":0,"surfaces":0,"resident_unique_triangles":0,"instanced_triangles":0,"visible_instanced_triangles":0,"unique_meshes":0,"effective_materials":0,"texture_resources":0,"texture_pixels":0,"texture_files_bytes":0,"skeletons":0,"bones":0,"lights":0,"particles":0,"collision_objects":0,"texture_paths":[]}
	var meshes := {}; var materials := {}; var textures := {}; var pending: Array = [owner]
	while not pending.is_empty():
		var node: Node = pending.pop_back(); pending.append_array(node.get_children()); result.nodes += 1
		if node is Skeleton3D: result.skeletons += 1; result.bones += node.get_bone_count()
		if node is Light3D: result.lights += 1
		if node is GPUParticles3D or node is CPUParticles3D: result.particles += 1
		if node is CollisionObject3D: result.collision_objects += 1
		if not node is MeshInstance3D or node.mesh == null: continue
		result.mesh_instances += 1
		if node.is_visible_in_tree(): result.visible_mesh_instances += 1
		var mesh: Mesh = node.mesh; var first := not meshes.has(mesh.get_instance_id()); meshes[mesh.get_instance_id()] = true
		for s in range(mesh.get_surface_count()):
			var count := triangles(mesh,s); result.surfaces += 1; result.instanced_triangles += count
			if first: result.resident_unique_triangles += count
			if node.is_visible_in_tree(): result.visible_instanced_triangles += count
			var material: Material = node.get_active_material(s)
			if material == null or materials.has(material.get_instance_id()): continue
			materials[material.get_instance_id()] = true
			for property in material.get_property_list():
				var value: Variant = material.get(property.name)
				if not value is Texture2D or textures.has(value.get_instance_id()): continue
				textures[value.get_instance_id()] = true; result.texture_pixels += value.get_width()*value.get_height()
				result.texture_paths.append({"path":value.resource_path,"width":value.get_width(),"height":value.get_height()})
				if FileAccess.file_exists(value.resource_path):
					var file := FileAccess.open(value.resource_path,FileAccess.READ); result.texture_files_bytes += file.get_length()
	result.unique_meshes = meshes.size(); result.effective_materials = materials.size(); result.texture_resources = textures.size()
	return result
func settle() -> void:
	await process_frame; await process_frame
func stable_key(row: Dictionary) -> Dictionary:
	var copy := row.duplicate(true); copy.erase("texture_paths"); return copy
func run() -> void:
	report.engine = Engine.get_version_info(); report.renderer = RenderingServer.get_current_rendering_method(); report.before_load = monitor()
	var sources := {}
	for path in ["res://project.godot","res://scenes/courtyard.tscn","res://scripts/courtyard.gd","res://scripts/player.gd","res://scripts/rama_ability_effects.gd","res://scripts/rama_motion.gd","res://scripts/hero_district_detail.gd","res://scripts/hero_atmosphere.gd","res://scripts/rama_surface_finish.gd","res://scripts/rama_character_accents.gd","res://shaders/rama_ability_calligraphy.gdshader",get_script().resource_path]:
		if FileAccess.file_exists(path): sources[path] = FileAccess.get_sha256(path)
	for label in ["gold","hair","ivory","skin","woven"]:
		var path: String = "res://assets/materials/rama-finish/"+label+"-roughness.png"
		if FileAccess.file_exists(path): sources[path] = FileAccess.get_sha256(path)
	report.source_sha256 = sources
	var packed: PackedScene = load("res://scenes/courtyard.tscn")
	for index in range(5):
		var before := monitor(); var start := Time.get_ticks_usec(); var scene = packed.instantiate(); root.add_child(scene)
		var constructed_us := Time.get_ticks_usec()-start
		# Disable autonomous simulation; explicit real menu/start/reset transitions below.
		scene.process_mode = Node.PROCESS_MODE_DISABLED
		await settle()
		var initial := census(scene); var post_create := monitor(); var transition_start := Time.get_ticks_usec()
		for turn in range(6):
			scene.night = turn % 2 == 1; scene._apply_settings(); scene.start_training(); scene.reset_training(); scene.return_to_menu()
		await settle()
		var after_transitions := census(scene); var transitions_us := Time.get_ticks_usec()-transition_start
		check("cycle_%d_same_scene_resources_after_six_day_night_start_reset_menu_transitions"%index,stable_key(initial)==stable_key(after_transitions),{"before":stable_key(initial),"after":stable_key(after_transitions)})
		var row := {"index":index,"before":before,"post_create":post_create,"construction_wall_us":constructed_us,"six_transitions_wall_us":transitions_us,"scene":initial,"after_transitions":after_transitions}
		scene.free(); scene = null; await settle(); row.after_free = monitor(); report.cycles.append(row)
		check("cycle_%d_scene_nodes_return_to_entry_count"%index,row.after_free.nodes==before.nodes,{"before":before.nodes,"after":row.after_free.nodes})
		check("cycle_%d_orphan_nodes_return_to_entry_count"%index,row.after_free.orphans==before.orphans,{"before":before.orphans,"after":row.after_free.orphans})
	var warm: Dictionary = report.cycles[0].after_free
	for index in range(1,5):
		var after: Dictionary = report.cycles[index].after_free
		check("warm_exit_%d_object_resource_counts_equal_first_exit"%index,after.objects==warm.objects and after.resources==warm.resources,{"first":warm,"actual":after})
		check("cycle_%d_scene_census_equal_first"%index,stable_key(report.cycles[index].scene)==stable_key(report.cycles[0].scene))
	if "--effects" in OS.get_cmdline_user_args():
		effects_probe()
		check("effect_probe_reached_complete_receipt",report.effects.get("complete",false))
	var source_after := {}; for path in sources: source_after[path] = FileAccess.get_sha256(path)
	check("scoped_sources_unchanged_during_probe",sources==source_after); report.source_after_sha256 = source_after
	report.checks = checks; report.passed = checks.all(func(row): return row.passed); report.after = monitor()
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):
			var path := argument.trim_prefix("--report="); var file := FileAccess.open(path,FileAccess.WRITE); file.store_string(JSON.stringify(report,"  ")); file.close()
	print("Visual resource census: %d/%d"%[checks.filter(func(row):return row.passed).size(),checks.size()]); quit(0 if report.passed else 1)
func effects_probe() -> void:
	var army = load("res://scripts/lane_army.gd").new(); army.visual_enabled=false; root.add_child(army); army.set_physics_process(false)
	var kit = load("res://scripts/rama_ability_kit.gd").new(); root.add_child(kit)
	var fx = load("res://scripts/rama_ability_effects.gd").new(); root.add_child(fx); fx.set_process(false)
	var events: Array=[]; army.configure(JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")),null); kit.configure(army)
	kit.ability_event.connect(func(event): events.append(event.duplicate(true)); fx.consume_event(event))
	kit.set_movement_receiver(func(_start,destination,_duration): return {"accepted":true,"destination":destination})
	var cases := {}; var maximum := 0
	for id in fx.IDS:
		army.reset(); events.clear(); var accepted: Dictionary = kit.request_ability(id,Vector3.ZERO,Vector3.BACK,Vector3(0,0,4))
		check(id+"_actual_kit_accepts_resource_fixture",accepted.accepted)
		var peak := {}; var peak_triangles := -1; var start := Time.get_ticks_usec()
		for tick in range(320):
			army.step_simulation(.025); fx.step(.025)
			var state: Dictionary = fx.report()
			if state.total_triangles > peak_triangles:
				peak_triangles = state.total_triangles; peak = {"time_s":(tick+1)*.025,"effect_report":state,"census":census(fx)}
		maximum = maxi(maximum,peak_triangles)
		cases[id] = {"peak":peak,"320_simulation_steps_wall_us":Time.get_ticks_usec()-start,"accepted_event_count":events.size()}
		check(id+"_lifetime_releases_all_cast_nodes",fx.report().active==0 and fx.report().allocated_impacts<=18)
	# Actual kit emits the start template. Sequence/generation IDs below are fixture
	# expansions to measure the presentation cap, not simultaneous gameplay authority.
	army.reset(); events.clear(); kit.request_ability("guardian_circle",Vector3.ZERO,Vector3.BACK,Vector3(0,0,4))
	var template: Dictionary = events[0].duplicate(true); fx.reset()
	for index in range(12):
		var event := template.duplicate(true); event.generation=int(template.generation)+1; event.cast_id=index+1; event.event_seq=index+1
		check("capacity_fixture_%d_accepted"%index,fx.consume_event(event))
	fx.step(.4)
	for index in range(18): fx._impact(Vector3(index%6,1,index/6),Color("e8c373"),true)
	var saturation := {"report":fx.report(),"census":census(fx)}
	check("capacity_fixture_twelve_casts_eighteen_impacts",saturation.report.active==12 and saturation.report.impacts==18)
	var overflow := template.duplicate(true); overflow.generation=int(template.generation)+1; overflow.cast_id=13; overflow.event_seq=13
	check("capacity_fixture_thirteenth_cast_refused",not fx.consume_event(overflow))
	fx.set_options({"reduced_effects":true,"reduced_motion":true}); var reduced := {"report":fx.report(),"census":census(fx)}
	check("reduced_effects_reduce_actual_allocated_geometry",reduced.report.total_triangles<saturation.report.total_triangles)
	fx.reset(); check("effect_reset_frees_all_child_nodes",fx.get_child_count()==0 and fx.report().total_triangles==0)
	report.effects = {"complete":true,"actual_kit_lifetime_samples":cases,"saturation_fixture":saturation,"reduced_saturation_fixture":reduced,"scope":"Actual accepted kit events sampled every 25 ms for 8 s each. Capacity fixture expands a genuine accepted ward event to twelve sequence IDs and injects eighteen contact effects. Node/material/triangle counts bound allocations, not screen-space overlap or fragment cost."}
	kit.free(); fx.free(); army.free()
