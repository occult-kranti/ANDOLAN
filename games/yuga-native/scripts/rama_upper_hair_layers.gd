extends Node
## Optional broad upper-nape tier; separate from rejected temple-wisp prototype.
## One head follower, one mesh, shared existing hair material, no frame writes.
const DATA_PATH := "res://assets/hero-finish/upper-hair-layers.json"
const HAIR_SHADER := preload("res://shaders/rama_secondary_cloth.gdshader")
const SOURCE_SHA := "8b6cf0f4c5520696d1d843e5bdebb2454c1dbd4341e17171c5b6d20353384d5c"
const OWNER_META := &"rama_upper_hair_layers_owner"
const REQUIRED_BONES := 164
const EXPECTED_HEAD_ORIGIN := Vector3(0, 1.677237, .053228)
const SEGMENTS := 16
const SIDES := 8
const LAYERS := 7
var configured := false
var last_reason := "unconfigured"
var _visual: Node3D
var _rig: Skeleton3D
var _attachment: BoneAttachment3D
var _mesh: MeshInstance3D
var _hair: ShaderMaterial

func _collect(node: Node, rigs: Array[Skeleton3D], meshes: Array[MeshInstance3D]) -> void:
	if node is Skeleton3D: rigs.append(node)
	if node is MeshInstance3D and node.mesh != null: meshes.append(node)
	for child in node.get_children(): _collect(child, rigs, meshes)

func _finite_transform(value: Transform3D) -> bool:
	return value.origin.is_finite() and value.basis.is_finite() and absf(value.basis.determinant()) > .000001

func _vector(value: Variant) -> Vector3:
	if not value is Array or value.size() != 3: return Vector3.INF
	for scalar in value:
		if not (scalar is float or scalar is int) or not is_finite(float(scalar)): return Vector3.INF
	return Vector3(value[0], value[1], value[2])

func _guides() -> Array:
	var raw: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not raw is Dictionary or raw.get("schema") != 1 or raw.get("source_sha256") != SOURCE_SHA or raw.get("bone") != "head" or raw.get("segments") != SEGMENTS or raw.get("sides") != SIDES: return []
	var guides: Variant = raw.get("guides")
	if not guides is Array or guides.size() != LAYERS: return []
	var result := []
	for guide in guides:
		if not guide is Dictionary or not guide.get("points") is Array or guide.points.size() != 4: return []
		var points: Array[Vector3] = []
		for value in guide.points:
			var point := _vector(value)
			if not point.is_finite() or absf(point.x) > .20 or point.y < 1.64 or point.y > 1.81 or point.z < -.22 or point.z > .04: return []
			points.append(point)
		var width := float(guide.get("width", 0.0))
		var depth := float(guide.get("depth", 0.0))
		var outward := _vector(guide.get("outward"))
		if not is_finite(width) or width < .014 or width > .027 or not is_finite(depth) or depth < .003 or depth > .004 or not outward.is_finite() or outward.length_squared() < .9: return []
		result.append({"points":points,"width":width,"depth":depth,"outward":outward.normalized()})
	return result

func _sample(points: Array[Vector3], t: float) -> Vector3:
	var u := 1.0-t
	return u*u*u*points[0] + 3*u*u*t*points[1] + 3*u*t*t*points[2] + t*t*t*points[3]

func _direction(points: Array[Vector3], t: float) -> Vector3:
	var u := 1.0-t
	return (3*u*u*(points[1]-points[0]) + 6*u*t*(points[2]-points[1]) + 3*t*t*(points[3]-points[2])).normalized()

func _geometry(head_rest: Transform3D, guides: Array) -> ArrayMesh:
	var to_head := head_rest.affine_inverse()
	var vertices := PackedVector3Array()
	var normals := PackedVector3Array()
	var tangents := PackedFloat32Array()
	var uvs := PackedVector2Array()
	var colors := PackedColorArray()
	var indices := PackedInt32Array()
	for guide in guides:
		var first := vertices.size()
		var points: Array[Vector3] = guide.points
		for ring in SEGMENTS+1:
			var t := float(ring)/SEGMENTS
			var center := _sample(points,t)
			var forward := _direction(points,t)
			var across := forward.cross(guide.outward).normalized()
			var out := across.cross(forward).normalized()
			var taper := .035 + .965*pow(sin(PI*t), .62)*(1.0-.24*t)
			var width: float = guide.width*taper
			var depth: float = guide.depth*taper
			for side in SIDES+1:
				var angle := TAU*float(side)/SIDES
				vertices.append(to_head*(center+across*width*cos(angle)+out*depth*sin(angle)))
				uvs.append(Vector2(float(side)/SIDES,t))
				# Upper hair follows the existing head rigidly; semantic alpha0.
				colors.append(Color(1,1,1,0))
		for ring in SEGMENTS:
			for side in SIDES:
				var a := first+ring*(SIDES+1)+side
				var b := a+1
				var c := a+SIDES+1
				indices.append_array(PackedInt32Array([a,c,b,b,c,c+1]))
		# Closed nonzero end rings; centre UV remains inside the source chart.
		for end in 2:
			var center_index := vertices.size()
			vertices.append(to_head*points[3 if end else 0])
			uvs.append(Vector2(.5,.985 if end else .015))
			colors.append(Color(1,1,1,0))
			var start := first+end*SEGMENTS*(SIDES+1)
			for side in SIDES:
				if end: indices.append_array(PackedInt32Array([center_index,start+side+1,start+side]))
				else: indices.append_array(PackedInt32Array([center_index,start+side,start+side+1]))
	# Derive the final normal/tangent frame from the actual curved, tapered
	# triangles. In particular UV-v follows the lock and requires its measured
	# bitangent sign; a guessed +1 handedness would invert normal-map grooves.
	var ns := PackedVector3Array(); ns.resize(vertices.size())
	var ts := PackedVector3Array(); ts.resize(vertices.size())
	var bs := PackedVector3Array(); bs.resize(vertices.size())
	for face in range(0,indices.size(),3):
		var a := indices[face]; var b := indices[face+1]; var c := indices[face+2]
		var e1 := vertices[b]-vertices[a]; var e2 := vertices[c]-vertices[a]
		var d1 := uvs[b]-uvs[a]; var d2 := uvs[c]-uvs[a]
		var determinant := d1.x*d2.y-d1.y*d2.x
		var face_normal := e1.cross(e2)
		var face_tangent := (e1*d2.y-e2*d1.y)/determinant
		var face_bitangent := (e2*d1.x-e1*d2.x)/determinant
		for index in [a,b,c]:
			ns[index] += face_normal; ts[index] += face_tangent; bs[index] += face_bitangent
	var per_layer := (SEGMENTS+1)*(SIDES+1)+2
	for layer in LAYERS:
		for ring in SEGMENTS+1:
			var a := layer*per_layer+ring*(SIDES+1)
			var b := a+SIDES
			var n := ns[a]+ns[b]; var t := ts[a]+ts[b]; var bit := bs[a]+bs[b]
			ns[a] = n; ns[b] = n; ts[a] = t; ts[b] = t; bs[a] = bit; bs[b] = bit
	normals.clear(); tangents.clear()
	for index in vertices.size():
		var normal := ns[index].normalized()
		var tangent := (ts[index]-normal*normal.dot(ts[index])).normalized()
		var handedness := -1.0 if normal.cross(tangent).dot(bs[index]) < 0 else 1.0
		normals.append(normal)
		tangents.append_array(PackedFloat32Array([tangent.x,tangent.y,tangent.z,handedness]))
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = vertices; arrays[Mesh.ARRAY_NORMAL] = normals
	arrays[Mesh.ARRAY_TANGENT] = tangents; arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_COLOR] = colors; arrays[Mesh.ARRAY_INDEX] = indices
	var mesh := ArrayMesh.new()
	mesh.resource_name = "Rama optional seven upper hair layers"
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	return mesh

func configure(visual: Node3D) -> bool:
	if configured: return visual == _visual and is_instance_valid(_attachment) and _attachment.get_parent() == _rig and is_instance_valid(_mesh) and _mesh.get_active_material(0) == _hair
	if not is_inside_tree() or not is_instance_valid(visual) or not visual.is_inside_tree() or not _finite_transform(visual.global_transform):
		last_reason = "live finite owner and visual required"
		return false
	if visual.has_meta(OWNER_META):
		last_reason = "upper hair layer owner already present"
		return false
	var rigs: Array[Skeleton3D] = []
	var meshes: Array[MeshInstance3D] = []
	_collect(visual,rigs,meshes)
	if rigs.size() != 1 or rigs[0].get_bone_count() != REQUIRED_BONES: return false
	var rig := rigs[0]
	var head := rig.find_bone("head")
	if head < 0 or not _finite_transform(rig.global_transform): return false
	var rest := rig.get_bone_global_rest(head)
	if not _finite_transform(rest) or rest.origin.distance_to(EXPECTED_HEAD_ORIGIN) > .0001: return false
	var material: ShaderMaterial
	for mesh in meshes:
		if mesh.material_override != null: continue
		for surface in mesh.mesh.get_surface_count():
			var source := mesh.mesh.surface_get_material(surface)
			var active := mesh.get_active_material(surface)
			if source is StandardMaterial3D and source.resource_name == "Swept black hair" and active is ShaderMaterial and active.shader == HAIR_SHADER and active.resource_name == "Swept black hair · bounded secondary":
				material = active
				break
		if material != null: break
	var guides := _guides()
	if material == null or guides.size() != LAYERS:
		last_reason = "recognized secondary hair and exact original guides required"
		return false
	var geometry := _geometry(rest,guides)
	geometry.surface_set_material(0,material)
	var attachment := BoneAttachment3D.new()
	attachment.name = "RamaUpperHairLayerAttachment"
	attachment.bone_name = "head"
	attachment.override_pose = false
	var instance := MeshInstance3D.new()
	instance.name = "SevenSweptUpperHairLayers"
	instance.mesh = geometry
	instance.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	attachment.add_child(instance)
	rig.add_child(attachment)
	_visual = visual; _rig = rig; _attachment = attachment; _mesh = instance; _hair = material
	visual.set_meta(OWNER_META,get_instance_id())
	visual.tree_exiting.connect(release)
	configured = true
	last_reason = "optional geometric tier configured; matched ablation review required"
	return true

func release() -> void:
	if is_instance_valid(_attachment) and _attachment.get_parent() == _rig:
		_attachment.get_parent().remove_child(_attachment)
		_attachment.free()
	if is_instance_valid(_visual):
		if _visual.get_meta(OWNER_META,0) == get_instance_id(): _visual.remove_meta(OWNER_META)
		if _visual.tree_exiting.is_connected(release): _visual.tree_exiting.disconnect(release)
	_visual = null; _rig = null; _attachment = null; _mesh = null; _hair = null
	configured = false

func report() -> Dictionary:
	var arrays: Array = _mesh.mesh.surface_get_arrays(0) if is_instance_valid(_mesh) else []
	return {"configured":configured,"layers":LAYERS if configured else 0,"triangles":arrays[Mesh.ARRAY_INDEX].size()/3 if configured else 0,"vertices":arrays[Mesh.ARRAY_VERTEX].size() if configured else 0,"extra_meshes":1 if configured else 0,"extra_materials":0,"frame_callbacks":0,"skeleton_writes":0,"last_reason":last_reason,"scope":"Optional short upper-hair tier, rigidly head-following. No source mesh rewrite, old wisps, hair simulation or full sculpt acceptance."}

func _exit_tree() -> void: release()
