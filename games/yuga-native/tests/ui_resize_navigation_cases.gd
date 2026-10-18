extends SceneTree
## Actual Window resize and content scale, retaining the production base canvas.
const SHELL=preload("res://scripts/launch_shell.gd")
var checks:Array[Dictionary]=[]
var output:="/tmp/ui-resize-navigation.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,ok:bool,detail:Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"detail":detail});print("PASS " if ok else "FAIL ",label)
func frames(count:=6) -> void:
	for unused in count:await process_frame
func key(code:Key) -> void:
	for down in [true,false]:
		var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down
		Input.parse_input_event(event);await frames(2)
func button(owner:Node,caption:String) -> Button:
	for item in owner.find_children("*","Button",true,false):
		if item.text==caption:return item
	return null
func resize_to(physical:Vector2i,scale:float) -> void:
	root.size=physical;root.content_scale_factor=scale;await frames()
func run() -> void:
	root.content_scale_size=Vector2i(1280,720)
	var shell:=SHELL.new();root.add_child(shell);await frames()
	check("native menu establishes usable window minimum",root.min_size.x>=960 and root.min_size.y>=540,{"minimum":str(root.min_size)})
	await resize_to(Vector2i(64,64),1.0)
	check("engine rejects an unusable 64x64 window request",root.size.x>=960 and root.size.y>=540,{"actual_window":str(root.size),"logical_canvas":str(root.get_visible_rect().size)})
	await resize_to(Vector2i(1280,720),1.0)
	var target:Button=shell._actions[-1];target.grab_focus();await frames()
	for spec in [[Vector2i(960,540),1.0],[Vector2i(960,540),2.0],[Vector2i(1280,720),1.25],[Vector2i(960,540),1.0]]:
		await resize_to(spec[0],spec[1])
		check("live title resize retains and reveals focus %s x%s"%[spec[0],spec[1]],root.gui_get_focus_owner()==target and shell.scroll.get_global_rect().encloses(target.get_global_rect()),{"viewport":str(root.get_visible_rect()),"focused":str(target.get_global_rect()),"scroll":str(shell.scroll.get_global_rect())})
	shell.queue_free();await frames()
	var court:Node3D=load("res://scenes/courtyard.tscn").instantiate();root.add_child(court);current_scene=court;await frames()
	var opener:Button=button(court.main_panel,"Settings");opener.grab_focus();court._open_settings(true);await frames()
	var scroll:ScrollContainer=court.settings_panel.get_node("Card/Scroll")
	var card:Control=court.settings_panel.get_node("Card")
	for scale in [1.0,1.25,2.0]:
		await resize_to(Vector2i(960,540),scale)
		for amount in [0,100000]:
			scroll.scroll_vertical=amount;await frames()
			check("settings Done stays outside scrolling body at scale%s scroll%s"%[scale,amount],not scroll.is_ancestor_of(court.settings_back) and card.get_global_rect().encloses(court.settings_back.get_global_rect()) and root.get_visible_rect().encloses(court.settings_back.get_global_rect()) and not scroll.get_global_rect().intersects(court.settings_back.get_global_rect()),{"done":str(court.settings_back.get_global_rect()),"body":str(scroll.get_global_rect())})
	var sensitivity:Slider=scroll.get_node("Content/Sensitivity");sensitivity.grab_focus();var before:float=sensitivity.value;await key(KEY_RIGHT)
	var config:=ConfigFile.new();var loaded:=config.load("user://courtyard-settings.cfg")
	check("scaled settings keyboard change still persists real preference",sensitivity.value>before and loaded==OK and is_equal_approx(float(config.get_value("controls","sensitivity",-1)),court.sensitivity) and is_equal_approx(court.player.sensitivity,court.sensitivity*.0024))
	var reachable:=false
	for unused in 20:
		if root.gui_get_focus_owner()==court.settings_back:reachable=true;break
		await key(KEY_TAB)
	check("scaled settings Done is reachable through actual Tab chain",reachable)
	await key(KEY_ENTER)
	check("scaled Done returns exact title opener with practice stopped",not court.settings_panel.visible and court.main_panel.visible and root.gui_get_focus_owner()==opener and not court.started and not court.player.active)
	court.start_training();court.set_paused(true);await resize_to(Vector2i(1280,720),1.0)
	var court_quit:=button(court.pause_panel,"QUIT TO DESKTOP");court_quit.grab_focus();await frames();await resize_to(Vector2i(960,540),2.0)
	check("live courtyard pause resize reveals retained lower action",root.gui_get_focus_owner()==court_quit and court.pause_panel.get_node("Card/Scroll").get_global_rect().encloses(court_quit.get_global_rect()) and paused)
	paused=false;court.queue_free();current_scene=null;await frames()
	await resize_to(Vector2i(1280,720),1.0)
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(world);current_scene=world;await frames();world.set_paused(true)
	var world_quit:=button(world.pause_panel,"Quit game");world_quit.grab_focus();await frames();var clock:float=world.army.elapsed
	await resize_to(Vector2i(960,540),2.0)
	check("live world pause resize reveals retained lower action and holds clock",root.gui_get_focus_owner()==world_quit and world.pause_scroll.get_global_rect().encloses(world_quit.get_global_rect()) and world.army.elapsed==clock and paused)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":{},"scope":"Actual Window size/content_scale_factor mutations with retained1280x720 base, native keyboard dispatch, real persisted preference in isolated test user data. Headless engine boundary; no OS-window-manager/DPI or rasterized acceptance."}
	for path in ["res://scripts/launch_shell.gd","res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;world.queue_free();current_scene=null;await frames();quit(0 if result.passed else 1)
