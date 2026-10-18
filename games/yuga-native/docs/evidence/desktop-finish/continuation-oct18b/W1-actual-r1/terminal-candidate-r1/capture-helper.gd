extends "/workspace/scratch/yuga-next-W1-r1/harness/full_world_collector.gd"
## STAGED real defeat → core boundary outcome without reset; viewport Escape returns to the ended world.
const CONTROL_MANIFEST := "/workspace/scratch/yuga-next-W1-r1/harness/controls.json"
const AUTHORITY = preload("/workspace/scratch/yuga-continuation-W1-r1/package-successor-r2-preparation/tools/ui-campaign/authority_stage.gd")
const UI_SOURCE := "/workspace/scratch/yuga-next-W2-r1/candidate-terminal-r2.gd"
const UI_SHA := "503093acba1f8b5679e8dfb3bf81beee5a273c9d766ba60d352e3d07035a375d"
var ui_source: Script
var stage_receipt: Dictionary={}
var terminal_receipt: Dictionary={}
func hashes() -> Dictionary:
	var controls: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTROL_MANIFEST))
	var result: Dictionary={}
	for path in controls.files:result[path]=FileAccess.get_sha256(path)
	result[get_script().resource_path]=FileAccess.get_sha256(get_script().resource_path)
	return result
func snapshot(id: String) -> Dictionary:
	var result:=super.snapshot(id)
	var scene: Node3D=current_scene
	result.defeat_fixture={"stage":encode_value(stage_receipt),"vitals":encode_value(scene.rama_runtime.vitals.report()),"player_active":scene.player.active,"ability_label":scene.ability_label.text,"goal_label":scene.goal_label.text,"compact_text":scene.compact_world_labels.map(func(child):return child.text),"scene_script_path":scene.get_script().resource_path,"scene_script_source_sha256":scene.get_script().source_code.sha256_text(),"scope":"Real vitals lethal damage through retained authority fixture; scene/player/army callback hold prevents respawn while actual UI scales100→200. Respawn clock is observed before/after the single declared army step; no playthrough claim."}
	result.terminal_fixture={"transition":encode_value(terminal_receipt),"current":encode_value(terminal_state(scene)),"scope":"STAGED core boundary and one actual army step after real lethal damage, without army/vitals reset. Viewport Escape uncovers the ended world; not a played victory."}
	return result

func terminal_state(scene: Node) -> Dictionary:
	return {"army":scene.army.report(),"vitals":scene.rama_runtime.vitals.report(),"player_active":scene.player.active,"paused":scene.paused,"tree_paused":paused,"pause_visible":scene.pause_panel.is_visible_in_tree(),"outcome_visible":scene.outcome_summary.is_visible_in_tree(),"heading":scene.ability_label.text,"goal":scene.goal_label.text,"combat_note":scene.rama_hud.note.text,"energy_value":scene.energy_bar.value,"energy_maximum":scene.energy_bar.max_value,"compact_visible":scene.compact_world_card.is_visible_in_tree(),"compact_rows":scene.compact_world_labels.map(func(child):return child.text)}

func run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
		elif arg=="--preflight":preflight=true
		else:finish("Unknown argument:"+arg);return
	if not output.is_absolute_path() or DirAccess.dir_exists_absolute(output):finish("Fresh output required");return
	DirAccess.make_dir_recursive_absolute(output)
	if not preflight and (DisplayServer.get_name()!="X11" or RenderingServer.get_current_rendering_method()!="forward_plus"):finish("X11 Forward+ required");return
	source_start=hashes();branch="terminal-after-real-defeat-externalUI503093-over-exact79e5"
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
	terminal_receipt.before_defeat=stage_receipt.before
	terminal_receipt.after_defeat=terminal_state(scene)
	var dead: Dictionary=scene.rama_runtime.vitals.report().duplicate(true)
	var army_before: Dictionary=scene.army.report().duplicate(true)
	var emissions: Array=[]
	var listener:=func(team: String):emissions.append(team)
	scene.army.outcome.connect(listener)
	scene.army.cores={"sun":100.0,"moon":0.0}
	terminal_receipt.rule_inputs={"cores":scene.army.cores.duplicate(),"steps":1,"delta":.05,"army_reset_called":false,"vitals_reset_called":false}
	var stepped: bool=scene.army.step_simulation(.05)
	scene.army.outcome.disconnect(listener)
	scene._update_practice_hud()
	terminal_receipt.after_outcome=terminal_state(scene)
	terminal_receipt.outcome_signals=emissions.duplicate()
	check("one actual core-boundary outcome signal",stepped and emissions==["sun"] and scene.army.winner=="sun")
	check("army clock advances one step without reset",is_equal_approx(scene.army.elapsed,float(army_before.elapsed)+.05))
	check("defeated identity survives outcome",not scene.rama_runtime.vitals.alive and scene.rama_runtime.vitals.health==0 and scene.rama_runtime.vitals.generation==dead.generation and scene.rama_runtime.vitals.deaths==dead.deaths and not scene.player.active)
	check("outcome opens genuine pause summary",scene.paused and paused and scene.outcome_summary.is_visible_in_tree())
	if checks.any(func(row):return not row.passed):finish("Defeat-to-terminal authority boundary failed");return
	# Inherited key() dispatches down/up InputEventKey through root.push_input.
	# This is explicit viewport input, not OS-native XTest or a direct pause setter.
	await key(KEY_ESCAPE)
	await frames(12)
	var refresh_before: Dictionary=scene.army.report().duplicate(true)
	scene._process(.13)
	terminal_receipt.after_viewport_escape=terminal_state(scene)
	terminal_receipt.presentation_refresh={"delta":.13,"army_unchanged":scene.army.report()==refresh_before}
	check("viewport Escape uncovers ended world",not scene.paused and not paused and not scene.pause_panel.is_visible_in_tree())
	check("presentation refresh preserves ended authority",scene.army.report()==refresh_before and scene.army.winner=="sun")
	var before: Dictionary=scene.rama_runtime.vitals.report().duplicate(true)
	for scale in [1.0,2.0]:
		root.content_scale_factor=scale
		await frames(12)
		check("vitals unchanged whileheld "+str(scale),scene.rama_runtime.vitals.report()==before)
		check("ordinary player camera "+str(scale),root.get_camera_3d()==scene.player.camera)
		check("terminal heading overrides RETURNING "+str(scale),scene.ability_label.text=="VAYU LIFT · ROUND ENDED")
		check("terminal normal detail "+str(scale),scene.goal_label.text.begins_with("Round ended · "))
		var rows: Array=terminal_state(scene).compact_rows
		if scale==2.0:
			check("terminal compact affordance200",scene.compact_world_card.is_visible_in_tree() and rows.size()==4 and rows[3]=="Flight and tether are unavailable after round end.")
		if not take("%02d-STAGED-terminal-%d" % [shots.size(),int(scale*100)]):return
	finish("")

func finish(failure: String) -> void:
	if done:return
	done=true
	var after:=hashes() if not source_start.is_empty() else {}
	check("two declared terminal views after real defeat",shots.size()==2)
	check("external inputs unchanged",not source_start.is_empty() and source_start==after)
	var passed:=failure.is_empty() and checks.all(func(row):return row.passed)
	var report:={"complete":passed,"failure":failure,"preflight":preflight,"shots":shots,"stage_at_exit":stage_receipt,"terminal_transition":terminal_receipt,"checks":checks,"checkpoints":checkpoints,"source_sha256":source_start,"source_after_sha256":after,"source_unchanged":source_start==after,"renderer":RenderingServer.get_current_rendering_method(),"adapter":RenderingServer.get_video_adapter_name(),"scope":"Exact79e5 PCK with only externallyloaded503093 production UI caller override proven on actual instance; real vitals lethal damage and declared callback hold; same ordinaryplayercamera, real defeat→core-boundary outcome with NOreset, viewport Escape and scales100/200. No played defeat/victory or fullgame acceptance."}
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
	print("TERMINAL_CANDIDATE_COMPLETE ",passed," ",failure)
	quit(0 if passed else 1)
