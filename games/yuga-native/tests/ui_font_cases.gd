extends SceneTree
## The portable interface must not rely on fonts installed on the host.
const UI = preload("res://scripts/hero_ui_theme.gd")
func _initialize() -> void:
	var checks: Array = []
	for role in ["body", "display"]:
		var font: Font = UI.text_font() if role == "body" else UI.display_font()
		var missing := ""
		for symbol in "YUGA Rama’s abilities ▲■◇●◎□×—·→…0123456789":
			if not font.has_char(symbol.unicode_at(0)): missing += symbol
		checks.append({"name": role + " text and tactical symbols are bundled", "passed":missing.is_empty(), "missing":missing})
		checks.append({"name": role + " avoids host font dependency", "passed":not font.allow_system_fallback and font.fallbacks.size() == 1 and font.fallbacks.all(func(fallback): return not fallback.allow_system_fallback and fallback.resource_path.begins_with("res://assets/fonts/"))})
	checks.append({"name":"body line metrics stay compact", "passed":UI.text_font().get_height(17) <= 25.0, "height":UI.text_font().get_height(17)})
	checks.append({"name":"caption line metrics stay compact", "passed":UI.text_font().get_height(11) <= 17.0, "height":UI.text_font().get_height(11)})
	checks.append({"name":"font resources shared across panels", "passed":UI.text_font() == UI.text_font() and UI.display_font() == UI.display_font()})
	var passed: bool = checks.all(func(item): return item.passed)
	var result := {"passed":passed,"checks":checks,"scope":"Bundled font resource and glyph coverage; no rendered layout acceptance"}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE)
			file.store_string(JSON.stringify(result, "  ")+"\n")
	print(JSON.stringify(result))
	quit(0 if passed else 1)
