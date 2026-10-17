extends SceneTree
const Bridge = preload("res://scripts/entity_bridge.gd")
const PROFILE := "native-offline-triad"
const SCOPE := {"room":"BRIDGE","epoch":1,"identity":"hero"}
var checks: Array=[]
var pins: Dictionary={}
var bridge: Node3D

func _initialize() -> void: call_deferred("run")
func check(name_: String, passed: bool, details: Dictionary={}) -> void:
	checks.append({"name":name_,"passed":passed,"details":details});print("PASS " if passed else "FAIL ",name_)
func entity(id: String, kind: String) -> Dictionary:
	return {"id":id,"generation":1,"kind":kind,"team":"sun","position":[0,0,0],"yaw":0.0,"pitch":0.0,"discontinuity":0,"alive":true,"ack_input":-1,"owner_id":"" if kind=="actor" else "hero"}
func snapshot(tick := 0) -> Dictionary:
	var entries := [entity("hero","actor")]
	for kind in ["minion","neutral","structure","projectile","zone","pickup","gold_shard"]: entries.append(entity(kind,kind))
	return {"version":1,"room":"BRIDGE","epoch":1,"tick":tick,"entities":entries}
func intent(seq := 0) -> Dictionary:
	return {"version":1,"room":"BRIDGE","epoch":1,"seq":seq,"actor_id":"hero","move":[0,1],"yaw":0,"pitch":0,"buttons":0}
func event(seq := 0, tick := 0) -> Dictionary:
	return {"version":1,"room":"BRIDGE","epoch":1,"seq":seq,"tick":tick,"kind":"shot","actor_id":"hero","target_id":"minion","position":[1,2,3],"amount":0}
func count_nodes(node: Node) -> int:
	var count_ := 1
	for child in node.get_children(): count_+=count_nodes(child)
	return count_
func count_collisions(node: Node) -> int:
	var count_ := 1 if node is CollisionObject3D else 0
	for child in node.get_children(): count_+=count_collisions(child)
	return count_
func reject(channel: String, value: Variant, label: String) -> void:
	var before: Dictionary=bridge.report()
	var result: Dictionary=bridge.call(channel,value)
	check(label,not result.ok and before==bridge.report(),{"code":result.code})

func scene_pose() -> Dictionary:
	# Read actual child transforms/visibility, independently of the bridge's digest.
	var state := {"entities":{},"events":[]}
	for node in bridge.get_node("Entities").get_children():
		var body: MeshInstance3D=node.get_node("Body")
		var aim: Node3D=node.get_node("Aim")
		state.entities[node.name]={"position":node.global_position,"basis":node.global_basis,"aim":aim.global_basis,"body_basis":body.global_basis,"visible":body.visible,"generation":node.get_meta("generation"),"kind":node.get_meta("kind")}
	for node in bridge.get_node("EventReceipts").get_children():
		state.events.append({"seq":node.get_meta("seq"),"position":node.global_position,"tick":node.get_meta("tick")})
	return state

func run() -> void:
	for path in ["res://scripts/entity_bridge.gd","res://tests/entity_bridge_cases.gd","res://scripts/native_contracts.gd","res://assets/contracts/native-contracts-v1.json"]: pins[path]=FileAccess.get_sha256(path)
	bridge=Bridge.new();root.add_child(bridge)
	var d: Dictionary=bridge.descriptor(PROFILE)
	reject("apply_snapshot",snapshot(),"closed_bridge_rejects_world_mutation")
	check("valid_contract_opens_presentation_only",bridge.open_session(PROFILE,d,SCOPE).ok and not bridge.report().network_connected)
	check("one_valid_snapshot_builds_all_eight_kinds",bridge.apply_snapshot(snapshot()).ok and bridge.report().entity_count==8)
	var types_ok := true
	for id in bridge.report().entities:
		var node: Node3D=bridge.entity_node(id)
		types_ok=types_ok and node is Node3D and node.get_node("Body") is MeshInstance3D and node.get_node("Aim") is Node3D and node.get_meta("kind")==id if id!="hero" else types_ok
	check("real_scene_nodes_have_meshes_and_aim_anchors",types_ok)
	check("presentation_creates_zero_collision_bodies",count_collisions(bridge)==0)
	check("ownership_and_team_are_authority_metadata",bridge.entity_node("projectile").get_meta("owner_id")=="hero" and bridge.entity_node("minion").get_meta("team")=="sun")
	var hero: Node3D=bridge.entity_node("hero")
	var first_id := hero.get_instance_id()
	check("input_intent_validates_without_moving_actor",bridge.submit_input(intent()).ok and hero.position==Vector3.ZERO)
	var moved := snapshot(1);moved.entities[0].position=[2,3,4];moved.entities[0].yaw=PI/2;moved.entities[0].pitch=.6;moved.entities[0].ack_input=0;moved.entities[4].yaw=-PI/2;moved.entities[4].pitch=.8
	check("snapshot_updates_existing_node_and_ack",bridge.apply_snapshot(moved).ok and bridge.entity_node("hero").get_instance_id()==first_id and hero.position==Vector3(2,3,4) and bridge.report().last_ack==0)
	var expected := Vector3(cos(.6),sin(.6),0)
	check("actual_remote_aim_anchor_uses_pitch_and_shared_yaw",hero.get_node("Aim").global_basis.z.distance_to(expected)<.00001)
	check("projectile_actual_mesh_axis_tracks_remote_pitch",bridge.entity_node("projectile").get_node("Body").global_basis.y.distance_to(Vector3(-cos(.8),sin(.8),0))<.00001)
	var aim_ok := true
	for yaw in [-PI,-PI/2,0.0,PI/2,PI]:
		for pitch in [-1.35,-.5,0.0,.5,1.35]:
			var direction: Vector3=Bridge.aim_direction(yaw,pitch)
			var native_yaw: float=Bridge.shared_to_native_yaw(yaw)
			var camera_direction: Vector3=-(Basis(Vector3.UP,native_yaw)*Basis(Vector3.RIGHT,pitch)).z
			aim_ok=aim_ok and direction.distance_to(camera_direction)<.00001 and absf(direction.length()-1)<.00001 and absf(wrapf(Bridge.native_to_shared_yaw(native_yaw)-yaw,-PI,PI))<.00001
	check("25_cardinal_high_low_camera_roundtrips",aim_ok)
	check("invalid_aim_numbers_have_no_direction",Bridge.aim_direction(NAN,0)==Vector3.ZERO and Bridge.aim_direction(0,INF)==Vector3.ZERO and is_nan(Bridge.shared_to_native_yaw(INF)))
	bridge.position=Vector3(50,50,50);bridge.rotation.y=1
	check("authority_world_coordinates_ignore_bridge_parent_transform",hero.global_position.distance_to(Vector3(2,3,4))<.00001 and hero.get_node("Aim").global_basis.z.distance_to(expected)<.00001)
	bridge.position=Vector3.ZERO;bridge.rotation=Vector3.ZERO
	for alteration in 8:
		var bad := moved.duplicate(true);bad.tick=2
		match alteration:
			0: bad.room="OTHER"
			1: bad.epoch=2
			2: bad.entities[0].erase("pitch")
			3: bad.entities[0].position=[INF,0,0]
			4: bad.entities.append(bad.entities[0].duplicate(true))
			5: bad.entities[0].ack_input=1
			6: bad.entities[0].position=[100,0,0]
			7: bad.room={}
		reject("apply_snapshot",bad,"rejected_snapshot_preserves_nodes_%d"%alteration)
	check("accepted_event_creates_world_receipt_node",bridge.apply_event(event()).ok and bridge.report().event_count==1 and bridge.get_node("EventReceipts").get_child(0).position==Vector3(1,2,3))
	reject("apply_event",event(),"duplicate_event_never_spawns_twice")
	var tele := moved.duplicate(true);tele.tick=2;tele.entities[0].position=[100,1,1];tele.entities[0].discontinuity=1
	check("teleport_keeps_node_clears_transients_resets_pose_history",bridge.apply_snapshot(tele).ok and bridge.entity_node("hero").get_instance_id()==first_id and bridge.report().event_count==0 and hero.get_meta("history_reset_count")==2)
	var dead := tele.duplicate(true);dead.tick=3;dead.entities[0].alive=false;dead.entities[0].discontinuity=2
	check("death_hides_body_without_destroying_lifetime",bridge.apply_snapshot(dead).ok and not hero.get_node("Body").visible and not hero.get_node("Aim").visible)
	var revived := dead.duplicate(true);revived.tick=4;revived.entities[0].alive=true;revived.entities[0].discontinuity=3
	check("respawn_restores_authoritative_visible_pose",bridge.apply_snapshot(revived).ok and hero.get_node("Body").visible)
	var old_projectile: Node3D=bridge.entity_node("projectile")
	var replaced := revived.duplicate(true);replaced.tick=5;replaced.entities[4].generation=2
	check("higher_generation_replaces_and_frees_old_node",bridge.apply_snapshot(replaced).ok and not is_instance_valid(old_projectile) and bridge.entity_node("projectile").get_meta("generation")==2)
	var absent := replaced.duplicate(true);absent.tick=6;absent.entities.remove_at(4)
	var removed: Node3D=bridge.entity_node("projectile")
	check("full_snapshot_absence_frees_actual_node",bridge.apply_snapshot(absent).ok and not is_instance_valid(removed) and bridge.entity_node("projectile")==null)
	var before_reconnect: Dictionary=bridge.report()
	check("reconnect_freezes_and_preserves_identity_ack",bridge.begin_reconnect().ok and bridge.report().state=="reconnecting" and bridge.report().session==before_reconnect.session and bridge.report().last_ack==0)
	reject("submit_input",intent(1),"reconnect_blocks_input_intent")
	var bad_scope := SCOPE.duplicate();bad_scope.epoch=2
	var frozen: Dictionary=bridge.report()
	check("wrong_resume_scope_preserves_frozen_world",not bridge.resume_session(d,bad_scope).ok and bridge.report()==frozen)
	check("authenticated_scope_resume_preserves_node",bridge.resume_session(d,SCOPE).ok and bridge.entity_node("hero").get_instance_id()==first_id and bridge.report().last_input_seq==0)
	reject("apply_event",event(),"resume_does_not_reset_receipt_watermark")
	var epoch_scope := SCOPE.duplicate();epoch_scope.epoch=2
	check("explicit_new_epoch_cleans_every_view_and_ack",bridge.migrate_session(PROFILE,d,epoch_scope).ok and bridge.report().entity_count==0 and bridge.report().event_count==0 and bridge.report().last_ack==-1 and not is_instance_valid(hero))
	reject("apply_snapshot",snapshot(7),"old_epoch_cannot_restore_old_nodes")
	bridge.disconnect_session()
	check("disconnect_leaves_two_empty_owning_containers",count_nodes(bridge)==3 and bridge.report().state=="closed")

	# Real forward scene mutation versus a backward-seek reconstruction of the same accepted records.
	check("second_fixture_open",bridge.open_session(PROFILE,d,SCOPE).ok)
	var records := [{"kind":"event","value":event(0,0)},{"kind":"snapshot","value":snapshot(0)},{"kind":"input","value":intent(0)}]
	var replay_snapshot := snapshot(1);replay_snapshot.entities[0].ack_input=0;replay_snapshot.entities[0].pitch=.75
	records.append({"kind":"snapshot","value":replay_snapshot})
	records.append({"kind":"event","value":event(1,1)})
	var replay_teleport := replay_snapshot.duplicate(true);replay_teleport.tick=2;replay_teleport.entities[0].discontinuity=1;replay_teleport.entities[0].position=[20,0,0]
	records.append({"kind":"snapshot","value":replay_teleport})
	records.append({"kind":"event","value":event(2,2)})
	var forward_states := []
	var forward_geometry := []
	for record in records:
		var method: String="submit_input" if record.kind=="input" else "apply_"+record.kind
		check("live_replay_fixture_record_%d"%forward_states.size(),bridge.call(method,record.value).ok)
		forward_states.append(bridge.report().pose_digest)
		forward_geometry.append(scene_pose())
	var header := {"format":1,"descriptor":d,"room":"BRIDGE","epoch":1,"identity":"hero","seed":9,"record_count":records.size()}
	var corrupted := records.duplicate(true);corrupted[-1].value.seq=999
	frozen=bridge.report()
	check("late_replay_corruption_rejected_before_live_cleanup",not bridge.load_replay(header,corrupted).ok and bridge.report()==frozen)
	check("valid_replay_replaces_live_world_with_empty_cursor",bridge.load_replay(header,records).ok and bridge.report().state=="replay" and bridge.report().entity_count==0)
	reject("apply_snapshot",snapshot(100),"live_snapshot_cannot_inject_into_replay")
	var seek_ok := true
	for round_ in 6:
		for n in range(records.size(),0,-1):
			seek_ok=seek_ok and bridge.seek_replay(n).ok and bridge.report().pose_digest==forward_states[n-1] and scene_pose()==forward_geometry[n-1]
	check("42_reverse_seeks_match_real_forward_node_state",seek_ok)
	for invalid in [-1,records.size()+1,.5,NAN,true,{},null]: reject("seek_replay",invalid,"invalid_seek_"+str(invalid))
	check("seek_zero_releases_all_scene_entities",bridge.seek_replay(0).ok and count_nodes(bridge)==3)
	bridge.disconnect_session();bridge.open_session(PROFILE,d,SCOPE)
	var stress_ok := true
	var max_nodes := 0
	for tick in 500:
		var s := snapshot(tick);s.entities[0].generation=tick+1
		stress_ok=stress_ok and bridge.apply_snapshot(s).ok and bridge.apply_event(event(tick,tick)).ok
		max_nodes=maxi(max_nodes,count_nodes(bridge))
	check("500_real_lifetime_replacements_and_effects_bounded",stress_ok and bridge.report().entity_count==8 and bridge.report().event_count<=64 and max_nodes<=165 and bridge.report().mesh_resources<=10 and bridge.report().material_resources<=3,{"maximum_nodes":max_nodes,"report":bridge.report()})
	bridge.disconnect_session();bridge.open_session(PROFILE,d,SCOPE);bridge.apply_snapshot(snapshot())
	var burst_ok := true
	for seq in 128: burst_ok=burst_ok and bridge.apply_event(event(seq,0)).ok
	check("128_receipts_have_bounded_64_event_presentations",burst_ok and bridge.report().event_count==64 and bridge.report().last_event_seq==127)
	check("tick_expiry_releases_all_event_presentations",bridge.apply_snapshot(snapshot(40)).ok and bridge.report().event_count==0)
	for cycle in 30:
		bridge.disconnect_session();bridge.open_session(PROFILE,d,SCOPE);bridge.apply_snapshot(snapshot());bridge.disconnect_session()
	check("30_session_cycles_do_not_accumulate_nodes",count_nodes(bridge)==3 and bridge.report().entity_count==0 and bridge.report().mesh_resources<=10)
	var weak: WeakRef=weakref(bridge);bridge.queue_free();await process_frame
	check("tree_teardown_releases_bridge_and_owned_children",weak.get_ref()==null)
	var same := true
	for path in pins: same=same and pins[path]==FileAccess.get_sha256(path)
	check("sources_frozen_during_test",same)
	var passed := true
	for c in checks: passed=passed and c.passed
	var result := {"passed":passed,"checks":checks,"source_sha256":pins,"engine":Engine.get_version_info().string,"scope":"Actual headless Node3D/MeshInstance creation, update, generation/discontinuity, aim, bounded events and replay/reconnect lifecycle under synthetic contract-v1 records. No server transport, rendered art or authoritative gameplay."}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):
			var file := FileAccess.open(arg.trim_prefix("--report="),FileAccess.WRITE);file.store_string(JSON.stringify(result,"\t")+"\n")
	print(JSON.stringify({"passed":passed,"checks":checks.size()}));quit(0 if passed else 1)
