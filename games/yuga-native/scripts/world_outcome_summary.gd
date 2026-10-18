extends VBoxContainer
## Read-only terminal summary. The army owns the winner, clocks and core health.
const UI = preload("res://scripts/hero_ui_theme.gd")
var heading: Label
var detail: Label

func _ready() -> void:
	name = "RoundOutcome"
	add_theme_constant_override("separation", UI.SPACE_XS)
	heading = UI.label("", UI.TYPE_SECTION, UI.GOLD)
	heading.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(heading)
	detail = UI.label("", UI.TYPE_CAPTION, UI.CREAM)
	detail.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	add_child(detail)
	hide()

static func headline(winner: String) -> String:
	return "Draw · both cores destroyed" if winner == "draw" else "%s core victory" % winner.capitalize()

func present(battle: Dictionary) -> void:
	var winner: String = battle.get("winner", "")
	visible = winner in ["sun", "moon", "draw"]
	if not visible: return
	heading.text = headline(winner)
	var cores: Dictionary = battle.get("cores", {})
	detail.text = "Final cores · Sun %d / Moon %d\nLane simulation and relay supplies have stopped.\nRestart lane practice below to begin a new round." % [cores.get("sun", 0), cores.get("moon", 0)]
