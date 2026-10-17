extends SceneTree
## Five real Confluence ability takes. Fixtures stage real receiver positions only.
## Damage, cooldowns, motion releases and VFX come from the actual hero runtime.
const FPS := 30
const Unit = preload("res://scripts/lane_minion.gd")
const IDS := ["kodanda","piercing_dawn","measured_step","guardian_circle","dawn_volley"]
const LENGTHS := {"kodanda":1.5,"piercing_dawn":1.8,"measured_step":.7,"guardian_circle":5.6,"dawn_volley":2.5}
const ORIGIN := Vector3(-40,.05,-10)
const REQUIRED_IMPORTS := ["res://assets/heroes/rama-hero.glb","res://assets/world/architecture.glb","res://assets/world/nature.glb"]
var output_path := ""
var preview := false
var scene: Node3D
var camera: Camera3D
var sources := {}
var imports := {}
var frames: Array=[]
var stills: Array=[]
var takes: Array=[]
var events: Array=[]
var current_events: Array=[]
var targets: Array=[]
var failure := ""
var started := Time.get_ticks_msec()
var capture_size := Vector2i(1280,720)
var frame_index := 0
var label: Label
func _initialize() -> void:call_deferred("run")
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output_path=arg.trim_prefix("--output=")
		elif arg=="--preview":preview=true
		else:push_error("Unknown argument "+arg);quit(1);return
	if not output_path.is_absolute_path() or DirAccess.dir_exists_absolute(output_path):push_error("Choose new absolute output");quit(1);return
	DirAccess.make_dir_recursive_absolute(output_path)
	if DisplayServer.get_name()=="headless" or RenderingServer.get_current_rendering_method()!="forward_plus":fail("Forward+ display required");return
	if Engine.physics_ticks_per_second!=60:fail("60 Hz physics required");return
	sources=_source_hashes()
	for path in REQUIRED_IMPORTS:
		if not _validate_import(path):finish(false);return
	root.size=capture_size;root.content_scale_size=capture_size;root.msaa_3d=Viewport.MSAA_2X
	root.title="YUGA — Rama real gameplay capture";root.show()
	scene=load("res://scenes/confluence_world.tscn").instantiate();root.add_child(scene);current_scene=scene
	await draw_frames(8)
	if not scene.world_ready or not scene.player.model_ready or not scene.rama_runtime.configured:fail("World/current hero/kit must be ready");return
	scene.set_paused(false);scene.set_overview(false);scene.set_review_phase(0.0)
	camera=Camera3D.new();scene.add_child(camera);camera.fov=58
	var layer:=CanvasLayer.new();layer.layer=100;root.add_child(layer)
	label=Label.new();layer.add_child(label);label.position=Vector2(340,9)
	label.add_theme_font_size_override("font_size",14);label.add_theme_color_override("font_color",Color("f1d7a0"));label.add_theme_color_override("font_outline_color",Color("101820"));label.add_theme_constant_override("outline_size",6)
	scene.rama_runtime.combat_event.connect(func(event):
		var entry: Dictionary=event.duplicate(true)
		entry.physics_tick=Engine.get_physics_frames()
		events.append(_normal(entry));current_events.append(entry))
	for id in IDS:
		await fixture(id)
		if not failure.is_empty():finish(false);return
		label.text="RAMA · "+id.replace("_"," ").to_upper()+" · REAL OFFLINE RECEIVERS"
		var accepted: Dictionary=scene.cast_rama_ability(id)
		if not accepted.get("accepted",false):fail("Real world cast rejected: "+id+" · "+str(accepted));return
		var begin: Dictionary=current_events.filter(func(e):return e.kind=="begin")[-1]
		_align_receivers(begin)
		var receiver_before:=receivers()
		var start_tick:=Engine.get_physics_frames()
		var prior_tick:=start_tick
		var prior_draw:=Engine.get_frames_drawn()
		var start_frame:=frame_index
		var count:=int(ceil((float(begin.timing.windup_s)+.45 if preview else float(LENGTHS[id]))*FPS))
		var still_ages: Array=[maxf(.03,float(begin.timing.windup_s)-.06),float(begin.timing.windup_s)+.065,float(begin.timing.windup_s)+.30]
		var still_done: Array=[]
		for local_index in range(count):
			await draw_frames(1)
			var tick:=Engine.get_physics_frames()
			var draw:=Engine.get_frames_drawn()
			if tick-prior_tick!=2 or draw<=prior_draw:fail("Nonconsecutive actual take clocks at "+id);return
			var age:=float(tick-start_tick)/60.0
			var fx_state: Dictionary=scene.rama_effects.report()
			if not fx_state.finite or not scene.player.rama_motion.diagnostics().get("finite",false):fail("Nonfinite effect or skeletal state");return
			var image_data: Dictionary={}
			if not preview:image_data=save_image("frame-%05d.png"%frame_index)
			frames.append({"index":frame_index,"take":id,"local_index":local_index,"sample_time_s":age,"physics_tick":tick,"physics_tick_delta":tick-prior_tick,"render_frame":draw,"image":image_data,"fx":fx_state,"motion":scene.player.rama_motion.diagnostics(),"hero_position":_normal(scene.player.global_position)})
			for s in still_ages.size():
				if not still_done.has(s) and age>=float(still_ages[s]):
					var phase: String=["windup","release","contact"][s]
					stills.append({"ability_id":id,"view":"gameplay","phase":phase,"sample_age_s":age,"image":save_image("still-"+id+"-"+phase+".png"),"fx":fx_state,"receivers":receivers()})
					still_done.append(s)
			frame_index+=1;prior_tick=tick;prior_draw=draw
		var releases:=current_events.filter(func(e):return e.kind=="release")
		var receipts:=0
		for event in current_events:receipts+=event.get("receipts",[]).size()
		var ended:=current_events.any(func(e):return e.kind=="end")
		if releases.size()!=1 or (not preview and (not ended or scene.rama_effects.report().active!=0)):fail("Incomplete actual lifecycle for "+id);return
		if id in ["kodanda","piercing_dawn","dawn_volley","guardian_circle"] and receipts==0:fail("No actual receiver receipt for "+id);return
		takes.append({"ability_id":id,"cast":_normal(accepted),"start_frame":start_frame,"frame_count":count,"start_tick":start_tick,"physics_ticks":prior_tick-start_tick,"release_count":releases.size(),"receipt_count":receipts,"normal_expiry":ended,"receivers_before":receiver_before,"receivers_after":receivers(),"events":_normal(current_events),"scope":"Actual world cast entry, normal army clock, real staged receivers, player gameplay camera."})
		print("RAMA_GAMEPLAY_CAPTURE ",id," frames=",count," receipts=",receipts)
	# Separate replayed low-angle presentation stills; these are outside the video.
	for id in ["piercing_dawn","guardian_circle","dawn_volley"]:
		await fixture(id)
		var accepted: Dictionary=scene.cast_rama_ability(id)
		if not accepted.get("accepted",false):fail("Low-angle replay rejected");return
		var begin: Dictionary=current_events.filter(func(e):return e.kind=="begin")[-1]
		_align_receivers(begin)
		var focus: Vector3=begin.origin+begin.forward*1.5+Vector3.UP*1.2
		camera.global_position=begin.origin+Vector3(-5.2,2.9,5.5)
		if id=="guardian_circle":
			focus=begin.target+Vector3.UP*.6
			camera.global_position=begin.target+Vector3(-7,4.2,-8)
		camera.look_at(focus);camera.current=true
		label.text="RAMA · "+id.replace("_"," ").to_upper()+" · SEPARATE LOW-ANGLE REPLAY"
		await draw_frames(maxi(1,int(floor(float(begin.timing.windup_s)*FPS*.80))))
		stills.append({"ability_id":id,"view":"low_angle","phase":"windup","image":save_image("still-"+id+"-low-windup.png"),"fx":scene.rama_effects.report(),"receivers":receivers()})
		await draw_frames(int(ceil(float(begin.timing.windup_s)*FPS*.20))+5)
		stills.append({"ability_id":id,"view":"low_angle","phase":"released","image":save_image("still-"+id+"-low-released.png"),"fx":scene.rama_effects.report(),"receivers":receivers()})
		if id=="guardian_circle":
			scene.rama_effects.set_options({"reduced_effects":true,"reduced_motion":true})
			await draw_frames(2)
			stills.append({"ability_id":id,"view":"low_reduced","phase":"active","image":save_image("still-guardian-circle-reduced.png"),"fx":scene.rama_effects.report()})
			scene.rama_effects.set_options({"reduced_effects":false,"reduced_motion":false})
	# Actual hero lifecycle, separate from the five ability video takes.
	await fixture("kodanda")
	label.text="RAMA · ACTUAL PRACTICE HIT / DEFEAT / RETURN"
	var hero=scene.rama_runtime.vitals
	var hit_receipt: Dictionary=hero.receive_damage(90,"capture_lifecycle",hero.generation,1)
	await draw_frames(3)
	stills.append({"ability_id":"hero_vitals","view":"gameplay","phase":"hit","image":save_image("still-hero-hit.png"),"receipt":hit_receipt,"vitals":hero.report(),"motion":scene.player.rama_motion.diagnostics()})
	var death_receipt: Dictionary=hero.receive_damage(500,"capture_lifecycle",hero.generation,2)
	await draw_frames(17)
	stills.append({"ability_id":"hero_vitals","view":"gameplay","phase":"defeated","image":save_image("still-hero-defeated.png"),"receipt":death_receipt,"vitals":hero.report(),"motion":scene.player.rama_motion.diagnostics()})
	if hero.alive:fail("Actual lethal receiver did not defeat hero");return
	await draw_frames(83)
	stills.append({"ability_id":"hero_vitals","view":"gameplay","phase":"respawned","image":save_image("still-hero-respawned.png"),"vitals":hero.report(),"motion":scene.player.rama_motion.diagnostics()})
	if not hero.alive or hero.health!=300 or not scene.player.active:fail("Actual hero did not respawn");return
	if sources!=_source_hashes():fail("Runtime sources changed during capture; this run is not source-pinned");return
	finish(true)

func fixture(id: String) -> void:
	scene.set_paused(false);scene.set_overview(false)
	scene._restart_army()
	scene.teleport_to(ORIGIN,0)
	scene.player.yaw=PI;scene.player.pitch=-.55 if id=="guardian_circle" else -.25;scene.player._update_camera()
	scene.player.camera.current=true
	await draw_frames(8)
	if not scene.player.is_on_floor():failure="Actual CharacterBody did not ground";return
	for unit in scene.army.units.duplicate():scene.army.units.erase(unit);unit.free()
	scene.army._attacks.clear();scene.army._decision_clock=100000;scene.army._next_wave=100000
	targets.clear()
	for i in range(4):
		var unit=Unit.new();unit.setup(scene.army,scene.army.next_id,"sun" if i==0 else "moon","commander",1)
		scene.army.next_id+=1;unit.position=ORIGIN+Vector3(0,-.05,6+i*2)
		unit.attack_time=100000;unit.attack_cooldown=100000;unit.target=null
		unit.defeated.connect(scene.army._on_defeated)
		scene.army.add_child(unit);scene.army.units.append(unit);targets.append(unit)
		if i==0:unit.receive_damage(80,"army")
	scene.army._rebuild_buckets()
	scene.rama_runtime.vitals.receive_damage(60,"capture_fixture")
	await draw_frames(10)
	current_events.clear()
func _align_receivers(begin: Dictionary) -> void:
	for i in targets.size():
		var unit=targets[i]
		if i==0:unit.global_position=begin.target+Vector3(.7,0,0) if begin.ability_id=="guardian_circle" else begin.origin+Vector3(2,0,2)
		elif begin.ability_id=="dawn_volley":unit.global_position=begin.origin+begin.geometry.projectiles[i-1].forward*9.0
		else:unit.global_position=begin.origin+begin.forward*(4.5+i*2.5)
		unit.position.y=0;unit.previous_position=unit.position
	scene.army._rebuild_buckets()
func receivers() -> Array:
	var result: Array=[]
	for unit in targets:
		if is_instance_valid(unit):result.append({"unit_id":unit.unit_id,"team":unit.team,"health":unit.health,"shield":unit.shield,"alive":unit.alive,"position":_normal(unit.global_position)})
	result.append({"receiver":"hero","vitals":scene.rama_runtime.vitals.report()})
	return result
func draw_frames(count: int) -> void:
	for _index in count:
		await process_frame
		await RenderingServer.frame_post_draw
func save_image(filename: String) -> Dictionary:
	var image:=root.get_texture().get_image()
	if image.is_empty() or image.get_size()!=capture_size:failure="Invalid rendered image";return {}
	var path:=output_path.path_join(filename)
	if FileAccess.file_exists(path) or image.save_png(path)!=OK:failure="Image write failed";return {}
	return {"file":filename,"sha256":FileAccess.get_sha256(path),"width":capture_size.x,"height":capture_size.y,"draw_calls":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),"rendered_objects":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME),"rendered_primitives":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)}
func _source_hashes() -> Dictionary:
	var paths: Array[String]=["res://project.godot","res://tools/capture-rama-gameplay.gd","res://tools/run-rama-gameplay.py","res://tools/run-traversal-capture.py","res://art/world/confluence-map.json"]
	for directory in ["res://scripts","res://shaders","res://scenes","res://assets"]:_collect(directory,paths)
	paths.sort()
	var result:={}
	for path in paths:result[path]=FileAccess.get_sha256(path) if FileAccess.file_exists(path) else "MISSING"
	return result
func _collect(path: String, paths: Array[String]) -> void:
	for name in DirAccess.get_files_at(path):paths.append(path.path_join(name))
	for name in DirAccess.get_directories_at(path):_collect(path.path_join(name),paths)
func _validate_import(path: String) -> bool:
	var config:=ConfigFile.new()
	if config.load(path+".import")!=OK:failure="Missing import metadata: "+path;return false
	var imported: String=config.get_value("remap","path","")
	var checksum:=imported.get_basename()+".md5"
	if not FileAccess.file_exists(imported) or not FileAccess.file_exists(checksum):failure="Missing imported resource: "+path;return false
	var pattern:=RegEx.new()
	var stamp:=FileAccess.get_file_as_string(checksum)
	for item in [["source_md5",path],["dest_md5",imported]]:
		pattern.compile(String(item[0])+'="([a-f0-9]+)"')
		var found:=pattern.search(stamp)
		if not found or found.get_string(1)!=FileAccess.get_md5(item[1]):failure="Stale imported resource: "+path;return false
	imports[path]={"fresh":true,"imported":imported,"sha256":FileAccess.get_sha256(imported)}
	return true
func _normal(value: Variant) -> Variant:
	if value is Vector3:return [value.x,value.y,value.z]
	if value is Vector2:return [value.x,value.y]
	if value is Dictionary:
		var result:={}
		for key in value:result[key]=_normal(value[key])
		return result
	if value is Array:
		var result:=[]
		for item in value:result.append(_normal(item))
		return result
	return value
func fail(message: String) -> void:failure=message;finish(false)
func finish(success: bool) -> void:
	var after:=_source_hashes()
	var report:={"schema":1,"kind":"actual-rama-native-gameplay","complete":success,"failure":failure,"preview":preview,"gameplay_applied":true,"fps":FPS,"physics_hz":Engine.physics_ticks_per_second,"width":capture_size.x,"height":capture_size.y,"renderer":RenderingServer.get_current_rendering_method(),"display":DisplayServer.get_name(),"adapter":RenderingServer.get_video_adapter_name(),"godot":Engine.get_version_info(),"source_sha256":sources,"source_after_sha256":after,"source_unchanged":sources==after,"imports":imports,"frames":frames,"stills":stills,"takes":takes,"events":events,"wall_elapsed_ms":Time.get_ticks_msec()-started,"scope":"Five separate actual Confluence takes with real current hero, staged live lane receivers, normal gameplay clock and real accepted damage/heal/movement. Script invokes actual world cast entry; this is not human OS input, one uninterrupted fight, audio audition or physical-GPU performance. Low-angle replays are outside video. Preview ends before normal ability lifetimes."}
	var file:=FileAccess.open(output_path.path_join("rama-gameplay-review.json"),FileAccess.WRITE)
	if file:file.store_string(JSON.stringify(report,"  ")+"\n");file.close()
	if not success:push_error(failure)
	quit(0 if success else 1)
