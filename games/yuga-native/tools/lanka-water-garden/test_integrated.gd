extends "res://tools/lanka-water-garden/capture.gd"
## Actual production opt-out and fresh default caller, both native helpers and army.
func run() -> void:
	preflight = true
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): push_error("fresh absolute report required"); quit(1); return
	source_hashes = hashes()
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	scene.set("lanka_water_garden_enabled", false)
	root.add_child(scene); current_scene = scene
	await physics_frame; await physics_frame
	check("explicit garden opt-out preserves ready gate/world", scene.world_ready and scene.lanka_lane_gate_report.enabled and not scene.lanka_water_garden_report.enabled and not scene.world.has_node(Garden.ROOT_NAME))
	scene.set_paused(false); scene.set_process(false); scene.set_physics_process(false); hold_callbacks(scene.world)
	identity_before = identities(); context_before = water_context()
	gather_bodies(scene.world, original_body_ids)
	await install_candidate()
	var accepted_report: Dictionary = placement_result.get("report", {}).duplicate(true)
	scene.queue_free()
	await process_frame; await process_frame; await physics_frame
	scene = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene); current_scene = scene
	await physics_frame; await physics_frame
	scene.set_paused(false); scene.set_process(false); scene.set_physics_process(false); hold_callbacks(scene.world)
	check("fresh default caller enables both reviewed source modules", scene.world_ready and scene.lanka_water_garden_enabled and scene.lanka_lane_gate_enabled and scene.lanka_water_garden_report == accepted_report and scene.lanka_lane_gate_report.enabled)
	check("default scene adds exactly four bank bodies", scene.world.get_node(Garden.ROOT_NAME).find_children("*", "StaticBody3D", true, false).size() == 4)
	check("default army retains8authority8deck10gate9relay4garden", scene.army.boxes.size() == 39 and scene.manifest.authority_collision_boxes.size() == 8 and scene.manifest.traversal.native_collision_boxes.size() == 8)
	check("default actual army blocks bank/oldgate and preserves open routes", not scene.army.line_clear(Vector3(-64,0,5),Vector3(-61,0,5)) and not scene.army.line_clear(Vector3(-49,0,-70),Vector3(-49,0,-38)) and scene.army.line_clear(Vector3(-40,0,-70),Vector3(-40,0,-38)) and scene.army.line_clear(Vector3(-66,0,0),Vector3(-44,0,0)))
	for child in scene.player.get_children():
		if child is CollisionShape3D and child.shape is CapsuleShape3D: actual_capsule = child.shape
	check("fresh default integration retains all lanes/rotations/wet crossing", all_routes().is_empty(), all_routes())
	check("default helper duplicate rejected without extra bodies", Garden.build(scene.world, true).get("reason") == "duplicate_placement" and scene.world.get_node(Garden.ROOT_NAME).find_children("*", "StaticBody3D", true, false).size() == 4)
	check("default manifest remains exact original file data", scene.manifest == JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json")))
	check("all exact sources stay unchanged", hashes() == source_hashes)
	var passed := checks.all(func(row): return row.passed)
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"schema": 1, "passed": passed, "checks": checks, "source_sha256": source_hashes, "helper_sha256": FileAccess.get_sha256("res://scripts/lanka_water_garden.gd"), "world_sha256": FileAccess.get_sha256("res://scripts/confluence_world.gd"), "asset_sha256": Garden.ASSET_SHA, "scope": "Actual default integrated four bank features plus existing gate/relay/authority/decks. Source immutable and army copy preserved; actual full-world physics/cover/path negatives. No renderer/input/performance claim."}, "  ") + "\n")
	scene.queue_free()
	for unused in 8: await process_frame
	print(JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)
