extends SceneTree
## Focused volume and focus lifecycle QA. Headless player state is not an audible-output review.
const SETTINGS := "user://courtyard-settings.cfg"
var checks: Array[Dictionary]=[]
var output := ""
var director_path := "res://scripts/combat_film.gd"
var had_settings := false
var saved_settings := PackedByteArray()

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
		if arg.begins_with("--director="): director_path=arg.trim_prefix("--director=")
	call_deferred("_run")

func _record(name_: String, passed: bool, details: Dictionary={}) -> void:
	checks.append({"name":name_,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",name_)

func _setting(value: Variant) -> void:
	var config:=ConfigFile.new()
	config.set_value("audio","volume",value)
	assert(config.save(SETTINGS)==OK)

func _count_players(node: Node) -> int:
	var result:=1 if node is AudioStreamPlayer else 0
	for child in node.get_children(): result+=_count_players(child)
	return result

func _run() -> void:
	had_settings=FileAccess.file_exists(SETTINGS)
	if had_settings: saved_settings=FileAccess.get_file_as_bytes(SETTINGS)
	if had_settings: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var script=load(director_path)
	var reader=script.new()
	_record("missing settings preserve courtyard default",is_equal_approx(reader._read_saved_audio_volume(),.7))
	var fixtures:=[
		{"name":"zero","value":0.0,"expected":0.0},
		{"name":"fraction","value":.35,"expected":.35},
		{"name":"one","value":1.0,"expected":1.0},
		{"name":"negative clamped","value":-.2,"expected":0.0},
		{"name":"above one clamped","value":2.0,"expected":1.0},
		{"name":"NaN defaults","value":NAN,"expected":.7},
		{"name":"infinity defaults","value":INF,"expected":.7},
		{"name":"numeric string rejected","value":"0","expected":.7},
		{"name":"boolean rejected","value":false,"expected":.7}
	]
	for fixture in fixtures:
		_setting(fixture.value)
		var actual: float=reader._read_saved_audio_volume()
		_record("saved volume "+fixture.name,is_finite(actual) and is_equal_approx(actual,fixture.expected),{"actual":actual,"expected":fixture.expected})
	reader.free()
	var focus_baseline:=root.focus_exited.get_connections().size()
	_setting(0.0)
	var muted=script.new()
	root.add_child(muted)
	current_scene=muted
	await process_frame
	_record("zero-volume startup is stopped with visible timeline active",muted.ready_to_play and muted.playing and not muted.audio_player.playing and muted.audio_volume==0.0 and muted.get_diagnostics().audio.muted)
	var silent:=true
	for time_: float in [0,4.75,8.9,15.85,23.9]:
		muted.seek(time_)
		muted.set_playing(false)
		muted.set_playing(true)
		await process_frame
		silent=silent and muted.playing and not muted.audio_player.playing
	muted.replay()
	await process_frame
	silent=silent and muted.playing and not muted.audio_player.playing
	root.focus_exited.emit()
	await process_frame
	silent=silent and not muted.playing and not muted.audio_player.playing
	muted.set_playing(true)
	await process_frame
	silent=silent and muted.playing and not muted.audio_player.playing
	_record("zero remains silent across seek resume replay and focus",silent,{"audio_players":_count_players(muted)})
	var paused_at: float=muted.current_time
	root.focus_exited.emit()
	await create_timer(.05).timeout
	_record("focus loss pauses muted visual timeline",not muted.playing and is_equal_approx(muted.current_time,paused_at))
	current_scene=null
	muted.queue_free()
	await create_timer(.1).timeout
	_record("freed muted viewer disconnects window callback",root.focus_exited.get_connections().size()==focus_baseline)
	_setting(.35)
	var audible=script.new()
	root.add_child(audible)
	current_scene=audible
	await process_frame
	_record("nonzero setting applies expected gain and one player",audible.ready_to_play and is_equal_approx(audible.audio_player.volume_db,-2.0+linear_to_db(.35)) and audible.audio_player.playing and _count_players(audible)==1,{"volume_db":audible.audio_player.volume_db})
	var started: float=audible.current_time
	await create_timer(.06).timeout
	var advanced: bool=audible.current_time>started
	audible.set_playing(false)
	paused_at=audible.current_time
	await create_timer(.05).timeout
	_record("nonzero play and pause synchronize timeline and stream",advanced and not audible.playing and audible.audio_player.stream_paused and is_equal_approx(audible.current_time,paused_at))
	audible.seek(8.55)
	_record("paused seek stops nonzero soundtrack",not audible.audio_player.playing and is_equal_approx(audible.current_time,8.55))
	audible.set_playing(true)
	await process_frame
	_record("resume restarts one stream at timeline position",audible.playing and audible.audio_player.playing and not audible.audio_player.stream_paused and absf(audible.audio_player.get_playback_position()-audible.current_time)<.15,{"timeline":audible.current_time,"audio_position":audible.audio_player.get_playback_position()})
	root.focus_exited.emit()
	await create_timer(.04).timeout
	_record("focus loss pauses nonzero soundtrack",not audible.playing and audible.audio_player.stream_paused)
	audible.sample_time(15.85,true)
	_record("capture remains silent at nonzero saved volume",not audible.audio_player.playing and not audible.playing)
	audible.set_playing(true)
	var previous: WeakRef=weakref(audible)
	audible.return_to_courtyard()
	for unused in range(5): await process_frame
	_record("Return frees film and leaves only courtyard focus callback",not is_instance_valid(previous.get_ref()) and current_scene.scene_file_path=="res://scenes/courtyard.tscn" and root.focus_exited.get_connections().size()==focus_baseline+1)
	root.focus_exited.emit()
	current_scene.queue_free()
	current_scene=null
	await create_timer(.1).timeout
	_record("scene cleanup releases remaining focus callback",root.focus_exited.get_connections().size()==focus_baseline)
	if had_settings:
		var restored:=FileAccess.open(SETTINGS,FileAccess.WRITE)
		restored.store_buffer(saved_settings)
		restored.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var passed:=true
	for check in checks: passed=passed and check.passed
	var report:={"passed":passed,"engine":Engine.get_version_info().string,"sources":{"director":FileAccess.get_sha256(director_path),"runner":FileAccess.get_sha256(get_script().resource_path),"courtyard_settings_source":FileAccess.get_sha256("res://scripts/courtyard.gd"),"soundtrack":FileAccess.get_sha256("res://assets/cinematics/audio/confluence-duel-mix.wav")},"checks":checks,"scope":"Headless actual AudioStreamPlayer state and director lifecycle. Zero volume never starts playback. Focus events are explicitly emitted notifications; OS input and audible quality require separate review. Settings are restored after fixtures."}
	if not output.is_empty():
		var file:=FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed=false
	print("YUGA_COMBAT_FILM_AUDIO_CASES ",JSON.stringify(report))
	quit(0 if passed else 1)
