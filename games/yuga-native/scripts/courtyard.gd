extends Node3D
## Original native training foundation. No commercial game assets or rules claimed.

const PlayerScript = preload("res://scripts/player.gd")
const TargetScript = preload("res://scripts/target.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const CoastalWater = preload("res://shaders/production_water.gdshader")
const ProductionLighting = preload("res://scripts/production_lighting.gd")
const ENVIRONMENT_PATH := "res://assets/environment/lanka_courtyard.glb"
const SAVE_PATH := "user://courtyard-settings.cfg"
const INK := Color("10282e")
const GOLD := Color("e7c078")
const CREAM := Color("f1e6ce")
const MIST := Color("a4c6c3")

var world: Node3D
var player: CharacterBody3D
var targets: Array[Node3D] = []
var projectiles: Node3D
var effects: Node3D
var sun: DirectionalLight3D
var world_environment: WorldEnvironment
var ui: CanvasLayer
var hud: Control
var main_panel: Control
var pause_panel: Control
var settings_panel: Control
var objective_label: Label
var ammo_label: Label
var cooldown_label: Label
var status_label: Label
var stats_label: Label
var feedback_label: Label
var crosshair: Label
var start_button: Button
var resume_button: Button
var settings_back: Button
var settings_from_menu := true
var hit_count := 0
var defeat_count := 0
var elapsed := 0.0
var environment_ready := false
var collidable_meshes := 0
var started := false
var smoke_mode := false
var footstep_clock := 0.0
var feedback_clock := 0.0
var sensitivity := 1.0
var volume := 0.7
var invert_y := false
var full_screen := false
var shadows := true
var night := false
var sounds: Dictionary = {}
var audio_players: Array[AudioStreamPlayer] = []
var sound_cursor := 0
var overlay_reason := "TRAINING PAUSED"

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	smoke_mode = "--smoke" in OS.get_cmdline_user_args()
	_install_actions()
	_load_settings()
	_create_world()
	_create_audio()
	_create_ui()
	_apply_settings()
	get_window().focus_exited.connect(_on_focus_lost)
	print("YUGA_NATIVE_READY ", JSON.stringify({"hero": player.model_ready, "environment": environment_ready, "targets": targets.size(), "collision_meshes": collidable_meshes, "renderer": RenderingServer.get_current_rendering_method()}))
	if "--autostart" in OS.get_cmdline_user_args() or smoke_mode:
		start_training()

func _install_actions() -> void:
	var key_actions := {
		"move_forward": [KEY_W, KEY_UP], "move_back": [KEY_S, KEY_DOWN],
		"move_left": [KEY_A, KEY_LEFT], "move_right": [KEY_D, KEY_RIGHT],
		"jump": [KEY_SPACE], "sprint": [KEY_SHIFT], "reload": [KEY_R],
		"pulse": [KEY_Q], "dash": [KEY_E], "pause_game": [KEY_ESCAPE], "reset_training": [KEY_F5]
	}
	for action in key_actions:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for key in key_actions[action]:
			var event := InputEventKey.new()
			event.physical_keycode = key
			InputMap.action_add_event(action, event)
	if not InputMap.has_action("fire"):
		InputMap.add_action("fire")
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	InputMap.action_add_event("fire", click)

func _create_world() -> void:
	world = Node3D.new()
	world.name = "World"
	world.process_mode = Node.PROCESS_MODE_PAUSABLE
	add_child(world)
	world_environment = WorldEnvironment.new()
	world_environment.name = "CourtyardAtmosphere"
	var environment := Environment.new()
	environment.background_mode = Environment.BG_SKY
	var sky := Sky.new()
	var sky_material := ProceduralSkyMaterial.new()
	sky_material.sky_top_color = Color("37596d")
	sky_material.sky_horizon_color = Color("ddab7c")
	sky_material.ground_bottom_color = Color("102d3d")
	sky_material.ground_horizon_color = Color("ddab7c")
	sky_material.sun_angle_max = 16
	sky.sky_material = sky_material
	environment.sky = sky
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = Color("9bc9d5")
	environment.ambient_light_energy = 0.72
	environment.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	environment.tonemap_exposure = 1.1
	environment.fog_enabled = true
	environment.fog_light_color = Color("8da5a4")
	environment.fog_density = 0.002
	if RenderingServer.get_current_rendering_method() != "gl_compatibility":
		environment.glow_enabled = true
		environment.glow_intensity = 0.65
		environment.ssao_enabled = true
		environment.ssao_radius = 1.4
	world_environment.environment = environment
	world.add_child(world_environment)
	sun = DirectionalLight3D.new()
	sun.name = "SettingSun"
	sun.rotation_degrees = Vector3(-31, -28, 0)
	sun.light_color = Color("ffdcac")
	sun.light_energy = 1.4
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 65
	world.add_child(sun)
	var fill := DirectionalLight3D.new()
	fill.name = "CoolSkyFill"
	fill.rotation_degrees = Vector3(-48, 140, 0)
	fill.light_color = Color("6ca9c0")
	fill.light_energy = 0.45
	fill.shadow_enabled = false
	world.add_child(fill)
	if ResourceLoader.exists(ENVIRONMENT_PATH):
		var environment_model: Node3D = load(ENVIRONMENT_PATH).instantiate()
		environment_model.name = "AuthoredLankaCourtyard"
		world.add_child(environment_model)
		_make_static_geometry(environment_model, false)
		environment_ready = true
	else:
		push_warning("Courtyard art missing; visible fallback floor is development-only.")
		var ground := MeshInstance3D.new()
		var ground_mesh := BoxMesh.new()
		ground_mesh.size = Vector3(44, 0.2, 50)
		ground.mesh = ground_mesh
		ground.position.y = -0.1
		var floor_material := StandardMaterial3D.new()
		floor_material.albedo_color = Color("78877e")
		floor_material.roughness = 0.85
		ground.material_override = floor_material
		world.add_child(ground)
	_add_collision_box("CourtyardFloor", Vector3(0, -0.25, 0), Vector3(44, 0.5, 50))
	_add_collision_box("WestBoundary", Vector3(-22.25, 2, 0), Vector3(0.5, 4, 50))
	_add_collision_box("EastBoundary", Vector3(22.25, 2, 0), Vector3(0.5, 4, 50))
	_add_collision_box("NorthBoundary", Vector3(0, 2, -25.25), Vector3(45, 4, 0.5))
	_add_collision_box("SouthBoundary", Vector3(0, 2, 25.25), Vector3(45, 4, 0.5))
	for x in [-14.7, 14.7]:
		for z in [0.0, 12.0]:
			var lamp := OmniLight3D.new()
			lamp.position = Vector3(x, 1.8, z)
			lamp.light_color = Color("ff9b49")
			lamp.light_energy = 2.2
			lamp.omni_range = 7.0
			lamp.omni_attenuation = 1.4
			lamp.shadow_enabled = false
			world.add_child(lamp)
	projectiles = Node3D.new()
	projectiles.name = "Projectiles"
	world.add_child(projectiles)
	effects = Node3D.new()
	effects.name = "TransientEffects"
	world.add_child(effects)
	for i in range(5):
		var target := StaticBody3D.new()
		target.set_script(TargetScript)
		target.name = "Target%02d" % (i + 1)
		target.number = i + 1
		target.position = Vector3(-8 + i * 4, 0, -8)
		world.add_child(target)
		target.struck.connect(_on_target_struck)
		targets.append(target)
	player = CharacterBody3D.new()
	player.set_script(PlayerScript)
	player.name = "Rama"
	player.position = Vector3(0, 0.05, 12)
	world.add_child(player)
	player.fired.connect(_on_fired)
	player.pulse.connect(_on_pulse)
	player.changed.connect(_refresh_hud)

func _make_static_geometry(node: Node, inherited_collision: bool) -> void:
	var should_collide := inherited_collision or String(node.name).begins_with("COL_")
	if node is MeshInstance3D and String(node.name).begins_with("WATER_"):
		var water_material := ShaderMaterial.new()
		water_material.shader = CoastalWater
		node.material_override = water_material
	if node is MeshInstance3D and should_collide:
		node.create_trimesh_collision()
		collidable_meshes += 1
	# Work from a snapshot because collision generation adds descendants.
	for child in node.get_children():
		if child is Node3D and not child is StaticBody3D:
			_make_static_geometry(child, should_collide)

func _add_collision_box(label: String, location: Vector3, size: Vector3) -> void:
	var body := StaticBody3D.new()
	body.name = label
	body.position = location
	body.collision_layer = 1
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = size
	shape.shape = box
	body.add_child(shape)
	world.add_child(body)

func _create_ui() -> void:
	ui = CanvasLayer.new()
	ui.name = "NativeInterface"
	ui.process_mode = Node.PROCESS_MODE_ALWAYS
	add_child(ui)
	var root := Control.new()
	root.name = "InterfaceRoot"
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.theme = _theme()
	ui.add_child(root)
	hud = Control.new()
	hud.name = "TrainingHUD"
	hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(hud)
	var top := HBoxContainer.new()
	top.set_anchors_and_offsets_preset(Control.PRESET_TOP_WIDE)
	top.offset_left = 28
	top.offset_right = -28
	top.offset_top = 22
	top.add_theme_constant_override("separation", 18)
	hud.add_child(top)
	var title_card := _card()
	title_card.custom_minimum_size.x = 430
	top.add_child(title_card)
	var title_column := VBoxContainer.new()
	title_card.add_child(title_column)
	title_column.add_child(_label("Y U G A   /   LANKA COURTYARD", 16, GOLD))
	objective_label = _label("MASTER THE BOW", 28, CREAM)
	title_column.add_child(objective_label)
	stats_label = _label("0 hits  ·  0 targets cleared", 16, MIST)
	title_column.add_child(stats_label)
	var title_spacer := Control.new()
	title_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	title_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	top.add_child(title_spacer)
	var pause_button := _button("ESC  PAUSE", func(): set_paused(true))
	pause_button.custom_minimum_size = Vector2(150, 44)
	pause_button.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	top.add_child(pause_button)
	var bottom := HBoxContainer.new()
	bottom.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	bottom.offset_left = 28
	bottom.offset_right = -28
	bottom.offset_top = -100
	bottom.offset_bottom = -22
	bottom.add_theme_constant_override("separation", 24)
	hud.add_child(bottom)
	var ammo_card := _card()
	ammo_card.custom_minimum_size.x = 200
	bottom.add_child(ammo_card)
	var ammo_stack := VBoxContainer.new()
	ammo_card.add_child(ammo_stack)
	ammo_stack.add_child(_label("SOLAR BOW", 12, GOLD))
	ammo_label = _label("12 / 12", 28, CREAM)
	ammo_stack.add_child(ammo_label)
	var help_card := _card()
	help_card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	bottom.add_child(help_card)
	var help := VBoxContainer.new()
	help.alignment = BoxContainer.ALIGNMENT_CENTER
	help_card.add_child(help)
	cooldown_label = _label("Q  SUNBURST · READY     E  DASH · READY", 16, CREAM)
	help.add_child(cooldown_label)
	status_label = _label("WASD move   ·   Mouse aim / fire   ·   Space jump   ·   Shift sprint   ·   R reload", 14, MIST)
	help.add_child(status_label)
	crosshair = _label("·", 36, CREAM)
	crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	crosshair.offset_left = -14
	crosshair.offset_top = -25
	crosshair.offset_right = 14
	crosshair.offset_bottom = 25
	crosshair.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hud.add_child(crosshair)
	feedback_label = _label("", 18, GOLD)
	feedback_label.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	feedback_label.offset_left = -220
	feedback_label.offset_right = 220
	feedback_label.offset_top = 44
	feedback_label.offset_bottom = 80
	feedback_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	feedback_label.add_theme_constant_override("outline_size", 4)
	feedback_label.add_theme_color_override("font_outline_color", INK)
	hud.add_child(feedback_label)
	main_panel = _modal(root, "MainMenu", false)
	var intro := _modal_content(main_panel)
	intro.add_child(_label("AN ORIGINAL NATIVE FOUNDATION", 13, GOLD))
	intro.add_child(_label("Y U G A", 58, CREAM))
	intro.add_child(_label("LANKA COURTYARD", 25, CREAM))
	intro.add_child(_wrapped("A coastal citadel at the edge of dusk. Take up Rama’s solar bow and find your rhythm.", 18, MIST))
	intro.add_child(_divider())
	intro.add_child(_wrapped("Train movement, aim and abilities in a single-player courtyard. Five targets return after each clear.", 16, CREAM))
	start_button = _button("ENTER COURTYARD   →", start_training)
	intro.add_child(start_button)
	intro.add_child(_button("SETTINGS", func(): _open_settings(true)))
	intro.add_child(_button("QUIT TO DESKTOP", _quit))
	intro.add_child(_wrapped("NATIVE PROTOTYPE  ·  Local training only\nWASD + mouse  ·  Esc releases the cursor", 13, MIST))
	pause_panel = _modal(root, "PauseMenu", true)
	var pause_content := _modal_content(pause_panel)
	pause_content.add_child(_label("TAKE A BREATH", 13, GOLD))
	pause_content.add_child(_label("Training paused", 34, CREAM))
	pause_content.add_child(_wrapped("Your movement and all cooldowns are frozen.", 17, MIST))
	resume_button = _button("RESUME TRAINING", func(): set_paused(false))
	pause_content.add_child(resume_button)
	pause_content.add_child(_button("SETTINGS", func(): _open_settings(false)))
	pause_content.add_child(_button("RESET COURTYARD", func(): reset_training(); set_paused(false)))
	pause_content.add_child(_button("RETURN TO TITLE", return_to_menu))
	pause_content.add_child(_button("QUIT TO DESKTOP", _quit))
	settings_panel = _modal(root, "Settings", true)
	var settings := _modal_content(settings_panel)
	settings.add_child(_label("MAKE IT YOURS", 13, GOLD))
	settings.add_child(_label("Settings", 34, CREAM))
	settings.add_child(_label("Mouse sensitivity", 16, CREAM))
	var mouse_slider := HSlider.new()
	mouse_slider.name = "Sensitivity"
	mouse_slider.min_value = 0.35
	mouse_slider.max_value = 2.5
	mouse_slider.step = 0.05
	mouse_slider.value = sensitivity
	mouse_slider.custom_minimum_size.y = 32
	mouse_slider.value_changed.connect(func(value: float): sensitivity = value; _apply_settings(); _save_settings())
	settings.add_child(mouse_slider)
	settings.add_child(_label("Sound volume", 16, CREAM))
	var volume_slider := HSlider.new()
	volume_slider.name = "Volume"
	volume_slider.min_value = 0
	volume_slider.max_value = 1
	volume_slider.step = 0.05
	volume_slider.value = volume
	volume_slider.custom_minimum_size.y = 32
	volume_slider.value_changed.connect(func(value: float): volume = value; _apply_settings(); _save_settings())
	settings.add_child(volume_slider)
	settings.add_child(_check("Invert vertical aim", invert_y, func(value: bool): invert_y = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Fullscreen", full_screen, func(value: bool): full_screen = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Dynamic sun shadows", shadows, func(value: bool): shadows = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Moonlit courtyard", night, func(value: bool): night = value; _apply_settings(); _save_settings()))
	settings_back = _button("BACK", _close_settings)
	settings.add_child(settings_back)
	settings.add_child(_wrapped("Settings save locally on this computer.\nQ sunburst · E dash · F5 reset courtyard", 13, MIST))
	hud.visible = false
	pause_panel.visible = false
	settings_panel.visible = false
	start_button.grab_focus()

func _theme() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 18
	theme.set_color("font_color", "Button", CREAM)
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_color("font_focus_color", "Button", Color.WHITE)
	for state in ["normal", "hover", "pressed", "focus"]:
		var style := StyleBoxFlat.new()
		style.bg_color = Color("183b40") if state == "normal" else Color("28545a")
		if state == "pressed": style.bg_color = Color("36686b")
		style.border_color = GOLD if state == "focus" else Color("537873")
		style.set_border_width_all(2 if state == "focus" else 1)
		style.set_corner_radius_all(3)
		style.content_margin_left = 20
		style.content_margin_right = 20
		style.content_margin_top = 12
		style.content_margin_bottom = 12
		theme.set_stylebox(state, "Button", style)
	theme.set_color("font_color", "CheckButton", CREAM)
	return theme

func _label(text: String, font_size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", font_size)
	label.add_theme_color_override("font_color", color)
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return label

func _wrapped(text: String, font_size: int, color: Color) -> Label:
	var label := _label(text, font_size, color)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return label

func _button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size.y = 48
	button.pressed.connect(func(): _sound("menu"); callback.call())
	return button

func _check(text: String, enabled: bool, callback: Callable) -> CheckButton:
	var check := CheckButton.new()
	check.text = text
	check.button_pressed = enabled
	check.custom_minimum_size.y = 38
	check.toggled.connect(callback)
	return check

func _card() -> PanelContainer:
	var card := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.035, 0.10, 0.12, 0.88)
	style.border_color = Color("6b755b")
	style.set_border_width_all(1)
	style.content_margin_left = 20
	style.content_margin_right = 20
	style.content_margin_top = 10
	style.content_margin_bottom = 10
	card.add_theme_stylebox_override("panel", style)
	return card

func _modal(root: Control, label: String, centered: bool) -> Control:
	var veil := Control.new()
	veil.name = label
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(veil)
	var shade := ColorRect.new()
	shade.color = Color(0.015, 0.04, 0.055, 0.72 if centered else 0.34)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	veil.add_child(shade)
	var panel := _card()
	panel.name = "Card"
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER if centered else Control.PRESET_CENTER_LEFT)
	panel.offset_left = -245 if centered else 48
	panel.offset_right = 245 if centered else 538
	panel.offset_top = -310
	panel.offset_bottom = 310
	veil.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.name = "Scroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	panel.add_child(scroll)
	var stack := VBoxContainer.new()
	stack.name = "Content"
	stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stack.add_theme_constant_override("separation", 14)
	scroll.add_child(stack)
	return veil

func _modal_content(modal: Control) -> VBoxContainer:
	return modal.get_node("Card/Scroll/Content")

func _divider() -> HSeparator:
	return HSeparator.new()

func start_training() -> void:
	started = true
	main_panel.visible = false
	settings_panel.visible = false
	pause_panel.visible = false
	hud.visible = true
	get_tree().paused = false
	player.active = true
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_refresh_hud()
	print("YUGA_NATIVE_TRAINING_STARTED")

func set_paused(value: bool) -> void:
	if not started:
		return
	if value:
		_release_gameplay_actions()
		player.velocity.x = 0
		player.velocity.z = 0
		player.dash_time = 0
		player.dash_direction = Vector3.ZERO
	get_tree().paused = value
	pause_panel.visible = value
	settings_panel.visible = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if value else Input.MOUSE_MODE_CAPTURED
	if value:
		resume_button.grab_focus()
	else:
		get_viewport().gui_release_focus()
	print("YUGA_NATIVE_PAUSE ", value)

func reset_training() -> void:
	_release_gameplay_actions()
	player.reset()
	for target in targets:
		target.reset_target()
	for node in projectiles.get_children():
		node.queue_free()
	for node in effects.get_children():
		node.queue_free()
	hit_count = 0
	defeat_count = 0
	elapsed = 0
	feedback_clock = 0
	feedback_label.text = ""
	_refresh_hud()
	print("YUGA_NATIVE_RESET")

func return_to_menu() -> void:
	get_tree().paused = false
	player.active = false
	started = false
	reset_training()
	hud.visible = false
	pause_panel.visible = false
	settings_panel.visible = false
	main_panel.visible = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	start_button.grab_focus()

func _input(event: InputEvent) -> void:
	if event.is_action_pressed("pause_game"):
		if settings_panel.visible:
			_close_settings()
		elif started:
			set_paused(not get_tree().paused)
		get_viewport().set_input_as_handled()
	if event.is_action_pressed("reset_training") and started and not get_tree().paused:
		reset_training()

func _release_gameplay_actions() -> void:
	for action in ["move_forward", "move_back", "move_left", "move_right", "fire", "jump", "sprint", "dash", "pulse", "reload"]:
		Input.action_release(action)

func _on_focus_lost() -> void:
	if started and not smoke_mode:
		set_paused(true)

func _open_settings(from_menu: bool) -> void:
	settings_from_menu = from_menu
	main_panel.visible = false
	pause_panel.visible = false
	settings_panel.visible = true
	if started:
		get_tree().paused = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	settings_panel.get_node("Card/Scroll/Content/Sensitivity").grab_focus()

func _close_settings() -> void:
	settings_panel.visible = false
	if settings_from_menu:
		main_panel.visible = true
		start_button.grab_focus()
	else:
		pause_panel.visible = true
		resume_button.grab_focus()

func _physics_process(delta: float) -> void:
	if not started or get_tree().paused:
		return
	elapsed += delta
	feedback_clock = maxf(0, feedback_clock - delta)
	if feedback_clock == 0:
		feedback_label.text = ""
	footstep_clock -= delta
	if player.current_speed > 0.5 and player.is_on_floor() and footstep_clock <= 0:
		footstep_clock = 0.32 if player.current_speed > 7 else 0.45
		_sound("step", -13)
	_refresh_hud()

func _refresh_hud() -> void:
	if not is_instance_valid(ammo_label):
		return
	ammo_label.text = "RELOAD  %.1f" % player.reload_remaining if player.reload_remaining > 0 else "%02d / %02d" % [player.ammo, player.MAGAZINE]
	var pulse_text := "READY" if player.pulse_remaining <= 0 else "%.1fs" % player.pulse_remaining
	var dash_text := "READY" if player.dash_remaining <= 0 else "%.1fs" % player.dash_remaining
	cooldown_label.text = "Q  SUNBURST · %s     E  DASH · %s" % [pulse_text, dash_text]
	stats_label.text = "%d hits  ·  %d targets cleared  ·  %02d:%02d" % [hit_count, defeat_count, int(elapsed) / 60, int(elapsed) % 60]
	objective_label.text = "MASTER THE BOW" if defeat_count < 5 else "FIND YOUR RHYTHM"

func _on_fired(origin: Vector3, direction: Vector3, _empowered: bool) -> void:
	if projectiles.get_child_count() >= 48:
		return
	var projectile := Node3D.new()
	projectile.set_script(ProjectileScript)
	projectile.position = origin
	projectile.direction = direction
	projectile.ignore.assign([player.get_rid()])
	projectiles.add_child(projectile)
	projectile.impacted.connect(_on_projectile_impact)
	_sound("bow", -4)

func _on_projectile_impact(location: Vector3, _target: Node) -> void:
	_ring_effect(location, Color("ffc864"), 0.65, 0.22)

func _on_target_struck(target: Node3D, defeated: bool) -> void:
	hit_count += 1
	if defeated:
		defeat_count += 1
		feedback_label.text = "TARGET CLEARED  +1"
		feedback_clock = 1.3
		_sound("clear", -1)
	else:
		feedback_label.text = "HIT"
		feedback_clock = 0.25
		_sound("hit", -5)
	_ring_effect(target.global_position + Vector3(0, 1.65, 0), Color("76e2da"), 0.9, 0.35)

func _on_pulse(origin: Vector3) -> void:
	for target in targets:
		if target.global_position.distance_to(origin) <= 8.0:
			target.take_hit(2)
	_ring_effect(Vector3(origin.x, 0.12, origin.z), Color("ffce6b"), 8.0, 0.7, true)
	_sound("pulse", -3)

func _ring_effect(location: Vector3, color: Color, radius: float, duration: float, horizontal: bool = false) -> void:
	if effects.get_child_count() >= 24:
		return
	var ring := MeshInstance3D.new()
	var mesh := TorusMesh.new()
	mesh.inner_radius = 0.84
	mesh.outer_radius = 1.0
	mesh.rings = 24
	mesh.ring_segments = 6
	ring.mesh = mesh
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.albedo_color = color
	material.emission_enabled = true
	material.emission = color
	material.emission_energy_multiplier = 3
	ring.material_override = material
	ring.position = location
	if not horizontal:
		ring.rotation.x = PI / 2
	ring.scale = Vector3.ONE * 0.1
	effects.add_child(ring)
	var tween := ring.create_tween().set_parallel(true)
	tween.tween_property(ring, "scale", Vector3.ONE * radius, duration)
	tween.tween_property(material, "albedo_color:a", 0.0, duration)
	tween.chain().tween_callback(ring.queue_free)

func _create_audio() -> void:
	for i in range(6):
		var audio := AudioStreamPlayer.new()
		audio.process_mode = Node.PROCESS_MODE_ALWAYS
		add_child(audio)
		audio_players.append(audio)
	sounds["bow"] = _tone(290, 0.12, 4.0)
	sounds["hit"] = _tone(740, 0.11, 0.7)
	sounds["clear"] = _tone(1040, 0.28, 0.45)
	sounds["pulse"] = _tone(130, 0.5, 0.6)
	sounds["step"] = _tone(75, 0.055, 7.0)
	sounds["menu"] = _tone(560, 0.065, 0.2)

func _tone(frequency: float, duration: float, sweep: float) -> AudioStreamWAV:
	var rate := 22050
	var count := int(rate * duration)
	var bytes := PackedByteArray()
	bytes.resize(count * 2)
	var phase := 0.0
	for i in range(count):
		var t := float(i) / count
		phase += TAU * frequency * (1.0 + sweep * (1.0 - t)) / rate
		var envelope := minf(1.0, t * 24) * pow(1.0 - t, 2)
		var sample := int(sin(phase) * envelope * 10000)
		bytes.encode_s16(i * 2, sample)
	var stream := AudioStreamWAV.new()
	stream.format = AudioStreamWAV.FORMAT_16_BITS
	stream.mix_rate = rate
	stream.data = bytes
	return stream

func _sound(name: String, gain: float = 0) -> void:
	if not sounds.has(name) or volume <= 0 or audio_players.is_empty():
		return
	var audio: AudioStreamPlayer = audio_players[sound_cursor % audio_players.size()]
	sound_cursor += 1
	audio.stream = sounds[name]
	audio.volume_db = linear_to_db(maxf(0.001, volume)) + gain
	audio.play()

func _load_settings() -> void:
	var config := ConfigFile.new()
	if config.load(SAVE_PATH) != OK:
		return
	sensitivity = clampf(float(config.get_value("controls", "sensitivity", 1.0)), 0.35, 2.5)
	volume = clampf(float(config.get_value("audio", "volume", 0.7)), 0, 1)
	invert_y = bool(config.get_value("controls", "invert_y", false))
	full_screen = bool(config.get_value("video", "fullscreen", false))
	shadows = bool(config.get_value("video", "shadows", true))
	night = bool(config.get_value("video", "night", false))

func _save_settings() -> void:
	var config := ConfigFile.new()
	config.set_value("controls", "sensitivity", sensitivity)
	config.set_value("controls", "invert_y", invert_y)
	config.set_value("audio", "volume", volume)
	config.set_value("video", "fullscreen", full_screen)
	config.set_value("video", "shadows", shadows)
	config.set_value("video", "night", night)
	var result := config.save(SAVE_PATH)
	if result != OK:
		push_warning("Settings could not be saved: " + error_string(result))

func _apply_settings() -> void:
	if is_instance_valid(player):
		player.sensitivity = sensitivity * 0.0024
		player.invert_y = invert_y
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if full_screen else DisplayServer.WINDOW_MODE_WINDOWED)
	if is_instance_valid(sun):
		ProductionLighting.apply(world_environment.environment, sun, world, night, shadows)

func _quit() -> void:
	get_tree().paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	get_tree().quit()
