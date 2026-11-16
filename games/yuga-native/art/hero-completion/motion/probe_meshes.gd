extends SceneTree
func _initialize() -> void:call_deferred("run")
func visit(node: Node) -> void:
	if node is MeshInstance3D:
		var materials:=[]
		for index in node.mesh.get_surface_count():materials.append(node.mesh.surface_get_material(index).resource_name)
		print(node.name," bounds=",node.get_aabb()," materials=",materials)
	for c in node.get_children():visit(c)
func run() -> void:
	var actor=load("res://assets/heroes/rama-hero.glb").instantiate();root.add_child(actor);visit(actor);actor.free();quit()
