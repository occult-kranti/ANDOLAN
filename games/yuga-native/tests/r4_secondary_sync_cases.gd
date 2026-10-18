extends SceneTree
const FIXTURE := preload("res://tests/r4_secondary_fixture.gd")
const SECONDARY := preload("res://scripts/rama_secondary_motion.gd")
var checks: Array[Dictionary] = []
var output := "/tmp/r4-secondary-sync.json"

func _initialize() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="): output = arg.trim_prefix("--report=")
	call_deferred("run")

func check(label: String, passed: bool, details: Dictionary = {}) -> void:
	checks.append({"name":label,"passed":passed,"details":details})
	print("PASS " if passed else "FAIL ",label)

func uniform_error(secondary: Node) -> float:
	var error := 0.0
	for binding in secondary._bindings:
		var expected: Vector3 = secondary.hair_offset if binding.kind == "hair" else secondary.cloth_offset
		var actual: Vector3 = binding.mesh.global_basis * binding.material.get_shader_parameter("secondary_offset")
		error = maxf(error,actual.distance_to(secondary._visual.global_basis*expected))
	return error

func run() -> void:
	var player := FIXTURE.create(self)
	var motion: Node = player.rama_motion
	var secondary: Node = player.rama_secondary
	var lod: Node = player.rama_lod
	var rig: Skeleton3D = motion.rig
	var identities := FIXTURE.identities(player)
	check("actual player binds one 164-bone rig and three LODs",FIXTURE.collect(player,"Skeleton3D").size()==1 and rig.get_bone_count()==164 and lod.report().levels==3 and secondary.configured,{"lod":lod.report(),"secondary":secondary.report()})
	var modifiers := FIXTURE.collect(player,"SkeletonModifier3D")
	check("player has one skeleton writer and its imported animator is paused",modifiers.size()==1 and modifiers[0]==motion and not player.animator.is_playing() and not is_instance_valid(player.hero_pose) and not is_instance_valid(player.traversal_pose))
	var contender := SECONDARY.new()
	player.visual.add_child(contender)
	check("second secondary owner refuses already bound surfaces",not contender.configure(player.visual) and contender._bindings.is_empty())
	contender.free()
	for frame in 30: FIXTURE.step(player,1.0/60,Vector3(2,0,6),float(frame)*.01)
	var pose := FIXTURE.bones(rig)
	var elapsed_before: float = secondary.elapsed
	secondary.update_secondary(1.0/60,{"local_velocity":Vector3(3,0,5),"position":player.position,"yaw":player.visual.rotation.y})
	check("secondary updates real materials without changing any bone",pose==FIXTURE.bones(rig) and secondary.elapsed>elapsed_before and uniform_error(secondary)<.000001,{"maximum_uniform_error_m":uniform_error(secondary)})
	var before_request: Dictionary = secondary.report()
	var accepted: bool = motion.request_action("kodanda",.18,.22)
	check("action request does not reset unrelated follow-through",accepted and before_request==secondary.report())
	for frame in 24: FIXTURE.step(player,1.0/60)
	check("moving draw holds for authoritative release with bounded secondary",motion.action_stage=="hold" and motion.release_count==0 and motion.nocked and secondary.report().finite and secondary.cloth_offset.length()<=SECONDARY.CLOTH_LIMIT and secondary.hair_offset.length()<=SECONDARY.HAIR_LIMIT)
	var before_cancel: Dictionary = secondary.report()
	motion.cancel_action("R4 cancellation witness")
	check("cancel removes nock without release or a secondary reset",not motion.nocked and not motion.nocked_arrow.visible and motion.release_count==0 and before_cancel==secondary.report())
	for frame in 20: FIXTURE.step(player,1.0/60)
	check("cancel fade ends while locomotion secondary continues",motion.action_stage=="none" and secondary.elapsed>before_cancel.elapsed and secondary.reset_count==before_cancel.reset_count)
	motion.request_action("piercing_dawn",.18,.22)
	for frame in 20: FIXTURE.step(player,1.0/60)
	check("release remains explicit and consumed once",motion.release_action("piercing_dawn") and not motion.release_action("piercing_dawn") and motion.release_count==1 and not motion.nocked)
	var level_rows: Array[Dictionary] = []
	var levels_ok := true
	for level in [0,1,2,1,0,2,0]:
		FIXTURE.step(player,1.0/60,Vector3(3,0,5),.6)
		pose = FIXTURE.bones(rig)
		var response: Dictionary = secondary.report()
		lod._apply_level(level)
		var lod_report: Dictionary = lod.report()
		levels_ok = levels_ok and pose==FIXTURE.bones(rig) and response==secondary.report() and lod_report.visible_levels==[level] and lod_report.live_rigs==1 and uniform_error(secondary)<.000001
		level_rows.append({"level":level,"visible_levels":lod_report.visible_levels,"uniform_error_m":uniform_error(secondary)})
	check("LOD switches preserve pose and follow-through; hidden levels receive offsets",levels_ok,{"transitions":level_rows})
	check("motion/cancel/LOD reuse original nodes meshes skins and materials",identities==FIXTURE.identities(player))
	# Real SceneTree pause: enable the player's normal physics callback, then
	# pause before the next frame. The explicit CPU stepping helper is idle.
	player.set_physics_process(true)
	paused = true
	var paused_motion: Dictionary = motion.diagnostics()
	var paused_secondary: Dictionary = secondary.report()
	var paused_lod: Dictionary = lod.report()
	pose = FIXTURE.bones(rig)
	for frame in 4: await process_frame
	check("real tree pause holds action clocks follow-through pose and LOD",paused_motion==motion.diagnostics() and paused_secondary==secondary.report() and paused_lod==lod.report() and pose==FIXTURE.bones(rig))
	player.set_physics_process(false)
	paused = false
	FIXTURE.step(player,1.0/60)
	check("resume advances one declared delta without catch-up reset",is_equal_approx(secondary.elapsed,paused_secondary.elapsed+1.0/60) and secondary.reset_count==paused_secondary.reset_count)
	lod._apply_level(2)
	player.reset()
	check("actual player reset clears action nock secondary and restores near",motion.action_stage=="none" and not motion.nocked and secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.elapsed==0 and lod.level==0 and not player._quality_has_position)
	FIXTURE.step(player,1.0/60)
	player.position += Vector3(20,0,0)
	FIXTURE.step(player,1.0/60)
	check("actual player teleport clears inherited secondary inertia",secondary.cloth_offset==Vector3.ZERO and secondary.hair_offset==Vector3.ZERO and secondary.last_reason=="reset")
	var preserved: MeshInstance3D = secondary._bindings[0].mesh
	preserved.extra_cull_margin = .5
	var foreign := StandardMaterial3D.new()
	var slot: int = secondary._bindings[0].surface
	preserved.set_surface_override_material(slot,foreign)
	player.rama_finish.release()
	secondary.restore_materials()
	check("accepted teardown preserves real foreign material and margin",preserved.get_surface_override_material(slot)==foreign and preserved.extra_cull_margin==.5 and not secondary.configured and secondary._bindings.is_empty())
	var weak_player: WeakRef = weakref(player)
	var weak_rig: WeakRef = weakref(rig)
	player.queue_free()
	await process_frame
	await process_frame
	check("queued actual player teardown releases rig without orphan helper",weak_player.get_ref()==null and weak_rig.get_ref()==null)
	var result := {"passed":checks.all(func(row):return row.passed),"count":checks.size(),"checks":checks,"source_sha256":FIXTURE.pins(),"scope":"Current imported real player rig, manual native CPU motion/pose callbacks plus real SceneTree pause and teardown. LOD levels forced for ownership checks. No imports, 3D rendering, shader execution, skin contact/intersection acceptance or hardware FPS."}
	result.source_sha256[get_script().resource_path] = FileAccess.get_sha256(get_script().resource_path)
	result.source_sha256["res://tests/r4_secondary_fixture.gd"] = FileAccess.get_sha256("res://tests/r4_secondary_fixture.gd")
	FileAccess.open(output,FileAccess.WRITE).store_string(JSON.stringify(result,"  ")+"\n")
	quit(0 if result.passed else 1)
