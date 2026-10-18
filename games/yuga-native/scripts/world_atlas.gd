extends Control
## Fixed-orientation tactical map using the live world manifest and simulation.
const HeroUI = preload("res://scripts/hero_ui_theme.gd")
const ROUTE_COLOR := Color("9e936f")
const BLOCKER_COLOR := Color("394c59")
const DECK_FILL := Color("243b47")
const DECK_EDGE := Color("799fb4")

var data: Dictionary = {}
var hero_position := Vector3.ZERO
var hero_forward := Vector3.FORWARD
var _map_font: Font = HeroUI.text_font()
var _panel_style: StyleBoxFlat
var units: Array = []
var relays: Array = []
var footer_height := 70.0
func _plot_rect() -> Rect2:
	return Rect2(Vector2(12,16),Vector2(maxf(1,size.x-24),maxf(1,size.y-32-footer_height)))

func project(point: Vector3) -> Vector2:
	var bounds: Array=data.get("bounds",{}).get("nominal_xz",[-70,70,-130,130])
	var plot := _plot_rect()
	return plot.position+Vector2((point.x-bounds[0])/(bounds[1]-bounds[0])*plot.size.x,(point.z-bounds[2])/(bounds[3]-bounds[2])*plot.size.y)

func _footprint(entry: Dictionary) -> Rect2:
	var center := Vector3(entry.position[0],0,entry.position[2])
	var half := Vector3(entry.size[0]*.5,0,entry.size[2]*.5)
	return Rect2(project(center-half),project(center+half)-project(center-half))

func _native_deck_footprints() -> Array[Dictionary]:
	var result: Array[Dictionary] = []
	# These are the same native-only decks constructed by the world, not a
	# new collider set or a claim about the separate browser authority.
	for deck in data.get("traversal",{}).get("native_collision_boxes",[]):
		result.append({"id":deck.id,"rect":_footprint(deck)})
	return result

func _core_caption_rect(objective: Dictionary) -> Rect2:
	var point := project(Vector3(objective.position[0],0,objective.position[2]))
	var caption := String(objective.team).capitalize()
	var extent := _map_font.get_string_size(caption,HORIZONTAL_ALIGNMENT_LEFT,-1,HeroUI.TYPE_HUD_DETAIL)
	# Keep the actual core and player positions truthful. Put the caption to
	# the side so spawn/heading markers cannot erase its letters.
	var x := point.x+16.0
	if x+extent.x > size.x-6: x=point.x-16.0-extent.x
	var plot := _plot_rect()
	return Rect2(Vector2(clampf(x,6,maxf(6,size.x-extent.x-6)),clampf(point.y-extent.y*.5,plot.position.y,maxf(plot.position.y,plot.end.y-extent.y))),extent)

func project_heading(direction: Vector3) -> Vector2:
	if not direction.is_finite(): return Vector2.ZERO
	# Project the direction directly: subtracting two map positions loses
	# precision and makes the heading depend on the marker location.
	var bounds: Array=data.get("bounds",{}).get("nominal_xz",[-70,70,-130,130])
	var plot := _plot_rect()
	var projected := Vector2(direction.x/(bounds[1]-bounds[0])*plot.size.x, direction.z/(bounds[3]-bounds[2])*plot.size.y)
	return projected.normalized() if projected.is_finite() and not projected.is_zero_approx() else Vector2.ZERO

func _draw() -> void:
	draw_style_box(_background(),Rect2(Vector2.ZERO,size))
	if data.is_empty(): return
	for solid in data.authority_collision_boxes:
		draw_rect(_footprint(solid),BLOCKER_COLOR)
	for deck in _native_deck_footprints():
		var footprint: Rect2 = deck.rect
		draw_rect(footprint,DECK_FILL)
		draw_rect(footprint,DECK_EDGE,false,1,true)
		# An inset crossbar distinguishes a landing deck without relying on hue.
		draw_line(footprint.position+Vector2(1,1),Vector2(footprint.end.x-1,footprint.position.y+1),DECK_EDGE,1,true)
	for lane in data.lanes:
		for i in range(lane.points.size()-1):
			var a: Array=lane.points[i]
			var b: Array=lane.points[i+1]
			draw_line(project(Vector3(a[0],0,a[2])),project(Vector3(b[0],0,b[2])),ROUTE_COLOR,1.5,true)
	for camp in data.camps:
		draw_circle(project(Vector3(camp.position[0],0,camp.position[2])),3,HeroUI.MARSH)
	for objective in data.objectives:
		var point := project(Vector3(objective.position[0],0,objective.position[2]))
		var team_color: Color = HeroUI.SUN if objective.team=="sun" else HeroUI.MOON
		if objective.kind == "core": draw_circle(point,9,team_color,false,1.5,true)
		draw_circle(point,3,team_color)
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
		var caption: String = String(objective.team).capitalize()
		var caption_rect := _core_caption_rect(objective)
		draw_string(_map_font,caption_rect.position+Vector2(0,_map_font.get_ascent(HeroUI.TYPE_HUD_DETAIL)),caption,HORIZONTAL_ALIGNMENT_LEFT,-1,HeroUI.TYPE_HUD_DETAIL,HeroUI.CREAM)
	var here := project(hero_position)
	var heading := project_heading(hero_forward)
	if heading.is_finite() and not heading.is_zero_approx():
		var side := Vector2(-heading.y, heading.x)
		draw_colored_polygon(PackedVector2Array([here+heading*13,here+heading*7+side*4,here+heading*7-side*4]),HeroUI.CREAM)
	draw_circle(project(hero_position),5,Color.WHITE)
	draw_circle(project(hero_position),8,Color(1,1,1,.4),false,1,true)
func _background() -> StyleBoxFlat:
	if _panel_style == null: _panel_style=HeroUI.hud_panel_style(&"quiet",0)
	return _panel_style
