extends Node
## Explicit diagnostic only. The current source candidate has unresolved cast
## contacts. No default caller, bone writer, material writer or LOD selector.
const OWNER_META := &"yuga_s5_shoulder_review_owner"
const ACKNOWLEDGEMENT := "S5_SOURCE_CONTACTS_UNRESOLVED"
const TRIANGLES := [8928,4684,2204]
const MATERIAL_NAMES := ["Worked warm gold","Cobalt handwoven silk","Recessed antique gold"]
const EXPECTED_ORIGIN := Vector3(.200018927455,1.460128903389,.011324317195)
const EXPECTED_BASIS := Basis(Vector3(.086158156395,.026272492483,.995934963226),Vector3(.630582451820,-.775375485420,-.034096274525),Vector3(.771331906319,.630954146385,-.083370879292))
var configured := false
var reason := "Unconfigured review-only source candidate"
var _visual: Node3D
var _rig: Skeleton3D
var _attachment: BoneAttachment3D
var _instances: Array[MeshInstance3D] = []
var _materials: Array[Material] = []
var _level := 0

func _unit_transform(value: Transform3D) -> bool:
	if not value.origin.is_finite() or not value.basis.is_finite(): return false
	var b:=value.basis
	return absf(b.x.length_squared()-1)<.00003 and absf(b.y.length_squared()-1)<.00003 and absf(b.z.length_squared()-1)<.00003 and absf(b.x.dot(b.y))<.00003 and absf(b.x.dot(b.z))<.00003 and absf(b.y.dot(b.z))<.00003 and absf(b.determinant()-1)<.00003

func _valid_mesh(mesh: Mesh, level: int) -> bool:
	if not mesh is ArrayMesh or mesh.get_surface_count()!=3: return false
	var triangles:=0
	for surface in 3:
		var authored: Material=mesh.surface_get_material(surface)
		if authored==null or authored.resource_name!=MATERIAL_NAMES[surface]: return false
		if mesh.surface_get_primitive_type(surface)!=Mesh.PRIMITIVE_TRIANGLES: return false
		var arrays:=mesh.surface_get_arrays(surface)
		var vertices: PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
		var colors: PackedColorArray=arrays[Mesh.ARRAY_COLOR]
		if vertices.is_empty() or colors.size()!=vertices.size(): return false
		if arrays[Mesh.ARRAY_BONES]!=null and not arrays[Mesh.ARRAY_BONES].is_empty(): return false
		for color in colors:
			if color!=Color(1,1,1,0): return false
		for point in vertices:
			if not point.is_finite() or point.length()>.35: return false
		triangles+=arrays[Mesh.ARRAY_INDEX].size()/3
	return triangles==TRIANGLES[level]

func configure(visual: Node3D, meshes: Array[Mesh], acknowledgement: String = "") -> bool:
	if acknowledgement!=ACKNOWLEDGEMENT:
		reason="Source body/sash contacts remain unresolved; explicit diagnostic acknowledgement required"; return false
	if configured: return visual==_visual and is_instance_valid(_attachment)
	if not is_inside_tree() or not is_instance_valid(visual) or not visual.is_inside_tree() or not _unit_transform(visual.global_transform):
		reason="Live unscaled finite visual required"; return false
	if visual.has_meta(OWNER_META) or meshes.size()!=3:
		reason="One owner and three explicitly supplied review meshes required"; return false
	var rigs: Array[Skeleton3D]=[]
	for node in visual.find_children("*","Skeleton3D",true,false): rigs.append(node)
	if visual is Skeleton3D: rigs.append(visual)
	if rigs.size()!=1 or rigs[0].get_bone_count()!=164 or rigs[0].find_bone("upperarm01.L")!=50:
		reason="Unique exact 164-bone source rig required"; return false
	var rig:=rigs[0]
	var rest:=rig.get_bone_global_rest(50)
	if not _unit_transform(rig.global_transform) or not _unit_transform(rest) or rest.origin.distance_to(EXPECTED_ORIGIN)>.00003:
		reason="Unexpected shoulder transform"; return false
	for axis in [0,1,2]:
		if rest.basis[axis].distance_to(EXPECTED_BASIS[axis])>.00003:
			reason="Unexpected source shoulder basis"; return false
	var borrowed: Array[Material]=[]
	for label in MATERIAL_NAMES:
		var found: Material
		for node: MeshInstance3D in visual.find_children("*","MeshInstance3D",true,false):
			if node.mesh==null: continue
			for surface in node.mesh.get_surface_count():
				var original:=node.mesh.surface_get_material(surface)
				if original!=null and original.resource_name==label:
					found=node.get_active_material(surface); break
			if found!=null: break
		var finished:=false
		if label=="Recessed antique gold":
			finished=found is StandardMaterial3D and found.resource_name.ends_with(" · Rama finish v2") and absf(found.roughness-.43)<.00001 and absf(found.metallic-.92)<.00001
		else:
			finished=found is ShaderMaterial and found.has_meta(&"yuga_surface_finish_owner") and found.resource_name==label+" · bounded secondary" and found.shader!=null and found.shader.resource_path=="res://shaders/rama_secondary_cloth.gdshader"
		if not finished:
			reason="Accepted current finish owner must be active for "+label; return false
		borrowed.append(found)
	for level in 3:
		if not _valid_mesh(meshes[level],level): reason="Candidate mesh contract mismatch"; return false
	var attachment:=BoneAttachment3D.new()
	attachment.name="ReviewOnlyLeftShoulderArmour"; attachment.bone_name="upperarm01.L"; attachment.override_pose=false
	for level in 3:
		var instance:=MeshInstance3D.new(); instance.name="OriginalShoulderArmourLOD"+str(level)
		instance.mesh=meshes[level]
		for surface in 3: instance.set_surface_override_material(surface,borrowed[surface])
		instance.visible=level==0; instance.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		attachment.add_child(instance); _instances.append(instance)
	rig.add_child(attachment)
	_visual=visual; _rig=rig; _attachment=attachment; _materials=borrowed
	visual.set_meta(OWNER_META,get_instance_id()); configured=true; reason="Diagnostic source candidate; cast contacts unresolved"
	visual.tree_exiting.connect(release)
	return true

func use_existing_lod(level: int) -> bool:
	# The existing hero LOD owner supplies this index; no new distance policy.
	if not configured or level<0 or level>2: return false
	for index in _instances.size(): _instances[index].visible=index==level
	_level=level
	return true

func release() -> void:
	if is_instance_valid(_visual) and _visual.tree_exiting.is_connected(release): _visual.tree_exiting.disconnect(release)
	if is_instance_valid(_attachment):
		if _attachment.get_parent()!=null: _attachment.get_parent().remove_child(_attachment)
		_attachment.free()
	if is_instance_valid(_visual) and _visual.get_meta(OWNER_META,0)==get_instance_id(): _visual.remove_meta(OWNER_META)
	_instances.clear(); _materials.clear(); _attachment=null; _rig=null; _visual=null; configured=false

func _exit_tree() -> void: release()

func report() -> Dictionary:
	return {"configured":configured,"level":_level,"triangles":TRIANGLES[_level] if configured else 0,"material_draws":3 if configured else 0,"borrowed_materials":_materials.size(),"new_bones":0,"bone_writes":0,"material_writes":0,"frame_callbacks":0,"default_activation":false,"clearance_accepted":false,"reason":reason}
