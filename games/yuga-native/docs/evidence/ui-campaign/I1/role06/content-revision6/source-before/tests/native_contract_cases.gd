extends SceneTree
const Contracts = preload("res://scripts/native_contracts.gd")
var checks: Array = []
var sources: Dictionary = {}
const PROFILE := "native-offline-triad"
# Exact Batch 1 descriptor, preserved before revision-2 migration.
const CONTENT1_DESCRIPTOR := {"content_sha256":"d6943aafc45ead1b40f87a37ea0bdd6d7724e81eac86a434bfd6f04fc247520d","contract_id":"yuga-native-contracts-v1","map_id":"native-confluence-140x260","map_sha256":"d39043bfaabd9c3e173f03d68423269b5308b60c6906968315405690f844d77c","profile_id":"native-offline-triad","protocol":0.0,"rules_sha256":"5b692277e0257a893eabef198e353673c21359807f998c799f899f71164d84a1","versions":{"content":1.0,"contract":1.0,"entity":1.0,"event":1.0,"input":1.0,"map":1.0,"replay":1.0,"rules":1.0}}
# Exact Mythic descriptor, preserved before Rama revision-3 migration.
const CONTENT2_DESCRIPTOR := {"content_sha256":"f8664b894a5db300974fceb4fee1c8df31ed960b85d6e6f493554066ed86a15b","contract_id":"yuga-native-contracts-v1","map_id":"native-confluence-140x260","map_sha256":"d39043bfaabd9c3e173f03d68423269b5308b60c6906968315405690f844d77c","profile_id":"native-offline-triad","protocol":0.0,"rules_sha256":"3b269f5922e3420948dbc80ddc912aeb1b913ede47ff1705a451fe0c620bf060","versions":{"content":2,"contract":1.0,"entity":1.0,"event":1.0,"input":1.0,"map":1.0,"replay":1.0,"rules":1.0}}
# Exact released Rama revision-3 catalog and its source-derived descriptor.
const CONTENT3_CATALOG_PATH := "res://tests/fixtures/contracts/native-content3-catalog.json"
const CONTENT3_DESCRIPTOR_PATH := "res://tests/fixtures/contracts/native-content3-descriptor.json"
# Exact quality-wave revision-4 catalog and descriptor, before visual integration.
const CONTENT4_CATALOG_PATH := "res://tests/fixtures/contracts/native-content4-catalog.json"
const CONTENT4_DESCRIPTOR_PATH := "res://tests/fixtures/contracts/native-content4-descriptor.json"
const SCOPE := {"room":"FIXTURE","epoch":1,"identity":"hero"}

func _initialize() -> void:
	call_deferred("run")

func check(name_: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"name":name_,"passed":passed,"evidence":evidence})
	print("PASS " if passed else "FAIL ",name_)

func guard(id := PROFILE) -> RefCounted:
	var g := Contracts.new()
	assert(g.load_catalog().ok)
	assert(g.open_session(id,g.descriptor(id),SCOPE).ok)
	return g

func intent(seq := 0) -> Dictionary:
	return {"version":1,"room":"FIXTURE","epoch":1,"seq":seq,"actor_id":"hero","move":[0.0,1.0],"yaw":0.0,"pitch":0.0,"buttons":0}

func event(seq := 0, tick := 0) -> Dictionary:
	return {"version":1,"room":"FIXTURE","epoch":1,"seq":seq,"tick":tick,"kind":"shot","actor_id":"hero","target_id":"","position":[0,1,0],"amount":0}

func entity(id := "hero",kind := "actor") -> Dictionary:
	return {"id":id,"generation":1,"kind":kind,"team":"sun","position":[0,0,0],"yaw":0.0,"pitch":0.0,"discontinuity":0,"alive":true,"ack_input":-1,"owner_id":""}

func snapshot(tick := 0) -> Dictionary:
	return {"version":1,"room":"FIXTURE","epoch":1,"tick":tick,"entities":[entity()]}

func rejected(g: RefCounted, channel: String, v: Variant, name_: String) -> void:
	var before: Dictionary=g.report()
	var result: Dictionary=g.call("accept_"+channel,v)
	check(name_,not result.ok and before==g.report(),{"code":result.code,"transactional":before==g.report()})

func run() -> void:
	for path in ["res://scripts/native_contracts.gd","res://assets/contracts/native-contracts-v1.json","res://tests/native_contract_cases.gd","res://assets/contracts/native-envelope-v1.schema.json", CONTENT3_CATALOG_PATH, CONTENT3_DESCRIPTOR_PATH, CONTENT4_CATALOG_PATH, CONTENT4_DESCRIPTOR_PATH]:
		sources[path]=FileAccess.get_sha256(path)
	var catalog: Variant=JSON.parse_string(FileAccess.get_file_as_string(Contracts.CATALOG_PATH))
	check("catalog_loads_three_separate_rulesets",Contracts.validate_catalog(catalog).ok)
	if not Contracts.validate_catalog(catalog).ok:
		print(Contracts.validate_catalog(catalog));quit(1);return
	var g := guard()
	check("browser_defaults_remain_2_3v3_480",g.profile("browser-p2-3v3").protocol==2 and g.profile("browser-p2-3v3").team_size==3 and g.profile("browser-p2-3v3").duration_seconds==480)
	check("native_offline_not_a_competitive_team_size",g.profile(PROFILE).map_size_xz==[140.0,260.0] and g.profile(PROFILE).team_size==0 and not g.profile(PROFILE).live_handshake)
	check("production_6v6_1080_is_unimplemented_proposal",g.profile("production-6v6").state=="proposed" and g.profile("production-6v6").protocol==0 and g.profile("production-6v6").duration_seconds==1080 and g.profile("production-6v6").map_size_xz==[])
	for alteration in 18:
		var bad: Dictionary=catalog.duplicate(true)
		match alteration:
			0: bad.schema_version=2
			1: bad.profiles[0].team_size=6
			2: bad.profiles[0].duration_seconds=1080
			3: bad.profiles[1].map_size_xz=[140,170]
			4: bad.profiles[2].state="implemented"
			5: bad.profiles[2].map_size_xz=[140,260]
			6: bad.profiles[0].live_handshake=true
			7: bad.profiles[0].map_sha256=""
			8: bad.profiles.append(bad.profiles[0])
			9: bad.envelope_versions.input=0
			10: bad.limits.packet_bytes=1e20
			11: bad.profiles[0].content_sha256="f".repeat(64)
			12: bad.coordinate_contract.up="+Z"
			13: bad.coordinate_contract.collision_layers.world=4
			14: bad.profiles[0].buttons_mask=511
			15: bad.profiles[0].simulation_hz=120
			16: bad.profiles[0].authority="unexpected"
			17: bad.profiles[1].features.hero_health=false
		check("reject_changed_catalog_%d"%alteration,not Contracts.validate_catalog(bad).ok)
	var local: Dictionary=g.descriptor(PROFILE)
	check("exact_descriptor_match",Contracts.compatibility(local,local.duplicate(true)).ok)
	check("native_content_revision5_separate_from_unchanged_wire",local.versions.content==5 and local.versions.input==1 and local.versions.entity==1 and local.versions.event==1 and local.versions.replay==1)
	check("browser_and_proposal_content_stay_revision1",g.descriptor("browser-p2-3v3").versions.content==1 and g.descriptor("production-6v6").versions.content==1)
	for profile_index in 3:
		for invalid in [null,0,-1,1.5,true,"2",[],{},NAN,INF,65536]:
			var malformed: Dictionary=catalog.duplicate(true)
			malformed.profiles[profile_index].content_revision=invalid
			check("content_revision_type_%d_%s"%[profile_index,str(invalid)],not Contracts.validate_catalog(malformed).ok)
		var missing: Dictionary=catalog.duplicate(true);missing.profiles[profile_index].erase("content_revision")
		check("required_content_revision_%d"%profile_index,not Contracts.validate_catalog(missing).ok)
		var stale: Dictionary=catalog.duplicate(true);stale.profiles[profile_index].content_revision=1 if profile_index==1 else 2
		check("wrong_known_content_revision_%d"%profile_index,not Contracts.validate_catalog(stale).ok)
	var old_open := Contracts.new();assert(old_open.load_catalog().ok)
	var empty_before: Dictionary=old_open.report()
	var mismatch: Dictionary=old_open.open_session(PROFILE,CONTENT1_DESCRIPTOR,SCOPE)
	check("old_content1_cannot_open_revision5",not mismatch.ok and mismatch.code=="MISMATCH_VERSIONS" and mismatch.details.field=="content" and old_open.report()==empty_before)
	var before_revision_reject: Dictionary=g.report()
	check("old_content1_resume_transactional",not g.resume_session(CONTENT1_DESCRIPTOR,SCOPE).ok and before_revision_reject==g.report())
	var next_epoch: Dictionary=SCOPE.duplicate(true);next_epoch.epoch=2
	check("old_content1_migration_cannot_downgrade",not g.migrate_session(PROFILE,CONTENT1_DESCRIPTOR,next_epoch).ok and before_revision_reject==g.report())
	var old_replay: Dictionary={"format":1,"descriptor":CONTENT1_DESCRIPTOR.duplicate(true),"room":"FIXTURE","epoch":1,"identity":"hero","seed":1,"record_count":0}
	check("old_content1_replay_rejected_before_reconstruction",not g.validate_replay(old_replay,[]).ok and before_revision_reject==g.report())
	var stale_content2: Dictionary=catalog.duplicate(true);stale_content2.profiles[1].content_revision=2
	check("native_revision2_catalog_rejected",not Contracts.validate_catalog(stale_content2).ok)
	var old2_open := Contracts.new();assert(old2_open.load_catalog().ok)
	var old2_before: Dictionary=old2_open.report()
	var old2_mismatch: Dictionary=old2_open.open_session(PROFILE,CONTENT2_DESCRIPTOR,SCOPE)
	check("old_content2_cannot_open_revision5",not old2_mismatch.ok and old2_mismatch.code=="MISMATCH_VERSIONS" and old2_mismatch.details.field=="content" and old2_open.report()==old2_before)
	check("old_content2_resume_transactional",not g.resume_session(CONTENT2_DESCRIPTOR,SCOPE).ok and before_revision_reject==g.report())
	check("old_content2_migration_cannot_downgrade",not g.migrate_session(PROFILE,CONTENT2_DESCRIPTOR,next_epoch).ok and before_revision_reject==g.report())
	var old2_replay: Dictionary={"format":1,"descriptor":CONTENT2_DESCRIPTOR.duplicate(true),"room":"FIXTURE","epoch":1,"identity":"hero","seed":1,"record_count":0}
	check("old_content2_replay_rejected_before_reconstruction",not g.validate_replay(old2_replay,[]).ok and before_revision_reject==g.report())
	var forged_content2: Dictionary=CONTENT2_DESCRIPTOR.duplicate(true);forged_content2.versions.content=5
	check("old_content2_cannot_bypass_identity_with_revision_number",not Contracts.compatibility(local,forged_content2).ok)
	var forged_current: Dictionary=CONTENT1_DESCRIPTOR.duplicate(true);forged_current.versions.content=5
	check("revision_number_alone_does_not_bypass_source_identity",not Contracts.compatibility(local,forged_current).ok)
	var old3_catalog: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTENT3_CATALOG_PATH))
	var old3_descriptor: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTENT3_DESCRIPTOR_PATH))
	var old3_profile: Dictionary=old3_catalog.profiles[1]
	var old3_versions: Dictionary=old3_catalog.envelope_versions.duplicate(true);old3_versions.content=3
	var derived_old3 := {"contract_id":old3_catalog.contract_id,"profile_id":old3_profile.id,"versions":old3_versions,"protocol":old3_profile.protocol,"rules_sha256":JSON.stringify({"profile":old3_profile,"coordinates":old3_catalog.coordinate_contract,"limits":old3_catalog.limits},"",true).sha256_text(),"map_id":old3_profile.map_id,"map_sha256":old3_profile.map_sha256,"content_sha256":old3_profile.content_sha256}
	check("preserved_revision3_descriptor_matches_exact_catalog_derivation",Contracts.compatibility(derived_old3,old3_descriptor).ok,{"derived":derived_old3,"fixture":old3_descriptor})
	check("preserved_revision3_catalog_rejected",not Contracts.validate_catalog(old3_catalog).ok)
	var old3_open := Contracts.new();assert(old3_open.load_catalog().ok)
	var old3_before: Dictionary=old3_open.report()
	var old3_mismatch: Dictionary=old3_open.open_session(PROFILE,old3_descriptor,SCOPE)
	check("old_content3_cannot_open_revision5",not old3_mismatch.ok and old3_mismatch.code=="MISMATCH_VERSIONS" and old3_mismatch.details.field=="content" and old3_open.report()==old3_before)
	check("old_content3_resume_transactional",not g.resume_session(old3_descriptor,SCOPE).ok and before_revision_reject==g.report())
	check("old_content3_migration_cannot_downgrade",not g.migrate_session(PROFILE,old3_descriptor,next_epoch).ok and before_revision_reject==g.report())
	var old3_replay: Dictionary={"format":1,"descriptor":old3_descriptor.duplicate(true),"room":"FIXTURE","epoch":1,"identity":"hero","seed":1,"record_count":0}
	check("old_content3_replay_rejected_before_reconstruction",not g.validate_replay(old3_replay,[]).ok and before_revision_reject==g.report())
	var forged_content3: Dictionary=old3_descriptor.duplicate(true);forged_content3.versions.content=5
	check("old_content3_cannot_bypass_identity_with_revision_number",not Contracts.compatibility(local,forged_content3).ok)
	var old4_catalog: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTENT4_CATALOG_PATH))
	var old4_descriptor: Dictionary=JSON.parse_string(FileAccess.get_file_as_string(CONTENT4_DESCRIPTOR_PATH))
	var old4_profile: Dictionary=old4_catalog.profiles[1]
	var old4_versions: Dictionary=old4_catalog.envelope_versions.duplicate(true);old4_versions.content=4
	var derived_old4 := {"contract_id":old4_catalog.contract_id,"profile_id":old4_profile.id,"versions":old4_versions,"protocol":old4_profile.protocol,"rules_sha256":JSON.stringify({"profile":old4_profile,"coordinates":old4_catalog.coordinate_contract,"limits":old4_catalog.limits},"",true).sha256_text(),"map_id":old4_profile.map_id,"map_sha256":old4_profile.map_sha256,"content_sha256":old4_profile.content_sha256}
	check("preserved_revision4_descriptor_matches_exact_catalog_derivation",Contracts.compatibility(derived_old4,old4_descriptor).ok,{"derived":derived_old4,"fixture":old4_descriptor})
	check("preserved_revision4_catalog_rejected",not Contracts.validate_catalog(old4_catalog).ok)
	var old4_open := Contracts.new();assert(old4_open.load_catalog().ok)
	var old4_before: Dictionary=old4_open.report()
	var old4_mismatch: Dictionary=old4_open.open_session(PROFILE,old4_descriptor,SCOPE)
	check("old_content4_cannot_open_revision5",not old4_mismatch.ok and old4_mismatch.code=="MISMATCH_VERSIONS" and old4_mismatch.details.field=="content" and old4_open.report()==old4_before)
	check("old_content4_resume_transactional",not g.resume_session(old4_descriptor,SCOPE).ok and before_revision_reject==g.report())
	check("old_content4_migration_cannot_downgrade",not g.migrate_session(PROFILE,old4_descriptor,next_epoch).ok and before_revision_reject==g.report())
	var old4_replay: Dictionary={"format":1,"descriptor":old4_descriptor.duplicate(true),"room":"FIXTURE","epoch":1,"identity":"hero","seed":1,"record_count":0}
	check("old_content4_replay_rejected_before_reconstruction",not g.validate_replay(old4_replay,[]).ok and before_revision_reject==g.report())
	var forged_content4: Dictionary=old4_descriptor.duplicate(true);forged_content4.versions.content=5
	check("old_content4_cannot_bypass_identity_with_revision_number",not Contracts.compatibility(local,forged_content4).ok)

	for field in ["contract_id","profile_id","protocol","rules_sha256","map_id","map_sha256","content_sha256"]:
		var bad := local.duplicate(true)
		if field=="protocol": bad[field]=2
		elif field in ["rules_sha256","map_sha256","content_sha256"]: bad[field]="a".repeat(64)
		else: bad[field]="wrong"
		check("handshake_reject_"+field,not Contracts.compatibility(local,bad).ok)
	for version in Contracts.VERSION_KEYS:
		var bad := local.duplicate(true)
		bad.versions[version]+=1
		check("handshake_reject_version_"+version,not Contracts.compatibility(local,bad).ok)
	var bad_descriptor := local.duplicate(true)
	bad_descriptor.extra="ignored?"
	check("unknown_handshake_field_rejected",not Contracts.compatibility(local,bad_descriptor).ok)
	check("no_automatic_cross_profile_downgrade",not Contracts.compatibility(local,g.descriptor("browser-p2-3v3")).ok)
	var detached: Dictionary=g.profile(PROFILE)
	detached.map_size_xz[0]=0
	check("profile_snapshot_is_detached",g.profile(PROFILE).map_size_xz==[140.0,260.0])

	check("first_input_zero_accepted",g.accept_input(intent()).ok)
	check("input_gap_permitted_for_coalescing",g.accept_input(intent(3)).ok)
	rejected(g,"input",intent(3),"duplicate_input_rejected")
	rejected(g,"input",intent(2),"stale_input_rejected")
	rejected(g,"input",intent(9000),"oversized_sequence_jump_requires_resync")
	for alteration in 16:
		var v := intent(4)
		match alteration:
			0: v.seq=1.5
			1: v.seq=9007199254740992.0
			2: v.move=[NAN,0]
			3: v.move=[INF,0]
			4: v.move=[1,1]
			5: v.move=[0,0,0]
			6: v.yaw=TAU
			7: v.pitch=1.3501
			8: v.pitch=NAN
			9: v.buttons=512
			10: v.actor_id="someone_else"
			11: v.epoch=0
			12: v.room="FOREIGN"
			13: v.version=2
			14: v.position=[0,0,0]
			15: v.seq=true
		rejected(g,"input",v,"malformed_input_%d"%alteration)
	for bad_value in [42,[],{},true,null]:
		for channel in ["input","event","snapshot"]:
			var malformed: Dictionary=intent(4) if channel=="input" else event(2) if channel=="event" else snapshot(1)
			malformed.room=bad_value
			rejected(g,channel,malformed,"typed_room_"+channel+"_"+str(typeof(bad_value)))
		var bad_input := intent(4);bad_input.actor_id=bad_value
		rejected(g,"input",bad_input,"typed_actor_"+str(typeof(bad_value)))
		var bad_event := event(2);bad_event.target_id=bad_value
		rejected(g,"event",bad_event,"typed_event_target_"+str(typeof(bad_value)))
		var bad_entity := snapshot(1);bad_entity.entities[0].owner_id=bad_value
		rejected(g,"snapshot",bad_entity,"typed_entity_owner_"+str(typeof(bad_value)))
	var browser := guard("browser-p2-3v3")
	var flight := intent()
	flight.buttons=16
	rejected(browser,"input",flight,"offline_flight_cannot_leak_into_browser_rules")
	check("json_float_numeric_roundtrip",browser.parse_packet(JSON.stringify(intent()).to_utf8_buffer(),"input").ok)
	check("oversized_packet_rejected_before_parse",not browser.parse_packet(" ".repeat(2049).to_utf8_buffer(),"input").ok)
	check("invalid_json_rejected",not browser.parse_packet("{invalid}".to_utf8_buffer(),"snapshot").ok)
	check("unknown_packet_channel_rejected",not browser.parse_packet("{}".to_utf8_buffer(),"admin").ok)

	check("event_zero_accepted",g.accept_event(event()).ok)
	rejected(g,"event",event(),"duplicate_event_cannot_reapply_reward")
	rejected(g,"event",event(2),"event_gap_requires_reliable_replay")
	var reward := event(1)
	reward.kind="reward";reward.amount=6
	check("contiguous_reward_receipt_accepted_once",g.accept_event(reward).ok)
	rejected(g,"event",reward,"same_reward_receipt_replay_rejected")
	for alteration in 10:
		var v := event(2)
		match alteration:
			0: v.tick=-1
			1: v.position=[0,INF,0]
			2: v.position=[10001,0,0]
			3: v.amount=-1
			4: v.amount=NAN
			5: v.amount=1000001
			6: v.kind="client_award"
			7: v.actor_id=""
			8: v.target_id="a".repeat(65)
			9: v.epoch=2
		rejected(g,"event",v,"malformed_event_%d"%alteration)
	var limited := guard()
	var bounded := true
	for n in 128: bounded=bounded and limited.accept_event(event(n,0)).ok
	check("128_event_tick_budget_accepts_exact_boundary",bounded)
	rejected(limited,"event",event(128,0),"129th_event_same_tick_rejected")
	check("next_tick_budget_recovers",limited.accept_event(event(128,1)).ok)
	rejected(limited,"event",event(129,0),"event_tick_cannot_go_backwards")

	var first := snapshot()
	first.entities[0].ack_input=3
	check("snapshot_accepts_issued_input_ack",g.accept_snapshot(first).ok)
	rejected(g,"snapshot",first,"duplicate_snapshot_rejected")
	for alteration in 19:
		var v := snapshot(1)
		v.entities[0].ack_input=3
		match alteration:
			0: v.entities[0].ack_input=4
			1: v.entities[0].ack_input=2
			2: v.entities[0].erase("pitch")
			3: v.entities[0].pitch=NAN
			4: v.entities[0].pitch=2
			5: v.entities[0].position=[0,0,INF]
			6: v.entities[0].position=[0,10001,0]
			7: v.entities[0].generation=0
			8: v.entities[0].alive=1
			9: v.entities.append(v.entities[0].duplicate(true))
			10: v.entities=[]
			11: v.entities[0].position=[9,0,0]
			12: v.entities[0].alive=false
			13: v.entities[0].kind="minion"
			14: v.entities[0].team="moon"
			15: v.entities[0].owner_id="intruder"
			16: v.tick=201
			17: v.entities[0].unknown=true
			18: v.entities.resize(641)
		rejected(g,"snapshot",v,"malformed_snapshot_%d"%alteration)
	var teleported := snapshot(1)
	teleported.entities[0].position=[30,0,0]
	teleported.entities[0].pitch=1.0
	teleported.entities[0].discontinuity=1
	teleported.entities[0].ack_input=3
	check("explicit_remote_pitch_and_teleport_counter_accepted",g.accept_snapshot(teleported).ok)
	var regression := teleported.duplicate(true);regression.tick=2;regression.entities[0].discontinuity=0
	rejected(g,"snapshot",regression,"discontinuity_counter_regression_rejected")
	var death := teleported.duplicate(true);death.tick=2;death.entities[0].discontinuity=2;death.entities[0].alive=false
	check("explicit_death_discontinuity_accepted",g.accept_snapshot(death).ok)
	var restored := death.duplicate(true);restored.tick=3;restored.entities[0].alive=true;restored.entities[0].discontinuity=3
	check("explicit_respawn_discontinuity_accepted",g.accept_snapshot(restored).ok)
	var detached_report: Dictionary=g.report();detached_report.entities.hero.pitch=-1
	check("caller_cannot_mutate_accepted_pose",g.report().entities.hero.pitch==1.0)

	var life := guard()
	var spawn := snapshot();spawn.entities.append(entity("arrow","projectile"))
	check("new_projectile_lifetime_accepted",life.accept_snapshot(spawn).ok)
	check("full_snapshot_absence_despawns",life.accept_snapshot(snapshot(1)).ok)
	spawn.tick=2
	rejected(life,"snapshot",spawn,"absent_id_cannot_resurrect_same_generation")
	spawn.entities[1].generation=2
	check("new_generation_reuses_slot_safely",life.accept_snapshot(spawn).ok)
	spawn.tick=3;spawn.entities[1].generation=1
	rejected(life,"snapshot",spawn,"old_generation_cannot_overwrite_new_entity")
	var cap := guard()
	var crowd := snapshot()
	for n in 193: crowd.entities.append(entity("arrow%d"%n,"projectile"))
	rejected(cap,"snapshot",crowd,"per_kind_projectile_cap_even_below_total")
	crowd.entities.pop_back()
	check("192_projectile_limit_accepted",cap.accept_snapshot(crowd).ok)

	for profile_id in Contracts.PROFILE_IDS:
		var cohort := guard(profile_id)
		var maximum: int=1 if profile_id==PROFILE else 6 if profile_id=="browser-p2-3v3" else 12
		var slots := snapshot()
		for n in range(1,maximum): slots.entities.append(entity("peer%d"%n))
		check(profile_id+"_exact_actor_limit",cohort.accept_snapshot(slots).ok)
		slots.tick=1;slots.entities.append(entity("excess"))
		rejected(cohort,"snapshot",slots,profile_id+"_excess_actor_rejected")
	var history_guard := guard()
	var history_ok := true
	for batch in 42:
		var s := snapshot(batch)
		for n in 96: s.entities.append(entity("unit%d"%(batch*96+n),"minion"))
		history_ok=history_ok and history_guard.accept_snapshot(s).ok
	var boundary := snapshot(42)
	for n in 63: boundary.entities.append(entity("last%d"%n,"minion"))
	check("4096_lifetime_history_boundary",history_ok and history_guard.accept_snapshot(boundary).ok and history_guard.report().entity_history.size()==4096)
	var overflow := snapshot(43);overflow.entities.append(entity("too_many","minion"))
	rejected(history_guard,"snapshot",overflow,"history_cannot_grow_without_new_epoch")
	var old: Dictionary=g.report()
	check("resume_keeps_ack_tick_events_and_room",g.resume_session(local,SCOPE).ok and old==g.report())
	check("resume_json_numbers_preserve_scope",g.resume_session(JSON.parse_string(JSON.stringify(local)),JSON.parse_string(JSON.stringify(SCOPE))).ok and old==g.report())
	for field in ["room","epoch","identity"]:
		var changed := SCOPE.duplicate();changed[field]=2 if field=="epoch" else "FOREIGN"
		check("resume_rejects_changed_"+field,not g.resume_session(local,changed).ok and old==g.report())
	check("active_session_cannot_silent_reopen",not g.open_session(PROFILE,local,SCOPE).ok and old==g.report())
	check("rollback_same_epoch_rejected",not g.migrate_session("browser-p2-3v3",g.descriptor("browser-p2-3v3"),SCOPE).ok and old==g.report())
	var next_scope := SCOPE.duplicate();next_scope.epoch=2
	check("explicit_version_rollback_requires_new_epoch",g.migrate_session("browser-p2-3v3",g.descriptor("browser-p2-3v3"),next_scope).ok and g.report().last_ack==-1 and g.report().entities.is_empty())
	rejected(g,"event",event(),"old_epoch_reward_rejected_after_rollback")
	rejected(g,"input",intent(),"old_epoch_input_rejected_after_rollback")
	check("resume_requires_new_profile_after_rollback",not g.resume_session(local,next_scope).ok)

	var replay_guard := guard()
	var header := {"format":1,"descriptor":replay_guard.descriptor(PROFILE),"room":"FIXTURE","epoch":1,"identity":"hero","seed":42,"record_count":3}
	var snap := snapshot();snap.entities[0].ack_input=0
	var records := [{"kind":"input","value":intent()},{"kind":"snapshot","value":snap},{"kind":"event","value":event()}]
	var state_before: Dictionary=replay_guard.report()
	var replay: Dictionary=replay_guard.validate_replay(header,records)
	check("replay_validates_ordered_records_without_active_mutation",replay.ok and replay.details.final.last_ack==0 and replay.details.final.last_event_seq==0 and replay_guard.report()==state_before)
	check("replay_seek_revalidates_from_epoch_start_deterministically",replay==replay_guard.validate_replay(header,records))
	var oversized_records := [];oversized_records.resize(100001)
	var oversized_header := header.duplicate(true);oversized_header.record_count=100001
	check("replay_record_budget_rejects_before_iteration",not replay_guard.validate_replay(oversized_header,oversized_records).ok)
	for alteration in 9:
		var h := header.duplicate(true);var r := records.duplicate(true)
		match alteration:
			0: h.format=2
			1: h.descriptor.content_sha256="b".repeat(64)
			2: h.record_count=4
			3: h.seed=-1
			4: r[2].value.epoch=2
			5: r[2].value.seq=1
			6: r[1].value.entities[0].pitch=NAN
			7: r.reverse()
			8: r[0].kind="load_resource"
		check("replay_rejects_corruption_%d"%alteration,not replay_guard.validate_replay(h,r).ok and replay_guard.report()==state_before)

	var stress := guard()
	var stress_ok := true
	for n in 2000:
		stress_ok=stress_ok and stress.accept_input(intent(n)).ok and stress.accept_event(event(n,n)).ok
		var s := snapshot(n);s.entities[0].ack_input=n;s.entities[0].pitch=sin(n*.1)
		stress_ok=stress_ok and stress.accept_snapshot(s).ok
	check("2000_interleaved_cycles_keep_bounded_state",stress_ok and stress.report().entity_history.size()==1 and stress.report().entities.size()==1 and stress.report().last_ack==1999 and stress.report().last_event_seq==1999)
	stress.reset()
	check("explicit_reset_clears_all_epoch_state",stress.report().session.is_empty() and stress.report().last_ack==-1 and stress.report().entity_history.is_empty())
	var frozen := true
	for path in sources: frozen=frozen and sources[path]==FileAccess.get_sha256(path)
	check("source_unchanged_during_run",frozen)
	var passed := true
	for c in checks: passed=passed and c.passed
	var report_ := {"passed":passed,"checks":checks,"source_sha256":sources,"engine":Engine.get_version_info().string,"scope":"Pure contract admission, stream lifecycle, reconnect/rollback and replay validation fixtures. No socket, server migration, authority re-simulation or rendered online match."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE)
			if file==null: push_error("Cannot write report");quit(2);return
			file.store_string(JSON.stringify(report_,"\t")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
