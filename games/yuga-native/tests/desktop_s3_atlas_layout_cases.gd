extends SceneTree
## Integrated atlas/legend layout. Headless geometry and real bundled fonts.
const Bindings=preload("res://scripts/input_bindings.gd")
var checks:Array[Dictionary]=[]
var output:="/tmp/desktop-s3-atlas-layout.json"
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,passed:bool,detail:Dictionary={})->void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)
func frames(n:=4)->void:
	for unused in n:await process_frame
func visible_peers_disjoint(a:Control,b:Control)->bool:
	return not (a.is_visible_in_tree() and b.is_visible_in_tree()) or not a.get_global_rect().intersects(b.get_global_rect())
func run()->void:
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world);current_scene=world;await frames()
	world.set_process(false);world.set_physics_process(false)
	world.player.set_physics_process(false);world.army.set_physics_process(false)
	var atlas:Control=world.map_control
	var legend:Label=atlas.get_node("AtlasLegend")
	var original_bindings:Dictionary=Bindings.bindings.duplicate()
	var original_events:Array[InputEvent]=InputMap.action_get_events("world_overview")
	var before:Dictionary=world.army.report()
	for scenario in [
		{"name":"960x540","physical":Vector2i(960,540),"logical":Vector2i(960,540),"font":14,"key":KEY_F1},
		{"name":"960x600","physical":Vector2i(960,600),"logical":Vector2i(960,600),"font":14,"key":KEY_F1},
		{"name":"1280x720","physical":Vector2i(1280,720),"logical":Vector2i(1280,720),"font":14,"key":KEY_F1},
		{"name":"1920x1080 physical at 960x540 logical","physical":Vector2i(1920,1080),"logical":Vector2i(960,540),"font":14,"key":KEY_F1},
		{"name":"960x540 enlarged text and long active key","physical":Vector2i(960,540),"logical":Vector2i(960,540),"font":18,"key":KEY_MASK_CTRL|KEY_MASK_SHIFT|KEY_F12}]:
		root.size=scenario.physical;root.content_scale_size=scenario.logical
		root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
		# Simulate an externally overridden active action, without writing a user
		# preference: the public settings UI currently reserves this action.
		Bindings.bindings["world_overview"]=scenario.key
		InputMap.action_erase_events("world_overview")
		var event:=InputEventKey.new();event.keycode=scenario.key;InputMap.action_add_event("world_overview",event)
		legend.add_theme_font_size_override("font_size",scenario.font)
		await frames();world._layout_world_hud();await frames()
		var plot:Rect2=atlas._plot_rect()
		var viewport:=root.get_visible_rect()
		var key_inside:=viewport.encloses(atlas.get_global_rect()) and atlas.get_global_rect().encloses(legend.get_global_rect())
		var width_ok:=true
		for line in legend.text.split("\n"):
			width_ok=width_ok and legend.get_theme_font("font").get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,legend.get_theme_font_size("font_size")).x<=legend.size.x+.1
		var plot_global:=Rect2(atlas.global_position+plot.position,plot.size)
		check("useful live plot and unclipped two-line key: "+scenario.name,key_inside and width_ok and plot.size.x>=120 and plot.size.y>=96 and not plot_global.intersects(legend.get_global_rect()) and legend.text.split("\n").size()==2,{"map":str(atlas.get_global_rect()),"plot":str(plot),"key":str(legend.get_global_rect()),"key_text":legend.text,"footer":atlas.footer_height})
		var marker_ok:=true
		for objective in world.manifest.objectives:
			if objective.kind!="core":continue
			var spawn:=Vector3(0,0,float(objective.position[2])+(8 if objective.team=="sun" else -8))
			atlas.hero_position=spawn
			var here:Vector2=atlas.project(spawn)
			marker_ok=marker_ok and Rect2(Vector2.ZERO,atlas.size).encloses(Rect2(here-Vector2(13,13),Vector2(26,26)))
			var caption:Rect2=atlas._core_caption_rect(objective)
			marker_ok=marker_ok and Rect2(Vector2.ZERO,atlas.size).encloses(caption) and not caption.intersects(Rect2(here-Vector2(13,13),Vector2(26,26)))
		var decks:Array=atlas._native_deck_footprints()
		marker_ok=marker_ok and decks.size()==8
		for deck in decks:marker_ok=marker_ok and plot.encloses(deck.rect)
		check("both spawn markers, captions and eight actual decks fit: "+scenario.name,marker_ok)
		world.set_overview(true);await frames();world._layout_atlas();await frames()
		var guide:Control=world.atlas_guide
		var symbols:Label=guide.get_node("KeyScroll").get_child(0).get_node("Symbols")
		var semantics_ok:=true
		for meaning in ["Sun","Moon","Siege","Relay","contested","Tether","landing deck","cover","core","You","heading"]:semantics_ok=semantics_ok and symbols.text.contains(meaning)
		check("overview exposes complete non-hover key and active return binding: "+scenario.name,guide.visible and viewport.encloses(guide.get_global_rect()) and semantics_ok and world.atlas_guide_return.text.contains(Bindings.label("world_overview")) and root.gui_get_focus_owner()==world.atlas_guide_scroll and world.atlas_guide_scroll.horizontal_scroll_mode==ScrollContainer.SCROLL_MODE_DISABLED,{"guide":str(guide.get_global_rect()),"return":world.atlas_guide_return.text})
		world.set_paused(true);await frames()
		var hidden_for_pause:=not guide.visible
		world.set_paused(false);await frames()
		var restored:bool=guide.visible and world.overview and root.gui_get_focus_owner()==world.atlas_guide_scroll
		world.set_overview(false);await frames()
		check("guide yields to nested pause and closes with overview: "+scenario.name,hidden_for_pause and restored and not guide.visible and not world.overview)
	for dimensions in [Vector2i(640,360),Vector2i(768,432),Vector2i(853,480)]:
		root.size=Vector2i(960,540);root.content_scale_size=dimensions
		legend.add_theme_font_size_override("font_size",14)
		Bindings.bindings.erase("world_overview")
		await frames();world._update_practice_hud();world._layout_world_hud();await frames()
		var state:Control=world.compact_world_card
		var zones:Array[Rect2]=[state.get_global_rect(),atlas.get_global_rect(),world.rama_hud.get_global_rect()]
		var bounded:=state.visible and legend.visible and legend.text.contains(Bindings.label("world_overview"))
		var viewport:=root.get_visible_rect()
		for zone in zones:bounded=bounded and viewport.encloses(zone)
		for a in zones.size():
			for b in range(a+1,zones.size()):bounded=bounded and not zones[a].intersects(zones[b])
		for path in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus"]:bounded=bounded and not world.hud.get_node(path).visible
		for row in world.compact_world_labels:bounded=bounded and state.get_global_rect().encloses(row.get_global_rect()) and row.get_line_count()==1
		var plot:Rect2=atlas._plot_rect()
		check("actual constrained composite contains all visible peers: "+str(dimensions),bounded and plot.size.x>=120 and plot.size.y>=100,{"summary":str(zones[0]),"map":str(zones[1]),"combat":str(zones[2]),"plot":str(plot),"summary_lines":world.compact_world_labels.map(func(row):return row.text)})
		var original:Dictionary=world.player.traversal.report()
		world.player.traversal.energy=17;world.player.traversal.flight_cooldown=4;world.player.traversal.grapple_cooldown=1.2
		world._update_practice_hud();await frames()
		var resources_fit:=true
		for row in world.compact_world_labels:resources_fit=resources_fit and state.get_global_rect().encloses(row.get_global_rect()) and row.get_line_count()==1
		var resource_ok:bool=resources_fit and world.compact_world_labels[2].text.contains("Energy 17/100") and world.compact_world_labels[2].text.contains("4.0s") and world.compact_world_labels[2].text.contains("1.2s") and world.compact_world_labels[3].text.contains("refill")
		world.player.traversal.mode="flight";world.player.traversal.energy=80
		world._update_practice_hud();await frames()
		var flight_fit:=true
		for row in world.compact_world_labels:flight_fit=flight_fit and state.get_global_rect().encloses(row.get_global_rect()) and row.get_line_count()==1
		var flight_ok:bool=flight_fit and world.compact_world_labels[3].text.contains(Bindings.label("jump")) and world.compact_world_labels[3].text.contains(Bindings.label("descend")) and world.compact_world_labels[3].text.contains(Bindings.label("fly"))
		world.player.traversal.enabled=false;world._refresh_compact_world()
		check("real traversal energy cooldown mode and unavailable capability survive condensation: "+str(dimensions),resource_ok and flight_ok and world.compact_world_labels[3].text.contains("unavailable"))
		for property in ["energy","mode","enabled","flight_cooldown","grapple_cooldown"]:world.player.traversal.set(property,original[property])
		world._update_practice_hud();world.set_overview(true);await frames()
		check("constrained overview gives focus and scrollable live details without covering combat: "+str(dimensions),world.atlas_guide.visible and not state.visible and not world.rama_hud.is_visible_in_tree() and viewport.encloses(world.atlas_guide.get_global_rect()) and visible_peers_disjoint(world.atlas_guide,world.rama_hud) and world.atlas_live_details.text.contains(world.score_label.text) and world.atlas_live_details.text.contains(world.goal_label.text) and root.gui_get_focus_owner()==world.atlas_guide_scroll,{"guide_visible":world.atlas_guide.visible,"summary_hidden":not state.visible,"guide_inside":viewport.encloses(world.atlas_guide.get_global_rect()),"combat_visible":world.rama_hud.is_visible_in_tree(),"guide_rect":str(world.atlas_guide.get_global_rect()),"combat_rect":str(world.rama_hud.get_global_rect()),"raw_no_intersection":not world.atlas_guide.get_global_rect().intersects(world.rama_hud.get_global_rect()),"score_present":world.atlas_live_details.text.contains(world.score_label.text),"goal_present":world.atlas_live_details.text.contains(world.goal_label.text),"focused":root.gui_get_focus_owner()==world.atlas_guide_scroll})
		# Synchronous presentation-only corruption: an actually visible combat
		# rectangle must be rejected, then restore before another scene frame.
		var combat_was_visible:bool=world.rama_hud.visible
		world.rama_hud.show()
		var rejects_overlap:bool=not visible_peers_disjoint(world.atlas_guide,world.rama_hud)
		world.rama_hud.visible=combat_was_visible
		check("visible overlap counterexample rejects actual combat and restores overview: "+str(dimensions),rejects_overlap and not world.rama_hud.is_visible_in_tree() and visible_peers_disjoint(world.atlas_guide,world.rama_hud),{"visible_overlap_rejected":rejects_overlap,"combat_visible_after_restore":world.rama_hud.is_visible_in_tree()})
		world.set_overview(false);await frames()
	# Exercise the production path independently: the world presentation process
	# stays active, scale changes emit native resize signals, and no manual
	# layout call repairs a stale container minimum after the transition.
	world.set_process(true)
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720)
	root.content_scale_factor=1.0;await frames(8)
	for scale in [1.0,1.5,2.0,1.0]:
		root.content_scale_factor=scale
		var observations:Array=[]
		var all_bounded:=true
		var torso_clear:=true
		for sample in 12:
			await process_frame
			var viewport:=root.get_visible_rect()
			var camera:Camera3D=world.player.camera
			var torso:=Rect2();var first:=true
			for height in [.75,1.80]:
				for side in [-.32,.32]:
					var point:=camera.unproject_position(world.player.global_position+Vector3.UP*height+camera.global_basis.x*side)
					if first:torso=Rect2(point,Vector2.ZERO);first=false
					else:torso=torso.expand(point)
			var zones:Array[Rect2]=[];var visible:Dictionary={}
			for path in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus","WorldAtlas","CompactWorldState","RamaHeroHUD"]:
				var peer:Control=world.hud.get_node(path)
				if not peer.is_visible_in_tree():continue
				var rect:=peer.get_global_rect();zones.append(rect);visible[path]=str(rect)
				all_bounded=all_bounded and viewport.encloses(rect)
				torso_clear=torso_clear and not rect.intersects(torso)
			for a in zones.size():
				for b in range(a+1,zones.size()):all_bounded=all_bounded and not zones[a].intersects(zones[b])
			observations.append({"frame":sample,"viewport":str(viewport),"torso_proxy":str(torso),"visible":visible})
		check("live processed scale transition has bounded disjoint peers at "+str(scale),all_bounded,{"frames":observations})
		check("live processed scale transition leaves neutral torso proxy clear at "+str(scale),torso_clear)
	world.set_process(false)
	check("atlas presentation preserves actual authority",world.army.report()==before)
	# The resized signal must follow the actual integrated combat HUD footprint,
	# not an isolated atlas with an assumed 300px card.
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(960,540);await frames();world._layout_world_hud();await frames()
	var old_top:float=world.rama_hud.offset_top
	world.rama_hud.offset_top=old_top-24;await frames()
	var expected:float=root.get_visible_rect().size.y+world.rama_hud.offset_top-12-world.hud.get_node("TraversalStatus").size.y
	check("combat HUD resize immediately updates atlas peer placement",is_equal_approx(world.hud.get_node("TraversalStatus").position.y,expected),{"actual":world.hud.get_node("TraversalStatus").position.y,"expected":expected,"offset_top":world.rama_hud.offset_top,"hud_size":str(world.rama_hud.size),"signal_connected":world.rama_hud.resized.is_connected(world._layout_world_hud)})
	world.rama_hud.offset_top=old_top
	Bindings.bindings=original_bindings
	InputMap.action_erase_events("world_overview")
	for event in original_events:InputMap.action_add_event("world_overview",event)
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"sources":{},"scope":"Actual integrated native world nodes and bundled-font headless layout; physical/logical viewport stretch, enlarged key text, synthetic active InputMap/binding override without saved preference, complete overview key and pause visibility, actual spawn/deck geometry. Includes constrained640×360/768×432/853×480 composite, staged real traversal-source states, and world-process-active production scale1→1.5→2→1 transitions without manual repair, all12observed frames per scale and existing neutral torso projection proxy. No rasterized pixels, mouse/OS input or graphical acceptance."}
	for path in ["res://scripts/world_atlas.gd","res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd","res://scripts/input_bindings.gd","res://assets/world/confluence-map.json",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;world.queue_free();await frames(6);quit(0 if result.passed else 1)
