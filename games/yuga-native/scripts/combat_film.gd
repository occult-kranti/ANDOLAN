extends Node3D
## Deterministic original combat film. Visual receipts never drive multiplayer state.
const Actor = preload("res://scripts/cinematic_actor.gd")
const Effects = preload("res://scripts/duel_effects.gd")
const Lighting = preload("res://scripts/film_lighting.gd")
const FILM_PATH := "res://assets/cinematics/confluence-duel.json"
const AUDIO_SETTINGS_PATH := "user://courtyard-settings.cfg"
var manifest_override: Dictionary = {}
var manifest: Dictionary = {}
var errors: Array[String] = []
var ready_to_play := false
var playing := false
var capture_mode := false
var current_time := 0.0
var duration := 24.0
var reduced_flash := true
var reduced_motion := false
var captions_enabled := true
var actors: Dictionary = {}
var effects: Node3D
var world: Node3D
var camera: Camera3D
var ui: CanvasLayer
var controls: PanelContainer
var caption_panel: PanelContainer
var caption_label: Label
var time_label: Label
var play_button: Button
var timeline_slider: HSlider
var receipt_label: Label
var audio_player: AudioStreamPlayer
var audio_volume := 0.7
var reduced_flash_button: CheckButton
var reduced_motion_button: CheckButton
var visual_health: Dictionary = {}
var active_actions: Dictionary = {}
var active_camera := ""
var last_receipt := ""
var release_sockets: Dictionary = {}

func _ready() -> void:
	process_mode=Node.PROCESS_MODE_ALWAYS
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	if manifest_override.is_empty():
		var parsed=JSON.parse_string(FileAccess.get_file_as_string(FILM_PATH))
		if parsed is Dictionary: manifest=parsed
		else: errors.append("Film script is missing or invalid JSON.")
	else: manifest=manifest_override.duplicate(true)
	if errors.is_empty(): errors=validate_script(manifest)
	_build_ui()
	if not errors.is_empty():
		_show_error()
		return
	duration=manifest.duration_seconds
	timeline_slider.max_value=duration
	_build_stage()
	if not errors.is_empty():
		_show_error()
		return
	ready_to_play=true
	reduced_flash=manifest.get("accessibility",{}).get("reduced_flash",true)
	set_accessibility(reduced_flash,false)
	sample_time(0,false)
	set_playing(true)
	get_window().focus_exited.connect(func():
		if not capture_mode: set_playing(false))
	print("YUGA_COMBAT_FILM_READY ",JSON.stringify(get_diagnostics()))

func _finite_vector(value: Variant) -> bool:
	if not value is Array or value.size()!=3: return false
	for component in value:
		if not (component is float or component is int) or not is_finite(float(component)): return false
	return true

func _number(value: Variant) -> bool:
	return (value is float or value is int) and is_finite(float(value))

func validate_script(data: Dictionary) -> Array[String]:
	var result: Array[String]=[]
	if data.get("schema_version",0)!=1: result.append("Unsupported film schema.")
	var length_: float=float(data.get("duration_seconds",0))
	if not is_finite(length_) or length_<=0 or length_>120: result.append("Film duration must be finite and between 0 and 120 seconds.")
	for field in ["actors","actions","motion_tracks","cameras","cues","visual_receipts","captions"]:
		if not data.get(field) is Array: result.append("Missing film array: "+field)
	if not result.is_empty(): return result
	if data.actors.size()!=2: result.append("This film requires exactly two declared actors.")
	var ids:={}
	var actor_ids:={}
	var resource_paths:={}
	for actor in data.actors:
		if not actor is Dictionary or not actor.has("id"):
			result.append("Invalid actor entry.")
			continue
		actor_ids[actor.id]=true
		for field in ["model_path","animation_library_path"]:
			if not actor.get(field) is String or not ResourceLoader.exists(actor[field]): result.append(str(actor.id)+": missing "+field)
			elif resource_paths.has(actor[field]): result.append(str(actor.id)+": duplicate actor resource "+field)
			else: resource_paths[actor[field]]=true
		if not _finite_vector(actor.get("position")) or not is_finite(float(actor.get("yaw_degrees",NAN))): result.append(str(actor.id)+": invalid initial transform")
	for field in ["actors","actions","cameras","cues","visual_receipts","captions"]:
		for entry in data[field]:
			if not entry is Dictionary or not entry.get("id") is String:
				result.append("Invalid ID in "+field)
				continue
			if ids.has(entry.id): result.append("Duplicate film ID: "+entry.id)
			ids[entry.id]=true
			for actor_field in ["actor_id","target_id","aim_target_id"]:
				if entry.has(actor_field) and not actor_ids.has(entry[actor_field]): result.append(entry.id+": unknown "+actor_field)
			if field!="actors":
				if not _number(entry.get("t_seconds")): result.append(entry.id+": nonnumeric event time")
				if field in ["actions","cameras","cues"] and (not _number(entry.get("duration_seconds")) or float(entry.get("duration_seconds",0))<=0): result.append(entry.id+": missing positive duration")
				if entry.has("duration_seconds") and (not _number(entry.duration_seconds) or float(entry.duration_seconds)<=0): result.append(entry.id+": duration must be positive")
				var start: float=float(entry.get("t_seconds",NAN))
				var end: float=float(entry.get("end_seconds",start+float(entry.get("duration_seconds",0))))
				if not is_finite(start) or not is_finite(end) or start<0 or end<start or end>length_+.0001: result.append(entry.id+": invalid time window")
			for vector_field in ["position","look_at","from_position","to_position"]:
				if entry.has(vector_field) and not _finite_vector(entry[vector_field]): result.append(entry.id+": nonfinite "+vector_field)
			if field=="actions" and (not actor_ids.has(entry.get("actor_id")) or not entry.get("clip_id") is String): result.append(entry.id+": action requires actor and clip")
			if field=="captions" and (not _number(entry.get("end_seconds")) or not entry.get("text") is String): result.append(entry.id+": caption requires end time and text")
			if field=="visual_receipts":
				for receipt_field in ["amount","health_before","health_after"]:
					if not _number(entry.get(receipt_field)) or float(entry.get(receipt_field,-1))<0 or float(entry.get(receipt_field,101))>100: result.append(entry.id+": invalid "+receipt_field)
	for track in data.motion_tracks:
		if not track is Dictionary or not actor_ids.has(track.get("actor_id")) or not track.get("keys") is Array:
			result.append("Invalid motion track")
			continue
		if track.keys.size()<2:
			result.append("Motion track requires two endpoint keys: "+str(track.actor_id))
			continue
		var previous:=-1.0
		for key in track.keys:
			if not key is Dictionary:
				result.append("Invalid motion key object")
				continue
			var time: float=float(key.get("t_seconds",NAN))
			if not _number(key.get("t_seconds")) or time<=previous or time<0 or time>length_ or not _finite_vector(key.get("position")) or not _number(key.get("yaw_degrees")): result.append("Invalid motion key: "+str(track.actor_id))
			previous=time
		if track.keys[0] is Dictionary and track.keys[-1] is Dictionary:
			if float(track.keys[0].get("t_seconds",-1))!=0 or not is_equal_approx(float(track.keys[-1].get("t_seconds",-1)),length_): result.append("Motion track must cover the full film: "+str(track.actor_id))
	for actor_id in actor_ids:
		var track_count:=0
		var action_count:=0
		var action_end:=-1.0
		for track in data.motion_tracks:
			if track is Dictionary and track.get("actor_id")==actor_id: track_count+=1
		for action in data.actions:
			if not action is Dictionary or action.get("actor_id")!=actor_id: continue
			action_count+=1
			if float(action.get("t_seconds",-1))<action_end-.00001: result.append("Overlapping or unordered actor actions: "+str(actor_id))
			action_end=float(action.get("t_seconds",0))+float(action.get("duration_seconds",0))
		if track_count!=1: result.append("Exactly one motion track required for "+str(actor_id))
		if action_count==0: result.append("No actions declared for "+str(actor_id))
	for path in [data.get("environment_path",""),data.get("audio_mix_path","")]:
		if not path is String or not ResourceLoader.exists(path): result.append("Missing film resource: "+str(path))
	if data.cameras.is_empty(): result.append("Film requires a camera track.")
	var previous_camera:=-1.0
	for view in data.cameras:
		if not view is Dictionary: continue
		if not _finite_vector(view.get("position")) or not _finite_vector(view.get("look_at")): result.append("Camera position and target are required")
		elif _v(view.position).distance_squared_to(_v(view.look_at))<.000001: result.append("Camera position equals its target")
		if not _number(view.get("fov")) or float(view.get("fov",0))<20 or float(view.get("fov",0))>100: result.append("Camera FOV out of range")
		if not _number(view.get("blend_seconds",0)) or float(view.get("blend_seconds",0))<0: result.append("Camera blend must be finite and nonnegative")
		if float(view.get("t_seconds",-1))<=previous_camera: result.append("Camera times must increase strictly")
		previous_camera=float(view.get("t_seconds",-1))
	if result.is_empty():
		var soundtrack=load(data.audio_mix_path)
		if not soundtrack is AudioStream or absf(soundtrack.get_length()-length_)>.05: result.append("Film soundtrack duration/resource does not match the timeline")
		if soundtrack is AudioStreamWAV and soundtrack.loop_mode!=AudioStreamWAV.LOOP_DISABLED: result.append("Film soundtrack must not loop")
		for actor in data.actors:
			var library=load(actor.animation_library_path)
			if not library is AnimationLibrary:
				result.append(actor.id+": invalid animation library")
				continue
			if not library.has_animation("ready"): result.append(actor.id+": missing ready clip")
			for action in data.actions:
				if action.actor_id==actor.id and not library.has_animation(action.get("clip_id","")): result.append(action.id+": missing film clip")
	return result

func _v(value: Array) -> Vector3:
	return Vector3(value[0],value[1],value[2])

func _build_stage() -> void:
	world=Node3D.new()
	world.name="FilmStage"
	add_child(world)
	var packed=load(manifest.environment_path)
	if not packed is PackedScene:
		errors.append("Film environment is not an imported scene.")
		return
	var environment_model=packed.instantiate()
	environment_model.name="AuthoredCourtyard"
	world.add_child(environment_model)
	var atmosphere:=WorldEnvironment.new()
	atmosphere.environment=Environment.new()
	world.add_child(atmosphere)
	var sun:=DirectionalLight3D.new()
	world.add_child(sun)
	Lighting.apply(atmosphere.environment,sun,world,false,true)
	for actor_spec in manifest.actors:
		var actor:=Node3D.new()
		actor.set_script(Actor)
		actor.name=actor_spec.id
		world.add_child(actor)
		actors[actor_spec.id]=actor
		errors.append_array(actor.configure(actor_spec))
	if not errors.is_empty(): return
	_cache_release_sockets()
	camera=Camera3D.new()
	camera.name="DirectorCamera"
	camera.near=.08
	camera.far=180
	world.add_child(camera)
	camera.current=true
	effects=Node3D.new()
	effects.set_script(Effects)
	effects.name="TimelineEffects"
	world.add_child(effects)
	if not effects.configure(manifest,socket_at_time): errors.append("Film VFX rejected the cue manifest.")
	audio_player=AudioStreamPlayer.new()
	audio_player.name="FilmAudio"
	audio_player.stream=load(manifest.audio_mix_path)
	audio_volume=_read_saved_audio_volume()
	audio_player.volume_db=-80.0 if audio_volume<=0.0 else -2.0+linear_to_db(audio_volume)
	add_child(audio_player)

func _read_saved_audio_volume() -> float:
	var config:=ConfigFile.new()
	if config.load(AUDIO_SETTINGS_PATH)!=OK: return 0.7
	var value=config.get_value("audio","volume",0.7)
	if not _number(value): return 0.7
	return clampf(float(value),0.0,1.0)

func _play_audio_at_current_time() -> void:
	# A zero user setting must be silent, not merely an attenuated active stream.
	if capture_mode or not playing or audio_volume<=0.0:
		audio_player.stop()
		audio_player.stream_paused=true
		return
	audio_player.stream_paused=false
	audio_player.play(current_time)

func _cache_release_sockets() -> void:
	release_sockets.clear()
	for cue in manifest.cues:
		if cue.type!="projectile" or not actors.has(cue.actor_id): continue
		var actor: Node3D=actors[cue.actor_id]
		var motion:=_motion(cue.actor_id,cue.t_seconds)
		actor.position=motion.position
		actor.rotation=Vector3(0,motion.yaw,0)
		var selection:=_selection(cue.actor_id,cue.t_seconds)
		actor.sample(selection.clip,selection.phase,selection.prior,1.0,selection.blend)
		for socket_name in ["bow","chest","root"]:
			release_sockets["%s:%s:%.6f" % [cue.actor_id,socket_name,cue.t_seconds]]=actor.socket(socket_name)

func socket_at_time(actor_id: String, socket_name: String, time: float) -> Vector3:
	var key:="%s:%s:%.6f" % [actor_id,socket_name,time]
	if release_sockets.has(key): return release_sockets[key]
	# No arbitrary-time skeleton mutation is allowed during effect sampling.
	# Uncached sockets are deliberately invalid so VFX uses its authored vector.
	return Vector3(INF,INF,INF)

func _selection(actor_id: String, time: float) -> Dictionary:
	var chosen: Dictionary={}
	var previous: Dictionary={}
	for action in manifest.actions:
		if action.actor_id!=actor_id: continue
		var start: float=action.t_seconds
		var end: float=start+action.duration_seconds
		if time>=start and (time<end or (is_equal_approx(time,duration) and is_equal_approx(end,duration))):
			chosen=action
			break
		if end<=time: previous=action
	if chosen.is_empty(): return {"id":"ready-gap","clip":"ready","phase":0.0,"prior":"","blend":1.0}
	var local: float=time-chosen.t_seconds
	var blend_length: float=maxf(chosen.get("blend_in_seconds",.12),previous.get("blend_out_seconds",0))
	var blend:=smoothstep(0,maxf(blend_length,.00001),local)
	return {"id":chosen.id,"clip":chosen.clip_id,"phase":clampf(local/maxf(chosen.duration_seconds,.00001),0,1),"prior":previous.get("clip_id","") if local<blend_length else "","blend":blend}

func _motion(actor_id: String, time: float) -> Dictionary:
	for track in manifest.motion_tracks:
		if track.actor_id!=actor_id or track.keys.is_empty(): continue
		var left: Dictionary=track.keys[0]
		var right: Dictionary=track.keys[-1]
		for key in track.keys:
			if key.t_seconds<=time: left=key
			if key.t_seconds>=time:
				right=key
				break
		var fraction: float=clampf((time-left.t_seconds)/maxf(right.t_seconds-left.t_seconds,.00001),0,1)
		return {"position":_v(left.position).lerp(_v(right.position),fraction),"yaw":lerp_angle(deg_to_rad(left.yaw_degrees),deg_to_rad(right.yaw_degrees),fraction)}
	for actor in manifest.actors:
		if actor.id==actor_id: return {"position":_v(actor.position),"yaw":deg_to_rad(actor.yaw_degrees)}
	return {"position":Vector3.ZERO,"yaw":0.0}

func _sample_camera(time: float) -> void:
	var selected: Dictionary=manifest.cameras[0]
	var previous: Dictionary=selected
	for candidate in manifest.cameras:
		if candidate.t_seconds>time: break
		previous=selected
		selected=candidate
	var blend_seconds: float=selected.get("blend_seconds",0)
	var weight:=1.0 if blend_seconds<=0 else smoothstep(0,blend_seconds,time-selected.t_seconds)
	if reduced_motion:
		selected=manifest.cameras[0]
		previous=selected
		weight=1
	camera.position=_v(previous.position).lerp(_v(selected.position),weight)
	var target:=_v(previous.look_at).lerp(_v(selected.look_at),weight)
	camera.look_at(target,Vector3.UP)
	camera.fov=lerpf(previous.get("fov",50),selected.get("fov",50),weight)
	active_camera=selected.id

func sample_time(time: float, for_capture: bool=false) -> Dictionary:
	if not ready_to_play: return get_diagnostics()
	if not is_finite(time):
		errors.append("Cannot sample nonfinite film time.")
		return get_diagnostics()
	capture_mode=for_capture
	if capture_mode:
		playing=false
		audio_player.stop()
	controls.visible=not capture_mode
	current_time=clampf(time,0,duration)
	active_actions.clear()
	for actor_id in actors:
		var actor: Node3D=actors[actor_id]
		var motion:=_motion(actor_id,current_time)
		actor.position=motion.position
		actor.rotation=Vector3(0,motion.yaw,0)
		var selection:=_selection(actor_id,current_time)
		actor.sample(selection.clip,selection.phase,selection.prior,1.0,selection.blend)
		active_actions[actor_id]=selection.id
	_sample_camera(current_time)
	effects.sample(current_time)
	visual_health.clear()
	for actor in manifest.actors: visual_health[actor.id]=actor.get("visual_health",100)
	last_receipt=""
	for receipt in manifest.visual_receipts:
		if receipt.t_seconds<=current_time:
			visual_health[receipt.target_id]=receipt.health_after
			if current_time-receipt.t_seconds<1.4: last_receipt=String(receipt.outcome).to_upper()
	caption_label.text=""
	for caption in manifest.captions:
		if current_time>=caption.t_seconds and (current_time<caption.end_seconds or (current_time==duration and caption.end_seconds==duration)): caption_label.text=caption.text
	caption_panel.visible=captions_enabled and not caption_label.text.is_empty()
	caption_panel.offset_top=-78 if capture_mode else -232
	caption_panel.offset_bottom=-24 if capture_mode else -152
	receipt_label.text="RAMA  %d     ·     RAVANA  %d     %s" % [visual_health.get("rama",100),visual_health.get("ravana",100),last_receipt]
	timeline_slider.set_value_no_signal(current_time)
	time_label.text="%04.1f / %02d s" % [current_time,int(duration)]
	if current_time>=duration:
		playing=false
		audio_player.stop()
	play_button.text="Pause" if playing else "Play"
	return get_diagnostics()

func _process(delta: float) -> void:
	if ready_to_play and playing and not capture_mode: sample_time(current_time+delta,false)

func set_playing(value: bool) -> void:
	if not ready_to_play: return
	capture_mode=false
	controls.visible=true
	if value and current_time>=duration: sample_time(0,false)
	playing=value
	if value: _play_audio_at_current_time()
	else: audio_player.stream_paused=true
	play_button.text="Pause" if playing else "Play"

func seek(time: float) -> void:
	if not ready_to_play: return
	sample_time(time,false)
	if playing:
		_play_audio_at_current_time()
	else:
		audio_player.stop()
		audio_player.stream_paused=true

func replay() -> void:
	if not ready_to_play: return
	sample_time(0,false)
	set_playing(true)

func set_accessibility(flash: bool, motion: bool) -> void:
	reduced_flash=flash
	reduced_motion=motion
	if reduced_flash_button: reduced_flash_button.set_pressed_no_signal(flash)
	if reduced_motion_button: reduced_motion_button.set_pressed_no_signal(motion)
	if effects: effects.set_accessibility(flash,motion)
	if ready_to_play: sample_time(current_time,capture_mode)

func set_captions(value: bool) -> void:
	captions_enabled=value
	if ready_to_play: sample_time(current_time,capture_mode)

func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode==KEY_SPACE:
			set_playing(not playing)
			get_viewport().set_input_as_handled()
		elif event.physical_keycode==KEY_ESCAPE: return_to_courtyard()
		elif event.physical_keycode==KEY_LEFT: seek(current_time-1)
		elif event.physical_keycode==KEY_RIGHT: seek(current_time+1)

func _panel() -> StyleBoxFlat:
	var style:=StyleBoxFlat.new()
	style.bg_color=Color(.018,.035,.052,.94)
	style.border_color=Color(.66,.56,.35,.5)
	style.set_border_width_all(1)
	style.set_corner_radius_all(10)
	style.content_margin_left=18
	style.content_margin_right=18
	style.content_margin_top=12
	style.content_margin_bottom=12
	return style

func _label(text: String, size_: int=16) -> Label:
	var label:=Label.new()
	label.text=text
	label.add_theme_font_size_override("font_size",size_)
	label.add_theme_color_override("font_color",Color("f3e7cc"))
	return label

func _button(parent: Node, name_: String, text: String, callback: Callable) -> Button:
	var button:=Button.new()
	button.name=name_
	button.text=text
	button.custom_minimum_size=Vector2(90,38)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button

func _build_ui() -> void:
	ui=CanvasLayer.new()
	ui.name="FilmInterface"
	add_child(ui)
	var title:=PanelContainer.new()
	title.name="FilmTitle"
	title.add_theme_stylebox_override("panel",_panel())
	title.position=Vector2(24,20)
	ui.add_child(title)
	var heading:=VBoxContainer.new()
	title.add_child(heading)
	heading.add_child(_label("YUGA  /  CONFLUENCE",20))
	heading.add_child(_label("A DUEL OF TIMING  ·  ORIGINAL SCRIPTED FILM",12))
	receipt_label=_label("RAMA  100     ·     RAVANA  100",12)
	heading.add_child(receipt_label)
	controls=PanelContainer.new()
	controls.name="FilmControls"
	ui.add_child(controls)
	controls.add_theme_stylebox_override("panel",_panel())
	controls.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	controls.offset_left=24
	controls.offset_right=-24
	controls.offset_top=-136
	controls.offset_bottom=-20
	var rows:=VBoxContainer.new()
	controls.add_child(rows)
	var line:=HBoxContainer.new()
	line.add_theme_constant_override("separation",10)
	rows.add_child(line)
	play_button=_button(line,"FilmPlayPause","Play",func():set_playing(not playing))
	_button(line,"FilmReplay","Replay",replay)
	_button(line,"FilmReturn","Courtyard",return_to_courtyard)
	time_label=_label("00.0 / 24 s",14)
	time_label.size_flags_horizontal=Control.SIZE_EXPAND_FILL
	time_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_RIGHT
	line.add_child(time_label)
	var accessibility:=HBoxContainer.new()
	accessibility.add_theme_constant_override("separation",12)
	rows.add_child(accessibility)
	reduced_flash_button=CheckButton.new()
	reduced_flash_button.name="FilmReducedEffects"
	reduced_flash_button.text="Reduced flashes"
	reduced_flash_button.button_pressed=true
	reduced_flash_button.toggled.connect(func(value: bool):set_accessibility(value,reduced_motion))
	accessibility.add_child(reduced_flash_button)
	reduced_motion_button=CheckButton.new()
	reduced_motion_button.name="FilmReducedMotion"
	reduced_motion_button.text="Static camera"
	reduced_motion_button.toggled.connect(func(value: bool):set_accessibility(reduced_flash,value))
	accessibility.add_child(reduced_motion_button)
	var captions:=CheckButton.new()
	captions.name="FilmCaptions"
	captions.text="Captions"
	captions.button_pressed=true
	captions.toggled.connect(set_captions)
	accessibility.add_child(captions)
	timeline_slider=HSlider.new()
	timeline_slider.name="FilmTimeline"
	timeline_slider.step=.01
	timeline_slider.max_value=24
	timeline_slider.value_changed.connect(seek)
	rows.add_child(timeline_slider)
	caption_panel=PanelContainer.new()
	caption_panel.name="CaptionPanel"
	ui.add_child(caption_panel)
	caption_panel.add_theme_stylebox_override("panel",_panel())
	caption_panel.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_WIDE)
	caption_panel.offset_left=90
	caption_panel.offset_right=-90
	caption_panel.offset_top=-232
	caption_panel.offset_bottom=-152
	caption_label=_label("",19)
	caption_label.horizontal_alignment=HORIZONTAL_ALIGNMENT_CENTER
	caption_label.vertical_alignment=VERTICAL_ALIGNMENT_CENTER
	caption_label.autowrap_mode=TextServer.AUTOWRAP_WORD_SMART
	caption_panel.add_child(caption_label)

func _show_error() -> void:
	playing=false
	caption_label.text="Film cannot start: "+"; ".join(errors)
	caption_panel.visible=true
	play_button.disabled=true
	timeline_slider.editable=false
	push_error("YUGA_COMBAT_FILM: "+"; ".join(errors))

func get_diagnostics() -> Dictionary:
	var actor_states:={}
	var finite:=true
	for id in actors:
		actor_states[id]=actors[id].snapshot(false)
		finite=finite and actor_states[id].finite
	var effect_state: Dictionary=effects.diagnostics() if effects else {}
	if effect_state.has("state"):
		effect_state.state_sha256=JSON.stringify(effect_state.state).sha256_text()
		effect_state.erase("state")
	return {"ready":ready_to_play,"errors":errors.duplicate(),"time":current_time,"duration":duration,"playing":playing,"capture_mode":capture_mode,"audio":{"configured_volume":audio_volume,"muted":audio_volume<=0.0,"playing":audio_player.playing if audio_player else false,"paused":audio_player.stream_paused if audio_player else true},"actors":actor_states,"active_actions":active_actions.duplicate(),"finite":finite and (camera.global_transform.is_finite() if camera else true),"camera":{"id":active_camera,"position":[camera.position.x,camera.position.y,camera.position.z],"rotation":[camera.rotation.x,camera.rotation.y,camera.rotation.z],"fov":camera.fov} if camera else {},"effects":effect_state,"visual_health":visual_health.duplicate(),"caption":caption_label.text if caption_label else "","receipt":last_receipt,"reduced_flash":reduced_flash,"reduced_motion":reduced_motion,"scope":"Scripted cinematic; visual receipts are not authoritative combat."}

func get_state() -> Dictionary:
	return get_diagnostics()

func get_build_report() -> Dictionary:
	return get_diagnostics()

func get_actor_diagnostics(actor_id: String, detailed: bool=true) -> Dictionary:
	return actors[actor_id].snapshot(detailed) if actors.has(actor_id) else {}

func return_to_courtyard() -> void:
	playing=false
	if audio_player: audio_player.stop()
	get_tree().paused=false
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
	get_tree().change_scene_to_file("res://scenes/courtyard.tscn")

func _exit_tree() -> void:
	if audio_player:
		audio_player.stop()
		audio_player.stream=null
	Input.mouse_mode=Input.MOUSE_MODE_VISIBLE
