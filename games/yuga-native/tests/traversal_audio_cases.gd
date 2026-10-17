extends SceneTree
## Actual native player-state verification; Dummy audio is not a listening test.
const AUDIO := preload("res://scripts/traversal_audio.gd")
const SETTINGS := "user://courtyard-settings.cfg"
var checks: Array[Dictionary] = []
var output := ""
var had_settings := false
var saved_settings := PackedByteArray()

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("_run")

func _record(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func _setting(value: Variant) -> void:
	var config := ConfigFile.new()
	config.set_value("audio","volume",value)
	assert(config.save(SETTINGS)==OK)

func _count_players(node: Node) -> int:
	var result := 1 if node is AudioStreamPlayer or node is AudioStreamPlayer3D else 0
	for child in node.get_children(): result += _count_players(child)
	return result

func _wait_wall_clock(seconds: float) -> void:
	# Audio cooldowns use real monotonic time. --fixed-fps can advance many
	# simulated seconds before one physical audio buffer has elapsed.
	var deadline := Time.get_ticks_usec() + int(seconds * 1000000.0)
	while Time.get_ticks_usec() < deadline: await process_frame

func _run() -> void:
	had_settings = FileAccess.file_exists(SETTINGS)
	if had_settings: saved_settings = FileAccess.get_file_as_bytes(SETTINGS)
	if had_settings: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var reader = AUDIO.new()
	_record("missing settings use modest default",is_equal_approx(reader._read_saved_volume(),0.35))
	var fixtures := [
		{"name":"zero","value":0,"expected":0.0},
		{"name":"fraction","value":0.4,"expected":0.4},
		{"name":"negative","value":-1.0,"expected":0.0},
		{"name":"above one","value":3.0,"expected":1.0},
		{"name":"NaN","value":NAN,"expected":0.35},
		{"name":"infinity","value":INF,"expected":0.35},
		{"name":"string","value":"0","expected":0.35},
		{"name":"bool","value":false,"expected":0.35},
		{"name":"array","value":[1],"expected":0.35},
		{"name":"dictionary","value":{"volume":0},"expected":0.35}]
	for fixture in fixtures:
		_setting(fixture.value)
		var result: float = reader._read_saved_volume()
		_record("saved volume "+fixture.name,is_finite(result) and is_equal_approx(result,fixture.expected))
	var unsafe_configs := {
		"constructor syntax":"[audio]\nvolume=Object(\"AudioStreamPlayer\")\n",
		"oversized file":"[audio]\nvolume=\""+"0".repeat(65536)+"\"\n",
		"deep nesting":"[audio]\nvolume="+"[".repeat(12)+"0"+"]".repeat(12)+"\n",
		"unterminated string":"[audio]\nvolume=\"unterminated\n"}
	for label: String in unsafe_configs:
		var unsafe_file := FileAccess.open(SETTINGS,FileAccess.WRITE)
		unsafe_file.store_string(unsafe_configs[label])
		unsafe_file.close()
		var before_hash := FileAccess.get_sha256(SETTINGS)
		_record("unsafe saved config "+label+" rejected and preserved",is_equal_approx(reader._read_saved_volume(),.35) and FileAccess.get_sha256(SETTINGS)==before_hash)
	reader.free()
	var lost_connections := root.focus_exited.get_connections().size()
	var gained_connections := root.focus_entered.get_connections().size()
	_setting(0.0)
	var muted = AUDIO.new()
	root.add_child(muted)
	await process_frame
	muted.play_event("grapple_lock")
	_record("saved zero never starts any player",muted.volume==0.0 and not muted.music_player.playing and muted.get_diagnostics().playing_cues==0)
	muted.queue_free()
	await process_frame
	_setting(1.0)
	var host := Node3D.new()
	root.add_child(host)
	var audio = AUDIO.new()
	audio.configure(.6)
	host.add_child(audio)
	await process_frame
	_record("configure before ready wins over saved volume",is_equal_approx(audio.volume,.6))
	_record("bounded pool starts one music player and six cue players",_count_players(audio)==7 and audio.get_diagnostics().pool_size==6 and audio.music_player.playing)
	var loop: AudioStreamWAV = audio.music_player.stream
	_record("loop covers all twenty seconds without end fade",loop.loop_mode==AudioStreamWAV.LOOP_FORWARD and loop.loop_begin==0 and loop.loop_end==480000 and loop.mix_rate==24000 and loop.stereo and absf(loop.get_length()-20.0)<.001)
	var exact_pcm := loop.format==AudioStreamWAV.FORMAT_16_BITS and loop.data==FileAccess.get_file_as_bytes(AUDIO.BASE+"lane-procession-loop.wav").slice(44)
	for kind: String in AUDIO.EVENT_PRIORITY:
		var stream: AudioStreamWAV = audio._streams[kind]
		exact_pcm = exact_pcm and stream.format==AudioStreamWAV.FORMAT_16_BITS and stream.data==FileAccess.get_file_as_bytes(AUDIO.BASE+kind+".wav").slice(44)
	_record("all eight imported streams preserve verified PCM bytes exactly",exact_pcm)
	var all_kinds := true
	var last_played := 0
	for kind: String in AUDIO.EVENT_PRIORITY:
		audio.play_event(kind,Vector3(2,3,4))
		all_kinds = all_kinds and audio.get_diagnostics().played_events==last_played+1
		last_played = audio.get_diagnostics().played_events
	_record("all seven distinct semantic cues can play",all_kinds,{"played":last_played})
	var before: int = audio.get_diagnostics().played_events
	for index in range(10000): audio.play_event("minion_hit",Vector3(0,1,0))
	_record("ten thousand event flood is bounded and throttled",_count_players(audio)==7 and audio.get_diagnostics().playing_cues<=6 and audio.get_diagnostics().played_events-before<=1 and audio.get_diagnostics().dropped_events>=9999,audio.get_diagnostics())
	before = audio.get_diagnostics().played_events
	audio.play_event("../unknown")
	audio.play_event("coin",Vector3(NAN,0,0))
	_record("unknown cue and nonfinite position rejected",audio.get_diagnostics().played_events==before and audio._last_event_usec.size()<=7)
	await create_timer(.04).timeout
	_record("semantic events duck quiet music",audio.get_diagnostics().duck_db<0.0 and audio.music_player.volume_db<linear_to_db(.6)-20.0)
	audio.set_volume(0)
	for kind: String in AUDIO.EVENT_PRIORITY: audio.play_event(kind)
	_record("mute immediately stops music and all cue players",not audio.music_player.playing and audio.get_diagnostics().playing_cues==0 and audio.get_diagnostics().muted)
	audio.set_suspended(true)
	audio.set_volume(.4)
	_record("unmute while suspended does not start music",not audio.music_player.playing and audio.get_diagnostics().playing_cues==0)
	audio.set_suspended(false)
	_record("resume starts one music stream",audio.music_player.playing and not audio.music_player.stream_paused and _count_players(audio)==7)
	root.focus_exited.emit()
	before = audio.get_diagnostics().played_events
	audio.play_event("flight_exhaust")
	_record("focus loss pauses music and suppresses new cues",audio.music_player.stream_paused and not audio.focused and audio.get_diagnostics().played_events==before and audio.get_diagnostics().playing_cues==0)
	root.focus_entered.emit()
	_record("focus regain resumes owned music",audio.focused and audio.music_player.playing and not audio.music_player.stream_paused)
	paused = true
	await create_timer(.025,true).timeout
	before = audio.get_diagnostics().played_events
	audio.play_event("flight_start")
	_record("scene tree pause freezes audio and refuses signal-triggered cues",audio.music_player.stream_paused and audio.get_diagnostics().played_events==before)
	audio.set_volume(.8)
	audio.set_music_enabled(false)
	audio.set_music_enabled(true)
	_record("settings changes during tree pause remain silent",not audio.music_player.playing and audio.get_diagnostics().playing_cues==0)
	paused = false
	await process_frame
	_record("scene tree resume restores single loop",audio.music_player.playing and not audio.music_player.stream_paused)
	audio.set_music_enabled(false)
	await _wait_wall_clock(.09)
	before = audio.get_diagnostics().played_events
	audio.play_event("coin")
	_record("music off leaves gameplay cues enabled",not audio.music_player.playing and audio.get_diagnostics().played_events==before+1)
	audio.set_volume(NAN)
	_record("nonfinite API volume safely defaults",is_finite(audio.volume) and is_equal_approx(audio.volume,.35))
	audio.set_volume(INF)
	_record("infinite API volume safely defaults",is_finite(audio.volume) and is_equal_approx(audio.volume,.35))
	audio.set_volume(-4)
	_record("negative API volume is mute",audio.volume==0.0 and audio.get_diagnostics().playing_cues==0)
	audio.set_volume(7)
	_record("high API volume clamps without positive cue gain",audio.volume==1.0 and audio.cue_players[0].volume_db<=-6.0 and audio.cue_players[0].max_db<=-6.0)
	var freed: WeakRef = weakref(audio)
	host.queue_free()
	await process_frame
	await process_frame
	_record("scene return releases all players and focus callbacks",not is_instance_valid(freed.get_ref()) and root.focus_exited.get_connections().size()==lost_connections and root.focus_entered.get_connections().size()==gained_connections)
	var repeated := true
	for index in range(4):
		var next = AUDIO.new()
		next.configure(0)
		root.add_child(next)
		await process_frame
		repeated = repeated and _count_players(next)==7 and not next.music_player.playing
		next.queue_free()
		await process_frame
		repeated = repeated and root.focus_exited.get_connections().size()==lost_connections and root.focus_entered.get_connections().size()==gained_connections
	_record("four muted scene recreations leave no player or callback accumulation",repeated)
	if had_settings:
		var file := FileAccess.open(SETTINGS,FileAccess.WRITE)
		file.store_buffer(saved_settings)
		file.close()
	else: DirAccess.remove_absolute(ProjectSettings.globalize_path(SETTINGS))
	var passed := true
	for check in checks: passed = passed and check.passed
	var report := {"passed":passed,"engine":Engine.get_version_info().string,"checks":checks,
		"sources":{"runtime":FileAccess.get_sha256("res://scripts/traversal_audio.gd"),"runner":FileAccess.get_sha256(get_script().resource_path),"settings_validator":FileAccess.get_sha256("res://scripts/input_bindings.gd"),"loop":FileAccess.get_sha256("res://assets/audio/traversal/lane-procession-loop.wav")},
		"scope":"Headless actual AudioStreamPlayer/AudioStreamPlayer3D state, 10000-event flood, settings and scene lifecycle. Focus signals explicitly emitted. No audible-quality, spatial-listening, GPU or OS-focus claim. Saved settings restored."}
	if not output.is_empty():
		var file := FileAccess.open(output,FileAccess.WRITE)
		if file: file.store_string(JSON.stringify(report,"\t")+"\n")
		else: passed = false
	print("YUGA_TRAVERSAL_AUDIO_CASES ",JSON.stringify(report))
	quit(0 if passed else 1)
