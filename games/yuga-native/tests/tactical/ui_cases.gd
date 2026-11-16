extends SceneTree
const T=preload("res://scripts/tactical_theme.gd")
const UI=preload("res://scripts/tactical_ui.gd")
const Frontend=preload("res://scripts/tactical_frontend.gd")
const Rules=preload("res://scripts/tactical_round_rules.gd")
var checks:Array[Dictionary]=[]
var report_path:=""

class Host extends Node:
	var ui:CanvasLayer
	var rules:RefCounted
	var purchases:Array=[]
	var resumes:=0
	var restarts:=0
	var menus:=0
	func request_purchase(id:String)->void:purchases.append(id);rules.purchase(0,id)
	func request_resume()->void:resumes+=1;ui.close_modal(false)
	func request_shop_close()->void:request_resume()
	func request_menu()->void:menus+=1
	func request_restart()->void:restarts+=1
	func request_settings()->void:ui.show_settings()
	func apply_settings(_values:Dictionary)->void:pass

func _initialize()->void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="):report_path=argument.trim_prefix("--report=")
	call_deferred("run")

func check(name_:String,passed:bool)->void:
	checks.append({"name":name_,"passed":passed});print("PASS " if passed else "FAIL ",name_)

func labels(node:Node)->String:
	var result:PackedStringArray=[]
	for label in node.find_children("*","Label",true,false):result.append(label.text)
	return "\n".join(result)

func run()->void:
	root.content_scale_size=Vector2i(960,540)
	root.size=Vector2i(960,540)
	var safe:=T.sanitize_settings({"sensitivity":INF,"master_volume":-5,"fov":500,"ui_scale":0,"reduced_motion":"false"})
	check("Invalid/nonfinite settings use safe bounds and types",safe.sensitivity==T.DEFAULTS.sensitivity and safe.master_volume==0 and safe.fov==110 and safe.ui_scale==1 and not safe.reduced_motion)
	var path:="user://tactical-ui-test-settings.cfg"
	check("Settings save and fresh ConfigFile load retain real values",T.save_settings({"sensitivity":.004,"master_volume":.35,"fov":105,"reduced_motion":true,"ui_scale":1.3},path)==OK and is_equal_approx(T.load_settings(path).sensitivity,.004) and T.load_settings(path).reduced_motion)
	DirAccess.remove_absolute(path)
	var main_scene:String=ProjectSettings.get_setting("application/run/main_scene","")
	check("Configured native entry is the tactical frontend",main_scene=="res://scenes/tactical_frontend.tscn")
	var entry:PackedScene=load(main_scene) if main_scene=="res://scenes/tactical_frontend.tscn" else load("res://scenes/tactical_frontend.tscn")
	var front:=entry.instantiate();root.add_child(front)
	await process_frame;await process_frame
	check("Frontend starts with actual Casual action and local-bot disclosure",front.page=="home" and labels(front).contains("Local match with allied and opposing bots"))
	front.show_page("casual")
	var ranked=false
	for button in front.body.find_children("*","Button",true,false):
		if button.text.begins_with("Ranked"):ranked=button.disabled
	check("Ranked is visibly planned and cannot launch",ranked)
	front.show_page("hero")
	check("Hero page presents four tactical abilities and firearm identity",labels(front).contains("Solar veil") and labels(front).contains("Measured step") and labels(front).contains("Ward wall") and labels(front).contains("Dawn volley") and labels(front).contains("ARKA"))
	front.show_page("settings")
	check("Settings page exposes all saved controls",front.settings_controls.size()==5)
	front.show_page("help")
	check("Controls explain actual objective hold and scoreboard inputs",labels(front).contains("F hold") and labels(front).contains("Hold Tab"))
	front.begin_loading("res://tests/tactical/does-not-exist.tscn")
	check("Missing match resource gives recoverable error without fabricated progress",front.page=="load_error" and front.loading_path.is_empty() and labels(front).contains("unavailable"))
	front.show_page("casual")
	front.begin_loading("res://tests/tactical/ui_loading_fixture.tscn");front.cancel_loading()
	check("Cancel returns to Casual and prevents stale navigation",front.page=="casual" and front.loading_path.is_empty())
	for unused in 3:await process_frame
	check("Canceled threaded load never changes the current scene",current_scene==null)
	front.begin_loading("res://tests/tactical/ui_loading_fixture.tscn")
	for unused in 100:
		await process_frame
		if current_scene!=null:break
	check("Actual threaded PackedScene load enters the completed fixture",current_scene!=null and current_scene.name=="TacticalLoadingFixture")
	if current_scene!=null:var scene:=current_scene;current_scene=null;root.remove_child(scene);scene.free()
	root.remove_child(front);front.free()
	var authority:=Rules.new();authority.start_match()
	var host:=Host.new();host.rules=authority;root.add_child(host)
	var ui:=UI.new();root.add_child(ui);host.ui=ui;ui.configure(host);ui.configure(host)
	check("Repeated configure retains one UI owner",ui.get_child_count()==1)
	var state:=authority.snapshot();state.merge({"local_id":0,"ammo":12,"reserve":36,"paused":false,"shop_open":true,"buy_allowed":true,"callout":"Sun court","sites":{"A":Vector3(-29,0,8),"B":Vector3(29,0,8)},"map_bounds":Rect2(-50,-65,100,130),"actor_positions":{0:Vector3(0,0,-54),1:Vector3(3,0,-54),5:Vector3(0,0,54)}})
	ui.update_view(state)
	check("Shop gates expensive rifle and owned free dash truthfully",ui.modal=="shop" and ui.shop_entries.carbine.button.disabled and ui.shop_entries.e.button.disabled and not ui.shop_entries.q.button.disabled)
	var original_credits:int=ui._local().credits
	ui.shop_entries.q.button.pressed.emit()
	check("Purchase delegates exactly once without optimistic UI inventory mutation",host.purchases==["q"] and authority.actors[0].credits==600 and ui._local().credits==original_credits)
	state.actors=authority.snapshot().actors;ui.update_view(state)
	check("Receipt snapshot updates credits and charges",ui.shop_credit.text=="600 CREDITS" and ui.ability_labels[0].text.ends_with("1"))
	authority.purchase(0,"q");state.actors=authority.snapshot().actors;ui.update_view(state)
	check("Utility cap disables the completed offer",ui.shop_entries.q.button.disabled)
	state.buy_allowed=false;ui.update_view(state)
	check("Outside own buy zone all offers are disabled",ui.shop_entries.values().all(func(row):return row.button.disabled))
	state.buy_allowed=true;state.phase="live";ui.update_view(state)
	check("Expired preparation rejects every purchase in presentation",ui.shop_entries.values().all(func(row):return row.button.disabled))
	state.shop_open=false;state.phase="live";state.scoreboard_open=true;ui.update_view(state)
	check("Held scoreboard remains nonmodal and shows all ten actors",not ui.has_modal() and ui.scoreboard_layer.visible and ui.scoreboard_rows.size()==10)
	check("Minimap reveals living teammates only",ui.minimap.visible_actor_ids==[0,1,2,3,4] and not ui.minimap.visible_actor_ids.has(5))
	state.actors[1].health=67;state.actors[5].health=12;ui.update_view(state)
	check("Scoreboard shows actual ally health without hidden enemy health",ui.scoreboard_rows[1].health.text.contains("67 HP") and not ui.scoreboard_rows[5].health.text.contains("12 HP"))
	state.scoreboard_open=false;state.paused=true;ui.update_view(state)
	check("Pause creates a blocking overlay and hides scoreboard",ui.has_modal() and ui.modal=="pause" and not ui.scoreboard_layer.visible)
	ui.show_settings();check("Settings is a real interactive modal",ui.modal=="settings" and ui.settings_controls.size()==5)
	ui.close_modal();check("Resume callback closes without recursion or stale modal latch",host.resumes==1 and not ui.has_modal())
	ui.show_guide();check("Guide contains complete tactical kit and hold controls",ui.modal=="guide" and labels(ui.modal_body).contains("Dawn volley") and labels(ui.modal_body).contains("Hold F"))
	ui.close_modal(false);state.paused=false;state.interaction_actor=0;state.interaction_progress=.5;ui.update_view(state)
	check("Local objective hold uses authority normalized progress",ui.objective.visible and is_equal_approx(ui.objective.value,50))
	state.interaction_actor=1;ui.update_view(state);check("Another actor's objective hold does not appear as local progress",not ui.objective.visible)
	state.actors[0].ult=5;ui.update_view(state);check("Ultimate displays earned points rather than a cooldown",ui.ability_labels[3].text.ends_with("5/6"))
	state.actors[0].alive=false;state.actors[0].health=0;state.spectating="Tara";ui.update_view(state)
	check("Elimination is visible and removes the active aiming reticle",ui.hint_label.text.contains("ELIMINATED") and not ui.crosshair.visible and ui.health_label.text=="0 HP")
	state.phase="round_end";state.winner="sun";state.reason="Defenders eliminated";ui.update_view(state)
	check("Round outcome reads actual winner and reason",ui.outcome.visible and ui.outcome_title.text=="ROUND WON" and ui.outcome_reason.text.contains("Defenders"))
	state.phase="match_end";state.scores={"sun":13,"moon":7};ui.update_view(state)
	check("Match outcome shows first13 result with replay/menu controls",ui.modal=="match" and ui.modal_heading.text=="VICTORY" and labels(ui.modal_body).contains("13  —  7"))
	state.phase="buy";state.actors[0].alive=true;state.actors[0].health=100;ui.update_view(state)
	check("New match view clears previous result ownership",not ui.has_modal() and not ui.outcome.visible)
	for scale_ in [1.0,1.5]:
		ui.canvas.theme=T.create(scale_);T.rescale(ui.canvas,scale_);ui._layout()
		await process_frame;await process_frame
		var health:Control=ui.hud.get_node("Vitals");var utility:Control=ui.hud.get_node("Utility");var ammo:Control=ui.hud.get_node("Ammunition")
		check("Compact HUD regions stay distinct at960x540 scale"+str(scale_),not health.get_global_rect().intersects(utility.get_global_rect()) and not ammo.get_global_rect().intersects(utility.get_global_rect()) and Rect2(Vector2.ZERO,Vector2(960,540)).encloses(ammo.get_global_rect()))
		ui.show_settings();await process_frame;await process_frame
		check("Scrollable settings panel stays within compact viewport scale"+str(scale_),Rect2(Vector2.ZERO,Vector2(960,540)).encloses(ui.modal_panel.get_global_rect()))
		ui.close_modal(false)
	root.remove_child(ui);ui.free();root.remove_child(host);host.free()
	var passed:=checks.all(func(c):return c.passed)
	var sources:Dictionary={}
	for path_ in ["res://project.godot","res://scenes/tactical_frontend.tscn","res://scripts/tactical_theme.gd","res://scripts/tactical_frontend.gd","res://scripts/tactical_ui.gd","res://tests/tactical/ui_cases.gd"]:sources[path_]=FileAccess.get_sha256(path_)
	var report:={"passed":passed,"count":checks.size(),"checks":checks,"sources":sources,"scope":"Native headless actual controls/settings/resources plus actual rules catalog and receipts. Structural layout at960x540 scales1/1.5. No actual pixels, ordinary input, online or GPU performance claim."}
	if not report_path.is_empty():var file:=FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t"))
	quit(0 if passed else 1)
