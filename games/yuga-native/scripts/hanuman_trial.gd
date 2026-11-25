extends Node3D
## Reuses the native Lanka court and practice target clock in an offline
## training scene built around Hanuman's own third-person rig and abilities.

const Actor = preload("res://scripts/hanuman_actor.gd")
const Bindings = preload("res://scripts/input_bindings.gd")
const Target = preload("res://scripts/target.gd")
const PracticeArmy = preload("res://scripts/rama_practice_army.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const UI = preload("res://scripts/hero_ui_theme.gd")
const Transition = preload("res://scripts/scene_transition.gd")
const Water = preload("res://shaders/production_water.gdshader")
const Lighting = preload("res://scripts/production_lighting.gd")
const COURT := "res://assets/environment/lanka_courtyard.glb"
const Combat = preload("res://scripts/hanuman_combat.gd")
const Effects = preload("res://scripts/hanuman_trial_effects.gd")
const SPAWN := Vector3(0, .06, 9)
const DRILL_TARGETS := [Vector3(0, .02, 4.5), Vector3(3.3, .02, 2.5), Vector3(-3.3, .02, 2.5), Vector3(0, .02, -2.8), Vector3(3.0, .02, 10.5)]
const INPUT_SLOTS := {"primary":"fire", "ability_1":"pulse", "ability_2":"dash", "ability_3":"guardian_circle", "ultimate":"ultimate"}
const MAX_TARGET_LABEL_PX := 25.0

var hero: CharacterBody3D
var army: Node3D
var combat: Node3D
var vitals: Node
var effects: Node3D
var ready_for_play := false
var paused := true
var _paused_before_return := false
var _leaving := false
var _profiles: Dictionary = {}
var _slot_action: Dictionary = {}
var _event_status := ""
var _event_count := 0
var _clock := 0.0
var _hud: Control
var _status: Label
var _vital: Label
var _pause: PanelContainer
var _pause_heading: Label
var _pause_hint: Label
var _resume: Button
var _reset: Button
var _back: Button
var _ability_cards: HBoxContainer
var _cards: Dictionary = {}
var _target_labels: Array[Dictionary] = []
var _stage_meshes := 0

func _ready() -> void:
	Bindings.install()
	_build_ui()
	if not _create_world() or not _configure_combat():
		_show_message("Trial unavailable", _event_status)
		_resume.disabled = true
		_reset.disabled = true
		_back.grab_focus()
		return
	ready_for_play = true
	get_window().focus_exited.connect(_focus_lost)
	_show_message("Hanuman Trial", "Move with %s / %s / %s / %s. Aim with the mouse. Read the ability keys below, then try each move against the courtyard targets." % [Bindings.label("move_forward"), Bindings.label("move_left"), Bindings.label("move_back"), Bindings.label("move_right")])
	_set_paused(true)
	_update_hud()

func _create_world() -> bool:
	var packed := load(COURT) as PackedScene
	if packed == null:
		_event_status = "The practice courtyard asset could not load."
		return false
	var court := packed.instantiate() as Node3D
	court.name = &"AuthoredLankaCourtyard"
	add_child(court)
	_mount_court_collision(court)
	_lighting()
	var targets: Array[Node3D] = []
	for index in range(DRILL_TARGETS.size()):
		var target := StaticBody3D.new()
		target.set_script(Target)
		target.name = "TrialTarget%02d" % (index + 1)
		target.number = index + 1
		target.position = DRILL_TARGETS[index]
		add_child(target)
		targets.append(target)
	army = PracticeArmy.new()
	army.name = &"TrialClock"
	add_child(army)
	_floor_collision()
	if not army.configure(targets):
		_event_status = "The practice targets could not be registered."
		return false
	# The gold target behind the starting position receives allied effects.
	army.units.back().team = "sun"
	targets.back().ring_material.albedo_color = Color("f9bd57")
	targets.back().ring_material.emission = Color("c58527")
	for target in targets:
		target.label.modulate = Color("ffd48c") if target == targets.back() else Color("c8e9f0")
		target.label.pixel_size = .0058
		target.label.outline_size = 5
		_target_labels.append({"label":target.label,"size":target.label.pixel_size})
	vitals = Vitals.new()
	add_child(vitals)
	if not vitals.configure(army):
		_event_status = "The practice hero receiver could not be registered."
		return false
	hero = Actor.new()
	hero.name = &"Hanuman"
	hero.position = SPAWN
	add_child(hero)
	var model := ResourceLoader.load(Actor.MODEL_PATH, "PackedScene") as PackedScene if ResourceLoader.exists(Actor.MODEL_PATH, "PackedScene") else null
	if not hero.configure_visual(model):
		_event_status = hero.last_error
		return false
	var portrait := Camera3D.new()
	portrait.name = "TrialOverview"
	portrait.fov = 32.0
	portrait.position = SPAWN + Vector3(3.75, 1.77, -5.2)
	add_child(portrait)
	portrait.look_at(SPAWN + Vector3(0, 1.13, 0))
	portrait.current = true
	return true

func _mount_court_collision(node: Node3D, inherited := false) -> void:
	# Names and inheritance follow the existing courtyard asset contract.
	var collidable := inherited or String(node.name).begins_with("COL_")
	if node is MeshInstance3D:
		if String(node.name).begins_with("WATER_"):
			var water := ShaderMaterial.new()
			water.shader = Water
			node.material_override = water
		if collidable:
			node.create_trimesh_collision()
			_stage_meshes += 1
	for child in node.get_children():
		if child is Node3D and not child is StaticBody3D: _mount_court_collision(child, collidable)

func _floor_collision() -> void:
	var floor := StaticBody3D.new()
	floor.name = &"TrialFloor"
	floor.position.y = -.25
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(44, .5, 50)
	shape.shape = box
	floor.add_child(shape)
	add_child(floor)
	# The same boxes bound the actor and the fixed-step target adapter.
	for pair in army.boxes:
		var body := StaticBody3D.new()
		body.position = pair.position
		var bound := CollisionShape3D.new()
		var extent := BoxShape3D.new()
		extent.size = pair.size
		bound.shape = extent
		body.add_child(bound)
		add_child(body)

func _lighting() -> void:
	var atmosphere := WorldEnvironment.new()
	atmosphere.environment = Environment.new()
	add_child(atmosphere)
	var sun := DirectionalLight3D.new()
	add_child(sun)
	Lighting.apply(atmosphere.environment, sun, self)

func _load_settings() -> void:
	var result := Bindings.read_config(Bindings.SAVE_PATH)
	if not result.ok: return
	var config: ConfigFile = result.config
	var sensitivity: Variant = config.get_value("controls", "sensitivity", 1.0)
	var invert: Variant = config.get_value("controls", "invert_y", false)
	if typeof(sensitivity) in [TYPE_FLOAT, TYPE_INT] and is_finite(float(sensitivity)):
		hero.look_sensitivity = .0024 * clampf(float(sensitivity), .35, 2.5)
	if invert is bool: hero.invert_y = invert
	effects.set_options({"volume":config.get_value("audio", "volume", .7)})

func _configure_combat() -> bool:
	effects = Effects.new()
	effects.name = "TrialEffects"
	add_child(effects)
	_load_settings()
	combat = Combat.new()
	combat.name = "HanumanCombat"
	add_child(combat)
	combat.ability_event.connect(_on_event)
	if not combat.configure(army, hero.accept_move, vitals, func(): return hero.global_position):
		_event_status = "The training ability catalog failed validation."
		return false
	for definition: Dictionary in combat.report(false).abilities:
		var id := String(definition.id)
		var slot := String(definition.slot).to_lower()
		if not INPUT_SLOTS.has(slot) or _slot_action.has(slot) or not hero.has_clip(StringName(definition.motion)):
			_event_status = "An ability is missing its input or authored action: " + id
			return false
		_profiles[id] = definition
		_slot_action[slot] = id
		_add_ability_card(definition, String(INPUT_SLOTS[slot]))
	return true

func _input(event: InputEvent) -> void:
	if _leaving or not ready_for_play: return
	if event.is_action_pressed("pause_game", false):
		if not paused: _show_message("Trial paused", "Resume practice or reset the targets.")
		_set_paused(not paused)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("reset_training", false) and not paused:
		_reset_trial()
		get_viewport().set_input_as_handled()

func _unhandled_input(event: InputEvent) -> void:
	if paused or _leaving or not ready_for_play: return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		hero.turn_camera(event.relative)
		return
	for slot in _slot_action:
		var binding := String(INPUT_SLOTS[slot])
		if event.is_action_pressed(binding, false):
			_request(String(_slot_action[slot]))
			get_viewport().set_input_as_handled()
			return

func _request(id: String) -> Dictionary:
	if not ready_for_play or paused or _leaving or not _profiles.has(id): return {"accepted":false}
	if not hero.is_on_floor():
		_event_status = "Land before using a grounded ability."
		_update_hud()
		return {"accepted":false,"reason":_event_status}
	var result: Dictionary = combat.request_ability(id, hero.global_position, hero.aim_forward(), hero.aim_ground())
	if not result.get("accepted", false):
		_event_status = String(result.get("reason", "Ability unavailable"))
		_update_hud()
	return result

func _on_event(event: Dictionary) -> void:
	_event_count += 1
	var id := String(event.get("ability_id", ""))
	var definition: Dictionary = _profiles.get(id, {})
	hero.play_event(event, definition)
	if is_instance_valid(effects): effects.consume_event(event)
	if not definition.is_empty():
		match String(event.kind):
			"begin": _event_status = String(definition.label) + " · preparing"
			"release": _event_status = String(definition.label)
			"cancel": _event_status = String(event.get("reason", "Cast cancelled"))
			"impact":
				var receipts: Variant = event.get("receipts", [])
				if receipts is Array and not receipts.is_empty():
					_event_status = String(definition.label) + " · %d target effects" % receipts.size()
	_update_hud()

func _process(delta: float) -> void:
	if not ready_for_play or paused: return
	_clock -= delta
	if _clock <= 0:
		_clock = .075
		_update_hud()

func _set_paused(value: bool) -> void:
	if not ready_for_play: return
	paused = value
	Bindings.release_gameplay()
	army.set_suspended(value)
	combat.set_suspended(value)
	vitals.set_suspended(value)
	effects.set_suspended(value)
	hero.set_paused(value)
	if not value:
		_resume.text = "Resume practice"
		hero.camera.current = true
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	else:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	_pause.visible = value
	if value: _resume.grab_focus()

func _focus_lost() -> void:
	if ready_for_play and not paused and not _leaving:
		_show_message("Trial paused", "Return when you are ready. The practice clock is stopped.")
		_set_paused(true)

func _reset_trial() -> void:
	if not ready_for_play: return
	Bindings.release_gameplay()
	army.reset("Trial reset")
	hero.reset_at(SPAWN)
	_event_status = "Trial reset. All five abilities are available."
	_update_hud()

func _return_title() -> void:
	if _leaving: return
	_paused_before_return = paused
	if ready_for_play: _set_paused(true)
	var loader := Transition.ensure_for_tree(get_tree())
	if not loader.cancelled.is_connected(_on_return_cancelled): loader.cancelled.connect(_on_return_cancelled)
	_leaving = loader.begin(&"courtyard", self, _back)
	if not _leaving and ready_for_play: _set_paused(_paused_before_return)

func _on_return_cancelled(destination: StringName) -> void:
	if destination != &"courtyard" or not _leaving: return
	_leaving = false
	if ready_for_play: _set_paused(_paused_before_return)

func _exit_tree() -> void:
	if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	Bindings.release_gameplay()

func _build_ui() -> void:
	var canvas := CanvasLayer.new()
	add_child(canvas)
	_hud = Control.new()
	_hud.name = "TrialHud"
	_hud.theme = UI.create()
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	canvas.add_child(_hud)
	var top := PanelContainer.new()
	top.add_theme_stylebox_override("panel", UI.hud_panel_style(&"status", UI.SPACE_MD))
	top.position = Vector2(20, 20)
	_hud.add_child(top)
	var heading := VBoxContainer.new()
	heading.add_theme_constant_override("separation", UI.SPACE_XS)
	top.add_child(heading)
	heading.add_child(UI.label("HANUMAN  /  WIND-BORN GUARDIAN", UI.TYPE_HUD_TITLE, UI.GOLD))
	_vital = UI.label("Offline practice", UI.TYPE_HUD_DETAIL, UI.MIST)
	heading.add_child(_vital)
	var crosshair := Label.new()
	crosshair.text = "◈"
	crosshair.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	crosshair.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	crosshair.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	crosshair.position -= Vector2(10, 13)
	crosshair.size = Vector2(20, 26)
	crosshair.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(crosshair)
	var hud_bottom := MarginContainer.new()
	hud_bottom.name = "Abilities"
	hud_bottom.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	hud_bottom.offset_left = 20.0
	hud_bottom.offset_right = -20.0
	hud_bottom.offset_top = -104.0
	hud_bottom.offset_bottom = -18.0
	hud_bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(hud_bottom)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", UI.SPACE_XS)
	hud_bottom.add_child(column)
	_status = UI.label("Aim at the blue targets. Gold marks an ally.", UI.TYPE_BODY, UI.CREAM)
	_status.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status.add_theme_color_override("font_shadow_color", Color("070a12"))
	_status.add_theme_constant_override("shadow_offset_y", 2)
	column.add_child(_status)
	_ability_cards = HBoxContainer.new()
	_ability_cards.name = "AbilityList"
	_ability_cards.add_theme_constant_override("separation", UI.SPACE_SM)
	column.add_child(_ability_cards)
	var pause_anchor := MarginContainer.new()
	pause_anchor.set_anchors_and_offsets_preset(Control.PRESET_CENTER_LEFT)
	pause_anchor.offset_left = 20
	pause_anchor.offset_right = 404
	pause_anchor.offset_top = -141
	pause_anchor.offset_bottom = 141
	pause_anchor.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_hud.add_child(pause_anchor)
	_pause = PanelContainer.new()
	_pause.add_theme_stylebox_override("panel", UI.panel_style(true))
	pause_anchor.add_child(_pause)
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", UI.SPACE_SM)
	_pause.add_child(content)
	_pause_heading = UI.label("Hanuman Trial", UI.TYPE_SECTION, UI.GOLD)
	content.add_child(_pause_heading)
	_pause_hint = UI.label("", UI.TYPE_BODY, UI.CREAM)
	_pause_hint.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(_pause_hint)
	_resume = _button("Begin practice", func(): _set_paused(false), &"primary")
	_resume.name = "BeginPractice"
	content.add_child(_resume)
	_reset = _button("Reset targets", _reset_trial)
	_reset.name = "ResetTargets"
	content.add_child(_reset)
	_back = _button("Return to title", _return_title)
	_back.name = "ReturnToTitle"
	content.add_child(_back)
	for index in range(3):
		var choices := [_resume, _reset, _back]
		choices[index].focus_next = choices[index].get_path_to(choices[(index + 1) % 3])
		choices[index].focus_previous = choices[index].get_path_to(choices[(index + 2) % 3])

func _button(text: String, callback: Callable, variant: StringName = &"secondary") -> Button:
	var button := Button.new()
	button.text = text
	UI.button_variant(button, variant)
	button.pressed.connect(callback)
	return button

func _show_message(title: String, message: String) -> void:
	_pause_heading.text = title
	_pause_hint.text = message

func _add_ability_card(definition: Dictionary, input: String) -> void:
	var card := PanelContainer.new()
	card.name = String(definition.id)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.add_theme_stylebox_override("panel", UI.hud_panel_style(&"ready"))
	card.tooltip_text = String(definition.get("description", ""))
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_ability_cards.add_child(card)
	var content := VBoxContainer.new()
	content.add_theme_constant_override("separation", 3)
	card.add_child(content)
	var label := UI.label(String(definition.label), UI.TYPE_HUD_DETAIL, UI.CREAM)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(label)
	var detail := UI.label(Bindings.label(input), UI.TYPE_HUD_DETAIL, UI.GOLD)
	content.add_child(detail)
	_cards[String(definition.id)] = {"detail":detail,"key":Bindings.label(input)}

func _update_hud() -> void:
	if not ready_for_play: return
	_update_target_label_sizes()
	_status.text = _event_status if not _event_status.is_empty() else "Gold marks an ally  ·  Esc menu  ·  F5 reset"
	_vital.text = "%.0f / %.0f health   ·   %.0f shield" % [vitals.health, vitals.MAX_HEALTH, vitals.shield]
	for definition: Dictionary in combat.report(false).abilities:
		var card: Dictionary = _cards.get(String(definition.id), {})
		if card.is_empty(): continue
		var left := float(definition.cooldown_remaining)
		card.detail.text = "%s  ·  %s" % [card.key, ("%.1fs" % left) if left > 0.0 else "Ready"]
		card.detail.modulate = UI.MIST if left > 0.0 else UI.GOLD

func _update_target_label_sizes() -> void:
	var view := get_viewport().get_camera_3d()
	if not is_instance_valid(view): return
	var view_up := view.global_basis.y.normalized()
	for entry in _target_labels:
		var label: Label3D = entry.label
		if not is_instance_valid(label) or view.is_position_behind(label.global_position): continue
		var anchor := view.unproject_position(label.global_position)
		var world_em := float(label.font_size) * float(entry.size)
		var top := view.unproject_position(label.global_position + view_up * world_em)
		var pixels := anchor.distance_to(top)
		if is_finite(pixels):
			var scale_ := minf(1.0, MAX_TARGET_LABEL_PX / maxf(.001, pixels))
			label.pixel_size = float(entry.size) * scale_

func report() -> Dictionary:
	return {"ready":ready_for_play, "paused":paused, "events":_event_count, "collidable_court_meshes":_stage_meshes,
		"status":_event_status, "actor":hero.report() if is_instance_valid(hero) else {},
		"combat":combat.report() if is_instance_valid(combat) else {}, "targets":army.report() if is_instance_valid(army) else {},
		"effects":effects.report() if is_instance_valid(effects) else {}}
