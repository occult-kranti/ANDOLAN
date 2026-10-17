extends SceneTree
## Owner-authored pure-rule tests; scene integration is a separate independent gate.

const Relay = preload("res://scripts/relay_control.gd")
var checks: Array = []
var hashes: Dictionary = {}

func _initialize() -> void:
	call_deferred("run")

func record(label: String, passed: bool, evidence: Dictionary = {}) -> void:
	checks.append({"case":label,"passed":passed,"evidence":evidence})
	print("RELAY_CASE ",label," ",passed)

func actor(id: Variant, team: String = "sun", position: Vector3 = Vector3.ZERO, alive: bool = true) -> Dictionary:
	return {"id":id,"team":team,"position":position,"alive":alive}

func site(control, index: int = 1) -> Dictionary:
	return control.sites()[index]

func advance(control, count: int, actors: Array, delta: float = 0.1) -> Dictionary:
	var result := {"accepted":true,"events":[],"support_requests":[]}
	for _i in range(count):
		var next: Dictionary = control.step(delta,actors)
		result.accepted = result.accepted and next.accepted
		result.events.append_array(next.events)
		result.support_requests.append_array(next.support_requests)
	return result

func captured(control, team: String = "sun") -> void:
	control.reset()
	advance(control,40,[actor(1,team),actor(2,team)])

func close(a: float,b: float) -> bool:
	return absf(a-b) < 0.00001

func run() -> void:
	for path in ["res://scripts/relay_control.gd","res://tools/test-relay-control.gd"]:
		hashes[path] = FileAccess.get_sha256(path)
	var control = Relay.new()
	var initial: Array = control.sites()
	record("three_fixed_sites_have_exact_labels_positions_and_neutral_state",initial.size()==3 and initial[0].label=="Reed Relay" and initial[1].label=="Lotus Relay" and initial[2].label=="Sky Relay" and initial[0].position==Vector3(-40,0,0) and initial[1].position==Vector3.ZERO and initial[2].position==Vector3(40,0,0) and initial.all(func(s):return s.radius==5.0 and s.owner=="neutral" and s.progress==0))
	initial[0].owner = "moon"
	initial[1].contributors.sun = 42
	initial.clear()
	record("snapshots_are_detached_from_private_state",site(control,0).owner=="neutral" and site(control).contributors.sun==0 and control.sites().size()==3)
	record("module_is_refcounted_without_node_or_resource_lifecycle",control is RefCounted and not control is Node and not control is Resource)

	advance(control,79,[actor("hero")])
	record("one_actor_needs_full_eight_contribution_seconds",site(control).owner=="neutral" and close(site(control).progress,7.9))
	var result: Dictionary = control.step(.1,[actor("hero")])
	record("sun_capture_occurs_once_at_eight_seconds",site(control).owner=="sun" and site(control).progress==8.0 and result.events.size()==1 and result.events[0].kind=="captured" and result.events[0].team=="sun")
	record("capture_tick_does_not_credit_supply_time",site(control).supply_clock==0.0 and result.support_requests.is_empty())
	control.reset()
	advance(control,80,[actor(1,"moon")])
	record("moon_has_symmetric_capture_threshold",site(control).owner=="moon" and site(control).progress==-8.0)
	control.reset()
	advance(control,39,[actor(1),actor("hero")])
	var before: bool = site(control).owner=="neutral"
	control.step(.1,[actor(1),actor("hero")])
	record("hero_and_troop_have_equal_capture_weight",before and site(control).owner=="sun")
	control.reset()
	var crowd: Array = []
	for i in range(97): crowd.append(actor(i))
	advance(control,39,crowd)
	before = site(control).owner=="neutral"
	control.step(.1,crowd)
	record("ninety_seven_actors_are_capped_at_two_contributors",before and site(control).owner=="sun" and site(control).contributors.sun==2 and control.report().actors.unique_alive==97)

	captured(control)
	advance(control,79,[actor(3,"moon")])
	record("held_relay_stays_owned_during_partial_neutralization",site(control).owner=="sun" and close(site(control).progress,.1))
	result = control.step(.1,[actor(3,"moon")])
	record("enemy_neutralizes_at_zero_without_instant_capture",site(control).owner=="neutral" and site(control).progress==0 and result.events.size()==1 and result.events[0].kind=="neutralized" and result.events[0].team=="moon")
	advance(control,79,[actor(3,"moon")])
	before = site(control).owner=="neutral"
	result = control.step(.1,[actor(3,"moon")])
	record("enemy_requires_second_eight_seconds_to_own",before and site(control).owner=="moon" and result.events.size()==1 and result.events[0].kind=="captured")
	advance(control,160,[actor(4,"sun")])
	record("reverse_takeover_obeys_same_two_stage_rule",site(control).owner=="sun" and control.report().neutralizations==2)

	control.reset()
	advance(control,20,[actor(1),actor(2)])
	var pre_contest_progress: float = site(control).progress
	result = advance(control,100,[actor(1),actor(2),actor(3,"moon")])
	record("outnumbered_opposition_still_freezes_capture_and_emits_one_contest",close(pre_contest_progress,4.0) and site(control).progress==pre_contest_progress and site(control).contested and site(control).supply_clock==0 and result.events.size()==1 and result.events[0].kind=="contested" and result.support_requests.is_empty(),{"before":pre_contest_progress,"after":site(control).progress,"events":result.events})
	advance(control,40,[])
	record("empty_neutral_partial_capture_decays_half_per_second",close(site(control).progress,2.0) and not site(control).contested)
	advance(control,100,[])
	record("empty_decay_stops_at_neutral_without_changing_owner",site(control).progress==0 and site(control).owner=="neutral")
	for team in ["sun","moon"]:
		captured(control,team)
		advance(control,20,[actor(3,"moon" if team=="sun" else "sun")])
		var partial: float = absf(site(control).progress)
		advance(control,40,[])
		record(team+"_empty_countercapture_recovers_toward_held_stable_state",close(partial,6.0) and absf(site(control).progress)==8.0 and site(control).owner==team)

	captured(control)
	result = advance(control,49,[actor("hero")])
	before = result.support_requests.is_empty()
	result = control.step(.1,[actor("hero")])
	record("supply_is_issued_once_at_five_seconds_with_exact_recipient",before and result.support_requests.size()==1 and result.support_requests[0].actor_ids==["hero"] and result.support_requests[0].site_id==1 and result.support_requests[0].team=="sun" and result.support_requests[0].id==1 and result.support_requests[0].epoch==control.report().epoch)
	var first_receipt: Dictionary = result.support_requests[0].duplicate(true)
	result.support_requests[0].actor_ids.append("forged")
	result = advance(control,50,[actor("hero")])
	record("supply_receipts_are_detached_and_monotonic",result.support_requests.size()==1 and result.support_requests[0].actor_ids==["hero"] and result.support_requests[0].id==2)
	control.reset()
	record("reset_invalidates_prior_epoch_and_clears_all_progress",control.report().epoch!=first_receipt.epoch and control.report().last_support_id==0 and control.report().steps==0 and control.report().elapsed==0 and control.report().sites.all(func(s):return s.owner=="neutral" and s.progress==0 and s.supply_clock==0 and not s.contested))
	captured(control,"moon")
	result = advance(control,50,[actor(5,"moon"),actor(6,"sun",Vector3(7,0,0))])
	record("moon_owner_gets_symmetric_supply_without_enemy_recipient",result.support_requests.size()==1 and result.support_requests[0].team=="moon" and result.support_requests[0].actor_ids==[5])

	captured(control)
	advance(control,49,[actor(1)])
	control.step(.1,[actor(1),actor(2,"moon")])
	result = advance(control,49,[actor(1)])
	before = result.support_requests.is_empty()
	result = control.step(.1,[actor(1)])
	record("contesting_resets_supply_instead_of_banking_near_ready_tick",before and result.support_requests.size()==1)
	captured(control)
	advance(control,49,[actor(1)])
	control.step(.1,[actor(2,"moon")])
	before = site(control).supply_clock==0 and not site(control).contested
	result = advance(control,49,[actor(1)])
	record("enemy_only_pressure_also_resets_supply_clock",before and result.support_requests.is_empty())
	captured(control)
	result = advance(control,200,[])
	record("empty_owned_sites_do_not_emit_empty_supply_requests",result.support_requests.is_empty() and control.report().last_support_id==0 and site(control).owner=="sun")

	control.reset()
	advance(control,40,[actor(1,"sun",Vector3(5,2.5,0)),actor(2,"sun",Vector3(0,-2.5,5))])
	record("capture_boundary_includes_radius_five_and_height_plus_minus_two_point_five",site(control).owner=="sun")
	control.reset()
	advance(control,100,[actor(1,"sun",Vector3(5.001,0,0)),actor(2,"sun",Vector3(0,2.501,0)),actor(3,"sun",Vector3(0,-2.501,0)),actor("flying","sun",Vector3(0,24,0)),actor("far","sun",Vector3(1e15,0,1e15))])
	record("outside_radius_high_flight_and_out_of_world_positions_do_not_capture",site(control).owner=="neutral" and site(control).progress==0 and site(control).contributors.sun==0)
	captured(control)
	result = advance(control,50,[actor("edge","sun",Vector3(8,2.5,0)),actor("wide","sun",Vector3(8.001,0,0)),actor("high","sun",Vector3(0,2.501,0)),actor("dead","sun",Vector3.ZERO,false),actor("enemy","moon",Vector3(7,0,0))])
	record("supply_filters_team_life_horizontal_range_and_height_independently",result.support_requests.size()==1 and result.support_requests[0].actor_ids==["edge"])

	control.reset()
	crowd.clear()
	for i in range(97): crowd.append(actor("one"))
	advance(control,79,crowd)
	record("identical_duplicate_ids_cannot_accelerate_capture",site(control).owner=="neutral" and close(site(control).progress,7.9) and control.report().actors.unique_alive==1 and control.report().actors.duplicate_rows==96)
	control.reset()
	result = advance(control,100,[actor(1),actor(1,"moon"),actor(2),actor(2,"sun",Vector3.ZERO,false)])
	record("conflicting_team_or_life_duplicates_invalidate_that_identity",site(control).progress==0 and control.report().actors.conflicting_ids==2 and control.report().actors.unique_alive==0 and result.events.is_empty())
	var reordered = Relay.new()
	control.reset()
	var mixed := [actor(7),actor(7,"moon"),actor("7"),actor("hero"),actor("hero"),actor(9,"sun",Vector3(8,0,0))]
	var reversed := mixed.duplicate(true)
	reversed.reverse()
	advance(control,90,mixed)
	advance(reordered,90,reversed)
	record("actor_order_and_conflicting_duplicate_order_do_not_change_results",control.sites()==reordered.sites() and control.report().last_support_id==reordered.report().last_support_id)
	control.reset()
	advance(control,40,[actor(1),actor("1")])
	record("integer_and_string_ids_are_distinct_stable_identities",site(control).owner=="sun" and control.report().actors.unique_alive==2)

	var bad_rows: Array = [null,7,"actor",Vector3.ZERO,{},actor(1,"unknown"),{"id":false,"team":"sun","position":Vector3.ZERO,"alive":true},{"id":"","team":"sun","position":Vector3.ZERO,"alive":true},{"id":"x".repeat(129),"team":"sun","position":Vector3.ZERO,"alive":true},{"id":1,"team":"sun","position":Vector3.ZERO,"alive":1},actor(3,"sun",Vector3(NAN,0,0)),actor(4,"sun",Vector3(0,INF,0))]
	control.reset()
	advance(control,100,bad_rows)
	record("malformed_and_nonfinite_actor_rows_are_ignored",site(control).progress==0 and control.report().actors.invalid_rows==bad_rows.size() and control.report().actors.unique_alive==0)
	control.step(.1,[actor("valid")])
	var snapshot: Dictionary = control.report()
	var invalid_ok := true
	for bad_delta in [NAN,INF,-INF,-.1,.250001,1e30]:
		result = control.step(bad_delta,[actor("valid")])
		invalid_ok = invalid_ok and not result.accepted and not result.error.is_empty() and result.events.is_empty() and result.support_requests.is_empty() and control.report()==snapshot
	record("invalid_delta_is_rejected_transactionally",invalid_ok)
	crowd.clear()
	for i in range(98): crowd.append(actor(i))
	result = control.step(.1,crowd)
	record("over_capacity_array_rejects_whole_step_without_truncation",not result.accepted and control.report()==snapshot)
	result = control.step(0.0,[actor("valid")])
	record("zero_delta_is_an_accepted_state_preserving_noop",result.accepted and control.report()==snapshot and result.events.is_empty() and result.support_requests.is_empty())
	var original := [actor("hero")]
	var original_copy := original.duplicate(true)
	control.step(.1,original)
	record("input_actor_records_are_not_mutated",original==original_copy)

	var fine = Relay.new()
	var coarse = Relay.new()
	var a: Dictionary = advance(fine,130,[actor(1)],.1)
	var b: Dictionary = advance(coarse,52,[actor(1)],.25)
	record("capture_and_supply_boundary_agree_at_ten_and_four_hertz",site(fine).owner=="sun" and site(coarse).owner=="sun" and a.events==b.events and a.support_requests==b.support_requests and close(site(fine).supply_clock,site(coarse).supply_clock))

	control.reset()
	crowd.clear()
	for index in range(3):
		crowd.append(actor(index*2,"sun",Vector3((index-1)*40,0,0)))
		crowd.append(actor(index*2+1,"sun",Vector3((index-1)*40,0,0)))
	result = advance(control,40,crowd)
	before = result.events.size()==3 and result.events[0].site_id==0 and result.events[2].site_id==2
	result = advance(control,50,crowd)
	record("three_sites_emit_ordered_unique_supply_receipts",before and result.support_requests.size()==3 and result.support_requests[0].id==1 and result.support_requests[1].id==2 and result.support_requests[2].id==3 and result.support_requests[0].actor_ids==[0,1] and result.support_requests[2].actor_ids==[4,5])

	_stress(control)
	var same := true
	for path in hashes: same = same and hashes[path]==FileAccess.get_sha256(path)
	record("tested_sources_unchanged_during_run",same,hashes)
	var passed: bool = checks.all(func(c):return c.passed)
	var report := {"passed":passed,"checks":checks,"engine":Engine.get_version_info().string,"source_sha256":hashes,
		"scope":"Owner-authored pure RefCounted offline relay rules, malformed inputs and one-hour bounded simulation. No scene, healing/ammo application, replay consumer, renderer, network or performance acceptance claim."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var path := arg.trim_prefix("--report=")
			DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(path).get_base_dir())
			var file := FileAccess.open(path,FileAccess.WRITE)
			if file: file.store_string(JSON.stringify(report,"\t")+"\n")
			else: passed = false
	print("YUGA_RELAY_CONTROL ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)

func _stress(control) -> void:
	control.reset()
	var phases: Array = []
	for phase in range(7):
		var rows: Array = []
		for index in range(3):
			var position := Vector3((index-1)*40,0,0)
			if phase in [0,3,5,6]:
				rows.append(actor(index*4,"sun",position))
				rows.append(actor(index*4+1,"sun",position))
			if phase in [1,2,3]:
				rows.append(actor(index*4+2,"moon",position))
				rows.append(actor(index*4+3,"moon",position))
		while rows.size()<97:
			rows.append(actor(1000+rows.size(),"sun",Vector3(500+rows.size(),0,500)))
		phases.append(rows)
	var finite := true
	var bounded := true
	var receipts := 0
	var event_kinds := {"captured":0,"neutralized":0,"contested":0}
	var previous_id := 0
	var begin := Time.get_ticks_msec()
	for tick in range(36000):
		var phase: int = (tick/100)%7
		var result: Dictionary = control.step(.1,phases[phase])
		bounded = bounded and result.accepted and result.events.size()<=3 and result.support_requests.size()<=3
		for event in result.events: event_kinds[event.kind] += 1
		for request in result.support_requests:
			receipts += 1
			bounded = bounded and request.id==previous_id+1 and request.epoch==control.report().epoch and request.actor_ids.size()==2 and request.actor_ids[0]!=request.actor_ids[1]
			previous_id = request.id
		for entry in control.sites():
			finite = finite and is_finite(entry.progress) and absf(entry.progress)<=8.0 and is_finite(entry.supply_clock) and entry.supply_clock>=0 and entry.supply_clock<5.0 and entry.owner in ["neutral","sun","moon"] and entry.contributors.sun<=2 and entry.contributors.moon<=2
	var metrics := {"steps":36000,"simulation_seconds":control.report().elapsed,"actors_per_step":97,"supply_receipts":receipts,"events":event_kinds,"wall_ms":Time.get_ticks_msec()-begin}
	record("one_hour_repeated_simulation_remains_finite_and_bounded",finite and bounded and close(control.report().elapsed,3600.0),metrics)
	record("stress_repeatedly_exercises_both_ownership_transfers_contest_and_supply",event_kinds.captured>100 and event_kinds.neutralized>100 and event_kinds.contested>100 and receipts>100,metrics)
