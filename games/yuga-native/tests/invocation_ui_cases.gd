extends SceneTree
const InvocationPanel = preload("res://scripts/invocation_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var panel: Control
var selected_requests: Array[String] = []
var option_events := []
var closes := 0
var path := ""
var source_before := {}

func check(ok: bool, id: String, details: Dictionary = {}) -> void:
	checks.append({"id":id,"passed":ok,"details":details})
	if not ok: push_error(id)

func _initialize() -> void: call_deferred("_run")

func _run() -> void:
	for file in ["res://scripts/invocation_panel.gd","res://scripts/input_bindings.gd","res://assets/design/hero-codex.json","res://assets/design/native-ultimate-rules.json","res://tests/invocation_ui_cases.gd"]:
		source_before[file] = FileAccess.get_sha256(file)
	path = "user://invocation-ui-test-" + str(Time.get_ticks_usec()) + ".cfg"
	Bindings.install(path)
	var seed := Bindings.merge_settings({"audio":{"volume":0.37},"video":{"night":true}},path)
	check(seed.ok,"isolated preferences seeded")
	var back := Button.new()
	back.text = "World pause return"
	root.add_child(back)
	panel = InvocationPanel.new()
	root.add_child(panel)
	panel.invocation_selected.connect(func(id: String): selected_requests.append(id))
	panel.effects_options_changed.connect(func(value: Dictionary): option_events.append(value))
	panel.closed.connect(func(): closes += 1)
	check(panel.configure(),"complete catalogue and native rules configure")
	check(panel.report().hero_count == 14 and panel.report().focusable_count == 19,"all fourteen invocations and nineteen focus controls exist")
	check(panel.update_session(_state("rama",7.5)),"session accepts authoritative cooldown")
	panel.open(back)
	await _frames(3)
	check(root.gui_get_focus_owner() == panel.hero_buttons.rama,"open focuses current invocation")
	check(panel.report().selected_hero == "rama" and panel.report().preview_id == "rama","opening uses accepted selection")
	panel.hero_buttons.ravana.pressed.emit()
	check(panel.report().preview_id == "ravana" and panel.report().selected_hero == "rama" and panel.report().cooldown_remaining == 7.5,"preview never changes accepted selection or recovery")
	check(selected_requests.is_empty(),"browsing emits no selection request")
	panel.choose_button.pressed.emit()
	check(selected_requests == ["ravana"] and panel.report().selected_hero == "rama" and panel.report().cooldown_remaining == 7.5,"choose emits request without optimistic selection or timer reset")
	panel.update_session(_state("ravana",7.5))
	check(panel.report().selected_hero == "ravana" and panel.report().cooldown_remaining == 7.5,"session acknowledgement preserves shared cooldown")
	var bad_state := _state("missing",0)
	check(not panel.update_session(bad_state) and panel.report().selected_hero == "ravana","unknown session selection rejected atomically")
	bad_state = _state("rama",NAN)
	check(not panel.update_session(bad_state) and panel.report().cooldown_remaining == 7.5,"nonfinite cooldown rejected")
	bad_state = _state("rama",13)
	check(not panel.update_session(bad_state),"oversized cooldown rejected")
	bad_state = _state("rama",0)
	bad_state.suspended = "true"
	check(not panel.update_session(bad_state),"mistyped suspended flag rejected")
	for id in panel.hero_buttons:
		panel.hero_buttons[id].pressed.emit()
		var state: Dictionary = panel.report()
		check(not state.payload.is_empty() and not state.geometry.is_empty() and not state.counterplay.is_empty(),"readable payload geometry counterplay: " + id)
	panel.hero_buttons.rama.pressed.emit()
	check("32 damage" in panel.report().payload and "per arrow" in panel.report().payload and "3 arrows" in panel.report().geometry,"Rama renders actual three-arrow native payload")
	panel.hero_buttons.hanuman.pressed.emit()
	check("65 damage" in panel.report().payload and "45 health" in panel.report().payload and "does not move Rama" in panel.report().counterplay,"Hanuman projection is distinguished from avatar movement")
	panel.hero_buttons.sita.pressed.emit()
	check("70 allied shield" in panel.report().payload and "9 allied health/s" in panel.report().payload,"Sita renders native shield and heal rate")
	panel.hero_buttons.ulupi.pressed.emit()
	check("55%" in panel.report().payload and "12 enemy damage/s" in panel.report().payload,"Ulupi renders actual slow and per-second payload")
	panel.hero_buttons.subhadra.pressed.emit()
	check("2 bow sentinels" in panel.report().payload and "9 s" in panel.report().payload,"Subhadra displays bounded actual summon pair")
	panel.hero_buttons.hidimbi.pressed.emit()
	check("2 spear sentinels" in panel.report().payload,"Hidimbi displays spear pair")
	# Fixed viewport layout and every selectable role, with actual container sizes.
	var layouts := []
	for viewport in [Vector2i(960,600),Vector2i(1280,720)]:
		root.size = viewport
		root.content_scale_size = viewport
		await _frames(4)
		var errors := []
		for id in panel.hero_buttons:
			panel.hero_buttons[id].pressed.emit()
			await _frames(2)
			var state: Dictionary = panel.report()
			var frame := Rect2(Vector2.ZERO,Vector2(viewport))
			if not frame.encloses(state.card_rect): errors.append(id + " card outside viewport")
			for name in state.control_rects:
				var rect: Rect2 = state.control_rects[name]
				if not frame.encloses(rect) or rect.size.x < 36 or rect.size.y < 36: errors.append(id + " clipped/small control " + name)
		layouts.append({"viewport":str(viewport),"card":str(panel.report().card_rect),"errors":errors})
		check(errors.is_empty(),"all fourteen selections fit " + str(viewport),layouts.back())
	panel.hero_buttons.rama.grab_focus()
	await _frames(1)
	_key(KEY_RIGHT)
	check(root.gui_get_focus_owner() == panel.hero_buttons.ravana and panel.report().preview_id == "ravana","right arrow previews next column")
	_key(KEY_DOWN)
	check(root.gui_get_focus_owner() == panel.hero_buttons.duryodhana,"down arrow moves one roster row")
	_key(KEY_ENTER)
	check(selected_requests.back() == "duryodhana","Enter requests focused invocation")
	panel.hero_buttons.rama.grab_focus()
	await _frames(1)
	var focused := []
	for i in range(19):
		focused.append(root.gui_get_focus_owner().get_instance_id())
		_key(KEY_TAB)
	check(focused.size() == 19 and _unique_count(focused) == 19 and root.gui_get_focus_owner() == panel.hero_buttons.rama,"Tab cycle reaches every focusable control exactly once")
	_key(KEY_TAB,true)
	check(root.gui_get_focus_owner() == panel.close_button,"Shift Tab wraps to Back")
	root.size = Vector2i(960,600)
	root.content_scale_size = Vector2i(960,600)
	panel.hero_buttons.sita.pressed.emit()
	await _frames(4)
	panel.details_scroll.grab_focus()
	await _frames(1)
	_key(KEY_PAGEDOWN)
	var scroll_before: int = panel.details_scroll.scroll_vertical
	check(scroll_before > 0,"keyboard Page Down advances an actually overflowing detail",{"scroll":scroll_before,"viewport":"960x600"})
	panel.update_session(_state("ravana",7.5))
	await _frames(2)
	check(panel.details_scroll.scroll_vertical == scroll_before,"session refresh preserves reading scroll")
	panel.set_available(false,"Practice is unavailable after a result.")
	var requests_before := selected_requests.size()
	panel.choose_button.pressed.emit()
	check(panel.report().choose_disabled and selected_requests.size() == requests_before and "unavailable" in panel.report().status,"unavailable selection explains disabled action")
	panel.set_available(true)
	panel.reduced_effects_button.button_pressed = true
	panel.reduced_motion_button.button_pressed = true
	check(option_events.size() == 2 and panel.options().reduced_effects and panel.options().reduced_motion,"both effect options emit saved bool preferences")
	var saved := Bindings.read_config(path)
	check(saved.ok and saved.config.get_value("invocations","reduced_effects") == true and saved.config.get_value("invocations","reduced_motion") == true,"effect preferences persisted in invocation section")
	check(saved.config.get_value("audio","volume") == 0.37 and saved.config.get_value("video","night") == true,"saving effects preserves other settings sections")
	var detached: Dictionary = panel.options()
	detached.reduced_effects = false
	check(panel.options().reduced_effects,"external options dictionary cannot mutate panel state")
	var remap := Bindings.set_binding("ultimate",KEY_T)
	check(remap.ok,"ultimate remaps in shared binding owner")
	panel.update_session(_state("ravana",0))
	panel.set_notice("")
	check("T to invoke" in panel.report().status,"cast hint reads actual remapped control")
	Input.action_press("move_forward")
	Input.action_press("fire")
	_key(KEY_ESCAPE)
	check(not panel.visible and closes == 1 and not Input.is_action_pressed("move_forward") and not Input.is_action_pressed("fire"),"Escape closes and neutralizes held gameplay")
	check(root.gui_get_focus_owner() == back,"closing restores external return focus")
	panel.open(back)
	await _frames(2)
	check(panel.options().reduced_effects and panel.options().reduced_motion,"reopen restores saved effect preferences")
	var events_before_external_edit := option_events.size()
	Bindings.merge_settings({"invocations":{"reduced_effects":false,"reduced_motion":true}},path)
	panel.open(back)
	await _frames(2)
	check(not panel.options().reduced_effects and panel.options().reduced_motion and option_events.size() == events_before_external_edit + 1 and option_events.back() == panel.options(),"external settings reload synchronizes live effects")
	_key(KEY_F3)
	check(not panel.visible and closes == 2,"bound selector key closes without reopening")
	panel.close()
	check(closes == 2,"repeated close does not emit twice")
	var catalogue: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(InvocationPanel.CATALOGUE_PATH))
	var rules: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(InvocationPanel.RULES_PATH))
	var duplicate := rules.duplicate(true)
	duplicate.rules[1].hero_id = "rama"
	check(not panel.configure(catalogue,duplicate) and panel.report().hero_count == 14,"duplicate rule rejected without discarding good catalogue")
	var malformed := rules.duplicate(true)
	malformed.rules[0].effects[0].amount = NAN
	check(not panel.configure(catalogue,malformed),"nonfinite payload rejected")
	malformed = rules.duplicate(true)
	malformed.rules[0].effects[0].amount = true
	check(not panel.configure(catalogue,malformed),"boolean amount rejected")
	# A failed save must preserve invalid original bytes and restore saved state.
	var file := FileAccess.open(path,FileAccess.WRITE)
	file.store_string("not valid config = (((")
	file.close()
	var original := FileAccess.get_file_as_bytes(path)
	panel.open(back)
	await _frames(2)
	var event_count := option_events.size()
	panel.reduced_effects_button.button_pressed = true
	check(option_events.size() == event_count and FileAccess.get_file_as_bytes(path) == original and "Could not save" in panel.report().status,"invalid config save reports failure and preserves original bytes")
	back.queue_free()
	await _frames(1)
	panel.close()
	check(not panel.visible,"freed return focus is safe")
	var hashes_same := true
	for file_path in source_before: hashes_same = hashes_same and FileAccess.get_sha256(file_path) == source_before[file_path]
	check(hashes_same,"sources unchanged during test")
	var passed := true
	for item in checks: passed = passed and item.passed
	var report := {"passed":passed,"checks":checks,"source_sha256":source_before,"engine":Engine.get_version_info().string,
		"layouts":layouts,"scope":"Actual Godot Control layout/focus and headless input-method injection, source-derived text, immutable selection/cooldown display and isolated settings persistence. Not OS input, art/render acceptance or online gameplay."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var output := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if output: output.store_string(JSON.stringify(report,"\t") + "\n")
			else: passed = false
	print("YUGA_INVOCATION_UI_CASES ", JSON.stringify({"passed":passed,"checks":checks.size(),"layouts":layouts}))
	panel.free()
	DirAccess.remove_absolute(path)
	Bindings.install()
	quit(0 if passed else 1)

func _state(id: String, cooldown: float) -> Dictionary:
	return {"selected_hero":id,"cooldown_remaining":cooldown,"active_phase":"ready","suspended":true}

func _frames(count: int) -> void:
	for i in range(count): await process_frame

func _key(key: int, shift: bool = false) -> void:
	var event := InputEventKey.new()
	event.keycode = key
	event.physical_keycode = key
	event.pressed = true
	event.shift_pressed = shift
	panel._input(event)

func _unique_count(items: Array) -> int:
	var unique := {}
	for item in items: unique[item] = true
	return unique.size()
