extends Node
## Protocol-2 authoritative arena transport. Reconnect credentials remain in memory.
signal state_changed(state: String)
signal welcomed(identity: Dictionary)
signal snapshot_received(snapshot: Dictionary)
signal command_result(result: Dictionary)
signal protocol_fault(code: String)
signal disconnected(code: int)
signal match_finished(result: Dictionary)

const PROTOCOL := 2
const MAX_SAFE_INTEGER := 9007199254740991
const MAX_PACKET_BYTES := 524288
const MIN_SNAPSHOT_INTERVAL_SECONDS := 0.000001
const MAX_MATCH_DURATION_SECONDS := 4800.0
const MAX_ABS_YAW := TAU
const COLLECTION_LIMITS := {"actors": 96, "neutrals": 32, "goldShards": 48, "structures": 32, "projectiles": 192, "zones": 32, "pickups": 32, "events": 64}
const REQUIRED_NUMBERS := {
	"actors": ["y", "yaw", "health", "maxHealth", "shield", "respawn", "fireCooldown", "credits", "level", "kills", "deaths", "assists", "damageDealt"],
	"neutrals": ["y", "yaw", "health", "maxHealth", "respawnAt", "slow"], "goldShards": ["y", "value", "createdAt", "expiresAt"],
	"structures": ["health", "maxHealth"], "projectiles": ["y", "vx", "vy", "vz", "damage", "radius", "life"],
	"zones": ["radius", "life", "duration", "power"], "pickups": ["readyAt"], "events": ["time"]}
var state := "disconnected"
var identity := ""
var room := ""
var last_tick := -1
var sent_sequence := -1
var rejected_packets := 0
var stale_snapshots := 0
var received_snapshots := 0
var _peer: WebSocketPeer
var _endpoint := ""
var _hero := ""
var _name := ""
var _token := ""
var _snapshot: Dictionary = {}
var _previous: Dictionary = {}
var _pending: Dictionary = {}
var _command_sequence := 0
var _last_input_msec := -50
var _last_command_msec := -50
var _connection_started := 0
var _manual_close := false
var _consecutive_invalid := 0
var _finish_emitted := false

func connect_arena(endpoint: String, hero_id: String, player_name: String, room_code := "") -> Error:
	if not endpoint.begins_with("ws://") and not endpoint.begins_with("wss://"):
		return ERR_INVALID_PARAMETER
	if "@" in endpoint or player_name.length() < 1 or player_name.length() > 24 or not _matches(hero_id, "^[a-z0-9_-]{1,32}$"):
		return ERR_INVALID_PARAMETER
	if not room_code.is_empty() and not _matches(room_code, "^[A-Z0-9-]{3,16}$"):
		return ERR_INVALID_PARAMETER
	disconnect_arena()
	_endpoint = endpoint
	_hero = hero_id
	_name = player_name
	room = room_code
	return _open_transport()

func reconnect_arena() -> Error:
	if not can_reconnect() or _endpoint.is_empty():
		return ERR_UNCONFIGURED
	_close_transport()
	_cancel_pending("TRANSPORT_RESET")
	_snapshot = {}
	_previous = {}
	last_tick = -1
	return _open_transport()

func disconnect_arena() -> void:
	_close_transport()
	_cancel_pending("DISCONNECTED")
	_token = ""
	identity = ""
	room = ""
	_endpoint = ""
	_hero = ""
	_name = ""
	_snapshot = {}
	_previous = {}
	last_tick = -1
	sent_sequence = -1
	_command_sequence = 0
	_set_state("disconnected")

func can_reconnect() -> bool:
	return not _token.is_empty() and not room.is_empty()

func get_snapshot() -> Dictionary:
	return _snapshot.duplicate(true)

func get_previous_snapshot() -> Dictionary:
	return _previous.duplicate(true)

func pending_command_count() -> int:
	return _pending.size()

func send_input(move: Vector2, yaw: float, pitch: float, fire: bool, jump: bool) -> bool:
	if state != "playing" or not move.is_finite() or not is_finite(yaw) or not is_finite(pitch):
		return false
	var now := Time.get_ticks_msec()
	if now - _last_input_msec < 50 or sent_sequence >= MAX_SAFE_INTEGER:
		return false
	var bounded := move.limit_length(1.0)
	var sequence := sent_sequence + 1
	if not _send({"type": "input", "seq": sequence, "moveX": bounded.x, "moveZ": bounded.y, "yaw": wrapf(yaw, -PI, PI), "pitch": clampf(pitch, -1.35, 1.35), "fire": fire, "jump": jump}):
		return false
	sent_sequence = sequence
	_last_input_msec = now
	return true

func send_ability(slot: int) -> String:
	return _send_command({"type": "command", "action": "ability", "slot": slot}) if slot >= 0 and slot <= 2 else ""

func send_upgrade(upgrade: String) -> String:
	return _send_command({"type": "command", "action": "upgrade", "upgrade": upgrade}) if upgrade in ["power", "vitality", "tempo"] else ""

func _open_transport() -> Error:
	_peer = WebSocketPeer.new()
	_peer.inbound_buffer_size = MAX_PACKET_BYTES * 2
	_peer.outbound_buffer_size = 8192
	_peer.max_queued_packets = 32
	_manual_close = false
	_consecutive_invalid = 0
	_finish_emitted = false
	_connection_started = Time.get_ticks_msec()
	_last_input_msec = -50
	_last_command_msec = -50
	var error := _peer.connect_to_url(_endpoint)
	_set_state("connecting" if error == OK else "disconnected")
	return error

func _close_transport() -> void:
	_manual_close = true
	if _peer and _peer.get_ready_state() in [WebSocketPeer.STATE_OPEN, WebSocketPeer.STATE_CONNECTING]:
		_peer.close(1000, "Leaving arena")

func _exit_tree() -> void:
	disconnect_arena()
	_peer = null

func _process(_delta: float) -> void:
	if not _peer:
		return
	_peer.poll()
	var ready := _peer.get_ready_state()
	if ready == WebSocketPeer.STATE_OPEN and state == "connecting":
		var join := {"type": "join", "protocol": PROTOCOL, "heroId": _hero, "name": _name}
		if not room.is_empty(): join.room = room
		if not _token.is_empty(): join.token = _token
		if _send(join): _set_state("joining")
	elif ready == WebSocketPeer.STATE_CLOSED:
		if state != "disconnected":
			_cancel_pending("TRANSPORT_CLOSED")
			_set_state("disconnected")
			disconnected.emit(_peer.get_close_code())
		_peer = null
		return
	if _manual_close:
		return
	if state in ["connecting", "joining"] and Time.get_ticks_msec() - _connection_started > 8000:
		_abort("CONNECTION_TIMEOUT")
		return
	for _index in mini(_peer.get_available_packet_count(), 16):
		var packet := _peer.get_packet()
		if not _peer.was_string_packet() or packet.size() > MAX_PACKET_BYTES:
			_reject("INVALID_PACKET")
		else:
			var parser := JSON.new()
			if parser.parse(packet.get_string_from_utf8()) != OK: _reject("INVALID_JSON")
			else: _handle_message(parser.data)
		if _manual_close: break
	for command_id in _pending.keys():
		if Time.get_ticks_msec() - int(_pending[command_id]) > 4000:
			_pending.erase(command_id)
			command_result.emit({"type": "result", "id": command_id, "ok": false, "code": "CLIENT_TIMEOUT"})

func _send(message: Dictionary) -> bool:
	return _peer != null and _peer.get_ready_state() == WebSocketPeer.STATE_OPEN and _peer.send_text(JSON.stringify(message)) == OK

func _send_command(message: Dictionary) -> String:
	var now := Time.get_ticks_msec()
	if state != "playing" or _pending.size() >= 32 or now - _last_command_msec < 50:
		return ""
	_command_sequence += 1
	var command_id := "native_%d" % _command_sequence
	message.id = command_id
	if not _send(message): return ""
	_pending[command_id] = now
	_last_command_msec = now
	return command_id

func _cancel_pending(code: String) -> void:
	var ids := _pending.keys()
	_pending.clear()
	for command_id in ids:
		command_result.emit({"type": "result", "id": command_id, "ok": false, "code": code})

func _handle_message(message: Variant) -> void:
	if not message is Dictionary or not _finite_tree(message):
		_reject("INVALID_MESSAGE")
		return
	match message.get("type"):
		"welcome":
			if state != "joining" or message.get("protocol") != PROTOCOL or not _identifier(message.get("id")) or not message.get("token") is String or not _matches(message.token, "^[a-f0-9]{48}$") or not message.get("room") is String or not _matches(message.room, "^[A-Z0-9-]{3,16}$"):
				_reject("INVALID_WELCOME")
				return
			if not identity.is_empty() and identity != message.id or not room.is_empty() and room != message.room:
				_reject("IDENTITY_MISMATCH")
				return
			if not _valid_snapshot(message.get("snapshot"), message.room) or not _has_local_actor(message.snapshot, message.id):
				_reject("INVALID_WELCOME_SNAPSHOT")
				return
			identity = message.id
			room = message.room
			_token = message.token
			_set_state("playing")
			_accept_snapshot(message.snapshot)
			welcomed.emit({"id": identity, "room": room, "protocol": PROTOCOL})
		"snapshot":
			if state not in ["playing", "finished"] or not _valid_snapshot(message.get("snapshot"), room) or not _has_local_actor(message.snapshot, identity):
				_reject("INVALID_SNAPSHOT")
				return
			if int(message.snapshot.tick) <= last_tick:
				stale_snapshots += 1
				return
			if not _snapshot.is_empty():
				var interval := float(message.snapshot.time) - float(_snapshot.time)
				if interval < 0.0 or state == "finished" and message.snapshot.phase != "finished":
					_reject("TIME_OR_PHASE_REGRESSION")
					return
				if interval > 0.0 and interval < MIN_SNAPSHOT_INTERVAL_SECONDS and message.snapshot.phase != "finished":
					_reject("UNUSABLE_TIME_INTERVAL")
					return
			_accept_snapshot(message.snapshot)
		"result":
			if not _identifier(message.get("id")) or not message.get("ok") is bool or not message.get("code") is String:
				_reject("INVALID_RESULT")
				return
			if _pending.has(message.id):
				_pending.erase(message.id)
				command_result.emit(message.duplicate(true))
		"error":
			if not message.get("message") is String:
				_reject("INVALID_ERROR")
				return
			protocol_fault.emit("SERVER_REJECTED_REQUEST")
			if state == "joining": _abort("JOIN_REJECTED")
		_: _reject("UNKNOWN_MESSAGE")

func _accept_snapshot(snapshot: Dictionary) -> void:
	_previous = _snapshot
	_snapshot = snapshot.duplicate(true)
	last_tick = int(snapshot.tick)
	received_snapshots += 1
	_consecutive_invalid = 0
	for actor in snapshot.actors:
		if actor.id == identity: sent_sequence = maxi(sent_sequence, int(actor.lastInputSeq))
	snapshot_received.emit(_snapshot.duplicate(true))
	if snapshot.phase == "finished" and not _finish_emitted:
		_finish_emitted = true
		_set_state("finished")
		_cancel_pending("MATCH_FINISHED")
		match_finished.emit({"winner": snapshot.winner, "reason": snapshot.reason, "scores": snapshot.scores.duplicate(true)})

func _reject(code: String) -> void:
	rejected_packets += 1
	_consecutive_invalid += 1
	protocol_fault.emit(code)
	if _consecutive_invalid >= 5: _abort("TOO_MANY_INVALID_MESSAGES")

func _abort(code: String) -> void:
	protocol_fault.emit(code)
	_close_transport()
	_cancel_pending(code)
	_set_state("disconnected")
	disconnected.emit(1008)

func _set_state(value: String) -> void:
	if state != value:
		state = value
		state_changed.emit(value)

func _matches(value: String, expression: String) -> bool:
	var regex := RegEx.new()
	return regex.compile(expression) == OK and regex.search(value) != null

func _identifier(value: Variant) -> bool:
	return value is String and _matches(value, "^[A-Za-z0-9_-]{1,64}$")

func _number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))

func _integer(value: Variant, minimum := 0) -> bool:
	return _number(value) and float(value) >= minimum and float(value) <= MAX_SAFE_INTEGER and floor(float(value)) == float(value)

func _finite_tree(value: Variant, depth := 0) -> bool:
	if depth > 12: return false
	if value is float or value is int: return is_finite(float(value))
	if value is String: return value.length() <= 256
	if value is Array:
		if value.size() > 1024: return false
		for item in value:
			if not _finite_tree(item, depth + 1): return false
	elif value is Dictionary:
		if value.size() > 64: return false
		for key in value:
			if not key is String or key.length() > 64 or not _finite_tree(value[key], depth + 1): return false
	return value == null or value is bool or value is String or value is Array or value is Dictionary

func _has_local_actor(snapshot: Dictionary, actor_id: String) -> bool:
	for actor in snapshot.actors:
		if actor.id == actor_id and actor.kind == "hero" and actor.connected and not actor.bot: return true
	return false

func _valid_snapshot(value: Variant, expected_room: String) -> bool:
	if not value is Dictionary or value.get("protocol") != PROTOCOL or value.get("room") != expected_room: return false
	if not _integer(value.get("tick")) or not _number(value.get("time")) or float(value.time) < 0 or not _number(value.get("duration")) or float(value.duration) <= 0 or float(value.duration) > MAX_MATCH_DURATION_SECONDS or float(value.time) > float(value.duration) + 0.1 or not _integer(value.get("seed")): return false
	if float(value.time) > 0.0 and float(value.time) < MIN_SNAPSHOT_INTERVAL_SECONDS: return false
	if value.get("phase") not in ["playing", "finished"] or value.get("winner") not in [null, "sun", "moon", "draw"] or not value.get("reason") is String: return false
	if value.phase == "playing" and value.winner != null or value.phase == "finished" and value.winner == null: return false
	if not value.get("scores") is Dictionary or not _number(value.scores.get("sun")) or not _number(value.scores.get("moon")): return false
	for collection in COLLECTION_LIMITS:
		var entries: Variant = value.get(collection)
		if not entries is Array or entries.size() > COLLECTION_LIMITS[collection]: return false
		var ids := {}
		for entry in entries:
			if not entry is Dictionary or not _number(entry.get("x")) or not _number(entry.get("z")): return false
			if absf(float(entry.x)) > 10000 or absf(float(entry.z)) > 10000: return false
			for field in REQUIRED_NUMBERS[collection]:
				if not _number(entry.get(field)): return false
			if entry.has("y") and (not _number(entry.y) or absf(float(entry.y)) > 10000): return false
			if entry.has("yaw") and (not _number(entry.yaw) or absf(float(entry.yaw)) > MAX_ABS_YAW): return false
			if collection == "events":
				if not _integer(entry.get("id")): return false
			elif not _identifier(entry.get("id")): return false
			if ids.has(entry.id): return false
			ids[entry.id] = true
			if not _valid_entity(entry, collection): return false
	return _finite_tree(value)

func _valid_entity(entry: Dictionary, collection: String) -> bool:
	match collection:
		"actors":
			if entry.get("kind") not in ["hero", "minion"] or entry.get("team") not in ["sun", "moon"] or not entry.get("connected") is bool or not entry.get("bot") is bool or not _identifier(entry.get("heroId")) or not _integer(entry.get("lastInputSeq"), -1) or not entry.get("name") is String or not _integer(entry.get("lane")) or float(entry.lane) > 2: return false
			if not entry.get("cooldowns") is Array or entry.cooldowns.size() != 3 or not entry.get("upgrades") is Dictionary or not entry.get("effects") is Dictionary: return false
			for cooldown in entry.cooldowns:
				if not _number(cooldown) or float(cooldown) < 0: return false
			for upgrade in ["power", "vitality", "tempo"]:
				if not _integer(entry.upgrades.get(upgrade)) or float(entry.upgrades[upgrade]) > 3: return false
			for effect in ["haste", "slow", "ward"]:
				if not _number(entry.effects.get(effect)): return false
		"neutrals":
			if entry.get("kind") != "neutral" or entry.get("team") != "neutral" or entry.get("species") not in ["yaksha", "naga", "sky-sentinel"] or entry.get("state") not in ["idle", "aggro", "returning", "dead"]: return false
		"structures":
			if entry.get("kind") not in ["tower", "core"] or entry.get("team") not in ["sun", "moon"] or not _integer(entry.get("lane")) or float(entry.lane) > 2 or not entry.get("shielded") is bool: return false
		"goldShards":
			if not _identifier(entry.get("sourceId")) or entry.get("originTeam") not in ["sun", "moon"]: return false
		"projectiles", "zones":
			if not _identifier(entry.get("owner")) or entry.get("team") not in ["sun", "moon", "neutral"] or not entry.get("color") is String: return false
			if collection == "zones" and entry.get("kind") not in ["bolt", "burst", "dash", "heal", "ward", "nova", "slow", "line", "leap", "summon", "pull", "cone"]: return false
		"pickups":
			if entry.get("kind") not in ["vigor", "haste", "ward"]: return false
		"events":
			var valid_actor: bool = _identifier(entry.get("actorId")) or entry.get("type") == "victory" and entry.get("actorId") == ""
			if not valid_actor or entry.get("team") not in ["sun", "moon", "neutral"] or not entry.get("label") is String or not entry.get("color") is String or entry.get("type") not in ["shot", "hit", "ability", "defeat", "tower", "core", "pickup", "upgrade", "victory", "gold", "camp", "buff"]: return false
	return true
