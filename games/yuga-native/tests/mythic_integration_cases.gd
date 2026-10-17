extends SceneTree
## Independent real-world invocation/receiver/presentation integration.
## Headless checks cannot establish rendered quality, listening or hardware FPS.

const HEROES := ["rama","ravana","arjuna","duryodhana","hanuman","karna","bhima","meghnad","sita","draupadi","subhadra","hidimbi","chitrangada","ulupi"]
const ORIGIN := Vector3(-40,.05,-10)
const FORWARD := Vector3(0,0,1)
const TARGET := Vector3(-40,0,-6)
const Rules=preload("res://scripts/ultimate_rules.gd")
const SOURCE_PATHS := [
	"res://scripts/confluence_world.gd", "res://scripts/player.gd",
	"res://scripts/ultimate_session.gd", "res://scripts/ultimate_rules.gd",
	"res://scripts/invocation_audio.gd", "res://assets/audio/invocations/manifest.json",
	"res://scripts/controls_overlay.gd",
	"res://scripts/lane_army.gd", "res://scripts/lane_minion.gd",
	"res://assets/design/native-ultimate-rules.json", "res://assets/design/hero-codex.json",
	"res://tests/mythic_integration_cases.gd"
]

var scene: Node3D
var session: Node
var fx: Node3D
var checks: Array = []
var events: Array = []
var source_hashes: Dictionary = {}
var output := "/tmp/mythic-integration-cases.json"
var event_overflow := false
var baseline_nodes := 0

func _initialize() -> void:
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--report="): output=argument.trim_prefix("--report=")
	call_deferred("run")

func record(label: String, passed: bool, details: Dictionary={}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label," ",JSON.stringify(details))

func frames(count_: int=3) -> void:
	for _index in range(count_): await process_frame

func collect_event(event: Dictionary) -> void:
	if events.size()>=4096: event_overflow=true;return
	events.append(event.duplicate(true))

func has_objects(value: Variant) -> bool:
	if value is Object:return true
	if value is Dictionary:
		for key in value:
			if has_objects(key) or has_objects(value[key]):return true
	elif value is Array:
		for item in value:
			if has_objects(item):return true
	return false

func receiver_snapshot() -> Dictionary:
	var units := {}
	for unit in scene.army.units:
		if not is_instance_valid(unit):continue
		units[str(unit.unit_id)]={"health":unit.health,"alive":unit.alive,"team":unit.team,
			"position":unit.position,"status":unit.status_report()}
	return {"units":units,"gold":scene.army.gold,"kills":scene.army.kills,"cores":scene.army.cores.duplicate(true)}

func isolate_receivers() -> Dictionary:
	scene._restart_army()
	scene.army.set_physics_process(false)
	scene.army._attacks.clear()
	scene.army._decision_clock=1000.0
	var ally: Node3D
	var enemy: Node3D
	for unit in scene.army.units:
		if unit.role=="commander" and unit.team=="sun" and ally==null:ally=unit
		elif unit.role=="commander" and unit.team=="moon" and enemy==null:enemy=unit
	for unit in scene.army.units.duplicate():
		if unit!=ally and unit!=enemy:
			scene.army.units.erase(unit)
			unit.free()
	for unit in [ally,enemy]:
		unit.target=null
		unit.attack_time=1000.0
		unit.attack_cooldown=1000.0
	ally.position=Vector3(-42,0,-7)
	enemy.position=Vector3(-40,0,-4)
	ally.previous_position=ally.position
	enemy.previous_position=enemy.position
	ally.receive_damage(100.0,"army")
	scene.army._rebuild_buckets()
	events.clear()
	return {"ally":ally,"enemy":enemy}

func advance(seconds: float) -> void:
	var remaining:=seconds
	while remaining>.000001:
		var delta:=minf(.05,remaining)
		scene.army.step_simulation(delta)
		fx.step(delta)
		remaining-=delta

func observed_receipts(kind: String="") -> Array:
	var result: Array=[]
	for event in events:
		for receipt in event.get("receipts",[]):
			if kind.is_empty() or receipt.get("kind")==kind:result.append(receipt)
	return result

func validate_receipts() -> Dictionary:
	var valid:=true
	var count:=0
	var last_sequence: Dictionary={}
	for event in events:
		valid=valid and not has_objects(event) and event.receipts.size()<=72
		var prior: int=last_sequence.get(event.epoch,-1)
		valid=valid and int(event.event_seq)>prior
		last_sequence[event.epoch]=event.event_seq
		for receipt in event.receipts:
			count+=1
			if receipt.has("health_before"):
				valid=valid and is_finite(receipt.health_before) and is_finite(receipt.health_after)
				var change: float=receipt.health_after-receipt.health_before+receipt.get("shield_after",0.0)-receipt.get("shield_before",0.0)
				var expected: float=receipt.get("healing_applied",0.0)-receipt.get("damage_applied",0.0)
				if not "shield" in receipt.get("effects",[]):valid=valid and absf(change-expected)<.001
	return {"valid":valid,"count":count,"events":events.size()}

func payload_cases() -> void:
	var damage:={"rama":32.0,"ravana":90.0,"arjuna":88.0,"duryodhana":92.0,"hanuman":65.0,"karna":95.0,"bhima":92.0,"meghnad":78.0,"ulupi":72.0}
	var healing:={"hanuman":45.0,"sita":54.0,"draupadi":95.0}
	for hero in HEROES:
		var fixture:=isolate_receivers()
		session.select_invocation(hero)
		var before:=receiver_snapshot()
		var result: Dictionary=session.request_cast(ORIGIN,FORWARD,TARGET)
		var initial_fx: Dictionary=fx.report()
		record("actual world session begins "+hero,result.get("accepted",false) and events.size()==1 and events[0].kind=="begin" and initial_fx.active==1,{"result":result,"fx_active":initial_fx.active})
		if not result.get("accepted",false):continue
		var timing: Dictionary=session.report().selected_rule.timing
		var first: float=timing.windup_s+timing.travel_s+.05
		var total: float=timing.windup_s+timing.travel_s+timing.active_s+timing.recovery_s+.10
		advance(first)
		var actual_summons: Array=scene.army.units.filter(func(u):return u.practice_summon and u.alive)
		if hero in ["subhadra","hidimbi"]:
			var expected_role: String="bow_guard" if hero=="subhadra" else "spearman"
			var expected_attack: float=28.0 if hero=="subhadra" else 32.0
			var pair_ok:=actual_summons.size()==2
			for unit in actual_summons:
				pair_ok=pair_ok and unit.role==expected_role and unit.health==105.0 and unit.attack_damage()==expected_attack and unit.core_damage()==0.0
				unit.attack_time=1000;unit.attack_cooldown=1000
			record("accepted temporary pair is actual bounded units "+hero,pair_ok,{"summons":actual_summons.size(),"receipts":observed_receipts("summon").size()})
		if hero in ["sita","chitrangada"]:
			var shield: float=70.0 if hero=="sita" else 80.0
			var health_before: float=fixture.ally.health
			var received: bool=fixture.ally.receive_damage(10.0,"army")
			record("invocation shield absorbs real later damage "+hero,received and fixture.ally.health==health_before and absf(fixture.ally.shield-(shield-10))<.001)
		advance(total-first)
		var enemy_expected: float=150.0-float(damage.get(hero,0.0))
		var ally_expected: float=50.0+float(healing.get(hero,0.0))
		var applied: bool=absf(fixture.enemy.health-enemy_expected)<.002 and absf(fixture.ally.health-ally_expected)<.002
		if hero in ["subhadra","hidimbi"]:applied=applied and scene.army.units.filter(func(u):return u.practice_summon).is_empty()
		record("actual payload and team isolation "+hero,applied,{"enemy_health":fixture.enemy.health,"expected_enemy":enemy_expected,"ally_health":fixture.ally.health,"expected_ally":ally_expected})
		var receipts:=validate_receipts()
		record("receipts lifecycle and cores remain honest "+hero,receipts.valid and receipts.count>0 and session.report().active_cast_id==0 and session.report().history_size<=64 and fx.report().active==0 and scene.army.cores==before.cores and scene.army.gold==before.gold,{"receipts":receipts,"history":session.report().history_size,"fx_active":fx.report().active})

func malformed_and_cooldown_cases() -> void:
	isolate_receivers()
	session.select_invocation("rama")
	var before:=receiver_snapshot()
	var invalids:=[{"origin":Vector3(NAN,0,0),"forward":FORWARD,"target":TARGET},
		{"origin":Vector3(1e30,0,0),"forward":FORWARD,"target":TARGET},
		{"origin":ORIGIN+Vector3.UP,"forward":FORWARD,"target":TARGET},
		{"origin":ORIGIN,"forward":Vector3.ZERO,"target":TARGET},
		{"origin":ORIGIN,"forward":Vector3(1e30,0,1e30),"target":TARGET},
		{"origin":ORIGIN,"forward":Vector3(INF,0,1),"target":TARGET},
		{"origin":ORIGIN,"forward":FORWARD,"target":Vector3(0,NAN,0)}]
	var rejected:=true
	for input in invalids:rejected=rejected and not session.request_cast(input.origin,input.forward,input.target).accepted
	record("malformed airborne and overflow aim reject before mutation",rejected and events.is_empty() and receiver_snapshot()==before and session.report().cooldown_remaining==0)
	session.select_invocation("ulupi")
	var invalid_target: Dictionary=session.request_cast(ORIGIN,FORWARD,ORIGIN+Vector3(0,0,40))
	record("aimed invocation rejects out of range target",not invalid_target.accepted and events.is_empty())
	session.select_invocation("rama")
	var accepted: Dictionary=session.request_cast(ORIGIN,FORWARD,TARGET)
	var cooldown: float=session.report().cooldown_remaining
	var count:=events.size()
	session.select_invocation("ravana")
	var repeated: Dictionary=session.request_cast(ORIGIN,FORWARD,TARGET)
	record("selection cannot bypass shared twelve second cooldown",accepted.accepted and cooldown==12.0 and not repeated.accepted and events.size()==count and session.report().cooldown_remaining==cooldown)
	advance(3.0)
	session.cancel_active("qa_cancel")
	record("cancellation preserves remaining cooldown",absf(session.report().cooldown_remaining-9.0)<.001)

func warning_and_attachment_cases() -> void:
	for hero in ["ravana","duryodhana","meghnad"]:
		isolate_receivers();session.select_invocation(hero);session.request_cast(ORIGIN,FORWARD,TARGET)
		fx.set_options({"reduced_effects":true,"reduced_motion":true})
		var state: Dictionary=fx.report().casts[0]
		var violations:=0
		for vertex in state.warning_vertices:
			var world_vertex: Vector3=state.warning_transform*vertex
			if not Rules.contains(state.geometry,world_vertex):violations+=1
		record("actual low-effects warning stays inside authority "+hero,state.warning_visible and violations==0,{"vertices":state.warning_vertices.size(),"outside":violations})
		var snapshot:=receiver_snapshot()
		var prior: Dictionary=fx.report()
		var repeated: bool=fx.consume_event(events[0])
		record("duplicate presentation cannot replay gameplay "+hero,not repeated and fx.report().active==prior.active and receiver_snapshot()==snapshot)
	isolate_receivers();session.select_invocation("chitrangada");session.request_cast(ORIGIN,FORWARD,TARGET);advance(.70)
	var ally=scene.army.units.filter(func(u):return u.team=="sun")[0]
	ally.position+=Vector3(1,0,0);ally.previous_position=ally.position
	advance(.05)
	var attachments: Array=fx.report().casts[0].attachments
	var matched:=false
	for row in attachments:matched=matched or (row.unit_id==ally.unit_id and row.kind=="shield" and row.position==ally.global_position)
	record("accepted shield follows actual receiver position",matched,{"attachments":attachments.size()})
	ally.receive_damage(100.0,"army");advance(.05)
	attachments=fx.report().casts[0].attachments
	record("depleted shield attachment retires on next authoritative step",attachments.all(func(a):return a.unit_id!=ally.unit_id))
	fx.set_options({"reduced_effects":false,"reduced_motion":false})

func world_control_cases() -> void:
	isolate_receivers();session.select_invocation("rama");session.request_cast(ORIGIN,FORWARD,TARGET)
	for mode in ["pause","overview","focus"]:
		if mode=="overview":scene.set_overview(true)
		elif mode=="focus":scene._focus_lost()
		else:scene.set_paused(true)
		var before: Dictionary=session.report()
		var effects_before: Dictionary=fx.report()
		await frames(5)
		var result: Dictionary=scene.cast_invocation()
		record("world "+mode+" freezes cooldown and presentation",not result.accepted and session.report().elapsed==before.elapsed and session.report().cooldown_remaining==before.cooldown_remaining and fx.report().casts==effects_before.casts and fx.report().suspended)
		if mode=="overview":scene.set_overview(false)
		else:scene.set_paused(false)
	var cooldown: float=session.report().cooldown_remaining
	scene._open_invocations();await frames(3)
	var selected: String=session.report().selected_hero
	scene.invocation_panel.hero_buttons["sita"].pressed.emit();await frames(2)
	record("panel preview does not alter accepted selection or cooldown",scene.invocation_panel.report().preview_id=="sita" and session.report().selected_hero==selected and session.report().cooldown_remaining==cooldown and paused)
	scene.invocation_panel.reduced_effects_button.button_pressed=true
	scene.invocation_panel.reduced_motion_button.button_pressed=true
	record("panel accessibility options reach actual presentation",fx.report().reduced_effects and fx.report().reduced_motion and fx.report().casts[0].warning_visible)
	scene.invocation_panel.reduced_effects_button.button_pressed=false
	scene.invocation_panel.reduced_motion_button.button_pressed=false
	scene.invocation_panel.choose_button.pressed.emit();await frames(3)
	record("panel choose routes through real session",session.report().selected_hero=="sita" and not scene.invocation_panel.visible and not paused and session.report().cooldown_remaining==cooldown)
	var first_epoch: int=session.report().epoch
	scene._restart_army();await frames(3)
	record("world restart clears cast effects and resets shared cooldown",session.report().epoch>first_epoch and session.report().active_cast_id==0 and session.report().cooldown_remaining==0 and fx.report().active==0 and scene.army.report().alive==30)

func authority_clock_case() -> void:
	isolate_receivers();session.select_invocation("rama")
	scene.teleport_to(ORIGIN,0.0)
	scene.player.yaw=PI
	scene.player.pitch=-.25
	scene.player._update_camera()
	scene.player.set_physics_process(true)
	for _index in range(12):await physics_frame
	scene.player.set_physics_process(false)
	var result: Dictionary=scene.cast_invocation()
	record("actual world cast entry begins grounded preparation",result.get("accepted",false) and scene.player.is_on_floor() and scene.player.invocation_preparing,{"result":result,"position":str(scene.player.position)})
	if not result.get("accepted",false):return
	var before: Vector3=scene.player.position
	var shots: int=scene.player.shots_fired
	Input.action_press("move_forward");Input.action_press("fire")
	for _index in range(12):scene.player._physics_process(.1)
	Input.action_release("move_forward");Input.action_release("fire")
	var displacement:=Vector2(scene.player.position.x-before.x,scene.player.position.z-before.z).length()
	record("late authority step cannot unlock from cosmetic player clock",session.report().active_phase=="windup" and scene.player.invocation_preparing and scene.player.invocation_remaining==0 and scene.player.shots_fired==shots and displacement<.001 and not scene.player.shoot(),{"displacement":displacement,"session_phase":session.report().active_phase})
	advance(.95)
	record("preparation remains locked before release receipt",scene.player.invocation_preparing and not scene.player.toggle_flight() and not scene.player.try_grapple() and not scene.player.shoot())
	advance(.05)
	record("authoritative release unlocks player actions",not scene.player.invocation_preparing and scene.player.shoot())
	var preparing: bool=scene.player.invocation_preparing
	var active_clip: String=scene.player.active_clip
	var rejected: Dictionary=scene.cast_invocation()
	record("cooldown rejection does not restart preparation",not rejected.accepted and scene.player.invocation_preparing==preparing and scene.player.active_clip==active_clip)

func hud_notice_and_layout_cases() -> void:
	var fixture:=isolate_receivers()
	# A real cast with no eligible receivers reproduces the packaged-window bug:
	# no impact receipt may be relied upon to replace the preparation notice.
	fixture.ally.position=Vector3(42,0,50)
	fixture.enemy.position=Vector3(40,0,50)
	for unit in [fixture.ally,fixture.enemy]:unit.previous_position=unit.position
	scene.army._rebuild_buckets()
	session.select_invocation("rama")
	scene.teleport_to(ORIGIN,0.0)
	scene.player.yaw=PI
	scene.player.pitch=-.25
	scene.player._update_camera()
	scene.player.set_physics_process(true)
	for _index in range(12):await physics_frame
	scene.player.set_physics_process(false)
	var accepted: Dictionary=scene.cast_invocation()
	scene._process(.13) # Exercise the actual periodic HUD refresh, not a label assignment.
	record("zero-hit world cast HUD announces authoritative preparation",accepted.get("accepted",false) and events.any(func(event):return event.kind=="begin") and session.report().active_phase=="windup" and scene.player.invocation_preparing and scene.invocation_notice=="Preparing · aim locked" and scene.invocation_detail.text.ends_with(scene.invocation_notice),{"notice":scene.invocation_notice,"detail":scene.invocation_detail.text})
	advance(1.0)
	scene._process(.13)
	record("zero-hit release removes stale preparation notice and unlocks actions",events.any(func(event):return event.kind=="release") and observed_receipts().is_empty() and not scene.player.invocation_preparing and scene.invocation_notice=="Released · movement restored" and scene.invocation_detail.text.ends_with(scene.invocation_notice) and not "Preparing" in scene.invocation_detail.text,{"notice":scene.invocation_notice,"receipts":observed_receipts().size()})
	advance(3.0)
	scene._process(.13)
	record("zero-hit completion announces end without inventing troop effects",events.any(func(event):return event.kind=="end") and observed_receipts().is_empty() and session.report().active_cast_id==0 and scene.invocation_notice=="Invocation ended" and scene.invocation_detail.text.ends_with(scene.invocation_notice),{"notice":scene.invocation_notice,"receipts":observed_receipts().size()})
	scene._restart_army()
	scene._process(.13)
	record("round reset restores ready notice and ready HUD",events.back().kind=="reset" and session.report().cooldown_remaining==0 and not scene.player.invocation_preparing and scene.invocation_notice=="Ready · aim, then cast" and scene.invocation_detail.text.ends_with(scene.invocation_notice) and scene.invocation_label.text.ends_with("READY"),{"notice":scene.invocation_notice,"heading":scene.invocation_label.text})
	var card: Control=scene.hud.find_child("InvocationStatus",true,false)
	var old_size:=root.size
	var old_scale:=root.content_scale_size
	for dimensions in [Vector2i(960,600),Vector2i(1280,720)]:
		root.size=dimensions
		root.content_scale_size=dimensions
		await frames(4)
		var view:=root.get_visible_rect()
		var card_rect:=card.get_global_rect()
		var overlaps:=[]
		for other_name in ["TitleCard","RelayStatus","ControlsCard","TraversalStatus","AtlasLegend","Crosshair"]:
			var other: Control=scene.hud.find_child(other_name,true,false)
			if other!=null and other.is_visible_in_tree() and card_rect.intersects(other.get_global_rect()):overlaps.append(other_name)
		# This central lower band is a layout reserve, not a measured hero silhouette.
		var centre_reserve:=Rect2(Vector2(view.size.x*.5-100,view.size.y*.5),Vector2(200,view.size.y*.5))
		var expected:=Vector2(20,view.size.y-206)
		var contained:=card_rect.encloses(scene.invocation_label.get_global_rect()) and card_rect.encloses(scene.invocation_detail.get_global_rect())
		record("invocation HUD lower-left slot fits logical "+str(dimensions),view.size.is_equal_approx(Vector2(dimensions)) and view.encloses(card_rect) and card_rect.position.is_equal_approx(expected) and card_rect.size.is_equal_approx(Vector2(330,100)) and contained and overlaps.is_empty() and not card_rect.intersects(centre_reserve),{"viewport":str(view),"card":str(card_rect),"overlaps":overlaps,"labels_contained":contained,"central_reserve":str(centre_reserve)})
	root.size=old_size
	root.content_scale_size=old_scale
	await frames(3)

func pause_action_visible(control: Control) -> bool:
	return control.is_visible_in_tree() and scene.pause_scroll.get_global_rect().grow(.5).encloses(control.get_global_rect())

func pause_focus_cases() -> void:
	var old_size:=root.size
	var old_scale:=root.content_scale_size
	var first: Control=scene.pause_actions[0]
	var last: Control=scene.pause_actions[-1]
	for dimensions in [Vector2i(960,600),Vector2i(1280,720)]:
		root.size=dimensions
		root.content_scale_size=dimensions
		for operation in ["repeat pause","focus loss","reopen"]:
			scene.set_paused(true)
			await frames(6)
			scene.pause_scroll.scroll_vertical=10000
			await frames(4)
			# Do not repair focus/scroll between this precondition and the check.
			var clipped_with_same_focus:=first.has_focus() and not pause_action_visible(first)
			var before:=str(first.get_global_rect())
			if operation=="focus loss":scene._focus_lost()
			elif operation=="reopen":
				scene.set_paused(false)
				scene.set_paused(true)
			else:scene.set_paused(true)
			await frames(8)
			record("same-focus clipped Continue revealed on "+operation+" "+str(dimensions),clipped_with_same_focus and first.has_focus() and pause_action_visible(first) and scene.paused and paused,{"precondition_clipped":clipped_with_same_focus,"before":before,"after":str(first.get_global_rect()),"scroll":str(scene.pause_scroll.get_global_rect())})
		scene.set_paused(true)
		last.grab_focus()
		await frames(8)
		record("deferred pause reveal preserves a newer focused action "+str(dimensions),last.has_focus() and pause_action_visible(last),{"focused":str(root.gui_get_focus_owner()),"rect":str(last.get_global_rect())})
		scene.set_paused(true)
		scene.set_paused(false)
		await frames(8)
		record("deferred pause reveal cannot reacquire focus after resume "+str(dimensions),not paused and not scene.paused and not scene.pause_panel.visible and root.gui_get_focus_owner()==null and scene.player.active)
	# Open modals before queued pause callbacks execute, then lose OS focus while
	# they are already open. Neither immediate nor deferred pause focus may win.
	root.size=Vector2i(960,600)
	root.content_scale_size=Vector2i(960,600)
	scene.set_paused(true)
	scene._open_invocations()
	await frames(8)
	var selected: String=session.report().selected_hero
	record("pending pause reveal preserves invocation modal initial focus",scene.invocation_panel.visible and not scene.pause_panel.visible and scene.invocation_panel.hero_buttons[selected].has_focus())
	var hero_focus: Control=scene.invocation_panel.hero_buttons.sita
	hero_focus.grab_focus()
	scene._focus_lost()
	await frames(8)
	record("focus loss preserves current invocation modal keyboard target",scene.invocation_panel.visible and not scene.pause_panel.visible and hero_focus.has_focus() and hero_focus.is_visible_in_tree() and paused)
	scene.invocation_panel.close()
	await frames(8)
	record("selector close returns visible focus to its pause-menu action",not scene.invocation_panel.visible and scene.pause_panel.visible and scene.invocation_button.has_focus() and pause_action_visible(scene.invocation_button))
	scene.set_paused(true)
	scene._open_controls()
	await frames(8)
	record("pending pause reveal preserves controls modal initial focus",scene.controls_overlay.visible and not scene.pause_panel.visible and scene.controls_overlay.binding_buttons.move_forward.has_focus())
	scene.controls_overlay.begin_capture("grapple")
	scene._focus_lost()
	await frames(8)
	var binding_focus: Control=scene.controls_overlay.binding_buttons.grapple
	record("focus loss cancels key capture without stealing controls focus",scene.controls_overlay.visible and not scene.pause_panel.visible and scene.controls_overlay.capture_action.is_empty() and binding_focus.has_focus() and binding_focus.is_visible_in_tree() and paused)
	scene.controls_overlay.close()
	await frames(8)
	record("controls close restores a fully visible Continue action",not scene.controls_overlay.visible and scene.pause_panel.visible and first.has_focus() and pause_action_visible(first))
	scene.set_paused(false)
	root.size=old_size
	root.content_scale_size=old_scale
	await frames(4)

func on_reset_during_defeat(_unit: Node3D,_by_player: bool) -> void:
	scene.army.reset()

func reset_and_reconfigure_cases() -> void:
	var fixture:=isolate_receivers()
	session.select_invocation("ravana")
	fixture.enemy.receive_damage(100.0,"army")
	fixture.enemy.defeated.connect(on_reset_during_defeat)
	var accepted: Dictionary=session.request_cast(ORIGIN,FORWARD,TARGET)
	var old_begin: Dictionary=events[0].duplicate(true)
	advance(1.0)
	var clean:=true
	for event in events:
		if event.epoch>accepted.epoch:clean=clean and event.kind=="reset" and event.receipts.is_empty()
	for unit in scene.army.units:clean=clean and unit.alive and unit.health==unit.max_health
	record("defeat callback reset cannot free locked emitter or cross epochs",clean and session.report().epoch>accepted.epoch and scene.army.report().alive==30 and session.report().applied_receipts>=0,{"events":events.map(func(e):return {"kind":e.kind,"epoch":e.epoch,"cast_id":e.cast_id,"receipts":e.receipts.size()})})
	var snapshot:=receiver_snapshot()
	record("old epoch presentation cannot revive after reset",not fx.consume_event(old_begin) and fx.report().active==0 and receiver_snapshot()==snapshot)
	fixture=isolate_receivers();session.select_invocation("chitrangada");session.request_cast(ORIGIN,FORWARD,TARGET);advance(.7)
	var shield_before: float=fixture.ally.shield
	var state_before: Dictionary=session.report()
	var invalid:=Node3D.new()
	var rejected: bool=not session.configure(invalid)
	invalid.free()
	record("invalid reconfigure preserves live session",rejected and session.report()==state_before and fixture.ally.shield==shield_before)
	var foreign=load("res://scripts/lane_army.gd").new()
	foreign.visual_enabled=false;root.add_child(foreign);foreign.set_physics_process(false);foreign.configure(scene.manifest,null)
	var connected: bool=session.configure(foreign)
	record("successful reconfigure clears previous receivers and subscriptions",connected and shield_before==80 and fixture.ally.shield==0 and scene.army.simulation_stepped.get_connections().is_empty() and foreign.simulation_stepped.get_connections().size()==1)
	session.configure(scene.army)
	foreign.free()
	var bounded:=true
	var connection_count: int=scene.army.simulation_stepped.get_connections().size()
	for _index in range(24):
		scene._restart_army()
		bounded=bounded and scene.army.units.size()==30 and scene.army.get_child_count()==30 and scene.army.simulation_stepped.get_connections().size()==connection_count and fx.report().active==0 and session.report().history_size==1
	record("repeated real world resets do not accumulate units casts or callbacks",bounded,{"callbacks":connection_count,"army_children":scene.army.get_child_count()})

func population_receipt_case() -> void:
	isolate_receivers()
	for unit in scene.army.units.duplicate():scene.army.units.erase(unit);unit.free()
	var specs: Array=[]
	for row in range(9):
		for column in range(8):specs.append({"team":"moon","role":"commander","lane":1,"progress":122.0-row,"lateral":float(column)-3.5})
	scene.army.visual_enabled=false
	var spawned: bool=scene.army._spawn_specifications(specs)
	scene.army.visual_enabled=true
	for unit in scene.army.units:unit.attack_time=1000;unit.attack_cooldown=1000
	scene.army._rebuild_buckets()
	session.select_invocation("ulupi")
	var result: Dictionary=session.request_cast(Vector3(0,0,-10),FORWARD,Vector3(0,0,-6))
	advance(.95)
	var ticks: Array=events.filter(func(e):return e.kind=="tick")
	var receipts: Array=ticks[-1].receipts if not ticks.is_empty() else []
	var unique: Dictionary={}
	for receipt in receipts:unique[receipt.unit_id]=true
	var actual:=true
	for unit in scene.army.units:actual=actual and absf(unit.health-149.4)<.002 and unit.movement_multiplier()==.55
	record("seventy two receivers retain complete combined damage and slow receipts",spawned and result.accepted and scene.army.units.size()==72 and receipts.size()==72 and unique.size()==72 and actual,{"units":scene.army.units.size(),"receipts":receipts.size(),"unique":unique.size()})
	advance(6.1)
	actual=true
	for unit in scene.army.units:actual=actual and absf(unit.health-78.0)<.004
	record("full population zone is clipped to exact duration and bounded history",actual and session.report().history_size<=64 and fx.report().finite and validate_receipts().valid,{"history":session.report().history_size})
	scene._restart_army()

func audio_integration_cases() -> void:
	isolate_receivers()
	var audio=scene.invocation_audio
	scene._set_volume(.35,false)
	var before: Dictionary=audio.report()
	session.select_invocation("rama");session.request_cast(ORIGIN,FORWARD,TARGET)
	var begin: Dictionary=audio.report()
	record("real begin routes to bounded original audio pool",begin.ready and begin.players==3 and begin.streams==16 and begin.played==before.played+1 and begin.active.hero=="rama" and begin.voices.any(func(v):return v.cue=="windup.wav"))
	advance(1.0)
	var release: Dictionary=audio.report()
	record("real release chooses the selected invocation cue",release.played==begin.played+1 and release.voices.any(func(v):return v.cue=="rama-release.wav"))
	var release_event: Dictionary=events.filter(func(e):return e.kind=="release")[-1]
	var duplicate: Dictionary=audio.consume_event(release_event)
	record("duplicate receipt cannot replay sound",not duplicate.ok and audio.report().played==release.played)
	scene._set_volume(0.0,false)
	isolate_receivers();session.select_invocation("ravana")
	before=audio.report();session.request_cast(ORIGIN,FORWARD,TARGET)
	record("world volume zero mutes cues while warning remains",audio.report().volume==0 and audio.report().playing==0 and audio.report().played==before.played and audio.report().suppressed>before.suppressed and fx.report().active==1 and fx.report().casts[0].warning_visible)
	scene._set_volume(.35,false)
	isolate_receivers();session.select_invocation("chitrangada");session.request_cast(ORIGIN,FORWARD,TARGET)
	scene.set_paused(true);await frames(3)
	before=audio.report()
	record("world pause stops voices and suspends invocation audio",before.suspended and before.playing==0)
	scene.set_paused(false);advance(.65)
	record("resume admits only the next real release cue",not audio.report().suspended and audio.report().played==before.played+1 and audio.report().voices.any(func(v):return v.cue=="chitrangada-release.wav"))
	session.cancel_active("qa_audio_cancel")
	var cancelled: Dictionary=audio.report()
	record("cancellation retires cast and stops prior audio cues",cancelled.active.is_empty() and cancelled.voices.all(func(v):return not v.playing or v.cue=="cancel.wav"))
	var invalid: Dictionary=release_event.duplicate(true)
	invalid.time_s=NAN;invalid.event_seq+=10000
	var malformed: Dictionary=audio.consume_event(invalid)
	record("malformed audio receipt cannot add playback",not malformed.ok and audio.report().played==cancelled.played)
	scene._restart_army()
	record("world restart clears active audio and bounded voice ownership",audio.report().playing==0 and audio.report().active.is_empty() and audio.report().players==3 and audio.get_child_count()==3)

func run() -> void:
	baseline_nodes=int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))
	for path in SOURCE_PATHS:source_hashes[path]=FileAccess.get_sha256(path)
	var audio_manifest=JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/invocations/manifest.json"))
	if audio_manifest is Dictionary:
		for file_name in audio_manifest.get("files",{}):
			var path: String="res://assets/audio/invocations/"+file_name
			source_hashes[path]=FileAccess.get_sha256(path)
	root.size=Vector2i(1280,720)
	scene=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene)
	await frames(5)
	session=scene.invocations;fx=scene.ultimate_fx
	record("real native world owns invocation modules",scene.world_ready and session!=null and fx!=null and scene.invocation_panel!=null)
	if session==null or fx==null:await finish();return
	for node in [fx,scene.invocation_panel]:source_hashes[node.get_script().resource_path]=FileAccess.get_sha256(node.get_script().resource_path)
	scene.set_process(false);scene.set_physics_process(false);scene.army.set_physics_process(false);scene.player.set_physics_process(false);fx.set_process(false)
	session.invocation_event.connect(collect_event)
	record("catalogue exposes fourteen invocation buttons",scene.invocation_panel.hero_buttons.size()==14 and HEROES.all(func(id):return scene.invocation_panel.hero_buttons.has(id)))
	payload_cases()
	malformed_and_cooldown_cases()
	warning_and_attachment_cases()
	await authority_clock_case()
	await world_control_cases()
	reset_and_reconfigure_cases()
	population_receipt_case()
	await audio_integration_cases()
	await hud_notice_and_layout_cases()
	await pause_focus_cases()
	record("bounded test event capture",not event_overflow)
	await finish()

func finish() -> void:
	paused=false
	if is_instance_valid(scene):
		var scene_id:=scene.get_instance_id()
		var session_id:=session.get_instance_id() if is_instance_valid(session) else 0
		var fx_id:=fx.get_instance_id() if is_instance_valid(fx) else 0
		var audio_id: int=scene.invocation_audio.get_instance_id()
		scene.queue_free()
		await frames(4)
		OS.delay_msec(100)
		await frames(2)
		record("scene disposal frees session effects audio and owned nodes",not is_instance_id_valid(scene_id) and not is_instance_id_valid(session_id) and not is_instance_id_valid(fx_id) and not is_instance_id_valid(audio_id) and int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))==baseline_nodes,{"baseline_nodes":baseline_nodes,"remaining_nodes":int(Performance.get_monitor(Performance.OBJECT_NODE_COUNT))})
	var stable:=true
	for path in source_hashes:stable=stable and source_hashes[path]==FileAccess.get_sha256(path)
	if not source_hashes.is_empty():record("integration sources remain frozen",stable)
	var passed:=not checks.is_empty()
	for entry in checks:passed=passed and entry.passed
	var report={"passed":passed,"checks":checks,"sources":source_hashes,"engine":Engine.get_version_info().string,
		"scope":"Headless real native world, actual invocation session and troop receivers, bounded presentation lifecycle and source-pinned fixtures. No rendered quality, listening, hardware performance, online match, fourteen production avatars or competitive balance acceptance."}
	var file:=FileAccess.open(output,FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(report,"\t")+"\n")
	else:passed=false
	print("MYTHIC_INTEGRATION ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
