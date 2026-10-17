extends SceneTree
const Audio = preload("res://scripts/rama_action_audio.gd")
const Army = preload("res://scripts/lane_army.gd")
const Kit = preload("res://scripts/rama_ability_kit.gd")
const Vitals = preload("res://scripts/rama_vitals.gd")
const SOURCE := "res://art/audio/rama-quality/runtime/"
var audio: Node3D
var checks: Array = []
var pins := {}
var seq := 0
var generation := 1
var clock := 0.0
var kit_results: Array = []
var playback_refs: Array[WeakRef] = []
func _initialize() -> void: call_deferred("run")
func check(label: String, passed: bool, detail: Dictionary = {}) -> void:
	checks.append({"name":label, "passed":passed, "evidence":detail})
	print("PASS " if passed else "FAIL ", label)
func event(kind: String, id := 1, ability := "kodanda", age := 0.0, release_age := -1.0) -> Dictionary:
	seq += 1; clock += .001
	var windup: float = {"kodanda":.18, "piercing_dawn":.65, "measured_step":.1, "guardian_circle":.55, "dawn_volley":.95}[ability]
	var projectiles := []
	if ability == "dawn_volley":
		for i in 3: projectiles.append({"index":i, "delay_s":.1*i})
	return {"schema":1, "kind":kind, "generation":generation, "epoch":generation, "cast_id":id, "event_seq":seq, "hero_id":"rama", "ability_id":ability, "time_s":clock, "age_s":age, "release_age_s":release_age, "origin":Vector3.ZERO, "forward":Vector3.FORWARD, "target":Vector3(0,0,-5), "timing":{"windup_s":windup, "recovery_s":.22}, "geometry":{"projectiles":projectiles}, "receipts":[]}
func reset_session() -> void:
	generation += 1
	var e := event("reset", 0); e.ability_id = ""
	check("advance_generation_%d" % generation, audio.consume_event(e).ok)
func stable() -> Dictionary:
	var r: Dictionary = audio.report(); r.erase("rejected"); return r
func reject(e: Variant, label: String) -> void:
	var before := stable(); var result: Dictionary = audio.consume_event(e)
	check(label, not result.ok and stable() == before, {"code":result.code})
func reject_damage(receipt: Variant, label: String) -> void:
	var before := stable(); var result: Dictionary = audio.consume_damage(receipt)
	check(label, not result.ok and stable() == before, {"code":result.code})
func nodes(n: Node) -> int:
	var result := 1
	for c in n.get_children(): result += nodes(c)
	return result
func damage(time: float, health := 280.0, source := "enemy_siege:1", sequence := 0, gen := 1) -> Dictionary:
	return {"accepted":true, "generation":gen, "source_id":source, "sequence":sequence, "time_s":time, "health_before":300.0, "health_after":health, "shield_before":0.0, "shield_after":0.0, "damage_applied":300-health}
func run() -> void:
	for path in ["res://scripts/rama_action_audio.gd", "res://tests/rama_action_audio_cases.gd", SOURCE+"manifest.json"]: pins[path] = FileAccess.get_sha256(path)
	audio = Audio.new(SOURCE); root.add_child(audio); await process_frame
	check("fifteen_original_cues_exact_four_player_budget", audio.report().ready and audio.report().streams == 15 and audio.report().players == 4 and nodes(audio) == 5, audio.report())
	var pcm := true; var unique := {}
	for cue in audio._streams:
		var stream: AudioStreamWAV = audio._streams[cue]
		pcm = pcm and stream.mix_rate == 48000 and not stream.stereo and stream.format == AudioStreamWAV.FORMAT_16_BITS and stream.loop_mode == AudioStreamWAV.LOOP_DISABLED and stream.get_length() <= 1
		unique[stream.data.hex_encode().sha256_text()] = true
	check("actual_loaded_pcm_48k_mono16_unique_finite_nonlooping", pcm and unique.size() == 15)
	check("three_spatial_one_local_feedback_no_added_bus", audio._world.size() == 3 and audio._feedback is AudioStreamPlayer and audio._world.all(func(v): return v.max_distance == 36 and v.max_db == -18 and v.bus == &"Master") and audio._feedback.bus == &"Master")
	var begin := event("begin")
	check("accepted_begin_plays_tension_once", audio.consume_event(begin).ok and audio.report().played == 1 and audio.report().playing == 1)
	reject(begin, "duplicate_begin_does_not_replay")
	var early := event("release", 1, "kodanda", .1, .1)
	reject(early, "release_before_authority_windup_rejected")
	check("actual_primary_release_replaces_its_draw", audio.consume_event(event("release", 1, "kodanda", .2, .2)).ok and audio.report().played == 2 and audio.report().playing == 1 and audio.report().voices.any(func(v): return v.playing and v.cue == "release_kodanda"))
	reject(event("release", 1, "kodanda", .2, .2), "higher_sequence_duplicate_release_rejected")
	var played: int = audio.report().played
	for i in 50: audio.consume_event(event("tick", 1, "kodanda", .25+i*.001, .2))
	check("fifty_projectile_ticks_do_not_restart_sound", audio.report().played == played)
	var impact := event("impact", 1, "kodanda", .35, .2)
	impact.reason = "unit"; impact.projectile_index = 0; impact.contact_position = Vector3(0,1,-5)
	impact.receipts = [{"kind":"damage", "unit_id":12, "position":Vector3(0,0,-5), "damage_applied":28.0}]
	check("accepted_damage_receipt_selects_contact_and_local_confirm", audio.consume_event(impact).ok and audio.report().played == played+2 and audio.report().voices.any(func(v): return v.playing and v.cue == "confirm" and not v.spatial))
	played = audio.report().played
	impact.event_seq = seq+1; seq += 1; impact.time_s = clock+.001; clock += .001
	check("same_unit_and_projectile_cannot_repeat_confirm", audio.consume_event(impact).ok and audio.report().played == played)
	var empty_hit := event("impact", 1, "kodanda", .4, .2); empty_hit.reason = "unit"
	check("missing_damage_receipt_is_silent", audio.consume_event(empty_hit).ok and audio.report().played == played)
	var wall := event("impact", 1, "kodanda", .45, .2); wall.reason = "wall"; wall.projectile_index = 0
	check("cover_impact_uses_dull_contact_without_success", audio.consume_event(wall).ok and audio.report().played == played+1)
	check("end_retires_cast_and_voices", audio.consume_event(event("end", 1, "kodanda", 1.2, .2)).ok and audio.report().active_casts == 0 and audio.report().playing == 0)
	reject(event("release", 1, "kodanda", .2, .2), "retired_cast_cannot_sound_again")
	reject(event("begin", 1), "cast_identity_cannot_be_reused")
	for key in ["kind", "generation", "epoch", "cast_id", "event_seq", "hero_id", "ability_id", "age_s", "origin", "timing", "receipts"]:
		var e := event("begin", 2); e[key] = {}
		reject(e, "malformed_%s_has_no_audio_or_state_change" % key)
	# These explicitly reject dynamic types before scalar comparisons. A false
	# return after a script exception is NOT valid rejection; the shared runner
	# additionally rejects every SCRIPT ERROR anywhere in the full engine log.
	for key in ["schema", "epoch", "hero_id", "ability_id"]:
		for index in 4:
			var bad_scalar: Variant = [null, {}, [], true][index]
			var malformed_scalar := event("begin", 2); malformed_scalar[key] = bad_scalar
			reject(malformed_scalar, "scalar_type_%s_case_%d_rejected_without_engine_error" % [key, index])
	for index in 4:
		var malformed_projectile := event("begin", 2, "dawn_volley")
		malformed_projectile.geometry.projectiles[0].index = [null, {}, [], true][index]
		reject(malformed_projectile, "projectile_index_type_case_%d_rejected_without_engine_error" % index)
	for index in 4:
		var malformed_damage := damage(.5); malformed_damage.accepted = [null, {}, [], 1][index]
		reject_damage(malformed_damage, "damage_accepted_type_case_%d_rejected_without_engine_error" % index)
	for value in [NAN, INF, -1.0]:
		var e := event("begin", 2); e.time_s = value
		reject(e, "nonfinite_or_negative_clock_%s_rejected" % str(value))
	var bad := event("begin", 2); bad.origin = Vector3(INF,0,0)
	reject(bad, "nonfinite_spatial_position_rejected")
	check("next_valid_cast_survives_malformed_attempts", audio.consume_event(event("begin", 2, "dawn_volley")).ok)
	var wrong := event("release", 2, "dawn_volley", .95, .95); wrong.geometry.projectiles[1].delay_s = 0
	reject(wrong, "changed_volley_stagger_cannot_emit_early_pulse")
	check("volley_first_pulse_on_authority_release", audio.consume_event(event("release", 2, "dawn_volley", .95, .95)).ok)
	played = audio.report().played
	check("volley_early_tick_silent", audio.consume_event(event("tick", 2, "dawn_volley", 1.0, .95)).ok and audio.report().played == played)
	check("volley_second_pulse_on_existing_tick", audio.consume_event(event("tick", 2, "dawn_volley", 1.05, .95)).ok and audio.report().played == played+1)
	check("volley_third_pulse_on_existing_tick", audio.consume_event(event("tick", 2, "dawn_volley", 1.15, .95)).ok and audio.report().played == played+2)
	check("volley_later_tick_does_not_repeat_pulses", audio.consume_event(event("tick", 2, "dawn_volley", 1.2, .95)).ok and audio.report().played == played+2)
	var changed := event("tick", 2, "dawn_volley", 1.25, .9)
	reject(changed, "changed_release_age_cannot_retime_existing_cast")
	check("cancel_stops_cast_and_damps_tension", audio.consume_event(event("cancel", 2, "dawn_volley", 1.3, .95)).ok and audio.report().active_casts == 0 and audio.report().voices.any(func(v): return v.playing and v.cue == "cancel"))
	reset_session()
	check("reset_clears_all_voices", audio.report().playing == 0)
	var volume: float = audio.report().volume
	check("nonfinite_volume_preserves_setting", not audio.set_volume(NAN) and audio.report().volume == volume)
	check("volume_clamps_high", audio.set_volume(100) and audio.report().volume == 1)
	audio.consume_event(event("begin"))
	check("zero_volume_stops_existing_players_immediately", audio.set_volume(0) and audio.report().playing == 0)
	played = audio.report().played
	check("muted_release_is_consumed_silently", audio.consume_event(event("release", 1, "kodanda", .2, .2)).ok and audio.report().played == played)
	audio.set_volume(.5)
	reject(event("release", 1, "kodanda", .2, .2), "unmute_cannot_replay_consumed_release")
	check("unmute_has_no_delayed_queue", audio.report().playing == 0)
	reset_session(); audio.consume_event(event("begin", 1, "dawn_volley")); audio.consume_event(event("release", 1, "dawn_volley", .95, .95))
	audio.set_suspended(true); played = audio.report().played
	check("pause_stops_every_voice", audio.report().playing == 0)
	check("paused_volley_pulses_consumed_without_queue", audio.consume_event(event("tick", 1, "dawn_volley", 1.2, .95)).ok and audio.report().played == played)
	audio.set_suspended(false)
	check("resume_does_not_replay_suppressed_volley", audio.consume_event(event("tick", 1, "dawn_volley", 1.3, .95)).ok and audio.report().playing == 0 and audio.report().played == played)
	reset_session(); audio.consume_event(event("begin")); audio.set_focused(false)
	check("focus_loss_stops_every_voice", audio.report().playing == 0)
	played = audio.report().played; audio.consume_event(event("release", 1, "kodanda", .2, .2)); audio.set_focused(true)
	check("focus_return_does_not_replay_sound", audio.report().playing == 0 and audio.report().played == played)
	var hit := damage(1.0)
	check("real_vitals_shape_selects_local_damage_cue", audio.consume_damage(hit).ok and audio.report().voices.any(func(v): return v.playing and v.cue == "threat" and v.priority == 3))
	played = audio.report().played
	var replay: Dictionary = audio.consume_damage(hit)
	check("repeated_damage_receipt_is_silent", not replay.ok and audio.report().played == played)
	var fake := damage(1.1); fake.health_after = 300
	check("inconsistent_damage_math_cannot_create_threat", not audio.consume_damage(fake).ok and audio.report().played == played)
	var lower := event("impact", 1, "kodanda", .4, .2); lower.reason = "unit"; lower.receipts = [{"kind":"damage", "unit_id":25, "position":Vector3.ZERO, "damage_applied":28.0}]
	audio.consume_event(lower)
	check("hit_confirmation_cannot_evict_local_incoming_damage", audio.report().voices.any(func(v): return v.playing and v.cue == "threat" and v.priority == 3))
	check("defeat_stops_all_no_orphan_voices", audio.consume_damage(damage(1.2, 0.0, "enemy_siege:2")).ok and not audio.report().alive and audio.report().playing == 0)
	played = audio.report().played
	reset_session(); audio.consume_event(event("begin"))
	check("dead_hero_cannot_sound_until_explicit_respawn", audio.report().played == played and audio.report().playing == 0)
	audio.set_alive(true); audio.consume_event(event("release", 1, "kodanda", .2, .2))
	check("explicit_respawn_allows_new_receipts_only", audio.report().played == played+1)
	reset_session()
	for id in range(1,4):
		audio.consume_event(event("begin", id)); audio.consume_event(event("release", id, "kodanda", .2, .2))
	var dropped: int = audio.report().dropped
	audio.consume_event(event("begin", 4))
	check("lower_priority_draw_cannot_evict_three_releases", audio.report().dropped == dropped+1 and audio.report().voices.filter(func(v): return v.playing and v.cue == "release_kodanda").size() == 3)
	var bounded_damage := true
	for i in 100: bounded_damage = bounded_damage and audio.consume_damage(damage(2.0+i*.1, 280, "source:%d" % i, 0, 2)).ok
	check("damage_watermarks_bounded_to_64_sources", bounded_damage and audio.report().damage_sources == 64)
	reset_session()
	for id in range(1,13): audio.consume_event(event("begin", id))
	check("active_cast_state_capped_at_twelve", audio.report().active_casts == 12)
	reject(event("begin", 13), "thirteenth_cast_cannot_grow_state")
	var last_seq: int = audio.report().last_event_seq
	audio.reset()
	check("local_cleanup_preserves_watermarks", audio.report().playing == 0 and audio.report().active_casts == 0 and audio.report().last_event_seq == last_seq)
	reset_session(); audio.consume_event(event("begin")); paused = true; await process_frame
	check("actual_tree_pause_stops_playing_voices", audio.report().playing == 0)
	played = audio.report().played; audio.consume_event(event("release", 1, "kodanda", .2, .2)); paused = false
	check("tree_pause_receipt_consumed_without_delayed_replay", audio.report().playing == 0 and audio.report().played == played)
	reset_session(); audio.consume_event(event("begin")); audio.consume_event(event("release", 1, "kodanda", .2, .2))
	for i in 100:
		var crowded := event("impact", 1, "kodanda", .4, .2); crowded.reason = "unit"
		crowded.receipts = [{"kind":"damage", "unit_id":1000+i, "position":Vector3.ZERO, "damage_applied":1.0}]
		audio.consume_event(crowded)
	check("per_cast_contact_dedup_state_never_exceeds_eighteen", audio._active[1].confirmed.size() == 18)
	reset_session()
	var bounded := true
	for i in 1000:
		var id := i+1
		bounded = bounded and audio.consume_event(event("begin", id)).ok and audio.consume_event(event("release", id, "kodanda", .2, .2)).ok and audio.consume_event(event("end", id, "kodanda", 1.2, .2)).ok
		bounded = bounded and nodes(audio) == 5 and audio.report().active_casts == 0 and audio.report().playing <= 4
	check("1000_casts_no_node_voice_or_state_growth", bounded, {"nodes":nodes(audio), "report":audio.report()})
	var gains := true
	for v in audio.report().voices: gains = gains and v.volume_db <= -18 and v.pitch_scale >= .988-.000001 and v.pitch_scale <= 1.012+.000001
	check("all_voice_gains_and_variation_remain_bounded", gains, {"voices":audio.report().voices, "pitch_float_tolerance":.000001})
	# Test-only numeric mixer probe. Runtime owns no bus/effect/timer.
	audio.reset(); audio.set_volume(1)
	var listener := AudioListener3D.new(); root.add_child(listener); listener.make_current()
	var probe_bus: int = AudioServer.bus_count
	AudioServer.add_bus(probe_bus); AudioServer.set_bus_name(probe_bus, "RamaAudioProbe")
	AudioServer.set_bus_send(probe_bus, &"Master")
	var capture := AudioEffectCapture.new(); capture.buffer_length = 2.0
	AudioServer.add_bus_effect(probe_bus, capture)
	for voice in audio._world: voice.bus = &"RamaAudioProbe"
	audio._feedback.bus = &"RamaAudioProbe"
	capture.clear_buffer()
	for id in range(1,4): audio._play("release_piercing_dawn", Vector3.ZERO, 2, id)
	audio._play("threat", Vector3.ZERO, 3, 0, true)
	var four_playing: bool = audio.report().playing == 4
	await create_timer(.8).timeout
	var frames: PackedVector2Array = capture.get_buffer(capture.get_frames_available())
	var actual_peak := 0.0; var energy := 0.0
	for frame in frames:
		actual_peak = maxf(actual_peak, maxf(absf(frame.x), absf(frame.y)))
		energy += frame.x*frame.x + frame.y*frame.y
	check("actual_dummy_four_voice_mixer_fixture_has_numeric_headroom", four_playing and frames.size() > 0 and actual_peak > 0 and actual_peak <= .085, {"captured_stereo_frames":frames.size(), "mix_rate_hz":AudioServer.get_mix_rate(), "peak_linear":actual_peak, "headroom_db":-linear_to_db(actual_peak) if actual_peak > 0 else 0, "rms_linear":sqrt(energy/(2*frames.size())) if not frames.is_empty() else 0, "scope":"One fixed four-voice Dummy mix with listener and test-only capture bus; no whole-game/device/listening acceptance."})
	audio._stop_all()
	for voice in audio._world: voice.bus = &"Master"
	audio._feedback.bus = &"Master"; AudioServer.remove_bus(probe_bus); listener.queue_free()
	audio.set_volume(.5)
	var actual_audio := Audio.new(SOURCE); root.add_child(actual_audio)
	var army := Army.new(); army.visual_enabled = false; root.add_child(army); army.set_physics_process(false)
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/world/confluence-map.json"))
	var army_ok: bool = army.configure(manifest, null)
	var kit := Kit.new(); root.add_child(kit)
	kit.ability_event.connect(func(e): kit_results.append(actual_audio.consume_event(e)))
	check("actual_army_and_kit_configure_for_audio_receipts", army_ok and kit.configure(army))
	kit.set_origin_sampler(func(): return Vector3.ZERO)
	kit.set_movement_receiver(func(_start, destination, _duration): return {"accepted":true, "destination":destination})
	var all_abilities := true
	var action_details := []
	for ability in Audio.IDS:
		army.reset()
		for unit in army.units.duplicate(): army.units.erase(unit); unit.free()
		army._rebuild_buckets()
		var before: int = actual_audio.report().played
		var accepted: Dictionary = kit.request_ability(ability, Vector3.ZERO, Vector3.FORWARD, Vector3.ZERO, {"step_direction":Vector3.RIGHT})
		for step in 125: army.step_simulation(.05)
		var added: int = actual_audio.report().played-before
		all_abilities = all_abilities and accepted.accepted and added == (4 if ability == "dawn_volley" else 2)
		action_details.append({"ability":ability, "accepted":accepted.accepted, "onsets":added})
	check("all_five_real_kit_lifecycles_select_expected_onsets", all_abilities, {"actions":action_details})
	check("all_actual_kit_snapshots_accepted_without_schema_translation", not kit_results.is_empty() and kit_results.all(func(r): return r.ok) and actual_audio.report().rejected == 0, {"events":kit_results.size(), "report":actual_audio.report()})
	var vitals := Vitals.new(); root.add_child(vitals)
	check("actual_vitals_receiver_configures", vitals.configure(army) and actual_audio.set_receiver_generation(vitals.generation))
	var actual_damage: Dictionary = vitals.receive_damage(20.0, "audio_fixture", vitals.generation, 0)
	check("actual_vitals_damage_receipt_selects_local_cue", actual_audio.consume_damage(actual_damage).ok)
	if actual_audio._feedback.playing: playback_refs.append(weakref(actual_audio._feedback.get_stream_playback()))
	var actual_death: Dictionary = vitals.receive_damage(500.0, "audio_fixture", vitals.generation, 1)
	check("actual_vitals_defeat_stops_entire_audio_pool", actual_audio.consume_damage(actual_death).ok and actual_audio.report().playing == 0 and not actual_audio.report().alive)
	var retired_generation: int = vitals.generation
	vitals.reset(); actual_audio.reset(); actual_audio.set_receiver_generation(vitals.generation); actual_audio.set_alive(true)
	var played_before_stale: int = actual_audio.report().played
	var stale_damage: Dictionary = actual_audio.consume_damage(damage(3.0, 280, "late_old_generation", 1, retired_generation))
	check("explicit_receiver_reset_rejects_delayed_prior_life_damage", not stale_damage.ok and actual_audio.report().played == played_before_stale and actual_audio.report().playing == 0)
	var future_damage: Dictionary = actual_audio.consume_damage(damage(3.1, 280, "future_generation", 1, vitals.generation+1))
	check("future_damage_generation_cannot_rebind_live_receiver", not future_damage.ok and actual_audio.report().receiver_generation == vitals.generation)
	check("receiver_generation_cannot_move_backwards", not actual_audio.set_receiver_generation(retired_generation))
	vitals.queue_free(); kit.queue_free(); army.queue_free(); actual_audio.queue_free(); await process_frame
	var frozen := true
	for path in pins: frozen = frozen and pins[path] == FileAccess.get_sha256(path)
	check("sources_frozen_for_run", frozen)
	var weak: WeakRef = weakref(audio); audio.queue_free(); await process_frame
	check("teardown_frees_entire_player_pool", weak.get_ref() == null)
	var retire_start: int = Time.get_ticks_msec()
	while playback_refs.any(func(ref_: WeakRef): return ref_.get_ref() != null) and Time.get_ticks_msec()-retire_start < 1000:
		await create_timer(.025).timeout
	check("stopped_dummy_playback_retires_within_one_second", not playback_refs.any(func(ref_: WeakRef): return ref_.get_ref() != null), {"sampled_playbacks":playback_refs.size(), "wait_ms":Time.get_ticks_msec()-retire_start})
	var passed := checks.all(func(c): return c.passed)
	var report := {"passed":passed, "checks":checks, "source_sha256":pins, "engine":Engine.get_version_info().string, "scope":"Original PCM plus actual Dummy-driver event/voice/lifecycle counterexamples. No listening, device, dense-fight intelligibility or overall-mix quality claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="), FileAccess.WRITE); file.store_string(JSON.stringify(report, "\t")+"\n")
	print(JSON.stringify({"passed":passed, "checks":checks.size()})); quit(0 if passed else 1)
