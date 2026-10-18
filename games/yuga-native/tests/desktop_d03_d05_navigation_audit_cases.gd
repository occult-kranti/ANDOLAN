extends SceneTree
## Actual compact title/help/remap/film routes. No fault injection or runtime edits.
const Bindings=preload("res://scripts/input_bindings.gd")
var output:="/tmp/desktop-d03-d05-navigation.json"
var checks:Array[Dictionary]=[]
var sources:={}
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func frames(n:=5)->void:
	for unused in n:await process_frame
func key(code:Key)->void:
	for down in [true,false]:
		var event:=InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event);await frames(2)
func activate(control:Control)->void:
	control.grab_focus();await key(KEY_ENTER);await frames()
func check(label:String,passed:bool,detail:Dictionary={})->void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)
func scene(path:String)->bool:
	var limit:=Time.get_ticks_msec()+20000
	while Time.get_ticks_msec()<limit:
		await process_frame
		var loader:=root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if is_instance_valid(loader) and loader.phase==&"error":return false
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path and (not is_instance_valid(loader) or loader.phase==&"done"):
			await frames();return true
	return false
func run()->void:
	for path in ["res://scripts/courtyard.gd","res://scripts/launch_shell.gd","res://scripts/combat_film.gd","res://scripts/controls_overlay.gd","res://scripts/input_bindings.gd","res://scripts/scene_transition.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]:sources[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=2.0
	change_scene_to_file("res://scenes/courtyard.tscn")
	if not await scene("res://scenes/courtyard.tscn"):
		check("Actual courtyard starts",false);finish();return
	for mode in ["train","world"]:
		var court:Node=current_scene
		var shell:Control=court.main_panel
		await activate(shell.train_mode_button if mode=="train" else shell.world_mode_button)
		var help_opener:Button=shell.find_child("Quit",true,false)
		help_opener.grab_focus();await key(KEY_F2)
		var help_scroll:ScrollContainer=court.help_panel.get_node("Card/Scroll")
		await key(KEY_END)
		var bar:=help_scroll.get_v_scroll_bar()
		check(mode+" help reaches full compact text through End",court.help_panel.visible and absf(float(help_scroll.scroll_vertical)-(bar.max_value-bar.page))<=1 and shell.selected_mode==mode)
		await key(KEY_F2);await frames()
		check(mode+" F2 returns exact lower title opener and selection",shell.visible and not court.help_panel.visible and root.gui_get_focus_owner()==help_opener and shell.scroll.get_global_rect().encloses(help_opener.get_global_rect()) and shell.selected_mode==mode)
		var settings_opener:Button=shell.find_child("Settings",true,false)
		await activate(settings_opener)
		await activate(court.controls_button)
		var overlay:Control=court.controls_overlay
		var old_key:int=Bindings.current().reload
		await activate(overlay.binding_buttons.reload)
		await key(KEY_W)
		await key(KEY_ESCAPE)
		check(mode+" compact remap conflict cancels without changing active key",overlay.visible and overlay.capture_action.is_empty() and Bindings.current().reload==old_key)
		await key(KEY_ESCAPE);await frames()
		var settings_scroll:ScrollContainer=court.settings_panel.get_node("Card/Scroll")
		check(mode+" remap close reveals exact settings opener",not overlay.visible and court.settings_panel.visible and root.gui_get_focus_owner()==court.controls_button and settings_scroll.get_global_rect().encloses(court.controls_button.get_global_rect()),{"opener":str(court.controls_button.get_global_rect()),"scroll":str(settings_scroll.get_global_rect())})
		await key(KEY_ESCAPE);await frames()
		check(mode+" settings return preserves original title opener",shell.visible and not court.settings_panel.visible and root.gui_get_focus_owner()==settings_opener and shell.selected_mode==mode)
		var previous:WeakRef=weakref(court)
		await activate(shell.film_button)
		var film_open:=await scene("res://scenes/combat_film.tscn")
		check(mode+" keyboard Watch duel opens actual scripted film",film_open and current_scene.get("ready_to_play")==true)
		if not film_open:finish();return
		await key(KEY_ESCAPE)
		var returned:=await scene("res://scenes/courtyard.tscn")
		var expected:="Begin bow training" if mode=="train" else "Enter Confluence"
		check(mode+" real duel return preserves practice and usable primary",returned and not is_instance_valid(previous.get_ref()) and current_scene.main_panel.selected_mode==mode and current_scene.main_panel.primary_button.text.begins_with(expected) and root.gui_get_focus_owner()==current_scene.main_panel.primary_button and not current_scene.started and not paused)
		if not returned:finish();return
	finish()
func finish()->void:
	var stable:=true
	for path in sources:stable=stable and sources[path]==FileAccess.get_sha256(path)
	check("Audited navigation sources unchanged",stable)
	var passed:=checks.all(func(row):return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":sources,"scope":"Actual imported courtyard/film and real viewport key dispatch at physical960x540/base1280x720/200% UI scale. Both practice modes; lower-opener Help, real conflict/cancel nested remap/settings and film scene replacement. No injected failure, OS input, renderer or new artwork claim."},"  ")+"\n")
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	current_scene=null
	var loader:=root.get_node_or_null("YugaSceneTransitionLayer")
	if loader:loader.queue_free()
	await frames(8);quit(0 if passed else 1)
