extends SceneTree
const Audio = preload("res://scripts/invocation_audio.gd")
var audio: Node
var checks: Array=[]
var pins: Dictionary={}
func _initialize() -> void: call_deferred("run")
func check(name_: String, passed: bool, evidence: Dictionary={}) -> void:
	checks.append({"name":name_,"passed":passed,"evidence":evidence});print("PASS " if passed else "FAIL ",name_)
func ev(kind: String, seq: int, cast_id := 1, hero := "rama", epoch := 1) -> Dictionary:
	return {"schema":1,"kind":kind,"epoch":epoch,"cast_id":cast_id,"event_seq":seq,"hero_id":hero,"effect_id":hero+".r.v1","team":"sun","time_s":1.0,"age_s":.1,"origin":Vector3.ZERO,"forward":Vector3.FORWARD,"target":Vector3(0,0,10),"timing":{},"geometry":{},"receipts":[],"reason":"test"}
func stable() -> Dictionary:
	var r: Dictionary=audio.report();r.erase("rejected");return r
func rejected(e: Variant, name_: String) -> void:
	var before := stable();var result: Dictionary=audio.consume_event(e)
	check(name_,not result.ok and stable()==before,{"code":result.code})
func count_nodes(n: Node) -> int:
	var result:=1
	for child in n.get_children(): result+=count_nodes(child)
	return result
func run() -> void:
	for path in ["res://scripts/invocation_audio.gd","res://tests/invocation_audio_cases.gd","res://assets/audio/invocations/manifest.json"]: pins[path]=FileAccess.get_sha256(path)
	audio=Audio.new();root.add_child(audio);await process_frame
	check("sixteen_original_streams_and_exact_three_players",audio.report().ready and audio.report().streams==16 and audio.report().players==3 and count_nodes(audio)==4,{"report":audio.report()})
	var safe := true;var unique := {};var stream_details := []
	for file_name in audio._streams:
		var stream: AudioStreamWAV=audio._streams[file_name]
		safe=safe and stream.mix_rate==48000 and not stream.stereo and stream.format==AudioStreamWAV.FORMAT_16_BITS and stream.loop_mode==AudioStreamWAV.LOOP_DISABLED and stream.get_length()<=.5
		unique[stream.data.hex_encode().sha256_text()]=true
		var import_path: String=Audio.DIRECTORY+file_name+".import"
		if FileAccess.file_exists(import_path): pins[import_path]=FileAccess.get_sha256(import_path)
		stream_details.append({"cue":file_name,"rate":stream.mix_rate,"stereo":stream.stereo,"format":stream.format,"length":stream.get_length(),"loop_mode":stream.loop_mode})
	check("all_pcm_are_short_nonlooping_unique_and_48khz",safe and unique.size()==16,{"streams":stream_details})
	check("begin_plays_one_original_windup",audio.consume_event(ev("begin",1)).ok and audio.report().played==1 and audio.report().playing==1)
	rejected(ev("begin",1),"duplicate_begin_does_not_replay")
	check("release_selects_rama_timbre_once",audio.consume_event(ev("release",2)).ok and audio.report().played==2 and audio.report().playing==1 and audio.report().voices.any(func(v): return v.playing and v.cue=="rama-release.wav"))
	rejected(ev("release",3),"higher_sequence_duplicate_release_is_silent")
	var played: int=audio.report().played
	var silent_ticks := true
	for seq in range(3,203): silent_ticks=silent_ticks and audio.consume_event(ev("tick" if seq%2==0 else "impact",seq)).ok
	check("200_tick_and_impact_events_do_not_restart_sound",silent_ticks and audio.report().played==played and count_nodes(audio)==4)
	check("end_retires_cast_and_stops_sound",audio.consume_event(ev("end",203)).ok and audio.report().active.is_empty() and audio.report().playing==0)
	rejected(ev("release",204),"late_release_after_end_rejected")
	rejected(ev("begin",204),"cast_id_cannot_be_reused")
	check("next_cast_begin_accepted",audio.consume_event(ev("begin",204,2)).ok)
	check("cancel_retires_and_plays_short_cue",audio.consume_event(ev("cancel",205,2)).ok and audio.report().active.is_empty() and audio.report().voices.any(func(v): return v.playing and v.cue=="cancel.wav"))
	for key in ["kind","epoch","cast_id","event_seq","hero_id","effect_id","team","time_s","origin"]:
		var malformed := ev("begin",206,3);malformed[key]={}
		rejected(malformed,"reject_malformed_"+key)
	for value in [NAN,INF,-1.0]:
		var malformed := ev("begin",206,3);malformed.time_s=value
		rejected(malformed,"reject_nonfinite_time_"+str(value))
	var malformed := ev("begin",206,3);malformed.target=Vector3(INF,0,0)
	rejected(malformed,"reject_nonfinite_vector")
	malformed=ev("begin",206,3);malformed.effect_id="rama.r.v2"
	rejected(malformed,"effect_version_mismatch_rejected")
	malformed=ev("begin",206,3);malformed.hero_id="unknown"
	rejected(malformed,"unknown_hero_cannot_load_resource")
	var unchanged: float=audio.report().volume
	check("nonfinite_volume_preserves_previous_setting",not audio.set_volume(NAN) and audio.report().volume==unchanged)
	check("volume_clamps_high",audio.set_volume(100) and audio.report().volume==1)
	check("zero_volume_truly_stops_voices",audio.set_volume(0) and audio.report().playing==0)
	played=audio.report().played
	check("muted_begin_and_release_consume_silently",audio.consume_event(ev("begin",206,3)).ok and audio.consume_event(ev("release",207,3)).ok and audio.report().played==played and audio.report().playing==0)
	audio.set_volume(.5)
	rejected(ev("release",207,3),"unmute_cannot_replay_consumed_release")
	check("unmute_does_not_restart_old_voice",audio.report().playing==0)
	audio.consume_event(ev("end",208,3));audio.consume_event(ev("begin",209,4))
	audio.set_suspended(true)
	check("suspension_stops_current_sound",audio.report().playing==0 and audio.report().suspended)
	played=audio.report().played
	check("suspended_release_consumed_without_voice",audio.consume_event(ev("release",210,4)).ok and audio.report().played==played)
	audio.set_suspended(false)
	rejected(ev("release",210,4),"resume_cannot_replay_release")
	audio.reset()
	check("local_reset_clears_voices_keeps_epoch_and_watermark",audio.report().playing==0 and audio.report().active.is_empty() and audio.report().epoch==1 and audio.report().last_event_seq==210)
	rejected(ev("begin",209,4),"late_event_after_local_reset_rejected")
	rejected(ev("reset",211,0),"same_epoch_reset_cannot_retire_current_session")
	check("higher_epoch_reset_starts_new_serial_space",audio.consume_event(ev("reset",1,0,"rama",4)).ok and audio.report().epoch==4 and audio.report().last_event_seq==1 and audio.report().last_cast_id==0)
	rejected(ev("begin",999,99,"rama",1),"old_epoch_never_plays")
	var manifest: Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/audio/invocations/manifest.json"))
	var seq := 2;var cast_id := 1;var timbres := true
	for hero in manifest.heroes:
		timbres=timbres and audio.consume_event(ev("begin",seq,cast_id,hero,4)).ok
		timbres=timbres and audio.consume_event(ev("release",seq+1,cast_id,hero,4)).ok
		timbres=timbres and audio.report().voices.any(func(v): return v.playing and v.cue==hero+"-release.wav")
		audio.consume_event(ev("end",seq+2,cast_id,hero,4));seq+=3;cast_id+=1
	check("all_fourteen_heroes_select_distinct_original_release",timbres)
	var bounded := true;var max_playing := 0;var playback_refs: Array[WeakRef]=[]
	for i in 1000:
		bounded=bounded and audio.consume_event(ev("begin",seq,cast_id,"rama",4)).ok and audio.consume_event(ev("release",seq+1,cast_id,"rama",4)).ok
		max_playing=maxi(max_playing,audio.report().playing)
		if i%100==0:
			for voice in audio._voices:
				if voice.playing: playback_refs.append(weakref(voice.get_stream_playback()))
		audio.consume_event(ev("end",seq+2,cast_id,"rama",4));seq+=3;cast_id+=1
		bounded=bounded and count_nodes(audio)==4 and audio.report().playing==0
	check("1000_casts_no_node_or_voice_growth",bounded and max_playing<=3,{"maximum_playing":max_playing,"players":audio.report().players,"nodes":count_nodes(audio)})
	paused=true
	played=audio.report().played
	check("paused_tree_onsets_consumed_without_playback",audio.consume_event(ev("begin",seq,cast_id,"rama",4)).ok and audio.consume_event(ev("release",seq+1,cast_id,"rama",4)).ok and audio.report().played==played and audio.report().playing==0)
	paused=false
	rejected(ev("release",seq+1,cast_id,"rama",4),"tree_resume_cannot_replay_suppressed_release")
	check("resume_has_no_delayed_audio_queue",audio.report().playing==0)
	var frozen := true
	for path in pins: frozen=frozen and pins[path]==FileAccess.get_sha256(path)
	check("source_frozen",frozen)
	var weak: WeakRef=weakref(audio);audio.queue_free();await process_frame
	# Dummy mixer retirement is asynchronous; observe actual sampled playback release.
	var retire_start := Time.get_ticks_msec()
	while playback_refs.any(func(ref_: WeakRef): return ref_.get_ref()!=null) and Time.get_ticks_msec()-retire_start<1000:
		await create_timer(.025).timeout
	check("stopped_playbacks_retire_within_one_second",not playback_refs.any(func(ref_: WeakRef): return ref_.get_ref()!=null),{"sampled_playbacks":playback_refs.size(),"wait_ms":Time.get_ticks_msec()-retire_start})
	check("teardown_frees_all_audio_players",weak.get_ref()==null)
	var passed := true
	for c in checks: passed=passed and c.passed
	var report_ := {"passed":passed,"checks":checks,"source_sha256":pins,"engine":Engine.get_version_info().string,"scope":"Original PCM structural checks and actual Dummy AudioStreamPlayer lifecycle/event/mute tests. No listening or perceptual quality claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE);file.store_string(JSON.stringify(report_,"\t")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
