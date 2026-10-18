extends SceneTree
## Two independent processes share one isolated user directory. The writer also
## stages a directory at the save pathname to exercise a real failed write.
const Bindings := preload("res://scripts/input_bindings.gd")
var output := ""
var phase := ""
var checks: Array[Dictionary] = []
var sources := {}
var court: Node

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
		if arg.begins_with("--phase="): phase=arg.trim_prefix("--phase=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"detail":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(count:=5) -> void:
	for unused in count: await process_frame

func key(code: Key) -> void:
	for down in [true,false]:
		var event:=InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await frames(2)

func checkbox(caption: String) -> CheckButton:
	for node in court.settings_panel.find_children("*","CheckButton",true,false):
		if node.text==caption:return node
	return null

func mapped_j() -> bool:
	return Bindings.label("pulse")=="J" and InputMap.action_get_events("pulse").any(func(event):return event is InputEventKey and event.physical_keycode==KEY_J)

func settings_match() -> bool:
	return is_equal_approx(court.sensitivity,1.65) and is_equal_approx(court.volume,.25) and court.invert_y and not court.shadows and court.night and not court.full_screen

func run() -> void:
	if output.is_empty() or phase not in ["write","read"] or "--desktop-prefs-fixture" not in OS.get_cmdline_user_args():
		push_error("Requires --desktop-prefs-fixture, --phase=write|read and fresh --report in an isolated XDG directory")
		quit(2);return
	for path in ["res://scripts/courtyard.gd","res://scripts/input_bindings.gd","res://scripts/controls_overlay.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_ability_effects.gd",get_script().resource_path]:sources[path]=FileAccess.get_sha256(path)
	if phase=="write" and (FileAccess.file_exists(Bindings.SAVE_PATH) or DirAccess.dir_exists_absolute(Bindings.SAVE_PATH)):
		push_error("Writer refuses existing settings; use a fresh isolated user directory")
		quit(2);return
	var initial_hash:=FileAccess.get_sha256(Bindings.SAVE_PATH) if FileAccess.file_exists(Bindings.SAVE_PATH) else ""
	court=load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court);current_scene=court
	await frames()
	court._open_settings(true)
	await frames()
	if phase=="write":
		check("Fresh writer starts with default keys and no saved file",initial_hash.is_empty() and Bindings.current()==Bindings.DEFAULTS)
		court.settings_panel.get_node("Card/Scroll/Content/Sensitivity").value=1.65
		court.settings_panel.get_node("Card/Scroll/Content/Volume").value=.25
		checkbox("Invert vertical aim").button_pressed=true
		checkbox("Dynamic sun shadows").button_pressed=false
		checkbox("Moonlit courtyard").button_pressed=true
		check("Real Settings callbacks save and apply aim sound and display values",settings_match() and court.settings_notice.text=="Changes saved on this computer.")
	else:
		check("Independent process loads saved settings into real controls and player",not initial_hash.is_empty() and settings_match() and is_equal_approx(court.player.sensitivity,.0024*1.65) and court.player.invert_y and is_equal_approx(court.settings_panel.get_node("Card/Scroll/Content/Volume").value,.25),{"initial_sha256":initial_hash,"user_directory":OS.get_user_data_dir()})
	court._open_controls()
	await frames()
	if phase=="write":
		court.controls_overlay.begin_capture("pulse")
		await key(KEY_J)
	check("Saved J binding reaches InputMap and the real mapping control",mapped_j() and court.controls_overlay.binding_buttons.pulse.text=="J" and court.controls_overlay.capture_action.is_empty())
	var before_conflict:=FileAccess.get_sha256(Bindings.SAVE_PATH)
	court.controls_overlay.begin_capture("pulse")
	await key(KEY_W)
	check("Conflicting remap leaves the save and active mapping exact",court.controls_overlay.capture_action=="pulse" and court.controls_overlay.status.text.contains("already assigned") and mapped_j() and FileAccess.get_sha256(Bindings.SAVE_PATH)==before_conflict)
	await key(KEY_ESCAPE)
	check("Capture cancel preserves its owner and existing mapping",court.controls_overlay.visible and court.controls_overlay.capture_action.is_empty() and mapped_j() and FileAccess.get_sha256(Bindings.SAVE_PATH)==before_conflict)
	court.controls_overlay.close();court._close_settings();court._open_hero()
	await frames()
	if phase=="write":
		court.hero_panel.reduced_effects_button.grab_focus();await key(KEY_ENTER)
		court.hero_panel.reduced_motion_button.grab_focus();await key(KEY_ENTER)
	check("Guide loads saved remap and both real effect receiver options",court.hero_panel.ability_buttons.piercing_dawn.text.begins_with("J") and court.hero_panel.reduced_effects_button.button_pressed and court.hero_panel.reduced_motion_button.button_pressed and court.rama_effects.report().reduced_effects and court.rama_effects.report().reduced_motion)
	if phase=="write":await blocked_write()
	else:court.hero_panel.close()
	var config:ConfigFile=Bindings.read_config().config
	check("Writes retain every other settings section",is_equal_approx(config.get_value("controls","sensitivity",0),1.65) and config.get_value("controls","invert_y",false) and is_equal_approx(config.get_value("audio","volume",0),.25) and not config.get_value("video","shadows",true) and config.get_value("video","night",false) and config.get_value("rama_effects","reduced_effects",false) and config.get_value("rama_effects","reduced_motion",false))
	if phase=="read":check("Opening and cancelling after relaunch never rewrites saved bytes",FileAccess.get_sha256(Bindings.SAVE_PATH)==initial_hash)
	await finish()

func blocked_write() -> void:
	var original:=FileAccess.get_sha256(Bindings.SAVE_PATH)
	var backup:=Bindings.SAVE_PATH+".d05-fixture-backup"
	var moved:=DirAccess.rename_absolute(Bindings.SAVE_PATH,backup)==OK
	var blocked:=moved and DirAccess.make_dir_absolute(Bindings.SAVE_PATH)==OK
	check("Fixture creates a real non-writable save target with exact original backup",blocked and FileAccess.get_sha256(backup)==original)
	if not blocked:
		if moved:DirAccess.rename_absolute(backup,Bindings.SAVE_PATH)
		court.hero_panel.close();return
	court.hero_panel.reduced_motion_button.grab_focus();await key(KEY_ENTER)
	check("Failed ability preference write rolls back the toggle and real receiver",court.rama_effects.report().reduced_motion and court.hero_panel.reduced_motion_button.button_pressed and court.hero_panel.effects_notice.text.contains("Could not save") and FileAccess.get_sha256(backup)==original,{"notice":court.hero_panel.effects_notice.text})
	court.hero_panel.close()
	court._open_settings(true);court._open_controls()
	court.controls_overlay.begin_capture("pulse");await key(KEY_K)
	check("Failed remap write retains J with visible failure and capture available",mapped_j() and court.controls_overlay.capture_action=="pulse" and court.controls_overlay.status.text.contains("could not be saved") and FileAccess.get_sha256(backup)==original,{"notice":court.controls_overlay.status.text})
	await key(KEY_ESCAPE);court.controls_overlay.close();court._close_settings()
	var restored:=DirAccess.remove_absolute(Bindings.SAVE_PATH)==OK and DirAccess.rename_absolute(backup,Bindings.SAVE_PATH)==OK
	check("Fixture restores exactly the original valid save",restored and FileAccess.get_sha256(Bindings.SAVE_PATH)==original)
	court._open_settings(true);court._open_controls();court.controls_overlay.begin_capture("pulse");await key(KEY_K)
	check("Retry after storage recovery commits a new mapping without restarting",Bindings.label("pulse")=="K" and court.controls_overlay.capture_action.is_empty())
	court.controls_overlay.begin_capture("pulse");await key(KEY_J)
	check("Restoring J persists while retaining unrelated sections",mapped_j() and Bindings.read_config().config.get_value("controls","bindings",{}).get("pulse")==KEY_J)
	court.controls_overlay.close();court._close_settings()

func finish() -> void:
	check("Relevant runtime and test sources remain exact",sources.keys().all(func(path):return FileAccess.get_sha256(path)==sources[path]))
	var report:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"phase":phase,"process_id":OS.get_process_id(),"user_directory":OS.get_user_data_dir(),"settings_sha256":FileAccess.get_sha256(Bindings.SAVE_PATH),"sources":sources,"scope":"Actual title settings callbacks and native GUI key dispatch across separate headless processes using one isolated XDG namespace. Explicit save-path directory fixture tests blocked writes and recovery. No OS-input, fullscreen/render/audio-quality or package claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	paused=false;current_scene=null;court.queue_free();await frames(8)
	OS.delay_msec(100);await process_frame
	quit(0 if report.passed else 1)
