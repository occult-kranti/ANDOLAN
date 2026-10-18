extends SceneTree
const Guide := preload("res://scripts/rama_hero_panel.gd")
const Effects := preload("res://scripts/rama_ability_effects.gd")
const Bindings := preload("res://scripts/input_bindings.gd")
var output := "/tmp/ui-u5-effect-feedback.json"
var checks: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func frames() -> void:
	for unused in 6: await process_frame

func press() -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=KEY_ENTER;event.physical_keycode=KEY_ENTER;event.pressed=down
		root.push_input(event)
		await process_frame

func check(label: String, passed: bool, detail: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func visible_feedback(guide: Control) -> bool:
	var page: Rect2 = guide.details_scroll.get_global_rect()
	return page.encloses(guide.effects_notice.get_global_rect()) and page.encloses(guide.reduced_motion_button.get_global_rect()) and root.gui_get_focus_owner()==guide.reduced_motion_button

func run() -> void:
	Bindings.install("user://u5-feedback.cfg")
	var receiver := Effects.new()
	root.add_child(receiver)
	var guide := Guide.new()
	root.add_child(guide)
	guide.configure_effects(receiver)
	var recovery := Button.new()
	recovery.text="Recovery owner"
	root.add_child(recovery)
	for size_ in [Vector2i(1280,720),Vector2i(960,540)]:
		root.size=size_;root.content_scale_size=size_
		Bindings.config_path="user://u5-feedback.cfg"
		guide.select_ability("dawn_volley")
		guide.open()
		await frames()
		guide.reduced_motion_button.grab_focus()
		await frames()
		await press()
		await frames()
		check("Saved feedback and focused toggle remain visible "+str(size_),visible_feedback(guide) and guide.effects_notice.text.contains("saved"),{"scroll":guide.details_scroll.scroll_vertical,"page":str(guide.details_scroll.get_global_rect()),"notice":str(guide.effects_notice.get_global_rect())})
		var active: bool = receiver.report().reduced_motion
		Bindings.config_path="user://missing-u5/preferences.cfg"
		await press()
		await frames()
		check("Failed-write reason and unchanged focused toggle remain visible "+str(size_),visible_feedback(guide) and receiver.report().reduced_motion==active and guide.effects_notice.text.contains("Could not save"))
		guide.close()
	Bindings.config_path="user://u5-feedback.cfg"
	guide.open()
	await frames()
	guide.reduced_motion_button.grab_focus()
	await frames()
	guide._change_effect_option(not receiver.report().reduced_motion,"reduced_motion")
	guide.select_ability("kodanda")
	guide.ability_buttons.kodanda.grab_focus()
	await frames()
	check("Newer ability selection cancels stale feedback reveal",root.gui_get_focus_owner()==guide.ability_buttons.kodanda and guide.details_scroll.scroll_vertical==0)
	guide.reduced_motion_button.grab_focus()
	await frames()
	guide._change_effect_option(not receiver.report().reduced_motion,"reduced_motion")
	guide.close_button.grab_focus()
	var scroll_before: int = guide.details_scroll.scroll_vertical
	await frames()
	check("Newer focus cancels stale feedback reveal without scrolling",root.gui_get_focus_owner()==guide.close_button and guide.details_scroll.scroll_vertical==scroll_before)
	guide.reduced_motion_button.grab_focus()
	await frames()
	guide._change_effect_option(not receiver.report().reduced_motion,"reduced_motion")
	guide.close()
	recovery.grab_focus()
	await frames()
	check("Closed guide cannot scroll or steal recovery focus",root.gui_get_focus_owner()==recovery and not guide.visible)
	guide.open()
	await frames()
	guide.reduced_motion_button.grab_focus()
	await frames()
	guide._change_effect_option(not receiver.report().reduced_motion,"reduced_motion")
	await process_frame
	root.remove_child(guide)
	recovery.grab_focus()
	await frames()
	check("Detached guide drops pending feedback reveal",root.gui_get_focus_owner()==recovery)
	guide.free();receiver.free();recovery.free()
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"guide_sha256":FileAccess.get_sha256("res://scripts/rama_hero_panel.gd"),"test_sha256":FileAccess.get_sha256(get_script().resource_path),"scope":"Native2D headless input/containment and lifetime checks at1280x720/960x540. Failure path is isolated missing settings directory; no renderer/OS file-dialog claim."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
