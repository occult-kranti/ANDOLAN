extends Node
## Optional, review-gated temple wisps. Existing rig/material owners remain unique.
## Four small curves soften the cap edge; they do not replace the authored hair.
const HAIR_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const OWNER_META := &"rama_character_accents_owner"
const REQUIRED_BONES := 164
const SEGMENTS := 16
const SIDES := 6
const RING_VERTICES := SIDES+1
const WISPS := 4
const NEAR_END := 8.0
const NEAR_MARGIN := 1.0
const EXPECTED_HEAD_ORIGIN := Vector3(0, 1.677237, .053228)

var configured := false
var last_reason := ""
var _visual: Node3D
var _rig: Skeleton3D
var _attachment: BoneAttachment3D
var _mesh: MeshInstance3D
var _hair: ShaderMaterial

func _collect(node: Node, rigs: Array[Skeleton3D], meshes: Array[MeshInstance3D]) -> void:
	if node is Skeleton3D: rigs.append(node)
	if node is MeshInstance3D and node.mesh: meshes.append(node)
	for child in node.get_children(): _collect(child, rigs, meshes)

func _finite_transform(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.is_finite() and absf(value.basis.determinant()) > .000001

func _curve(index: int) -> Array[Vector3]:
	var side := -1.0 if index < 2 else 1.0
	# Deliberate small asymmetry, anchored outside the eye/eyelid aperture.
	var extra := .003 if side < 0 else 0.0
	if index % 2 == 0:
		return [Vector3(side*.062, 1.815, .093), Vector3(side*.097, 1.811, .120), Vector3(side*(.128+extra), 1.743, .086), Vector3(side*.110, 1.698-extra, .050)]
	return [Vector3(side*.094, 1.782, .040), Vector3(side*(.123+extra), 1.764, .048), Vector3(side*.133, 1.711, .043), Vector3(side*.112, 1.664+extra, .020)]

func _sample(points: Array[Vector3], t: float) -> Vector3:
	var u := 1.0-t
	return u*u*u*points[0] + 3*u*u*t*points[1] + 3*u*t*t*points[2] + t*t*t*points[3]

func _direction(points: Array[Vector3], t: float) -> Vector3:
	var u := 1.0-t
	return (3*u*u*(points[1]-points[0]) + 6*u*t*(points[2]-points[1]) + 3*t*t*(points[3]-points[2])).normalized()

func _geometry(head_rest: Transform3D) -> ArrayMesh:
	var to_head := head_rest.affine_inverse()
	var normal_basis := head_rest.basis.transposed()
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var tangents := PackedFloat32Array()
	var uvs := PackedVector2Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	for strand in WISPS:
		var points := _curve(strand)
		var first := vertices.size()
		var width := .0033 if strand % 2 == 0 else .0023
		for ring in SEGMENTS+1:
			var t := float(ring)/SEGMENTS
			var center := _sample(points, t)
			var forward := _direction(points, t)
			var radial := forward.cross(Vector3.UP).normalized()
			if radial.length_squared() < .5: radial = forward.cross(Vector3.RIGHT).normalized()
			var across := forward.cross(radial).normalized()
			var radius := .00022 + width*pow(sin(PI*t), .8)*(1.0-.65*t)
			for side in RING_VERTICES:
				var angle := TAU*float(side)/SIDES
				var normal := radial*cos(angle) + across*sin(angle)
				var tangent := (to_head.basis*(-radial*sin(angle)+across*cos(angle))).normalized()
				vertices.append(to_head*(center+normal*radius))
				normals.append((normal_basis*normal).normalized())
				tangents.append_array(PackedFloat32Array([tangent.x, tangent.y, tangent.z, 1.0]))
				uvs.append(Vector2(float(side)/SIDES, t))
				# Zero is the secondary owner's anchored semantic mask, not opacity.
				colors.append(Color(1, 1, 1, 0))
		for ring in SEGMENTS:
			for side in SIDES:
				var a := first+ring*RING_VERTICES+side
				var b := a+1
				indices.append_array(PackedInt32Array([a, a+RING_VERTICES, b, b, a+RING_VERTICES, b+RING_VERTICES]))
		# Closed tapered ends; no backface or transparency dependency.
		for end in 2:
			var ring_start := first+end*SEGMENTS*RING_VERTICES
			for side in range(1, SIDES-1):
				if end == 0: indices.append_array(PackedInt32Array([ring_start, ring_start+side, ring_start+side+1]))
				else: indices.append_array(PackedInt32Array([ring_start, ring_start+side+1, ring_start+side]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices
	arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TANGENT] = tangents
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_COLOR] = colors
	arrays[Mesh.ARRAY_INDEX] = indices
	var result := ArrayMesh.new()
	result.resource_name = "Rama optional four temple wisps"
	result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return result

func configure(visual: Node3D) -> bool:
	if configured: return is_instance_valid(_visual) and visual == _visual and is_instance_valid(_attachment)
	if not is_instance_valid(visual) or not visual.is_inside_tree() or not _finite_transform(visual.global_transform):
		last_reason = "live finite visual required"
		return false
	if visual.has_meta(OWNER_META):
		last_reason = "accent owner already present"
		return false
	var rigs: Array[Skeleton3D] = []
	var meshes: Array[MeshInstance3D] = []
	_collect(visual, rigs, meshes)
	if rigs.size() != 1 or rigs[0].get_bone_count() != REQUIRED_BONES:
		last_reason = "unique 164-bone Rama rig required"
		return false
	var rig := rigs[0]
	var head := rig.find_bone("head")
	if head < 0 or not _finite_transform(rig.global_transform):
		last_reason = "finite live head required"
		return false
	var rest := rig.get_bone_global_rest(head)
	if not _finite_transform(rest) or rest.origin.distance_to(EXPECTED_HEAD_ORIGIN) > .0001:
		last_reason = "unrecognized Rama head rest"
		return false
	var material: ShaderMaterial
	var original: StandardMaterial3D
	for mesh in meshes:
		for surface in mesh.mesh.get_surface_count():
			var active := mesh.get_active_material(surface)
			var authored := mesh.mesh.surface_get_material(surface)
			if authored is StandardMaterial3D and authored.resource_name == "Swept black hair" and active is ShaderMaterial and active.shader == HAIR_SHADER and active.resource_name == "Swept black hair · bounded secondary":
				material = active
				original = authored
				break
		if material != null: break
	if material == null:
		last_reason = "configure after the existing secondary and finish material owners"
		return false
	var geometry := _geometry(rest)
	geometry.surface_set_material(0, original)
	var attachment := BoneAttachment3D.new()
	attachment.name = "RamaOptionalTempleWisps"
	attachment.bone_name = "head"
	attachment.override_pose = false
	var instance := MeshInstance3D.new()
	instance.name = "FourTaperedTempleWisps"
	instance.mesh = geometry
	instance.set_surface_override_material(0, material)
	instance.visibility_range_end = NEAR_END
	instance.visibility_range_end_margin = NEAR_MARGIN
	instance.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_DISABLED
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	attachment.add_child(instance)
	rig.add_child(attachment)
	_visual = visual; _rig = rig; _attachment = attachment; _mesh = instance; _hair = material
	visual.set_meta(OWNER_META, get_instance_id())
	configured = true
	last_reason = "optional candidate configured; actual matched visual acceptance required"
	return true

func release() -> void:
	if is_instance_valid(_attachment):
		if _attachment.get_parent(): _attachment.get_parent().remove_child(_attachment)
		_attachment.free()
	if is_instance_valid(_visual) and _visual.get_meta(OWNER_META, 0) == get_instance_id(): _visual.remove_meta(OWNER_META)
	_visual = null; _rig = null; _attachment = null; _mesh = null; _hair = null
	configured = false

func _exit_tree() -> void: release()

func report() -> Dictionary:
	var triangles := 0
	var vertices := 0
	if is_instance_valid(_mesh) and _mesh.mesh:
		var arrays := _mesh.mesh.surface_get_arrays(0)
		triangles = arrays[Mesh.ARRAY_INDEX].size()/3
		vertices = arrays[Mesh.ARRAY_VERTEX].size()
	return {"configured":configured,"wisps":WISPS if configured else 0,"triangles":triangles,"vertices":vertices,"near_end_m":NEAR_END,"near_hysteresis_m":NEAR_MARGIN,"frame_callbacks":0,"skeleton_writes":0,"material_writes":0,"last_reason":last_reason,"scope":"Optional rigid head-following temple silhouette candidate. Existing four hair motion bones and secondary owner unchanged. No hair simulation or finished sculpt claim."}
