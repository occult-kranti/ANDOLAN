extends RefCounted
## Shared texture, ground card and faceted stone insert for every invocation.

const STAMP_SHADER := preload("res://shaders/hanuman_invocation_mark.gdshader")
const MASKS := "res://assets/vfx/hanuman-invocation-masks.png"
const ROWS := ["crescent", "ward", "wind", "ember", "mountain"]
const OPACITY := [.61, .82, .72]

var _materials: Dictionary = {}
var _card: PlaneMesh
var _stone: ArrayMesh
var _stone_material: StandardMaterial3D


func configure(styles: Dictionary) -> void:
	var painted_masks := load(MASKS) as Texture2D
	if painted_masks == null:
		return
	_card = PlaneMesh.new()
	_card.size = Vector2(2.0, 2.0)
	for style in styles.values():
		var row: int = ROWS.find(style.kind)
		if row < 0:
			continue
		var phases: Array[ShaderMaterial] = []
		for column in 3:
			var ink := ShaderMaterial.new()
			ink.shader = STAMP_SHADER
			ink.render_priority = 1
			ink.set_shader_parameter("painted_masks", painted_masks)
			ink.set_shader_parameter("atlas_cell", Vector2(column, row))
			ink.set_shader_parameter("tone", style.accent)
			ink.set_shader_parameter("glint", style.color)
			ink.set_shader_parameter("opacity", OPACITY[column])
			phases.append(ink)
		_materials[style.kind] = phases
	_stone = _make_stone()
	_stone_material = StandardMaterial3D.new()
	_stone_material.vertex_color_use_as_albedo = true
	_stone_material.vertex_color_is_srgb = true
	_stone_material.roughness = .88


func mark(group: Node3D, geometry: Dictionary, style: String, radius: float, angle: float) -> MeshInstance3D:
	if _card == null or not _materials.has(style):
		return null
	var width := radius * .43
	var depth := radius * .34
	var center := Vector3.UP * .074
	var rotation := 0.0
	match String(geometry.kind):
		"sector":
			# These corner bounds remain comfortably inside the authority fan.
			width = minf(radius * .32, radius * .23 * tan(minf(1.23, angle)))
			depth = radius * .22
			center.z = radius * .48
		"movement":
			var start := group.to_local(geometry.origin)
			var planar := Vector2(start.x, start.z)
			center = Vector3(planar.x, .074, planar.y) * Vector3(.53, 1, .53)
			rotation = atan2(-planar.x, -planar.y)
			width = minf(planar.length() * .2, .68)
			depth = minf(planar.length() * .33, 1.6)
	if width < .06 or depth < .06:
		return null
	var stamp := MeshInstance3D.new()
	stamp.name = &"InvocationMark"
	stamp.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	stamp.mesh = _card
	stamp.position = center
	stamp.rotation.y = rotation
	stamp.scale = Vector3(width, 1.0, depth)
	stamp.set_meta("art_base_size", stamp.scale)
	stamp.set_meta("art_kind", style)
	group.add_child(stamp, false, Node.INTERNAL_MODE_BACK)
	set_phase(stamp, 0)
	return stamp


func set_phase(stamp: MeshInstance3D, phase: int) -> void:
	stamp.material_override = _materials[stamp.get_meta("art_kind")][phase]
	stamp.set_meta("art_phase", phase)


func mountain(parent: Node3D, width: float) -> void:
	if _stone == null:
		return
	var chunk := MeshInstance3D.new()
	chunk.name = &"PaintedMountain"
	chunk.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	chunk.mesh = _stone
	chunk.material_override = _stone_material
	chunk.scale = Vector3.ONE * width
	parent.add_child(chunk)


static func _make_stone() -> ArrayMesh:
	var base := PackedVector3Array([Vector3(-.81, -.19, .24), Vector3(-.41, -.21, -.51), Vector3(.27, -.17, -.61),
		Vector3(.79, -.21, -.14), Vector3(.67, -.20, .49), Vector3(-.16, -.23, .61)])
	var ridge := PackedVector3Array([Vector3(-.59, .17, .12), Vector3(-.33, .32, -.31), Vector3(.19, .48, -.27),
		Vector3(.46, .30, -.04), Vector3(.40, .20, .30), Vector3(-.18, .30, .42)])
	var peak := Vector3(.05, .84, .02)
	var faces := SurfaceTool.new()
	faces.begin(Mesh.PRIMITIVE_TRIANGLES)
	faces.set_smooth_group(-1)
	for index in 6:
		var next := (index + 1) % 6
		var warmth := float(index % 3) * .12
		_triangle(faces, base[index], ridge[next], base[next], Color(.29 + warmth, .24, .18))
		_triangle(faces, base[index], ridge[index], ridge[next], Color(.46 + warmth, .35, .21))
		_triangle(faces, ridge[index], peak, ridge[next], Color(.61 + warmth, .48, .30))
		_triangle(faces, Vector3(0, -.2, 0), base[index], base[next], Color(.29, .22, .16))
	faces.generate_normals()
	return faces.commit()


static func _triangle(out: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, color: Color) -> void:
	out.set_color(color)
	out.add_vertex(a)
	out.add_vertex(b)
	out.add_vertex(c)
