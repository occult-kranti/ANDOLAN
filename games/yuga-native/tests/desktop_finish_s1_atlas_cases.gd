extends SceneTree
## S1 native atlas truth, marker legibility and owned-resource counterexamples.
## Headless draw dispatch is not a rasterized visual acceptance result.
const Atlas = preload("res://scripts/world_atlas.gd")
const MANIFEST := "res://assets/world/confluence-map.json"
var checks: Array[Dictionary] = []
var output := "/tmp/desktop-finish-s1-atlas.json"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("_run")

func check(label: String, ok: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail})
	print("PASS " if ok else "FAIL ",label)

func _frames(count := 2) -> void:
	for unused in count: await process_frame

func _run() -> void:
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
	var original := JSON.stringify(manifest)
	var atlas := Atlas.new()
	atlas.data=manifest
	root.add_child(atlas)
	var other := Atlas.new()
	root.add_child(other)
	var owned := atlas._background()
	var distinct := owned != other._background()
	for index in 100: distinct=distinct and atlas._background()==owned
	check("one stable private panel resource per atlas",distinct)
	var bounds: Array=manifest.bounds.nominal_xz
	var expected_ids: Array[String] = []
	for entry in manifest.traversal.native_collision_boxes: expected_ids.append(entry.id)
	var unique_ids: Dictionary = {}
	for identity in expected_ids: unique_ids[identity]=true
	check("actual native manifest has eight distinct raised decks",expected_ids.size()==8 and unique_ids.size()==8)
	var draw_count := [0]
	atlas.draw.connect(func(): draw_count[0]+=1)
	# These are the actual compact/wide atlas sizes allocated by the existing
	# caller at the three supported desktop windows, with a conservative footer.
	for scenario in [{"window":"960x540","size":Vector2(152,300)}, {"window":"1280x720","size":Vector2(166,316)}, {"window":"1366x768","size":Vector2(166,316)}]:
		atlas.size=scenario.size
		atlas.footer_height=90
		var plot: Rect2=atlas._plot_rect()
		var footprints: Array[Dictionary]=atlas._native_deck_footprints()
		var ids: Array[String]=[]
		var geometry_ok:=footprints.size()==8
		for index in footprints.size():
			var actual: Dictionary=footprints[index]
			var source: Dictionary=manifest.traversal.native_collision_boxes[index]
			ids.append(actual.id)
			var rect: Rect2=actual.rect
			# Independent ground-to-card relation against the original manifest,
			# including all four corners and the physical X/Z footprint scale.
			var expected_center:=Vector2(12+(float(source.position[0])-float(bounds[0]))/(float(bounds[1])-float(bounds[0]))*(atlas.size.x-24),26+(float(source.position[2])-float(bounds[2]))/(float(bounds[3])-float(bounds[2]))*(atlas.size.y-52-atlas.footer_height))
			var expected_size:=Vector2(float(source.size[0])/(float(bounds[1])-float(bounds[0]))*(atlas.size.x-24),float(source.size[2])/(float(bounds[3])-float(bounds[2]))*(atlas.size.y-52-atlas.footer_height))
			geometry_ok=geometry_ok and rect.get_center().is_equal_approx(expected_center) and rect.size.is_equal_approx(expected_size) and plot.encloses(rect)
		check("all native deck IDs and footprints match real manifest at "+scenario.window,geometry_ok and ids==expected_ids,{"ids":ids,"plot":str(plot)})
		var heading_ok:=true
		for direction in [Vector3.RIGHT,Vector3.LEFT,Vector3.FORWARD,Vector3.BACK,Vector3(1,0,1),Vector3(-1,0,1)]:
			var expected:=Vector2(direction.x/(float(bounds[1])-float(bounds[0]))*plot.size.x,direction.z/(float(bounds[3])-float(bounds[2]))*plot.size.y).normalized()
			heading_ok=heading_ok and atlas.project_heading(direction).distance_to(expected)<.00001
		check("cardinal and diagonal headings retain anisotropic projection at "+scenario.window,heading_ok)
		var labels_ok:=true
		for core in manifest.objectives:
			if core.kind!="core": continue
			var caption: Rect2=atlas._core_caption_rect(core)
			# Actual spawn points are eight world metres toward the centre.
			var spawn:=Vector3(0,0,float(core.position[2])+(8.0 if core.team=="sun" else -8.0))
			var marker:=Rect2(atlas.project(spawn)-Vector2(13,13),Vector2(26,26))
			labels_ok=labels_ok and not caption.intersects(marker) and Rect2(Vector2.ZERO,atlas.size).encloses(caption)
			var position_swapped: Dictionary=core.duplicate(true)
			position_swapped.position[2]=-position_swapped.position[2]
			var swapped: Rect2=atlas._core_caption_rect(position_swapped)
			labels_ok=labels_ok and signf(swapped.get_center().y-caption.get_center().y)==signf(float(position_swapped.position[2])-float(core.position[2]))
		check("both core captions clear spawn marker and follow actual positions at "+scenario.window,labels_ok)
		for position_ in [Vector3(0,0,-112),Vector3(0,0,112),Vector3(-20,8,-88),Vector3.ZERO]:
			atlas.hero_position=position_
			atlas.hero_forward=Vector3(1,0,1)
			atlas.units=[{"position":Vector3(0,0,-20),"team":"sun","role":"cannon_cart"},{"position":Vector3(0,0,20),"team":"moon","role":"spearman"}]
			atlas.relays=[{"position":Vector3.ZERO,"owner":"sun","contested":true}]
			atlas.queue_redraw()
			await _frames()
	check("draw notifications exercise spawns deck siege and contested relay",draw_count[0]>=12,{"draws":draw_count[0]})
	check("map reading and draw dispatch leave source world data unchanged",JSON.stringify(manifest)==original)
	var without_decks: Dictionary=manifest.duplicate(true)
	without_decks.erase("traversal")
	atlas.data=without_decks
	check("legacy manifest without native traversal stays a valid empty deck layer",atlas._native_deck_footprints().is_empty())
	atlas.data=manifest
	check("invalid or zero heading produces no false orientation",atlas.project_heading(Vector3(NAN,0,0))==Vector2.ZERO and atlas.project_heading(Vector3.ZERO)==Vector2.ZERO)
	var report := {"passed":checks.all(func(row): return row.passed),"count":checks.size(),"checks":checks,"source_sha256":{},"scope":"Headless actual-manifest geometry, font extents, draw dispatch and resource ownership. No actual pixels, hardware FPS or full caller layout acceptance."}
	for path in ["res://scripts/world_atlas.gd",MANIFEST,"res://scripts/hero_ui_theme.gd",get_script().resource_path]:report.source_sha256[path]=FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"\t")+"\n")
	atlas.queue_free();other.queue_free();await _frames()
	quit(0 if report.passed else 1)
