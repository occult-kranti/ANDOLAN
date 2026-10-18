extends SceneTree
## I2 malformed-save sequences through real modal and async scene lifetimes.
const Bindings := preload("res://scripts/input_bindings.gd")
var output := "/tmp/ui-i2-preferences-sequences.json"
var checks: Array[Dictionary] = []
var sources := {}
var sequence_receipts: Array[Dictionary] = []

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames(number := 5) -> void:
	for unused in number: await process_frame

func key(code: Key) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=code;event.physical_keycode=code;event.pressed=down
		root.push_input(event)
		await frames(2)

func wait_scene(path: String) -> bool:
	var deadline := Time.get_ticks_msec()+20000
	while Time.get_ticks_msec()<deadline:
		await process_frame
		var loader := root.get_node_or_null("YugaSceneTransitionLayer/SceneTransition")
		if is_instance_valid(loader) and loader.phase==&"error": return false
		if is_instance_valid(current_scene) and current_scene.scene_file_path==path and (not is_instance_valid(loader) or loader.phase==&"done"):
			await frames()
			return true
	return false

func valid_fixture() -> void:
	# Explicit on-disk replacement fixture, analogous to restoring a valid user
	# backup; the product is never allowed to rewrite the rejected bytes itself.
	var config := ConfigFile.new()
	var bindings: Dictionary = Bindings.DEFAULTS.duplicate()
	bindings.pulse=KEY_J
	config.set_value("controls","bindings",bindings)
	config.set_value("controls","sensitivity",1.4)
	config.set_value("controls","invert_y",true)
	config.set_value("audio","volume",.2)
	config.set_value("video","fullscreen",false)
	config.set_value("video","shadows",false)
	config.set_value("rama_effects","reduced_effects",true)
	config.set_value("rama_effects","reduced_motion",false)
	config.save(Bindings.SAVE_PATH)

func corrupt_fixture(kind: String) -> String:
	if kind=="typed-map":
		var config := ConfigFile.new()
		var bindings: Dictionary = Bindings.DEFAULTS.duplicate()
		bindings.jump=KEY_W
		config.set_value("controls","bindings",bindings)
		config.set_value("controls","sensitivity",[1.4])
		config.set_value("controls","invert_y","true")
		config.set_value("audio","volume","loud")
		config.set_value("video","fullscreen","yes")
		config.set_value("rama_effects","reduced_effects",false)
		config.set_value("rama_effects","reduced_motion","invalid")
		config.save(Bindings.SAVE_PATH)
	else:
		var file := FileAccess.open(Bindings.SAVE_PATH,FileAccess.WRITE)
		file.store_string("[controls]\nbindings=Object(\"Node\")\n" if kind=="unsupported-data" else "#".repeat(Bindings.MAX_CONFIG_BYTES+1))
		file.close()
	return FileAccess.get_sha256(Bindings.SAVE_PATH)

func run() -> void:
	for path in ["res://scripts/courtyard.gd","res://scripts/confluence_world.gd","res://scripts/player.gd","res://scripts/scene_transition.gd","res://scripts/input_bindings.gd","res://scripts/controls_overlay.gd","res://scripts/rama_hero_panel.gd","res://scripts/rama_ability_effects.gd","res://assets/heroes/rama-hero.glb",get_script().resource_path]: sources[path]=FileAccess.get_sha256(path)
	valid_fixture()
	var court: Node = load("res://scenes/courtyard.tscn").instantiate()
	root.add_child(court)
	current_scene=court
	await frames()
	for kind in ["typed-map","unsupported-data","oversized"]:
		court=current_scene
		var original_hash := corrupt_fixture(kind)
		var effect_before: Dictionary = court.rama_effects.report()
		court._open_settings(true)
		court._open_controls()
		court.controls_overlay.begin_capture("jump")
		await key(KEY_W)
		court._on_focus_lost()
		check(kind+" conflict then focus loss retires capture without saving",court.controls_overlay.visible and court.controls_overlay.capture_action.is_empty() and Bindings.label("jump")=="Space" and FileAccess.get_sha256(Bindings.SAVE_PATH)==original_hash)
		court.controls_overlay.close()
		check(kind+" controls close restores its settings owner and opener",court.settings_panel.visible and root.gui_get_focus_owner()==court.controls_button and not court.controls_overlay.visible)
		court._close_settings()
		court.start_training()
		court._open_hero()
		await frames()
		var rejected_message: String = court.hero_panel.effects_notice.text
		court._on_focus_lost()
		if kind!="typed-map":
			court.hero_panel.reduced_motion_button.grab_focus()
			await key(KEY_ENTER)
		check(kind+" guide rejects invalid save during training without partial effect changes",court.rama_effects.report().reduced_effects==effect_before.reduced_effects and court.rama_effects.report().reduced_motion==effect_before.reduced_motion and FileAccess.get_sha256(Bindings.SAVE_PATH)==original_hash and (rejected_message.contains("Invalid") if kind=="typed-map" else court.hero_panel.effects_notice.text.contains("Could not save")),{"notice":court.hero_panel.effects_notice.text})
		court.hero_panel.close()
		check(kind+" focus loss converts temporary guide return into explicit pause",paused and court.pause_panel.visible and not court.hero_panel.visible)
		court.return_to_menu()
		court._open_settings(true)
		court._open_controls()
		court.controls_overlay.begin_capture("reload")
		var old_controls: WeakRef = weakref(court.controls_overlay)
		court.enter_confluence()
		var arrived := await wait_scene("res://scenes/confluence_world.tscn")
		check(kind+" mode change retires pending remap and preserves rejected file",arrived and old_controls.get_ref()==null and FileAccess.get_sha256(Bindings.SAVE_PATH)==original_hash)
		if not arrived:
			await finish()
			return
		var world: Node = current_scene
		check(kind+" new world loads bounded defaults instead of stale valid settings",Bindings.current()==Bindings.DEFAULTS and is_equal_approx(world.player.sensitivity,.0024) and not world.player.invert_y and is_equal_approx(world.audio.volume,.7) and not world.rama_effects.report().reduced_effects and not world.rama_effects.report().reduced_motion)
		world._open_controls()
		world.controls_overlay.begin_capture("reload")
		world._focus_lost()
		await key(KEY_ESCAPE)
		check(kind+" world remap interruption returns to pause without changing bindings",paused and world.pause_panel.visible and not world.controls_overlay.visible and Bindings.label("reload")=="R" and FileAccess.get_sha256(Bindings.SAVE_PATH)==original_hash)
		world.set_paused(false)
		world._open_rama_panel()
		world._focus_lost()
		world.rama_panel.close()
		check(kind+" repeated world guide interruption preserves pause and unavailable HUD",paused and world.pause_panel.visible and not world.rama_panel.visible and not world.rama_hud.slots.any(func(slot):return slot.text.contains("READY")))
		sequence_receipts.append({"kind":kind,"rejected_sha256":original_hash,"still_unchanged":FileAccess.get_sha256(Bindings.SAVE_PATH)==original_hash,"load_notice":Bindings.load_notice})
		valid_fixture()
		var restored_hash := FileAccess.get_sha256(Bindings.SAVE_PATH)
		world.return_to_courtyard()
		arrived = await wait_scene("res://scenes/courtyard.tscn")
		check(kind+" later valid backup loads atomically on actual return",arrived and FileAccess.get_sha256(Bindings.SAVE_PATH)==restored_hash and Bindings.label("pulse")=="J" and is_equal_approx(current_scene.volume,.2) and current_scene.invert_y and is_equal_approx(current_scene.sensitivity,1.4))
		if not arrived:
			await finish()
			return
		current_scene._open_hero()
		await frames()
		check(kind+" returned guide reloads validated effect pair and remap label",current_scene.hero_panel.reduced_effects_button.button_pressed and not current_scene.hero_panel.reduced_motion_button.button_pressed and current_scene.hero_panel.ability_buttons.piercing_dawn.text.begins_with("J"))
		current_scene.hero_panel.close()
	await finish()

func finish() -> void:
	var stable := true
	for path in sources: stable = stable and sources[path]==FileAccess.get_sha256(path)
	check("I2 preferences sequence sources stable",stable)
	var result := {"passed":checks.all(func(row):return row.passed),"checks":checks,"sources":sources,"sequences":sequence_receipts,"scope":"New I2 sequence stress with explicitly staged typed-conflict, unsupported and oversized save bytes while real title/training/world modals and actual scene routes change. Native GUI event dispatch plus actual focus-loss callbacks; no OS-input/render/audio-quality claim. Valid-backup replacements are declared fixture mutations, not product auto-repair."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false
	if is_instance_valid(current_scene): current_scene.queue_free()
	current_scene=null
	await frames(8)
	OS.delay_msec(100)
	await process_frame
	quit(0 if result.passed else 1)
