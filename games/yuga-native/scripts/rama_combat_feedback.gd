extends Control
## Read-only aim feedback. A launch or wall collision is never a confirmed hit.
## Position is a temporary viewport overlay, deliberately outside the bottom HUD.
const UI = preload("res://scripts/hero_ui_theme.gd")
const HOLD_SECONDS := 1.1
const RECEIPT_CAP := 96
const HURT := Color("f49b90")
var runtime: Node3D
var badge: PanelContainer
var hit_text: Label
var hurt_text: Label
var hurt_panel: PanelContainer
var _generation := -1
var _sequence := -1
var _vitals_generation := -1
var _damage_serial := -1
var _seen: Dictionary = {}
var _seen_order: Array[String] = []
var _cast_key := ""
var _targets: Dictionary = {}
var _damage := 0.0
var _defeats := 0
var _shield_only := true
var _until := -1.0
var _hurt_until := -1.0
var _last_incoming: Dictionary = {}
var _layout_suppressed := false
var _confirmed_events := 0
var _rejected := 0

func _ready() -> void:
	name = "ConfirmedCombatFeedback"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	theme = UI.create()
	badge = PanelContainer.new()
	badge.name = "ConfirmedHit"
	badge.mouse_filter = Control.MOUSE_FILTER_IGNORE
	badge.add_theme_stylebox_override("panel", UI.hud_panel_style(&"quiet", UI.SPACE_XS))
	add_child(badge)
	hit_text = UI.label("", UI.TYPE_CAPTION, UI.CREAM)
	hit_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hit_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	badge.add_child(hit_text)
	hurt_panel = PanelContainer.new()
	hurt_panel.name = "IncomingDamage"
	hurt_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var hurt_surface := UI.hud_panel_style(&"quiet", UI.SPACE_XS)
	hurt_surface.content_margin_top = 0
	hurt_surface.content_margin_bottom = 0
	hurt_panel.add_theme_stylebox_override("panel", hurt_surface)
	add_child(hurt_panel)
	hurt_text = UI.label("", UI.TYPE_CAPTION, HURT)
	hurt_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	hurt_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	hurt_panel.add_child(hurt_text)
	hide()
	_bind_signals()

func _enter_tree() -> void:
	_bind_signals.call_deferred()

func configure(value: Node3D) -> void:
	_disconnect()
	runtime = value
	_clear_history()
	if is_instance_valid(runtime) and is_instance_valid(runtime.get("kit")):
		_generation = int(runtime.kit.generation)
	if is_instance_valid(runtime) and is_instance_valid(runtime.get("vitals")):
		_vitals_generation = int(runtime.vitals.generation)
	_bind_signals()

func _bind_signals() -> void:
	if not is_inside_tree() or not is_instance_valid(runtime): return
	if runtime.has_signal("combat_event") and not runtime.combat_event.is_connected(consume_event): runtime.combat_event.connect(consume_event)
	var vitals: Node = runtime.get("vitals")
	if is_instance_valid(vitals):
		if not vitals.damaged.is_connected(consume_damage): vitals.damaged.connect(consume_damage)
		if not vitals.changed.is_connected(_vitals_changed): vitals.changed.connect(_vitals_changed)

func _disconnect() -> void:
	if not is_instance_valid(runtime): return
	if runtime.has_signal("combat_event") and runtime.combat_event.is_connected(consume_event): runtime.combat_event.disconnect(consume_event)
	var vitals: Node = runtime.get("vitals")
	if is_instance_valid(vitals):
		if vitals.damaged.is_connected(consume_damage): vitals.damaged.disconnect(consume_damage)
		if vitals.changed.is_connected(_vitals_changed): vitals.changed.disconnect(_vitals_changed)

func _exit_tree() -> void:
	_disconnect()
	_clear_history()

func _number(value: Variant, maximum := 100000.0) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) >= 0 and float(value) <= maximum

func _usable() -> bool:
	if not is_inside_tree() or not is_instance_valid(runtime) or not runtime.get("configured") or not runtime.is_inside_tree(): return false
	for node in [runtime.get("kit"), runtime.get("vitals"), runtime.get("army"), runtime.get("player")]:
		if not is_instance_valid(node): return false
	return not runtime.suspended and not get_tree().paused and runtime.vitals.alive and runtime.player.active and String(runtime.army.winner).is_empty()

func _clear_visuals() -> void:
	_damage = 0
	_defeats = 0
	_targets.clear()
	_cast_key = ""
	_until = -1
	_hurt_until = -1
	_last_incoming.clear()
	if is_instance_valid(hit_text): hit_text.text = ""
	if is_instance_valid(hurt_text): hurt_text.text = ""
	hide()
	queue_redraw()

func _clear_history() -> void:
	_clear_visuals()
	_generation = -1
	_sequence = -1
	_vitals_generation = -1
	_damage_serial = -1
	_seen.clear()
	_seen_order.clear()

func _vitals_changed() -> void:
	if not is_instance_valid(runtime) or not is_instance_valid(runtime.get("vitals")): return
	if _vitals_generation != int(runtime.vitals.generation):
		_vitals_generation = int(runtime.vitals.generation)
		_damage_serial = -1
		_clear_visuals()
	if not _usable(): _clear_visuals()

func consume_event(event: Dictionary) -> void:
	if not _usable():
		_clear_visuals()
		return
	if not event.get("generation") is int or int(event.generation) != int(runtime.kit.generation) or not event.get("event_seq") is int or int(event.event_seq) <= 0:
		_rejected += 1
		return
	if _generation != int(event.generation):
		_clear_history()
		_generation = int(event.generation)
	if int(event.event_seq) <= _sequence:
		_rejected += 1
		return
	_sequence = int(event.event_seq)
	if event.get("kind") == "reset":
		_clear_visuals()
		_seen.clear(); _seen_order.clear()
		return
	if event.get("kind") != "impact" or not event.get("receipts") is Array or not _number(event.get("time_s")) or not event.get("cast_id") is int or int(event.cast_id) < 1: return
	var now := float(runtime.kit.elapsed)
	if absf(float(event.time_s) - now) > .050001:
		_rejected += 1
		return
	var cast_key := "%d:%d" % [_generation, int(event.cast_id)]
	for value: Variant in event.receipts:
		if not value is Dictionary or value.get("kind") != "damage" or not value.get("unit_id") is int or int(value.unit_id) < 1: continue
		if not _number(value.get("damage_applied")) or float(value.damage_applied) <= 0: continue
		if not _number(value.get("health_before")) or not _number(value.get("health_after")): continue
		var before := float(value.health_before)
		var after := float(value.health_after)
		if not _number(value.get("shield_before", 0)) or not _number(value.get("shield_after", 0)): continue
		var shield_before := float(value.get("shield_before", 0))
		var shield_after := float(value.get("shield_after", 0))
		if after > before or shield_after > shield_before: continue
		var applied := before - after + shield_before - shield_after
		if applied <= 0 or not is_equal_approx(applied, float(value.damage_applied)): continue
		var key := "%s:%d:%d" % [cast_key, int(event.get("projectile_index", -1)), int(value.unit_id)]
		if _seen.has(key): continue
		_seen[key] = true; _seen_order.append(key)
		while _seen_order.size() > RECEIPT_CAP: _seen.erase(_seen_order.pop_front())
		if _cast_key != cast_key or now > _until:
			_damage = 0; _defeats = 0; _targets.clear(); _shield_only = true
			_cast_key = cast_key
		_damage += applied
		_targets[int(value.unit_id)] = true
		if before > 0 and after <= 0: _defeats += 1
		_shield_only = _shield_only and is_equal_approx(before, after)
		_until = now + HOLD_SECONDS
		_confirmed_events += 1
	_refresh_display()

func consume_damage(receipt: Dictionary) -> void:
	if not _usable():
		_clear_visuals()
		return
	if not receipt.get("accepted", false) or not receipt.get("generation") is int or int(receipt.generation) != int(runtime.vitals.generation): return
	if _vitals_generation != int(receipt.generation):
		_vitals_generation = int(receipt.generation)
		_damage_serial = -1
	var serial := int(runtime.vitals.damage_receipts)
	if serial <= _damage_serial: return
	for field in ["health_before", "health_after", "shield_before", "shield_after", "damage_applied", "time_s"]:
		if not _number(receipt.get(field)): return
	var health_loss := float(receipt.health_before) - float(receipt.health_after)
	var shield_loss := float(receipt.shield_before) - float(receipt.shield_after)
	if health_loss < 0 or shield_loss < 0 or health_loss + shield_loss <= 0 or not is_equal_approx(health_loss + shield_loss, float(receipt.damage_applied)): return
	_damage_serial = serial
	_last_incoming = {"health":health_loss, "shield":shield_loss}
	_hurt_until = float(runtime.vitals.elapsed) + HOLD_SECONDS
	_refresh_display()

func _process(_delta: float) -> void:
	if not _usable():
		_clear_visuals()
		return
	_refresh_display()

func _refresh_display() -> void:
	if not is_instance_valid(hit_text) or not _usable(): return
	var outgoing := _damage > 0 and float(runtime.kit.elapsed) <= _until
	var incoming := not _last_incoming.is_empty() and float(runtime.vitals.elapsed) <= _hurt_until
	badge.visible = outgoing
	hurt_panel.visible = incoming
	if outgoing:
		var result := "%.0f DAMAGE · %d %s" % [_damage, _targets.size(), "TARGET" if _targets.size() == 1 else "TARGETS"]
		if _defeats > 0: result += " · %d %s" % [_defeats, "TARGET DOWN" if _defeats == 1 else "TARGETS DOWN"]
		hit_text.text = result
		hit_text.add_theme_color_override("font_color", UI.MOON if _shield_only else UI.CREAM)
	if incoming:
		var losses: Array[String] = []
		if _last_incoming.health > 0: losses.append("−%.0f HEALTH" % _last_incoming.health)
		if _last_incoming.shield > 0: losses.append("−%.0f SHIELD" % _last_incoming.shield)
		hurt_text.text = "  ·  ".join(losses)
	visible = outgoing or incoming
	_layout_overlay()
	queue_redraw()

func _layout_overlay() -> void:
	if not is_instance_valid(badge) or not is_instance_valid(get_parent_control()): return
	var viewport := get_viewport_rect().size
	var font := hit_text.get_theme_font("font")
	var text_width := font.get_string_size(hit_text.text, HORIZONTAL_ALIGNMENT_LEFT, -1, hit_text.get_theme_font_size("font_size")).x + UI.SPACE_LG
	var width := minf(maxf(260, text_width), maxf(1, viewport.x - UI.SPACE_LG * 2))
	size = Vector2(width, 88 if badge.visible and hurt_panel.visible else 66)
	var top := Vector2((viewport.x - width) * .5, viewport.y * .5 - 14)
	var limit := minf(viewport.y - UI.SPACE_SM, get_parent_control().get_global_rect().position.y - UI.SPACE_SM)
	_layout_suppressed = top.y < UI.SPACE_SM or top.y + size.y > limit
	if _layout_suppressed:
		hide()
		return
	position = top - get_parent_control().global_position
	badge.position = Vector2(0, 38)
	badge.size = Vector2(width, 28)
	hit_text.clip_text = true
	hit_text.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	hurt_panel.position = Vector2(0, 64 if badge.visible else 38)
	hurt_panel.size = Vector2(width, 24)

func _draw() -> void:
	if not badge or not badge.visible or _layout_suppressed: return
	var center := Vector2(size.x * .5, 14)
	var color := UI.GOLD if _defeats == 0 else UI.CREAM
	if _shield_only: color = UI.MOON
	for signs in [Vector2(-1,-1),Vector2(1,-1),Vector2(-1,1),Vector2(1,1)]:
		draw_line(center + signs * 6, center + signs * 11, color, 2, true)

func report() -> Dictionary:
	return {"visible":visible,"rect":get_global_rect(),"layout_suppressed":_layout_suppressed,"damage":_damage,"targets":_targets.size(),"defeats":_defeats,"shield_only":_shield_only,"hit_text":hit_text.text if hit_text else "","hurt_text":hurt_text.text if hurt_text else "","cached_receipts":_seen.size(),"cache_capacity":RECEIPT_CAP,"confirmed_events":_confirmed_events,"rejected":_rejected,"authority":"Read-only actual impact/vitals receipts; no begin/release hit inference."}
