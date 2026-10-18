extends "res://tests/desktop_s3_hud_readability_cases.gd"
## Real remaps/states from S3, plus compact keys/glyphs/state and torso clearance.
func inspect_layout(state_name: String) -> void:
	await super.inspect_layout(state_name)
	var hud: Control=scene.rama_hud
	var issues: Array[String]=[]
	var row_y: float=hud.slot_cards[0].global_position.y
	for index in hud.slots.size():
		var slot: Label=hud.slots[index]
		var glyph: Control=hud.slot_glyphs[index]
		var key: String=Bindings.label(hud.ACTIONS[index])
		if not slot.text.split("\n")[0].ends_with(key):issues.append("actual key missing: "+key)
		if not slot.get_global_rect().encloses(glyph.get_global_rect()):issues.append("glyph outside: "+str(index))
		if not is_equal_approx(hud.slot_cards[index].global_position.y,row_y):issues.append("slot wrapped")
		if not hud.slot_cards[index].tooltip_text.contains(key) or hud.slot_cards[index].tooltip_text.split("·").size()<3:issues.append("full-name tooltip missing")
	var note: Label=hud.note
	if note.get_theme_font("font").get_string_size(note.text,HORIZONTAL_ALIGNMENT_LEFT,-1,note.get_theme_font_size("font_size")).x>note.size.x+.5:issues.append("action/status clipped: "+note.text)
	if not hud.get_global_rect().encloses(hud.status_panel.get_global_rect()):issues.append("status outside")
	if hud.size.y>100.1:issues.append("compact height grew")
	var camera: Camera3D=scene.player.camera
	var torso:=Rect2();var first:=true
	for height in [.75,1.80]:
		for side in [-.32,.32]:
			var point:=camera.unproject_position(scene.player.global_position+Vector3.UP*height+camera.global_basis.x*side)
			if first:torso=Rect2(point,Vector2.ZERO);first=false
			else:torso=torso.expand(point)
	if hud.get_global_rect().intersects(torso):issues.append("combat HUD covers neutral torso")
	check(state_name+" compact single row retains keys glyphs full action status and neutral torso",issues.is_empty(),{"issues":issues,"hud":str(hud.get_global_rect()),"torso":str(torso),"note":note.text,"note_width":note.size.x,"status":str(hud.status_panel.get_global_rect()),"card":str(hud.slot_cards[0].get_global_rect()),"status_min":str(hud.status_panel.get_combined_minimum_size())})
