extends SceneTree
## Bake native RamaMotion's solved joints on level ground into a portable, reproducible clip cache.
const Motion = preload("res://scripts/rama_motion.gd")
const KIT := "res://assets/design/rama-ability-kit.json"
const HERO := "res://assets/heroes/rama-hero.glb"
const RATE := 60

func _initialize() -> void:
    call_deferred("capture")

func capture() -> void:
    var args := OS.get_cmdline_user_args()
    if args.size() < 1 or args.size() > 2:
        push_error("Supply a new capture JSON path and optional global-pose oracle JSON path")
        quit(1)
        return
    var kit: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(KIT))
    var clips := {}
    var muzzles := {}
    var oracle := {}
    var bone_names := []
    for rule in kit.abilities:
        var scene: Node3D = load(HERO).instantiate()
        root.add_child(scene)
        var motion := Motion.new()
        if not motion.configure(scene, scene.find_children("*","AnimationPlayer",true,false)[0]):
            push_error("Rig and original motion library disagree")
            quit(1)
            return
        var skel: Skeleton3D = motion.rig
        if bone_names.is_empty():
            for joint in skel.get_bone_count(): bone_names.append(skel.get_bone_name(joint))
        var state := {"grounded":true,"floor_y":0.0, "aiming":false}
        for warm in 24:
            motion.update_motion(1.0/RATE, state)
            motion.evaluate_pose()
        if not motion.request_action(rule.id, rule.windup_s, rule.recovery_s):
            push_error("Original controller rejected " + str(rule.id))
            quit(1)
            return
        var pair:Array=Motion.ACTIONS[rule.id]
        for stage in 2:
            var name_: String = pair[stage]
            if rule.id == "measured_step" and stage == 1: name_ = "dash_release"
            var duration: float = rule.windup_s if stage == 0 else rule.recovery_s
            if stage == 1 and not motion.release_action(rule.id):
                push_error("Original controller failed release")
                quit(1)
                return
            var count := ceili(duration * RATE)
            var samples := []
            var observations := []
            for frame in range(count + 1):
                if frame > 0:
                    motion.update_motion(duration / count, state)
                motion.evaluate_pose()
                if not motion.finite:
                    push_error("Nonfinite native sampled pose")
                    quit(1)
                    return
                var row := []
                var global_values := []
                for joint in skel.get_bone_count():
                    var position := skel.get_bone_pose_position(joint)
                    var rotation := skel.get_bone_pose_rotation(joint)
                    row.append_array([position.x, position.y, position.z, rotation.x, rotation.y, rotation.z, rotation.w])
                    if args.size() == 2:
                        var pose := skel.get_bone_global_pose(joint)
                        for col in [pose.basis.x, pose.basis.y, pose.basis.z, pose.origin]:
                            global_values.append_array([col.x, col.y, col.z])
                if args.size() == 2:
                    observations.append({"time":duration*frame/count,"values":global_values})
                samples.append(row)
            clips[name_] = {"duration":duration,"samples":samples}
            oracle[name_] = observations
            if stage == 0 and rule.has("speed_mps"):
                var muzzle: Vector3 = motion.socket_global("arrow_muzzle").origin
                muzzles[rule.id] = [muzzle.x, muzzle.y, muzzle.z]
        scene.free()
    var out := FileAccess.open(args[0],FileAccess.WRITE)
    out.store_string(JSON.stringify({"bones":bone_names,"clips":clips,"muzzles":muzzles}, "",true,true))
    out.close()
    if args.size() == 2:
        var report := FileAccess.open(args[1],FileAccess.WRITE)
        report.store_string(JSON.stringify({"hero_id":"rama", "engine":Engine.get_version_info().string,
            "source_glb_sha256":FileAccess.get_sha256(HERO), "source_motion_sha256":FileAccess.get_sha256(Motion.LIBRARY_PATH),
            "bones":bone_names, "clips":oracle}, "",true,true))
        report.close()
    print("Captured ", clips.size(), " action-stage clips and ", bone_names.size(), " native joints")
    quit()
