extends VBoxContainer
## Read-only ability/loadout studio. Preview requests never buy or spend utility.
const T=preload("res://scripts/tactical_theme.gd")
const Rules=preload("res://scripts/tactical_round_rules.gd")
const Weapon=preload("res://scripts/tactical_weapon.gd")
const SLOTS:=["q","e","c","x"]
const COUNTERPLAY:={
	"q":"Bullets pass through the veil. Wait for it to clear or change your angle.",
	"e":"Solid cover blocks movement. Watch the angle where Rama finishes the dash.",
	"c":"Shoot the wall to break it, wait for it to expire, or take another route. Placement needs clear space.",
	"x":"Solid cover stops each shot. Change position between the three releases."
}
var selected_slot:="q"
var selectors:Dictionary={}
var abilities:Dictionary={}
var weapons:Dictionary={}
var preview_button:Button
var aim_button:Button
var ready_button:Button
var selected_title:Label
var facts_label:Label
var detail_label:Label
var counterplay_label:Label
var preview_status:Label
var _showcase:Node
var _rules:RefCounted
var _built:=false
var _poll_age:=0.0
var _rejected:=false
var _data_ready:=false

func _ready()->void:
	name="HeroDossier"
	add_theme_constant_override("separation",10)
	size_flags_horizontal=Control.SIZE_EXPAND_FILL
	_read_data()
	_build()
	select_ability(selected_slot)

func configure(showcase:Node,settings:Dictionary={})->void:
	_showcase=showcase
	if is_instance_valid(_showcase) and _showcase.has_method("set_reduced_motion"):
		_showcase.set_reduced_motion(bool(settings.get("reduced_motion",false)))
	_refresh_preview()

func _read_data()->void:
	_rules=Rules.new()
	_data_ready=_rules.configured
	if not _data_ready:return
	var duration_pattern:=RegEx.new();duration_pattern.compile("for ([0-9]+) seconds")
	for authored in T.ABILITIES:
		var slot:String=authored.key.to_lower()
		var row:Dictionary=authored.duplicate(true)
		row["counterplay"]=COUNTERPLAY[slot]
		var duration:=duration_pattern.search(authored.detail)
		row["duration_text"]=duration.get_string(1)+" s" if duration!=null else ("Grounded dash" if slot=="e" else "Three shots")
		if slot=="x":
			row["cost"]=int(_rules.config.ult_cost);row["capacity"]=0;row["cost_kind"]="earned points"
		else:
			var offer:Dictionary=_rules.config.catalog[slot]
			row["cost"]=int(offer.cost);row["capacity"]=int(offer.max);row["cost_kind"]="credits"
		abilities[slot]=row
	for id in ["pistol","carbine"]:
		var row:Dictionary=Weapon.PROFILES[id].duplicate(true)
		row["label"]=_rules.config.catalog[id].label;row["cost"]=int(_rules.config.catalog[id].cost)
		row["role"]="Starting sidearm" if id=="pistol" else "Buy upgrade · shown in studio"
		weapons[id]=row

func _build()->void:
	var choices:=T.row(8);choices.name="AbilitySelectors";add_child(choices)
	var group:=ButtonGroup.new()
	for slot in SLOTS:
		var button:=T.button(slot.to_upper(),func():select_ability(slot))
		button.name="Select_"+slot;button.toggle_mode=true;button.button_group=group
		button.custom_minimum_size.x=64;button.size_flags_horizontal=Control.SIZE_EXPAND_FILL
		if abilities.has(slot):
			button.icon=load("res://assets/tactical/ui/"+abilities[slot].id+".svg")
			button.expand_icon=true;button.add_theme_constant_override("icon_max_width",24)
			button.tooltip_text=abilities[slot].name
		button.gui_input.connect(func(event:InputEvent):_selector_input(event,slot))
		selectors[slot]=button;choices.add_child(button)
	var heading:=T.row(10);add_child(heading)
	selected_title=T.prose("",22,T.GOLD);heading.add_child(selected_title)
	preview_button=T.button("Preview",func():request_preview(selected_slot));preview_button.name="PreviewAbility";preview_button.tooltip_text="Preview the selected ability pose";preview_button.set_meta("tactical_base_font_size",15);preview_button.add_theme_font_size_override("font_size",roundi(15*T.current_scale));heading.add_child(preview_button)
	facts_label=T.prose("",14,T.TEAL);add_child(facts_label)
	detail_label=T.prose("",15,T.IVORY);add_child(detail_label)
	counterplay_label=T.prose("",14);add_child(counterplay_label)
	preview_status=T.prose("Preparing studio…",12);add_child(preview_status)
	add_child(HSeparator.new())
	var loadout:=T.row(8);add_child(loadout)
	var title:=T.label("Firearms",17,T.IVORY,true);title.size_flags_horizontal=Control.SIZE_EXPAND_FILL;loadout.add_child(title)
	ready_button=T.button("Ready",func():request_preview("idle"));ready_button.name="PreviewReady"
	aim_button=T.button("Aim",func():request_preview("aim"));aim_button.name="PreviewAim"
	for button in [ready_button,aim_button]:
		T.quiet(button);button.set_meta("tactical_base_font_size",14);button.add_theme_font_size_override("font_size",roundi(14*T.current_scale));loadout.add_child(button)
	for id in ["pistol","carbine"]:
		if not weapons.has(id):continue
		var data:Dictionary=weapons[id]
		var row:=T.stack(3);row.name="Weapon_"+id;add_child(row)
		row.add_child(T.prose(data.label+"  /  "+("Default" if id=="pistol" else str(data.cost)+" credits"),15,T.IVORY))
		row.add_child(T.prose("%d / %d ammo · %d damage · %s s reload"%[data.magazine,data.reserve,data.damage,str(data.reload)],13))
		row.add_child(T.prose(data.role,12,T.TEAL))
	_built=true

func select_ability(slot:String)->bool:
	if slot not in SLOTS:return false
	selected_slot=slot;_rejected=false
	if not _built:return true
	for id in selectors:
		selectors[id].set_pressed_no_signal(id==slot);T.quiet(selectors[id],id==slot)
	if not _data_ready:
		selected_title.text="Loadout data unavailable";facts_label.text="";detail_label.text="Return to Casual or try the studio again.";counterplay_label.text="";_refresh_preview();return false
	var data:Dictionary=abilities[slot]
	selected_title.text=data.name
	if slot=="x":facts_label.text="%d earned points · %s"%[data.cost,data.duration_text]
	else:
		facts_label.text="%d credits · carry %d · %s"%[data.cost,data.capacity,data.duration_text]
		if slot=="e":facts_label.text+=" · refills each round"
	detail_label.text=data.detail
	counterplay_label.text="Counterplay: "+data.counterplay
	_refresh_preview()
	return true

func _selector_input(event:InputEvent,slot:String)->void:
	if not event is InputEventKey or not event.pressed or event.echo:return
	var index:=SLOTS.find(slot)
	if event.keycode==KEY_RIGHT:index=(index+1)%SLOTS.size()
	elif event.keycode==KEY_LEFT:index=(index+SLOTS.size()-1)%SLOTS.size()
	elif event.keycode==KEY_HOME:index=0
	elif event.keycode==KEY_END:index=SLOTS.size()-1
	else:return
	select_ability(SLOTS[index]);selectors[SLOTS[index]].grab_focus();accept_event()

func request_preview(action:String)->bool:
	if not _data_ready or not is_instance_valid(_showcase) or not _showcase.has_method("set_preview"):return false
	var report:=_preview_report()
	if not bool(report.get("ready",false)) or not report.get("supported_actions",[]).has(action):return false
	if bool(report.get("busy",false)) and action!="idle":return false
	var accepted:bool=_showcase.set_preview(action)
	_rejected=not accepted;_refresh_preview()
	return accepted

func _preview_report()->Dictionary:
	if is_instance_valid(_showcase) and _showcase.has_method("preview_report"):
		var result=_showcase.preview_report()
		if result is Dictionary:return result
	return {}

func _refresh_preview()->void:
	if not _built:return
	var report:=_preview_report()
	var ready:bool=_data_ready and bool(report.get("ready",false))
	var supported:Array=report.get("supported_actions",[])
	var busy:=bool(report.get("busy",false))
	preview_button.disabled=not ready or busy or not supported.has(selected_slot)
	aim_button.disabled=not ready or busy or not supported.has("aim")
	ready_button.disabled=not ready or not supported.has("idle")
	if not ready:preview_status.text="Studio preview unavailable"
	elif _rejected:preview_status.text="Preview could not start. Try Ready, then preview again."
	elif bool(report.get("paused",false)):preview_status.text="Preview paused · Play resumes"
	elif busy:preview_status.text="Playing "+str(report.get("current_action","ability")).to_upper()+" preview · Ready resets the pose"
	elif bool(report.get("reduced_motion",false)):preview_status.text="Studio preview · reduced motion enabled"
	else:preview_status.text="Studio preview · choose a pose or ability"

func _process(delta:float)->void:
	_poll_age+=delta
	if _poll_age>=.1:_poll_age=0;_refresh_preview()

func data_report()->Dictionary:
	return {"ready":_data_ready,"selected_slot":selected_slot,"abilities":abilities.duplicate(true),"weapons":weapons.duplicate(true),"rules_actors":_rules.actors.size() if _rules!=null else 0,"rules_phase":_rules.phase if _rules!=null else "unavailable","preview":_preview_report()}
