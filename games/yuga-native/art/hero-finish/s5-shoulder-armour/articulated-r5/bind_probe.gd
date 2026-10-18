extends SceneTree
var destination: String=OS.get_environment("YUGA_SHOULDER_BIND_OUTPUT")
func matrix(t: Transform3D) -> Array:
	return [[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0,0,0,1]]
func _initialize() -> void: call_deferred("run")
func run() -> void:
	var packed: PackedScene=load("res://assets/heroes/rama-hero.glb")
	var visual: Node3D=packed.instantiate(); root.add_child(visual)
	var rig: Skeleton3D=visual.find_children("*","Skeleton3D",true,false)[0]
	var mesh: MeshInstance3D=rig.get_node("RamaHero")
	var surface: int=-1
	for index in mesh.mesh.get_surface_count():
		if mesh.mesh.surface_get_material(index).resource_name=="Rama warm skin": surface=index
	assert(surface>=0 and mesh.skin!=null)
	var arrays: Array=mesh.mesh.surface_get_arrays(surface)
	var outputs: Dictionary={}
	for index in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_BONES,Mesh.ARRAY_WEIGHTS,Mesh.ARRAY_INDEX]:
		var path: String=destination+"/skin-array-"+str(index)+".bin"
		var bytes: PackedByteArray=arrays[index].to_byte_array()
		FileAccess.open(path,FileAccess.WRITE).store_buffer(bytes)
		outputs[str(index)]={"sha256":FileAccess.get_sha256(path),"bytes":bytes.size(),"elements":arrays[index].size()}
	var binds: Array=[]; var bones: Array=[]
	for index in mesh.skin.get_bind_count():
		binds.append({"slot":index,"name":str(mesh.skin.get_bind_name(index)),"bone":mesh.skin.get_bind_bone(index),"matrix":matrix(mesh.skin.get_bind_pose(index))})
	for index in rig.get_bone_count():
		bones.append({"index":index,"name":rig.get_bone_name(index),"parent":rig.get_bone_parent(index),"rest":matrix(rig.get_bone_rest(index)),"global_rest":matrix(rig.get_bone_global_rest(index))})
	var result: Dictionary={"complete":true,"scope":"Actual existing cached imported skin arrays and bind-space capture. No new candidate import, controller evaluation or rendered skin.","engine":Engine.get_version_info().string,"source_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"descriptor_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb.import"),"packed_path":packed.resource_path,"mesh_path":str(visual.get_path_to(mesh)),"mesh_global":matrix(mesh.global_transform),"rig_global":matrix(rig.global_transform),"surface":surface,"format":mesh.mesh.surface_get_format(surface),"arrays":outputs,"binds":binds,"bones":bones}
	visual.free()
	FileAccess.open(destination+"/bind.json",FileAccess.WRITE).store_string(JSON.stringify(result,"\t")+"\n")
	print("PASS captured actual shoulder skin/bind resources: ",bones.size()," bones, ",binds.size()," binds")
	quit(0)
