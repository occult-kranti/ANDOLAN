extends Node
## Review-only geometry. RamaMotion remains the sole arrow transform/visibility writer.
const DATA_PATH := "res://art/hero-finish/s3-arrow-fletching/candidate-mesh.json"
const DATA_SHA := "0ae78829849c2a9eb5a5492c0649b97016210f7cc632d2e51fe906dde767adf6"
const OWNER_META := &"rama_arrow_fletching_owner"
static var _shared_mesh: ArrayMesh
var configured := false
var last_reason := "unconfigured"
var _arrow: Node3D
var _instance: MeshInstance3D
var _material: StandardMaterial3D

func _finite_transform(value: Transform3D) -> bool:
	if not value.origin.is_finite() or not value.basis.is_finite(): return false
	var axes: Array[Vector3]=[value.basis.x,value.basis.y,value.basis.z]
	for axis in axes:
		if absf(axis.length_squared()-1.0)>.0001: return false
	return (absf(axes[0].dot(axes[1]))<.0001 and absf(axes[0].dot(axes[2]))<.0001
		and absf(axes[1].dot(axes[2]))<.0001 and absf(value.basis.determinant()-1.0)<.001)

func _recognized_arrow(arrow: Node3D) -> bool:
	if arrow.name != "NockedArrow" or not arrow.get_parent() is Skeleton3D: return false
	var skeleton := arrow.get_parent() as Skeleton3D
	if skeleton.get_bone_count()!=164 or skeleton.find_bone("bowstring")<0 or skeleton.find_bone("wrist.R")<0: return false
	var shaft := 0
	var tip := 0
	var meshes := 0
	for child in arrow.get_children():
		if child.is_queued_for_deletion(): continue
		if not child is MeshInstance3D or not child.mesh is CylinderMesh: return false
		var cylinder := child.mesh as CylinderMesh
		meshes+=1
		if (is_equal_approx(cylinder.height,.72) and is_equal_approx(cylinder.top_radius,.003)
				and is_equal_approx(cylinder.bottom_radius,.003) and child.position.is_equal_approx(Vector3(0,.36,0))): shaft+=1
		if (is_equal_approx(cylinder.height,.065) and is_zero_approx(cylinder.top_radius)
				and is_equal_approx(cylinder.bottom_radius,.012) and child.position.is_equal_approx(Vector3(0,.7525,0))): tip+=1
		if not child.basis.is_equal_approx(Basis.IDENTITY): return false
	return meshes==2 and shaft==1 and tip==1

func _geometry() -> ArrayMesh:
	if _shared_mesh != null: return _shared_mesh
	if FileAccess.get_sha256(DATA_PATH)!=DATA_SHA: return null
	var data = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not data is Dictionary or data.get("schema")!=1 or data.get("triangles")!=60 or data.get("vanes")!=3: return null
	for key in ["vertices","normals","tangents","uvs","indices"]:
		if not data.get(key) is Array or data[key].size()!=180: return null
	var positions:=PackedVector3Array()
	var normals:=PackedVector3Array()
	var tangents:=PackedFloat32Array()
	var uvs:=PackedVector2Array()
	var indices:=PackedInt32Array()
	for i in 180:
		var p: Array=data.vertices[i]
		var n: Array=data.normals[i]
		var t: Array=data.tangents[i]
		var uv: Array=data.uvs[i]
		positions.append(Vector3(p[0],p[1],p[2]))
		normals.append(Vector3(n[0],n[1],n[2]))
		tangents.append_array(PackedFloat32Array(t))
		uvs.append(Vector2(uv[0],uv[1]))
		indices.append(int(data.indices[i]))
	var arrays:=[]
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX]=positions;arrays[Mesh.ARRAY_NORMAL]=normals
	arrays[Mesh.ARRAY_TANGENT]=tangents;arrays[Mesh.ARRAY_TEX_UV]=uvs
	arrays[Mesh.ARRAY_INDEX]=indices
	var result:=ArrayMesh.new()
	result.resource_name="Original optional three-vane arrow fletching"
	result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	_shared_mesh=result
	return result

func configure(arrow: Node3D, ivory: StandardMaterial3D) -> bool:
	if configured:
		return arrow==_arrow and ivory==_material and is_instance_valid(_instance) and _instance.get_parent()==_arrow and _instance.mesh==_shared_mesh and _instance.material_override==_material
	if not is_inside_tree() or not is_instance_valid(arrow) or not arrow.is_inside_tree() or not _finite_transform(arrow.global_transform):
		last_reason="live owner and existing unit-scale arrow frame required"
		return false
	if arrow.has_meta(OWNER_META) or not _recognized_arrow(arrow):
		last_reason="recognized unowned nocked shaft/tip required"
		return false
	if ivory==null or ivory.resource_name!="Ivory silk · Rama finish v2" or ivory.cull_mode!=BaseMaterial3D.CULL_DISABLED:
		last_reason="borrow the current finished ivory material without editing it"
		return false
	var mesh:=_geometry()
	if mesh==null:
		last_reason="exact original candidate geometry required"
		return false
	var instance:=MeshInstance3D.new()
	instance.name="OptionalArrowFletching"
	instance.mesh=mesh
	# The shared geometry holds no material: each live instance borrows its
	# own hero's material, avoiding cross-hero edits or texture copies.
	instance.material_override=ivory
	instance.set_meta(OWNER_META,get_instance_id())
	arrow.add_child(instance)
	arrow.set_meta(OWNER_META,get_instance_id())
	arrow.tree_exiting.connect(release)
	_arrow=arrow;_instance=instance;_material=ivory;configured=true
	last_reason="candidate attached; transform and visibility inherited, render review pending"
	return true

func release() -> void:
	if (is_instance_valid(_instance) and _instance.get_parent()==_arrow
			and _instance.get_meta(OWNER_META,0)==get_instance_id()):
		_instance.hide()
		# Safe during ancestor exit. Transferred geometry belongs to its new
		# parent and is left intact; the borrowed material is never modified.
		_instance.queue_free()
	if is_instance_valid(_arrow):
		if _arrow.get_meta(OWNER_META,0)==get_instance_id(): _arrow.remove_meta(OWNER_META)
		if _arrow.tree_exiting.is_connected(release): _arrow.tree_exiting.disconnect(release)
	_arrow=null;_instance=null;_material=null;configured=false
	last_reason="released"

func report() -> Dictionary:
	return {"configured":configured,"triangles":60 if configured else 0,"vertices":180 if configured else 0,
		"extra_mesh_instances":1 if configured else 0,"shared_geometry_resources":1 if _shared_mesh!=null else 0,
		"new_materials":0,"new_textures":0,"frame_callbacks":0,"skeleton_writes":0,
		"axis_bounds_m":[.05,.137],"max_radial_m":.012,"last_reason":last_reason,
		"scope":"Optional original fletching only. Current shaft, tip, arrow transform, visibility and bone/socket ownership remain external. No accepted appearance or general action clearance claim."}

func _exit_tree() -> void: release()
