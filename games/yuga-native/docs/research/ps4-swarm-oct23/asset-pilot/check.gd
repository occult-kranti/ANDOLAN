extends SceneTree
func _initialize():
 var packed = load("res://diya.glb") as PackedScene
 if packed == null:
  push_error("No imported PackedScene")
  quit(2)
  return
 var root = packed.instantiate()
 var todo = [root]
 var meshes = 0
 var surfaces = 0
 while not todo.is_empty():
  var node = todo.pop_back()
  if node is MeshInstance3D:
   if node.mesh == null:
    quit(3)
    return
   meshes += 1
   surfaces += node.mesh.get_surface_count()
  for child in node.get_children(): todo.push_back(child)
 print(JSON.stringify({"source":"diya.glb","meshes":meshes,"surfaces":surfaces,"scope":"Isolated GLB import/instantiation only; no game runtime promotion"}))
 root.free()
 quit(0 if meshes > 0 and surfaces > 0 else 4)
