extends "res://tests/desktop_s1_hud_cases.gd"
## New live DRAWING/BUSY and RECOVERING/QUEUED text, not the old idle layout.
func inspect_text(phase: String) -> void:
	for dimensions in [Vector2i(960,540),Vector2i(1280,720)]:
		root.size=dimensions;root.content_scale_size=dimensions
		await frames(5)
		var errors:=[]
		var hud:Control=scene.rama_hud
		var viewport:=root.get_visible_rect()
		for slot in hud.slots:
			if not viewport.encloses(slot.get_global_rect()) or not hud.get_global_rect().encloses(slot.get_parent().get_global_rect()):errors.append("outside: "+slot.text)
			var font:Font=slot.get_theme_font("font")
			var size:int=slot.get_theme_font_size("font_size")
			for line in slot.text.split("\n"):
				if font.get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,size).x>slot.size.x+.5:errors.append("clipped: "+line)
		var note:Label=hud.note
		if note.get_theme_font("font").get_string_size(note.text,HORIZONTAL_ALIGNMENT_LEFT,-1,note.get_theme_font_size("font_size")).x>note.size.x+.5:errors.append("notice clipped: "+note.text)
		check(phase+" text and cards fit "+str(dimensions),errors.is_empty(),{"errors":errors,"notice":note.text,"hud":hud.get_global_rect()})

func run() -> void:
	for path in ["res://scripts/rama_hero_hud.gd","res://scripts/hero_ui_theme.gd",get_script().resource_path]:source_start[path]=FileAccess.get_sha256(path)
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	await frames()
	scene.rama_runtime.set_volume(0)
	await ground_fixture()
	scene.cast_rama_ability("piercing_dawn");hud_frame()
	await inspect_text("drawing/busy")
	var queued:=queue_volley();hud_frame()
	check("layout fixture uses an actual queued intent",queued.get("queued",false))
	await inspect_text("recovering/queued")
	var stable:=true
	for path in source_start:stable=stable and FileAccess.get_sha256(path)==source_start[path]
	check("HUD theme and fixture unchanged",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":source_start,"scope":"Headless actual-font live-state width and enclosure checks; no image or perceptual acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;scene.queue_free();await frames(8);OS.delay_msec(80);await process_frame
	quit(0 if result.passed else 1)
