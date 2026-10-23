extends SceneTree
## Independent bounded headless check; never renders or saves donor resources.

func _initialize() -> void:
	call_deferred("run")

func collect(node: Node, kind: String) -> Array:
	var found := []
	if node.is_class(kind): found.append(node)
	for child in node.get_children(): found.append_array(collect(child,kind))
	return found

func named_meshes(node: Node) -> Dictionary:
	var result := {}
	for mesh in collect(node,"MeshInstance3D"):
		if String(mesh.name) in ["RamaHero","RamaFace","RamaBow"]: result[String(mesh.name)] = mesh
	return result

func run() -> void:
	var destination := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): destination = argument.trim_prefix("--output=")
	if not destination.is_absolute_path() or FileAccess.file_exists(destination):
		printerr("fresh absolute --output required"); quit(2); return
	var donor_path := "res://assets/heroes/rama-hero.glb"
	var before := FileAccess.get_sha256(donor_path)
	var packed = load("res://docs/research/hero-family-reuse-oct23/pilot/arjuna-template.tscn")
	var first = packed.instantiate()
	var second = packed.instantiate()
	root.add_child(first); root.add_child(second)
	await process_frame
	var first_meshes := named_meshes(first)
	var second_meshes := named_meshes(second)
	var identities := {}
	for mesh_name in ["RamaHero","RamaFace","RamaBow"]:
		identities[mesh_name] = {"shared_mesh_resource":first_meshes[mesh_name].mesh == second_meshes[mesh_name].mesh,
			"separate_mesh_instances":first_meshes[mesh_name] != second_meshes[mesh_name],
			"first_mesh_resource_path":first_meshes[mesh_name].mesh.resource_path}
	var invalid = packed.instantiate()
	invalid.hero_id = "hanuman"
	root.add_child(invalid)
	await process_frame
	var retry_rejected: bool = not invalid.setup()
	var checks := {"two_configured_authoring_instances":first.configured and second.configured,
		"one_skeleton_each":collect(first,"Skeleton3D").size() == 1 and collect(second,"Skeleton3D").size() == 1,
		"independent_skeleton_state":first.motion.rig != second.motion.rig,
		"shared_near_geometry_resources":identities.values().all(func(v):return v.shared_mesh_resource),
		"shared_external_runtime_library":first.motion.library == second.motion.library,
		"unknown_anatomy_template_rejected":not invalid.configured and not invalid.errors.is_empty(),
		"failed_setup_retry_rejected":retry_rejected,
		"failed_setup_has_no_motion_helper":collect(invalid,"SkeletonModifier3D").is_empty(),
		"source_donor_unchanged":before == FileAccess.get_sha256(donor_path),
		"all_remain_templates":not first.report().finished_hero and not second.report().runtime_promoted}
	var report := {"schema_version":1,"scope":"Independent two-template source-resource sharing and rejected-instance lifecycle; no render/art/hardware evidence.",
		"script_sha256":FileAccess.get_sha256(get_script().resource_path),
		"template_script_sha256":FileAccess.get_sha256("res://tools/hero-family-reuse/family_template.gd"),
		"manifest_sha256":FileAccess.get_sha256("res://docs/research/hero-family-reuse-oct23/rama-family-manifest.json"),
		"donor_sha256":before,"mesh_resources":identities,"checks":checks,
		"first":first.report(),"second":second.report(),"invalid":invalid.report(),
		"passed":checks.values().all(func(v):return v)}
	var file := FileAccess.open(destination,FileAccess.WRITE)
	file.store_string(JSON.stringify(report,"  ")+"\n"); file.close()
	invalid.free(); second.free(); first.free()
	print("INDEPENDENT_HERO_SHARING "+JSON.stringify(checks)); quit(0 if report.passed else 1)
