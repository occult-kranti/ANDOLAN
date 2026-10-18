extends SceneTree
## Read-only actual PackedScene skeleton order; no editor or GLTF reimport.
func _initialize() -> void:
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output=arg.trim_prefix("--report=")
	if not output.is_absolute_path() or FileAccess.file_exists(output): quit(2); return
	var packed: PackedScene=load("res://assets/heroes/rama-hero.glb")
	var instance:=packed.instantiate()
	var rigs:=instance.find_children("*","Skeleton3D",true,false)
	if rigs.size()!=1: instance.free(); quit(3); return
	var rig: Skeleton3D=rigs[0]
	var bones:=[]
	for index in rig.get_bone_count(): bones.append({"index":index,"name":String(rig.get_bone_name(index)),"parent":rig.get_bone_parent(index)})
	var receipt: Dictionary={"complete":bones.size()==164,"godot":Engine.get_version_info(),"source_sha256":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb"),"bones":bones,"scope":"Actual loaded near PackedScene Skeleton3D order used by final modifier pose arrays. No scene simulation, framebuffer or import."}
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(receipt,"  ",true,true)+"\n")
	instance.free()
	quit(0 if receipt.complete else 1)
