extends SceneTree
## Capture the native trial's actual AnimationPlayer poses for check_hero_pose.mjs.
## Run in a scratch Godot project containing imported base.glb and motion.tres.

func _initialize() -> void:
    call_deferred("capture")

func capture() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() != 1:
        push_error("Supply a new native reference JSON path")
        quit(1)
        return
    var original: Node = load("res://base.glb").instantiate()
    root.add_child(original)
    var player: AnimationPlayer = original.find_children("*", "AnimationPlayer", true, false)[0]
    var skeleton: Skeleton3D = original.find_children("*", "Skeleton3D", true, false)[0]
    var revised: AnimationLibrary = load("res://motion.tres")
    if player.add_animation_library(&"trial", revised) != OK:
        push_error("Cannot install native source motion")
        quit(1)
        return
    var names := []
    for bone in skeleton.get_bone_count():
        names.append(skeleton.get_bone_name(bone))
    var clips := {}
    for clip in revised.get_animation_list():
        var source_name := "trial/" + clip
        var animation := player.get_animation(source_name)
        var phases: Array[float] = []
        # Include quarter-key intervals and the exact authored release / landing.
        for tick in range(97):
            phases.append(tick / 96.0)
        for key in [&"hanuman_release_phase", &"hanuman_impact_phase"]:
            if animation.has_meta(key):
                phases.append(float(animation.get_meta(key)))
        phases.sort()
        player.stop()
        skeleton.reset_bone_poses()
        player.play(source_name)
        var samples := []
        for phase in phases:
            var time := animation.length * phase
            player.seek(time, true)
            var values := []
            for bone in names.size():
                var transform := skeleton.get_bone_global_pose(bone)
                for column in [transform.basis.x, transform.basis.y, transform.basis.z, transform.origin]:
                    values.append(column.x)
                    values.append(column.y)
                    values.append(column.z)
            samples.append({"time":time, "values":values})
        clips[clip] = samples
    var file := FileAccess.open(args[0], FileAccess.WRITE)
    if not file:
        push_error("Cannot open reference output")
        quit(1)
        return
    file.store_string(JSON.stringify({"engine":Engine.get_version_info().string, "bones":names, "clips":clips,
        "source_glb_sha256":FileAccess.get_sha256("res://base.glb"), "source_motion_sha256":FileAccess.get_sha256("res://motion.tres")}, "", true, true))
    file.close()
    print("Wrote %d source clips, %d joints to %s" % [clips.size(), names.size(), args[0]])
    quit()
