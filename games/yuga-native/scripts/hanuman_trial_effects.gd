extends Node3D
## Presentation uses the kit's locked geometry and accepted event order.
## The hit result, movement and timing remain owned by the practice controller.

const BOUNDARY := preload("res://shaders/rama_ability_boundary.gdshader")
const GroundField := preload("res://scripts/hanuman_ground_field.gd")
const RIBBON := preload("res://shaders/rama_ribbon.gdshader")
const PROFILES := "res://assets/design/hanuman-presentation.json"
const AUDIO_ROOT := "res://assets/audio/"
const MAX_CASTS := 6
const MAX_RECEIPTS := 8
const STAGES := ["begin", "release", "impact", "tick", "recovery", "end", "cancel", "reset"]

var _style: Dictionary = {}
var _casts: Dictionary = {}
var _voices: Array[AudioStreamPlayer3D] = []
var _ground_field: MultiMeshInstance3D
var _voice_index := 0
var _generation := -1
var _sequence := -1
var _high_cast := -1
var _reduced := false
var _suspended := false
var _volume := 0.42
var _accepted := 0
var _played := 0


func _ready() -> void:
	process_mode = Node.PROCESS_MODE_PAUSABLE
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(PROFILES))
	if raw is Dictionary:
		for id in raw:
			var entry: Variant = raw[id]
			if not entry is Dictionary or not entry.get("kind") in ["crescent", "ward", "wind", "ember", "mountain"]:
				continue
			var rise: Variant = entry.get("rise_m", 1.0)
			var gain: Variant = entry.get("impact_gain", 1.0)
			if not _number(rise, 0.1, 6.0) or not _number(gain, 0.0, 1.0):
				continue
			_style[id] = {
				"kind": entry.kind,
				"color": Color.from_string(str(entry.get("color", "")), Color.WHEAT),
				"accent": Color.from_string(str(entry.get("accent", "")), Color.CORAL),
				"stream": _stream(entry.get("audio", "")),
				"impact_stream": _stream(entry.get("impact_audio", "")),
				"impact_gain": float(gain),
				"rise_m": float(rise),
			}
	for index in 3:
		var voice := AudioStreamPlayer3D.new()
		voice.name = "AbilityVoice%d" % index
		voice.unit_size = 5.0
		voice.max_distance = 28.0
		add_child(voice)
		_voices.append(voice)
	_ground_field = GroundField.new()
	add_child(_ground_field, false, Node.INTERNAL_MODE_BACK)
	_ground_field.set_reduced(_reduced)


static func _stream(path: Variant) -> AudioStream:
	if not path is String or path.is_empty() or path.begins_with("/") or ".." in path:
		return null
	var resource_path := AUDIO_ROOT + String(path)
	return load(resource_path) as AudioStream if ResourceLoader.exists(resource_path) else null


func set_options(options: Dictionary) -> void:
	_reduced = options.get("reduced_effects", false) == true or options.get("reduced_motion", false) == true
	if is_instance_valid(_ground_field):
		_ground_field.set_reduced(_reduced)
	var volume: Variant = options.get("volume", _volume)
	if _number(volume, 0.0, 1.0):
		_volume = float(volume)
		for voice in _voices:
			if _volume == 0.0:
				voice.stop()
			else:
				voice.volume_db = linear_to_db(_volume * float(voice.get_meta("gain", 1.0)))


func set_suspended(value: bool) -> void:
	_suspended = value
	for voice in _voices:
		voice.stream_paused = value


static func _number(value: Variant, low: float, high: float) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and value >= low and value <= high


static func _point(value: Variant) -> bool:
	return value is Vector3 and value.is_finite() and value.length_squared() < 1_000_000


func consume_event(event: Dictionary) -> bool:
	var kind: String = str(event.get("kind", ""))
	if kind not in STAGES or event.get("schema") != 1 or event.get("hero_id") != "hanuman":
		return false
	for key in ["generation", "event_seq", "cast_id"]:
		if not event.get(key) is int or event[key] < 0:
			return false
	var generation: int = event.generation
	var sequence: int = event.event_seq
	var id: int = event.cast_id
	if generation < _generation or (generation == _generation and sequence <= _sequence):
		return false
	if generation > _generation and kind not in ["begin", "reset"]:
		return false
	if kind == "reset":
		if id != 0 or generation <= _generation:
			return false
		_clear()
		_generation = generation
		_sequence = sequence
		_accepted += 1
		return true
	var profile_id: String = str(event.get("ability_id", ""))
	if not _style.has(profile_id):
		return false
	if kind == "begin":
		if id == 0 or not _valid_geometry(event.get("geometry")) or not event.get("timing") is Dictionary:
			return false
		for field in ["windup_s", "travel_s", "recovery_s", "active_s"]:
			if not _number(event.timing.get(field), 0.0, 8.0):
				return false
		if generation > _generation:
			_clear()
			_generation = generation
		if id <= _high_cast or _casts.size() >= MAX_CASTS:
			return false
		_high_cast = id
		_casts[id] = _preview(event, _style[profile_id])
	else:
		if not _casts.has(id) or _casts[id].ability_id != profile_id:
			return false
		var cast: Dictionary = _casts[id]
		if kind == "release":
			if cast.released:
				return false
			cast.released = true
			cast.release_time = cast.age
			cast.flash = 0.0
			_build_release(cast)
			_play(cast.style.stream, cast.geometry.origin, id)
		elif kind == "impact":
			if not cast.released or cast.impacted:
				return false
			cast.impacted = true
			cast.flash = 0.0
			_build_impact(cast, event)
		elif kind == "tick":
			if not cast.impacted:
				return false
		elif kind == "recovery":
			if not cast.impacted or cast.recovered:
				return false
			cast.recovered = true
		else:
			if kind == "end" and not cast.recovered:
				return false
			_retire(id)
			if kind == "cancel":
				for voice in _voices:
					if voice.get_meta("cast_id", -1) == id:
						voice.stop()
	_sequence = sequence
	_accepted += 1
	return true


func _valid_geometry(geometry: Variant) -> bool:
	if not geometry is Dictionary or not geometry.get("kind") in ["sector", "disk", "movement"]:
		return false
	for key in ["center", "origin", "forward"]:
		if not _point(geometry.get(key)):
			return false
	var forward: Vector3 = geometry.forward
	if Vector2(forward.x, forward.z).length_squared() < 0.9:
		return false
	if geometry.kind == "sector":
		return _number(geometry.get("range_m"), 0.1, 24.0) and _number(geometry.get("half_angle_cos"), -1.0, 1.0)
	return geometry.kind == "movement" or _number(geometry.get("radius_m"), 0.1, 24.0)


func _preview(event: Dictionary, style: Dictionary) -> Dictionary:
	var geometry: Dictionary = event.geometry.duplicate()
	var group := Node3D.new()
	group.name = "Cue%d" % event.cast_id
	add_child(group)
	group.top_level = true
	group.global_position = geometry.origin if geometry.kind == "sector" else geometry.center
	group.rotation.y = atan2(geometry.forward.x, geometry.forward.z)
	var radius := _radius(geometry)
	var angle := _angle(geometry)
	var warning := _material(BOUNDARY, style.color, 0.78)
	_ring(group, warning, radius, minf(0.13, radius * 0.24), angle, 0.042)
	if geometry.kind == "sector":
		for side: float in [-1.0, 1.0]:
			var a := side * angle
			var inner := a - side * 0.011
			var vertices := PackedVector3Array([
				_polar(inner, 0.23, 0.043), _polar(a, 0.23, 0.043),
				_polar(inner, radius, 0.043), _polar(a, radius, 0.043),
			])
			_draw_strip(group, warning, vertices, PackedVector2Array([Vector2.ZERO, Vector2.DOWN, Vector2.RIGHT, Vector2.ONE]))
	var timing: Dictionary = event.timing
	return {
		"group": group, "style": style, "geometry": geometry, "warning": warning,
		"ability_id": event.ability_id, "ribbons": [], "age": 0.0, "released": false,
		"release_time": 0.0, "travel_s": float(timing.travel_s), "active_s": float(timing.active_s), "recovery_s": float(timing.recovery_s),
		"impacted": false, "recovered": false, "flash": 0.0,
		"ttl": float(timing.windup_s) + float(timing.travel_s) + float(timing.recovery_s) + clampf(float(timing.get("active_s", 0.0)), 0.0, 8.0) + 1.0,
	}


func _build_release(cast: Dictionary) -> void:
	var group: Node3D = cast.group
	var geometry: Dictionary = cast.geometry
	var radius := _radius(geometry)
	var angle := _angle(geometry)
	var style: Dictionary = cast.style
	var front := _material(RIBBON, style.color, 0.82)
	var edge := _material(RIBBON, style.accent, 0.58)
	cast.ribbons.append_array([front, edge])
	match style.kind:
		"ward":
			_ring(group, front, radius * 0.90, 0.25, angle, 0.085)
		"wind":
			var start := group.to_local(geometry.origin)
			for index in (1 if _reduced else 3):
				var drift := Vector3((float(index) - 1.0) * 0.20, 0.0, 0.0)
				var path: Array[Vector3] = []
				for point in 24:
					var t := float(point) / 23.0
					path.append(start.lerp(Vector3.ZERO, t) + drift + Vector3.UP * (0.10 + 1.15 * sin(PI * t)))
				_stroke(group, front, path, 0.09)
		"mountain":
			_ring(group, edge, radius * 0.72, 0.15, PI, 0.080)
			if not _reduced:
				_build_mountain_payload(cast, front, edge)
		"ember":
			_ring(group, front, radius * 0.97, 0.29, angle, 0.17)
			if not _reduced:
				_build_ember_field(cast, front, edge, radius, angle)
		_:
			_ring(group, front, radius * 0.96, minf(radius * 0.15, 0.29), angle, 0.23)
			if not _reduced:
				_ring(group, edge, radius * 0.81, 0.11, angle * 0.78, 0.38)


func _build_ember_field(cast: Dictionary, core: ShaderMaterial, accent: ShaderMaterial, radius: float, angle: float) -> void:
	var group: Node3D = cast.group
	var field := Node3D.new()
	field.name = "EmberField"
	group.add_child(field)
	# Use polar widths so both painted edges stay inside the authoritative fan.
	for index in 2:
		var material := core if index == 0 else accent
		var side := -1.0 if index == 0 else 1.0
		var vertices := PackedVector3Array()
		var uv := PackedVector2Array()
		for sample in 37:
			var t := float(sample) / 36.0
			var a := side * lerpf(-0.62, 0.69, t) * angle
			var envelope := sin(PI * t)
			var height := 0.08 + float(cast.style.rise_m) * envelope * (0.93 - 0.16 * index)
			var distance := radius * lerpf(0.12 + 0.06 * index, 0.88, t)
			var width := radius * (0.013 + 0.072 * envelope)
			vertices.append(_polar(a, distance - width, height * 0.73))
			vertices.append(_polar(a, distance + width, height))
			uv.append(Vector2(t, 0.0))
			uv.append(Vector2(t, 1.0))
		_draw_strip(field, material, vertices, uv)
	cast.decor = field


func _build_mountain_payload(cast: Dictionary, core: ShaderMaterial, accent: ShaderMaterial) -> void:
	var group: Node3D = cast.group
	var payload := Node3D.new()
	payload.name = "MountainPayload"
	group.add_child(payload)
	payload.position.y = cast.style.rise_m
	var width := _radius(cast.geometry) * 0.18
	# Two crossed ridge contours convey mass from either shoulder angle.
	for index in 2:
		var ridge := Node3D.new()
		payload.add_child(ridge)
		ridge.rotation.y = (float(index) + 0.32) * PI * 0.5
		_stroke(ridge, core, [Vector3(-width, -.18, 0.0), Vector3(-width * .52, .28, 0.0), Vector3(-width * .27, .18, 0.0),
			Vector3(width * .06, .85, 0.0), Vector3(width * .49, .19, 0.0), Vector3(width, -.18, 0.0)], .145, Vector3.FORWARD)
	_ring(payload, accent, width * 1.11, .23, PI, -.12)
	cast.payload = payload
	cast.decor = payload


func _build_impact(cast: Dictionary, event: Dictionary) -> void:
	var group: Node3D = cast.group
	var style: Dictionary = cast.style
	var material := _material(RIBBON, style.color, 0.90)
	cast.ribbons.append(material)
	if style.kind == "mountain":
		# The pulse uses the locked, ground-checked target. A movement receipt
		# is only a launch acceptance, so it never produces a landing burst here.
		_ring(group, material, _radius(cast.geometry) * 0.96, 0.16, PI, 0.075)
		if cast.has("payload"):
			cast.payload.hide()
		if not _reduced:
			_ring(group, material, _radius(cast.geometry) * 0.56, 0.09, PI, 0.105)
			_build_mountain_impact(cast, material)
		_play(style.impact_stream, cast.geometry.center, event.cast_id, style.impact_gain)
		_ground_field.stamp(event.cast_id, cast.geometry, float(cast.recovery_s), style.color)
	elif style.kind == "ember":
		_ground_field.stamp(event.cast_id, cast.geometry, float(cast.active_s), style.accent)
	var receipts: Variant = event.get("receipts", [])
	if not receipts is Array:
		return
	var played_ward := false
	for index in mini(receipts.size(), MAX_RECEIPTS):
		var receipt: Variant = receipts[index]
		if not receipt is Dictionary or not _point(receipt.get("position")):
			continue
		var pos := group.to_local(receipt.position)
		var kinds: Variant = receipt.get("effects")
		if style.kind == "ward" and kinds is Array and "shield" in kinds and _number(receipt.get("shield_after"), 0.1, 100.0):
			_build_shield_receipt(cast, pos, material)
			if not played_ward:
				_play(style.impact_stream, receipt.position, event.cast_id, style.impact_gain)
				played_ward = true
		elif not _reduced:
			var mark := pos + Vector3.UP * 0.65
			_stroke(group, material, [mark - Vector3(0.19, 0.26, 0.0), mark, mark + Vector3(0.16, 0.40, 0.0)], 0.09, Vector3.FORWARD)


func _build_mountain_impact(cast: Dictionary, material: ShaderMaterial) -> void:
	var group: Node3D = cast.group
	var spires := Node3D.new()
	spires.name = "MountainImpact"
	group.add_child(spires)
	var radius := _radius(cast.geometry)
	for index in 5:
		var axis := TAU * float(index) / 5.0
		var height := 0.9 + 0.21 * float(index % 3)
		_stroke(spires, material, [_polar(axis, 0.20, .07), _polar(axis + .09, radius * .22, height),
			_polar(axis + .16, radius * .43, .13)], .19, Vector3.FORWARD.rotated(Vector3.UP, axis))
	cast.decor = spires


func _build_shield_receipt(cast: Dictionary, pos: Vector3, material: ShaderMaterial) -> void:
	var group: Node3D = cast.group
	var ward := Node3D.new()
	ward.name = "ShieldReceipt"
	ward.position = pos
	group.add_child(ward, true)
	_ring(ward, material, 0.88, 0.16, PI, 0.06)
	if _reduced:
		return
	for index in 2:
		var turn := (float(index) - .5) * PI * .42
		var normal := Vector3.FORWARD.rotated(Vector3.UP, turn)
		var hex: Array[Vector3] = []
		for corner in 7:
			var theta := PI * float(corner) / 3.0
			var point := Vector3(sin(theta) * .57, 1.02 + cos(theta) * .65, -.58)
			hex.append(point.rotated(Vector3.UP, turn))
		_stroke(ward, material, hex, 0.09, normal)


func _process(delta: float) -> void:
	if _suspended:
		return
	_ground_field.advance(delta)
	for id in _casts.keys():
		var cast: Dictionary = _casts[id]
		cast.age += delta
		if cast.age > cast.ttl:
			_retire(id)
			continue
		if cast.released:
			cast.flash += delta
		if cast.has("decor"):
			cast.decor.visible = not _reduced and (not cast.has("payload") or cast.decor != cast.payload or not cast.impacted)
		if cast.has("payload") and not cast.impacted:
			var t := clampf((float(cast.age) - float(cast.release_time)) / maxf(float(cast.travel_s), 0.05), 0.0, .98)
			cast.payload.position.y = lerpf(float(cast.style.rise_m), .18, t * t)
			cast.payload.rotation.y = t * .72
		var fade := maxf(0.17, 1.0 - float(cast.flash) * 1.9)
		if cast.style.kind == "ember" and cast.impacted:
			fade = maxf(0.22, 1.0 - 0.8 * float(cast.flash) / maxf(float(cast.active_s), 0.05))
		for material: ShaderMaterial in cast.ribbons:
			material.set_shader_parameter("phase", cast.flash)
			material.set_shader_parameter("reduced_motion", _reduced)
			material.set_shader_parameter("opacity", float(material.get_meta("base_opacity")) * fade * (0.66 if _reduced else 0.94))


static func _radius(geometry: Dictionary) -> float:
	return float(geometry.get("range_m", 1.05)) if geometry.kind == "sector" else float(geometry.get("radius_m", 1.05))


static func _angle(geometry: Dictionary) -> float:
	return acos(float(geometry.half_angle_cos)) if geometry.kind == "sector" else PI


static func _material(shader: Shader, tint: Color, opacity: float) -> ShaderMaterial:
	var material := ShaderMaterial.new()
	material.shader = shader
	material.set_shader_parameter("tint", tint)
	material.set_shader_parameter("opacity", opacity)
	material.set_meta("base_opacity", opacity)
	if shader == RIBBON:
		material.set_shader_parameter("core_strength", 0.55)
		material.set_shader_parameter("luminous", 0.38)
	return material


static func _polar(angle: float, radius: float, height: float) -> Vector3:
	return Vector3(sin(angle) * radius, height, cos(angle) * radius)


static func _ring(parent: Node3D, material: Material, radius: float, width: float, angle: float, height: float) -> void:
	var vertices := PackedVector3Array()
	var uv := PackedVector2Array()
	for index in 65:
		var t := float(index) / 64.0
		var a := lerpf(-angle, angle, t)
		vertices.append(_polar(a, maxf(0.0, radius - width), height))
		vertices.append(_polar(a, radius, height))
		uv.append(Vector2(t, 0.0))
		uv.append(Vector2(t, 1.0))
	_draw_strip(parent, material, vertices, uv)


static func _stroke(parent: Node3D, material: Material, points: Array[Vector3], width: float, normal := Vector3.UP) -> void:
	var vertices := PackedVector3Array()
	var uv := PackedVector2Array()
	for index in points.size():
		var t := float(index) / float(points.size() - 1)
		var direction := points[mini(index + 1, points.size() - 1)] - points[maxi(0, index - 1)]
		var side := direction.cross(normal).normalized()
		if side.length_squared() < 0.1:
			side = Vector3.RIGHT
		var offset := side * (width * maxf(0.18, sin(PI * t)))
		vertices.append(points[index] - offset)
		vertices.append(points[index] + offset)
		uv.append(Vector2(t, 0.0))
		uv.append(Vector2(t, 1.0))
	_draw_strip(parent, material, vertices, uv)


static func _draw_strip(parent: Node3D, material: Material, vertices: PackedVector3Array, uv: PackedVector2Array) -> void:
	var indices := PackedInt32Array()
	for index in range(2, vertices.size(), 2):
		indices.append_array(PackedInt32Array([index - 2, index - 1, index, index, index - 1, index + 1]))
	var colors := PackedColorArray()
	colors.resize(vertices.size())
	colors.fill(Color.WHITE)
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_TEX_UV] = uv
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var shape := MeshInstance3D.new()
	shape.mesh = mesh
	shape.material_override = material
	shape.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(shape)


func _play(stream: AudioStream, position: Vector3, cast_id: int, gain := 1.0) -> void:
	if stream == null or _volume <= 0.0 or gain <= 0.0 or _suspended or _voices.is_empty():
		return
	var voice: AudioStreamPlayer3D = _voices[_voice_index]
	_voice_index = (_voice_index + 1) % _voices.size()
	voice.stop()
	voice.global_position = position
	voice.stream = stream
	voice.volume_db = linear_to_db(_volume * gain)
	voice.set_meta("cast_id", cast_id)
	voice.set_meta("gain", gain)
	voice.play()
	_played += 1


func _retire(id: int) -> void:
	_ground_field.retire(id)
	var group: Node3D = _casts[id].group
	group.hide()
	group.queue_free()
	_casts.erase(id)


func _clear() -> void:
	if is_instance_valid(_ground_field):
		_ground_field.clear()
	for id in _casts.keys():
		_retire(id)
	for voice in _voices:
		voice.stop()
	_high_cast = -1


func _exit_tree() -> void:
	for voice in _voices:
		if is_instance_valid(voice):
			voice.stop()
			voice.stream = null


func report() -> Dictionary:
	return {"profiles": _style.size(), "active": _casts.size(), "accepted": _accepted, "audio_cues": _played,
		"ground_field": _ground_field.report() if is_instance_valid(_ground_field) else {}}
