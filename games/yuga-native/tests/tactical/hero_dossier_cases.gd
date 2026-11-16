extends SceneTree
const Dossier=preload("res://scripts/tactical_hero_dossier.gd")
const Frontend=preload("res://scripts/tactical_frontend.gd")
const T=preload("res://scripts/tactical_theme.gd")
const Rules=preload("res://scripts/tactical_round_rules.gd")
const Weapon=preload("res://scripts/tactical_weapon.gd")
var checks:Array[Dictionary]=[]
var report_path:=""
class PreviewHost extends Node:
	var calls:Array[String]=[]
	var is_ready:=true
	var busy:=false
	var paused:=false
	var reduced_motion:=false
	var current_action:="idle"
	var supported_actions:Array=["idle","aim","q","e","c","x"]
	func set_reduced_motion(value:bool)->void:reduced_motion=value
	func set_preview(action:String)->bool:
		if not is_ready or action not in supported_actions:return false
		calls.append(action);current_action=action;busy=action in ["q","e","c","x"];return true
	func preview_report()->Dictionary:return {"ready":is_ready,"busy":busy,"paused":paused,"reduced_motion":reduced_motion,"current_action":current_action,"supported_actions":supported_actions}
func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):report_path=argument.trim_prefix("--report=")
	call_deferred("run")
func check(label:String,passed:bool)->void:
	checks.append({"name":label,"passed":passed});print("PASS " if passed else "FAIL ",label)
func labels(node:Node)->String:
	var strings:PackedStringArray=[]
	for label in node.find_children("*","Label",true,false):strings.append(label.text)
	return "\n".join(strings)
func run()->void:
	root.size=Vector2i(1280,720);root.content_scale_size=root.size
	var host:=PreviewHost.new();root.add_child(host)
	var front:=Frontend.new();root.add_child(front);await process_frame
	front.show_page("hero");await process_frame;await process_frame
	var dossier:Control=front.hero_dossier;dossier.configure(host,{"reduced_motion":true})
	var rules:=Rules.new()
	check("Dossier loads verified rules without starting a match",dossier.data_report().ready and dossier.data_report().rules_actors==0 and dossier.data_report().rules_phase=="match_end")
	check("Four distinct native selectors start on Solar veil",dossier.selectors.size()==4 and dossier.selected_slot=="q" and dossier.selected_title.text=="Solar veil")
	check("Utility cost and capacity follow the authoritative catalog",["q","e","c"].all(func(slot):return dossier.abilities[slot].cost==int(rules.config.catalog[slot].cost) and dossier.abilities[slot].capacity==int(rules.config.catalog[slot].max)))
	check("Duration facts retain existing theme values",dossier.abilities.q.duration_text=="12 s" and dossier.abilities.c.duration_text=="10 s")
	dossier.selectors.x.pressed.emit()
	check("Selection exposes ultimate earned points without triggering a preview",dossier.selected_slot=="x" and dossier.facts_label.text.contains(str(int(rules.config.ult_cost))+" earned points") and host.calls.is_empty())
	check("All ability counterplay is populated without fake cooldowns",dossier.abilities.values().all(func(row):return not row.counterplay.is_empty()) and not dossier.facts_label.text.contains("cooldown"))
	dossier.preview_button.pressed.emit()
	check("Explicit preview calls showcase once with selected slot",host.calls==["x"] and dossier.preview_button.disabled and dossier.aim_button.disabled and not dossier.ready_button.disabled)
	check("Busy studio rejects retrigger before contacting the showcase",not dossier.request_preview("q") and host.calls==["x"])
	host.paused=true;dossier._refresh_preview()
	check("Paused preview copy follows viewer state while Ready stays available",dossier.preview_status.text=="Preview paused · Play resumes" and not dossier.ready_button.disabled and dossier.preview_button.disabled)
	dossier.ready_button.pressed.emit();host.paused=false;dossier._refresh_preview()
	check("Ready resets an active preview and re-enables controls",host.calls==["x","idle"] and not dossier.preview_button.disabled and not dossier.aim_button.disabled)
	dossier.aim_button.pressed.emit();check("Aim is an explicit presentation request",host.calls.back()=="aim")
	check("Reduced-motion setting reaches showcase API",host.reduced_motion and dossier.preview_status.text.contains("reduced motion"))
	var before:int=host.calls.size();var key:=InputEventKey.new();key.pressed=true;key.keycode=KEY_RIGHT
	dossier._selector_input(key,"x")
	check("Keyboard selector wraps and keeps browsing separate from animation",dossier.selected_slot=="q" and dossier.selectors.q.has_focus() and host.calls.size()==before)
	check("Unknown selection leaves the current detail intact",not dossier.select_ability("future_hero") and dossier.selected_slot=="q")
	check("Weapon facts follow actual firearm profiles and catalog",["pistol","carbine"].all(func(id):return dossier.weapons[id].magazine==Weapon.PROFILES[id].magazine and dossier.weapons[id].reserve==Weapon.PROFILES[id].reserve and dossier.weapons[id].damage==Weapon.PROFILES[id].damage and dossier.weapons[id].reload==Weapon.PROFILES[id].reload and dossier.weapons[id].cost==int(rules.config.catalog[id].cost)))
	check("Weapon roles distinguish starting equipment from studio display",labels(dossier).contains("Starting sidearm") and labels(dossier).contains("Buy upgrade · shown in studio"))
	host.supported_actions=["idle","aim"];dossier._refresh_preview()
	check("Unsupported ability preview disables truthfully",dossier.preview_button.disabled and not dossier.request_preview("q"))
	host.is_ready=false;dossier._refresh_preview();check("Unavailable showcase leaves readable details and disables actions",dossier.preview_button.disabled and dossier.aim_button.disabled and dossier.ready_button.disabled and dossier.detail_label.text.contains("veil"))
	host.is_ready=true;host.supported_actions=["idle","aim","q","e","c","x"];dossier._refresh_preview()
	for dimensions in [Vector2i(1280,720),Vector2i(960,540)]:
		for scale_ in [1.0,1.5]:
			root.size=dimensions;root.content_scale_size=dimensions
			front._settings.ui_scale=scale_;front._apply_settings();front._layout();await process_frame;await process_frame
			dossier.selectors.q.grab_focus();await process_frame;await process_frame
			var within:Rect2=front.content_scroll.get_global_rect()
			var selector_fit:bool=dossier.selectors.values().all(func(button):return within.encloses(button.get_global_rect()))
			check("Selectors fit and scroll into view "+str(dimensions)+" scale"+str(scale_),selector_fit)
			var action:Control=front._page_actions.get_child(0)
			check("ChooseCasual remains pinned inside native viewport "+str(dimensions)+" scale"+str(scale_),Rect2(Vector2.ZERO,Vector2(dimensions)).encloses(action.get_global_rect()) and action.get_global_rect().position.y>=front.content_scroll.get_global_rect().end.y)
			dossier.aim_button.grab_focus();await process_frame;await process_frame
			check("Keyboard focus reveals loadout preview controls "+str(dimensions)+" scale"+str(scale_),front.content_scroll.get_global_rect().encloses(dossier.aim_button.get_global_rect()))
	check("Preview requests never create local match actors",dossier.data_report().rules_actors==0 and dossier.data_report().rules_phase=="match_end" and Input.mouse_mode==Input.MOUSE_MODE_VISIBLE)
	front.show_page("settings");check("Studio exit preserves five native settings controls",front.settings_controls.size()==5)
	front.show_page("hero");await process_frame;await process_frame
	check("Re-entry resets selection and keeps one dossier",front.hero_dossier.selected_slot=="q" and front.body.find_children("HeroDossier","VBoxContainer",true,false).size()==1)
	root.remove_child(front);front.free();root.remove_child(host);host.free()
	var sources:={}
	for path in ["res://scripts/tactical_frontend.gd","res://scripts/tactical_hero_dossier.gd","res://tests/tactical/hero_dossier_cases.gd","res://assets/tactical/rules.json","res://scripts/tactical_theme.gd","res://scripts/tactical_weapon.gd"]:sources[path]=FileAccess.get_sha256(path)
	var passed:bool=checks.all(func(row):return row.passed)
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"sources":sources,"scope":"Actual native dossier controls/data/focus/layout with a contract-compatible preview host. No root pose acceptance, rendered-art, ordinary-input or game-performance claim."}
	if not report_path.is_empty():var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"))
	quit(0 if passed else 1)
