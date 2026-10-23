extends RefCounted
## Raw GLTFDocument load works in CI without editor-generated .godot imports.
static func load_diya() -> PackedScene:
    var path:="res://assets/diya.glb"
    if not FileAccess.file_exists(path):path="res://art/concepts/cloud-diya-pilot/candidate.glb"
    var document:=GLTFDocument.new();var state:=GLTFState.new()
    if document.append_from_file(path,state)!=OK:return null
    var node: Node=document.generate_scene(state)
    if node==null:return null
    var packed:=PackedScene.new();var status:=packed.pack(node);node.free()
    return packed if status==OK else null
