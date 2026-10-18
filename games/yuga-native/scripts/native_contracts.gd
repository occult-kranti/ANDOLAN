extends RefCounted
## FG00-T04 pure admission/replay validator. This is not a transport or authority.
const CATALOG_PATH := "res://assets/contracts/native-contracts-v1.json"
const MAX_SAFE := 9007199254740991
const PROFILE_IDS := ["browser-p2-3v3", "native-offline-triad", "production-6v6"]
const CONTENT_REVISIONS := {"browser-p2-3v3":1,"native-offline-triad":8,"production-6v6":1}
const ENTITY_CAPS := {"actor":12,"minion":96,"neutral":32,"structure":32,"projectile":192,"zone":128,"pickup":32,"gold_shard":96}
const EVENT_KINDS := ["spawn","despawn","shot","hit","defeat","objective","reward","match_end"]
const DESCRIPTOR_KEYS := ["contract_id","profile_id","versions","protocol","rules_sha256","map_id","map_sha256","content_sha256"]
const EXPECTED_LIMITS := {"safe_integer":9007199254740991,"packet_bytes":524288,"input_bytes":2048,"entities":640,"entity_history":4096,"events_per_tick":128,"replay_records":100000,"position_abs":10000,"pitch_abs":1.35,"input_gap":4096,"snapshot_tick_gap":200,"input_stale_seconds":0.35}
const VERSION_KEYS := ["contract","rules","map","content","replay","input","event","entity"]
var _catalog: Dictionary = {}
var _session: Dictionary = {}
var _input_seq := -1
var _event_seq := -1
var _event_tick := -1
var _events_this_tick := 0
var _snapshot_tick := -1
var _ack := -1
var _entities: Dictionary = {}
var _history: Dictionary = {}

static func _result(ok: bool, code := "OK", details: Dictionary = {}) -> Dictionary:
	return {"ok":ok,"code":code,"details":details}

static func _text(v: Variant, expected: String) -> bool:
	return v is String and v==expected

static func _choice(v: Variant, choices: Array) -> bool:
	return v is String and v in choices

static func _number(v: Variant) -> bool:
	return (v is int or v is float) and is_finite(float(v))

static func _integer(v: Variant, minimum: int = 0, maximum: int = MAX_SAFE) -> bool:
	return _number(v) and float(v)>=minimum and float(v)<=maximum and floor(float(v))==float(v)

static func _id(v: Variant, maximum := 64) -> bool:
	if not v is String or v.is_empty() or v.length()>maximum: return false
	for c in v:
		if not (c>="a" and c<="z" or c>="A" and c<="Z" or c>="0" and c<="9" or c in ["-","_","."]): return false
	return true

static func _hash(v: Variant) -> bool:
	if not v is String or v.length()!=64: return false
	for c in v:
		if not (c>="a" and c<="f" or c>="0" and c<="9"): return false
	return true

static func _keys(v: Variant, expected: Array) -> bool:
	if not v is Dictionary or v.size()!=expected.size(): return false
	for k in expected:
		if not v.has(k): return false
	return true

static func _vector(v: Variant, size_: int, bound: float) -> bool:
	if not v is Array or v.size()!=size_: return false
	for x in v:
		if not _number(x) or absf(float(x))>bound: return false
	return true

static func _size_xz(value: Variant, width: float, depth: float) -> bool:
	return _vector(value,2,10000) and float(value[0])==width and float(value[1])==depth

static func validate_catalog(data: Variant) -> Dictionary:
	if not data is Dictionary or not _integer(data.get("schema_version"),1,1) or not _text(data.get("contract_id"),"yuga-native-contracts-v1"): return _result(false,"CATALOG_VERSION")
	if not data.get("profiles") is Array or data.profiles.size()!=3: return _result(false,"CATALOG_PROFILES")
	if not _keys(data.get("envelope_versions"),VERSION_KEYS): return _result(false,"CATALOG_VERSIONS")
	for v in data.envelope_versions.values():
		if not _integer(v,1,1): return _result(false,"CATALOG_VERSIONS")
	if not _keys(data.get("limits"),EXPECTED_LIMITS.keys()): return _result(false,"CATALOG_LIMITS")
	for key in EXPECTED_LIMITS:
		if not _number(data.limits[key]) or float(data.limits[key])!=float(EXPECTED_LIMITS[key]): return _result(false,"CATALOG_LIMITS")
	var coords: Variant=data.get("coordinate_contract")
	if not coords is Dictionary or not _text(coords.get("units"),"metres") or not _text(coords.get("up"),"+Y") or not _text(coords.get("forward"),"+Z") or not _text(coords.get("position"),"feet_origin") or not _text(coords.get("wire_vectors"),"arrays_xyz"): return _result(false,"COORDINATE_CONTRACT")
	if not _keys(coords.get("collision_layers"),["world","actor","target"]) or not _integer(coords.collision_layers.world,1,1) or not _integer(coords.collision_layers.actor,2,2) or not _integer(coords.collision_layers.target,4,4): return _result(false,"COLLISION_LAYERS")
	var found := {}
	for p in data.profiles:
		if not p is Dictionary or not _choice(p.get("id"),PROFILE_IDS) or found.has(p.id): return _result(false,"CATALOG_PROFILE")
		found[p.id]=true
		if not _integer(p.get("content_revision"),CONTENT_REVISIONS[p.id],CONTENT_REVISIONS[p.id]): return _result(false,"CATALOG_CONTENT_REVISION")
		if not p.get("live_handshake") is bool or p.live_handshake or not _hash(p.get("map_sha256")) or not _hash(p.get("content_sha256")) or not _id(p.get("map_id")): return _result(false,"CATALOG_IDENTITY")
		if not p.get("content_sources") is Dictionary or p.content_sources.is_empty() or p.content_sources.size()>32: return _result(false,"CATALOG_CONTENT")
		for path in p.content_sources:
			if not path is String or path.length()>256 or path.begins_with("/") or ".." in path or not _hash(p.content_sources[path]): return _result(false,"CATALOG_CONTENT")
		if JSON.stringify(p.content_sources,"",true).sha256_text()!=p.content_sha256: return _result(false,"CONTENT_DIGEST")
		match p.id:
			"browser-p2-3v3":
				if not _integer(p.get("protocol"),2,2) or not _integer(p.get("team_size"),3,3) or not _integer(p.get("duration_seconds"),480,480) or not _size_xz(p.get("map_size_xz"),140,170) or not _text(p.get("state"),"observed"): return _result(false,"BROWSER_RULES")
			"native-offline-triad":
				if not _integer(p.get("protocol"),0,0) or not _integer(p.get("team_size"),0,0) or not _integer(p.get("duration_seconds"),0,0) or not _size_xz(p.get("map_size_xz"),140,260) or not _text(p.get("state"),"implemented_offline"): return _result(false,"OFFLINE_RULES")
			"production-6v6":
				if not _integer(p.get("protocol"),0,0) or not _integer(p.get("team_size"),6,6) or not _integer(p.get("duration_seconds"),1080,1080) or not _text(p.get("state"),"proposed") or not p.get("map_size_xz") is Array or not p.map_size_xz.is_empty() or not _integer(p.get("simulation_hz"),0,0) or not _text(p.get("map_digest_scope"),"design_document_not_collision_geometry"): return _result(false,"PRODUCTION_RULES")
		var offline: bool=p.id=="native-offline-triad"
		var browser: bool=p.id=="browser-p2-3v3"
		var mask_: int=511 if offline else 3
		var hz_: int=60 if offline else 20 if browser else 0
		var authority_: String="godot_local_60hz_army20_relay10" if offline else "node_typescript_20hz" if browser else "unselected_FG05-T02"
		if not _integer(p.get("buttons_mask"),mask_,mask_) or not _integer(p.get("simulation_hz"),hz_,hz_) or not _text(p.get("authority"),authority_): return _result(false,"PROFILE_SEMANTICS")
		if not _keys(p.get("features"),["relays","flight","grapple","hero_health"]): return _result(false,"PROFILE_FEATURES")
		for key in p.features:
			if not p.features[key] is bool or p.features[key]!=(true if key=="hero_health" else offline): return _result(false,"PROFILE_FEATURES")
	return _result(true)

func load_catalog(path: String = CATALOG_PATH) -> Dictionary:
	if not _session.is_empty(): return _result(false,"SESSION_ACTIVE")
	if not FileAccess.file_exists(path): return _result(false,"CATALOG_MISSING")
	var file := FileAccess.open(path,FileAccess.READ)
	if file==null or file.get_length()>65536: return _result(false,"CATALOG_SIZE")
	var data: Variant = JSON.parse_string(file.get_as_text())
	var valid := validate_catalog(data)
	if valid.ok: _catalog=data.duplicate(true)
	return valid

func profile(id: String) -> Dictionary:
	for p in _catalog.get("profiles",[]):
		if p.id==id: return p.duplicate(true)
	return {}

func descriptor(id: String) -> Dictionary:
	var p := profile(id)
	if p.is_empty(): return {}
	var versions: Dictionary=_catalog.envelope_versions.duplicate(true)
	versions.content=int(p.content_revision)
	return {"contract_id":_catalog.contract_id,"profile_id":p.id,"versions":versions,"protocol":p.protocol,"rules_sha256":JSON.stringify({"profile":p,"coordinates":_catalog.coordinate_contract,"limits":_catalog.limits},"",true).sha256_text(),"map_id":p.map_id,"map_sha256":p.map_sha256,"content_sha256":p.content_sha256}

static func validate_descriptor(value: Variant) -> Dictionary:
	if not _keys(value,DESCRIPTOR_KEYS) or not _text(value.get("contract_id"),"yuga-native-contracts-v1") or not _choice(value.get("profile_id"),PROFILE_IDS): return _result(false,"DESCRIPTOR_SCHEMA")
	if not _keys(value.versions,VERSION_KEYS) or not _integer(value.protocol,0,65535) or not _hash(value.rules_sha256) or not _id(value.map_id) or not _hash(value.map_sha256) or not _hash(value.content_sha256): return _result(false,"DESCRIPTOR_FIELDS")
	for v in value.versions.values():
		if not _integer(v,1,65535): return _result(false,"DESCRIPTOR_VERSION")
	return _result(true)

static func compatibility(local: Variant, remote: Variant) -> Dictionary:
	if not validate_descriptor(local).ok or not validate_descriptor(remote).ok: return _result(false,"INVALID_DESCRIPTOR")
	for k in DESCRIPTOR_KEYS:
		if k=="versions":
			for v in VERSION_KEYS:
				if int(local.versions[v])!=int(remote.versions[v]): return _result(false,"MISMATCH_VERSIONS",{"field":v,"action":"reject_before_world_admission"})
		elif local[k]!=remote[k]: return _result(false,"MISMATCH_"+str(k).to_upper(),{"field":k,"action":"reject_before_world_admission"})
	return _result(true,"EXACT_MATCH",{"network_adoption":false})

static func _valid_scope(scope: Variant) -> bool:
	return _keys(scope,["room","epoch","identity"]) and _id(scope.room,16) and _integer(scope.epoch,1) and _id(scope.identity)

func open_session(profile_id: String, remote: Variant, scope: Variant) -> Dictionary:
	if not _session.is_empty(): return _result(false,"SESSION_ACTIVE")
	var checked := compatibility(descriptor(profile_id),remote)
	if not checked.ok: return checked
	if not _valid_scope(scope): return _result(false,"INVALID_SCOPE")
	_session={"descriptor":descriptor(profile_id),"scope":scope.duplicate(true)}
	return _result(true,"VALIDATOR_SESSION_OPEN",{"transport_connected":false})

func resume_session(remote: Variant, scope: Variant) -> Dictionary:
	if _session.is_empty(): return _result(false,"NO_SESSION")
	var checked := compatibility(_session.descriptor,remote)
	if not checked.ok: return checked
	if not _valid_scope(scope) or scope.room!=_session.scope.room or scope.identity!=_session.scope.identity or scope.epoch!=_session.scope.epoch: return _result(false,"RESUME_SCOPE_MISMATCH")
	return _result(true,"RESUMED",{"last_input_seq":_input_seq,"last_ack":_ack,"last_event_seq":_event_seq,"snapshot_tick":_snapshot_tick})

func migrate_session(profile_id: String, remote: Variant, scope: Variant) -> Dictionary:
	# Explicit deployment/rollback transition; never an in-match downgrade.
	if _session.is_empty(): return _result(false,"NO_SESSION")
	var checked := compatibility(descriptor(profile_id),remote)
	if not checked.ok: return checked
	if not _valid_scope(scope) or scope.room!=_session.scope.room or scope.identity!=_session.scope.identity or scope.epoch<=_session.scope.epoch: return _result(false,"MIGRATION_REQUIRES_NEW_EPOCH")
	reset()
	return open_session(profile_id,remote,scope)

func reset() -> void:
	_session.clear()
	_input_seq=-1
	_event_seq=-1
	_event_tick=-1
	_events_this_tick=0
	_snapshot_tick=-1
	_ack=-1
	_entities.clear()
	_history.clear()

func report() -> Dictionary:
	return {"session":_session.duplicate(true),"last_input_seq":_input_seq,"last_event_seq":_event_seq,"last_event_tick":_event_tick,"events_this_tick":_events_this_tick,"last_snapshot_tick":_snapshot_tick,"last_ack":_ack,"entities":_entities.duplicate(true),"entity_history":_history.duplicate(true),"network_connected":false}

func _envelope(value: Variant, version_key: String) -> Dictionary:
	if _session.is_empty(): return _result(false,"NO_SESSION")
	if not value is Dictionary or not _integer(value.get("version"),1) or value.get("version")!=_session.descriptor.versions[version_key]: return _result(false,"MESSAGE_VERSION")
	if not _integer(value.get("epoch"),1) or not _id(value.get("room"),16) or value.room!=_session.scope.room or value.get("epoch")!=_session.scope.epoch: return _result(false,"STALE_OR_FOREIGN_SCOPE")
	return _result(true)

func accept_input(value: Variant) -> Dictionary:
	var valid := _envelope(value,"input")
	if not valid.ok: return valid
	if not _keys(value,["version","room","epoch","seq","actor_id","move","yaw","pitch","buttons"]): return _result(false,"INPUT_FIELDS")
	if not _id(value.actor_id) or value.actor_id!=_session.scope.identity or not _integer(value.seq) or not _vector(value.move,2,1) or not _number(value.yaw) or absf(value.yaw)>PI or not _number(value.pitch) or absf(value.pitch)>1.35 or not _integer(value.buttons,0,511): return _result(false,"INPUT_VALUE")
	if Vector2(value.move[0],value.move[1]).length_squared()>1.000001: return _result(false,"INPUT_MAGNITUDE")
	var mask: int=profile(_session.descriptor.profile_id).buttons_mask
	if int(value.buttons)&~mask: return _result(false,"UNSUPPORTED_INPUT")
	if value.seq<=_input_seq: return _result(false,"STALE_INPUT")
	if value.seq-_input_seq>4096: return _result(false,"INPUT_GAP_REQUIRES_RESYNC")
	_input_seq=int(value.seq)
	return _result(true)

func accept_event(value: Variant) -> Dictionary:
	var valid := _envelope(value,"event")
	if not valid.ok: return valid
	if not _keys(value,["version","room","epoch","seq","tick","kind","actor_id","target_id","position","amount"]): return _result(false,"EVENT_FIELDS")
	if not _integer(value.seq) or not _integer(value.tick) or not _choice(value.kind,EVENT_KINDS) or not _vector(value.position,3,10000) or not _number(value.amount) or value.amount<0 or value.amount>1000000: return _result(false,"EVENT_VALUE")
	if not _id(value.actor_id) and not (value.kind=="match_end" and _text(value.actor_id,"")): return _result(false,"EVENT_ACTOR")
	if not _text(value.target_id,"") and not _id(value.target_id): return _result(false,"EVENT_TARGET")
	if value.seq!=_event_seq+1: return _result(false,"EVENT_ORDER_REQUIRES_RESYNC")
	if value.tick<_event_tick: return _result(false,"EVENT_TICK_REGRESSION")
	var count_: int=_events_this_tick+1 if value.tick==_event_tick else 1
	if count_>128: return _result(false,"EVENT_BUDGET")
	_event_seq=int(value.seq)
	_event_tick=int(value.tick)
	_events_this_tick=count_
	return _result(true)

static func _valid_entity(e: Variant) -> bool:
	if not _keys(e,["id","generation","kind","team","position","yaw","pitch","discontinuity","alive","ack_input","owner_id"]): return false
	if not _id(e.id) or not _integer(e.generation,1) or not _choice(e.kind,ENTITY_CAPS.keys()) or not _choice(e.team,["sun","moon","neutral"]) or not _vector(e.position,3,10000): return false
	if not _number(e.yaw) or absf(e.yaw)>PI or not _number(e.pitch) or absf(e.pitch)>1.35 or not _integer(e.discontinuity) or not e.alive is bool or not _integer(e.ack_input,-1): return false
	return _text(e.owner_id,"") or _id(e.owner_id)

func accept_snapshot(value: Variant) -> Dictionary:
	var valid := _envelope(value,"entity")
	if not valid.ok: return valid
	if not _keys(value,["version","room","epoch","tick","entities"]): return _result(false,"SNAPSHOT_FIELDS")
	if not _integer(value.tick) or not value.entities is Array or value.entities.size()>640: return _result(false,"SNAPSHOT_VALUE")
	if value.tick<=_snapshot_tick: return _result(false,"STALE_SNAPSHOT")
	if _snapshot_tick>=0 and value.tick-_snapshot_tick>200: return _result(false,"SNAPSHOT_GAP_REQUIRES_RESYNC")
	var next := {}
	var counts := {}
	var next_history := _history.duplicate(true)
	var local_ack := _ack
	for e in value.entities:
		if not _valid_entity(e) or next.has(e.id): return _result(false,"INVALID_OR_DUPLICATE_ENTITY")
		counts[e.kind]=counts.get(e.kind,0)+1
		var cap_: int=ENTITY_CAPS[e.kind]
		if e.kind=="actor":
			var profile_id: String=_session.descriptor.profile_id
			cap_=1 if profile_id=="native-offline-triad" else 6 if profile_id=="browser-p2-3v3" else 12
		if counts[e.kind]>cap_: return _result(false,"ENTITY_KIND_BUDGET")
		if e.id==_session.scope.identity:
			if e.kind!="actor" or e.ack_input<_ack or e.ack_input>_input_seq: return _result(false,"INVALID_INPUT_ACK")
			local_ack=int(e.ack_input)
		if next_history.has(e.id):
			var h: Dictionary=next_history[e.id]
			if e.generation<h.generation or e.generation==h.generation and (not h.active or e.kind!=h.kind or e.owner_id!=h.owner_id or e.team!=h.team): return _result(false,"ENTITY_LIFETIME_REUSE")
			if e.generation==h.generation:
				if e.discontinuity<h.discontinuity: return _result(false,"DISCONTINUITY_REGRESSION")
				if e.alive!=h.alive and e.discontinuity<=h.discontinuity: return _result(false,"LIFECYCLE_NEEDS_DISCONTINUITY")
				if e.discontinuity==h.discontinuity and Vector3(e.position[0]-h.position[0],e.position[1]-h.position[1],e.position[2]-h.position[2]).length()>8: return _result(false,"TELEPORT_NEEDS_DISCONTINUITY")
		next[e.id]=e.duplicate(true)
		next_history[e.id]={"generation":e.generation,"active":true,"kind":e.kind,"owner_id":e.owner_id,"team":e.team,"discontinuity":e.discontinuity,"alive":e.alive,"position":e.position.duplicate()}
	if not next.has(_session.scope.identity): return _result(false,"LOCAL_ENTITY_MISSING")
	if next_history.size()>4096: return _result(false,"ENTITY_HISTORY_REQUIRES_NEW_EPOCH")
	for id in next_history:
		if not next.has(id): next_history[id].active=false
	_entities=next
	_history=next_history
	_snapshot_tick=int(value.tick)
	_ack=local_ack
	return _result(true)

func validate_replay(header: Variant, records: Variant) -> Dictionary:
	if not _keys(header,["format","descriptor","room","epoch","identity","seed","record_count"]) or not _integer(header.format,1,1) or not _integer(header.seed,0,4294967295): return _result(false,"REPLAY_HEADER")
	if not records is Array or not _integer(header.record_count,0,100000) or records.size()!=header.record_count: return _result(false,"REPLAY_SIZE")
	if not validate_descriptor(header.descriptor).ok: return _result(false,"REPLAY_DESCRIPTOR")
	# Independent scratch stream: validation never changes the active session.
	var guard: RefCounted=get_script().new()
	guard._catalog=_catalog.duplicate(true)
	var opened: Dictionary=guard.open_session(header.descriptor.profile_id,header.descriptor,{"room":header.room,"epoch":header.epoch,"identity":header.identity})
	if not opened.ok: return opened
	var index := 0
	for record in records:
		if not _keys(record,["kind","value"]) or not _choice(record.kind,["input","event","snapshot"]): return _result(false,"REPLAY_RECORD",{"index":index})
		var accepted: Dictionary
		match record.kind:
			"input": accepted=guard.accept_input(record.value)
			"event": accepted=guard.accept_event(record.value)
			"snapshot": accepted=guard.accept_snapshot(record.value)
		if not accepted.ok: return _result(false,accepted.code,{"index":index})
		index+=1
	return _result(true,"REPLAY_VALIDATED",{"records":index,"final":guard.report(),"simulation_reexecuted":false})

func parse_packet(bytes: PackedByteArray, channel: String) -> Dictionary:
	# Check bytes before JSON decoding; no resource paths or user objects are loaded.
	if channel not in ["input","event","snapshot"]: return _result(false,"CHANNEL")
	var cap_: int=2048 if channel=="input" else 524288
	if bytes.is_empty() or bytes.size()>cap_: return _result(false,"PACKET_SIZE")
	var parser := JSON.new()
	if parser.parse(bytes.get_string_from_utf8())!=OK: return _result(false,"INVALID_JSON")
	match channel:
		"input": return accept_input(parser.data)
		"event": return accept_event(parser.data)
		"snapshot": return accept_snapshot(parser.data)
	return _result(false,"CHANNEL")
