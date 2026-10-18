extends "/workspace/scratch/yuga-next-W1-r1/harness/full_world_collector.gd"
## Declared real kit/physics reload staging and saved remaps; no OS-input playthrough claim.
const CONTROL_MANIFEST := "/workspace/scratch/yuga-next-W1-r1/harness/controls.json"
const AUTHORITY = preload("/workspace/scratch/yuga-continuation-W1-r1/package-successor-r2-preparation/tools/ui-campaign/authority_stage.gd")
const WORLD_PARENT_SOURCE := "/workspace/scratch/yuga-next-W2-r1/candidate-terminal-r2.gd"
const WORLD_PARENT_SHA := "503093acba1f8b5679e8dfb3bf81beee5a273c9d766ba60d352e3d07035a375d"
const UI_SOURCE := "/workspace/scratch/yuga-next-W2-r1/reload-r1/capture-only-confluence_world-r3.gd"
const UI_SHA := "fae4222b305c0cb5bde5f2c08f44b0b4f9f304326c7db7a85fa54f8240230f3d"
const HUD_SOURCE := "/workspace/scratch/yuga-next-W2-r1/reload-r1/candidate-rama_hero_hud.gd"
const HUD_SHA := "572b0b8469c6b9d0b80d39cde5e8389450c9e0d7e8af989c18644f956dd657bc"
const Bindings = preload("res://scripts/input_bindings.gd")
const HUD_REMAP := "res://scripts/rama_hero_hud.gdc"
const HUD_REMAP_SHA := "7736d83e3797ddb75bf1f7dc4dbf90937a686b4915250cfb73dab2a4b83e0995"
var hud_source: Script
var ui_source: Script
var stage_receipt: Dictionary={}
func hashes() -> Dictionary:
	var controls: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTROL_MANIFEST))
	var result: Dictionary={}
	for path in controls.files:result[path]=FileAccess.get_sha256(path)
	result[HUD_SOURCE]=FileAccess.get_sha256(HUD_SOURCE)
	result[WORLD_PARENT_SOURCE]=FileAccess.get_sha256(WORLD_PARENT_SOURCE)
	result[UI_SOURCE]=FileAccess.get_sha256(UI_SOURCE)
	result[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	return result
func snapshot(id: String) -> Dictionary:
	var result:=super.snapshot(id)
	var scene: Node3D=current_scene
	result.reload_fixture={"stage":encode_value(stage_receipt),"current":encode_value(reload_state(scene)),"world_instance_source_sha256":scene.get_script().source_code.sha256_text(),"world_parent_sha256":WORLD_PARENT_SHA,"world_transport_delta":"ONE absolute HUD preload string; reverse-line source proof reconstructs503093 byte-exact","hud_instance_source_sha256":scene.rama_hud.get_script().source_code.sha256_text(),"saved_bindings":Bindings.current(),"scope":"Real accepted kit releases, real start_reload and manual existing army/player physics steps. Held callbacks isolate scaled inspection. No direct ammo/reload/UI text assignment, OS-input or natural timing claim."}
	return result
func reload_state(scene: Node) -> Dictionary:
	return {"kit":scene.rama_runtime.kit.report(),"vitals":scene.rama_runtime.vitals.report(),"army":scene.army.report(),"eligibility":scene.rama_runtime._input_eligibility(),"ammo":scene.player.ammo,"reload_remaining":scene.player.reload_remaining,"note":scene.rama_hud.note.text,"slots":scene.rama_hud.slots.map(func(slot):return slot.text),"styles":scene.rama_hud._slot_states.duplicate(),"logical_size":root.get_visible_rect().size,"scale":root.content_scale_factor}

func advance_reload_fixture(scene: Node) -> void:
	scene.army.step_simulation(.05)
	for unused in 3:scene.player._physics_process(1.0/60)
	scene.rama_effects.step(.05)
	scene.rama_hud._process(.05)

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown argument:"+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	source_start=hashes();branch="reload-capture-only-preload-world-parent503093-HUD572b-over-exact79e5"
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight:root.show()
	if FileAccess.get_sha256(WORLD_PARENT_SOURCE)!=WORLD_PARENT_SHA:finish("World parent503093 pin mismatch");return
	var restored: String=FileAccess.get_file_as_string(UI_SOURCE).replace('const RamaHUD = preload("/workspace/scratch/yuga-next-W2-r1/reload-r1/candidate-rama_hero_hud.gd")','const RamaHUD = preload("res://scripts/rama_hero_hud.gd")')
	if restored.sha256_text()!=WORLD_PARENT_SHA:finish("Capture-only one-line reverse proof failed");return
	if FileAccess.get_sha256(UI_SOURCE)!=UI_SHA:finish("Candidate UI derivative pin mismatch");return
	if FileAccess.get_sha256(HUD_SOURCE)!=HUD_SHA:finish("HUD source pin mismatch");return
	hud_source=load(HUD_SOURCE) as Script
	if hud_source==null or not hud_source.can_instantiate() or hud_source.source_code.sha256_text()!=HUD_SHA:finish("HUD load mismatch");return
	if FileAccess.get_sha256("res://scripts/rama_hero_hud.gd.remap")!=HUD_REMAP_SHA:finish("Unexpected exported HUD remap");return
	# Keep the private HUD resource at its absolute path; the external-only world preload names it directly.
	ui_source=load(UI_SOURCE) as Script
	if ui_source==null or not ui_source.can_instantiate() or ui_source.source_code.sha256_text()!=UI_SHA:finish("Candidate UI source load mismatch");return
	check("world compiled preload is exact572b HUD",ui_source.get_script_constant_map().get("RamaHUD")==hud_source)
	if checks.any(func(row):return not row.passed):finish("HUD preload provenance failed");return
	ui_source.take_over_path("res://scripts/confluence_world.gd")
	if change_scene_to_file("res://scenes/confluence_world.tscn")!=OK:finish("World load failed");return
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("World readiness failed");return
	await frames(12)
	var scene: Node3D=current_scene
	check("actual world instance is exact declared one-line503093 derivative",scene.get_script()==ui_source and scene.get_script().source_code.sha256_text()==UI_SHA)
	check("actual HUD instance is exact external source572b",scene.rama_hud.get_script()==hud_source and scene.rama_hud.get_script().source_code.sha256_text()==HUD_SHA)
	if checks.any(func(row):return not row.passed):finish("External UI/HUD instance provenance failed");return
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	stage_receipt.before=reload_state(scene)
	AUTHORITY.new()._hold(scene)
	scene.rama_effects.set_process(false)
	Bindings.install("user://reload-actual-fixture.cfg")
	var saved:=true
	for pair in [["jump",KEY_J],["sprint",KEY_K],["descend",KEY_L],["pulse",KEY_SPACE],["dash",KEY_SHIFT],["guardian_circle",KEY_CTRL]]:saved=Bindings.set_binding(pair[0],pair[1]).ok and saved
	check("supported long keys saved through actual API",saved and Bindings.label("pulse")=="Space" and Bindings.label("dash")=="Shift" and Bindings.label("guardian_circle")=="Ctrl")
	stage_receipt.piercing=scene.cast_rama_ability("piercing_dawn")
	for unused in 21:advance_reload_fixture(scene)
	stage_receipt.arrow=scene.cast_rama_ability("kodanda")
	for unused in 9:advance_reload_fixture(scene)
	stage_receipt.started_reload=scene.player.start_reload()
	stage_receipt.rejected_input=scene.rama_runtime.request_input_ability("dawn_volley",73101)
	scene.rama_hud._process(.001)
	stage_receipt.reload_started=reload_state(scene)
	stage_receipt.declared_steps={"delta":.05,"physics_delta":1.0/60,"physics_steps_per_army_step":3,"piercing_steps":21,"arrow_steps":9}
	check("actual releases consume one arrow then reload",stage_receipt.piercing.get("accepted",false) and stage_receipt.arrow.get("accepted",false) and stage_receipt.started_reload and scene.player.ammo==scene.player.MAGAZINE-1 and scene.player.reload_remaining>0)
	check("real mounted input rejects during reload",not stage_receipt.rejected_input.get("accepted",false) and stage_receipt.rejected_input.get("reason","")=="Finish the current action")
	if checks.any(func(row):return not row.passed):finish("Real reload preparation failed");return
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale
		var before: Dictionary=reload_state(scene)
		await frames(12)
		check("reload authority held while scaled "+str(scale),reload_state(scene)==before)
		check("ordinary player camera "+str(scale),root.get_camera_3d()==scene.player.camera)
		check("reload non-ready affordance "+str(scale),scene.rama_hud.note.text=="Reloading bow" and scene.rama_hud.slots[0].text.contains("RELOADING") and scene.rama_hud.slots.slice(2).all(func(slot):return slot.text.contains("BUSY")))
		if not take("%02d-STAGED-reload-%d" % [shots.size(),int(scale*100)]):return
	var ticks:=0
	while scene.player.reload_remaining>0 and ticks<40:
		advance_reload_fixture(scene);ticks+=1
	scene.rama_hud._process(.001)
	stage_receipt.completion_steps=ticks
	stage_receipt.completed=reload_state(scene)
	check("real physics completion restores ammo and eligibility",scene.player.reload_remaining==0 and scene.player.ammo==scene.player.MAGAZINE and scene.rama_runtime._input_eligibility().eligible)
	check("completed reload restores ability readiness",scene.rama_hud.slots.slice(2).all(func(slot):return slot.text.contains("READY")) and scene.rama_hud.note.text!="Reloading bow")
	await frames(12)
	if not take("02-STAGED-reload-complete-200"):return
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("three declared reload/completion views",shots.size()==3)
	check("external inputs unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(row):return row.passed)
	var report:={"complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"stage_at_exit":stage_receipt,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Exact79e5 PCK with externally loaded capture-only world derivative(parent503093, ONE explicit HUD preload path)/HUD572b proven on actual instances. Real accepted kit releases, start_reload, input rejection and physics-driven completion; callback hold during100/200 view inspection; saved actual bindings. No UI state assignment, native input playthrough, cold-cache or fullgame acceptance."}
	paused=false
	if is_instance_valid(current_scene):current_scene.queue_free()
	for unused in 8:await process_frame
	var started:=Time.get_ticks_usec();var previous:=AudioServer.get_time_since_last_mix();var observed:=0
	while observed<2 and Time.get_ticks_usec()-started<250000:
		OS.delay_msec(1)
		var now:=AudioServer.get_time_since_last_mix()
		if now+.0002<previous:observed+=1
		previous=now
	for unused in 8:await process_frame
	report.audio_cleanup={"observed_real_mixer_ticks":observed,"budget_usec":250000}
	if not output.is_empty() and DirAccess.dir_exists_absolute(output):write_json(output.path_join("preflight.json" if preflight else "capture.json"),report)
	print("RELOAD_CANDIDATE_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
