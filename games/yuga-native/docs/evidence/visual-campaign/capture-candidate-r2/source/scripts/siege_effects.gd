extends Node3D
## Original, bounded presentation for committed offline siege attacks. The army
## owns targeting, cancellation, damage and impact time; these meshes never hit.
const MAX_EVENTS := 32
const MAX_VOICES := 6
const HISTORY_CAP := 64
const DEFAULT_VOLUME := 0.35
const CUE_GAIN_DB := -12.0
const IMPACT_LIFETIME := 0.48
const HAZARD_SEGMENTS := 12
const HAZARD_COVERAGE := 0.58
const ROLES := {"cannon_cart":"cannon", "royal_chariot":"chariot"}
const AUDIO_BASE := "res://assets/audio/siege/"
const CUE_NAMES := ["cannon_windup", "cannon_impact", "chariot_windup", "chariot_impact"]

var volume := DEFAULT_VOLUME
var suspended := false
var _ready_complete := false
var _effects: Array[Dictionary] = []
var _voices: Array[AudioStreamPlayer3D] = []
var _voice_started: Array[int] = []
var _voice_priority: Array[int] = []
var _voice_ids: Array[int] = []
var _resume_positions: Array[float] = []
var _streams: Dictionary = {}
var _last_cue: Dictionary = {}
var _terminal_ids: Array[int] = []
var _latest_id := 0
var _accepted := 0
var _rejected := 0
var _cancelled := 0
var _played := 0
var _dropped_audio := 0
var _peak_events := 0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	for cue: String in CUE_NAMES:
		_streams[cue] = load(AUDIO_BASE + cue + ".wav") as AudioStreamWAV
	for index in range(MAX_VOICES):
		var voice := AudioStreamPlayer3D.new()
		voice.name = "SiegeCue%d" % index
		voice.max_distance = 75.0
		voice.unit_size = 2.5
		voice.max_db = CUE_GAIN_DB
		voice.panning_strength = 0.5
		voice.attenuation_filter_cutoff_hz = 7500.0
		add_child(voice)
		_voices.append(voice)
		_voice_started.append(0)
		_voice_priority.append(0)
		_voice_ids.append(0)
		_resume_positions.append(-1.0)
	_ready_complete = true
	_sync_audio()

func configure(value: float) -> void:
	set_volume(value)

func set_volume(value: float) -> void:
	volume = clampf(value, 0.0, 1.0) if is_finite(value) else DEFAULT_VOLUME
	if volume == 0.0:
		for index in range(_voices.size()):
			_voices[index].stop()
			_resume_positions[index] = -1.0
	_sync_audio()

func set_suspended(value: bool) -> void:
	suspended = value
	_sync_audio()

func _frozen() -> bool:
	return suspended or not is_inside_tree() or get_tree().paused

func _sync_audio() -> void:
	if not _ready_complete: return
	var gain := linear_to_db(volume) + CUE_GAIN_DB if volume > 0.0 else -80.0
	for index in range(_voices.size()):
		var voice := _voices[index]
		voice.volume_db = gain
		# AudioStreamPlayer3D queues play until a physics callback. Setting only
		# stream_paused can miss that pending start in the same tick. Retaining
		# position and stopping explicitly handles both pending and mixed voices.
		if _frozen():
			if voice.playing and _resume_positions[index] < 0.0:
				_resume_positions[index] = voice.get_playback_position()
				voice.stop()
		elif _resume_positions[index] >= 0.0:
			if volume > 0.0 and voice.stream:
				voice.stream_paused = false
				voice.play(_resume_positions[index])
			_resume_positions[index] = -1.0

func _notification(what: int) -> void:
	if what == NOTIFICATION_PAUSED or what == NOTIFICATION_UNPAUSED:
		_sync_audio()

func _number(value: Variant) -> bool:
	return typeof(value) in [TYPE_INT, TYPE_FLOAT] and is_finite(float(value))

func _valid_event(event: Dictionary) -> bool:
	if event.size() > 10: return false
	for key in event:
		if key not in ["kind","id","role","team","origin","target","delay","radius","damage","cancelled"]:
			return false
	if typeof(event.get("kind")) != TYPE_STRING or event.kind not in ["windup","impact"]: return false
	if typeof(event.get("id")) != TYPE_INT or event.id <= 0 or event.id > 2147483647: return false
	if typeof(event.get("role")) != TYPE_STRING or not ROLES.has(event.role): return false
	if typeof(event.get("team")) != TYPE_STRING or event.team not in ["sun","moon"]: return false
	for key in ["origin","target"]:
		if typeof(event.get(key)) != TYPE_VECTOR3: return false
		var point: Vector3 = event[key]
		if not point.is_finite() or absf(point.x) > 10000 or absf(point.y) > 1000 or absf(point.z) > 10000: return false
	if event.origin.distance_to(event.target) > 500.0: return false
	# Ground-target contract: the current offline army snapshots a lane-floor
	# position. Elevated targets require a separately agreed support-surface API.
	if absf(event.target.y) > 0.01: return false
	for key in ["delay","radius","damage"]:
		if not _number(event.get(key)): return false
	if event.radius < 0.1 or event.radius > 20.0 or event.damage < 0.0 or event.damage > 100000.0: return false
	if event.kind == "windup" and (event.delay < 0.05 or event.delay > 10.0): return false
	if event.kind == "impact" and event.delay != 0.0: return false
	if event.has("cancelled"):
		if typeof(event.cancelled) != TYPE_BOOL: return false
		if event.cancelled and (event.kind != "impact" or event.damage != 0.0): return false
	return true

func handle_event(event: Dictionary) -> void:
	# Reset remains valid while paused so world/menu cleanup is idempotent.
	if typeof(event.get("kind")) == TYPE_STRING and event.kind == "reset":
		if not _valid_reset(event):
			_rejected += 1
			return
		clear()
		return
	if not _ready_complete or _frozen() or not _valid_event(event):
		_rejected += 1
		return
	var identity: int = event.id
	var active := _find_id(identity)
	if _terminal_ids.has(identity) or (identity < _latest_id - HISTORY_CAP and active < 0):
		_rejected += 1
		return
	if event.kind == "windup" and active >= 0:
		_rejected += 1
		return
	_latest_id = maxi(_latest_id, identity)
	if event.kind == "impact":
		if active >= 0: _remove_at(active)
		_stop_attack_voice(identity)
		_remember_terminal(identity)
		if event.get("cancelled", false):
			_cancelled += 1
			_accepted += 1
			return
	if _effects.size() >= MAX_EVENTS:
		# Preserve committed danger warnings before decorative impact aftermath.
		var disposable := -1
		for index in range(_effects.size()):
			if _effects[index].kind == "impact":
				disposable = index
				break
		if disposable < 0:
			_rejected += 1
			return
		_remove_at(disposable)
	var effect := _make_effect(event)
	_effects.append(effect)
	_peak_events = maxi(_peak_events, _effects.size())
	_accepted += 1
	var cue: String = ROLES[event.role] + "_" + event.kind
	_play_cue(cue, event.origin if event.kind == "windup" else event.target, 1 if event.kind == "windup" else 2, identity)

func _valid_reset(event: Dictionary) -> bool:
	if typeof(event.get("id")) != TYPE_INT or event.id != 0: return false
	for key in event:
		if key not in ["kind","id","role","team","origin","target","delay","radius","damage"]: return false
	for key in ["role","team"]:
		if event.has(key) and (typeof(event[key]) != TYPE_STRING or event[key] != ""): return false
	for key in ["origin","target"]:
		if event.has(key) and (typeof(event[key]) != TYPE_VECTOR3 or event[key] != Vector3.ZERO): return false
	for key in ["delay","radius","damage"]:
		if event.has(key) and (not _number(event[key]) or event[key] != 0.0): return false
	return true

func _find_id(identity: int) -> int:
	for index in range(_effects.size()):
		if _effects[index].id == identity: return index
	return -1

func _remember_terminal(identity: int) -> void:
	_terminal_ids.append(identity)
	if _terminal_ids.size() > HISTORY_CAP: _terminal_ids.pop_front()

func _material(team: String) -> StandardMaterial3D:
	var material := StandardMaterial3D.new()
	material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	material.cull_mode = BaseMaterial3D.CULL_DISABLED
	material.vertex_color_use_as_albedo = true
	material.albedo_color = Color("efad52") if team == "sun" else Color("70c5d5")
	# Unshaded geometry remains visible at night without emissive bloom/flash.
	material.emission_enabled = false
	return material

func _mesh(parent: Node3D, shape: Mesh, material: Material, label: String) -> MeshInstance3D:
	var mesh := MeshInstance3D.new()
	mesh.name = label
	mesh.mesh = shape
	mesh.material_override = material
	mesh.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(mesh)
	return mesh

func _triangle(geometry: ImmediateMesh, a: Vector3, b: Vector3, c: Vector3, color: Color) -> void:
	geometry.surface_set_color(color)
	geometry.surface_add_vertex(a)
	geometry.surface_add_vertex(b)
	geometry.surface_add_vertex(c)

func _quad(geometry: ImmediateMesh, a: Vector3, b: Vector3, c: Vector3, d: Vector3, color: Color) -> void:
	_triangle(geometry,a,b,c,color)
	_triangle(geometry,a,c,d,color)

func _flat_point(angle: float, radius: float, height := 0.0) -> Vector3:
	return Vector3(sin(angle)*radius,height,cos(angle)*radius)

func _hazard_footprint(radius: float) -> ImmediateMesh:
	# Twelve broken boundary ribbons expose the true maximum radius, while a
	# dark underprint keeps them distinct from bright decorative map rings.
	# Every vertex stays inside the declared radius; no filled ground disk.
	var geometry := ImmediateMesh.new()
	geometry.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var width := clampf(radius*0.085,0.008,0.28)
	for segment in range(HAZARD_SEGMENTS):
		var center := TAU*float(segment)/HAZARD_SEGMENTS
		var half_span := PI/HAZARD_SEGMENTS*HAZARD_COVERAGE
		for step in range(4):
			var begin := center-half_span+2.0*half_span*float(step)/4.0
			var end := center-half_span+2.0*half_span*float(step+1)/4.0
			_quad(geometry,_flat_point(begin,radius),_flat_point(end,radius),
				_flat_point(end,radius-width),_flat_point(begin,radius-width),Color(0.045,0.06,0.075,1.0))
			_quad(geometry,_flat_point(begin,radius-width*.18,.003),_flat_point(end,radius-width*.18,.003),
				_flat_point(end,radius-width*.72,.003),_flat_point(begin,radius-width*.72,.003),Color.WHITE)
	# The broad source-facing notch points from the firing unit toward target.
	# It is wholly inside the footprint and does not imply a second hit area.
	_triangle(geometry,Vector3(0,.006,radius*.66),Vector3(-radius*.12,.006,radius*.88),Vector3(radius*.12,.006,radius*.88),Color(0.045,0.06,0.075,1.0))
	_triangle(geometry,Vector3(0,.009,radius*.72),Vector3(-radius*.07,.009,radius*.85),Vector3(radius*.07,.009,radius*.85),Color.WHITE)
	geometry.surface_end()
	return geometry

func _glyph_bar(geometry: ImmediateMesh, a: Vector3, b: Vector3, thickness: float) -> void:
	var along := (b-a).normalized()
	var side := Vector3(-along.z,0,along.x)*thickness*.5
	_quad(geometry,a-side,b-side,b+side,a+side,Color(0.045,0.06,0.075,1.0))
	var rise := Vector3.UP*.003
	side *= .48
	_quad(geometry,a-side+rise,b-side+rise,b+side+rise,a+side+rise,Color.WHITE)

func _team_glyph(team: String, radius: float, outward := false) -> ImmediateMesh:
	var geometry := ImmediateMesh.new()
	geometry.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var count := 8 if team == "sun" else 4
	for index in range(count):
		var angle := TAU * float(index) / count
		var radial := Vector3(sin(angle),0,cos(angle))
		var tangent := Vector3(cos(angle),0,-sin(angle))
		var tip := radius*(.84 if outward else .60)
		var back := radius*(.61 if outward else .83)
		if team == "moon":
			# Four squared brackets remain distinct from Sun's eight arrowheads
			# even when the owner colors coincide or the scene is desaturated.
			var half_span := tangent*radius*.12
			_glyph_bar(geometry,radial*tip-half_span,radial*tip+half_span,radius*.065)
			_glyph_bar(geometry,radial*tip-half_span,radial*back-half_span,radius*.065)
			_glyph_bar(geometry,radial*tip+half_span,radial*back+half_span,radius*.065)
		else:
			_triangle(geometry,radial*tip,radial*back+tangent*radius*.10,radial*back-tangent*radius*.10,Color(0.045,0.06,0.075,1.0))
			var center := (tip+back)*.5
			_triangle(geometry,radial*lerpf(center,tip,.67)+Vector3.UP*.003,
				radial*lerpf(center,back,.67)+tangent*radius*.055+Vector3.UP*.003,
				radial*lerpf(center,back,.67)-tangent*radius*.055+Vector3.UP*.003,Color.WHITE)
	geometry.surface_end()
	return geometry

func _make_effect(event: Dictionary) -> Dictionary:
	var body := Node3D.new()
	body.name = "Siege%s%d" % [event.kind.capitalize(), event.id]
	add_child(body)
	body.top_level = true
	body.global_position = event.target + Vector3.UP * 0.055
	var source_direction: Vector3 = event.origin-event.target
	source_direction.y = 0.0
	if source_direction.length_squared() > .000001:
		body.rotation.y = atan2(source_direction.x,source_direction.z)
	var material := _material(event.team)
	# Retain the internal ring/glyph slots and node budget for existing consumers.
	var ring := _mesh(body, _hazard_footprint(event.radius), material, "SegmentedTroopImpactBoundary")
	ring.position.y = 0.0 if event.team=="sun" else .008
	var glyph := _mesh(body, _team_glyph(event.team, event.radius, event.kind=="impact"), material, "InwardCountdown" if event.kind=="windup" else "OutwardAftermath")
	glyph.position.y = .018 if event.team=="sun" else .026
	var effect := {"id":event.id,"kind":event.kind,"role":event.role,"team":event.team,
		"origin":event.origin,"target":event.target,"delay":float(event.delay),"radius":float(event.radius),
		"age":0.0,"ttl":float(event.delay)+0.35 if event.kind=="windup" else IMPACT_LIFETIME,
		"node":body,"ring":ring,"glyph":glyph,"material":material}
	if event.kind == "windup":
		var sphere := SphereMesh.new()
		sphere.radius = 0.17
		sphere.height = 0.34
		sphere.radial_segments = 10
		sphere.rings = 5
		effect.charge = _mesh(body, sphere, material, "BarrelCharge")
		effect.charge.global_position = event.origin
		effect.projectile = _mesh(body, sphere, material, "PresentationProjectile")
		effect.projectile.visible = false
	_update_effect(effect)
	return effect

static func arc_position(origin: Vector3, target: Vector3, phase: float) -> Vector3:
	var t := clampf(phase, 0.0, 1.0)
	var height := clampf(origin.distance_to(target) * 0.12, 1.0, 8.0)
	return origin.lerp(target, t) + Vector3.UP * (4.0 * t * (1.0 - t) * height)

func _update_effect(effect: Dictionary) -> void:
	var color: Color = effect.material.albedo_color
	if effect.kind == "windup":
		var phase := clampf(effect.age / effect.delay, 0.0, 1.0)
		color.a = 0.88
		# Boundary remains fixed. Only the inner team-shaped ticks converge,
		# communicating countdown without shrinking the actual affected area.
		effect.glyph.scale = Vector3.ONE*lerpf(1.0,.35,phase)
		effect.charge.scale = Vector3.ONE * (0.7 + phase * 0.9)
		var can_arc: bool = effect.delay >= 0.22
		effect.charge.visible = not can_arc or phase < 0.4
		effect.projectile.visible = can_arc and phase >= 0.4 and effect.age <= effect.delay
		if effect.projectile.visible:
			effect.projectile.global_position = arc_position(effect.origin, effect.target, (phase-0.4)/0.6)
	else:
		var phase := clampf(effect.age / IMPACT_LIFETIME, 0.0, 1.0)
		var expansion := 0.28 + 0.72 * (1.0 - pow(1.0-phase, 2.0))
		effect.glyph.scale = Vector3.ONE * expansion
		color.a = (1.0-phase) * 0.62
	effect.material.albedo_color = color

func _process(delta: float) -> void:
	if _frozen() or not is_finite(delta) or delta < 0.0: return
	for index in range(_effects.size()-1, -1, -1):
		var effect := _effects[index]
		effect.age += delta
		if effect.age >= effect.ttl:
			_remove_at(index)
		else:
			_update_effect(effect)

func _play_cue(cue: String, position: Vector3, priority: int, identity: int) -> void:
	if volume <= 0.0 or _frozen() or not _streams.get(cue): return
	var now := Time.get_ticks_usec()
	if now - int(_last_cue.get(cue, -10000000)) < 55000:
		_dropped_audio += 1
		return
	var slot := -1
	for index in range(_voices.size()):
		if not _voices[index].playing:
			slot = index
			break
	if slot < 0:
		var oldest := 9223372036854775807
		for index in range(_voices.size()):
			if _voice_priority[index] <= priority and _voice_started[index] < oldest:
				slot = index
				oldest = _voice_started[index]
	if slot < 0:
		_dropped_audio += 1
		return
	var voice := _voices[slot]
	voice.stop()
	voice.stream = _streams[cue]
	voice.global_position = position
	voice.stream_paused = false
	voice.play()
	_voice_started[slot] = now
	_voice_priority[slot] = priority
	_voice_ids[slot] = identity
	_resume_positions[slot] = -1.0
	_last_cue[cue] = now
	_played += 1

func _stop_attack_voice(identity: int) -> void:
	for index in range(_voices.size()):
		if _voice_ids[index] == identity:
			_voices[index].stop()
			_voice_ids[index] = 0
			_resume_positions[index] = -1.0

func _remove_at(index: int) -> void:
	var body: Node3D = _effects[index].node
	_effects.remove_at(index)
	# Only owned presentation nodes; immediate removal bounds same-frame floods.
	remove_child(body)
	body.free()

func clear() -> void:
	for index in range(_effects.size()-1, -1, -1): _remove_at(index)
	for index in range(_voices.size()):
		var voice := _voices[index]
		voice.stop()
		voice.stream = null
		_resume_positions[index] = -1.0
		_voice_ids[index] = 0
	_terminal_ids.clear()
	_latest_id = 0
	_last_cue.clear()

func report() -> Dictionary:
	var playing := 0
	var paused_voices := 0
	var windups := 0
	var impacts := 0
	var states: Array[Dictionary] = []
	for index in range(_voices.size()):
		var voice := _voices[index]
		if voice.playing: playing += 1
		if _resume_positions[index] >= 0.0: paused_voices += 1
	for effect in _effects:
		if effect.kind == "windup": windups += 1
		else: impacts += 1
		states.append({"id":effect.id,"kind":effect.kind,"role":effect.role,"team":effect.team,
			"age":effect.age,"radius":effect.radius,"target":effect.target,"origin":effect.origin,
			"glyph_count":8 if effect.team=="sun" else 4,
			"projectile_visible":effect.kind=="windup" and effect.projectile.visible,
			"projectile_position":effect.projectile.global_position if effect.kind=="windup" else effect.target})
	return {"volume":volume,"muted":volume==0.0,"suspended":suspended,"tree_paused":is_inside_tree() and get_tree().paused,
		"active_events":_effects.size(),"windups":windups,"impacts":impacts,"peak_events":_peak_events,
		"voice_pool":_voices.size(),"playing_voices":playing,"paused_voices":paused_voices,
		"accepted":_accepted,"rejected":_rejected,"cancelled":_cancelled,"played_cues":_played,
		"dropped_audio":_dropped_audio,"history_size":_terminal_ids.size(),"states":states}

func _exit_tree() -> void:
	clear()
