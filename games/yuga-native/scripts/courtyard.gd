extends Node3D
## Original native training foundation. No commercial game assets or rules claimed.

const Bindings = preload("res://scripts/input_bindings.gd")
const ControlsOverlay = preload("res://scripts/controls_overlay.gd")
const PlayerScript = preload("res://scripts/player.gd")
const TargetScript = preload("res://scripts/target.gd")
const ProjectileScript = preload("res://scripts/projectile.gd")
const CoastalWater = preload("res://shaders/production_water.gdshader")
const ProductionLighting = preload("res://scripts/production_lighting.gd")
const MythicEnvironment = preload("res://scripts/mythic_environment.gd")
const HeroDistrict = preload("res://scripts/hero_district_detail.gd")
const HeroAtmosphere = preload("res://scripts/hero_atmosphere.gd")
const HeroUITheme = preload("res://scripts/hero_ui_theme.gd")
const LaunchShell = preload("res://scripts/launch_shell.gd")
const SceneTransition = preload("res://scripts/scene_transition.gd")
const RamaHeroPanel = preload("res://scripts/rama_hero_panel.gd")
const RamaHeroHUD = preload("res://scripts/rama_hero_hud.gd")
const RamaHeroRuntime = preload("res://scripts/rama_hero_runtime.gd")
const RamaPracticeArmy = preload("res://scripts/rama_practice_army.gd")
const ENVIRONMENT_PATH := "res://assets/environment/lanka_courtyard.glb"
const SAVE_PATH := "user://courtyard-settings.cfg"
const INK := HeroUITheme.INK
const GOLD := HeroUITheme.GOLD
const CREAM := HeroUITheme.CREAM
const MIST := HeroUITheme.MIST

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
var status_label: Label
var stats_label: Label
var feedback_label: Label
var crosshair: Label
var start_button: Button
var resume_button: Button
var settings_back: Button
var controls_button: Button
var controls_overlay: Control
var help_panel: Control
var help_label: Label
var help_return := "menu"
var menu_hint: Label
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
var title_camera: Camera3D
var title_light: OmniLight3D
var hero_panel: Control
var hero_panel_return := "menu"
var hero_button: Button
var settings_return_focus: WeakRef
var help_return_focus: WeakRef
var hero_return_focus: WeakRef
var help_back: Button
var title_wordmark: Label
var interface_root: Control
var last_ui_size := Vector2.ZERO
var sensitivity_value: Label
var volume_value: Label
var settings_notice: Label
var rama_kit: Node
var rama_effects: Node3D
var rama_panel: Control
var rama_runtime: Node
var rama_hud: Control
var practice_army: Node3D
var hero_atmosphere := HeroAtmosphere.new()
var scene_transition: Control
var _transition_return_focus: WeakRef
var _transition_world_process := Node.PROCESS_MODE_PAUSABLE
var _transition_ui_process := Node.PROCESS_MODE_ALWAYS
var _transition_isolating := false

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
	Bindings.install()

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
	MythicEnvironment.configure(world, "courtyard")
	var district: Dictionary = HeroDistrict.configure(world)
	if not district.get("ok", false): push_error("Hero courtyard detail could not be built")
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
	_create_rama_practice()
	_create_title_camera()

func _create_rama_practice() -> void:
	practice_army = RamaPracticeArmy.new()
	practice_army.name = "RamaPracticeTargets"
	world.add_child(practice_army)
	if not practice_army.configure(targets):
		push_error("Courtyard practice targets could not be configured.")
		return
	rama_runtime = RamaHeroRuntime.new()
	rama_runtime.name = "RamaHeroRuntime"
	world.add_child(rama_runtime)
	if not rama_runtime.configure(player, practice_army):
		push_error("Rama’s courtyard ability kit could not be configured.")
		return
	rama_kit = rama_runtime.kit
	rama_effects = rama_runtime.effects
	rama_runtime.changed.connect(_refresh_hud)
	_set_practice_suspended(true)

func _set_practice_suspended(value: bool) -> void:
	if is_instance_valid(practice_army): practice_army.set_suspended(value)
	if is_instance_valid(rama_runtime): rama_runtime.set_suspended(value)

func _create_title_camera() -> void:
	# Show the actual gameplay actor in its environment, including its idle clip.
	title_camera = Camera3D.new()
	title_camera.name = "RamaTitleCamera"
	title_camera.fov = 34
	title_camera.near = .1
	title_camera.far = 100
	world.add_child(title_camera)
	title_camera.global_position = player.global_position + Vector3(3.4, 1.7, -5.2)
	title_camera.look_at(player.global_position + Vector3(1.65, 1.15, .6), Vector3.UP)
	title_camera.make_current()
	title_light = OmniLight3D.new()
	title_light.name = "HeroPortraitFill"
	title_light.position = player.position + Vector3(-1.8, 2.8, -2.0)
	title_light.light_color = Color("b4d4e5")
	title_light.light_energy = 1.8
	title_light.omni_range = 5.5
	title_light.shadow_enabled = false
	world.add_child(title_light)

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
	interface_root = root
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
	title_card.custom_minimum_size.x = 330
	top.add_child(title_card)
	var title_column := VBoxContainer.new()
	title_card.add_child(title_column)
	title_column.add_child(_label("YUGA  /  BOW TRAINING", 13, GOLD))
	objective_label = _label("Master the bow", 23, CREAM)
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
	status_label = _label(Bindings.label("reload") + " reload  ·  F3 abilities  ·  F2 help", 13, MIST)
	title_column.add_child(status_label)
	rama_hud = RamaHeroHUD.new()
	hud.add_child(rama_hud)
	if is_instance_valid(rama_runtime) and rama_runtime.configured: rama_hud.configure(rama_runtime)
	else: rama_hud.hide()
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
	main_panel = LaunchShell.new()
	root.add_child(main_panel)
	main_panel.world_requested.connect(enter_confluence)
	main_panel.train_requested.connect(start_training)
	main_panel.guide_requested.connect(_open_hero)
	main_panel.film_requested.connect(enter_combat_film)
	main_panel.help_requested.connect(_open_help)
	main_panel.settings_requested.connect(func(): _open_settings(true))
	main_panel.quit_requested.connect(_quit)
	for action in main_panel._actions:
		action.pressed.connect(func(): _sound("menu"))
	# Retain public Control aliases used by native automation and scene callers.
	start_button = main_panel.primary_button
	hero_button = main_panel.guide_button
	title_wordmark = main_panel.title_wordmark
	menu_hint = main_panel.menu_hint
	pause_panel = _modal(root, "PauseMenu", true)
	var pause_content := _modal_content(pause_panel)
	pause_content.add_child(_label("LANKA COURTYARD", 13, GOLD))
	pause_content.add_child(_label("Training paused", 34, CREAM))
	pause_content.add_child(_wrapped("Your movement and all cooldowns are frozen.", 17, MIST))
	resume_button = _button("RESUME TRAINING", func(): set_paused(false))
	HeroUITheme.button(resume_button, true)
	pause_content.add_child(resume_button)
	for entry in [{"name":"RamaAbilities", "text":"RAMA’S ABILITIES", "action":_open_hero}, {"name":"Help", "text":"CONTROLS & HELP", "action":_open_help}, {"name":"Settings", "text":"SETTINGS", "action":func(): _open_settings(false)}]:
		var action := _button(entry.text, entry.action)
		action.name = entry.name
		pause_content.add_child(action)
	pause_content.add_child(_button("RESET COURTYARD", func(): reset_training(); set_paused(false)))
	pause_content.add_child(_button("RETURN TO TITLE", return_to_menu))
	pause_content.add_child(_button("QUIT TO DESKTOP", _quit))
	settings_panel = _modal(root, "Settings", true)
	var settings := _modal_content(settings_panel)
	settings.add_child(_label("YOUR PREFERENCES", 13, GOLD))
	settings.add_child(_label("Settings", 34, CREAM))
	settings_notice = _wrapped("Changes save on this computer.", 13, MIST)
	settings.add_child(settings_notice)
	sensitivity_value = _label("Mouse sensitivity  ·  %.2f×" % sensitivity, 16, CREAM)
	settings.add_child(sensitivity_value)
	var mouse_slider := HSlider.new()
	mouse_slider.name = "Sensitivity"
	mouse_slider.min_value = 0.35
	mouse_slider.max_value = 2.5
	mouse_slider.step = 0.05
	mouse_slider.value = sensitivity
	mouse_slider.custom_minimum_size.y = 32
	mouse_slider.value_changed.connect(func(value: float): sensitivity = value; sensitivity_value.text = "Mouse sensitivity  ·  %.2f×" % value; _apply_settings(); _save_settings())
	settings.add_child(mouse_slider)
	volume_value = _label("Sound volume  ·  %d%%" % roundi(volume * 100), 16, CREAM)
	settings.add_child(volume_value)
	var volume_slider := HSlider.new()
	volume_slider.name = "Volume"
	volume_slider.min_value = 0
	volume_slider.max_value = 1
	volume_slider.step = 0.05
	volume_slider.value = volume
	volume_slider.custom_minimum_size.y = 32
	volume_slider.value_changed.connect(func(value: float): volume = value; volume_value.text = "Sound volume  ·  %d%%" % roundi(value * 100); _apply_settings(); _save_settings())
	settings.add_child(volume_slider)
	settings.add_child(_check("Invert vertical aim", invert_y, func(value: bool): invert_y = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Fullscreen", full_screen, func(value: bool): full_screen = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Dynamic sun shadows", shadows, func(value: bool): shadows = value; _apply_settings(); _save_settings()))
	settings.add_child(_check("Moonlit courtyard", night, func(value: bool): night = value; _apply_settings(); _save_settings()))
	controls_button = _button("CUSTOMIZE KEYBOARD CONTROLS", _open_controls)
	settings.add_child(controls_button)
	settings_back = _button("BACK", _close_settings)
	settings.add_child(settings_back)
	help_panel = _modal(root,"ControlsHelp",true)
	var help_content := _modal_content(help_panel)
	help_content.add_child(_label("CONTROLS & HELP",28,CREAM))
	help_back = _button("BACK",_close_help)
	help_content.add_child(help_back)
	help_label = _wrapped(Bindings.help_text(),17,CREAM)
	help_content.add_child(help_label)
	help_content.add_child(_wrapped("Courtyard: the same five Rama abilities against stationary targets. F5 restores cleared targets. Confluence adds lane battles, flight and grapple rings. Open F3 for ability timing and range.",15,MIST))
	help_panel.hide()
	hero_panel = RamaHeroPanel.new()
	rama_panel = hero_panel
	root.add_child(hero_panel)
	hero_panel.configure_effects(rama_effects)
	hero_panel.closed.connect(_close_hero)
	controls_overlay = ControlsOverlay.new()
	root.add_child(controls_overlay)
	controls_overlay.closed.connect(_close_controls)
	controls_overlay.bindings_changed.connect(_bindings_changed)
	hud.visible = false
	pause_panel.visible = false
	settings_panel.visible = false
	main_panel.focus_primary()
	_layout_interface()

func _theme() -> Theme:
	return HeroUITheme.create()

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
	HeroUITheme.button(button)
	button.pressed.connect(func(): _sound("menu"); callback.call())
	return button

func _check(text: String, enabled: bool, callback: Callable) -> CheckButton:
	var check := CheckButton.new()
	check.text = text
	check.button_pressed = enabled
	check.custom_minimum_size.y = 44
	check.toggled.connect(callback)
	return check

func _card() -> PanelContainer:
	var card := PanelContainer.new()
	var style := HeroUITheme.panel_style(false, 16)
	card.add_theme_stylebox_override("panel", style)
	return card

func _modal(root: Control, label: String, centered: bool) -> Control:
	var veil := Control.new()
	veil.name = label
	veil.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.add_child(veil)
	if centered:
		var shade := ColorRect.new()
		shade.color = Color(.015, .025, .04, .74)
		shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
		veil.add_child(shade)
	else:
		var wash := TextureRect.new()
		var texture := GradientTexture2D.new()
		texture.width = 1024
		texture.height = 1
		texture.fill_from = Vector2.ZERO
		texture.fill_to = Vector2.RIGHT
		texture.gradient = Gradient.new()
		# Keep the title's contrast on its left edge; the actual actor's face and
		# costume use the scene's lighting rather than a screen-space dark veil.
		texture.gradient.offsets = PackedFloat32Array([0, .36, .54, .67, 1])
		texture.gradient.colors = PackedColorArray([Color(.015, .025, .04, .98), Color(.015, .025, .04, .9), Color(.015, .025, .04, .25), Color(.015, .025, .04, 0), Color(.015, .025, .04, 0)])
		wash.texture = texture
		wash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		wash.mouse_filter = Control.MOUSE_FILTER_IGNORE
		veil.add_child(wash)
	var panel := _card()
	panel.name = "Card"
	if not centered:
		var title_style := StyleBoxEmpty.new()
		panel.add_theme_stylebox_override("panel", title_style)
	panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER if centered else Control.PRESET_CENTER_LEFT)
	panel.offset_left = -245 if centered else 48
	panel.offset_right = 245 if centered else 538
	panel.offset_top = -310
	panel.offset_bottom = 310
	veil.add_child(panel)
	var scroll := ScrollContainer.new()
	scroll.name = "Scroll"
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.follow_focus = true
	panel.add_child(scroll)
	var stack := VBoxContainer.new()
	stack.name = "Content"
	stack.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	stack.add_theme_constant_override("separation", 12)
	scroll.add_child(stack)
	return veil

func _modal_content(modal: Control) -> VBoxContainer:
	return modal.get_node("Card/Scroll/Content")

func _divider() -> HSeparator:
	return HSeparator.new()

func enter_confluence() -> void:
	_begin_scene_transition(&"confluence", main_panel.primary_button)

func enter_combat_film() -> void:
	_begin_scene_transition(&"combat_film", main_panel.film_button)

func _ensure_scene_transition() -> Control:
	if is_instance_valid(scene_transition): return scene_transition
	var layer := get_tree().root.get_node_or_null("YugaSceneTransitionLayer") as CanvasLayer
	if not layer:
		layer = CanvasLayer.new()
		layer.name = "YugaSceneTransitionLayer"
		layer.layer = 100
		layer.process_mode = Node.PROCESS_MODE_ALWAYS
		get_tree().root.add_child(layer)
	scene_transition = layer.get_node_or_null("SceneTransition") as Control
	if not scene_transition:
		scene_transition = SceneTransition.new()
		scene_transition.name = "SceneTransition"
		layer.add_child(scene_transition)
	scene_transition.phase_changed.connect(_on_transition_phase)
	scene_transition.cancelled.connect(_on_transition_cancelled)
	return scene_transition

func _transition_owns_navigation() -> bool:
	return is_instance_valid(scene_transition) and scene_transition.visible

func _begin_scene_transition(destination: StringName, opener: Control) -> bool:
	var loader := _ensure_scene_transition()
	if loader.is_busy() or loader.phase == &"error": return false
	_release_gameplay_actions()
	_transition_return_focus = weakref(opener) if is_instance_valid(opener) else null
	_transition_world_process = world.process_mode
	_transition_ui_process = ui.process_mode
	main_panel.set_launch_state("loading")
	if not loader.begin(destination, self, opener):
		main_panel.set_launch_state("error", "Another scene is opening. Return here and try again.")
		main_panel.focus_primary()
		return false
	# These children intentionally have explicit process modes, so the caller's
	# disabled mode alone does not isolate them during loading or recovery.
	world.process_mode = Node.PROCESS_MODE_DISABLED
	ui.process_mode = Node.PROCESS_MODE_DISABLED
	_transition_isolating = true
	return true

func _on_transition_phase(phase: StringName, message: String, _progress: float) -> void:
	if phase in [&"queued", &"loading", &"constructing", &"error"]:
		# Recovery stays in the loader with its Retry/Back actions. Keep the title
		# disabled behind it, including when the resource request has failed.
		main_panel.set_launch_state("loading", message)

func _on_transition_cancelled(_destination: StringName) -> void:
	if _transition_isolating:
		world.process_mode = _transition_world_process
		ui.process_mode = _transition_ui_process
		_transition_isolating = false
	main_panel.set_launch_state("ready")
	_restore_modal_opener(_transition_return_focus, main_panel, main_panel.primary_button)
	_transition_return_focus = null

func start_training() -> void:
	if _transition_owns_navigation(): return
	_release_gameplay_actions()
	title_light.hide()
	player.camera.make_current()
	hero_panel.hide()
	help_panel.hide()
	started = true
	main_panel.visible = false
	settings_panel.visible = false
	pause_panel.visible = false
	hud.visible = true
	get_tree().paused = false
	player.active = not rama_runtime or not rama_runtime.configured or rama_runtime.vitals.alive
	_set_practice_suspended(false)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	_refresh_hud()
	print("YUGA_NATIVE_TRAINING_STARTED")

func set_paused(value: bool) -> void:
	if not started:
		return
	_release_gameplay_actions()
	if value and not is_instance_valid(rama_runtime):
		player.velocity.x = 0
		player.velocity.z = 0
		player.dash_time = 0
		player.dash_direction = Vector3.ZERO
	get_tree().paused = value
	_set_practice_suspended(value)
	pause_panel.visible = value
	hud.visible = not value
	settings_panel.visible = false
	if not value:
		player.active = not rama_runtime or not rama_runtime.configured or rama_runtime.vitals.alive
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE if value else Input.MOUSE_MODE_CAPTURED
	if value:
		_restore_modal_opener(null, pause_panel, resume_button)
	else:
		get_viewport().gui_release_focus()
	print("YUGA_NATIVE_PAUSE ", value)

func reset_training() -> void:
	_release_gameplay_actions()
	player.reset()
	if is_instance_valid(practice_army) and practice_army.configured:
		practice_army.reset("courtyard reset")
	else:
		for target in targets: target.reset_target()
	# Defeat disables the player; resetting vitals alone does not reactivate input.
	# A paused reset and title reset must stay inactive until their owner resumes.
	player.active = started and not get_tree().paused and (not is_instance_valid(rama_runtime) or not rama_runtime.configured or rama_runtime.vitals.alive)
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
	if _transition_owns_navigation(): return
	get_tree().paused = false
	player.active = false
	started = false
	_set_practice_suspended(true)
	reset_training()
	hud.visible = false
	pause_panel.visible = false
	settings_panel.visible = false
	help_panel.hide()
	hero_panel.hide()
	main_panel.visible = true
	title_light.show()
	title_camera.make_current()
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	main_panel.set_launch_state("ready")
	main_panel.focus_primary()

func _input(event: InputEvent) -> void:
	if _transition_owns_navigation(): return
	if event is InputEventKey and event.echo: return
	if controls_overlay.visible: return
	if hero_panel.visible: return
	if help_panel.visible and event is InputEventKey and event.pressed and event.keycode in [KEY_PAGEDOWN, KEY_PAGEUP, KEY_HOME, KEY_END]:
		var scroll: ScrollContainer = help_panel.get_node("Card/Scroll")
		match event.keycode:
			KEY_PAGEDOWN: scroll.scroll_vertical += int(scroll.size.y * .75)
			KEY_PAGEUP: scroll.scroll_vertical -= int(scroll.size.y * .75)
			KEY_HOME: scroll.scroll_vertical = 0
			KEY_END: scroll.scroll_vertical = int(scroll.get_v_scroll_bar().max_value)
		get_viewport().set_input_as_handled()
		return
	if _trap_modal_focus(event): return
	if event.is_action_pressed("open_invocations") and not settings_panel.visible and not help_panel.visible:
		_open_hero()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("help_controls") and not settings_panel.visible:
		if help_panel.visible: _close_help()
		else: _open_help()
		get_viewport().set_input_as_handled()
		return
	if event.is_action_pressed("pause_game"):
		if help_panel.visible:
			_close_help()
		elif settings_panel.visible:
			_close_settings()
		elif started:
			set_paused(not get_tree().paused)
		get_viewport().set_input_as_handled()
	if event.is_action_pressed("reset_training") and started and not get_tree().paused:
		reset_training()

func _release_gameplay_actions() -> void:
	Bindings.release_gameplay()
	if is_instance_valid(player) and player.has_method("cancel_traversal"):
		player.cancel_traversal("interface")

func _on_focus_lost() -> void:
	if _transition_owns_navigation(): return
	_release_gameplay_actions()
	if controls_overlay and controls_overlay.visible:
		controls_overlay.cancel_capture()
		return
	# Losing application focus must not turn a temporary guide into an
	# implicit resume when it closes. Keep the current modal visible.
	if started:
		if hero_panel.visible and hero_panel_return == "training": hero_panel_return = "pause"
		if help_panel.visible and help_return == "training": help_return = "pause"
	if settings_panel.visible or help_panel.visible or hero_panel.visible: return
	if started and not smoke_mode: set_paused(true)

func _open_controls() -> void:
	_release_gameplay_actions()
	settings_panel.hide()
	controls_overlay.open()

func _close_controls() -> void:
	settings_panel.show()
	controls_button.grab_focus()
	_bindings_changed()

func _bindings_changed() -> void:
	help_label.text = Bindings.help_text()
	status_label.text = Bindings.label("reload") + " reload  ·  F3 abilities  ·  F2 help"
	_refresh_hud()
	hero_panel.refresh_bindings()

func _open_hero() -> void:
	_release_gameplay_actions()
	hero_panel_return = "menu" if not started else ("pause" if get_tree().paused else "training")
	var owner: Control = main_panel if hero_panel_return == "menu" else pause_panel
	hero_return_focus = _remember_modal_opener(owner) if hero_panel_return != "training" else null
	main_panel.hide()
	pause_panel.hide()
	hud.hide()
	if started: get_tree().paused = true
	_set_practice_suspended(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	# The caller restores its owner first and validates the opener afterward.
	# The shared panel must not then restore a disabled or reparented old control.
	hero_panel.open("courtyard" if started or main_panel.selected_mode == "train" else "confluence")

func _close_hero() -> void:
	if hero_panel_return == "menu":
		main_panel.show()
		_restore_modal_opener(hero_return_focus, main_panel, main_panel.primary_button)
	else:
		set_paused(hero_panel_return == "pause")
		if hero_panel_return == "pause": _restore_modal_opener(hero_return_focus, pause_panel, resume_button)

func cast_rama_ability(id: String) -> Dictionary:
	if is_instance_valid(rama_runtime): return rama_runtime.cast_ability(id)
	return {"ok":false, "reason":"Rama practice is not ready."}

func _open_help() -> void:
	_release_gameplay_actions()
	help_return = "menu" if not started else ("pause" if get_tree().paused else "training")
	help_return_focus = _remember_modal_opener(main_panel if help_return == "menu" else pause_panel) if help_return != "training" else null
	main_panel.hide()
	pause_panel.hide()
	hud.hide()
	_bindings_changed()
	help_panel.show()
	if started: get_tree().paused = true
	_set_practice_suspended(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	help_back.grab_focus()

func _close_help() -> void:
	help_panel.hide()
	if help_return == "menu":
		main_panel.show()
		_restore_modal_opener(help_return_focus, main_panel, main_panel.primary_button)
	else:
		set_paused(help_return == "pause")
		if help_return == "pause": _restore_modal_opener(help_return_focus, pause_panel, resume_button)

func _remember_modal_opener(owner: Control) -> WeakRef:
	var previous := get_viewport().gui_get_focus_owner()
	if is_instance_valid(previous) and owner.is_ancestor_of(previous) and previous.is_visible_in_tree():
		return weakref(previous)
	return null

func _restore_modal_opener(previous_ref: WeakRef, owner: Control, fallback: Control) -> void:
	var previous: Control = previous_ref.get_ref() if previous_ref else null
	if is_instance_valid(previous) and owner.is_ancestor_of(previous) and previous.is_visible_in_tree() and previous.focus_mode == Control.FOCUS_ALL:
		if (not previous is BaseButton or not previous.disabled) and (not previous is Slider or previous.editable):
			previous.grab_focus()
			return
	if is_instance_valid(fallback) and fallback.is_visible_in_tree() and fallback.focus_mode == Control.FOCUS_ALL and (not fallback is BaseButton or not fallback.disabled) and (not fallback is Slider or fallback.editable):
		fallback.grab_focus()
		return
	var order: Array[Control] = []
	_focusable_children(owner, order)
	if not order.is_empty(): order[0].grab_focus()

func _process(_delta: float) -> void:
	var viewport := get_viewport().get_visible_rect().size
	if viewport != last_ui_size: _layout_interface()

func _layout_interface() -> void:
	var viewport := get_viewport().get_visible_rect().size
	last_ui_size = viewport
	# The launch shell owns its responsive column and wordmark sizing.
	for modal in [pause_panel,settings_panel,help_panel]:
		if not modal: continue
		var panel: Control = modal.get_node("Card")
		panel.set_anchors_preset(Control.PRESET_TOP_LEFT)
		panel.size = Vector2(minf(560, viewport.x - 48), minf(620, viewport.y - 48))
		panel.position = (viewport - panel.size) * .5

func _trap_modal_focus(event: InputEvent) -> bool:
	if not event is InputEventKey or not event.pressed or event.keycode != KEY_TAB: return false
	var active_modal: Control = null
	for modal in [main_panel, pause_panel, settings_panel, help_panel]:
		if modal.visible: active_modal = modal; break
	if not active_modal: return false
	var order: Array[Control] = []
	_focusable_children(active_modal, order)
	if order.is_empty(): return false
	var index := order.find(get_viewport().gui_get_focus_owner())
	order[posmod(index + (-1 if event.shift_pressed else 1), order.size())].grab_focus()
	get_viewport().set_input_as_handled()
	return true

func _focusable_children(node: Node, result: Array[Control]) -> void:
	for child in node.get_children():
		if (child is BaseButton or child is Slider) and child.is_visible_in_tree() and child.focus_mode == Control.FOCUS_ALL:
			if child is BaseButton and child.disabled: continue
			if child is Slider and not child.editable: continue
			result.append(child)
		_focusable_children(child, result)

func _open_settings(from_menu: bool) -> void:
	_release_gameplay_actions()
	settings_from_menu = from_menu
	settings_return_focus = _remember_modal_opener(main_panel if from_menu else pause_panel)
	main_panel.visible = false
	pause_panel.visible = false
	hud.hide()
	settings_panel.visible = true
	if started:
		get_tree().paused = true
	_set_practice_suspended(true)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	settings_panel.get_node("Card/Scroll/Content/Sensitivity").grab_focus()
	call_deferred("_settle_settings_entry")

func _settle_settings_entry() -> void:
	# Focus may scroll against the hidden panel's old container geometry. Wait
	# for both layout passes, then reveal the heading without taking focus away.
	var scroll: ScrollContainer = settings_panel.get_node("Card/Scroll")
	var sensitivity_control: Control = scroll.get_node("Content/Sensitivity")
	for unused in range(2):
		await get_tree().process_frame
		if not settings_panel.visible or get_viewport().gui_get_focus_owner() != sensitivity_control: return
	scroll.scroll_vertical = 0

func _close_settings() -> void:
	settings_panel.visible = false
	if settings_from_menu:
		main_panel.visible = true
		_restore_modal_opener(settings_return_focus, main_panel, main_panel.primary_button)
	else:
		pause_panel.visible = true
		_restore_modal_opener(settings_return_focus, pause_panel, resume_button)

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
	if not is_instance_valid(stats_label): return
	stats_label.text = "%d hits  ·  %d targets cleared  ·  %02d:%02d" % [hit_count, defeat_count, int(elapsed) / 60, int(elapsed) % 60]
	objective_label.text = "Master the bow" if defeat_count < 5 else "Find your rhythm"
	if rama_hud: rama_hud._refresh()

func _on_fired(origin: Vector3, direction: Vector3, _empowered: bool) -> void:
	if is_instance_valid(rama_runtime) and rama_runtime.configured: return
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
	if is_instance_valid(rama_runtime) and rama_runtime.configured: return
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

func _saved_number(config: ConfigFile,section: String,key: String,fallback: float,minimum: float,maximum: float) -> float:
	var value = config.get_value(section,key,fallback)
	return clampf(float(value),minimum,maximum) if (value is int or value is float) and is_finite(float(value)) else fallback

func _saved_bool(config: ConfigFile,section: String,key: String,fallback: bool) -> bool:
	var value = config.get_value(section,key,fallback)
	return value if value is bool else fallback

func _load_settings() -> void:
	var loaded := Bindings.read_config(SAVE_PATH)
	if not loaded.ok: return
	var config: ConfigFile = loaded.config
	sensitivity = _saved_number(config,"controls","sensitivity",1.0,0.35,2.5)
	volume = _saved_number(config,"audio","volume",0.7,0,1)
	invert_y = _saved_bool(config,"controls","invert_y",false)
	full_screen = _saved_bool(config,"video","fullscreen",false)
	shadows = _saved_bool(config,"video","shadows",true)
	night = _saved_bool(config,"video","night",false)

func _save_settings() -> void:
	var result := Bindings.merge_settings({"controls":{"sensitivity":sensitivity,"invert_y":invert_y},"audio":{"volume":volume},"video":{"fullscreen":full_screen,"shadows":shadows,"night":night}})
	if settings_notice:
		settings_notice.text = "Changes saved on this computer." if result.ok else result.message
		settings_notice.add_theme_color_override("font_color", MIST if result.ok else GOLD)
	if not result.ok: push_warning(result.message)

func _apply_settings() -> void:
	if is_instance_valid(rama_runtime): rama_runtime.set_volume(volume)
	if volume <= 0:
		for audio in audio_players: audio.stop()
	if is_instance_valid(player):
		player.sensitivity = sensitivity * 0.0024
		player.invert_y = invert_y
	if DisplayServer.get_name() != "headless":
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if full_screen else DisplayServer.WINDOW_MODE_WINDOWED)
	if is_instance_valid(sun):
		ProductionLighting.apply(world_environment.environment, sun, world, night, shadows)
		MythicEnvironment.set_phase(world, 1.0 if night else 0.0)
		HeroDistrict.set_phase(world, 1.0 if night else 0.0)
		if not hero_atmosphere.configure(world, world_environment.environment, sun, night):
			push_error("Hero courtyard atmosphere could not be configured")

func _quit() -> void:
	get_tree().paused = false
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	get_tree().quit()
