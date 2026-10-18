extends SceneTree
## Shared original glyph identity plus actual HUD/guide state and geometry.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Glyph = preload("res://scripts/rama_ability_glyph.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(6): await process_frame

func contrast(a: Color, b: Color) -> float:
	var x := a.srgb_to_linear(); var y := b.srgb_to_linear()
	var left := .2126*x.r+.7152*x.g+.0722*x.b
	var right := .2126*y.r+.7152*y.g+.0722*y.b
	return (maxf(left,right)+.05)/(minf(left,right)+.05)

func press(code: int) -> void:
	for down in [true,false]:
		var event := InputEventKey.new()
		event.keycode=code; event.physical_keycode=code; event.pressed=down
		root.push_input(event)
		await process_frame

func run() -> void:
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world); current_scene=world
	await frames(); world.set_paused(false)
	for unused in range(5): await physics_frame
	world.set_process(false); world.set_physics_process(false)
	world.player.set_physics_process(false); world.army.set_physics_process(false)
	world.rama_hud.set_process(false); world.rama_runtime.set_volume(0)
	var hud: Control = world.rama_hud
	var guide: Control = world.rama_panel
	var hashes := {}; var shared := true; var raster_valid := true
	for index in hud.IDS.size():
		var id: String = hud.IDS[index]
		var texture: Texture2D = Glyph.texture_for(id)
		var bitmap := texture.get_image()
		var digest := HashingContext.new(); digest.start(HashingContext.HASH_SHA256); digest.update(bitmap.get_data())
		hashes[digest.finish().hex_encode()] = id
		raster_valid = raster_valid and bitmap.get_used_rect().has_area() and bitmap.get_used_rect().size.x < bitmap.get_width() and bitmap.get_used_rect().size.y < bitmap.get_height()
		shared = shared and hud.slot_glyphs[index].texture == texture and guide.ability_buttons[id].icon == texture
	check("Five original emblems are distinct nonempty bounded rasters",hashes.size()==5 and raster_valid,{"glyphs":hashes.values()})
	check("HUD and guide share one cached texture per ability",shared and Glyph._textures.size()==5)
	check("Unknown abilities do not invent a fallback meaning",Glyph.texture_for("not_a_real_ability")==null)
	var contrasts := true
	for state in [&"ready",&"cooling",&"unavailable"]:
		for background in [UI.INK,UI.DEEP]: contrasts=contrasts and contrast(Glyph.color_for(state),background)>=3
	check("Ready cooling and unavailable emblems contrast with both combat surfaces",contrasts)
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size=dimensions; root.content_scale_size=dimensions
		world._layout_world_hud(); hud._refresh(); await frames()
		var failures := []
		for i in hud.IDS.size():
			var label: Label = hud.slots[i]; var glyph: TextureRect = hud.slot_glyphs[i]
			if not label.get_global_rect().encloses(glyph.get_global_rect()): failures.append(str(i)+" glyph outside label")
			var font := label.get_theme_font("font")
			var line := label.text.split("\n")[1]
			var line_width := font.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,UI.TYPE_HUD).x
			var indent_width := font.get_string_size(hud._glyph_indent(label),HORIZONTAL_ALIGNMENT_LEFT,-1,UI.TYPE_HUD).x
			var name_start := label.global_position.x+(label.size.x-line_width)*.5+indent_width
			if glyph.get_global_rect().end.x>name_start: failures.append(str(i)+" glyph overlaps name")
			if glyph.mouse_filter != Control.MOUSE_FILTER_IGNORE or glyph.focus_mode!=Control.FOCUS_NONE: failures.append(str(i)+" interactive decoration")
		check("Inline emblems fit without replacing or overlapping names "+str(dimensions),failures.is_empty(),{"failures":failures})
		world.set_paused(true); guide.open("confluence"); await frames()
		var guide_fit := true
		for id in guide.ability_buttons:
			guide.select_ability(id)
			var button: Button = guide.ability_buttons[id]
			button.grab_focus(); await frames()
			var text_width := button.get_theme_font("font").get_string_size(button.text,HORIZONTAL_ALIGNMENT_LEFT,-1,button.get_theme_font_size("font_size")).x
			var minimum := button.get_theme_stylebox("normal").get_minimum_size().x
			guide_fit = guide_fit and text_width+Glyph.GUIDE_SIZE+UI.SPACE_SM+minimum <= button.size.x+.5 and guide.detail_glyph.texture==button.icon and root.gui_get_focus_owner()==button
		check("Guide keys names and matching selected emblem fit with native focus "+str(dimensions),guide_fit)
		guide.close(); world.set_paused(false)
	world.player.reload_remaining=.4; hud._refresh()
	check("Real reload is a cooling emblem with explicit RELOADING text",hud.slot_glyphs[0].state==&"cooling" and hud.slots[0].text.contains("RELOADING"))
	world.player.reload_remaining=0
	var cast: Dictionary = world.rama_runtime.kit.request_ability("piercing_dawn",world.player.position,Vector3.FORWARD,world.player.position+Vector3.FORWARD*8)
	world.army.step_simulation(.05); hud._refresh()
	check("Accepted kit cooldown changes emblem and retains the remaining seconds",cast.accepted and hud.slot_glyphs[1].state==&"cooling" and hud.slots[1].text.contains("s\n"))
	world.set_paused(true); hud._refresh()
	check("Paused abilities retain names and use unavailable emblems",hud.slot_glyphs.all(func(glyph):return glyph.state==&"unavailable") and not hud.slots.any(func(label):return label.text.contains("READY")))
	var prior_path: String = Bindings.config_path
	Bindings.config_path="user://graphics-g2-glyph-options.cfg"
	DirAccess.remove_absolute(ProjectSettings.globalize_path(Bindings.config_path))
	guide.configure_effects(world.rama_runtime.effects)
	guide.open("confluence"); await frames()
	var texture_before: Texture2D = guide.detail_glyph.texture
	guide.reduced_effects_button.grab_focus(); await press(KEY_ENTER)
	guide.reduced_motion_button.grab_focus(); await press(KEY_ENTER)
	check("Reduced options preserve static recognition and live receiver semantics",world.rama_runtime.effects.report().reduced_effects and world.rama_runtime.effects.report().reduced_motion and guide.detail_glyph.texture==texture_before and not guide.detail_glyph.is_processing())
	guide.configure_effects(null)
	guide.reduced_motion_button.release_focus()
	guide.ability_buttons.dawn_volley.grab_focus(); await press(KEY_TAB)
	check("Absent receiver stays disabled and decorative icons add no focus stop",guide.reduced_effects_button.disabled and guide.reduced_motion_button.disabled and root.gui_get_focus_owner()==guide.close_button)
	Bindings.config_path=prior_path
	DirAccess.remove_absolute(ProjectSettings.globalize_path("user://graphics-g2-glyph-options.cfg"))
	var result := {"passed":checks.all(func(row):return row.passed),"checks":checks,"sources":{},"scope":"Headless actual world/guide state and viewport-dispatched keys, cached original SVG rasters, contrast and geometry. No OS input or rendered appearance acceptance."}
	for path in ["res://scripts/rama_ability_glyph.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_hero_panel.gd","res://scripts/hero_ui_theme.gd","res://scripts/confluence_world.gd",get_script().resource_path]:result.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false; world.queue_free(); current_scene=null; await frames()
	OS.delay_msec(80); await process_frame
	quit(0 if result.passed else 1)
