extends SceneTree
const Replica = preload("res://scripts/rama_remote_replica.gd")
const Client = preload("res://scripts/arena_client.gd")
const Bridge = preload("res://scripts/entity_bridge.gd")
const Motion = preload("res://scripts/rama_motion.gd")
var checks: Array[Dictionary] = []
var report_path := "/tmp/rama-remote-replica.json"
var pinned := {}
func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): report_path = arg.trim_prefix("--report=")
	call_deferred("run")
func check(label: String, passed: bool, details := {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)
func rig_fixture() -> Node3D:
	# Exact authored rest rig, with NO GLB, mesh, imported art or renderer. This
	# exercises the real RamaMotion binding API, not a substitute avatar product.
	var library: AnimationLibrary = load(Motion.LIBRARY_PATH)
	var visual := Node3D.new()
	var skeleton := Skeleton3D.new()
	visual.add_child(skeleton)
	var names: Array = library.get_meta("rama_rig_names")
	var parents: PackedInt32Array = library.get_meta("rama_rig_parents")
	var rests: Array = library.get_meta("rama_rig_rest")
	for index in names.size(): skeleton.add_bone(names[index])
	for index in names.size():
		skeleton.set_bone_parent(index,parents[index])
		skeleton.set_bone_rest(index,rests[index])
	return visual
func create_replica() -> Node3D:
	var replica := Replica.new()
	root.add_child(replica)
	var visual := rig_fixture()
	replica.add_child(visual)
	check("real_motion_binds_exact164_rest_fixture",replica.configure_visual(visual) and replica.report().motion_bound)
	return replica
func actor(id := "remote") -> Dictionary:
	return {"id":id,"heroId":"rama","name":"Fixture","kind":"hero","team":"sun" if id=="local" else "moon","lane":0,"bot":false,"connected":true,"x":0,"y":0,"z":0,"yaw":0,"health":300,"maxHealth":300,"lastInputSeq":-1,"shield":0,"respawn":0,"fireCooldown":0,"credits":180,"level":1,"kills":0,"deaths":0,"assists":0,"damageDealt":0,"cooldowns":[0,0,0],"upgrades":{"power":0,"vitality":0,"tempo":0},"effects":{"haste":0,"slow":0,"ward":0}}
func snapshot(tick := 0, time := 0.0, x := 0.0) -> Dictionary:
	var remote := actor()
	remote.x = x
	return {"protocol":2,"room":"FIXTURE","tick":tick,"time":time,"duration":480.0,"phase":"playing","winner":null,"reason":"","seed":1,"actors":[actor("local"),remote],"neutrals":[],"goldShards":[],"structures":[],"projectiles":[],"zones":[],"pickups":[],"events":[],"scores":{"sun":0,"moon":0}}
func create_client() -> Node:
	var client := Client.new()
	root.add_child(client)
	client.state = "joining"
	client._handle_message({"type":"welcome","protocol":2,"id":"local","room":"FIXTURE","token":"a".repeat(48),"snapshot":snapshot()})
	return client
func deliver(client: Node, value: Dictionary) -> void:
	client._handle_message({"type":"snapshot","snapshot":value})
func entity(id := "remote") -> Dictionary:
	return {"id":id,"generation":1,"kind":"actor","team":"sun","position":[0.0,0.0,0.0],"yaw":0.0,"pitch":0.0,"discontinuity":0,"alive":true,"ack_input":-1,"owner_id":""}
func bridge_snapshot(tick := 0) -> Dictionary:
	return {"version":1,"room":"REPLICA","epoch":1,"tick":tick,"entities":[entity()]}
func run() -> void:
	for path in ["res://scripts/rama_remote_replica.gd","res://tests/rama_remote_replica_cases.gd","res://scripts/rama_motion.gd","res://scripts/arena_client.gd","res://scripts/arena_interpolator.gd","res://scripts/entity_bridge.gd","res://scripts/native_contracts.gd","res://assets/animations/rama_hero_motion.tres"]: pinned[path] = FileAccess.get_sha256(path)
	var replica := create_replica()
	var visual: Node3D = replica.get_child(0)
	check("duplicate_visual_binding_rejected",not replica.configure_visual(visual))
	var alien := Node.new()
	check("unvalidated_ducktyped_source_rejected",not replica.bind_arena(alien,"remote"))
	alien.free()
	var client := create_client()
	check("local_actor_cannot_be_remote_replica",not replica.bind_arena(client,"local"))
	check("validated_client_binds_remote_pose",replica.bind_arena(client,"remote") and replica.advance(1.0/60,10.0) and replica.report().visible)
	check("shared_forward_maps_to_model_forward",absf(wrapf(replica.global_rotation.y + visual.rotation.y,-PI,PI))<.0001)
	deliver(client,snapshot(1,.1,1.0));replica.advance(1.0/60,10.1);replica.advance(1.0/60,10.15)
	check("accepted_snapshot_interpolates_without_step",absf(replica.global_position.x-.5)<.001,{"x":replica.global_position.x})
	check("locomotion_is_derived_without_action_authority",replica._motion.locomotion in ["run","sprint"] and replica._motion.action=="" and not replica.report().local_damage_authority and not replica.report().network_connected_by_this_component)
	var before: Vector3 = replica.global_position
	var rejected: int = client.rejected_packets
	var bad := snapshot(2,.2,INF);deliver(client,bad)
	replica.advance(1.0/60,10.16)
	check("nonfinite_wire_rejected_by_existing_client",client.rejected_packets==rejected+1 and replica.global_position.is_finite())
	deliver(client,snapshot(0,0,99));var count: int = replica.report().counts.snapshots
	replica.advance(1.0/60,10.17)
	check("late_outoforder_snapshot_does_not_enter_buffer",client.stale_snapshots==1 and replica.report().counts.snapshots==count)
	var state_before: Dictionary = replica.report()
	check("invalid_delta_and_clock_leave_pose_unchanged",not replica.advance(NAN,10.18) and not replica.advance(0,10.18) and not replica.advance(1e-50,10.18) and not replica.advance(1.0/60,1e308) and not replica.advance(1.0/60,INF) and not replica.advance(1.0/60,9) and replica.global_position==Vector3(state_before.position[0],state_before.position[1],state_before.position[2]))
	client.snapshot_received.emit(snapshot(999,100,INF));replica.advance(1.0/60,10.18)
	check("signal_payload_cannot_replace_accepted_snapshot",replica.report().counts.snapshots==count and replica.global_position.is_finite())
	replica.advance(.1,11.2)
	check("stale_source_hides_without_fabricating_death",not replica.report().visible and replica.report().mode=="stale" and replica.report().alive and replica._motion.action=="")
	var stale_resets: int = replica.report().counts.resets
	replica.advance(.1,11.25)
	check("stale_hold_does_not_reset_motion_every_frame",replica.report().counts.resets==stale_resets)
	deliver(client,snapshot(2,.2,3.0));replica.advance(1.0/60,11.3)
	check("visibility_reappearance_has_no_old_origin_sweep",replica.report().visible and replica.global_position.distance_to(Vector3(3,0,0))<.001 and replica._motion.action=="",replica.report())
	var dead := snapshot(3,.3,4);dead.actors[1].health=0;dead.actors[1].respawn=3
	deliver(client,dead);replica.advance(1.0/60,11.4)
	check("authority_death_hides_no_damage_or_fake_death_event",not replica.report().visible and not replica.report().alive and client.get_snapshot().actors[1].health==0 and replica._motion.action=="")
	deliver(client,snapshot(4,.4,50));replica.advance(1.0/60,11.5)
	check("authority_respawn_snaps_and_clears_velocity",replica.report().visible and replica.global_position.distance_to(Vector3(50,0,0))<.001 and Vector3(replica.report().velocity[0],replica.report().velocity[1],replica.report().velocity[2]).length()<.001)
	var absent := snapshot(5,.5);absent.actors.remove_at(1);deliver(client,absent);replica.advance(1.0/60,11.6)
	check("full_snapshot_omission_hides_and_releases_history",not replica.report().visible and replica.report().buffered_snapshots==0)
	var not_rama := snapshot(6,.6);not_rama.actors[1].heroId="hanuman";deliver(client,not_rama);replica.advance(1.0/60,11.7)
	check("different_hero_is_not_misrepresented_as_Rama",not replica.report().visible)
	client._set_state("connecting")
	check("reconnect_clears_history_even_for_same_room",replica.report().buffered_snapshots==0 and not replica.report().visible)
	client._snapshot={};client.last_tick=-1;client._set_state("playing")
	deliver(client,snapshot(0,0,75));replica.advance(1.0/60,20)
	check("reused_actor_after_reconnect_has_no_stale_pose",replica.global_position.distance_to(Vector3(75,0,0))<.001)
	# Paused presentation resumes on a fresh accepted pose, with no catch-up run.
	deliver(client,snapshot(1,.1,76));replica.advance(2.0,22.0)
	check("long_pause_fresh_receipt_resets_history_without_catchup",replica.global_position.distance_to(Vector3(76,0,0))<.001 and replica._motion.movement_speed==0)
	client._set_state("connecting");client._snapshot={};client.last_tick=-1;client._set_state("playing")
	deliver(client,snapshot(0,0,75));replica.advance(.1,30.0)
	for index in range(1,100):
		deliver(client,snapshot(index,float(index)/10,75+float(index)/10))
		replica.advance(.1,30+float(index)/10)
	check("snapshot_history_is_bounded32",replica.report().buffered_snapshots==32,{"buffered":replica.report().buffered_snapshots})
	var finish := snapshot(100,10.0,85);finish.phase="finished";finish.winner="draw"
	deliver(client,finish);replica.advance(.1,40);replica.advance(.1,45)
	check("accepted_terminal_pose_holds_without_unbounded_projection",replica.report().visible and replica.global_position.distance_to(Vector3(85,0,0))<.001)
	client.free()
	check("freed_transport_hides_without_invalid_instance_access",not replica.advance(1.0/60,45.1) and not replica.report().visible)
	replica.free()

	# Two accepted yaws straddling +PI/-PI take the short arc.
	client=create_client();replica=create_replica();replica.bind_arena(client,"remote")
	var left:=snapshot(1,.1,0);left.actors[1].yaw=PI-.1;deliver(client,left);replica.advance(.1,1.0)
	var right:=snapshot(2,.2,0);right.actors[1].yaw=-PI+.1;deliver(client,right);replica.advance(.1,1.1);replica.advance(.05,1.15)
	check("yaw_wrap_uses_short_arc_without_full_spin",absf(replica.global_rotation.y)<.001 and replica.global_rotation.is_finite(),{"native_yaw":replica.global_rotation.y})
	client.queue_free()
	check("queued_transport_fails_closed_before_tree_flush",not replica.advance(.05,1.2) and not replica.report().visible)
	replica.free();client.free()

	var bridge := Bridge.new();root.add_child(bridge)
	var descriptor: Dictionary=bridge.descriptor("native-offline-triad")
	check("existing_bridge_validator_session_opens",bridge.open_session("native-offline-triad",descriptor,{"room":"REPLICA","epoch":1,"identity":"remote"}).ok and bridge.apply_snapshot(bridge_snapshot()).ok)
	replica=create_replica();visual=replica.get_child(0)
	check("bridge_pose_path_is_explicit_and_not_protocol2",replica.bind_bridge(bridge,"remote") and replica.advance(1.0/60,1) and replica.report().source_kind=="validated_entity_bridge" and replica.report().visible)
	var moved := bridge_snapshot(1);moved.entities[0].position=[2,3,4];moved.entities[0].pitch=.6;moved.entities[0].yaw=PI/2
	check("validated_bridge_carries_pitch_without_inventing_traversal",bridge.apply_snapshot(moved).ok and replica.advance(.1,1.1) and replica.global_position.distance_to(Vector3(2,3,4))<.001 and replica._motion.aim_pitch>0 and replica._motion.traversal=="ground" and replica._motion.action=="")
	var tele := moved.duplicate(true);tele.tick=2;tele.entities[0].position=[100,0,1];tele.entities[0].discontinuity=1
	var reset_count: int=replica.report().counts.resets
	check("bridge_explicit_teleport_resets_once_without_sweep",bridge.apply_snapshot(tele).ok and replica.advance(.1,1.2) and replica.global_position==Vector3(100,0,1) and replica._motion.movement_speed==0 and replica.report().counts.resets==reset_count+1)
	var dead_bridge := tele.duplicate(true);dead_bridge.tick=3;dead_bridge.entities[0].alive=false;dead_bridge.entities[0].discontinuity=2
	check("validated_bridge_lifecycle_hides",bridge.apply_snapshot(dead_bridge).ok and replica.advance(.1,1.3) and not replica.report().visible)
	var revive := dead_bridge.duplicate(true);revive.tick=4;revive.entities[0].alive=true;revive.entities[0].discontinuity=3;revive.entities[0].generation=2;revive.entities[0].position=[5,0,5]
	check("new_generation_restores_exact_pose_and_motion_history",bridge.apply_snapshot(revive).ok and replica.advance(.1,1.4) and replica.report().visible and replica.global_position==Vector3(5,0,5) and replica._motion.movement_speed==0)
	var invalid := revive.duplicate(true);invalid.tick=5;invalid.entities[0].pitch=INF
	check("invalid_bridge_payload_never_mutates_replica",not bridge.apply_snapshot(invalid).ok and replica.advance(.1,1.5) and replica.global_position==Vector3(5,0,5))
	bridge.disconnect_session();replica.advance(.1,1.55)
	check("bridge_disconnect_hides_immediately_without_timeout",not replica.report().visible and not replica.report().present)
	check("bridge_reopen_requires_current_scope_pose",bridge.open_session("native-offline-triad",descriptor,{"room":"REPLICA","epoch":2,"identity":"remote"}).ok)
	var reopened:=bridge_snapshot();reopened.epoch=2;reopened.entities[0].position=[20,0,20]
	check("new_bridge_epoch_reuses_id_without_old_origin",bridge.apply_snapshot(reopened).ok and replica.advance(.1,1.6) and replica.global_position==Vector3(20,0,20) and replica._motion.movement_speed==0)
	visual.free()
	check("freed_visual_and_modifier_fail_closed",not replica.advance(.1,1.7) and not replica.report().motion_bound and not replica.report().visible)
	replica.free();bridge.free()
	var frozen := true
	for path in pinned: frozen=frozen and pinned[path]==FileAccess.get_sha256(path)
	check("sources_frozen_during_tests",frozen)
	var passed := true
	for result in checks: passed=passed and result.passed
	var report := {"passed":passed,"checks":checks,"count":checks.size(),"sources":pinned,"engine":Engine.get_version_info().string,"scope":"Exact164-bone rest-fixture component test, real client and bridge validation APIs. No GLB/render/native match/WAN/hardware acceptance."}
	var file := FileAccess.open(report_path,FileAccess.WRITE);file.store_string(JSON.stringify(report,"\t")+"\n")
	print("RAMA_REMOTE_REPLICA_REPORT ",JSON.stringify({"passed":passed,"checks":checks.size()}))
	quit(0 if passed else 1)
