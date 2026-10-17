extends SceneTree
## Isolated structural inspection only; dummy-renderer samples are not visual evidence.
var skeletons: Array[Skeleton3D] = []
var players: Array[AnimationPlayer] = []
var meshes: Array[MeshInstance3D] = []
func _initialize() -> void:
	call_deferred("run")
func gather(node: Node) -> void:
	if node is Skeleton3D: skeletons.append(node)
	if node is AnimationPlayer: players.append(node)
	if node is MeshInstance3D: meshes.append(node)
	for child in node.get_children(): gather(child)
func run() -> void:
	var scene: PackedScene = load("res://player/model/player.glb")
	var model := scene.instantiate()
	root.add_child(model)
	await process_frame
	gather(model)
	var report := {"kind":"isolated-reference-character-structural-inspection", "godot":Engine.get_version_info(), "display_server":DisplayServer.get_name(), "renderer":RenderingServer.get_current_rendering_method(), "source_sha256":FileAccess.get_sha256("res://player/model/player.glb"), "skeletons":[], "animations":[], "meshes":[], "finite_samples":0, "non_rest_samples":0, "nonfinite_samples":0, "scope":"Headless structural import and frozen pose samples only. No rendered-image, continuity, retargeting, gameplay or visual-quality acceptance."}
	for skeleton in skeletons:
		var bones := []
		for bone in skeleton.get_bone_count(): bones.append({"name":skeleton.get_bone_name(bone),"parent":skeleton.get_bone_parent(bone)})
		report.skeletons.append({"path":str(model.get_path_to(skeleton)),"bone_count":skeleton.get_bone_count(),"bones":bones})
	for mesh in meshes:
		var materials := []
		for surface in mesh.mesh.get_surface_count():
			var material := mesh.get_active_material(surface)
			var entry := {"name":material.resource_name if material else "", "path":material.resource_path if material else "", "class":material.get_class() if material else "missing"}
			if material is BaseMaterial3D:
				for key in ["albedo_texture", "normal_texture", "metallic_texture", "roughness_texture", "ao_texture", "emission_texture"]:
					var texture = material.get(key)
					entry[key] = texture.resource_path if texture else ""
			materials.append(entry)
		report.meshes.append({"name":mesh.name,"surface_count":mesh.mesh.get_surface_count(),"skin_bind_count":mesh.skin.get_bind_count() if mesh.skin else 0,"materials":materials})
	for animator in players:
		for clip in animator.get_animation_list():
			var animation := animator.get_animation(clip)
			var sample_count := 0
			animator.play(clip, 0)
			for fraction in [0.0, 0.5, 0.99]:
				animator.seek(animation.length * fraction, true)
				animator.advance(0)
				for skeleton in skeletons:
					for bone in skeleton.get_bone_count():
						var pose := skeleton.get_bone_global_pose(bone)
						if pose.is_finite() and absf(pose.basis.determinant()) > 0.000001: report.finite_samples += 1
						else: report.nonfinite_samples += 1
						if not pose.is_equal_approx(skeleton.get_bone_global_rest(bone)): report.non_rest_samples += 1
						sample_count += 1
			report.animations.append({"name":clip,"length_seconds":animation.length,"loop_mode":animation.loop_mode,"track_count":animation.get_track_count(),"bone_samples":sample_count})
		animator.stop()
	var output := ProjectSettings.globalize_path("res://inspection.json")
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output = argument.trim_prefix("--output=")
	var file := FileAccess.open(output,FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n")
	print("REFERENCE_CHARACTER_INSPECTED ",JSON.stringify({"skeletons":skeletons.size(),"bones":report.skeletons[0].bone_count,"animations":report.animations.size(),"meshes":meshes.size(),"finite_samples":report.finite_samples,"nonfinite_samples":report.nonfinite_samples}))
	model.free()
	quit(0 if report.nonfinite_samples == 0 and not skeletons.is_empty() and not players.is_empty() else 1)
