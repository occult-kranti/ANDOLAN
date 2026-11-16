extends VBoxContainer
## Read-only terminal summary. The army owns the winner, clocks and core health.
const UI = preload("res://scripts/hero_ui_theme.gd")
var heading: Label
var detail: Label
var chart: CoreChart
var chart_caption: Label

class CoreChart extends Control:
	var samples: Array = []
	func _ready() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		custom_minimum_size = Vector2(260, 92)
		resized.connect(queue_redraw)
	func _draw() -> void:
		if samples.size() < 2: return
		var area := Rect2(Vector2(6, 5), Vector2(maxf(1, size.x - 12), maxf(1, size.y - 10)))
		draw_rect(area, Color("142039"))
		for ratio in [0.0, 0.5, 1.0]:
			var y: float = area.end.y - area.size.y * ratio
			draw_line(Vector2(area.position.x, y), Vector2(area.end.x, y), Color("42506a"), 1)
		var start := float(samples[0].time_s)
		var duration := maxf(.001, float(samples[-1].time_s) - start)
		for team in ["sun", "moon"]:
			var points := PackedVector2Array()
			for sample in samples:
				points.append(Vector2(area.position.x + (float(sample.time_s) - start) / duration * area.size.x, area.end.y - clampf(float(sample[team]) / 100.0, 0, 1) * area.size.y))
			draw_polyline(points, Color("e2bb70") if team == "sun" else Color("92bcf0"), 2.0, true)

func _ready() -> void:
	name = "RoundOutcome"
	add_theme_constant_override("separation", UI.SPACE_XS)
	heading = UI.label("", UI.TYPE_SECTION, UI.GOLD)
	heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(heading)
	detail = UI.label("", UI.TYPE_CAPTION, UI.CREAM)
	detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(detail)
	chart_caption = UI.label("", UI.TYPE_CAPTION, UI.MIST)
	chart_caption.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(chart_caption)
	chart = CoreChart.new()
	chart.name = "CorePressureChart"
	add_child(chart)
	hide()

static func headline(winner: String) -> String:
	return "Draw · both cores destroyed" if winner == "draw" else "%s core victory" % winner.capitalize()

func present(battle: Dictionary, metrics: Dictionary = {}) -> void:
	var winner: String = battle.get("winner", "")
	visible = winner in ["sun", "moon", "draw"]
	if not visible: return
	heading.text = headline(winner)
	var cores: Dictionary = battle.get("cores", {})
	detail.text = "Final cores · Sun %d / Moon %d\nLane simulation and relay supplies have stopped.\nRestart lane practice below to begin a new round." % [cores.get("sun", 0), cores.get("moon", 0)]
	chart.hide()
	chart_caption.hide()
	if metrics.get("completed", false) and metrics.get("winner", "") == winner:
		var elapsed := maxf(0, float(metrics.get("elapsed", 0)))
		var hero: Dictionary = metrics.get("hero", {})
		detail.text = "Rama · offline lane practice · %d:%02d\n%d lane last hits · %d gold earned\nFinal cores · Sun %d / Moon %d" % [int(elapsed) / 60, int(elapsed) % 60, metrics.get("kills", 0), metrics.get("gold", 0), cores.get("sun", 0), cores.get("moon", 0)]
		if not hero.is_empty():
			detail.text += "\nObserved Rama · %d releases · %.0f damage dealt · %.0f taken · %d defeats" % [hero.get("releases", 0), hero.get("damage_dealt", 0), hero.get("damage_taken", 0), hero.get("deaths", 0)]
		detail.text += "\nLane simulation and relay supplies have stopped.\nRestart lane practice below to begin a new round."
		var samples: Variant = metrics.get("core_timeline", [])
		if samples is Array and samples.size() >= 2:
			chart.samples = samples.duplicate(true)
			chart.queue_redraw()
			chart.show()
			chart_caption.text = "Core health over army time · Sun gold / Moon blue\n%.0fs–%.0fs · 100%% at top, 0%% at bottom" % [float(samples[0].time_s), float(samples[-1].time_s)]
			chart_caption.show()
