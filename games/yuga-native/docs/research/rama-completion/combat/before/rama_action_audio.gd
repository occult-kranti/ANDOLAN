extends Node3D
## One bounded presentation subscriber. Kit/vitals receipts alone select onsets.
## No timer, delayed queue, gameplay authority, bus mutation or external samples.
const DEFAULT_DIRECTORY := "res://assets/audio/rama-quality/"
const MAX_VOICES := 4
const WORLD_VOICES := 3
const MAX_CASTS := 12
const MAX_INTEGER := 9007199254740991
const GAIN_DB := -18.0
const IDS := ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"]
const KINDS := ["begin", "release", "impact", "tick", "recovery", "cancel", "end", "reset"]
const NAMES := ["draw_kodanda", "draw_piercing_dawn", "draw_measured_step", "draw_guardian_circle", "draw_dawn_volley", "release_kodanda", "release_piercing_dawn", "release_measured_step", "release_guardian_circle", "release_dawn_volley", "contact", "blocked", "confirm", "threat", "cancel"]
var _streams: Dictionary = {}
var _world: Array[AudioStreamPlayer3D] = []
var _feedback: AudioStreamPlayer
var _errors: Array[String] = []
var _active: Dictionary = {}
var _damage_sources: Dictionary = {}
var _generation := -1
var _last_seq := -1
var _last_cast := 0
var _last_time := -1.0
var _vitals_generation := -1
var _receiver_generation := -1
var _last_damage_time := -1.0
var _volume := .35
var _suspended := false
var _focused := true
var _alive := true
var _serial := 0
var _played := 0
var _suppressed := 0
var _rejected := 0
var _dropped := 0
var _last_confirm_time := -1.0

func _init(directory: String = DEFAULT_DIRECTORY) -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	set_process(true); set_physics_process(false)
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(directory + "manifest.json")) if FileAccess.file_exists(directory + "manifest.json") else null
	if not parsed is Dictionary or not _integer(parsed.get("schema"), 1) or parsed.schema != 1 or not parsed.get("files") is Dictionary or parsed.files.size() != NAMES.size():
		_errors.append("MANIFEST_INVALID")
	else:
		for cue: String in NAMES:
			var path := directory + cue + ".wav"
			var stream: AudioStreamWAV
			if FileAccess.file_exists(path + ".import") and ResourceLoader.exists(path): stream = load(path) as AudioStreamWAV
			elif FileAccess.file_exists(path): stream = AudioStreamWAV.load_from_file(path)
			if stream == null or stream.loop_mode != AudioStreamWAV.LOOP_DISABLED or stream.mix_rate != 48000 or stream.stereo or stream.format != AudioStreamWAV.FORMAT_16_BITS or stream.get_length() <= 0 or stream.get_length() > 1.0:
				_errors.append("STREAM_INVALID:" + cue)
			else: _streams[cue] = stream
	for index in WORLD_VOICES:
		var voice := AudioStreamPlayer3D.new()
		voice.name = "RamaActionWorld%d" % index
		voice.process_mode = Node.PROCESS_MODE_ALWAYS
		voice.max_distance = 36.0
		voice.unit_size = 3.5
		voice.max_db = GAIN_DB
		voice.panning_strength = .65
		voice.attenuation_filter_cutoff_hz = 8500.0
		_init_meta(voice)
		add_child(voice); _world.append(voice)
	_feedback = AudioStreamPlayer.new()
	_feedback.name = "RamaActionFeedback"
	_feedback.process_mode = Node.PROCESS_MODE_ALWAYS
	_init_meta(_feedback); add_child(_feedback)

func _ready() -> void:
	var window := get_window()
	if window:
		window.focus_exited.connect(_focus_exited)
		window.focus_entered.connect(_focus_entered)

func _init_meta(voice: Node) -> void:
	voice.set_meta("serial", -1); voice.set_meta("cast_id", 0)
	voice.set_meta("cue", ""); voice.set_meta("priority", 0)

static func _integer(value: Variant, minimum := 0) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and value >= minimum and value <= MAX_INTEGER and floorf(float(value)) == float(value)

static func _number(value: Variant, low: float, high: float) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value)) and float(value) >= low and float(value) <= high

static func _point(value: Variant) -> bool:
	return value is Vector3 and value.is_finite() and maxf(absf(value.x), maxf(absf(value.y), absf(value.z))) <= 10000

func _valid(event: Variant) -> bool:
	if not event is Dictionary or not _integer(event.get("schema"), 1) or event.schema != 1 or not event.get("kind") is String or event.kind not in KINDS: return false
	if not _integer(event.get("generation")) or not _integer(event.get("epoch")) or event.epoch != event.generation or not _integer(event.get("event_seq"), 1) or not _integer(event.get("cast_id")): return false
	if not event.get("hero_id") is String or event.hero_id != "rama" or not _number(event.get("time_s"), 0, 86400): return false
	if event.kind == "reset": return event.cast_id == 0
	if event.cast_id < 1 or not event.get("ability_id") is String or event.ability_id not in IDS or not _number(event.get("age_s"), 0, 8): return false
	for key in ["origin", "forward", "target"]:
		if not _point(event.get(key)): return false
	if not event.get("timing") is Dictionary or not _number(event.timing.get("windup_s"), .01, 2) or not _number(event.timing.get("recovery_s"), .01, 1): return false
	if not event.get("geometry") is Dictionary or not event.geometry.get("projectiles", []) is Array or event.geometry.get("projectiles", []).size() > 3: return false
	if event.ability_id == "dawn_volley":
		if event.geometry.get("projectiles", []).size() != 3: return false
		for index in 3:
			var projectile: Variant = event.geometry.projectiles[index]
			if not projectile is Dictionary or not _integer(projectile.get("index")) or projectile.index != index or not _number(projectile.get("delay_s"), 0, .4): return false
			if absf(float(projectile.delay_s) - .1 * index) > .000001: return false
	if not _number(event.get("release_age_s", -1.0), -1, 2): return false
	if event.kind == "begin" and (float(event.age_s) != 0 or float(event.release_age_s) != -1): return false
	if event.kind == "release" and (absf(float(event.release_age_s) - float(event.age_s)) > 1e-8 or float(event.age_s) + 1e-8 < float(event.timing.windup_s) or float(event.age_s) > float(event.timing.windup_s) + .050001): return false
	if not event.get("receipts") is Array or event.receipts.size() > 18: return false
	if event.has("contact_position") and not _point(event.contact_position): return false
	if event.has("reason") and (not event.reason is String or event.reason.length() > 80): return false
	for receipt in event.receipts:
		if not receipt is Dictionary or not receipt.get("kind") is String or receipt.kind not in ["damage", "guardian"] or not _integer(receipt.get("unit_id")): return false
		if receipt.kind == "damage" and (not _number(receipt.get("damage_applied"), 0, 1000) or not _point(receipt.get("position"))): return false
	return true

func _reject(code: String) -> Dictionary:
	_rejected += 1
	return {"ok":false, "code":code}

func consume_event(event: Variant) -> Dictionary:
	if not _errors.is_empty(): return {"ok":false, "code":"AUDIO_UNAVAILABLE"}
	if not _valid(event): return _reject("INVALID_EVENT")
	var generation: int = int(event.generation)
	var kind: String = event.kind
	var cast_id: int = int(event.cast_id)
	if generation < _generation or generation == _generation and (event.event_seq <= _last_seq or kind == "reset" or float(event.time_s) + 1e-8 < _last_time): return _reject("STALE_EVENT")
	if generation > _generation:
		if kind not in ["begin", "reset"]: return _reject("GENERATION_REQUIRES_BEGIN_OR_RESET")
		_stop_all(); _active.clear(); _generation = generation; _last_seq = -1; _last_cast = 0; _last_confirm_time = -1; _last_time = -1
	if kind == "reset":
		_last_seq = int(event.event_seq); _last_time = float(event.time_s); _stop_all(); _active.clear()
		return {"ok":true, "code":"RESET"}
	if kind == "begin":
		if cast_id <= _last_cast: return _reject("CAST_REUSE")
		if _active.size() >= MAX_CASTS: return _reject("CAST_CAP")
	elif not _active.has(cast_id) or _active[cast_id].ability != event.ability_id:
		return _reject("NO_MATCHING_CAST")
	else:
		if float(event.age_s) + 1e-8 < float(_active[cast_id].age): return _reject("AGE_REVERSED")
		if kind == "release" and _active[cast_id].released: return _reject("DUPLICATE_RELEASE")
		if event.timing != _active[cast_id].timing: return _reject("TIMING_CHANGED")
		if _active[cast_id].released and absf(float(event.release_age_s) - float(_active[cast_id].release_age)) > 1e-8: return _reject("RELEASE_AGE_CHANGED")
		if kind in ["impact", "recovery"] and not _active[cast_id].released: return _reject("RELEASE_REQUIRED")
	_last_seq = int(event.event_seq)
	_last_time = float(event.time_s)
	if kind == "begin":
		_last_cast = cast_id
		_active[cast_id] = {"ability":event.ability_id, "age":float(event.age_s), "released":false, "release_age":-1.0, "timing":event.timing.duplicate(true), "pulses":0, "confirmed":{}, "blocked":{}}
		_play("draw_" + event.ability_id, event.origin, 1, cast_id)
	else: _active[cast_id].age = float(event.age_s)
	match kind:
		"release":
			_active[cast_id].released = true
			_active[cast_id].release_age = float(event.release_age_s)
			_stop_cast_draw(cast_id)
			_play("release_" + event.ability_id, event.origin, 2, cast_id)
			if event.ability_id == "dawn_volley": _active[cast_id].pulses = 1
		"tick": _volley_pulses(event)
		"impact": _impact(event)
		"cancel":
			_stop_cast(cast_id)
			if event.get("reason", "") not in ["defeated", "reset", "player reset", "scene_exit", "reconfigure", "round_ended"]: _play("cancel", event.origin, 1, cast_id)
			_active.erase(cast_id)
		"end":
			_stop_cast(cast_id); _active.erase(cast_id)
	return {"ok":true, "code":"CONSUMED"}

func _volley_pulses(event: Dictionary) -> void:
	var cast: Dictionary = _active[int(event.cast_id)]
	if event.ability_id != "dawn_volley" or not cast.released: return
	# The existing army tick defines pulse eligibility. No AudioServer timer or
	# deferred queue can fire a cosmetic arrow after a pause/cancel/reset.
	for index in range(int(cast.pulses), 3):
		if float(event.age_s) + 1e-8 < float(event.release_age_s) + float(event.geometry.projectiles[index].delay_s): break
		cast.pulses = index + 1
		_play("release_dawn_volley", event.origin, 2, int(event.cast_id))

func _impact(event: Dictionary) -> void:
	var cast: Dictionary = _active[int(event.cast_id)]
	if event.get("reason", "") == "wall":
		var index: Variant = event.get("projectile_index", 0)
		if _integer(index) and index <= 2 and not cast.blocked.has(index):
			cast.blocked[index] = true
			_play("blocked", event.get("contact_position", event.target), 1, int(event.cast_id))
		return
	if event.get("reason", "") != "unit": return
	var accepted := false
	for receipt in event.receipts:
		if receipt.kind != "damage" or receipt.damage_applied <= 0: continue
		var key := "%s:%s" % [event.get("projectile_index", 0), receipt.unit_id]
		if not cast.confirmed.has(key) and cast.confirmed.size() < 18: cast.confirmed[key] = true; accepted = true
	if not accepted: return
	_play("contact", event.get("contact_position", event.target), 1, int(event.cast_id))
	if float(event.time_s) - _last_confirm_time + 1e-8 >= .07:
		_last_confirm_time = float(event.time_s)
		_play("confirm", Vector3.ZERO, 2, int(event.cast_id), true)

func consume_damage(receipt: Variant) -> Dictionary:
	if not receipt is Dictionary or not receipt.get("accepted") is bool or not receipt.accepted or not _integer(receipt.get("generation")) or not receipt.get("source_id") is String or receipt.source_id.is_empty() or receipt.source_id.length() > 80 or not _integer(receipt.get("sequence"), -1): return _reject("INVALID_DAMAGE")
	for key in ["health_before", "health_after", "shield_before", "shield_after", "damage_applied"]:
		if not _number(receipt.get(key), 0, 1000): return _reject("INVALID_DAMAGE")
	if not _number(receipt.get("time_s"), 0, 86400) or receipt.damage_applied <= 0: return _reject("INVALID_DAMAGE")
	if receipt.health_before > 300 or receipt.health_after > 300 or receipt.shield_before > 100 or receipt.shield_after > 100 or absf(float(receipt.health_before) + float(receipt.shield_before) - float(receipt.health_after) - float(receipt.shield_after) - float(receipt.damage_applied)) > .000001: return _reject("INVALID_DAMAGE")
	var generation: int = int(receipt.generation)
	if _receiver_generation >= 0 and generation != _receiver_generation: return _reject("RECEIVER_GENERATION_MISMATCH")
	if generation < _vitals_generation or generation == _vitals_generation and float(receipt.time_s) + 1e-8 < _last_damage_time: return _reject("STALE_DAMAGE")
	if generation > _vitals_generation:
		_damage_sources.clear(); _vitals_generation = generation; _last_damage_time = -1
	var key: String = receipt.source_id
	var watermark: Dictionary = _damage_sources.get(key, {"sequence":-2, "time":-1.0})
	if int(receipt.sequence) >= 0 and int(receipt.sequence) <= int(watermark.sequence) or int(receipt.sequence) == -1 and float(receipt.time_s) <= float(watermark.time) + 1e-8: return _reject("DUPLICATE_DAMAGE")
	if _damage_sources.size() >= 64 and not _damage_sources.has(key): _damage_sources.erase(_damage_sources.keys()[0])
	_damage_sources[key] = {"sequence":int(receipt.sequence), "time":float(receipt.time_s)}
	_last_damage_time = float(receipt.time_s)
	if receipt.health_after <= 0:
		set_alive(false)
		return {"ok":true, "code":"DEFEATED_SILENT"}
	_play("threat", Vector3.ZERO, 3, 0, true)
	return {"ok":true, "code":"DAMAGE_CONSUMED"}

func _can_play() -> bool:
	return _errors.is_empty() and _alive and _volume > 0 and not _suspended and _focused and is_inside_tree() and not get_tree().paused

func _play(cue: String, point: Vector3, priority: int, cast_id: int, feedback := false) -> void:
	if not _can_play(): _suppressed += 1; return
	var selected: Node
	if feedback:
		selected = _feedback
		if _feedback.playing and int(_feedback.get_meta("priority")) > priority: _dropped += 1; return
	else:
		for voice in _world:
			if not voice.playing: selected = voice; break
		if selected == null:
			for voice in _world:
				if int(voice.get_meta("priority")) <= priority and (selected == null or int(voice.get_meta("serial")) < int(selected.get_meta("serial"))): selected = voice
	if selected == null: _dropped += 1; return
	selected.stop(); selected.stream = _streams[cue]
	selected.volume_db = GAIN_DB + linear_to_db(_volume)
	selected.pitch_scale = .988 + .006 * posmod(cast_id + _generation + NAMES.find(cue), 5)
	if selected is AudioStreamPlayer3D: selected.global_position = point
	_serial += 1
	selected.set_meta("serial", _serial); selected.set_meta("cast_id", cast_id)
	selected.set_meta("cue", cue); selected.set_meta("priority", priority)
	selected.play(); _played += 1

func _stop_cast_draw(cast_id: int) -> void:
	for voice in _world:
		if int(voice.get_meta("cast_id")) == cast_id and String(voice.get_meta("cue")).begins_with("draw_"): voice.stop()

func _stop_cast(cast_id: int) -> void:
	for voice in _world:
		if int(voice.get_meta("cast_id")) == cast_id: voice.stop()
	if int(_feedback.get_meta("cast_id")) == cast_id: _feedback.stop()

func _stop_all() -> void:
	for voice in _world: voice.stop()
	if is_instance_valid(_feedback): _feedback.stop()

func set_volume(value: float) -> bool:
	if not is_finite(value): return false
	_volume = clampf(value, 0, 1)
	if _volume == 0: _stop_all()
	else:
		for voice in _world: voice.volume_db = GAIN_DB + linear_to_db(_volume)
		_feedback.volume_db = GAIN_DB + linear_to_db(_volume)
	return true

func set_suspended(value: bool) -> void:
	_suspended = value
	if value: _stop_all()

func set_focused(value: bool) -> void:
	_focused = value
	if not value: _stop_all()

func set_receiver_generation(value: int) -> bool:
	if value < 0 or value > MAX_INTEGER or value < _receiver_generation or value < _vitals_generation: return false
	if value > _vitals_generation:
		_stop_all(); _damage_sources.clear(); _last_damage_time = -1
		_vitals_generation = value
	_receiver_generation = value
	return true

func set_alive(value: bool) -> void:
	_alive = value
	if not value: _stop_all()

func _focus_exited() -> void: set_focused(false)
func _focus_entered() -> void: set_focused(true)

func _process(_delta: float) -> void:
	if is_inside_tree() and get_tree().paused: _stop_all()

func _notification(what: int) -> void:
	if what == NOTIFICATION_PAUSED: _stop_all()

func reset() -> void:
	# Local cleanup keeps all event/receipt watermarks. New kit generation is an
	# explicit reset event; vitals generation advances in its real owner.
	_stop_all(); _active.clear(); _alive = true

func _exit_tree() -> void: _stop_all()

func report() -> Dictionary:
	var voices := []
	var playing := 0
	for voice in _world + [_feedback]:
		if voice.playing: playing += 1
		voices.append({"playing":voice.playing, "cue":voice.get_meta("cue"), "cast_id":voice.get_meta("cast_id"), "serial":voice.get_meta("serial"), "priority":voice.get_meta("priority"), "volume_db":voice.volume_db, "pitch_scale":voice.pitch_scale, "spatial":voice is AudioStreamPlayer3D})
	return {"ready":_errors.is_empty() and _streams.size() == NAMES.size(), "errors":_errors.duplicate(), "generation":_generation, "last_event_seq":_last_seq, "last_cast_id":_last_cast, "active_casts":_active.size(), "damage_sources":_damage_sources.size(), "vitals_generation":_vitals_generation, "receiver_generation":_receiver_generation, "volume":_volume, "suspended":_suspended, "focused":_focused, "alive":_alive, "playing":playing, "players":MAX_VOICES, "streams":_streams.size(), "played":_played, "suppressed":_suppressed, "rejected":_rejected, "dropped":_dropped, "voices":voices, "listening":"UNRUN"}
