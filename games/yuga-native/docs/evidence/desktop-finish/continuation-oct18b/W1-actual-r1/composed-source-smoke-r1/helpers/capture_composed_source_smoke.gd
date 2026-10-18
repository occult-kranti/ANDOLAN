extends "/workspace/scratch/yuga-next-W1-r1/harness/full_world_collector.gd"
## Tiny local-source composition smoke. No Resource.take_over_path or product source overrides.
const CONTROL_PATH := "/workspace/scratch/yuga-next-W1-r1/composed-source-smoke-r1/controls.json"
const AUTHORITY = preload("/workspace/scratch/yuga-continuation-W1-r1/package-successor-r2-preparation/tools/ui-campaign/authority_stage.gd")
const SOURCE := "1236db5036b558be3e90c1e11b816f2a12e384dc"
const EXPECTED := {"world":"503093acba1f8b5679e8dfb3bf81beee5a273c9d766ba60d352e3d07035a375d","hud":"572b0b8469c6b9d0b80d39cde5e8389450c9e0d7e8af989c18644f956dd657bc","motion":"d5550b25044ea97c9ce482a130ac73f012c313e96f2029a555abb590e1375b0e","water":"3f5a6b89b6bdaaea547c51829da558d829445fb63a690d119e21720b8ce27a7e"}
var composition: Dictionary={}
var jump_trace: Array=[]
var full_refs: Array=[]
var reload_receipt: Dictionary={}
func hashes() -> Dictionary:
	var controls: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTROL_PATH))
	var values: Dictionary={}
	for path in controls.files:values[path]=FileAccess.get_sha256(path)
	return values
func observe_composition(scene: Node3D) -> Dictionary:
	var rows: Array=[]
	for description in scene.manifest.waters:
		var node: MeshInstance3D=scene.world.get_node(String(description.id))
		var material: ShaderMaterial=node.get_active_material(0) as ShaderMaterial
		rows.append({"id":String(description.id),"shader_path":material.shader.resource_path,"sha256":material.shader.code.sha256_text()})
	return {"world":scene.get_script().source_code.sha256_text(),"hud":scene.rama_hud.get_script().source_code.sha256_text(),"motion":scene.player.rama_motion.get_script().source_code.sha256_text(),"water":rows,"paths":[scene.get_script().resource_path,scene.rama_hud.get_script().resource_path,scene.player.rama_motion.get_script().resource_path]}
func sample_jump(scene: Node3D) -> Dictionary:
	return {"draw":Engine.get_frames_drawn(),"process":Engine.get_process_frames(),"physics":Engine.get_physics_frames(),"position":vector(scene.player.global_position),"velocity":vector(scene.player.velocity),"on_floor":scene.player.is_on_floor(),"jump_count":scene.player.jump_count,"locomotion":scene.player.rama_motion.locomotion,"motion_phase":scene.player.rama_motion.phase}
func save_observation(id: String) -> bool:
	var state: Dictionary=snapshot(id)
	state.composed_source_smoke={"source_commit":SOURCE,"composition":composition,"jump_trace":jump_trace,"reload_receipt":reload_receipt,"scope":"Canonical source/imports, ordinary product camera, real jump input action and accepted game-rule reload; callback hold only during final scaled inspection. No package or ordinary OS-input journey qualification."}
	var raw: PackedByteArray=JSON.stringify(state).to_utf8_buffer()
	var packed: PackedByteArray=raw.compress(FileAccess.COMPRESSION_GZIP)
	var name: String=id+".json.gz"
	var file: FileAccess=FileAccess.open(output.path_join(name),FileAccess.WRITE)
	if file==null or packed.is_empty():return false
	file.store_buffer(packed);file.close()
	full_refs.append({"file":name,"compressed_sha256":FileAccess.get_sha256(output.path_join(name)),"decoded_sha256":raw.get_string_from_utf8().sha256_text(),"decoded_bytes":raw.size()})
	if not preflight:
		var pixels: Image=root.get_texture().get_image()
		if pixels.is_empty() or pixels.save_png(output.path_join(id+".png"))!=OK:return false
		shots.append({"file":id+".png","sha256":FileAccess.get_sha256(output.path_join(id+".png")),"dimensions":[pixels.get_width(),pixels.get_height()]})
	check("correlated complete164 final poses "+id,final_pose.bone_names.size()==164 and final_pose.bone_global_poses.size()==164 and Engine.get_process_frames()==int(final_pose.process_frame) and Engine.get_physics_frames()==int(final_pose.physics_frame) and serialization_errors.is_empty())
	return true
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown argument");return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	source_start=hashes();branch="canonical-source1236-composed-smoke"
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight:root.show()
	if change_scene_to_file("res://scenes/confluence_world.tscn")!=OK:finish("World load failed");return
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("World readiness failed");return
	await frames(12)
	var scene: Node3D=current_scene
	composition=observe_composition(scene)
	check("actual canonical world HUD motion source bytes",composition.world==EXPECTED.world and composition.hud==EXPECTED.hud and composition.motion==EXPECTED.motion and composition.paths==["res://scripts/confluence_world.gd","res://scripts/rama_hero_hud.gd","res://scripts/rama_motion.gd"])
	check("three actual canonical thin-film water shaders",composition.water.size()==3 and composition.water.all(func(row):return row.sha256==EXPECTED.water and row.shader_path=="res://scripts/world_water.gdshader"))
	check("ordinary active full world",scene.world_ready and scene.player.model_ready and scene.player.active and not paused and root.get_camera_3d()==scene.player.camera)
	if checks.any(func(row):return not row.passed):finish("Composition identity failed");return
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	var before_jump: int=scene.player.jump_count
	Input.action_press("jump")
	await frames(2)
	Input.action_release("jump")
	var airborne: bool=false
	var fell: bool=false
	var landed: bool=false
	for unused in 60:
		await frames(1)
		var item: Dictionary=sample_jump(scene);jump_trace.append(item)
		airborne=airborne or not item.on_floor
		fell=fell or item.locomotion=="fall"
		if airborne and item.on_floor:landed=true;break
	check("one real input jump fall and landing",scene.player.jump_count==before_jump+1 and airborne and fell and landed)
	if checks.any(func(row):return not row.passed):finish("Jump smoke failed");return
	if not save_observation("00-current-source-land-100"):finish("First observation failed");return
	var ammo_before: int=scene.player.ammo
	reload_receipt.shoot_accepted=scene.player.shoot()
	for unused in 30:
		await frames(1)
		if scene.player.ammo<ammo_before and not scene.player.rama_action_locked:break
	reload_receipt.start_reload_accepted=scene.player.start_reload()
	reload_receipt.ammo_before=ammo_before;reload_receipt.ammo_after=scene.player.ammo;reload_receipt.remaining=scene.player.reload_remaining
	check("real accepted arrow release starts reload",reload_receipt.shoot_accepted and reload_receipt.start_reload_accepted and scene.player.ammo==ammo_before-1 and scene.player.reload_remaining>0)
	if checks.any(func(row):return not row.passed):finish("Reload smoke failed");return
	AUTHORITY.new()._hold(scene)
	root.content_scale_factor=2.0
	scene.rama_hud._process(.001)
	await frames(12)
	check("current reload HUD truthful at200",scene.rama_hud.note.text=="Reloading bow" and scene.rama_hud.slots[0].text.contains("RELOADING") and scene.rama_hud.slots.slice(2).all(func(slot):return slot.text.contains("BUSY")))
	if not save_observation("01-current-source-reload-200"):finish("Second observation failed");return
	finish("")
func finish(failure: String) -> void:
	if done:return
	done=true;Input.action_release("jump")	
	var after: Dictionary=hashes() if not source_start.is_empty() else {}
	check("two compressed controls and expected image count",full_refs.size()==2 and shots.size()==(0 if preflight else 2))
	check("pinned source/helper inputs unchanged",not source_start.is_empty() and source_start==after)
	var passed: bool=failure.is_empty() and checks.all(func(row):return row.passed)
	var report: Dictionary={"complete":passed,"failure":failure,"preflight":preflight,"source_commit":SOURCE,"scope":"Single canonical-source composition smoke, no PCK/export/package qualification; warm owned cache, no native physical-input/FPS/feel claim.","shots":shots,"full_snapshot_refs":full_refs,"composition":composition,"jump_trace":jump_trace,"reload_receipt":reload_receipt,"checks":checks,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after}
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	var started: int=Time.get_ticks_usec();var previous: float=AudioServer.get_time_since_last_mix();var observed: int=0
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now: float=AudioServer.get_time_since_last_mix()
		if now+.0002<previous:observed+=1
		previous=now
	for unused in 8:await process_frame
	report.audio_cleanup={"observed_real_mixer_ticks":observed,"budget_usec":250000}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("COMPOSED_SOURCE_SMOKE_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
