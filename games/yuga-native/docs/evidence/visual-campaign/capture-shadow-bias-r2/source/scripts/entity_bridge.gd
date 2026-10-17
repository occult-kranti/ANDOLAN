extends Node3D
## Original contract-driven diagnostic presentation. No collisions, input sending or gameplay outcomes.
const Contracts = preload("res://scripts/native_contracts.gd")
const MAX_EVENT_VIEWS := 64
const EVENT_LIFETIME_TICKS := 40
var _guard: RefCounted
var _catalog_status: Dictionary
var _state := "closed"
var _entity_root: Node3D
var _event_root: Node3D
var _views: Dictionary = {}
var _event_views: Dictionary = {}
var _meshes: Dictionary = {}
var _materials: Dictionary = {}
var _presentation_tick := -1
var _replay_header: Dictionary = {}
var _replay_records: Array = []
var _replay_cursor := 0
var _counts := {"spawned":0,"despawned":0,"updates":0,"discontinuities":0,"events_presented":0,"events_evicted":0}

func _init() -> void:
	_guard=Contracts.new()
	_catalog_status=_guard.load_catalog()
	_entity_root=Node3D.new();_entity_root.name="Entities";_entity_root.top_level=true;add_child(_entity_root)
	_event_root=Node3D.new();_event_root.name="EventReceipts";_event_root.top_level=true;add_child(_event_root)
	set_process(false)
	set_physics_process(false)

static func _result(ok: bool, code := "OK") -> Dictionary:
	return {"ok":ok,"code":code}

static func aim_direction(yaw: float, pitch: float) -> Vector3:
	if not is_finite(yaw) or not is_finite(pitch) or absf(yaw)>PI or absf(pitch)>1.35: return Vector3.ZERO
	return Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))

static func native_to_shared_yaw(yaw: float) -> float:
	return wrapf(yaw+PI,-PI,PI) if is_finite(yaw) and absf(yaw)<=TAU else NAN

static func shared_to_native_yaw(yaw: float) -> float:
	return wrapf(yaw-PI,-PI,PI) if is_finite(yaw) and absf(yaw)<=PI else NAN

func descriptor(profile_id: String) -> Dictionary:
	return _guard.descriptor(profile_id)

func open_session(profile_id: String, remote: Variant, scope: Variant) -> Dictionary:
	if not _catalog_status.ok: return _catalog_status.duplicate(true)
	if _state!="closed": return _result(false,"BRIDGE_ALREADY_OPEN")
	var accepted: Dictionary=_guard.open_session(profile_id,remote,scope)
	if not accepted.ok: return accepted
	_state="active"
	return _result(true,"PRESENTATION_OPEN_NOT_CONNECTED")

func submit_input(value: Variant) -> Dictionary:
	if _state!="active": return _result(false,"INPUT_BLOCKED_"+_state.to_upper())
	return _guard.accept_input(value)

func apply_snapshot(value: Variant) -> Dictionary:
	if _state!="active": return _result(false,"SNAPSHOT_BLOCKED_"+_state.to_upper())
	var accepted: Dictionary=_guard.accept_snapshot(value)
	if not accepted.ok: return accepted
	_sync_entities(_guard.report().entities)
	_expire_events(int(value.tick))
	return _result(true)

func apply_event(value: Variant) -> Dictionary:
	if _state!="active": return _result(false,"EVENT_BLOCKED_"+_state.to_upper())
	var accepted: Dictionary=_guard.accept_event(value)
	if not accepted.ok: return accepted
	_expire_events(int(value.tick))
	_present_event(value)
	return _result(true)

func begin_reconnect() -> Dictionary:
	if _state!="active": return _result(false,"NOT_ACTIVE")
	_state="reconnecting"
	_clear_events()
	# Accepted entities freeze in place; no prediction, extrapolation or input queue.
	return _result(true,"PRESENTATION_FROZEN")

func resume_session(remote: Variant, scope: Variant) -> Dictionary:
	if _state!="reconnecting": return _result(false,"NOT_RECONNECTING")
	var accepted: Dictionary=_guard.resume_session(remote,scope)
	if not accepted.ok: return accepted
	_clear_events()
	_state="active"
	return accepted

func migrate_session(profile_id: String, remote: Variant, scope: Variant) -> Dictionary:
	if _state not in ["active","reconnecting"]: return _result(false,"NO_LIVE_VALIDATOR_SESSION")
	var accepted: Dictionary=_guard.migrate_session(profile_id,remote,scope)
	if not accepted.ok: return accepted
	_clear_views()
	_clear_replay()
	_state="active"
	return accepted

func disconnect_session() -> void:
	_clear_views()
	_clear_replay()
	_guard.reset()
	_state="closed"

func _clear_replay() -> void:
	_replay_header.clear();_replay_records.clear();_replay_cursor=0

func _free_view(node: Node3D) -> void:
	if is_instance_valid(node):
		if node.get_parent()!=null: node.get_parent().remove_child(node)
		node.free()

func _clear_events() -> void:
	for node in _event_views.values(): _free_view(node)
	_event_views.clear()

func _clear_views() -> void:
	for node in _views.values(): _free_view(node)
	_views.clear()
	_clear_events()
	_presentation_tick=-1

func _drop_entity(id: String) -> void:
	if _views.has(id):
		_free_view(_views[id]);_views.erase(id)
		_counts.despawned+=1
	_clear_entity_events(id)

func _clear_entity_events(id: String) -> void:
	for seq in _event_views.keys():
		var node: Node3D=_event_views[seq]
		if node.get_meta("actor_id")==id or node.get_meta("target_id")==id:
			_free_view(node);_event_views.erase(seq)

func _sync_entities(entities: Dictionary) -> void:
	for id in _views.keys():
		if not entities.has(id): _drop_entity(id)
	for id in entities:
		var e: Dictionary=entities[id]
		if _views.has(id) and int(_views[id].get_meta("generation"))!=int(e.generation): _drop_entity(id)
		if not _views.has(id):
			var created := _make_entity(e)
			_entity_root.add_child(created);_views[id]=created;_counts.spawned+=1
		var node: Node3D=_views[id]
		var reset_history: bool=int(node.get_meta("discontinuity",-1))!=int(e.discontinuity)
		if reset_history:
			_clear_entity_events(id)
			_counts.discontinuities+=1
			node.set_meta("history_reset_count",int(node.get_meta("history_reset_count",0))+1)
		node.position=Vector3(e.position[0],e.position[1],e.position[2])
		node.rotation=Vector3(0,float(e.yaw),0)
		var aim: Node3D=node.get_node("Aim")
		aim.rotation=Vector3(-float(e.pitch),0,0)
		if e.kind=="projectile": node.get_node("Body").rotation.x=PI/2-float(e.pitch)
		if reset_history: node.reset_physics_interpolation()
		node.set_meta("generation",int(e.generation));node.set_meta("discontinuity",int(e.discontinuity))
		node.set_meta("alive",e.alive);node.set_meta("ack_input",int(e.ack_input));node.set_meta("pitch",float(e.pitch))
		# Identity, collision and rewards remain entirely in authority, never this mesh.
		node.get_node("Body").visible=e.alive
		aim.visible=e.alive
		_counts.updates+=1

func _material(team: String) -> StandardMaterial3D:
	if _materials.has(team): return _materials[team]
	var material := StandardMaterial3D.new()
	material.albedo_color=Color("e8bc69") if team=="sun" else Color("8569cc") if team=="moon" else Color("53aaa4")
	material.roughness=.8
	_materials[team]=material
	return material

func _mesh(kind: String) -> Mesh:
	if _meshes.has(kind): return _meshes[kind]
	var mesh: Mesh
	match kind:
		"actor","minion","neutral":
			var capsule := CapsuleMesh.new();capsule.radius=.32 if kind=="actor" else .25;capsule.height=1.8 if kind=="actor" else 1.25
			capsule.radial_segments=12;capsule.rings=4;mesh=capsule
		"structure":
			var box := BoxMesh.new();box.size=Vector3(1.4,3,1.4);mesh=box
		"projectile","aim":
			var bolt := CylinderMesh.new();bolt.top_radius=.015;bolt.bottom_radius=.035;bolt.height=.8;bolt.radial_segments=6;mesh=bolt
		"zone":
			var disc := CylinderMesh.new();disc.top_radius=1.2;disc.bottom_radius=1.2;disc.height=.04;disc.radial_segments=16;mesh=disc
		_:
			var sphere := SphereMesh.new();sphere.radius=.16;sphere.height=.32;sphere.radial_segments=8;sphere.rings=4;mesh=sphere
	_meshes[kind]=mesh
	return mesh

func _make_entity(e: Dictionary) -> Node3D:
	var node := Node3D.new();node.name=e.id
	node.set_meta("entity_id",e.id);node.set_meta("generation",int(e.generation));node.set_meta("kind",e.kind)
	node.set_meta("team",e.team);node.set_meta("owner_id",e.owner_id);node.set_meta("diagnostic_geometry",true)
	var body := MeshInstance3D.new();body.name="Body";body.mesh=_mesh(e.kind);body.material_override=_material(e.team)
	body.position.y=.9 if e.kind=="actor" else .625 if e.kind in ["minion","neutral"] else 1.5 if e.kind=="structure" else 0
	if e.kind=="projectile": body.rotation.x=PI/2
	node.add_child(body)
	var aim := Node3D.new();aim.name="Aim";aim.position.y=1.2 if e.kind=="actor" else .85 if e.kind in ["minion","neutral"] else 0
	node.add_child(aim)
	if e.kind in ["actor","minion","neutral"]:
		var marker := MeshInstance3D.new();marker.name="Direction";marker.mesh=_mesh("aim");marker.material_override=_material(e.team)
		marker.rotation.x=PI/2;marker.position.z=.4;aim.add_child(marker)
	return node

func _expire_events(tick: int) -> void:
	_presentation_tick=maxi(_presentation_tick,tick)
	for seq in _event_views.keys():
		var node: Node3D=_event_views[seq]
		if _presentation_tick-int(node.get_meta("tick"))>=EVENT_LIFETIME_TICKS:
			_free_view(node);_event_views.erase(seq)

func _present_event(e: Dictionary) -> void:
	# Detached world marker; never attach an unversioned historic actor ID to a new lifetime.
	if _presentation_tick-int(e.tick)>=EVENT_LIFETIME_TICKS: return
	if _event_views.size()>=MAX_EVENT_VIEWS:
		var oldest: Variant=_event_views.keys()[0]
		_free_view(_event_views[oldest]);_event_views.erase(oldest);_counts.events_evicted+=1
	var node := Node3D.new();node.name="Receipt_%d"%int(e.seq)
	node.position=Vector3(e.position[0],e.position[1],e.position[2])
	for key in ["seq","tick","kind","actor_id","target_id","amount","epoch"]: node.set_meta(key,e[key])
	var marker := MeshInstance3D.new();marker.mesh=_mesh("event");marker.material_override=_material("neutral");node.add_child(marker)
	_event_root.add_child(node);_event_views[int(e.seq)]=node;_counts.events_presented+=1

func load_replay(header: Variant, records: Variant) -> Dictionary:
	if not _catalog_status.ok: return _catalog_status.duplicate(true)
	var valid: Dictionary=_guard.validate_replay(header,records)
	if not valid.ok: return valid
	var prepared := _replay_guard(header,records,0)
	if not prepared.result.ok: return prepared.result
	# Commit only after the entire replay validated, including records beyond initial seek.
	_clear_views()
	_replay_header=header.duplicate(true);_replay_records=records.duplicate(true);_replay_cursor=0
	_guard=prepared.guard;_state="replay"
	return _result(true,"REPLAY_READY_NOT_SIMULATED")

func _replay_guard(header: Dictionary, records: Array, count_: int) -> Dictionary:
	var candidate := Contracts.new()
	var loaded: Dictionary=candidate.load_catalog()
	if not loaded.ok: return {"result":loaded}
	var admitted: Dictionary=candidate.open_session(header.descriptor.profile_id,header.descriptor,{"room":header.room,"epoch":header.epoch,"identity":header.identity})
	if not admitted.ok: return {"result":admitted}
	var events: Array=[]
	var tick := -1
	for i in count_:
		var record: Dictionary=records[i]
		var before_entities: Dictionary=candidate.report().entities if record.kind=="snapshot" else {}
		var accepted: Dictionary=candidate.call("accept_"+record.kind,record.value)
		if not accepted.ok: return {"result":accepted}
		if record.kind in ["event","snapshot"]: tick=maxi(tick,int(record.value.tick))
		if record.kind=="snapshot":
			var current: Dictionary=candidate.report().entities
			for j in range(events.size()-1,-1,-1):
				var receipt: Dictionary=events[j]
				var changed := false
				for id in [receipt.actor_id,receipt.target_id]:
					if current.has(id)!=before_entities.has(id): changed=true
					elif current.has(id) and (current[id].generation!=before_entities[id].generation or current[id].discontinuity!=before_entities[id].discontinuity): changed=true
				if changed: events.remove_at(j)
		if record.kind=="event":
			events.append(record.value.duplicate(true))
			if events.size()>MAX_EVENT_VIEWS: events.pop_front()
	return {"result":_result(true),"guard":candidate,"events":events,"tick":tick}

func seek_replay(record_count: Variant) -> Dictionary:
	if _state!="replay": return _result(false,"NOT_REPLAY")
	if not Contracts._integer(record_count,0,_replay_records.size()): return _result(false,"REPLAY_CURSOR")
	var prepared := _replay_guard(_replay_header,_replay_records,int(record_count))
	if not prepared.result.ok: return prepared.result
	_clear_views();_guard=prepared.guard
	_sync_entities(_guard.report().entities)
	_expire_events(prepared.tick)
	for e in prepared.events: _present_event(e)
	_replay_cursor=int(record_count)
	return _result(true)

func entity_node(id: String) -> Node3D:
	return _views.get(id)

func report() -> Dictionary:
	var entities := {}
	for id in _views:
		var node: Node3D=_views[id]
		var direction: Vector3=(node.basis*node.get_node("Aim").basis).z
		entities[id]={"generation":node.get_meta("generation"),"kind":node.get_meta("kind"),"team":node.get_meta("team"),"owner_id":node.get_meta("owner_id"),"position":[node.position.x,node.position.y,node.position.z],"aim":[direction.x,direction.y,direction.z],"pitch":node.get_meta("pitch"),"discontinuity":node.get_meta("discontinuity"),"alive":node.get_meta("alive"),"ack_input":node.get_meta("ack_input"),"history_reset_count":node.get_meta("history_reset_count",0)}
	var events := []
	for seq in _event_views:
		var node: Node3D=_event_views[seq]
		events.append({"seq":seq,"tick":node.get_meta("tick"),"kind":node.get_meta("kind"),"epoch":node.get_meta("epoch"),"position":[node.position.x,node.position.y,node.position.z]})
	var pose_entities := entities.duplicate(true)
	for e in pose_entities.values(): e.erase("history_reset_count")
	var protocol: Dictionary=_guard.report()
	return {"state":_state,"session":protocol.session,"last_input_seq":protocol.last_input_seq,"last_ack":protocol.last_ack,"last_event_seq":protocol.last_event_seq,"last_snapshot_tick":protocol.last_snapshot_tick,"presentation_tick":_presentation_tick,"entities":entities,"events":events,"entity_count":_views.size(),"event_count":_event_views.size(),"counts":_counts.duplicate(true),"pose_digest":JSON.stringify({"entities":pose_entities,"events":events},"",true).sha256_text(),"mesh_resources":_meshes.size(),"material_resources":_materials.size(),"replay_cursor":_replay_cursor,"network_connected":false,"diagnostic_geometry":true}
