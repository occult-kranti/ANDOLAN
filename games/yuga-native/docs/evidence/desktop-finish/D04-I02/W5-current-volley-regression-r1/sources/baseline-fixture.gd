extends SceneTree
## One uncovered combined boundary: pause after Volley onset1, lethal after
## onset2, then same-instance restart. Actual world/kit/vitals/subscribers;
## fixed authority inputs and native pause frames, no raster/listening claim.
var output := "/tmp/desktop-i02-volley-feedback.json"
var scene: Node3D
var events: Array[Dictionary] = []
var checks: Array[Dictionary] = []
var timeline: Array[Dictionary] = []
var sources := {}
var run_before := {}
var warmup_ticks := 200

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
		if arg.begins_with("--warmup-ticks="):warmup_ticks=int(arg.trim_prefix("--warmup-ticks="))
	call_deferred("run")

func check(label: String, okay: bool, details: Dictionary={}) -> void:
	checks.append({"name":label,"passed":okay,"details":details})
	print("PASS " if okay else "FAIL ",label)

func pins() -> Dictionary:
	var result:={}
	for path in sources:result[path]=FileAccess.get_sha256(path)
	return result

func quiet() -> void:
	scene.set_process(false);scene.set_physics_process(false)
	scene.player.set_physics_process(false);scene.army.set_physics_process(false)
	scene.rama_effects.set_process(false);scene.rama_hud.set_process(false)
	scene.army._decision_clock=100000.0;scene.army._next_wave=100000.0
	for unit in scene.army.units.duplicate():scene.army.units.erase(unit);unit.free()
	scene.army._attacks.clear();scene.army._rebuild_buckets()

func ground() -> void:
	scene.teleport_to(Vector3(-40,.05,-10),0)
	scene.player.yaw=PI;scene.player.pitch=-.32;scene.player._update_camera()
	scene.player.set_physics_process(true)
	for unused in 8:await physics_frame
	scene.player.set_physics_process(false)

func advance(ticks: int) -> void:
	for unused in ticks:
		scene.army.step_simulation(.05)
		present()
	scene.rama_hud._process(.001)

func present() -> void:
	for frame in 3:
		scene.player._physics_process(1.0/60)
		scene.rama_effects.step(1.0/60)

func event_count(kind: String, generation: int, cast_id: int) -> int:
	return events.filter(func(e):return e.kind==kind and e.generation==generation and e.cast_id==cast_id).size()

func snapshot(label: String) -> Dictionary:
	var runtime: Node3D=scene.rama_runtime
	var row:={"label":label,"army_elapsed":scene.army.elapsed,"kit":runtime.kit.report(),"audio":runtime.action_audio.report(),"effects":runtime.effects.report(),"vitals":runtime.vitals.report(),"motion":scene.player.rama_motion.diagnostics(),"hud_note":scene.rama_hud.note.text,"hud_slots":scene.rama_hud.slots.map(func(slot):return slot.text),"physics_frame":Engine.get_physics_frames(),"process_frame":Engine.get_process_frames()}
	var arrows: Array=[]
	var contours: Array=[]
	for cast_ in runtime.effects._casts.values():
		var mesh: Mesh=cast_.accent.mesh
		contours.append({"cast_id":cast_.cast_id,"presentation_age_s":cast_.age,"geometry_frame":cast_.last_geometry_frame,"indices":mesh.surface_get_array_index_len(0) if mesh.get_surface_count()>0 else 0})
		for index in cast_.arrows.size():
			var point: Vector3=cast_.arrows[index].root.global_position
			arrows.append({"cast_id":cast_.cast_id,"index":index,"visible":cast_.arrows[index].root.visible,"authority_after_s":float(cast_.authority_age)-float(cast_.release_age_s),"presentation_after_s":float(cast_.age)-float(cast_.release_age_s),"delay_s":cast_.geometry.projectiles[index].delay_s,"terminal_contact":cast_.contacts.has(index),"position":[point.x,point.y,point.z]})
	row["arrows"]=arrows;row["contours"]=contours
	timeline.append(row.duplicate(true));return row

func run() -> void:
	for path in [get_script().resource_path,"res://scripts/confluence_world.gd","res://scripts/player.gd","res://scripts/rama_hero_runtime.gd","res://scripts/rama_ability_kit.gd","res://scripts/rama_vitals.gd","res://scripts/rama_ability_effects.gd","res://scripts/rama_action_audio.gd","res://scripts/rama_action_buffer.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_motion.gd","res://assets/design/rama-ability-kit.json","res://assets/audio/rama-quality/manifest.json","res://assets/heroes/rama-hero.glb","res://assets/heroes/rama-hero.glb.import"]:sources[path]=""
	var imports:=ConfigFile.new()
	if imports.load("res://assets/heroes/rama-hero.glb.import")==OK:
		for path in imports.get_value("deps","dest_files",[]):sources[path]=""
	run_before=pins()
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	for unused in 5:await process_frame
	quiet();scene.set_overview(false);scene.set_paused(false);root.focus_entered.emit()
	scene._restart_army();quiet();await ground()
	var runtime: Node3D=scene.rama_runtime
	var audio: Node3D=runtime.action_audio
	runtime.set_volume(.35)
	runtime.combat_event.connect(func(e: Dictionary):events.append(e.duplicate(true)))
	check("Exact frozen motion and actual imported world ready",run_before["res://scripts/rama_motion.gd"]=="8c3771a343a0538d749147393d0c407b1fb377d774a91b4cf99734e4852520f8" and runtime.configured and scene.player.is_on_floor() and audio.report().ready and not audio.report().suspended)
	for unused in warmup_ticks:scene.army.step_simulation(.05)
	var before:=snapshot("ready")
	var accepted: Dictionary=scene.cast_rama_ability("dawn_volley")
	var gen: int=accepted.get("generation",-1);var cast: int=accepted.get("cast_id",-1)
	var draw:=snapshot("draw accepted")
	check("One accepted Volley creates one draw across authority audio and effects",accepted.get("accepted",false) and event_count("begin",gen,cast)==1 and draw.audio.played==before.audio.played+1 and draw.effects.active==1 and draw.kit.action_locked,{"accepted":accepted})
	var ticks:=0
	while event_count("release",gen,cast)==0 and ticks<25:advance(1);ticks+=1
	var first:=snapshot("first release before pause")
	check("First eligible release produces one onset and one committed effect",event_count("release",gen,cast)==1 and first.audio.played==draw.audio.played+1 and first.effects.live_arrows==1 and first.effects.casts[0].released and first.hud_note.contains("RECOVERING"),{"authority_ticks":ticks})
	scene.set_paused(true)
	# Enable real callbacks while paused, rather than relying on fixture-disabled processing.
	scene.army.set_physics_process(true);scene.player.set_physics_process(true);scene.rama_effects.set_process(true)
	scene.rama_hud._process(.001)
	var held:=snapshot("pause entry")
	for unused in 10:await process_frame
	scene.rama_hud._process(.001)
	var paused_row:=snapshot("after ten native paused frames")
	check("Native pause freezes the inter-pulse gap and visible geometry age",paused_row.army_elapsed==held.army_elapsed and paused_row.kit==held.kit and paused_row.effects==held.effects and paused_row.audio.played==held.audio.played and paused_row.audio.playing==0 and paused_row.hud_note=="Practice paused")
	scene.army.set_physics_process(false);scene.player.set_physics_process(false);scene.rama_effects.set_process(false)
	scene.set_paused(false);scene.rama_hud._process(.001)
	var resumed:=snapshot("resume before authority step")
	check("Resume emits no replay of draw or first release",resumed.audio.played==first.audio.played and resumed.audio.playing==0 and event_count("release",gen,cast)==1 and resumed.hud_note.contains("RECOVERING"))
	advance(1)
	var early:=snapshot("one authority tick after resume")
	check("Tick before second pulse stays silent",early.audio.played==first.audio.played and early.effects.live_arrows==1 and not early.arrows.any(func(arrow):return arrow.index>0 and arrow.visible))
	check("Both unreleased notches remain until the authoritative second pulse",early.contours[0].indices==first.contours[0].indices)
	scene.army.step_simulation(.05)
	var boundary:=snapshot("second authority boundary before presentation advances")
	# The authority clamp may add floating-point roundoff without advancing the
	# mesh frame. Preserve that delta; this check targets the actual cache key.
	var boundary_age_delta: float=boundary.contours[0].presentation_age_s-early.contours[0].presentation_age_s
	check("Authority boundary removes one notch even within the same presentation frame",absf(boundary_age_delta)<=1e-12 and boundary.contours[0].geometry_frame==early.contours[0].geometry_frame and boundary.contours[0].indices==early.contours[0].indices-72 and boundary.effects.live_arrows==2,{"presentation_age_delta_s":boundary_age_delta,"geometry_frame":boundary.contours[0].geometry_frame})
	present();scene.rama_hud._process(.001)
	var second:=snapshot("second pulse eligible")
	check("Second projectile boundary emits exactly one new cue without another release event",second.audio.played==first.audio.played+1 and second.effects.live_arrows==2 and event_count("release",gen,cast)==1)
	var lethal: Dictionary=runtime.vitals.receive_damage(1000,"i02-between-volley-pulses",runtime.vitals.generation,1)
	scene.rama_hud._process(.001)
	var dead:=snapshot("lethal before third pulse")
	check("Lethal receipt cancels Volley effects and audio before third cue",lethal.accepted and not dead.vitals.alive and dead.audio.playing==0 and dead.audio.played==second.audio.played and dead.audio.active_casts==0 and dead.effects.active==0 and dead.effects.live_arrows==0 and event_count("cancel",gen,cast)==1 and dead.hud_note.begins_with("RETURNING") and not dead.hud_slots.any(func(text):return text.contains("READY")))
	advance(3)
	var overdue:=snapshot("past cancelled third pulse deadline")
	check("Later live authority ticks cannot resurrect cancelled pulse or visual",overdue.audio.played==dead.audio.played and overdue.audio.playing==0 and overdue.effects.active==0 and overdue.effects.live_arrows==0 and event_count("release",gen,cast)==1 and not overdue.vitals.alive)
	scene._restart_army();quiet();await ground();scene.rama_hud._process(.001)
	var restarted:=snapshot("same instance restart")
	check("Restart clears defeated action feedback before another draw",restarted.vitals.alive and restarted.kit.generation>gen and restarted.audio.generation==restarted.kit.generation and restarted.audio.receiver_generation==restarted.vitals.generation and restarted.effects.active==0 and restarted.effects.impacts==0 and restarted.audio.playing==0 and restarted.hud_note=="Rama is ready")
	var next: Dictionary=scene.cast_rama_ability("dawn_volley")
	advance(3)
	var fresh:=snapshot("next generation windup after old pulse deadline")
	check("New generation reuses cast ID safely with exactly one fresh draw",next.get("accepted",false) and int(next.cast_id)==cast and int(next.generation)>gen and fresh.audio.played==restarted.audio.played+1 and event_count("release",int(next.generation),int(next.cast_id))==0 and fresh.effects.live_arrows==0 and fresh.effects.active==1 and fresh.hud_note.contains("DRAWING"))
	ticks=0
	while event_count("release",int(next.generation),int(next.cast_id))==0 and ticks<25:advance(1);ticks+=1
	var next_release:=snapshot("next generation first release")
	advance(4)
	var next_complete:=snapshot("next generation all three pulses eligible")
	check("Restart does not suppress the next normal three-pulse release",next_release.audio.played==restarted.audio.played+2 and next_release.effects.live_arrows==1 and next_complete.audio.played==restarted.audio.played+4 and next_complete.effects.live_arrows==3 and event_count("release",int(next.generation),int(next.cast_id))==1)
	for ability in ["kodanda","piercing_dawn"]:
		scene._restart_army();quiet();await ground()
		var start:=snapshot(ability+" ready")
		var request: Dictionary=scene.cast_rama_ability(ability)
		ticks=0
		while event_count("release",int(request.get("generation",-1)),int(request.get("cast_id",-1)))==0 and ticks<25:advance(1);ticks+=1
		var released:=snapshot(ability+" released")
		check(ability+" zero-delay arrow remains eligible on its accepted release",request.get("accepted",false) and released.effects.live_arrows==1 and released.audio.played==start.audio.played+2 and released.arrows[0].delay_s==0.0)
	check("Exact source and imported inputs stayed unchanged",pins()==run_before)
	var result:={"passed":checks.all(func(row):return row.passed),"checks":checks,"timeline":timeline,"events":events,"source_before":run_before,"source_after":pins(),"engine":Engine.get_version_info(),"warmup_ticks":warmup_ticks,"scope":"One actual imported Confluence instance, public cast/lethal/restart methods, declared fixed50ms authority ticks and3x60Hz player/effect steps, ten native paused process frames. Empty troop fixture prevents unrelated contacts. Dummy audio onset counters, no audible quality, raster, OS-input or continuous-motion acceptance."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	paused=false;current_scene=null;scene.queue_free()
	for unused in 8:await process_frame
	OS.delay_msec(100);await process_frame
	quit(0 if result.passed else 1)
