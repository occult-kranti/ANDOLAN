extends SceneTree
## Real guide at production logical scaling; keyboard scroll/return, no pixels.
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var output := "/tmp/desktop-s4-guide.json"
var checks: Array[Dictionary] = []
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")
func frames(count := 5) -> void:
	for unused in count: await process_frame
func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode = code; event.physical_keycode = code; event.pressed = down
		root.push_input(event)
		await frames(2)
func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)
func run() -> void:
	Bindings.install("user://desktop-s4-guide.cfg")
	var remapped := true
	for pair in [["jump",KEY_J],["sprint",KEY_K],["descend",KEY_L],["pulse",KEY_SPACE],["dash",KEY_SHIFT],["guardian_circle",KEY_CTRL]]:
		remapped = Bindings.set_binding(pair[0],pair[1]).ok and remapped
	check("Real supported long key labels saved",remapped)
	var source := FileAccess.get_sha256("res://scripts/rama_hero_panel.gd")
	root.size = Vector2i(960,540)
	root.content_scale_size = Vector2i(1280,720)
	var host := Control.new()
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	root.add_child(host)
	var opener := Button.new()
	opener.text = "Guide opener"
	host.add_child(opener)
	var guide := Guide.new()
	host.add_child(guide)
	for scale in [1.0,1.5,2.0]:
		root.content_scale_factor = scale
		opener.grab_focus()
		guide.open("confluence",opener)
		await frames(8)
		var view := root.get_visible_rect()
		check("Guide plate and Back fit at scale " + str(scale),view.encloses(guide.card.get_global_rect()) and guide.card.get_global_rect().encloses(guide.close_button.get_global_rect()),{"viewport":str(view),"card":str(guide.card.get_global_rect()),"back":str(guide.close_button.get_global_rect())})
		for id in ["kodanda","guardian_circle","dawn_volley"]:
			guide.select_ability(id)
			guide.ability_buttons[id].grab_focus()
			await frames()
			var button: Button = guide.ability_buttons[id]
			var bar := guide.details_scroll.get_v_scroll_bar()
			await key(KEY_END)
			check(id + " details and selected control reachable at scale " + str(scale),guide.abilities_scroll.get_global_rect().encloses(button.get_global_rect()) and guide.details_scroll.size.x >= 260 and guide.details_scroll.size.y >= 60 and absf(float(guide.details_scroll.scroll_vertical)-(bar.max_value-bar.page)) <= 1,{"list":str(guide.abilities_scroll.get_global_rect()),"details":str(guide.details_scroll.get_global_rect()),"button":str(button.get_global_rect()),"selection":guide.selected_id,"button_text":button.text,"button_min":str(button.get_combined_minimum_size())})
			await key(KEY_HOME)
			check(id + " Home preserves selection at scale " + str(scale),guide.details_scroll.scroll_vertical == 0 and guide.selected_id == id and root.gui_get_focus_owner() == button)
		await key(KEY_ESCAPE)
		check("Escape restores exact keyboard opener at scale " + str(scale),not guide.visible and root.gui_get_focus_owner() == opener)
	var recovery := Button.new()
	recovery.text = "Current recovery owner"
	host.add_child(recovery)
	for invalidation in ["disabled", "focus disabled", "retiring"]:
		opener.disabled = false
		opener.focus_mode = Control.FOCUS_ALL
		guide.open("courtyard",opener)
		await frames()
		if invalidation == "disabled": opener.disabled = true
		elif invalidation == "focus disabled": opener.focus_mode = Control.FOCUS_NONE
		else: opener.queue_free()
		recovery.grab_focus()
		guide.close()
		await frames()
		check("Close preserves current recovery focus when opener becomes " + invalidation,root.gui_get_focus_owner() == recovery)
	check("Guide source stable during observation",source == FileAccess.get_sha256("res://scripts/rama_hero_panel.gd"))
	var passed := checks.all(func(row): return row.passed)
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"count":checks.size(),"checks":checks,"sources":{"res://scripts/rama_hero_panel.gd":source,"fixture":FileAccess.get_sha256(get_script().resource_path)},"scope":"Actual guide, real key dispatch and logical UI scales; no pixels, OS input or live gameplay claim."},"  ")+"\n")
	host.queue_free()
	await frames(8)
	quit(0 if passed else 1)
