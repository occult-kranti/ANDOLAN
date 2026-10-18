extends RefCounted
## Current real player/rig fixture. Native CPU callbacks are advanced explicitly;
## this does not import assets, render vertices, or synthesize achieved FPS.
const BINDINGS := preload("res://scripts/input_bindings.gd")
const PLAYER := preload("res://scripts/player.gd")
const SOURCES := ["res://scripts/input_bindings.gd", "res://scripts/player.gd", "res://scripts/rama_motion.gd", "res://scripts/rama_secondary_motion.gd", "res://scripts/rama_lod_binding.gd", "res://scripts/rama_visual_lod.gd", "res://scripts/rama_surface_materials.gd", "res://scripts/rama_surface_finish.gd", "res://scripts/rama_facial_performance.gd", "res://shaders/rama_secondary_cloth.gdshader", "res://assets/animations/rama_hero_motion.tres", "res://assets/heroes/rama-hero.glb", "res://assets/heroes/rama-hero-mid.glb", "res://assets/heroes/rama-hero-far.glb"]

static func create(tree: SceneTree) -> Node3D:
	BINDINGS.install()
	var player := PLAYER.new()
	tree.root.add_child(player)
	player.set_physics_process(false)
	player.set_process_unhandled_input(false)
	# Avoid a second engine pose application while tests await a frame. The
	# same real modifier's evaluate_pose() is called explicitly by step().
	player.rama_motion.active = false
	return player

static func step(player: Node3D, delta: float, velocity := Vector3(2,0,6), yaw := 0.0) -> void:
	player.velocity = velocity
	player.position += velocity * delta
	player.visual.rotation.y = yaw
	player._update_rama_motion(delta)
	player.rama_motion.evaluate_pose()

static func bones(rig: Skeleton3D) -> Array[Transform3D]:
	var result: Array[Transform3D] = []
	for index in rig.get_bone_count(): result.append(rig.get_bone_pose(index))
	return result

static func collect(node: Node, kind: String) -> Array[Node]:
	var result: Array[Node] = []
	if node.is_class(kind): result.append(node)
	for child in node.get_children(): result.append_array(collect(child,kind))
	return result

static func identities(player: Node3D) -> Dictionary:
	var result := {"meshes":[],"skins":[],"materials":[],"nodes":[]}
	for node in collect(player,"Node"):
		result.nodes.append(node.get_instance_id())
		if node is MeshInstance3D:
			result.meshes.append(node.mesh.get_instance_id() if node.mesh else 0)
			result.skins.append(node.skin.get_instance_id() if node.skin else 0)
			if node.mesh:
				for surface in node.mesh.get_surface_count():
					var material: Material = node.get_active_material(surface)
					result.materials.append(material.get_instance_id() if material else 0)
	return result

static func pins() -> Dictionary:
	var result := {}
	for path in SOURCES:
		result[path] = FileAccess.get_sha256(path)
		if path.ends_with(".glb"):
			var settings := ConfigFile.new()
			if settings.load(path+".import") == OK:
				var imported: String = settings.get_value("remap","path","")
				result[path+".import"] = FileAccess.get_sha256(path+".import")
				result[imported] = FileAccess.get_sha256(imported)
	return result
