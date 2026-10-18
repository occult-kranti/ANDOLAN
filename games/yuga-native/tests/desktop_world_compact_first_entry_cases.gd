extends SceneTree
## Fresh native viewport entry; never manually refresh, layout or preseed labels.
var output := "/tmp/desktop-world-compact-first-entry.json"
var checks: Array[Dictionary] = []
var timeline: Array[Dictionary] = []
var world: Node3D

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	call_deferred("run")

func frames(count := 16) -> void:
	for unused in count: await process_frame

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func observation() -> Dictionary:
	var card: Control=world.compact_world_card
	var contents: Control=card.get_child(0)
	var rows: Array[Dictionary]=[]
	var fit:=true
	for row in world.compact_world_labels:
		var text_size: Vector2=row.get_theme_font("font").get_multiline_string_size(row.text,HORIZONTAL_ALIGNMENT_LEFT,row.size.x,row.get_theme_font_size("font_size"))
		var inside: bool=card.get_global_rect().encloses(row.get_global_rect()) and row.size.y+1>=text_size.y and not row.text.is_empty()
		fit=fit and inside
		rows.append({"text":row.text,"rect":str(row.get_global_rect()),"font_text_size":str(text_size),"line_count":row.get_line_count(),"fits":inside})
	fit=fit and contents.get_combined_minimum_size().y<=card.size.y-16+1
	return {"scale":root.content_scale_factor,"logical":str(root.get_visible_rect().size),"card":str(card.get_global_rect()),"card_height":card.size.y,"contents_minimum":str(contents.get_combined_minimum_size()),"visible":card.is_visible_in_tree(),"rows":rows,"all_four_rows_fit":fit,"world_process":world.is_processing(),"world_physics":world.is_physics_processing(),"army_elapsed":world.army.elapsed}

func run() -> void:
	Engine.max_fps=60
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.content_scale_factor=1.0
	var sources: Dictionary={}
	for path in ["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/lane_army.gd",get_script().resource_path]: sources[path]=FileAccess.get_sha256(path)
	world=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world
	await frames()
	check("fresh expanded world has not seeded constrained labels",world.compact_world_labels.all(func(row):return row.text.is_empty()) and not world._constrained_world)
	for scale in [1.0,1.25,1.5,2.0,1.0,1.5]:
		root.content_scale_factor=scale
		await frames()
		var all_fit:=true
		var samples: Array[Dictionary]=[]
		for unused in 12:
			await process_frame
			var row:=observation();samples.append(row);timeline.append(row)
			all_fit=all_fit and (row.all_four_rows_fit if scale>=1.5 else not row.visible)
		check("fresh live scale has four contained actual-text rows: "+str(scale),all_fit,{"samples":samples})
	check("presentation and physics remain active throughout fresh entry",world.is_processing() and world.is_physics_processing() and world.army.is_physics_processing() and world.player.is_physics_processing() and world.army.elapsed>0)
	# Legitimate nonnegative offline score values, staged only in this fixture.
	# Observe whether ordinary periodic text updates can create a new wrap;
	# no manual HUD refresh or viewport resize repairs the resulting footprint.
	root.content_scale_factor=2.0;await frames()
	var wrap_witness: Dictionary={}
	for gold in [100,1000,10000]:
		world.army.gold=gold
		await frames()
		var seen:=observation();timeline.append(seen)
		if seen.rows[0].line_count>1:
			wrap_witness=seen
			break
	check("staged score refresh preserves text containment if a real wrap occurs",wrap_witness.is_empty() or wrap_witness.all_four_rows_fit,{"wrap_witness":wrap_witness,"scope":"Actual native Label wrap from staged positive army score; not a played earning/economy test. No wrap witness means that dynamic case remains unqualified."})
	var stable:=true
	for path in sources: stable=stable and FileAccess.get_sha256(path)==sources[path]
	check("observed sources unchanged",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"timeline":timeline,"sources":sources,"scope":"Fresh world, real active world/player/army processes and native100→125→150→200→100 viewport signals. No preseeded compact text/manual layout/HUD calls. Actual bundled-font/Label rectangle containment, staged positive-score wrap witness. Headless geometry only; actual successor pixels still required."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(8)
	await create_timer(.08,true,false,true).timeout
	quit(0 if result.passed else 1)
