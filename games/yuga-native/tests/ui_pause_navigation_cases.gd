extends SceneTree
## Real scene/modal authority and keyboard traversal; no renderer or loader mutation.
var checks: Array[Dictionary] = []
var output := "/tmp/ui-pause-navigation.json"
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):output=arg.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,ok:bool,details:Dictionary={}) -> void:
	checks.append({"name":label,"passed":ok,"details":details});print("PASS " if ok else "FAIL ",label)
func frames(count:=3) -> void:
	for unused in count:await process_frame
func key(code:Key,shift:=false) -> void:
	for down in [true,false]:
		var event:=InputEventKey.new();event.keycode=code;event.physical_keycode=code;event.pressed=down;event.shift_pressed=shift
		Input.parse_input_event(event);await frames()
func button(owner:Node,caption:String) -> Button:
	for item in owner.find_children("*","Button",true,false):
		if item.text==caption:return item
	return null
func run() -> void:
	root.size=Vector2i(960,540);root.content_scale_size=root.size
	var court:Node3D=load("res://scenes/courtyard.tscn").instantiate();root.add_child(court);current_scene=court
	await frames()
	check("title starts with one visible owner and no live practice",court.main_panel.visible and not court.started and not court.player.active and not paused)
	court.start_training();court.set_paused(true);await frames()
	var resume:Button=court.resume_button;resume.disabled=true
	var quit_button:=button(court.pause_panel,"QUIT TO DESKTOP");quit_button.grab_focus();await key(KEY_TAB)
	check("courtyard Tab skips disabled pause actions",root.gui_get_focus_owner()!=resume and root.gui_get_focus_owner() is BaseButton and not root.gui_get_focus_owner().disabled)
	resume.disabled=false
	var settings:=button(court.pause_panel,"SETTINGS");settings.grab_focus();court._open_settings(false);await frames();await key(KEY_ESCAPE)
	check("courtyard settings Escape restores exact pause opener",court.pause_panel.visible and paused and root.gui_get_focus_owner()==settings)
	var clock:float=court.rama_runtime.kit.elapsed;await frames(8)
	check("paused navigation holds authoritative kit clock",court.rama_runtime.kit.elapsed==clock)
	court.set_paused(false);check("courtyard resume clears GUI focus and resumes live authority",not paused and root.gui_get_focus_owner()==null and not court.rama_runtime.suspended)
	for code in [KEY_F3,KEY_F2]:
		await key(code);root.focus_exited.emit();await key(KEY_ESCAPE)
		check("focus loss inside courtyard modal returns to pause %s"%code,paused and court.pause_panel.visible and court.rama_runtime.suspended)
		court.set_paused(false)
	court.queue_free();current_scene=null;await frames(4)
	var world:Node3D=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(world);current_scene=world;await frames()
	world.set_paused(true);await frames()
	check("initial pause keeps title and eyebrow above primary visible",world.pause_scroll.scroll_vertical==0)
	var controls:=button(world.pause_panel,"Controls / remap keys");controls.grab_focus();world._open_controls();await frames();await key(KEY_ESCAPE)
	check("world controls Escape restores exact visible opener",world.pause_panel.visible and world.paused and paused and root.gui_get_focus_owner()==controls)
	controls.grab_focus();world._open_controls();await frames();controls.disabled=true;await key(KEY_ESCAPE)
	check("disabled world modal opener falls back to enabled pause action",root.gui_get_focus_owner() is BaseButton and not root.gui_get_focus_owner().disabled and world.pause_panel.is_ancestor_of(root.gui_get_focus_owner()))
	controls.disabled=false
	var volume:Slider=world.pause_panel.get_node("MenuScroll/MenuActions/WorldVolume")
	volume.grab_focus();world._open_controls();await frames();volume.editable=false;await key(KEY_ESCAPE)
	check("read-only world modal opener uses enabled fallback",root.gui_get_focus_owner()!=volume and root.gui_get_focus_owner() is BaseButton and not root.gui_get_focus_owner().disabled)
	volume.editable=true
	volume.grab_focus();await key(KEY_F3);await key(KEY_ESCAPE)
	check("world guide shortcut restores exact pause slider opener",root.gui_get_focus_owner()==volume and world.paused)
	# Pause from actual terminal authority; no UI owns the winner.
	world.set_paused(false);world.army.cores.moon=0;world.army.step_simulation(.05);world.set_paused(true);await frames()
	var restart:=button(world.pause_panel,"Restart lane practice")
	check("terminal pause prioritizes existing restart action",world.army.winner=="sun" and world.outcome_summary.visible and root.gui_get_focus_owner()==restart and world.pause_scroll.scroll_vertical==0)
	check("terminal pause describes world return without claiming continued simulation",button(world.pause_panel,"Return to world")!=null)
	var snapshot:Dictionary=world.army.report();world._layout_pause_panel();world._update_practice_hud();await frames(5)
	check("outcome navigation preserves authority clocks and winner",world.army.report()==snapshot and paused)
	# Restart is the existing route; presentation must recover ordinary primary.
	world._restart_army();world.set_paused(true);await frames()
	var continue_button:=button(world.pause_panel,"Continue practice")
	check("reset restores ordinary Continue focus and clears outcome",world.army.winner.is_empty() and not world.outcome_summary.visible and root.gui_get_focus_owner()==continue_button)
	var inside:bool=root.get_visible_rect().encloses(world.pause_panel.get_global_rect())
	check("compact pause viewport stays within 960x540",inside,{"rect":str(world.pause_panel.get_global_rect())})
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":{},"scope":"Actual headless courtyard/world scenes, dispatched keyboard Escape/Tab, actual staged terminal boundary through army tick, UI read-only authority checks. No renderer or OS-input claim."}
	for path in ["res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;world.queue_free();current_scene=null;await frames(4);quit(0 if result.passed else 1)
