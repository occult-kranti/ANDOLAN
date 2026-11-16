extends SceneTree
func _initialize() -> void:call_deferred("run")
func find(node:Node) -> Skeleton3D:
	if node is Skeleton3D:return node
	for child in node.get_children():
		var rig:=find(child)
		if rig:return rig
	return null
func run() -> void:
	var actor=load("res://assets/heroes/rama-hero.glb").instantiate();root.add_child(actor);var rig:=find(actor)
	for i in rig.get_bone_count():
		var n:=rig.get_bone_name(i)
		if "shoulder" in n or "clavicle" in n or n in ["upperarm01.L","upperarm01.R","spine03"]:
			print(n," ",rig.get_bone_global_rest(i))
	actor.free();quit()
