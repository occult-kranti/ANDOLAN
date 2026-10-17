extends Node
## Original traversal score and positional cues. One owned music player and six
## reusable cue players; no global buses, timers or players survive scene return.
const SETTINGS := "user://courtyard-settings.cfg"
const InputBindings = preload("res://scripts/input_bindings.gd")
const DEFAULT_VOLUME := 0.35
const POOL_SIZE := 6
const BASE := "res://assets/audio/traversal/"
const MUSIC_GAIN_DB := -20.0
const CUE_GAIN_DB := -6.0
const EVENT_PRIORITY := {"grapple_lock":3,"grapple_release":2,"flight_start":2,"flight_exhaust":3,"flight_recharge":3,"minion_hit":1,"coin":1}
const EVENT_COOLDOWN := {"grapple_lock":0.12,"grapple_release":0.12,"flight_start":0.25,"flight_exhaust":0.4,"flight_recharge":0.4,"minion_hit":0.07,"coin":0.08}
var volume := DEFAULT_VOLUME
var music_enabled := true
var suspended := false
var focused := true
var music_player: AudioStreamPlayer
var cue_players: Array[AudioStreamPlayer3D] = []
var _streams: Dictionary = {}
var _last_event_usec: Dictionary = {}
var _priorities: Array[int] = []
var _started_usec: Array[int] = []
var _configured := false
var _ready_complete := false
var _duck_remaining := 0.0
var _duck_db := 0.0
var _played_events := 0
var _dropped_events := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	if not _configured: volume = _read_saved_volume()
	music_player = AudioStreamPlayer.new()
	music_player.name = "LanternProcession"
	var loop := load(BASE + "lane-procession-loop.wav") as AudioStreamWAV
	if loop:
		loop = loop.duplicate() as AudioStreamWAV
		loop.loop_mode = AudioStreamWAV.LOOP_FORWARD
		loop.loop_begin = 0
		loop.loop_end = 480000
		music_player.stream = loop
	add_child(music_player)
	for kind: String in EVENT_PRIORITY:
		_streams[kind] = load(BASE + kind + ".wav")
	for index in range(POOL_SIZE):
		var player := AudioStreamPlayer3D.new()
		player.name = "TraversalCue%d" % index
		player.max_distance = 65.0
		player.unit_size = 2.5
		player.max_db = CUE_GAIN_DB
		player.panning_strength = 0.5
		player.attenuation_filter_cutoff_hz = 8500.0
		add_child(player)
		cue_players.append(player)
		_priorities.append(0)
		_started_usec.append(0)
	var window := get_window()
	if window:
		window.focus_exited.connect(_on_focus_exited)
		window.focus_entered.connect(_on_focus_entered)
	_ready_complete = true
	_sync_gain()
	_sync_music()

func _read_saved_volume() -> float:
	var loaded: Dictionary = InputBindings.read_config(SETTINGS)
	if not loaded.ok: return DEFAULT_VOLUME
	var config: ConfigFile = loaded.config
	var value: Variant = config.get_value("audio", "volume", DEFAULT_VOLUME)
	if typeof(value) not in [TYPE_INT, TYPE_FLOAT]: return DEFAULT_VOLUME
	if not is_finite(float(value)): return DEFAULT_VOLUME
	return clampf(float(value), 0.0, 1.0)

func configure(value: float) -> void:
	_configured = true
	set_volume(value)

func set_volume(value: float) -> void:
	volume = clampf(value, 0.0, 1.0) if is_finite(value) else DEFAULT_VOLUME
	if not _ready_complete: return
	if volume == 0.0:
		_stop_cues()
		music_player.stop()
	_sync_gain()
	_sync_music()

func set_music_enabled(value: bool) -> void:
	music_enabled = value
	_sync_music()

func set_suspended(value: bool) -> void:
	suspended = value
	if value: _stop_cues()
	_sync_music()

func _on_focus_exited() -> void:
	focused = false
	_stop_cues()
	_sync_music()

func _on_focus_entered() -> void:
	focused = true
	_sync_music()

func _notification(what: int) -> void:
	if not _ready_complete: return
	if what == NOTIFICATION_PAUSED:
		_stop_cues()
		music_player.stream_paused = true
	elif what == NOTIFICATION_UNPAUSED:
		_sync_music()

func _can_play() -> bool:
	return _ready_complete and volume > 0.0 and focused and not suspended and is_inside_tree() and not get_tree().paused

func _sync_music() -> void:
	if not _ready_complete: return
	if volume == 0.0 or not music_enabled:
		music_player.stop()
		return
	if not _can_play():
		music_player.stream_paused = true
		return
	music_player.stream_paused = false
	if not music_player.playing and music_player.stream: music_player.play()

func _sync_gain() -> void:
	if not _ready_complete: return
	var gain := linear_to_db(volume) if volume > 0.0 else -80.0
	music_player.volume_db = gain + MUSIC_GAIN_DB + _duck_db
	for player in cue_players: player.volume_db = gain + CUE_GAIN_DB

func _process(delta: float) -> void:
	_duck_remaining = maxf(0.0, _duck_remaining - delta)
	var target := -8.0 if _duck_remaining > 0.0 else 0.0
	_duck_db = move_toward(_duck_db, target, delta * (160.0 if target < _duck_db else 28.0))
	_sync_gain()

func play_event(kind: String, world_position: Vector3 = Vector3.ZERO) -> void:
	if not EVENT_PRIORITY.has(kind) or not world_position.is_finite() or not _can_play():
		_dropped_events += 1
		return
	var now := Time.get_ticks_usec()
	var last: int = _last_event_usec.get(kind, -10000000)
	if now - last < float(EVENT_COOLDOWN[kind]) * 1000000.0:
		_dropped_events += 1
		return
	var slot := -1
	for index in range(cue_players.size()):
		if not cue_players[index].playing:
			slot = index
			break
	if slot < 0:
		var oldest: int = 9223372036854775807
		for index in range(cue_players.size()):
			if _priorities[index] <= int(EVENT_PRIORITY[kind]) and _started_usec[index] < oldest:
				slot = index
				oldest = _started_usec[index]
	if slot < 0:
		_dropped_events += 1
		return
	var player := cue_players[slot]
	player.stop()
	player.stream = _streams[kind]
	player.global_position = world_position
	player.play()
	_last_event_usec[kind] = now
	_priorities[slot] = int(EVENT_PRIORITY[kind])
	_started_usec[slot] = now
	_duck_remaining = 0.22
	_played_events += 1

func _stop_cues() -> void:
	for player in cue_players: player.stop()

func get_diagnostics() -> Dictionary:
	var active := 0
	for player in cue_players:
		if player.playing: active += 1
	return {"volume":volume,"muted":volume==0.0,"music_enabled":music_enabled,
		"active_music":is_instance_valid(music_player) and music_player.playing,
		"music_paused":is_instance_valid(music_player) and music_player.stream_paused,
		"playing_cues":active,"pool_size":cue_players.size(),"focused":focused,"suspended":suspended,
		"played_events":_played_events,"dropped_events":_dropped_events,"duck_db":_duck_db}

func _exit_tree() -> void:
	_stop_cues()
	if is_instance_valid(music_player): music_player.stop()
