extends SceneTree
const Controls = preload("res://scripts/controls_overlay.gd")
const Guide = preload("res://scripts/rama_hero_panel.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var observations: Array[Dictionary] = []
func _initialize() -> void: call_deferred("run")
func frames() -> void:
	for unused in 10: await process_frame
func snap(id: String, control: Control, scroll: ScrollContainer) -> void:
	observations.append({"id":id,"focus_retained":root.gui_get_focus_owner()==control,"inside_scroll":scroll.get_global_rect().encloses(control.get_global_rect()),"viewport":str(root.get_visible_rect()),"card":str(control.get_global_rect()),"clip":str(scroll.get_global_rect()),"scroll_y":scroll.scroll_vertical})
func run() -> void:
	Bindings.install("user://resize-audit.cfg")
	root.size = Vector2i(960,540)
	root.content_scale_size = Vector2i(1280,720)
	root.content_scale_mode = Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
	root.content_scale_factor = 1.0
	var host := Control.new()
	root.add_child(host)
	var controls := Controls.new()
	host.add_child(controls)
	controls.open()
	await frames()
	controls.begin_capture("guardian_circle")
	await frames()
	var scroll: ScrollContainer = controls.card.find_child("MappingsScroll",true,false)
	snap("controls-before",controls.binding_buttons.guardian_circle,scroll)
	root.content_scale_factor = 2.0
	await frames()
	snap("controls-after",controls.binding_buttons.guardian_circle,scroll)
	controls.close()
	root.content_scale_factor = 1.0
	var guide := Guide.new()
	host.add_child(guide)
	guide.open()
	await frames()
	guide.ability_buttons.dawn_volley.grab_focus()
	await frames()
	snap("guide-before",guide.ability_buttons.dawn_volley,guide.abilities_scroll)
	root.content_scale_factor = 2.0
	await frames()
	snap("guide-after",guide.ability_buttons.dawn_volley,guide.abilities_scroll)
	guide.close()
	host.queue_free()
	await frames()
	var report := {"scope":"Read-only source audit; live canvas scale with real engine focus/capture. No raster.","observations":observations,"sources":{}}
	for path in ["res://scripts/controls_overlay.gd","res://scripts/rama_hero_panel.gd",get_script().resource_path]: report.sources[path]=FileAccess.get_sha256(path)
	FileAccess.open("user://report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  ")+"\n")
	print(JSON.stringify(report))
	quit()
