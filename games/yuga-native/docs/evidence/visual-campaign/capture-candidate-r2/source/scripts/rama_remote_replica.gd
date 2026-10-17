extends Node3D
## Pose-only presentation of Rama from existing validated APIs. No gameplay authority.
## Protocol 2 has no Rama action lifecycle, pitch or traversal snapshots. Those
## states deliberately remain unsupported rather than inferred from cooldowns.
const ArenaClient = preload("res://scripts/arena_client.gd")
const Interpolator = preload("res://scripts/arena_interpolator.gd")
const EntityBridge = preload("res://scripts/entity_bridge.gd")
const RamaMotion = preload("res://scripts/rama_motion.gd")
const MIN_RENDER_DELTA_SECONDS := 0.000001
const MAX_CLOCK_SECONDS := 1000000000000.0
const POSITION_LIMIT := 10000.0
const STALE_SECONDS := 1.0
const MAX_SPEED := 35.0
const TELEPORT_DISTANCE := 6.0
var _visual: Node3D
var _motion: SkeletonModifier3D
var _source: Node
var _source_kind := "none"
var _actor_id := ""
var _sampler: RefCounted = Interpolator.new()
var _last_tick := -1
var _last_received := -1.0
var _last_now := -1.0
var _last_pose := Vector3.ZERO
var _have_pose := false
var _alive := false
var _present := false
var _terminal := false
var _arena_dirty := true
var _identity_key := ""
var _scope_key := ""
var _discontinuity_key := ""
var _mode := "unbound"
var _last_reason := "unbound"
var _pitch := 0.0
var _velocity := Vector3.ZERO
var _counts := {"snapshots":0,"resets":0,"pose_updates":0,"rejected_updates":0,"missing":0,"stale_hides":0}

func _init() -> void:
	# Snapshot positions are world feet coordinates, independent of scene parents.
	top_level = true
	set_process(false)

func _find(node: Node, kind: String) -> Node:
	if node.is_class(kind): return node
	for child in node.get_children():
		var found := _find(child,kind)
		if found: return found
	return null

func _has_motion(node: Node) -> bool:
	if node.get_script() == RamaMotion: return true
	for child in node.get_children():
		if _has_motion(child): return true
	return false

func configure_visual(visual: Node3D, animator: AnimationPlayer = null) -> bool:
	# The caller supplies the actual hero. This component never creates a fallback
	# avatar or loads a diagnostic mesh as a product character.
	if is_instance_valid(_visual) or not is_instance_valid(visual) or visual.get_parent() != self or _has_motion(visual): return false
	if animator == null: animator = _find(visual,"AnimationPlayer")
	elif not visual.is_ancestor_of(animator): return false
	var candidate := RamaMotion.new()
	if not candidate.configure(visual,animator):
		candidate.free()
		return false
	_visual = visual
	_motion = candidate
	_visual.rotation.y = PI
	_visual.visible = false
	return true

func bind_arena(client: Node, remote_actor_id: String) -> bool:
	if not is_instance_valid(client) or client.get_script() != ArenaClient or not _valid_id(remote_actor_id) or remote_actor_id == client.identity: return false
	unbind_source()
	_source = client
	_source_kind = "arena_protocol2"
	_actor_id = remote_actor_id
	client.state_changed.connect(_on_arena_state)
	client.snapshot_received.connect(_on_arena_snapshot)
	set_process(true)
	_mode = "waiting"
	return true

func bind_bridge(bridge: Node3D, actor_id: String) -> bool:
	if not is_instance_valid(bridge) or bridge.get_script() != EntityBridge or not _valid_id(actor_id): return false
	unbind_source()
	_source = bridge
	_source_kind = "validated_entity_bridge"
	_actor_id = actor_id
	set_process(true)
	_mode = "waiting"
	return true

func unbind_source() -> void:
	if is_instance_valid(_source) and _source_kind == "arena_protocol2" and _source.state_changed.is_connected(_on_arena_state):
		_source.state_changed.disconnect(_on_arena_state)
	if is_instance_valid(_source) and _source_kind == "arena_protocol2" and _source.snapshot_received.is_connected(_on_arena_snapshot):
		_source.snapshot_received.disconnect(_on_arena_snapshot)
	set_process(false)
	_source = null
	_source_kind = "none"
	_actor_id = ""
	reset_replica("source unbound")
	_mode = "unbound"

func reset_replica(reason := "explicit reset") -> void:
	_sampler.reset()
	_last_tick = -1
	_last_received = -1.0
	_last_now = -1.0
	_have_pose = false
	_alive = false
	_present = false
	_terminal = false
	_arena_dirty = true
	_identity_key = ""
	_scope_key = ""
	_discontinuity_key = ""
	_pitch = 0.0
	_velocity = Vector3.ZERO
	_hide(reason)
	_reset_motion(reason)

func _on_arena_snapshot(_ignored_signal_payload: Dictionary) -> void:
	# Dirty flag only: use get_snapshot() for the accepted canonical copy.
	_arena_dirty = true

func _on_arena_state(state: String) -> void:
	if state in ["connecting","joining","disconnected"]:
		reset_replica("transport " + state)
		_mode = "waiting"

func _exit_tree() -> void:
	unbind_source()

func _process(delta: float) -> void:
	advance(delta)

func _valid_id(value: String) -> bool:
	if value.is_empty() or value.length() > 64: return false
	for character in value:
		if not (character >= "a" and character <= "z" or character >= "A" and character <= "Z" or character >= "0" and character <= "9" or character in ["_","-"]): return false
	return true

func _clock(value: float) -> float:
	var now := float(Time.get_ticks_usec()) / 1000000.0 if value == -1.0 else value
	if not is_finite(now) or now < 0 or now > MAX_CLOCK_SECONDS or now < _last_now: return NAN
	return now

func _reset_motion(reason: String) -> void:
	_counts.resets += 1
	_have_pose = false
	_velocity = Vector3.ZERO
	if is_instance_valid(_motion): _motion.cancel(reason)
	if is_inside_tree(): reset_physics_interpolation()

func _hide(reason: String) -> void:
	if is_instance_valid(_visual): _visual.visible = false
	_last_reason = reason

func _poll_arena(now: float) -> Dictionary:
	if _source.state not in ["playing","finished"] or not _arena_dirty: return {}
	# Read the client's accepted copy. A caller-supplied signal payload is never
	# accepted as a snapshot and no unvalidated dictionary admission API exists.
	var snapshot: Dictionary = _source.get_snapshot()
	_arena_dirty = false
	if snapshot.is_empty() or int(snapshot.tick) == _last_tick: return {}
	if int(snapshot.tick) < _last_tick:
		_counts.rejected_updates += 1
		return {}
	if _actor_id == _source.identity:
		_present = false
		_alive = false
		_sampler.reset()
		_hide("local actor is not a remote replica")
		return {}
	var actor := {}
	for entry in snapshot.actors:
		if entry.id == _actor_id: actor = entry; break
	_last_tick = int(snapshot.tick)
	_counts.snapshots += 1
	var stale_reappearance := _last_received >= 0 and now - _last_received > STALE_SECONDS
	_last_received = now
	_terminal = snapshot.phase == "finished"
	var present: bool = not actor.is_empty() and actor.kind == "hero" and actor.heroId == "rama" and actor.connected
	if not present:
		if _present: _counts.missing += 1
		_present = false
		_alive = false
		_sampler.reset(snapshot.room)
		_reset_motion("authoritative actor absent or not Rama")
		_hide("authoritative actor absent or not Rama")
		return {}
	var alive := float(actor.health) > 0.0 and float(actor.respawn) <= 0.0
	var identity := "%s|%s|%s|%s" % [snapshot.room,actor.id,actor.heroId,actor.team]
	if not _present or alive != _alive or identity != _identity_key or _mode == "stale" or stale_reappearance:
		_sampler.reset(snapshot.room)
		_reset_motion("authority lifecycle changed; protocol2 has no generations")
	_identity_key = identity
	_present = true
	_alive = alive
	_pitch = 0.0 # Explicitly unavailable in protocol2 Actor.
	var pose_snapshot := {"protocol":snapshot.protocol,"room":snapshot.room,"tick":snapshot.tick,"time":snapshot.time,"duration":snapshot.duration,"phase":snapshot.phase,"actors":[actor]}
	if not _sampler.push_snapshot(pose_snapshot,now):
		_counts.rejected_updates += 1
		return {}
	return {"accepted":true}

func _poll_bridge(now: float) -> Dictionary:
	# This is an explicit separate adapter for the validator bridge, not a wire
	# conversion to browser protocol2. The bridge currently has no live transport.
	var report: Dictionary = _source.report()
	if report.state not in ["active","replay"]:
		if report.state == "closed" and _present:
			_present = false
			_alive = false
			_scope_key = ""
			_reset_motion("validated bridge closed")
		return {}
	var scope: Dictionary = report.session.get("scope",{})
	if scope.is_empty(): return {}
	var scope_key := "%s|%s" % [scope.room,scope.epoch]
	if scope_key != _scope_key:
		_last_tick = -1
		_present = false
		_scope_key = scope_key
		_reset_motion("validated bridge scope changed")
	var tick := int(report.last_snapshot_tick)
	if tick == _last_tick: return {}
	if tick < _last_tick:
		_counts.rejected_updates += 1
		return {}
	_last_tick = tick
	_counts.snapshots += 1
	var stale_reappearance := _last_received >= 0 and now - _last_received > STALE_SECONDS
	_last_received = now
	if not report.entities.has(_actor_id):
		if _present: _counts.missing += 1
		_present = false
		_alive = false
		_reset_motion("validated full snapshot omission")
		_hide("validated full snapshot omission")
		return {}
	var entity: Dictionary = report.entities[_actor_id]
	if entity.kind != "actor":
		_present = false
		_hide("validated entity is not an actor")
		return {}
	var node: Node3D = _source.entity_node(_actor_id)
	if not is_instance_valid(node):
		_present = false
		_hide("validated presentation node was freed")
		return {}
	var discontinuity := "%s|%s|%s|%s" % [scope_key,node.get_instance_id(),entity.generation,entity.discontinuity]
	if not _present or discontinuity != _discontinuity_key or _alive != entity.alive or _mode == "stale" or stale_reappearance:
		_reset_motion("validated lifetime or discontinuity changed")
	_discontinuity_key = discontinuity
	_present = true
	_alive = entity.alive
	_pitch = float(entity.pitch)
	return {"position":Vector3(entity.position[0],entity.position[1],entity.position[2]),"yaw":float(node.rotation.y),"mode":"validated_bridge_exact"}

func advance(delta: float, at_seconds := -1.0) -> bool:
	var now := _clock(at_seconds)
	if not is_finite(delta) or delta < MIN_RENDER_DELTA_SECONDS or delta > 10.0 or not is_finite(now):
		_counts.rejected_updates += 1
		return false
	if not is_instance_valid(_visual) or not is_instance_valid(_motion) or _visual.is_queued_for_deletion() or _motion.is_queued_for_deletion() or not _motion.configured:
		_hide("hero visual or motion was freed or never configured")
		_counts.rejected_updates += 1
		return false
	_last_now = now
	if not is_instance_valid(_source) or _source.is_queued_for_deletion():
		_hide("source was freed or unbound")
		_mode = "unbound"
		_reset_motion("source was freed or unbound")
		return false
	var pose := {}
	if _source_kind == "arena_protocol2":
		_poll_arena(now)
		if _present:
			var frame: Dictionary = _sampler.sample(now)
			if not frame.actors.is_empty():
				var actor: Dictionary = frame.actors[0]
				pose = {"position":Vector3(actor.x,actor.y,actor.z),"yaw":float(actor.yaw),"mode":String(actor.get("presentation_mode","held"))}
	else:
		pose = _poll_bridge(now)
		# An unchanged validated tick holds its exact pose; never extrapolate an
		# envelope whose catalogue has no assigned presentation clock frequency.
		if pose.is_empty() and _present: pose = {"position":global_position,"yaw":EntityBridge.native_to_shared_yaw(global_rotation.y),"mode":"validated_bridge_held"}
	if not _present or not _alive:
		_hide("authority reports absent or defeated actor")
		_mode = "hidden"
		return true
	if not _terminal and _last_received >= 0 and now - _last_received > STALE_SECONDS:
		if _mode != "stale":
			_counts.stale_hides += 1
			_reset_motion("authority snapshot timeout")
		_hide("authority snapshot timeout")
		_mode = "stale"
		return true
	if pose.is_empty(): return true
	var position_: Vector3 = pose.position
	var shared_yaw: float = pose.yaw
	if not position_.is_finite() or maxf(absf(position_.x),maxf(absf(position_.y),absf(position_.z))) > POSITION_LIMIT or not is_finite(shared_yaw) or absf(shared_yaw) > TAU or not is_finite(_pitch) or absf(_pitch) > 1.35:
		_counts.rejected_updates += 1
		_hide("invalid presentation pose")
		return false
	_velocity = (position_ - _last_pose) / delta if _have_pose else Vector3.ZERO
	if not _velocity.is_finite() or _have_pose and (_last_pose.distance_to(position_) > TELEPORT_DISTANCE or _velocity.length() > MAX_SPEED):
		_reset_motion("presentation teleport or discontinuity")
		_velocity = Vector3.ZERO
	global_position = position_
	global_rotation = Vector3(0,EntityBridge.shared_to_native_yaw(wrapf(shared_yaw,-PI,PI)),0)
	_last_pose = position_
	_have_pose = true
	_visual.visible = true
	_mode = pose.mode
	_last_reason = "accepted pose only"
	_counts.pose_updates += 1
	# No jump/flight/grapple/aim/cast is invented from displacement, height,
	# cooldowns or generic ability receipts. Ground reference is the feet pose,
	# not a verified support surface. Network Rama action events remain OPEN.
	return _motion.update_motion(minf(delta,.1),{"velocity":_velocity,"local_velocity":_visual.global_basis.inverse()*_velocity,"grounded":true,"traversal":"ground","aiming":false,"aim_pitch":_pitch,"aim_yaw":0.0,"floor_y":position_.y})

func report() -> Dictionary:
	return {"source_kind":_source_kind,"actor_id":_actor_id,"mode":_mode,"reason":_last_reason,"last_tick":_last_tick,"present":_present,"alive":_alive,"visible":is_instance_valid(_visual) and _visual.visible,"position":[global_position.x,global_position.y,global_position.z],"velocity":[_velocity.x,_velocity.y,_velocity.z],"buffered_snapshots":_sampler.buffered_snapshot_count(),"maximum_snapshots":Interpolator.MAX_SNAPSHOTS,"stale_seconds":STALE_SECONDS,"counts":_counts.duplicate(true),"motion_bound":is_instance_valid(_motion) and _motion.configured,"network_connected_by_this_component":false,"local_damage_authority":false,"action_replication":"unsupported","unsupported_fields":["Rama action lifecycle","Rama four-ability authority","grounded support surface","flight/grapple","protocol2 remote pitch","protocol2 lifetime generation","bridge hero asset identification"],"scope":"Pose adapter only; not integrated native multiplayer or visual/hardware acceptance."}
