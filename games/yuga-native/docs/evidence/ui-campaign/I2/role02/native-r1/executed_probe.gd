extends SceneTree
## Actual native Control/Theme ownership, isolated from world and renderer cost.
const UI = preload("res://scripts/hero_ui_theme.gd")
const CYCLES := 12
const WARMUPS := 3
const RESETS := 8
var checks: Array = []
var samples: Array = []
var font_ids: Dictionary = {}
var contract: Dictionary = {}

func _initialize() -> void:
	call_deferred("_run")

func check(name: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name": name, "passed": passed, "detail": detail})

func census() -> Dictionary:
	return {"objects": int(Performance.get_monitor(Performance.OBJECT_COUNT)),
		"resources": int(Performance.get_monitor(Performance.OBJECT_RESOURCE_COUNT)),
		"nodes": int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT)),
		"orphan_nodes": int(Performance.get_monitor(Performance.OBJECT_ORPHAN_NODE_COUNT)),
		"allocator_live_bytes": OS.get_static_memory_usage()}

func bytes_sha(data: PackedByteArray) -> String:
	var context := HashingContext.new()
	context.start(HashingContext.HASH_SHA256)
	context.update(data)
	return context.finish().hex_encode()

func fonts_match() -> bool:
	var sans: FontFile = UI.text_font()
	var serif: FontFile = UI.display_font()
	return sans.get_instance_id() == font_ids.sans and serif.get_instance_id() == font_ids.serif \
		and sans.fallbacks.size() == 1 and serif.fallbacks.size() == 1 \
		and sans.fallbacks[0].get_instance_id() == font_ids.fallback \
		and serif.fallbacks[0].get_instance_id() == font_ids.fallback \
		and not sans.allow_system_fallback and not serif.allow_system_fallback \
		and not sans.fallbacks[0].allow_system_fallback

func watch(refs: Dictionary, object: Object, kind: String) -> void:
	var key := str(object.get_instance_id())
	if not refs.has(key): refs[key] = {"weak": weakref(object), "kind": kind}

func watch_theme(refs: Dictionary, theme: Theme) -> void:
	watch(refs, theme, "Theme")
	for type in theme.get_type_list():
		for name in theme.get_stylebox_list(type): watch(refs, theme.get_stylebox(name, type), "StyleBox")
		for name in theme.get_icon_list(type): watch(refs, theme.get_icon(name, type), "Texture2D")

func watch_tree(refs: Dictionary, node: Node) -> void:
	watch(refs, node, node.get_class())
	for child in node.get_children(): watch_tree(refs, child)

func fixture(styled: bool) -> Dictionary:
	var panel := PanelContainer.new()
	panel.size = Vector2(640, 480)
	var theme: Theme = UI.create() if styled else Theme.new()
	var peer_theme: Theme = UI.build() if styled else Theme.new()
	panel.theme = theme
	var column := VBoxContainer.new()
	panel.add_child(column)
	var first := Button.new()
	first.text = "First"
	column.add_child(first)
	var peer := Button.new()
	peer.text = "Peer"
	peer.theme = peer_theme
	column.add_child(peer)
	var text := Label.new()
	text.text = "YUGA resource ownership"
	column.add_child(text)
	var title := Label.new()
	title.text = "Rama"
	title.theme_type_variation = &"YugaTitle"
	column.add_child(title)
	var choice := OptionButton.new()
	choice.add_item("One")
	choice.add_item("Two")
	column.add_child(choice)
	column.add_child(CheckButton.new())
	column.add_child(CheckBox.new())
	column.add_child(HSlider.new())
	column.add_child(VSlider.new())
	var scroll := ScrollContainer.new()
	scroll.add_child(VBoxContainer.new())
	column.add_child(scroll)
	first.material = CanvasItemMaterial.new()
	peer.material = CanvasItemMaterial.new()
	root.add_child(panel)
	return {"root": panel, "theme": theme, "peer_theme": peer_theme,
		"first": first, "peer": peer, "text": text, "title": title}

func exercise(f: Dictionary, styled: bool, refs: Dictionary, label: String) -> Dictionary:
	var first: Button = f.first
	var peer: Button = f.peer
	var first_material_id: int = first.material.get_instance_id()
	var peer_material_id: int = peer.material.get_instance_id()
	first.material.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	peer.material.blend_mode = CanvasItemMaterial.BLEND_MODE_MIX
	watch_tree(refs, f.root)
	watch_theme(refs, f.theme)
	watch_theme(refs, f.peer_theme)
	watch(refs, first.material, "CanvasItemMaterial")
	watch(refs, peer.material, "CanvasItemMaterial")
	var retired: Array = []
	var reset_start := Time.get_ticks_usec()
	if styled:
		UI.button_variant(first, &"primary")
		UI.button_variant(peer, &"primary")
		var a: StyleBoxFlat = first.get_theme_stylebox("normal")
		var b: StyleBoxFlat = peer.get_theme_stylebox("normal")
		var peer_color := b.bg_color
		var theme_color: Color = f.theme.get_stylebox("normal", "Button").bg_color
		a.bg_color = Color.MAGENTA
		check(label + " local style mutation stays owned", a != b and b.bg_color == peer_color
			and f.theme.get_stylebox("normal", "Button").bg_color == theme_color)
		var ta: StyleBoxFlat = f.theme.get_stylebox("normal", "Button")
		var tb: StyleBoxFlat = f.peer_theme.get_stylebox("normal", "Button")
		var before_peer := tb.bg_color
		ta.bg_color = Color.CYAN
		check(label + " independent themes isolate style mutation", ta != tb and tb.bg_color == before_peer)
		ta.bg_color = theme_color
		a = null
		b = null
		ta = null
		tb = null
		for turn in range(RESETS):
			for state in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
				retired.append(weakref(first.get_theme_stylebox(state)))
			UI.button_variant(first, [&"primary", &"secondary", &"utility", &"selected"][turn % 4])
			for state in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
				watch(refs, first.get_theme_stylebox(state), "LocalStyleBox")
		for state in ["normal", "hover", "pressed", "hover_pressed", "disabled", "focus"]:
			watch(refs, peer.get_theme_stylebox(state), "LocalStyleBox")
		var live_retired := 0
		for item in retired:
			if item.get_ref() != null: live_retired += 1
		check(label + " replaced local styles release", live_retired == 0, {"retired": retired.size(), "remaining": live_retired})
		check(label + " native controls resolve shared exact fonts", f.text.get_theme_font("font").get_instance_id() == font_ids.sans
			and f.title.get_theme_font("font").get_instance_id() == font_ids.serif
			and f.theme.default_font.get_instance_id() == font_ids.sans
			and f.peer_theme.default_font.get_instance_id() == font_ids.sans and fonts_match())
	else:
		# Same native controls, materials and property resets; empty Theme instances.
		for turn in range(RESETS):
			first.theme_type_variation = [&"Button", &"YugaPrimaryButton", &"YugaUtilityButton", &"YugaSelectedButton"][turn % 4]
	var reset_usec := Time.get_ticks_usec() - reset_start
	check(label + " theme operations preserve peer material ownership", first.material.get_instance_id() == first_material_id
		and peer.material.get_instance_id() == peer_material_id and first_material_id != peer_material_id
		and first.material.blend_mode == CanvasItemMaterial.BLEND_MODE_ADD
		and peer.material.blend_mode == CanvasItemMaterial.BLEND_MODE_MIX)
	retired.clear()
	return {"exercise_including_assertions_usec": reset_usec, "reset_count": RESETS}

func cycle(styled: bool, index: int, warmup: bool) -> Dictionary:
	var label := ("theme" if styled else "empty") + " " + str(index) + (" warmup" if warmup else "")
	var before := census()
	var start := Time.get_ticks_usec()
	var f := fixture(styled)
	var create_usec := Time.get_ticks_usec() - start
	var refs: Dictionary = {}
	var reset := exercise(f, styled, refs, label)
	await process_frame
	await process_frame
	var live := census()
	var owned_by_kind: Dictionary = {}
	for item in refs.values(): owned_by_kind[item.kind] = int(owned_by_kind.get(item.kind, 0)) + 1
	var live_watch_count := refs.size()
	start = Time.get_ticks_usec()
	f.root.queue_free()
	f.clear()
	await process_frame
	await process_frame
	var dispose_usec := Time.get_ticks_usec() - start
	var survivors: Array = []
	for key in refs:
		if refs[key].weak.get_ref() != null: survivors.append({"id": key, "kind": refs[key].kind})
	check(label + " owned controls and resources release", survivors.is_empty(), {"watched": refs.size(), "survivors": survivors})
	refs.clear()
	await process_frame
	var after := census()
	check(label + " node and orphan census returns", after.nodes == before.nodes and after.orphan_nodes == before.orphan_nodes,
		{"before": before, "after": after})
	check(label + " fonts remain shared after teardown", fonts_match())
	return {"kind": "theme" if styled else "empty", "index": index, "warmup": warmup,
		"before": before, "live": live, "after": after,
		"create_usec": create_usec, "dispose_including_two_frame_wait_usec": dispose_usec,
		"reset": reset, "watched_by_kind": owned_by_kind, "live_weakref_observer_objects": live_watch_count,
		"survivors": survivors}

func _run() -> void:
	contract = JSON.parse_string(FileAccess.get_file_as_string("res://contract.json"))
	var sans: FontFile = UI.text_font()
	var serif: FontFile = UI.display_font()
	var fallback: FontFile = sans.fallbacks[0]
	font_ids = {"sans": sans.get_instance_id(), "serif": serif.get_instance_id(), "fallback": fallback.get_instance_id()}
	for pair in [["NotoSans-Regular.ttf", sans], ["NotoSerif-Regular.ttf", serif], ["DejaVuSans.ttf", fallback]]:
		check("FontFile.data binds raw " + pair[0], bytes_sha(pair[1].data) == contract.raw_font_sha256[pair[0]],
			{"data_sha256": bytes_sha(pair[1].data), "expected": contract.raw_font_sha256[pair[0]], "resource_path": pair[1].resource_path})
	check("primary fonts share one authored fallback", fonts_match())
	for index in range(WARMUPS):
		await cycle(false, index, true)
		await cycle(true, index, true)
	# Alternate order to expose order-dependent caches; both variants share controls.
	for index in range(CYCLES):
		for styled in ([false, true] if index % 2 == 0 else [true, false]):
			samples.append(await cycle(styled, index, false))
	var all_passed := true
	for item in checks: all_passed = all_passed and item.passed
	var report := {"task": "I2-02-native-UI-resource-ownership", "passed": all_passed,
		"engine": Engine.get_version_info(), "display_server": DisplayServer.get_name(), "contract": contract,
		"warmup_pairs": WARMUPS, "measured_pairs": CYCLES, "font_instance_ids": font_ids,
		"checks": checks, "samples": samples,
		"scope": "Actual 2D Control/Theme/StyleBox/Texture2D/CanvasItemMaterial objects. No scene import, GLB, GPU frame, full world, portable package, FPS or memory-budget claim. Allocator/census/timing observations are reported without an invented threshold; weak references and exact identity establish bounded ownership."}
	var output := OS.get_environment("I2_OWNERSHIP_OUTPUT")
	var file := FileAccess.open(output, FileAccess.WRITE)
	file.store_string(JSON.stringify(report, "\t") + "\n")
	file.close()
	print(JSON.stringify({"passed": all_passed, "checks": checks.size(), "measured_pairs": CYCLES, "output": output}))
	quit(0 if all_passed else 1)
