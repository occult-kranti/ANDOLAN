extends Control
## Fixed-orientation tactical map using the live world manifest and simulation.
const HeroUI = preload("res://scripts/hero_ui_theme.gd")

var data: Dictionary = {}
var hero_position := Vector3.ZERO
var hero_forward := Vector3.FORWARD
var _map_font: Font = HeroUI.text_font()
var units: Array = []
var relays: Array = []
var footer_height := 70.0
func project(point: Vector3) -> Vector2:
	var bounds: Array=data.get("bounds",{}).get("nominal_xz",[-70,70,-130,130])
	return Vector2(12+(point.x-bounds[0])/(bounds[1]-bounds[0])*(size.x-24),26+(point.z-bounds[2])/(bounds[3]-bounds[2])*(size.y-52-footer_height))
func project_heading(direction: Vector3) -> Vector2:
	if not direction.is_finite(): return Vector2.ZERO
	# Use the same anisotropic map projection as roads and objective positions.
	var projected := project(hero_position + direction) - project(hero_position)
	return projected.normalized() if projected.is_finite() and not projected.is_zero_approx() else Vector2.ZERO

func _draw() -> void:
	draw_style_box(_background(),Rect2(Vector2.ZERO,size))
	if data.is_empty(): return
	for solid in data.authority_collision_boxes:
		var p:=Vector3(solid.position[0],0,solid.position[2])
		var half:=Vector3(solid.size[0]/2,0,solid.size[2]/2)
		draw_rect(Rect2(project(p-half),project(p+half)-project(p-half)),Color("52676d"))
	for lane in data.lanes:
		for i in range(lane.points.size()-1):
			var a: Array=lane.points[i]
			var b: Array=lane.points[i+1]
			draw_line(project(Vector3(a[0],0,a[2])),project(Vector3(b[0],0,b[2])),HeroUI.GOLD,2,true)
	for camp in data.camps:
		draw_circle(project(Vector3(camp.position[0],0,camp.position[2])),3,HeroUI.MARSH)
	for objective in data.objectives:
		draw_circle(project(Vector3(objective.position[0],0,objective.position[2])),3,HeroUI.SUN if objective.team=="sun" else HeroUI.MOON)
	for anchor in data.get("traversal",{}).get("anchors",[]):
		var p:=project(Vector3(anchor.position[0],0,anchor.position[2]))
		draw_polyline(PackedVector2Array([p+Vector2(0,-3),p+Vector2(3,0),p+Vector2(0,3),p+Vector2(-3,0),p+Vector2(0,-3)]),HeroUI.GOLD,1,true)
	for unit in units:
		var p:=project(unit.position)
		if unit.get("role","") in ["cannon_cart","royal_chariot"]:
			draw_circle(p,5.5,HeroUI.SUN if unit.team=="sun" else HeroUI.MOON,false,1.5,true)
		if unit.team=="sun": draw_colored_polygon(PackedVector2Array([p+Vector2(0,-2.5),p+Vector2(2,2),p+Vector2(-2,2)]),HeroUI.SUN)
		else: draw_rect(Rect2(p-Vector2(1.7,1.7),Vector2(3.4,3.4)),HeroUI.MOON)
	for relay in relays:
		var p:=project(relay.position)
		var color:=HeroUI.SUN if relay.owner=="sun" else (HeroUI.MOON if relay.owner=="moon" else HeroUI.MIST)
		draw_rect(Rect2(p-Vector2(5,5),Vector2(10,10)),Color("14242d"))
		draw_rect(Rect2(p-Vector2(5,5),Vector2(10,10)),color,false,2)
		if relay.owner=="sun": draw_colored_polygon(PackedVector2Array([p+Vector2(0,-3),p+Vector2(3,2),p+Vector2(-3,2)]),color)
		elif relay.owner=="moon": draw_rect(Rect2(p-Vector2(2,2),Vector2(4,4)),color)
		if relay.contested:
			draw_line(p-Vector2(7,7),p+Vector2(7,7),Color.WHITE,2,true)
			draw_line(p+Vector2(-7,7),p+Vector2(7,-7),Color.WHITE,2,true)
	# Core labels use actual objective positions, so map orientation cannot
	# silently disagree with the army's Sun/Moon ownership.
	for objective in data.objectives:
		if objective.kind != "core": continue
		var position_ := project(Vector3(objective.position[0],0,objective.position[2]))
		var caption: String = String(objective.team).capitalize()
		var text_width := _map_font.get_string_size(caption, HORIZONTAL_ALIGNMENT_LEFT, -1, HeroUI.TYPE_HUD_DETAIL).x
		var baseline := position_.y - 8 if objective.team == "sun" else position_.y + 19
		draw_string(_map_font, Vector2(clampf(position_.x - text_width/2, 6, size.x-text_width-6),baseline),caption,HORIZONTAL_ALIGNMENT_LEFT,-1,HeroUI.TYPE_HUD_DETAIL,HeroUI.CREAM)
	var here := project(hero_position)
	var heading := project_heading(hero_forward)
	if heading.is_finite() and not heading.is_zero_approx():
		var side := Vector2(-heading.y, heading.x)
		draw_colored_polygon(PackedVector2Array([here+heading*13,here+heading*7+side*4,here+heading*7-side*4]),HeroUI.CREAM)
	draw_circle(project(hero_position),5,Color.WHITE)
	draw_circle(project(hero_position),8,Color(1,1,1,.4),false,1,true)
func _background() -> StyleBoxFlat:
	return HeroUI.hud_panel_style(&"quiet", 0)
