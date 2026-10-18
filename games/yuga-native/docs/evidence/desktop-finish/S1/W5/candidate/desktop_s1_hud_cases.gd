extends "res://tests/ui_i1_action_hud_cases.gd"
## New S1 action-feedback witnesses on the real kit and one real pending intent.
var edge := 1000

func hud_frame() -> Dictionary:
	# A semantic change must show even below the old80ms formatting interval.
	scene.rama_hud.clock=0
	scene.rama_hud._process(.001)
	var text := []
	for slot in scene.rama_hud.slots:text.append(slot.text)
	return {"note":scene.rama_hud.note.text,"slots":text,"kit":scene.rama_runtime.kit.report(),"buffer":scene.rama_runtime.action_buffer.report()}

func queue_volley() -> Dictionary:
	for unused in 17:advance()
	edge+=1
	return scene.rama_runtime.request_input_ability("dawn_volley",edge)

func run() -> void:
	for path in ["res://scripts/rama_motion.gd","res://scripts/rama_hero_hud.gd","res://scripts/player.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_action_buffer.gd",get_script().resource_path]:source_start[path]=FileAccess.get_sha256(path)
	scene=load("res://scenes/confluence_world.tscn").instantiate()
	root.add_child(scene);current_scene=scene
	await frames()
	scene.rama_runtime.set_volume(0)
	scene.rama_runtime.combat_event.connect(func(event:Dictionary):events.append(event.duplicate(true)))
	await ground_fixture()
	var response: Dictionary=scene.cast_rama_ability("piercing_dawn")
	var view:=hud_frame()
	check("accepted windup displays DRAWING on the next process frame",response.get("accepted",false) and view.kit.action_locked and view.note.contains("DRAWING"),view)
	check("other available slots say BUSY during the authoritative lock",view.slots[2].contains("BUSY") and view.slots[3].contains("BUSY") and view.slots[4].contains("BUSY") and not view.slots.any(func(text):return text.contains("READY")),view)
	edge+=1
	var early:Dictionary=scene.rama_runtime.request_input_ability("dawn_volley",edge)
	view=hud_frame()
	check("rejected early input never appears as QUEUED",not early.get("queued",false) and not view.slots[4].contains("QUEUED") and view.note.contains("DRAWING"),view)
	var kit_before:Dictionary=scene.rama_runtime.kit.report()
	var buffer_before:Dictionary=scene.rama_runtime.action_buffer.report()
	var motion_before:Dictionary=scene.player.rama_motion.diagnostics()
	var army_before:float=scene.army.elapsed
	for unused in 20:scene.rama_hud._process(.001)
	check("HUD observation cannot advance or dispatch any action",kit_before==scene.rama_runtime.kit.report() and buffer_before==scene.rama_runtime.action_buffer.report() and motion_before==scene.player.rama_motion.diagnostics() and army_before==scene.army.elapsed)
	var queued:=queue_volley()
	view=hud_frame()
	check("actual released recovery is labelled RECOVERING",view.kit.action_locked and view.kit.release_count==1 and view.note.contains("RECOVERING"),view)
	check("one genuine near-recovery intent displays QUEUED",queued.get("queued",false) and view.slots[4].contains("QUEUED") and view.note.contains("Dawn Volley") and view.buffer.pending.ability_id=="dawn_volley",view)
	check("active cooldown and bow stock remain visible",view.slots[1].contains("%.1fs"%float(view.kit.cooldowns.piercing_dawn)) and view.slots[0].replace(" ","").contains("12/12"),view)
	scene.set_overview(true)
	view=hud_frame()
	check("overview clears queued presentation and takes precedence",view.note=="Practice paused" and view.buffer.pending.is_empty() and not view.slots.any(func(text):return text.contains("QUEUED") or text.contains("BUSY") or text.contains("READY")),view)
	scene.set_overview(false)
	view=hud_frame()
	check("resume shows held recovery without reviving the cleared intent",view.note.contains("RECOVERING") and not view.slots[4].contains("QUEUED"),view)
	scene.rama_runtime.reset("S1 real generation change")
	view=hud_frame()
	check("generation reset clears active and pending HUD states immediately",not view.kit.action_locked and view.buffer.pending.is_empty() and view.slots[4].contains("READY") and view.note=="Rama is ready",view)
	await ground_fixture()
	scene.cast_rama_ability("piercing_dawn")
	queued=queue_volley()
	advance();advance()
	view=hud_frame()
	check("queue dispatch becomes the actual new draw exactly once",queued.get("queued",false) and count("begin")==2 and view.kit.active_ability=="dawn_volley" and view.buffer.pending.is_empty() and view.note.contains("Dawn Volley") and view.note.contains("DRAWING") and not view.slots[4].contains("QUEUED"),view)
	scene.rama_runtime.kit.cancel_windup("S1 public cancel")
	view=hud_frame()
	check("public cancel retires phase state without resetting cooldown",not view.kit.action_locked and view.note=="Action cancelled" and float(view.kit.cooldowns.dawn_volley)>0 and not view.slots[4].contains("QUEUED"),view)
	await ground_fixture()
	var actual_release_before:int=scene.rama_runtime.kit.report().release_count
	scene.cast_rama_ability("measured_step")
	advance()
	var no_early_release:=count("release")==0
	advance()
	check("actual Measured Step authority releases once at100ms",no_early_release and count("release")==1 and scene.rama_runtime.kit.report().release_count==actual_release_before+1 and scene.player.rama_motion.action_stage=="recovery",{"events":events.filter(func(event):return event.kind in ["begin","release"])})
	var damage:Dictionary=scene.rama_runtime.vitals.receive_damage(1000,"S1 death",scene.rama_runtime.vitals.generation,1)
	view=hud_frame()
	check("defeat takes precedence over an interrupted action",damage.accepted and view.note.begins_with("RETURNING") and not view.slots.any(func(text):return text.contains("BUSY") or text.contains("READY") or text.contains("QUEUED")),view)
	scene.rama_runtime.reset("S1 reset after defeat")
	scene.player.active=true
	scene.army.cores={"sun":100.0,"moon":0.0};scene.army.step_simulation(STEP)
	view=hud_frame()
	check("terminal outcome takes precedence over all action feedback",view.note=="Round ended · Sun victory" and not view.slots.any(func(text):return text.contains("BUSY") or text.contains("READY") or text.contains("QUEUED")),view)
	# Preserve the real runtime but detach it, then destroy it while HUD survives.
	var runtime:Node3D=scene.rama_runtime
	runtime.get_parent().remove_child(runtime)
	scene.rama_hud.clock=0;scene.rama_hud._process(.001)
	check("detached runtime is unavailable on the next HUD frame",scene.rama_hud.note.text=="Practice unavailable")
	runtime.free()
	scene.rama_hud._process(.001)
	check("disposed runtime leaves no stale action or resource labels",scene.rama_hud.note.text=="Practice unavailable" and scene.rama_hud.life_text.text=="—")
	var stable:=true
	for path in source_start:stable=stable and FileAccess.get_sha256(path)==source_start[path]
	check("owned action sources and fixture remain stable",stable)
	var result:={"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"sources":source_start,"scope":"Fresh real imported world/runtime/kit/buffer integration with controlled army ticks and manual HUD process callbacks. No screenshot, native key input, continuous motion or hardware acceptance."}
	DirAccess.make_dir_recursive_absolute(output.get_base_dir())
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;scene.queue_free()
	await frames(8)
	OS.delay_msec(80)
	await process_frame
	quit(0 if result.passed else 1)
