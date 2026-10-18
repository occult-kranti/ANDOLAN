extends SceneTree
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Controls = preload("res://scripts/controls_overlay.gd")
const Effects = preload("res://scripts/rama_ability_effects.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks:Array[Dictionary]=[]
var before:Dictionary={}
func _initialize()->void:
	call_deferred("run")
func frames(n:int=4)->void:
	for unused in n:await process_frame
func press(shift:bool)->void:
	for down in [true,false]:
		var event:=InputEventKey.new()
		event.keycode=KEY_TAB;event.physical_keycode=KEY_TAB;event.shift_pressed=shift;event.pressed=down
		root.push_input(event)
		await process_frame
func current()->String:
	var focused:Control=root.gui_get_focus_owner()
	return str(focused.get_path()) if is_instance_valid(focused) else "<none>"
func check(name_:String,passed:bool,detail:Dictionary={})->void:
	checks.append({"name":name_,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",name_," ",JSON.stringify(detail))
func pins()->Dictionary:
	var result:Dictionary={}
	for path in ["res://scripts/rama_hero_panel.gd","res://scripts/controls_overlay.gd","res://scripts/rama_ability_effects.gd","res://scripts/input_bindings.gd","res://scripts/hero_ui_theme.gd","res://scripts/courtyard.gd"]:result[path]=FileAccess.get_sha256(path)
	return result
func run()->void:
	before=pins()
	Bindings.install("user://focus-recovery.cfg")
	root.size=Vector2i(960,540);root.content_scale_size=root.size
	var host:=Control.new();host.process_mode=Node.PROCESS_MODE_ALWAYS;root.add_child(host)
	var effects:=Effects.new();host.add_child(effects)
	var guide:=Guide.new();host.add_child(guide);guide.configure_effects(effects);guide.open();await frames()
	guide.ability_buttons.kodanda.grab_focus();await press(true)
	check("guide existing first-control backward wrap reaches Close",root.gui_get_focus_owner()==guide.close_button,{"actual":current(),"expected":str(guide.close_button.get_path())})
	guide.reduced_motion_button.grab_focus()
	var before_disposal:=current();effects.queue_free();await frames()
	var after_disposal:=current()
	check("receiver disposal disables focused options",guide.reduced_effects_button.disabled and guide.reduced_motion_button.disabled,{"before":before_disposal,"after":after_disposal})
	await press(true)
	check("guide backward recovery after actual receiver disposal reaches last enabled control",root.gui_get_focus_owner()==guide.close_button,{"before_key":after_disposal,"actual":current(),"expected":str(guide.close_button.get_path())})
	root.gui_release_focus();await press(true)
	check("guide explicit unclaimed backward recovery reaches last enabled control",root.gui_get_focus_owner()==guide.close_button,{"actual":current(),"expected":str(guide.close_button.get_path())})
	root.gui_release_focus();await press(false)
	check("guide unclaimed forward recovery reaches first enabled control",root.gui_get_focus_owner()==guide.ability_buttons.kodanda,{"actual":current()})
	guide.close()
	var controls:=Controls.new();host.add_child(controls);controls.open();await frames();root.gui_release_focus();await press(true)
	check("shared ControlsOverlay unclaimed backward recovery reaches Done",root.gui_get_focus_owner()==controls.done_button,{"actual":current(),"expected":str(controls.done_button.get_path())})
	controls.close();host.queue_free();await frames()
	var after:=pins();check("all inspected runtime sources unchanged",before==after)
	var result:={"passed":checks.all(func(c):return c.passed),"count":checks.size(),"checks":checks,"source_before":before,"source_after":after,"engine":Engine.get_version_info(),"scope":"Headless actual shared 2D guide and controls components, viewport-dispatched Tab. Receiver disposal is an explicit component-lifetime counterexample; gui_release_focus is a separate staged boundary. No OS-input, rendered or package qualification. No production source edits."}
	FileAccess.open("/tmp/yuga-w5-focus-recovery-r1/report.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
