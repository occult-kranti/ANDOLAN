extends SceneTree
## Actual shared-resource load, inherited runtime setup, and save/reopen checks.
func _initialize() -> void:
	call_deferred("run")

func run() -> void:
	var output := ""
	for argument in OS.get_cmdline_user_args():
		if argument.begins_with("--output="): output = argument.trim_prefix("--output=")
	if not output.is_absolute_path() or FileAccess.file_exists(output):
		printerr("Use a fresh absolute output JSON path"); quit(2); return
	var scene_path := "res://docs/research/hero-family-reuse-oct23/pilot/arjuna-template.tscn"
	var packed = load(scene_path)
	if not packed is PackedScene:
		printerr("Cannot load template scene"); quit(2); return
	var first = packed.instantiate(); root.add_child(first)
	await process_frame
	var first_report: Dictionary = first.report()
	var action_ok: bool = first.motion.request_action("kodanda",.18,.22)
	for frame in 16:
		first.motion.update_motion(1.0/60,{"velocity":Vector3(0,0,6),"grounded":true})
		first.motion.evaluate_pose()
	var held: bool = first.motion.action_stage == "hold" and first.motion.finite
	var released: bool = first.motion.release_action("kodanda")
	var duplicate_rejected: bool = not first.motion.release_action("kodanda")
	for frame in 30:
		first.motion.update_motion(1.0/60,{"velocity":Vector3.ZERO,"grounded":true})
		first.motion.evaluate_pose()
	var recovered: bool = first.motion.action_stage == "none" and first.motion.finite
	var sockets := []
	for name_ in ["bow_grip","string_nock","draw_hand","arrow_muzzle","head"]:
		sockets.append(first.socket_checked(name_))
	var unknown: Dictionary = first.socket_checked("unreviewed_mace_grip")
	var library = load("res://assets/animations/rama_hero_motion.tres")
	var clips: Array[String] = []
	for name_ in library.get_animation_list(): clips.append(str(name_))
	var source_before := FileAccess.get_sha256("res://assets/heroes/rama-hero.glb")
	# Repack the resource-reference scene, not the expanded runtime actor; saving
	# a live configured tree would serialize helper instances and duplicate state.
	var editable = packed.instantiate()
	var saved := PackedScene.new(); var pack_error := saved.pack(editable)
	var saved_path := output.get_basename()+"-reopened-template.tscn"
	var save_error := ResourceSaver.save(saved,saved_path) if pack_error == OK else pack_error
	editable.free()
	var reopened = load(saved_path).instantiate() if save_error == OK else null
	var reopen_report := {}
	if reopened:
		root.add_child(reopened); await process_frame; reopen_report = reopened.report()
	var checks := {"initial_setup":first_report.configured,"one_live_rig":first_report.lod.get("live_rigs",0)==1,"164_bones":first_report.lod.get("live_bones",0)==164,"three_lod_levels":first_report.lod.get("levels",0)==3,"runtime_23_clips":clips.size()==23,"five_finite_sockets":sockets.all(func(s):return s.ok),"unknown_socket_rejected":not unknown.ok,"saved_scene_reopened":reopen_report.get("configured",false),"donor_hash_unchanged":FileAccess.get_sha256("res://assets/heroes/rama-hero.glb")==source_before,"template_never_promoted":not first_report.runtime_promoted and not first_report.finished_hero and not first_report.gameplay_enabled}
	checks["inherited_run_draw_release_recovery"] = action_ok and held and released and recovered
	checks["duplicate_release_rejected"] = duplicate_rejected
	checks["canonical_donor_reference_reloaded"] = first.get_node("SharedRamaDonor").scene_file_path == "res://assets/heroes/rama-hero.glb" and reopened != null and reopened.get_node("SharedRamaDonor").scene_file_path == "res://assets/heroes/rama-hero.glb"
	var report := {"schema_version":1,"scope":"Isolated source-reuse template functional check; no art, gameplay or hardware-quality acceptance.","engine":Engine.get_version_info(),"template_path":scene_path,"template_sha256":FileAccess.get_sha256(scene_path),"clips":clips,"first":first_report,"sockets":sockets,"unknown_socket":unknown,"save_error":save_error,"reopened":reopen_report,"checks":checks,"passed":checks.values().all(func(v):return v),"runtime_promoted":false}
	report["manifest_sha256"] = FileAccess.get_sha256("res://docs/research/hero-family-reuse-oct23/rama-family-manifest.json")
	report["template_script_sha256"] = FileAccess.get_sha256("res://tools/hero-family-reuse/family_template.gd")
	report["probe_script_sha256"] = FileAccess.get_sha256(get_script().resource_path)
	report["motion_after_functional_exercise"] = first.motion.diagnostics()
	var file := FileAccess.open(output,FileAccess.WRITE)
	if file == null:
		printerr("Cannot write output"); quit(2); return
	file.store_string(JSON.stringify(report,"  ")+"\n"); file.close()
	if reopened: reopened.free()
	first.free()
	print("HERO_FAMILY_GODOT_PROBE "+JSON.stringify(checks)); quit(0 if report.passed else 1)
