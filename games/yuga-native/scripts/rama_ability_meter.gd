extends Control
## Read-only timing marks. Three marks during Dawn Volley are firing lanes,
## never charge stacks or hit confirmations. The HUD supplies authority state.
const UI = preload("res://scripts/hero_ui_theme.gd")
var ability_id := ""
var mode: StringName = &"unavailable"
var fraction := 0.0
var accent := UI.GOLD
var lanes: Array[bool] = []

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)

func present(id: String, value: Dictionary) -> void:
	ability_id = id
	mode = value.get("mode", &"unavailable")
	fraction = clampf(float(value.get("fraction", 0.0)), 0, 1)
	accent = value.get("accent", UI.GOLD)
	lanes.assign(value.get("lanes", []))
	queue_redraw()

func _draw() -> void:
	if size.x < 4 or size.y < 4: return
	var track := Rect2(0, size.y - 3, size.x, 3)
	draw_rect(track, UI.HUD_EDGE)
	if mode == &"unavailable": return
	var color := accent if mode in [&"windup", &"recovery", &"ready"] else UI.MOON
	if mode == &"blocked": color = UI.MUTED
	if fraction > 0:
		draw_rect(Rect2(track.position, Vector2(size.x * fraction, 3)), color)
	# During a committed volley, outlined = pending; solid = launched by the
	# actual release event and its per-projectile delay. All stay in this card.
	if ability_id == "dawn_volley" and lanes.size() == 3:
		var gap := 4.0
		var width := minf(24.0, (size.x - gap * 2) / 3)
		var left := (size.x - width * 3 - gap * 2) * .5
		for index in 3:
			var mark := Rect2(left + index * (width + gap), 0, width, 3)
			if lanes[index]: draw_rect(mark, accent)
			else: draw_rect(mark, accent, false, 1.0)

func report() -> Dictionary:
	return {"ability_id":ability_id,"mode":mode,"fraction":fraction,"lanes":lanes.duplicate()}
