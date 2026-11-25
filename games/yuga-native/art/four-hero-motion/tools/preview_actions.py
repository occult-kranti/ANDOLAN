"""Author in-place performance keys on the existing MakeHuman/YUGA FK/IK solver at 30 fps."""

import math

import bpy
from mathutils import Quaternion, Vector

from animations import _ready, _Pose, _mix, _planted, author_animations

DURATIONS = {
    "shiva": {"fire": 15, "cast": 24, "cast1": 27, "cast2": 30, "cast3": 42},
    "krishna": {"fire": 15, "cast": 24, "cast1": 27, "cast2": 30, "cast3": 48},
}


def envelope(frame, keys):
    for (start, a), (end, b) in zip(keys, keys[1:]):
        if frame <= end:
            t = max(0, (frame - start) / (end - start))
            return a + (b - a) * t * t * (3 - 2 * t)
    return keys[-1][1]


def shiva_pose(rig, clip, frame, end):
    pose = _Pose(rig)
    _ready(pose, "staff")
    if clip == "cast3":
        coil = envelope(frame, [(0, 0), (8, 0.35), (15, 1), (19, 1), (24, 0), (end, 0)])
        impact = envelope(
            frame, [(0, 0), (19, 0), (24, 1), (27, 0.88), (35, 0.25), (end, 0)]
        )
        _planted(pose, -0.035 + 0.055 * coil - 0.16 * impact)
        pose.leg(
            "L",
            (0.21, -0.075 - 0.065 * coil, 0.085 + 0.39 * coil),
            (0.27, -0.65, 0.64),
            24 + 15 * coil,
        )
        pose.rotate("spine02", x=-11 * coil + 15 * impact, z=-13 * coil + 9 * impact)
        pose.rotate("head", x=4 * coil - 8 * impact)
        pose.arm(
            "R",
            (-0.29, -0.19 - 0.13 * impact, 1.13 + 0.53 * coil - 0.20 * impact),
            (-0.58, -0.02, 1.44),
            (0, -0.84, 0.36),
            (0.10 * coil, -0.10 * impact, 1),
        )
        pose.arm(
            "L",
            (
                0.27 + 0.19 * coil,
                -0.21 - 0.12 * impact,
                1.13 + 0.36 * coil - 0.04 * impact,
            ),
            (0.58, 0.02, 1.43),
        )
    elif clip == "cast2":
        wave = envelope(frame, [(0, 0.45), (5, 1), (13, 0.82), (22, 0.37), (end, 0)])
        pose.rotate("spine02", z=-13 * wave, x=6 * wave)
        pose.rotate("neck01", z=8 * wave)
        pose.arm(
            "L",
            (
                0.24 + 0.16 * wave,
                -0.21 - 0.24 * wave,
                1.13 + 0.06 * math.sin(2 * math.pi * frame / end),
            ),
            (0.55, -0.12, 1.36),
            (0, -1, 0.1),
        )
        pose.grip("L", 0.10)
    else:
        wave = envelope(frame, [(0, 0.68), (3, 1), (end * 0.48, 0.62), (end, 0)])
        side = 1 if clip == "fire" else -1
        amp = 0.60 if clip == "cast" else 1.0
        strike = wave * amp
        pose.rotate("spine02", z=side * 20 * strike, x=7 * strike)
        pose.arm(
            "R",
            (
                -0.29 + (0.28 if side < 0 else 0.05) * strike,
                -0.19 - 0.27 * strike,
                1.13 + 0.17 * strike,
            ),
            (-0.53, -0.07, 1.36),
            (0, -0.45, -0.88),
            (0.53 * strike * side, -0.84 * strike, 1.0 - 0.85 * strike),
        )
        pose.arm(
            "L",
            (0.29 + 0.085 * strike, -0.19 + 0.09 * strike, 1.12 + 0.17 * strike),
            (0.55, 0, 1.4),
        )
    pose.grip("R", 0.84)
    return pose


def finger_pad(pose, side):
    name = "finger2-3." + side
    origin, facing = pose.world(name)
    return origin + facing @ Vector((0, 0.8 * pose.bones[name].length, 0))


def cover_flute_hole(pose, target, weight):
    # Keep the authored curled hand, adjusting only three left-index phalanges.
    target = finger_pad(pose, "L").lerp(target, weight)
    for _ in range(4):
        for segment in (3, 2, 1):
            name = f"finger2-{segment}.L"
            pivot, orientation = pose.world(name)
            tip = finger_pad(pose, "L")
            if (target - tip).length_squared < 0.000004:
                return
            turn = (tip - pivot).rotation_difference(target - pivot)
            if turn.angle > math.radians(18):
                turn = Quaternion(turn.axis, math.radians(18))
            pose.orient(name, turn @ orientation)


def krishna_pose(rig, clip, frame, end):
    pose = _Pose(rig)
    _ready(pose, "chakram")
    parked = 0.0
    if clip == "cast3":
        lift = envelope(
            frame,
            [(0, 0), (7, 0.19), (17, 0.65), (26, 0.92), (30, 1), (36, 1), (end, 0)],
        )
        parked = envelope(frame, [(0, 0), (6, 1), (36, 1), (end, 0)])
        _planted(pose, -0.035 - 0.042 * math.sin(lift * math.pi))
        pose.rotate("spine02", z=-11 * lift, x=-6 * lift)
        pose.rotate("head", x=-14 * lift, z=5 * lift)
        pose.arm(
            "L",
            (0.28 - 0.10 * lift, -0.19 + 0.075 * lift, 1.12 + 0.78 * lift),
            (0.49, -0.04, 1.53),
            (0, -0.83, 0.52),
            (1, 0, 0),
        )
        pose.arm(
            "R",
            (-0.29 - 0.12 * lift, -0.27 + 0.06 * lift, 1.25 - 0.17 * lift),
            (-0.56, -0.02, 1.27),
        )
        pose.grip("L", 0.68 * lift)
        for j in range(1, 4):
            pose.rotate(f"finger2-{j}.L", x=-6 * lift)
        pose.grip("R", 0.75 - 0.65 * lift)
    elif clip == "cast2":
        melody = envelope(frame, [(0, 0.36), (5, 1), (17, 1), (23, 0.61), (end, 0)])
        pose.rotate("neck01", z=-6 * melody)
        pose.rotate("head", x=4 * melody)
        # Solve the near-end blow hole against a head-relative lower-lip landmark.
        # Distances within the rigid bamboo stay in metres; _Pose.arm targets
        # are normalized to this character's source skeleton stature.
        forward, bore = (0, -1, -0.10), (1, -0.18, -0.13)
        pose.hand_orientation("wrist.L", forward, bore)
        hand_orientation = pose.world("wrist.L")[1]
        head_rotation = pose.world("head")[1] @ pose.rest["head"].inverted()
        lip = pose.world("oris01")[0] + head_rotation @ (
            Vector((0, -0.024, 0.020)) * pose.scale
        )
        blow_hole = Vector((-0.248, 0.0935, -0.025))
        held_wrist = lip - hand_orientation @ blow_hole
        pose.arm(
            "L",
            _mix((0.28, -0.17, 1.12), held_wrist / pose.scale, melody),
            (0.49, 0.025, 1.42),
            forward,
            bore,
        )
        pose.grip("L", 0.80)
        far_hole = pose.world("wrist.L")[0] + hand_orientation @ Vector(
            (0.010, 0.0935, -0.025)
        )
        cover_flute_hole(pose, far_hole, melody)
        # The opposite index reaches the third finger hole while the far hand
        # supports the barrel. Solve its fingertip pad, so hand size is retained.
        pose.hand_orientation("wrist.R", forward, bore)
        pose.grip("R", 0.76)
        index_offset = finger_pad(pose, "R") - pose.world("wrist.R")[0]
        finger_hole = held_wrist + hand_orientation @ Vector((-0.118, 0.0935, -0.025))
        target = (finger_hole - index_offset) / pose.scale
        pose.arm(
            "R",
            _mix((-0.29, -0.27, 1.25), target, melody),
            (-0.44, -0.20, 1.38),
            forward,
            bore,
        )
        pose.grip("R", 0.76 - 0.10 * math.sin(frame * math.pi / 4) * melody)

    else:
        sweep = envelope(frame, [(0, 0.70), (3, 1), (end * 0.47, 0.69), (end, 0)])
        if clip == "cast":
            sweep *= 0.52
        pose.rotate("spine02", z=20 * sweep)
        pose.rotate("neck01", z=-12 * sweep)
        pose.arm(
            "R",
            (-0.29 + 0.16 * sweep, -0.27 - 0.27 * sweep, 1.25 + 0.16 * sweep),
            (-0.58, -0.04, 1.44),
            (0.4 * sweep, -1, 0.10),
            (0, 0.20, 1),
        )
        pose.arm(
            "L",
            (0.28 + 0.055 * sweep, -0.17 + 0.065 * sweep, 1.12 + 0.08 * sweep),
            (0.52, 0.02, 1.25),
        )
        pose.grip("R", 0.62 - 0.45 * sweep)
    # Translate the flute to its belt sling while the left hand lifts the canopy.
    if parked:
        hand, orientation = pose.world("wrist.L")
        socket = rig.data.bones["bansuri"]
        target = Vector((0.158, 0.045, 0.95)) * pose.scale
        delta = orientation.inverted() @ (target - hand)
        pose.loc["bansuri"] = delta * parked
        pose.cache.clear()
        pose.rotate("bansuri", x=48 * parked)
    return pose


def author(rig, hero):
    weapon = "staff" if hero == "shiva" else "chakram"
    actions = author_animations(rig, weapon, hero)
    rig.animation_data.action = None
    for clip, end in DURATIONS[hero].items():
        bpy.data.actions.remove(actions[clip], do_unlink=True)
        action = bpy.data.actions.new(clip)
        action.use_fake_user = True
        action["animation_role"] = hero + " motion study"
        rig.animation_data.action = action
        previous = {}
        keyed_frames = {0, 1, end, *range(3, end, 3)}
        if hero == "krishna" and clip == "cast2":
            keyed_frames.update((5, 17))
        for f in sorted(keyed_frames):
            pose = (shiva_pose if hero == "shiva" else krishna_pose)(rig, clip, f, end)
            for name in sorted(
                set(pose.rot)
                | set(pose.loc)
                | {"root", "pelvis.L", "pelvis.R", "spine05"}
                | ({"chakra", "bansuri"} if hero == "krishna" else set())
            ):
                pb = rig.pose.bones[name]
                pb.rotation_mode = "QUATERNION"
                q = pose.rot.get(name)
                if q is None:
                    pb.rotation_quaternion = (1, 0, 0, 0)
                else:
                    q = q.copy()
                    if name in previous and q.dot(previous[name]) < 0:
                        q.negate()
                    previous[name] = q.copy()
                    pb.rotation_quaternion = q
                pb.location = pose.loc.get(name, (0, 0, 0))
                pb.keyframe_insert(
                    data_path="rotation_quaternion", frame=f + 1, group=name
                )
                if name in {"root", "pelvis.L", "pelvis.R", "spine05", "bansuri"}:
                    pb.keyframe_insert(data_path="location", frame=f + 1, group=name)
                if name == "chakra":
                    release = (
                        envelope(
                            f, [(0, 0.18), (2, 0.03), (end * 0.55, 0.03), (end, 1)]
                        )
                        if clip in ("fire", "cast1")
                        else (
                            1 - envelopescale(f, end)
                            if clip in ("cast2", "cast3")
                            else 1
                        )
                    )
                    pb.scale = (release,) * 3
                    pb.keyframe_insert(data_path="scale", frame=f + 1, group=name)
        for curve in action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "LINEAR"
        actions[clip] = action
    return actions


def envelopescale(f, end):
    return envelope(f, [(0, 0), (5, 0.98), (end * 0.70, 0.98), (end, 0)])
