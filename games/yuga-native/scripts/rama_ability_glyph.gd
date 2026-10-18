extends TextureRect
## Original, static line emblems shared by the HUD and read-only ability guide.
## These are recognition aids; the adjacent key, name and state remain explicit.
const UI = preload("res://scripts/hero_ui_theme.gd")
const SIZE := 20
const GUIDE_SIZE := 22
const MARKS := {
	"kodanda": '<path d="M9 4 Q25 16 9 28 M9 4 L13 16 9 28 M4 16 H29 M24 12 L29 16 24 20"/>',
	"piercing_dawn": '<path d="M3 16 H29 M23 10 L29 16 23 22 M9 10 L15 16 9 22 3 16 Z M17 5 V8 M17 24 V27"/>',
	"measured_step": '<path d="M4 24 L13 15 18 20 9 29 Z M14 12 L23 3 28 8 19 17 Z M3 12 H8 M6 7 H11 M22 25 H29"/>',
	"guardian_circle": '<path d="M16 3 L27 8 V17 Q25 25 16 29 Q7 25 5 17 V8 Z M10 16 L16 10 22 16 16 22 Z M16 7 V10"/>',
	"dawn_volley": '<path d="M16 29 V3 M12 8 L16 3 20 8 M12 27 L4 8 M3 14 L4 8 10 10 M20 27 L28 8 M22 10 L28 8 29 14"/>'
}
static var _textures: Dictionary = {}
var ability_id := ""
var state: StringName = &"unavailable"

func _init() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	focus_mode = Control.FOCUS_NONE
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	custom_minimum_size = Vector2(SIZE, SIZE)

static func texture_for(id: String) -> Texture2D:
	if not MARKS.has(id): return null
	if not _textures.has(id):
		var source := '<svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 32 32"><g fill="none" stroke="#ffffff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round">%s</g></svg>' % MARKS[id]
		var bitmap := Image.new()
		if bitmap.load_svg_from_string(source, 2.0) != OK: return null
		_textures[id] = ImageTexture.create_from_image(bitmap)
	return _textures[id]

static func color_for(value: StringName) -> Color:
	match value:
		&"ready", &"selected": return UI.GOLD
		&"cooling": return UI.MOON
		_: return UI.MUTED

func present(id: String, value: StringName) -> void:
	if ability_id != id:
		ability_id = id
		texture = texture_for(id)
	if state != value:
		state = value
	self_modulate = color_for(value)
