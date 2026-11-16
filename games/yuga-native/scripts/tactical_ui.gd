extends CanvasLayer
const T = preload("res://scripts/tactical_theme.gd")
const Frontend = preload("res://scripts/tactical_frontend.gd")
var host: Node
var view: Dictionary = {}
var canvas: Control
var hud: Control
var score: Label
var clock_label: Label
var round_label: Label
var callout_label: Label
var phase_label: Label
var health_label: Label
var armor_label: Label
var ammo_label: Label
var weapon_label: Label
var hint_label: Label
var feed_label: Label
var ability_labels: Array[Label] = []
var ability_icons: Array[TextureRect] = []
var ult_pips: Label
var objective: ProgressBar
var objective_label: Label
var outcome: VBoxContainer
var outcome_title: Label
var outcome_reason: Label
var outcome_panel: PanelContainer
var crosshair: AimReticle
var minimap: TacticalMapView
var damage_border: Panel
var modal := ""
var modal_layer: Control
var modal_panel: PanelContainer
var modal_body: VBoxContainer
var modal_heading: Label
var shop_credit: Label
var shop_status: Label
var shop_entries := {}
var settings_controls := {}
var settings_status: Label
var scoreboard_layer: Control
var scoreboard_panel: PanelContainer
var scoreboard_rows := {}
var scoreboard_team_labels := {}
var scoreboard_match_label:Label
var _built := false

class AimReticle extends Control:
	var spread := 4.0
	var hit := false
	func _draw() -> void:
		var center := size*.5
		for direction in [Vector2.LEFT,Vector2.RIGHT,Vector2.UP,Vector2.DOWN]:
			draw_line(center+direction*spread,center+direction*(spread+6),Color(.88,.96,.95),2,true)
		if hit:
			for direction in [Vector2(-1,-1),Vector2(1,-1),Vector2(-1,1),Vector2(1,1)]:draw_line(center+direction*9,center+direction*14,Color("e5bd78"),2,true)

class TacticalMapView extends Control:
	var geometry:Dictionary={}
	var state:Dictionary={}
	var visible_actor_ids:Array[int]=[]
	var bounds:=Rect2(-50,-65,100,130)
	func _ready() -> void:
		var path:="res://assets/tactical/map.json"
		if FileAccess.file_exists(path):
			var data=JSON.parse_string(FileAccess.get_file_as_string(path))
			if data is Dictionary:geometry=data
	func point(at:Vector3)->Vector2:
		var unit:=(Vector2(at.x,at.z)-bounds.position)/bounds.size
		return Vector2(10,10)+Vector2(unit.x,1-unit.y)*(size-Vector2(20,20))
	func refresh(data:Dictionary,local:Dictionary)->void:
		state=data;visible_actor_ids.clear()
		if data.get("map_bounds") is Rect2 and data.map_bounds.size.x>0 and data.map_bounds.size.y>0:bounds=data.map_bounds
		for actor in data.get("actors",[]):
			if actor.get("team","")==local.get("team","") and actor.get("alive",false):visible_actor_ids.append(int(actor.id))
		queue_redraw()
	func ground_shapes()->Array:
		# The map owns physical footprints. Overhead galleries deliberately do
		# not enter this planar view; they leave the passage below usable.
		return geometry.get("buildings",[])+geometry.get("covers",[])+geometry.get("partitions",[])+geometry.get("static_details",[])
	func _draw()->void:
		draw_rect(Rect2(Vector2.ZERO,size),Color(.04,.07,.10,.9))
		draw_rect(Rect2(Vector2(5,5),size-Vector2(10,10)),Color("536472"),false,1)
		for item in ground_shapes():
			var at:=Vector3(item.position[0],0,item.position[2]);var extent:=Vector3(item.size[0],0,item.size[2])*.5
			var a:=point(at+Vector3(-extent.x,0,extent.z));var b:=point(at+Vector3(extent.x,0,-extent.z))
			draw_rect(Rect2(a,b-a),Color("566677"))
		var local_team:="sun"
		for actor in state.get("actors",[]):
			if int(actor.id)==int(state.get("local_id",0)):local_team=String(actor.team)
		var role:="attack" if state.get("attack_team","sun")==local_team else "defend"
		for site in geometry.get("routes",{}).values():
			var paths:Array=site.get(role,[])
			if paths.is_empty():continue
			var route:Array=paths[0]
			for i in range(1,route.size()):draw_line(point(Vector3(route[i-1][0],0,route[i-1][1])),point(Vector3(route[i][0],0,route[i][1])),Color(.52,.73,.72,.24),2,true)
		for id in state.get("sites",{}):
			var at:Vector3=state.sites[id];var center:=point(at)
			draw_circle(center,9,Color("e5bd78"),false,1.5,true)
			draw_string(T.Legacy.text_font(),center+Vector2(-4,4),String(id),HORIZONTAL_ALIGNMENT_LEFT,-1,11,Color("f5efdf"))
		for id in visible_actor_ids:
			var positions:Dictionary=state.get("actor_positions",{})
			if not positions.get(id) is Vector3:continue
			var local:bool=id==int(state.get("local_id",0))
			draw_circle(point(positions[id]),4 if local else 2.5,Color("f5efdf") if local else Color("86d1c6"))

func configure(owner: Node) -> void:
	host=owner
	if _built:return
	_built=true
	layer=20
	canvas=Control.new();canvas.name="TacticalInterface";canvas.mouse_filter=Control.MOUSE_FILTER_IGNORE;canvas.theme=T.create(T.load_settings().ui_scale);add_child(canvas);canvas.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	hud=Control.new();hud.mouse_filter=Control.MOUSE_FILTER_IGNORE;canvas.add_child(hud);hud.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_hud()
	canvas.resized.connect(_layout)
	_layout()

func _box(parent: Control, name_: String, rect: Rect2, color: Color = Color(.04,.07,.10,.88)) -> PanelContainer:
	var panel := PanelContainer.new();panel.name=name_;panel.mouse_filter=Control.MOUSE_FILTER_IGNORE;panel.add_theme_stylebox_override("panel",T.panel(color,10));panel.position=rect.position;panel.size=rect.size;parent.add_child(panel);return panel

func _build_hud() -> void:
	var top := _box(hud,"MatchClock",Rect2(0,0,430,68));var top_column:=T.stack(0);top.add_child(top_column)
	var line:=T.row(24);line.alignment=BoxContainer.ALIGNMENT_CENTER;top_column.add_child(line)
	score=T.label("0  —  0",24,T.IVORY);line.add_child(score)
	clock_label=T.label("00:20",24,T.GOLD);line.add_child(clock_label)
	round_label=T.label("ROUND 1  ·  FIRST TO 13",12,T.MUTED);round_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;top_column.add_child(round_label)
	callout_label=T.label("",16,T.IVORY);hud.add_child(callout_label)
	callout_label.add_theme_color_override("font_outline_color",Color(.015,.025,.04,.95));callout_label.add_theme_constant_override("outline_size",3)
	minimap=TacticalMapView.new();minimap.mouse_filter=Control.MOUSE_FILTER_IGNORE;minimap.size=Vector2(160,180);hud.add_child(minimap)
	phase_label=T.label("",22,T.GOLD);phase_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;hud.add_child(phase_label)
	var health_box:=_box(hud,"Vitals",Rect2(0,0,170,70));var health_column:=T.stack(0);health_box.add_child(health_column)
	health_label=T.label("100",30);health_column.add_child(health_label);armor_label=T.label("KAVACHA  0",12,T.MUTED);health_column.add_child(armor_label)
	var ammo_box:=_box(hud,"Ammunition",Rect2(0,0,180,70));var ammo_column:=T.stack(0);ammo_box.add_child(ammo_column)
	ammo_label=T.label("— / —",28);ammo_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT;ammo_column.add_child(ammo_label)
	weapon_label=T.label("AGNI SIDEARM",12,T.MUTED);weapon_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT;ammo_column.add_child(weapon_label)
	var utility:=_box(hud,"Utility",Rect2(0,0,400,70));var utility_row:=T.row(16);utility_row.alignment=BoxContainer.ALIGNMENT_CENTER;utility.add_child(utility_row)
	for ability in T.ABILITIES:
		var column:=T.stack(0);column.custom_minimum_size.x=70;utility_row.add_child(column)
		var glyph:=T.icon(ability.id,30);column.add_child(glyph);ability_icons.append(glyph);var count:=T.label(ability.key+"  /  0",14,T.IVORY);count.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;column.add_child(count);ability_labels.append(count)
	hint_label=T.label("",14,T.IVORY);hint_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;hud.add_child(hint_label)
	hint_label.add_theme_color_override("font_outline_color",Color(.015,.025,.04,.95));hint_label.add_theme_constant_override("outline_size",3)
	feed_label=T.label("",13,T.MUTED);feed_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT;hud.add_child(feed_label)
	crosshair=AimReticle.new();crosshair.mouse_filter=Control.MOUSE_FILTER_IGNORE;hud.add_child(crosshair);crosshair.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	damage_border=Panel.new();damage_border.mouse_filter=Control.MOUSE_FILTER_IGNORE;var damage_style:=T.panel(Color.TRANSPARENT,0,Color("ef8b83"));damage_style.set_border_width_all(3);damage_border.add_theme_stylebox_override("panel",damage_style);hud.add_child(damage_border);damage_border.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	objective=ProgressBar.new();objective.show_percentage=false;objective.mouse_filter=Control.MOUSE_FILTER_IGNORE;objective.custom_minimum_size=Vector2(240,6);hud.add_child(objective)
	objective_label=T.label("",15,T.IVORY);objective_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;hud.add_child(objective_label)
	outcome_panel=_box(hud,"RoundOutcome",Rect2(0,0,500,108),Color(.04,.07,.10,.95))
	outcome=T.stack(5);outcome.mouse_filter=Control.MOUSE_FILTER_IGNORE;outcome_panel.add_child(outcome)
	outcome_title=T.label("",32,T.GOLD,true);outcome_title.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;outcome.add_child(outcome_title)
	outcome_reason=T.label("",15,T.IVORY);outcome_reason.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;outcome.add_child(outcome_reason)

func _layout() -> void:
	if not _built:return
	var size_:=canvas.size
	var scale_:=T.current_scale;var bottom_height:=70*scale_;var clock_height:=68*scale_
	hud.get_node("MatchClock").position=Vector2((size_.x-430)/2,16);hud.get_node("MatchClock").size=Vector2(430,clock_height)
	minimap.position=Vector2(20,20);callout_label.position=Vector2(20,205)
	phase_label.position=Vector2(200,28+clock_height);phase_label.size=Vector2(maxf(160,size_.x-400),36)
	hud.get_node("Vitals").position=Vector2(24,size_.y-bottom_height-22);hud.get_node("Vitals").size.y=bottom_height
	hud.get_node("Ammunition").position=Vector2(size_.x-204,size_.y-bottom_height-22);hud.get_node("Ammunition").size.y=bottom_height
	hud.get_node("Utility").position=Vector2((size_.x-400)/2,size_.y-bottom_height-22);hud.get_node("Utility").size.y=bottom_height
	hint_label.position=Vector2(24,size_.y-bottom_height-56);hint_label.size=Vector2(size_.x-48,30)
	feed_label.position=Vector2(size_.x-330,106);feed_label.size=Vector2(306,110)
	objective.position=Vector2((size_.x-240)/2,size_.y*.5+42);objective.size=Vector2(240,6)
	objective_label.position=Vector2((size_.x-400)/2,size_.y*.5+55);objective_label.size=Vector2(400,28)
	outcome_panel.position=Vector2((size_.x-500)/2,size_.y*.25);outcome_panel.size=Vector2(500,108)
	for panel_ in [modal_panel,scoreboard_panel]:
		if is_instance_valid(panel_):
			var limit:=Vector2(880,620)
			if panel_==modal_panel:
				if modal=="pause":limit=Vector2(520,500)
				elif modal=="match":limit=Vector2(680,500)
				elif modal=="settings":limit=Vector2(680,620)
			var width:=minf(limit.x,size_.x-48);var height:=minf(limit.y,size_.y-48)
			panel_.position=(size_-Vector2(width,height))*.5;panel_.size=Vector2(width,height)

func _local() -> Dictionary:
	for actor in view.get("actors",[]):
		if int(actor.get("id",-1))==int(view.get("local_id",0)):return actor
	return {}

func update_view(next: Dictionary) -> void:
	if not _built:return
	view=next.duplicate(true)
	var actor:=_local();var scores:Dictionary=view.get("scores",{})
	score.text="%d  —  %d"%[scores.get("sun",0),scores.get("moon",0)]
	var seconds:=maxi(0,ceili(float(view.get("time_left",0))))
	clock_label.text="%02d:%02d"%[seconds/60,seconds%60]
	var attack:=String(view.get("attack_team","sun"))==String(actor.get("team","sun"))
	var alive:={"sun":0,"moon":0}
	for person in view.get("actors",[]):
		if person.get("alive",false):alive[String(person.get("team","sun"))]+=1
	round_label.text="R%d  %s  ·  SUN %d / MOON %d  ·  FIRST 13"%[view.get("round_number",1),"ATTACK" if attack else "DEFEND",alive.sun,alive.moon]
	callout_label.text=String(view.get("callout","Sangam"))
	health_label.text=str(roundi(float(actor.get("health",0))))+" HP"
	health_label.add_theme_color_override("font_color",T.RED if float(actor.get("health",0))<30 else T.IVORY)
	armor_label.text="KAVACHA  %d"%actor.get("armor",0)
	ammo_label.text="%s / %s"%[view.get("ammo","—"),view.get("reserve","—")]
	weapon_label.text=String(view.get("weapon_name","ARKA SIDEARM")).to_upper()
	if float(view.get("reload_progress",0))>0:weapon_label.text="RELOADING  %d%%"%roundi(clampf(view.reload_progress,0,1)*100)
	var charges:Dictionary=actor.get("charges",{})
	for i in 4:
		var count:=int(actor.get("ult",0)) if i==3 else int(charges.get(T.ABILITIES[i].key.to_lower(),0))
		ability_labels[i].text=T.ABILITIES[i].key+"  /  "+("%d/6"%count if i==3 else str(count))
		ability_labels[i].add_theme_color_override("font_color",T.GOLD if count>=(6 if i==3 else 1) else T.MUTED)
		ability_icons[i].modulate.a=1.0 if count>=(6 if i==3 else 1) else .35
	var phase:=String(view.get("phase","buy"))
	phase_label.text="PREPARE  ·  B TO BUY" if phase=="buy" else ("ASTRA ATTUNED  /  SITE "+String(view.get("site","")) if phase=="planted" else "")
	hint_label.text=String(view.get("hint",""))
	if hint_label.text.is_empty():hint_label.text=String(view.get("ability_hint",""))
	if not actor.get("alive",true):hint_label.text="ELIMINATED  ·  "+String(view.get("spectating","Return next round"))
	crosshair.visible=bool(actor.get("alive",true)) and not has_modal()
	crosshair.spread=clampf(float(view.get("crosshair_spread",4)),2,32);crosshair.hit=bool(view.get("hit_marker",false));crosshair.queue_redraw()
	minimap.refresh(view,actor);damage_border.modulate.a=clampf(float(view.get("damage_flash",0)),0,1)
	var lines:PackedStringArray=[]
	for entry in view.get("feed",[]).slice(-4):
		lines.append(String(entry) if entry is String else "%s  ›  %s"%[entry.get("attacker",""),entry.get("target","")])
	feed_label.text="\n".join(lines)
	objective.value=clampf(float(view.get("interaction_progress",0)),0,1)*100
	objective.visible=objective.value>0 and int(view.get("interaction_actor",-1))==int(actor.get("id",-2))
	objective_label.visible=objective.visible;objective_label.text="HOLD F  /  "+("SEVERING" if phase=="planted" else "ATTUNING")
	outcome.visible=phase=="round_end"
	outcome_panel.visible=outcome.visible
	outcome_title.text="ROUND WON" if view.get("winner","")==actor.get("team","sun") else "ROUND LOST"
	outcome_reason.text=String(view.get("reason","")).replace("_"," ").capitalize()
	var requested:=modal
	if phase=="match_end":requested="match"
	elif modal in ["", "pause", "shop", "match"]:
		requested="shop" if view.get("shop_open",false) else ("pause" if view.get("paused",false) else "")
	if requested!=modal:_show_modal(requested)
	crosshair.visible=bool(actor.get("alive",true)) and not has_modal()
	if modal=="shop":_refresh_shop()
	_show_scoreboard(bool(view.get("scoreboard_open",false)) and modal.is_empty())
	if is_instance_valid(scoreboard_layer) and scoreboard_layer.visible:_refresh_scoreboard()

func has_modal() -> bool:
	return not modal.is_empty()

func show_settings() -> void:_show_modal("settings")
func show_guide() -> void:_show_modal("guide")

func close_modal(notify_host: bool = true) -> void:
	var previous:=modal
	_show_modal("")
	if notify_host:_call("request_shop_close" if previous=="shop" else "request_resume")

func _call(method: String, argument: Variant = null) -> void:
	if not is_instance_valid(host) or not host.has_method(method):return
	if argument==null:host.call(method)
	else:host.call(method,argument)

func _overlay() -> Array:
	var layer_:=Control.new();canvas.add_child(layer_);layer_.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var dim:=ColorRect.new();dim.color=Color(.015,.025,.04,.82);layer_.add_child(dim);dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var panel_:=PanelContainer.new();panel_.add_theme_stylebox_override("panel",T.panel(T.INK,24,Color("405363")));layer_.add_child(panel_)
	return [layer_,panel_]

func _show_modal(next: String) -> void:
	modal=next
	if is_instance_valid(modal_layer):canvas.remove_child(modal_layer);modal_layer.queue_free()
	modal_layer=null;modal_panel=null;shop_entries.clear();settings_controls.clear()
	if next.is_empty():return
	var overlay:=_overlay();modal_layer=overlay[0];modal_panel=overlay[1]
	var column:=T.stack(16);modal_panel.add_child(column)
	var top:=T.row();column.add_child(top);modal_heading=T.label({"shop":"Round arsenal","pause":"Take a breath.","settings":"Settings","guide":"Rama's tactical kit","match":"Match complete"}.get(next,next),30,T.IVORY,true);modal_heading.size_flags_horizontal=Control.SIZE_EXPAND_FILL;top.add_child(modal_heading)
	if next!="match":top.add_child(T.button("Close",func():close_modal()))
	column.add_child(HSeparator.new())
	var scroll:=ScrollContainer.new();scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;column.add_child(scroll)
	modal_body=T.stack(14);modal_body.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(modal_body)
	match next:
		"pause":
			modal_body.add_child(T.prose("Casual · local 5v5 · first to 13",18,T.GOLD))
			modal_body.add_child(T.button("Resume match",func():close_modal(),true))
			modal_body.add_child(T.button("Settings",func():_call("request_settings")))
			modal_body.add_child(T.button("Rama & controls",show_guide))
			modal_body.add_child(T.button("Restart Casual",func():_call("request_restart")))
			modal_body.add_child(T.button("Leave match",func():_call("request_menu")))
		"settings":
			modal_body.add_theme_constant_override("separation",8)
			settings_controls=T.settings_form(modal_body,T.load_settings());settings_status=T.prose("Save to apply these settings.",14);modal_body.add_child(settings_status)
			modal_body.add_child(T.button("Save settings",_save_settings,true));modal_body.add_child(T.button("Discard changes",func():_show_modal("pause")))
		"guide":
			modal_body.add_child(T.prose("ARKA sidearm · SURYA carbine. Aim with RMB, fire with LMB, reload with R. Utility is spent on use; the ultimate requires six earned points."))
			Frontend._add_abilities(modal_body)
			modal_body.add_child(T.prose("WASD move · Shift walk · Space jump\nHold F at a site to attune or sever. B buys during preparation in your spawn. Hold Tab for the scoreboard. Escape pauses."))
		"shop":_build_shop()
		"match":
			var actor:=_local();var won:bool=view.get("winner","")==actor.get("team","sun")
			modal_heading.text="VICTORY" if won else "DEFEAT"
			modal_heading.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;modal_heading.add_theme_color_override("font_color",T.GOLD if won else T.RED)
			var result:=T.label("%d  —  %d"%[view.get("scores",{}).get("sun",0),view.get("scores",{}).get("moon",0)],64,T.IVORY,true);result.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;modal_body.add_child(result)
			var teams:=T.label("SUN                       MOON",14,T.GOLD);teams.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;modal_body.add_child(teams)
			var match_copy:=T.prose("Casual · Sangam · first to 13",18);match_copy.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;modal_body.add_child(match_copy)
			var stats:=T.prose("Rama  /  %d eliminations  /  %d deaths"%[actor.get("kills",0),actor.get("deaths",0)],16,T.IVORY);stats.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER;modal_body.add_child(stats)
			for action in [T.button("Play another Casual",func():_call("request_restart"),true),T.button("Return to menu",func():_call("request_menu"))]:action.size_flags_horizontal=Control.SIZE_SHRINK_CENTER;action.custom_minimum_size.x=300;modal_body.add_child(action)
	_layout()
	var buttons:=modal_body.find_children("*","Button",true,false)
	if next=="settings":settings_controls.sensitivity.grab_focus()
	else:
		for button in buttons:
			if not button.disabled:button.grab_focus();break

func _save_settings() -> void:
	var values:=T.settings_values(settings_controls)
	if T.save_settings(values)!=OK:settings_status.text="Settings could not be saved. Please try again.";return
	canvas.theme=T.create(values.ui_scale);T.rescale(canvas,values.ui_scale);_call("apply_settings",values);settings_status.text="Settings saved.";_layout()

func _build_shop() -> void:
	shop_credit=T.label("",24,T.GOLD);modal_body.add_child(shop_credit)
	shop_status=T.prose("",14);modal_body.add_child(shop_status)
	for id in ["carbine","armor","q","e","c"]:
		var line:=T.row(18);modal_body.add_child(line)
		line.add_child(T.icon({"carbine":"carbine","armor":"armor","q":"veil","e":"step","c":"wall"}[id],40))
		var copy:=T.stack(2);copy.size_flags_horizontal=Control.SIZE_EXPAND_FILL;line.add_child(copy)
		var name_:=T.label("",18);copy.add_child(name_)
		var detail:=T.prose("",14);copy.add_child(detail)
		var button:=T.button("",func():_call("request_purchase",id));button.custom_minimum_size.x=160;line.add_child(button)
		shop_entries[id]={"title":name_,"detail":detail,"button":button}
		modal_body.add_child(HSeparator.new())
	modal_body.add_child(T.prose("Equipment is retained when you survive. A fallen player starts the next round with a sidearm and no armor. Purchases use this round's credits.",14))
	_refresh_shop()

func _refresh_shop() -> void:
	var actor:=_local();var catalog:Dictionary=view.get("catalog",{});var credits:=int(actor.get("credits",0))
	shop_credit.text="%d CREDITS"%credits
	var allowed:bool=view.get("buy_allowed",false) and view.get("phase","")=="buy" and actor.get("alive",false)
	shop_status.text="Buy before the barrier falls. The local match is paused while this shop is open." if allowed else "Purchases require the preparation phase and your own spawn."
	for id in shop_entries:
		var item:Dictionary=catalog.get(id,{})
		var row_:Dictionary=shop_entries[id]
		row_.title.text=String(item.get("label",id.capitalize()))
		var cost:=int(item.get("cost",0));var owned:=false
		if id=="carbine":owned=actor.get("weapon","")=="carbine"
		elif id=="armor":owned=int(actor.get("armor",0))>=50
		else:owned=int(actor.get("charges",{}).get(id,0))>=int(item.get("max",1))
		row_.detail.text="Equipped" if owned else ("Not enough credits" if credits<cost else {"carbine":"Mythic automatic rifle","armor":"Up to 50 armor","q":"Smoke utility · up to two charges","e":"Grounded dash · one charge","c":"Temporary wall · one charge"}.get(id,""))
		row_.button.text="OWNED" if owned else ("%d  /  BUY"%cost if not item.is_empty() else "UNAVAILABLE")
		row_.button.disabled=not allowed or item.is_empty() or owned or credits<cost

func _show_scoreboard(enabled: bool) -> void:
	if enabled and not is_instance_valid(scoreboard_layer):
		var overlay:=_overlay();scoreboard_layer=overlay[0];scoreboard_panel=overlay[1];scoreboard_layer.mouse_filter=Control.MOUSE_FILTER_IGNORE
		var column:=T.stack(12);scoreboard_panel.add_child(column);column.add_child(T.label("Casual / scorecard",28,T.IVORY,true));scoreboard_match_label=T.label("",14,T.MUTED);column.add_child(scoreboard_match_label)
		var scroll:=ScrollContainer.new();scroll.size_flags_vertical=Control.SIZE_EXPAND_FILL;scroll.horizontal_scroll_mode=ScrollContainer.SCROLL_MODE_DISABLED;column.add_child(scroll)
		var rows:=T.stack(6);rows.size_flags_horizontal=Control.SIZE_EXPAND_FILL;scroll.add_child(rows)
		var widths:=[230,60,90,80,140]
		for team in ["sun","moon"]:
			var team_title:=T.label("",16,T.GOLD if team=="sun" else T.TEAL);rows.add_child(team_title);scoreboard_team_labels[team]=team_title
			var headings:=T.row(10);rows.add_child(headings)
			for i in 5:
				var heading:=T.label(["PLAYER","K / D","CREDITS","STATUS","EQUIPMENT"][i],12,T.MUTED);heading.custom_minimum_size.x=widths[i];headings.add_child(heading)
			for id in range(0 if team=="sun" else 5,5 if team=="sun" else 10):
				var line:=T.row(10);rows.add_child(line);var fields:Dictionary={}
				for i in 5:
					var field:=T.label("",15,T.IVORY);field.custom_minimum_size=Vector2(widths[i],28);line.add_child(field);fields[["player","kd","credits","health","weapon"][i]]=field
				scoreboard_rows[id]=fields
			rows.add_child(HSeparator.new())
		_layout()
	if is_instance_valid(scoreboard_layer):scoreboard_layer.visible=enabled

func _refresh_scoreboard() -> void:
	var local:=_local()
	scoreboard_match_label.text="ROUND %d  ·  %d : %d  ·  FIRST TO 13  ·  HOLD TAB"%[view.get("round_number",1),view.get("scores",{}).get("sun",0),view.get("scores",{}).get("moon",0)]
	for team in scoreboard_team_labels:scoreboard_team_labels[team].text=team.to_upper()+"  /  "+("ATTACK" if team==view.get("attack_team","sun") else "DEFEND")
	for actor in view.get("actors",[]):
		var id:=int(actor.get("id",-1))
		if not scoreboard_rows.has(id):continue
		var money:=str(actor.get("credits",0)) if actor.get("team","")==local.get("team","") else "—"
		var ally:bool=actor.get("team","")==local.get("team","")
		var life:=str(roundi(float(actor.get("health",0))))+" HP" if ally else "Alive"
		var fields:Dictionary=scoreboard_rows[id]
		fields.player.text=String(actor.get("name","")).replace(" · You","")+(" · YOU" if id==int(local.get("id",0)) else "")
		fields.kd.text="%d / %d"%[actor.get("kills",0),actor.get("deaths",0)]
		fields.credits.text=money;fields.health.text=life if actor.get("alive",false) else "Out"
		fields.weapon.text=("SURYA" if actor.get("weapon","")=="carbine" else "ARKA") if ally else "—"
		for field in fields.values():field.modulate=T.IVORY if actor.get("alive",false) else T.MUTED
