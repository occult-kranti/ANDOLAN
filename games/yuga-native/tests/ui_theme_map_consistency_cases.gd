extends SceneTree
const UI=preload("res://scripts/hero_ui_theme.gd")
const SHELL=preload("res://scripts/launch_shell.gd")
var checks:Array[Dictionary]=[]
var output:="/tmp/ui-theme-map-consistency.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,ok:bool,detail:Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail});print("PASS " if ok else "FAIL ",label)
func frames(count:=5) -> void:
	for unused in count:await process_frame
func ratio(a:Color,b:Color) -> float:
	var x:=a.srgb_to_linear();var y:=b.srgb_to_linear()
	var l:=.2126*x.r+.7152*x.g+.0722*x.b;var r:=.2126*y.r+.7152*y.g+.0722*y.b
	return (maxf(l,r)+.05)/(minf(l,r)+.05)
func run() -> void:
	var shell:=SHELL.new();root.add_child(shell);await frames()
	for dimensions in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080)]:
		root.size=dimensions;root.content_scale_size=dimensions;await frames()
		for mode in ["world","train"]:
			shell.set_mode(mode);await frames()
			var failures:=[]
			if not root.get_visible_rect().encloses(shell.card.get_global_rect()):failures.append("card outside viewport")
			for action in shell._actions:
				var width:float=action.get_theme_font("font").get_string_size(action.text,HORIZONTAL_ALIGNMENT_LEFT,-1,action.get_theme_font_size("font_size")).x
				var style:StyleBoxFlat=action.get_theme_stylebox("normal")
				if width+style.content_margin_left+style.content_margin_right>action.size.x+.1:failures.append(action.name)
				if action.size.y<44:failures.append("small target")
				if ratio(action.get_theme_color("font_color"),style.bg_color)<4.5:failures.append("low contrast")
			check("bundled title controls fit and contrast at %s %s"%[dimensions,mode],failures.is_empty(),{"failures":failures,"card":str(shell.card.get_global_rect()),"wordmark":str(shell.title_wordmark.size),"body17_line_height":UI.text_font().get_height(17)})
	shell.queue_free();await frames()
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(world);current_scene=world;await frames();world.set_paused(true)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1920,1080)]:
		root.size=dimensions;root.content_scale_size=dimensions;await frames()
		world._layout_world_hud();await frames()
		var atlas:Control=world.map_control;var legend:Label=atlas.get_node("AtlasLegend")
		var labels_fit:bool=atlas.get_global_rect().encloses(legend.get_global_rect()) and legend.size.y>=legend.get_combined_minimum_size().y
		var map_surface:StyleBoxFlat=atlas._background()
		check("bundled tactical legend fits and contrasts at "+str(dimensions),labels_fit and ratio(legend.get_theme_color("font_color"),map_surface.bg_color)>=4.5,{"legend":str(legend.size),"minimum":str(legend.get_combined_minimum_size()),"map":str(atlas.size),"footer":atlas.footer_height})
		var heading_ok:=atlas.has_method("project_heading");var maximum_old_error:=0.0
		for direction in [Vector3(1,0,1),Vector3(-1,0,1),Vector3(1,0,-1),Vector3(1,0,0),Vector3(0,0,-1)]:
			var expected:Vector2=(atlas.project(atlas.hero_position+direction)-atlas.project(atlas.hero_position)).normalized()
			maximum_old_error=maxf(maximum_old_error,absf(Vector2(direction.x,direction.z).normalized().angle_to(expected)))
			if heading_ok:heading_ok=atlas.project_heading(direction).distance_to(expected)<.00001
		check("map heading matches projected world direction at "+str(dimensions),heading_ok,{"old_raw_heading_max_error_degrees":rad_to_deg(maximum_old_error)})
		var zones:Array[Rect2]=[]
		for path in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus","WorldAtlas"]:zones.append(world.hud.get_node(path).get_global_rect())
		zones.append(world.rama_hud.get_global_rect())
		var overlap:=false
		for a in zones.size():
			for b in range(a+1,zones.size()):overlap=overlap or zones[a].intersects(zones[b])
		check("shared world panels remain separate at "+str(dimensions),not overlap)
	world.set_paused(false);world.army.cores.sun=0;world.army.cores.moon=0;world.army.step_simulation(.05);world.set_paused(true);await frames()
	var before:Dictionary=world.army.report();var summary:Control=world.outcome_summary
	check("actual draw uses explicit shared outcome and readable heading",world.army.winner=="draw" and summary.heading.text=="Draw · both cores destroyed" and ratio(summary.heading.get_theme_color("font_color"),UI.DEEP)>=4.5)
	world._update_practice_hud();check("outcome and map refresh are read-only",world.army.report()==before)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":{},"scope":"Actual engine layout with bundled fonts, applied control contrast, projected map directions and actual terminal authority. Headless; no rasterized pixel or OS-input acceptance."}
	for path in ["res://scripts/hero_ui_theme.gd","res://scripts/launch_shell.gd","res://scripts/world_atlas.gd","res://scripts/world_outcome_summary.gd","res://scripts/confluence_world.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;world.queue_free();current_scene=null;await frames();quit(0 if result.passed else 1)
