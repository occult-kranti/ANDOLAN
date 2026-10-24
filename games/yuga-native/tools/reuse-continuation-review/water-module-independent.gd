extends SceneTree
## Independent mount/manifest adverse cases; no gameplay/world edits.
const Garden = preload("res://tools/lanka-water-garden/mount.gd")
var checks: Array = []
var output := ""
var before := ""
func _initialize() -> void: call_deferred("run")
func check(label: String, pass_: bool, details: Variant = null) -> void:
	checks.append({"name": label, "passed": pass_, "details": details})
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): quit(2); return
	before = FileAccess.get_sha256("res://tools/lanka-water-garden/mount.gd")
	var world := Node3D.new()
	root.add_child(world)
	var source: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var unchanged := source.duplicate(true)
	check("default candidate opt-out adds no node", not Garden.build(world).enabled and world.get_child_count() == 0)
	world.scale = Vector3(2, 2, 2)
	check("scaled world rejected before loading", Garden.build(world, true).get("reason") == "identity_world_required" and world.get_child_count() == 0)
	world.scale = Vector3.ONE
	var mounted := Garden.build(world, true)
	check("exact source candidate mounts", mounted.enabled, mounted.get("report"))
	if not mounted.enabled: world.free(); finish(); return
	var node: Node3D = mounted.root
	var first := Garden.prepare_army_manifest(source, node)
	check("four source footprints appended to eight authority solids", first.ok and first.manifest.traversal.native_collision_boxes.size() == 12 and source == unchanged)
	node.position.x = 1
	check("moved root cannot return stale world footprints", not Garden.prepare_army_manifest(source, node).ok)
	node.position = Vector3.ZERO
	world.rotation.y = PI / 2
	check("rotated parent cannot return stale world footprints", not Garden.prepare_army_manifest(source, node).ok)
	world.rotation = Vector3.ZERO
	var north: Node3D = node.get_node("garden-north-column")
	var shape: CollisionShape3D = north.get_node("SourceCollision/WholeSourceFaces")
	shape.position.y = 1
	check("moved collider shape refuses misleading footprint", not Garden.prepare_army_manifest(source, node).ok)
	shape.position = Vector3.ZERO
	var metadata: Array = node.get_meta("army_ground_footprints").duplicate(true)
	var wrong := metadata.duplicate(true)
	wrong[0].position[0] = 900
	node.set_meta("army_ground_footprints", wrong)
	check("finite but wrong source footprint is rejected", not Garden.prepare_army_manifest(source, node).ok)
	wrong = metadata.duplicate(true)
	wrong[0].size[0] = INF
	node.set_meta("army_ground_footprints", wrong)
	check("nonfinite source footprint is rejected", not Garden.prepare_army_manifest(source, node).ok)
	node.set_meta("army_ground_footprints", metadata)
	var final := Garden.prepare_army_manifest(source, node)
	check("valid source restores after all adverse cases", final.ok and final.boxes == first.boxes)
	final.manifest.traversal.native_collision_boxes[0].position[0] = 999
	final.boxes[0].position[0] = 999
	check("returned data cannot modify source or candidate metadata", source == unchanged and node.get_meta("army_ground_footprints") == metadata)
	check("second mount rejected without extra bodies", not Garden.build(world, true).enabled and world.get_child_count() == 1)
	check("second army augmentation rejected", not Garden.prepare_army_manifest(first.manifest, node).ok)
	check("candidate stays self-contained source-pinned", ResourceLoader.get_dependencies(Garden.ASSET).is_empty() and FileAccess.get_sha256(Garden.ASSET) == Garden.ASSET_SHA)
	check("mount implementation frozen through review", FileAccess.get_sha256("res://tools/lanka-water-garden/mount.gd") == before)
	world.free()
	finish()
func finish() -> void:
	var passed := checks.all(func(row): return row.passed)
	var report := {"passed": passed, "checks": checks, "mount_sha256": before, "asset_sha256": Garden.ASSET_SHA, "scope": "Independent source mount and world-footprint admission, rejection and copy checks; no raster/full-world physics/input acceptance"}
	FileAccess.open(output, FileAccess.WRITE).store_string(JSON.stringify(report, "  ") + "\n")
	print(JSON.stringify({"passed": passed, "checks": checks.size()}))
	quit(0 if passed else 1)
