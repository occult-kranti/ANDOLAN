extends SceneTree
const Garden = preload("res://tools/lanka-water-garden/mount.gd")
var checks: Array = []
var output := ""
func _initialize() -> void: call_deferred("run")
func check(name: String, passed: bool, detail: Variant = null) -> void: checks.append({"name": name, "passed": passed, "detail": detail})
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="): output = arg.trim_prefix("--output=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): push_error("fresh absolute receipt required"); quit(1); return
	var parent := Node3D.new()
	root.add_child(parent)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var before := manifest.duplicate(true)
	check("native asset self-contained", ResourceLoader.get_dependencies(Garden.ASSET).is_empty())
	check("default off and null parent refuse", not Garden.build(parent).enabled and not Garden.build(null, true).enabled)
	parent.rotation.y = .2
	check("rotated parent refused before mount", Garden.build(parent, true).get("reason") == "identity_world_required")
	parent.rotation = Vector3.ZERO
	var result := Garden.build(parent, true)
	check("one pinned candidate loads", result.get("enabled", false), result.get("report", {}))
	if not result.get("enabled", false): await finish(parent); return
	var candidate: Node3D = result.root
	var north: Node3D = candidate.get_node("garden-north-column")
	var south: Node3D = candidate.get_node("garden-south-column")
	check("column resources share immutable mesh and exact source shape", north.get_child(0).mesh == south.get_child(0).mesh and north.get_node("SourceCollision/WholeSourceFaces").shape == south.get_node("SourceCollision/WholeSourceFaces").shape)
	check("source collider instances remain private", north.get_node("SourceCollision") != south.get_node("SourceCollision"))
	var original := Garden.prepare_army_manifest(manifest, candidate)
	check("four source footprints append without editing manifest", original.get("ok", false) and original.manifest.traversal.native_collision_boxes.size() == 12 and manifest == before)
	candidate.position.x = .25
	check("translated root fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "source_world_placement")
	candidate.position = Vector3.ZERO
	parent.rotation.y = .2
	check("rotated parent after mounting fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "source_world_placement")
	parent.rotation = Vector3.ZERO
	var old := north.position
	north.position.x += .25
	check("moved source cluster fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "source_world_placement")
	north.position = old
	var body: StaticBody3D = north.get_node("SourceCollision")
	body.position.z = .25
	check("moved collider fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "source_world_placement")
	body.position = Vector3.ZERO
	var metadata: Array = candidate.get_meta("army_ground_footprints").duplicate(true)
	var damaged := metadata.duplicate(true)
	damaged[0].position[0] += 10
	candidate.set_meta("army_ground_footprints", damaged)
	check("moved footprint metadata fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "source_footprint_value")
	damaged = metadata.duplicate(true)
	damaged[0].size[2] = NAN
	candidate.set_meta("army_ground_footprints", damaged)
	check("nonfinite metadata fails closed", Garden.prepare_army_manifest(manifest, candidate).get("reason") == "finite_footprint")
	candidate.set_meta("army_ground_footprints", metadata)
	var restored := Garden.prepare_army_manifest(manifest, candidate)
	check("restore yields original exact footprint copy", restored.get("ok", false) and restored.boxes == original.boxes)
	restored.manifest.traversal.native_collision_boxes[-1].position[0] = 999
	check("consumer copy cannot mutate metadata/source", candidate.get_meta("army_ground_footprints") == metadata and manifest == before and original.manifest.traversal.native_collision_boxes[-1].position[0] != 999)
	check("duplicate mount and duplicate army augmentation refused", Garden.build(parent, true).get("reason") == "duplicate_placement" and Garden.prepare_army_manifest(original.manifest, candidate).get("reason") == "duplicate_army_footprint")
	check("asset bytes remain immutable", FileAccess.get_sha256(Garden.ASSET) == Garden.ASSET_SHA)
	await finish(parent)
func finish(parent: Node3D) -> void:
	var passed := checks.all(func(row): return row.passed)
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify({"schema": 1, "passed": passed, "checks": checks, "asset_sha256": Garden.ASSET_SHA, "mount_sha256": FileAccess.get_sha256("res://scripts/lanka_water_garden.gd"), "fixture_mount_sha256": FileAccess.get_sha256("res://tools/lanka-water-garden/mount.gd"), "engine": Engine.get_version_info(), "scope": "Opt-in source cache, immutable resource sharing, copy isolation and source transform/metadata rejection. No image or gameplay acceptance."}, "  ") + "\n")
	parent.queue_free()
	for unused in 4: await process_frame
	print(JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)
