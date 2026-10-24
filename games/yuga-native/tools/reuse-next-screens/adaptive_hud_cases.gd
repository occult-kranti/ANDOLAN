extends "res://tests/desktop_s3_hud_readability_cases.gd"
## Actual authority/remap states from S3; both desktop base canvases, no pixels.

func label_fits(label: Label, card: Control) -> bool:
	var needed := label.get_theme_font("font").get_multiline_string_size(label.text,HORIZONTAL_ALIGNMENT_LEFT,label.size.x,label.get_theme_font_size("font_size"))
	return card.get_global_rect().encloses(label.get_global_rect()) and needed.y <= label.size.y+1

func inspect_layout(state_name: String) -> void:
	var hud: Control = scene.rama_hud
	var authority: Dictionary = scene.rama_runtime.kit.report()
	var army_clock: float = scene.army.elapsed
	for base in [Vector2i(1280,720),Vector2i(960,540)]:
		for scale_ in [1.0,1.5,2.0]:
			root.size=Vector2i(960,540)
			root.content_scale_size=base
			root.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
			root.content_scale_factor=scale_
			await frames(8)
			scene._update_practice_hud()
			await frames(8)
			var viewport := root.get_visible_rect()
			var issues: Array[String] = []
			var drawn: Rect2 = hud.status_panel.get_global_rect()
			if not viewport.encloses(drawn): issues.append("status outside viewport")
			for index in hud.slots.size():
				var slot: Label = hud.slots[index]
				var card: Control = hud.slot_cards[index]
				drawn=drawn.merge(card.get_global_rect())
				if not viewport.encloses(card.get_global_rect()): issues.append("card outside "+str(index))
				if not card.get_global_rect().encloses(slot.get_global_rect()): issues.append("label outside card "+str(index))
				if not slot.get_global_rect().encloses(hud.slot_glyphs[index].get_global_rect()): issues.append("glyph outside "+str(index))
				for line in slot.text.split("\n"):
					if slot.get_theme_font("font").get_string_size(line,HORIZONTAL_ALIGNMENT_LEFT,-1,slot.get_theme_font_size("font_size")).x > slot.size.x+.5: issues.append("clipped slot "+line)
				if slot.get_theme_font_size("font_size") != 16: issues.append("slot text size changed")
				if not slot.text.contains(Bindings.label(hud.ACTIONS[index])): issues.append("actual key missing")
			if not viewport.encloses(hud.life_text.get_global_rect()): issues.append("health outside")
			if not hud.get_global_rect().encloses(drawn): issues.append("drawn slab outside HUD bounds")
			var slab_limit := 102.1 if viewport.size.x<560 and state_name=="recovering/queued" else 82.1
			if hud._compact_slots and drawn.size.y > slab_limit: issues.append("compact drawn slab exceeds readable-state footprint budget")
			if not label_fits(hud.note,hud.status_panel): issues.append("combat notice outside")
			for word in hud.note.text.split(" "):
				if hud.note.get_theme_font("font").get_string_size(word,HORIZONTAL_ALIGNMENT_LEFT,-1,hud.note.get_theme_font_size("font_size")).x > hud.note.size.x+.5: issues.append("combat notice word clipped: "+word)
			if scene._constrained_world:
				for row in scene.compact_world_labels:
					if not label_fits(row,scene.compact_world_card): issues.append("summary clipped: "+row.text)
				if not viewport.encloses(scene.map_control.get_global_rect()): issues.append("map outside")
				var summary_rows:Array=scene.compact_world_labels
				var inner_width:float=scene.compact_world_card.size.x-16
				var stacked_budget:float=22
				for row in summary_rows: stacked_budget+=scene._compact_text_height(row,inner_width)
				if scene.compact_world_card.size.y>stacked_budget+.5: issues.append("split summary taller than full-width stack")
				if scene.map_control._plot_rect().size.y<63.9: issues.append("live map plot compressed below readable minimum")
				var plot:Rect2=scene.map_control._plot_rect()
				if plot.size.x<119.9: issues.append("live map plot below readable width")
				# Measure the actual visible combat edge, independently of the
				# world's anchor offsets. Keep the 64px tiny-canvas fallback, but
				# demand the full 100px plot when its padding/footer fit above it.
				var available_plot_height:float=hud.get_global_rect().position.y-scene.map_control.get_global_rect().position.y-12-32-scene.map_control.footer_height
				if available_plot_height>=100 and plot.size.y<99.9: issues.append("live map plot wastes available readable height")
				var core_rects := []
				for objective in scene.manifest.objectives:
					if objective.kind=="core":
						var caption:Rect2=scene.map_control._core_caption_rect(objective)
						core_rects.append(caption)
						if not Rect2(Vector2.ZERO,scene.map_control.size).encloses(caption): issues.append("core caption outside live map")
				if core_rects.size()!=2 or core_rects[0].intersects(core_rects[1]): issues.append("Sun/Moon captions collide")
			var detail := {"issues":issues,"base":[base.x,base.y],"physical":[960,540],"scale":scale_,"logical":str(viewport.size),"drawn_slab":str(drawn),"drawn_slab_physical_height":drawn.size.y*540/viewport.size.y,"note":hud.note.text,"health":hud.life_text.text,"slots":hud.slots.map(func(s):return s.text),"summary":str(scene.compact_world_card.get_global_rect()),"summary_rows":scene.compact_world_labels.map(func(row):return row.text),"map":str(scene.map_control.get_global_rect())}
			check(state_name+" base "+str(base)+" scale "+str(scale_)+" preserves readable live cues and measured footprint",issues.is_empty(),detail)
	check(state_name+" layout leaves actual authority clocks exact",authority==scene.rama_runtime.kit.report() and army_clock==scene.army.elapsed)
