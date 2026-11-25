extends MultiMeshInstance3D
## Local RG32F time fields. Each tile stores arrival time and remaining span
## at each covered ground location. Normal frame updates set one shared clock.

const SURFACE := preload("res://shaders/hanuman_ground_field.gdshader")
const SIDE := 96
const CAPACITY := 3
const GROUND_OFFSET := 0.052
const EMPTY := Color(0.0, 0.0, 0.0, 1.0)

var _atlas: Image
var _texture: ImageTexture
var _material: ShaderMaterial
var _fields: Array[Dictionary] = []
var _clock := 0.0
var _uploads := 0
var _reduced := false


func _ready() -> void:
	name = &"GroundTimeField"
	top_level = true
	global_transform = Transform3D.IDENTITY
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var quad := PlaneMesh.new()
	quad.size = Vector2(2.0, 2.0)
	multimesh = MultiMesh.new()
	multimesh.transform_format = MultiMesh.TRANSFORM_3D
	multimesh.use_colors = true
	multimesh.use_custom_data = true
	multimesh.mesh = quad
	multimesh.instance_count = CAPACITY
	multimesh.visible_instance_count = 0
	_atlas = Image.create_empty(SIDE, SIDE * CAPACITY, false, Image.FORMAT_RGF)
	_atlas.fill(EMPTY)
	_texture = ImageTexture.create_from_image(_atlas)
	_material = ShaderMaterial.new()
	_material.shader = SURFACE
	_material.set_shader_parameter("time_field", _texture)
	_material.set_shader_parameter("tile_count", float(CAPACITY))
	material_override = _material
	hide()


func set_reduced(value: bool) -> void:
	_reduced = value
	_set_visibility()


func stamp(cast_id: int, geometry: Dictionary, life: float, color: Color) -> bool:
	var kind: String = geometry.get("kind", "")
	var radius: float = geometry.get("range_m", 0.0) if kind == "sector" else geometry.get("radius_m", 0.0)
	var center: Vector3 = geometry.get("origin" if kind == "sector" else "center", Vector3.ZERO)
	var forward: Vector3 = geometry.get("forward", Vector3.ZERO)
	var axis := Vector2(forward.x, forward.z)
	var cutoff: float = geometry.get("half_angle_cos", -1.0)
	if _reduced or cast_id <= 0 or _fields.size() >= CAPACITY or kind not in ["sector", "disk"]:
		return false
	if not center.is_finite() or not axis.is_finite() or axis.length_squared() < .9:
		return false
	if not is_finite(radius) or radius < .1 or radius > 24.0 or not is_finite(life) or life <= 0.0 or life > 8.0:
		return false
	if not is_finite(cutoff) or cutoff < -1.0 or cutoff > 1.0 or _find(cast_id) >= 0:
		return false
	var slot := 0
	var used: Array[int] = []
	for field in _fields:
		used.append(field.slot)
	while slot in used:
		slot += 1
	var direction := Vector3(axis.x, 0.0, axis.y).normalized()
	var right := Vector3(direction.z, 0.0, -direction.x)
	var field := {
		"id": cast_id, "slot": slot, "kind": kind, "radius": radius, "cutoff": cutoff, "center": center,
		"end": _clock + life, "color": color,
		"transform": Transform3D(Basis(right * radius, Vector3.UP, direction * radius), center + Vector3.UP * GROUND_OFFSET),
	}
	_paint(field, life)
	_fields.append(field)
	_publish()
	return true


func advance(delta: float) -> void:
	if _fields.is_empty() or not is_finite(delta) or delta <= 0.0:
		return
	_clock += delta
	var expired := false
	for index in range(_fields.size() - 1, -1, -1):
		if _clock >= float(_fields[index].end):
			_erase(index)
			expired = true
	_material.set_shader_parameter("clock_s", _clock)
	if expired:
		_publish()


func retire(cast_id: int) -> void:
	var index := _find(cast_id)
	if index >= 0:
		_erase(index)
		_publish()


func clear() -> void:
	if not _fields.is_empty():
		_fields.clear()
		_atlas.fill(EMPTY)
		_publish()


func _find(cast_id: int) -> int:
	for index in _fields.size():
		if _fields[index].id == cast_id:
			return index
	return -1


func _paint(field: Dictionary, life: float) -> void:
	var sector: bool = field.kind == "sector"
	var cutoff: float = field.cutoff
	var duration: float = minf(.12 if sector else .19, life * .42)
	var tile_start: int = field.slot * SIDE
	for row in SIDE:
		var z := ((float(row) + .5) / SIDE) * 2.0 - 1.0
		for column in SIDE:
			var x := ((float(column) + .5) / SIDE) * 2.0 - 1.0
			var range_fraction := Vector2(x, z).length()
			if range_fraction > 1.0 or (sector and z < cutoff * range_fraction):
				continue
			# Different ground locations get different real start times.
			var delay := duration * range_fraction
			_atlas.set_pixel(column, tile_start + row, Color(_clock + delay, life - delay, 0.0, 1.0))


func _erase(index: int) -> void:
	_atlas.fill_rect(Rect2i(0, _fields[index].slot * SIDE, SIDE, SIDE), EMPTY)
	_fields.remove_at(index)


func _publish() -> void:
	_texture.update(_atlas)
	_uploads += 1
	var bounds := AABB()
	for index in _fields.size():
		var field := _fields[index]
		multimesh.set_instance_transform(index, field.transform)
		multimesh.set_instance_color(index, field.color)
		var sector := 1.0 if field.kind == "sector" else 0.0
		multimesh.set_instance_custom_data(index, Color(float(field.slot), sector, (float(field.cutoff) + 1.0) * .5, 0.0))
		var extent := Vector3(field.radius, .1, field.radius)
		var field_bounds := AABB(field.center - extent, extent * 2.0)
		bounds = field_bounds if index == 0 else bounds.merge(field_bounds)
	multimesh.custom_aabb = bounds
	multimesh.visible_instance_count = _fields.size()
	if _fields.is_empty():
		_clock = 0.0
		_material.set_shader_parameter("clock_s", _clock)
	_set_visibility()


func _set_visibility() -> void:
	visible = not _reduced and not _fields.is_empty()


func report() -> Dictionary:
	var bytes := SIDE * SIDE * CAPACITY * 2 * 4
	return {
		"active": _fields.size(), "capacity": CAPACITY, "visible_instances": _fields.size() if visible else 0,
		"clock_s": _clock, "atlas_size": Vector2i(SIDE, SIDE * CAPACITY),
		"texture_bytes": bytes, "texture_updates": _uploads, "updated_bytes": bytes * _uploads,
	}
