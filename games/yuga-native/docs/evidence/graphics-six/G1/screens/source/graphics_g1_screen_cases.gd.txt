extends SceneTree
## Actual world controls and current kit/vitals; no renderer or OS-input claim.
const UI = preload("res://scripts/hero_ui_theme.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
var checks: Array[Dictionary] = []
var output := ""

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output = argument.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":detail})
	print("PASS " if passed else "FAIL ",label)

func frames() -> void:
	for unused in range(6): await process_frame

func contrast(a: Color, b: Color) -> float:
	var x := a.srgb_to_linear(); var y := b.srgb_to_linear()
	var left := .2126*x.r+.7152*x.g+.0722*x.b
	var right := .2126*y.r+.7152*y.g+.0722*y.b
	return (maxf(left,right)+.05)/(minf(left,right)+.05)

func slot_failures(hud: Control) -> Array:
	var failures := []
	for label in hud.slots:
		var card: PanelContainer = label.get_parent()
		if not hud.get_global_rect().encloses(card.get_global_rect()): failures.append("card outside HUD")
		if not card.get_global_rect().encloses(label.get_global_rect()): failures.append("label outside card")
		for line in label.text.split("\n"):
			var width: float = label.get_theme_font("font").get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,label.get_theme_font_size("font_size")).x
			if width > label.size.x+.5: failures.append(line)
		var panel: StyleBoxFlat = card.get_theme_stylebox("panel")
		if contrast(label.get_theme_color("font_color"),panel.bg_color)<4.5: failures.append("text contrast")
	return failures

func run() -> void:
	var world: Node3D = load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(world); current_scene = world
	await frames(); world.set_paused(false)
	for unused in range(6): await physics_frame
	world.set_process(false); world.set_physics_process(false)
	world.player.set_physics_process(false); world.army.set_physics_process(false)
	world.rama_hud.set_process(false); world.rama_runtime.set_volume(0)
	var hud: Control = world.rama_hud
	for dimensions in [Vector2i(960,540),Vector2i(1280,720),Vector2i(1366,768)]:
		root.content_scale_size = dimensions; root.size = dimensions
		world._layout_world_hud(); hud._refresh(); await frames()
		check("critical stock and health nominal text remains at least 12px at 0.75 capture scale "+str(dimensions),hud.slots.all(func(label):return label.get_theme_font_size("font_size")*.75>=12) and hud.life_text.get_theme_font_size("font_size")*.75>=12)
		var failures := slot_failures(hud)
		check("larger live names and stock fit without clipping "+str(dimensions),failures.is_empty() and root.get_visible_rect().encloses(hud.get_global_rect()),{"failures":failures,"hud":str(hud.get_global_rect())})
		check("compact objective and controls remain separate "+str(dimensions),not world.hud.get_node("RelayStatus").get_global_rect().intersects(world.hud.get_node("ControlsCard").get_global_rect()) and world.objective_label.is_visible_in_tree())
		check("optional population and phase reappear after widening "+str(dimensions),world.lane_label.visible==(dimensions.x>=1100) and world.status_label.visible==(dimensions.x>=1100))
	var saved: Dictionary = Bindings.bindings.duplicate()
	Bindings.bindings.pulse=KEY_SPACE; Bindings.bindings.jump=KEY_Q
	world.player.reload_remaining=.5
	hud._refresh(); await frames()
	check("supported long key label and actual reload caption fit",slot_failures(hud).is_empty() and hud.slots[0].text.contains("RELOADING") and hud.slots[1].text.begins_with("Space"),{"failures":slot_failures(hud),"first":hud.slots[0].text,"second":hud.slots[1].text,"slot_width":hud.slots[0].size.x})
	world.player.reload_remaining=0; Bindings.bindings=saved
	var cast: Dictionary = world.rama_runtime.kit.request_ability("piercing_dawn",world.player.position,Vector3.FORWARD,world.player.position+Vector3.FORWARD*8)
	world.army.step_simulation(.05); hud._refresh(); await frames()
	check("actual cooldown stays textual and readable",cast.accepted and hud.slots[1].text.contains("s\n") and slot_failures(hud).is_empty())
	var retained: StyleBox = hud.slot_cards[1].get_theme_stylebox("panel")
	var before: Dictionary = world.army.report()
	for unused in range(20): hud._refresh()
	check("unchanged HUD state reuses owned surface without advancing authority",hud.slot_cards[1].get_theme_stylebox("panel")==retained and world.army.report()==before)
	world.set_paused(true); hud._refresh(); await frames()
	check("paused slots suppress readiness and retain readable text",not hud.slots.any(func(label):return label.text.contains("READY")) and slot_failures(hud).is_empty())
	var first := UI.hud_panel_style(&"ready"); var second := UI.hud_panel_style(&"ready")
	first.bg_color=Color.MAGENTA
	check("HUD surfaces are privately owned",second.bg_color!=first.bg_color and second.bg_color.a==1.0)
	check("health accent remains visible on the opaque status surface",contrast(UI.MARSH,UI.DEEP)>=3.0)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":{},"scope":"Headless actual world layout, applied font sizes and contrast, explicit supported-key/reload fixtures, actual kit cooldown and paused HUD. 0.75 is a nominal font-size calculation, not rasterized or visual acceptance. No imports, hardware FPS or OS-input claim."}
	for path in ["res://scripts/hero_ui_theme.gd","res://scripts/launch_shell.gd","res://scripts/rama_hero_hud.gd","res://scripts/world_atlas.gd","res://scripts/confluence_world.gd",get_script().resource_path]: result.sources[path]=FileAccess.get_sha256(path)
	if not output.is_empty(): FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false; world.queue_free(); current_scene=null; await frames()
	OS.delay_msec(80); await process_frame
	quit(0 if result.passed else 1)
