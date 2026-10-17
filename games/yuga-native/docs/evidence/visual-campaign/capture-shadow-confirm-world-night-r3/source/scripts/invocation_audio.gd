extends Node
## Original short cues. All invocation audio shares this three-player pool.
const DIRECTORY := "res://assets/audio/invocations/"
const MAX_VOICES := 3
const MAX_INTEGER := 9007199254740991
const KINDS := ["begin","release","impact","tick","end","cancel","reset"]
var _streams: Dictionary={}
var _voices: Array[AudioStreamPlayer]=[]
var _epoch := -1
var _last_seq := -1
var _last_cast := 0
var _active: Dictionary={}
var _volume := .35
var _suspended := false
var _serial := 0
var _played := 0
var _suppressed := 0
var _rejected := 0
var _errors: Array[String]=[]

func _init() -> void:
	process_mode=Node.PROCESS_MODE_ALWAYS
	set_process(false);set_physics_process(false)
	var manifest_path := DIRECTORY+"manifest.json"
	if not FileAccess.file_exists(manifest_path): _errors.append("manifest_missing")
	else:
		var data: Variant=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
		if not data is Dictionary or not data.get("files") is Dictionary or data.files.size()!=16: _errors.append("manifest_invalid")
		else:
			for file_name in data.files:
				if not file_name is String or "/" in file_name or ".." in file_name or not file_name.ends_with(".wav"):
					_errors.append("file_name_invalid");continue
				var path: String=DIRECTORY+file_name
				var stream: AudioStreamWAV
				if FileAccess.file_exists(path+".import") and ResourceLoader.exists(path): stream=load(path) as AudioStreamWAV
				elif FileAccess.file_exists(path): stream=AudioStreamWAV.load_from_file(path)
				if stream==null or stream.loop_mode!=AudioStreamWAV.LOOP_DISABLED or stream.mix_rate!=48000 or stream.get_length()<=0 or stream.get_length()>.5:
					_errors.append("stream_invalid:"+file_name);continue
				_streams[file_name]=stream
	for i in MAX_VOICES:
		var voice := AudioStreamPlayer.new();voice.name="InvocationVoice%d"%i
		voice.process_mode=Node.PROCESS_MODE_ALWAYS
		voice.set_meta("serial",-1);voice.set_meta("cast_id",0);voice.set_meta("cue","")
		add_child(voice);_voices.append(voice)

static func _integer(v: Variant, minimum: int=0) -> bool:
	return (v is int or v is float) and is_finite(float(v)) and v>=minimum and v<=MAX_INTEGER and floor(float(v))==float(v)

func _valid(event: Variant) -> bool:
	if not event is Dictionary or not _integer(event.get("schema"),1) or event.schema!=1 or not event.get("kind") is String or event.kind not in KINDS: return false
	if not _integer(event.get("epoch"),1) or not _integer(event.get("event_seq")) or not _integer(event.get("cast_id")): return false
	if event.kind=="reset": return event.cast_id==0
	if event.cast_id<1 or not event.get("hero_id") is String or not _streams.has(event.hero_id+"-release.wav") or not event.get("effect_id") is String or event.effect_id!=event.hero_id+".r.v1": return false
	if not event.get("team") is String or event.team!="sun": return false
	for key in ["time_s","age_s"]:
		var value: Variant=event.get(key)
		if not (value is int or value is float) or not is_finite(float(value)) or value<0 or value>86400: return false
	for key in ["origin","forward","target"]:
		var value: Variant=event.get(key)
		if not value is Vector3 or not value.is_finite(): return false
		if maxf(absf(value.x),maxf(absf(value.y),absf(value.z)))>10000: return false
	return true

func consume_event(event: Variant) -> Dictionary:
	if not _errors.is_empty(): return {"ok":false,"code":"AUDIO_UNAVAILABLE"}
	if not _valid(event): _rejected+=1;return {"ok":false,"code":"INVALID_EVENT"}
	if event.epoch<_epoch or event.epoch==_epoch and (event.event_seq<=_last_seq or event.kind=="reset"): _rejected+=1;return {"ok":false,"code":"STALE_EVENT"}
	if event.epoch>_epoch:
		if event.kind not in ["reset","begin"]: _rejected+=1;return {"ok":false,"code":"EPOCH_REQUIRES_BEGIN_OR_RESET"}
		_stop_all();_active.clear();_epoch=int(event.epoch);_last_seq=-1;_last_cast=0
	if event.kind=="reset":
		_last_seq=int(event.event_seq);_stop_all();_active.clear()
		return {"ok":true,"code":"RESET"}
	if event.kind=="begin":
		if event.cast_id<=_last_cast: _rejected+=1;return {"ok":false,"code":"CAST_REUSE"}
		_stop_all();_last_cast=int(event.cast_id)
		_active={"id":int(event.cast_id),"hero":event.hero_id,"released":false}
	elif _active.is_empty() or event.cast_id!=_active.id or event.hero_id!=_active.hero:
		_rejected+=1;return {"ok":false,"code":"NO_MATCHING_CAST"}
	if event.kind=="release" and _active.released:
		_rejected+=1;return {"ok":false,"code":"DUPLICATE_RELEASE"}
	_last_seq=int(event.event_seq)
	match event.kind:
		"begin": _play("windup.wav",int(event.cast_id))
		"release":
			_active.released=true
			_stop_all()
			_play(event.hero_id+"-release.wav",int(event.cast_id))
		"cancel":
			_stop_all();_play("cancel.wav",int(event.cast_id));_active.clear()
		"end":
			_stop_all();_active.clear()
	return {"ok":true,"code":"CONSUMED"}

func _play(file_name: String, cast_id: int) -> void:
	if _suspended or _volume<=0 or not is_inside_tree() or get_tree().paused: _suppressed+=1;return
	var selected: AudioStreamPlayer=null
	for voice in _voices:
		if not voice.playing: selected=voice;break
	if selected==null:
		selected=_voices[0]
		for voice in _voices:
			if voice.get_meta("serial")<selected.get_meta("serial"): selected=voice
	selected.stop();selected.stream=_streams[file_name];selected.volume_db=linear_to_db(_volume)
	_serial+=1;selected.set_meta("serial",_serial);selected.set_meta("cast_id",cast_id);selected.set_meta("cue",file_name)
	selected.play();_played+=1

func _stop_all() -> void:
	for voice in _voices: voice.stop()

func set_volume(value: float) -> bool:
	if not is_finite(value): return false
	_volume=clampf(value,0,1)
	if _volume==0: _stop_all()
	else:
		for voice in _voices: voice.volume_db=linear_to_db(_volume)
	return true

func set_suspended(value: bool) -> void:
	_suspended=value
	if value: _stop_all()

func reset() -> void:
	# Local cleanup keeps receipt watermarks; session reset advances epoch explicitly.
	_stop_all();_active.clear()

func report() -> Dictionary:
	var playing := 0
	var voices := []
	for voice in _voices:
		if voice.playing: playing+=1
		voices.append({"playing":voice.playing,"cue":voice.get_meta("cue"),"cast_id":voice.get_meta("cast_id"),"serial":voice.get_meta("serial")})
	return {"ready":_errors.is_empty() and _streams.size()==16,"errors":_errors.duplicate(),"epoch":_epoch,"last_event_seq":_last_seq,"last_cast_id":_last_cast,"active":_active.duplicate(true),"volume":_volume,"suspended":_suspended,"playing":playing,"players":_voices.size(),"streams":_streams.size(),"played":_played,"suppressed":_suppressed,"rejected":_rejected,"voices":voices}
