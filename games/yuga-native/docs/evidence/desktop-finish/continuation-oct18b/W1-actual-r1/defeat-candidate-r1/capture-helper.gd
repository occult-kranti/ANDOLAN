extends "/workspace/scratch/yuga-next-W1-r1/harness/full_world_collector.gd"
## Declared actual-rule lethal damage + simulation hold; no native defeat-playthrough claim.
const CONTROL_MANIFEST := "/workspace/scratch/yuga-next-W1-r1/harness/controls.json"
const AUTHORITY = preload("/workspace/scratch/yuga-continuation-W1-r1/package-successor-r2-preparation/tools/ui-campaign/authority_stage.gd")
const UI_SOURCE := "/workspace/scratch/yuga-next-W2-r1/candidate-terminal-r2.gd"
const UI_SHA := "503093acba1f8b5679e8dfb3bf81beee5a273c9d766ba60d352e3d07035a375d"
var ui_source: Script
var stage_receipt: Dictionary={}
func hashes() -> Dictionary:
	var controls: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTROL_MANIFEST))
	var result: Dictionary={}
	for path in controls.files:result[path]=FileAccess.get_sha256(path)
	return result
func snapshot(id: String) -> Dictionary:
	var result:=super.snapshot(id)
	var scene: Node3D=current_scene
	result.defeat_fixture={"stage":encode_value(stage_receipt),"vitals":encode_value(scene.rama_runtime.vitals.report()),"player_active":scene.player.active,"ability_label":scene.ability_label.text,"goal_label":scene.goal_label.text,"compact_text":scene.compact_world_card.get_children().map(func(child):return child.text if child is Label else str(child.get_class())),"scene_script_path":scene.get_script().resource_path,"scene_script_source_sha256":scene.get_script().source_code.sha256_text(),"scope":"Real vitals lethal damage through retained authority fixture; scene/player/army callback hold prevents respawn while actual UI scales100→200. Unmodified real respawn clock remains3s; no playthrough claim."}
	return result
func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown argument:"+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	source_start=hashes();branch="candidate-externalUI503093-over-exact79e5"
	root.size=Vector2i(960,540);root.content_scale_size=Vector2i(1280,720);root.content_scale_factor=1.0
	if not preflight:root.show()
	if FileAccess.get_sha256(UI_SOURCE)!=UI_SHA:finish("Candidate UI source pin mismatch");return
	ui_source=load(UI_SOURCE) as Script
	if ui_source==null or ui_source.source_code.sha256_text()!=UI_SHA:finish("Candidate UI source load mismatch");return
	ui_source.take_over_path("res://scripts/confluence_world.gd")
	if change_scene_to_file("res://scenes/confluence_world.tscn")!=OK:finish("World load failed");return
	if not await wait_scene("res://scenes/confluence_world.tscn"):finish("World readiness failed");return
	await frames(12)
	var scene: Node3D=current_scene
	check("actual UI instance is exact external source503093",scene.get_script()==ui_source and scene.get_script().source_code.sha256_text()==UI_SHA)
	if checks.any(func(row):return not row.passed):finish("External UI instance provenance failed");return
	scene.player.rama_motion.modification_processed.connect(observe_final_pose);final_observer_connected=true
	stage_receipt=AUTHORITY.new().perform(scene,"defeat")
	check("actual lethal receipt accepted",stage_receipt.get("passed",false))
	check("returning actor0HP inactive",not scene.rama_runtime.vitals.alive and not scene.player.active and scene.rama_hud.note.text=="RETURNING IN 3.0s")
	var before: Dictionary=scene.rama_runtime.vitals.report().duplicate(true)
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale
		await frames(12)
		check("vitals unchanged whileheld "+str(scale),scene.rama_runtime.vitals.report()==before)
		check("ordinary player camera "+str(scale),root.get_camera_3d()==scene.player.camera)
		if not take("%02d-STAGED-defeat-%d" % [shots.size(),int(scale*100)]):return
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("two declared actual-rule defeat views",shots.size()==2)
	check("external inputs unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(row):return row.passed)
	var report:={"complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"stage_at_exit":stage_receipt,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Exact79e5 PCK with only externallyloaded503093 production UI caller override proven on actual instance; real vitals lethal damage and declared callback hold; same ordinaryplayercamera, scales100/200. No native defeat playthrough or fullgame acceptance."}
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
	print("DEFEAT_CANDIDATE_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
