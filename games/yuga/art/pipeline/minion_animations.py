"""Original, in-place lane and jungle motion; no imported animation clips.

The unchanged hero module supplies only its native-bone quaternion/IK helper.
All seven unit poses and timing below are authored independently. Blender is
Z-up/-Y-forward; export through the existing +Y-up glTF pipeline. The right
wrist uses the existing X-axis handle and palm offset. Grounded guardians have
humanoid locomotion: the naga does not slither and the sentinel does not fly.
"""

import math

import bpy
from animations import FPS, IDENTITY, _Pose, _mix, _smooth


CLIP_NAMES = ("idle", "run", "fire", "defeat")
UNIT_KINDS = ("soldier", "city-watch", "minister", "king", "yaksha", "naga", "sky-sentinel")
# Attack visuals start on the authoritative shot, so their anticipation is
# intentionally short. Contact/release is 120–133 ms, never a late wind-up.
TIMING = {
    "soldier": (24, 18), "city-watch": (26, 18), "minister": (30, 21),
    "king": (34, 27), "yaksha": (32, 27), "naga": (28, 24), "sky-sentinel": (22, 21),
}


def _stance(p, kind):
    heavy = kind in ("king", "yaksha")
    width = .24 if heavy else .18
    drop = -.07 if heavy else -.035
    p.shift_hips(drop)
    p.rotate("spine03", x=7 if kind == "yaksha" else (4 if kind == "sky-sentinel" else 1))
    p.leg("L", (width, -.06, .085), (width, -.65, .52), 24)
    p.leg("R", (-width, .04, .085), (-width, -.65, .52), 24)
    if kind == "soldier":
        p.arm("R", (-.27, -.20, 1.15), (-.47, .10, 1.22), (0, -.4, -.9), (0, -.90, .44))
        # Shield art +X maps to native wrist -Z. This mirrored left-hand
        # orientation presents its boss forward/outward instead of into the body.
        p.arm("L", (.27, -.31, 1.24), (.49, -.10, 1.20), (-.9, -.3, .1), (0, 0, -1))
    elif kind == "city-watch":
        # Right-hand weapon points forward. Left hand supports its receiver.
        p.arm("R", (-.10, -.28, 1.44), (-.43, -.03, 1.34), (0, 0, -1), (0, -1, 0))
        # The left palm meets the receiver 120 mm along the actual weapon
        # axis. Its mirrored palm offset is included, not just the wrist head.
        p.arm("L", (-.10, -.384, 1.231), (.34, -.05, 1.25), (0, -.15, 1), (0, -1, -.15))
    elif kind == "minister":
        p.arm("R", (-.28, -.17, 1.12), (-.45, .05, 1.18), (0, -.75, .45))
        p.arm("L", (.20, -.27, 1.30), (.44, -.01, 1.18), (0, -.5, .8))
        p.rotate("head", x=2)
    elif kind in ("king", "yaksha"):
        p.arm("R", (-.31, -.24, 1.24), (-.53, .03, 1.17), (0, -.6, .6))
        p.arm("L", (.34, -.17, 1.08), (.58, .01, 1.12), (0, -.8, -.2))
    elif kind == "naga":
        p.arm("R", (-.31, -.16, 1.15), (-.48, .03, 1.27), (0, -.65, .65))
        p.arm("L", (.30, -.25, 1.34), (.53, -.03, 1.29), (0, -.95, .2))
        p.rotate("neck01", x=-3)
    else:
        # Folded forearms keep the wing silhouette compact during navigation.
        for side, sign in (("L", 1), ("R", -1)):
            p.arm(side, (.22 * sign, -.23, 1.28), (.52 * sign, .01, 1.43), (0, -.8, -.2))
        p.rotate("head", x=4)
    p.grip("R", .85 if kind != "sky-sentinel" else .45)
    p.grip("L", .10 if kind == "naga" else (.85 if kind in ("soldier", "city-watch", "minister") else .65))


def _sample_unit(rig, kind, clip, phase):
    p = _Pose(rig)
    _stance(p, kind)
    heavy = kind in ("king", "yaksha")
    drop = -.07 if heavy else -.035
    if clip == "idle":
        breath = math.sin(phase * math.tau)
        p.rotate("spine02", x=.65 * breath, z=.8 * breath if kind == "naga" else 0)
        p.rotate("spine01", x=-.35 * breath)
        p.rotate("neck01", x=(-3 if kind == "naga" else 0) + .3 * breath)
        p.shift_hips(drop + .0025 * breath)
    elif clip == "run":
        angle = phase * math.tau
        stride = .22 if heavy else (.20 if kind == "minister" else .29)
        lift_height = .11 if heavy else (.10 if kind == "minister" else .16)
        p.shift_hips(drop - .01 + (.012 if heavy else .018) * math.cos(2 * angle))
        p.rotate("spine05", z=(2 if heavy else 3) * math.sin(angle))
        p.rotate("spine02", x=5 if kind == "minister" else 9, z=-4 * math.sin(angle))
        p.rotate("head", x=-3)
        for side, sign in (("L", 1), ("R", -1)):
            cycle = angle + (0 if side == "L" else math.pi)
            travel = math.sin(cycle)
            lift = max(0, math.cos(cycle)) ** 2
            p.leg(side, ((.23 if heavy else .18) * sign, -stride * travel, .085 + lift_height * lift), (.25 * sign, -.7, .55), 24 + 7 * max(0, -travel))
            if kind == "sky-sentinel":
                p.arm(side, (sign * (.25 + .07 * lift), -.20 + .09 * travel, 1.25 + .09 * lift), (sign * .60, .03, 1.45), (0, -.8, -.2))
        # Weapons remain in their coherent two-hand/shield stance while the
        # torso counter-rotates. A marching grip should not swing through legs.
    elif clip == "fire":
        if phase <= 0 or phase >= 1:
            return p
        seconds = phase * TIMING[kind][1] / FPS
        wind = max(0, 1 - abs(seconds - .055) / .055)
        impact = max(0, 1 - abs(seconds - .125) / .09)
        follow = max(0, 1 - abs(seconds - .23) / .15)
        if kind == "soldier":
            p.rotate("spine02", x=5 * impact, z=-7 * impact + 3 * wind)
            p.arm("R", (-.21, -.20 - .35 * impact + .06 * wind, 1.22), (-.47, -.04, 1.23), (0, -.12, -1), (0, -1, .12))
            p.arm("L", (.27, -.31 - .035 * impact, 1.24), (.49, -.10, 1.20), (-.9, -.3, .1), (0, 0, -1))
        elif kind == "city-watch":
            recoil = .08 * impact + .025 * follow
            p.rotate("spine02", x=-3 * impact)
            p.arm("R", (-.10, -.28 + recoil, 1.44 + .025 * impact), (-.43, -.03, 1.34), (0, 0, -1), (0, -1, 0))
            p.arm("L", (-.10, -.384 + recoil, 1.231 + .025 * impact), (.34, -.05, 1.25), (0, -.15, 1), (0, -1, -.15))
        elif kind == "minister":
            p.rotate("spine02", x=3 * impact)
            p.arm("L", (.15, -.27 - .28 * impact, 1.30 + .12 * impact), (.43, -.06, 1.30), (0, -.95, .2))
            p.grip("L", .85)
        elif kind in ("king", "yaksha"):
            p.rotate("spine02", x=11 * impact, z=7 * impact - 6 * wind)
            hand = _mix((-.31, -.24, 1.24), (-.30, -.08, 1.60), wind)
            hand = _mix(hand, (-.20, -.56, 1.04), impact)
            p.arm("R", hand, (-.55, -.01, 1.38), _mix((0, -.6, .6), (0, -.12, 1), impact), _mix((0, 0, 1), (0, -1, -.10), impact))
            p.arm("L", (.34, -.17 - .07 * impact, 1.08 + .12 * follow), (.57, .01, 1.15))
        elif kind == "naga":
            p.rotate("spine02", z=-8 * impact + 4 * wind, x=4 * impact)
            p.rotate("neck01", x=-3 + 6 * impact)
            p.arm("L", (.30 - .16 * impact, -.25 - .28 * impact, 1.34 + .08 * impact), (.51, -.05, 1.31), (0, -.98, .1))
            p.grip("L", .1)
        else:
            p.rotate("spine02", x=7 * impact)
            for side, sign in (("L", 1), ("R", -1)):
                p.arm(side, (sign * (.22 + .30 * wind + .16 * follow), -.23 - .28 * impact, 1.28 + .20 * wind + .07 * follow), (sign * (.52 + .09 * wind), -.04, 1.45), (0, -.9, -.1))
    elif clip == "defeat":
        if phase <= 0:
            return p
        fall = _smooth(min(1, phase / .78))
        p.shift_hips(drop - (.40 if heavy else .44) * fall)
        p.rotate("spine05", x=15 * fall)
        p.rotate("spine03", x=(24 if kind == "sky-sentinel" else 20) * fall)
        p.rotate("spine01", x=14 * fall)
        p.rotate("neck01", x=12 * fall)
        p.rotate("head", x=10 * fall)
        for side, sign in (("L", 1), ("R", -1)):
            p.leg(side, ((.23 if heavy else .19) * sign, .12 * fall, .085), (.24 * sign, -.65, .34), 24)
            hand = _mix((.33 * sign, -.22, 1.10), (.36 * sign, -.36, .28), fall)
            p.arm(side, hand, (.58 * sign, -.12, .7), _mix((0, -.9, -.15), (0, -.1, -1), fall), _mix((0, 0, 1), (0, -1, .1), fall))
            p.grip(side, .85 if side == "L" and kind in ("soldier", "minister") else (.6 if side == "R" else .3))
    return p


def author_minion_animations(armature, unit_kind, variant=None):
    """Create four original clips on one rig; leave it in the idle stance.

    ``variant`` is an optional metadata label, not an alternate skeleton. The
    caller owns geometry/export. Existing hero actions and assets are untouched.
    """
    if armature.type != 'ARMATURE' or unit_kind not in UNIT_KINDS:
        raise ValueError(f"Unsupported unit rig/kind: {unit_kind}")
    animation = armature.animation_data_create()
    previous = animation.action
    animation.action = None
    for action in list(bpy.data.actions):
        if action.name.lower() in CLIP_NAMES and (action == previous or not action.users or action.get("yuga_unit_motion")):
            bpy.data.actions.remove(action)
    run_frames, fire_frames = TIMING[unit_kind]
    specs = {
        "idle": (96, [i / 8 for i in range(9)]),
        "run": (run_frames, [i / 8 for i in range(9)]),
        "fire": (fire_frames, sorted({0, 1, *[min(1, t * FPS / fire_frames) for t in (.055, .09, .125, .18, .23, .38, .5)]})),
        "defeat": (33, [0, .10, .24, .42, .62, .78, 1]),
    }
    bpy.context.scene.render.fps = FPS
    actions = {}
    for clip, (duration, phases) in specs.items():
        samples = [_sample_unit(armature, unit_kind, clip, phase) for phase in phases]
        controlled = set().union(*(set(p.rot) | set(p.loc) for p in samples)) | {"root", "spine03"}
        action = bpy.data.actions.new(clip)
        action.use_fake_user = True
        action["yuga_unit_motion"] = True
        action["yuga_unit"] = unit_kind
        action["yuga_variant"] = str(variant or unit_kind)
        action["yuga_loop"] = clip in ("idle", "run")
        action["yuga_root_motion"] = False
        if clip == "fire":
            action["yuga_release_seconds"] = .125
        animation.action = action
        quaternions = {}
        for phase, pose in zip(phases, samples):
            frame = 1 + round(duration * phase)
            for bone in armature.pose.bones:
                bone.rotation_mode = 'QUATERNION'
                q = pose.rot.get(bone.name, IDENTITY).copy()
                if bone.name in quaternions and q.dot(quaternions[bone.name]) < 0:
                    q.negate()
                quaternions[bone.name] = q.copy()
                bone.rotation_quaternion = q
                bone.location = pose.loc.get(bone.name, (0, 0, 0))
                bone.scale = (1, 1, 1)
                if bone.name in controlled:
                    bone.keyframe_insert(data_path="rotation_quaternion", frame=frame, group=bone.name)
                    if bone.name in ("root", "pelvis.L", "pelvis.R", "spine05"):
                        bone.keyframe_insert(data_path="location", frame=frame, group=bone.name)
        for curve in action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = 'LINEAR'
        actions[clip] = action
    animation.action = actions["idle"]
    bpy.context.scene.frame_start = 1
    bpy.context.scene.frame_end = 97
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    return actions


def validate_unit_deformation(armature, body, actions):
    """Evaluate every skin frame: finite motion, bounds, root, loop and attack.

    Use the complete weighted anatomy for body/ground checks. This is not a
    garment collision or subjective animation-quality certificate. It also
    reports hand trajectories and the visible head drop in the defeat pose.
    """
    import numpy as np

    if set(actions) != set(CLIP_NAMES):
        raise AssertionError("Expected the four unit actions")
    scene = bpy.context.scene
    previous, frame_before = armature.animation_data.action, scene.frame_current
    evidence = {}
    try:
        for clip, action in actions.items():
            armature.animation_data.action = action
            first = last = None
            motion = root_motion = 0.
            moved = 0
            bounds = []
            tracks = {name: [] for name in ("wrist.L", "wrist.R", "foot.L", "foot.R", "head")}
            start, end = (round(v) for v in action.frame_range)
            for frame in range(start, end + 1):
                scene.frame_set(frame)
                bpy.context.view_layer.update()
                mesh = body.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
                points = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                mesh.vertices.foreach_get("co", points)
                points = points.reshape((-1, 3))
                if not np.isfinite(points).all():
                    raise AssertionError(f"{clip}/{frame}: nonfinite skin")
                if first is None:
                    first = points.copy()
                distances = np.linalg.norm(points - first, axis=1)
                motion = max(motion, float(distances.max()))
                moved = max(moved, int((distances > .005).sum()))
                bounds.append((points.min(axis=0), points.max(axis=0)))
                last = points.copy()
                root_motion = max(root_motion, armature.location.length, armature.pose.bones["root"].location.length)
                for name in tracks:
                    tracks[name].append(tuple(armature.pose.bones[name].head))
            lower = np.array([b[0] for b in bounds]).min(axis=0)
            upper = np.array([b[1] for b in bounds]).max(axis=0)
            seam = float(np.linalg.norm(last - first, axis=1).max())
            if root_motion > 1e-6 or motion < .001 or float((upper - lower).max()) > 3.5 or float(lower[2]) < -.035:
                raise AssertionError(f"{clip}: invalid root/motion/body bounds {root_motion, motion, lower, upper}")
            if clip in ("idle", "run", "fire") and seam > 1e-4:
                raise AssertionError(f"{clip}: weighted loop gap {seam}")
            if clip == "fire" and max(np.linalg.norm(np.diff(np.array(tracks[name]), axis=0), axis=1).sum() for name in ("wrist.L", "wrist.R")) < .06:
                raise AssertionError("Attack has no meaningful hand trajectory")
            if clip == "defeat" and tracks["head"][0][2] - tracks["head"][-1][2] < .30:
                raise AssertionError("Defeat does not lower the silhouette")
            paths = {name: {"distance": float(np.linalg.norm(np.diff(np.array(values), axis=0), axis=1).sum()), "range": (np.array(values).max(axis=0) - np.array(values).min(axis=0)).tolist()} for name, values in tracks.items()}
            evidence[clip] = {"frames": end - start + 1, "maxVertexMotion": motion, "verticesMoved5mm": moved, "meshMinimum": lower.tolist(), "meshMaximum": upper.tolist(), "rootTranslation": root_motion, "loopGap": seam, "jointPaths": paths}
    finally:
        armature.animation_data.action = previous
        scene.frame_set(frame_before)
        bpy.context.view_layer.update()
    return evidence
