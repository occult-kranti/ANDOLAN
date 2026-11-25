"""Author five in-place Hanuman Trial actions on the pinned R5 Blender rig.

Pose coordinates are Blender armature-space metres (-Y forward). A separate
editable .blend can retain the new Actions. Only the pose tracks are exported.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Quaternion, Vector

SOURCE_SHA256 = "b27582783f7a68f35225cd0545e7e31e3c09762c736da1e6a689cabaa400e589"
NATIVE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(NATIVE.parent / "yuga/art/pipeline"))
from animations import _sample

DEFINITION = NATIVE / "assets/design/hanuman-ability-kit.json"
RIGHT_READY = (-.28, -.28, 1.25)
LEFT_READY = (.28, -.14, 1.05)
RIGHT_FINGERS = (0, -.50, .65)
LEFT_FINGERS = (0, -.9, -.15)
UP = (0, 0, 1)
TAIL = tuple(f"tail_{index:02}" for index in range(1, 5))


def curve(t, *keys):
    """Blend authored beat values without overshooting their control points."""
    if t <= keys[0][0]:
        return keys[0][1]
    for (before, value), (after, target) in zip(keys, keys[1:]):
        if t <= after:
            u = (t - before) / (after - before)
            weight = u * u * (3 - 2 * u)
            if isinstance(value, tuple):
                return tuple(a + (b - a) * weight for a, b in zip(value, target))
            return value + (target - value) * weight
    return keys[-1][1]


def torso(pose, drop, pitch, yaw, roll=0):
    pose.shift_hips(drop)
    pose.rotate("spine03", x=2 + .25 * pitch, z=.27 * yaw)
    pose.rotate("spine02", x=.76 * pitch, y=roll, z=.73 * yaw)
    pose.rotate("head", x=-.48 * pitch, z=-.55 * yaw)


def feet(pose):
    pose.leg("L", (.21, -.075, .085), (.25, -.60, .55), 24)
    pose.leg("R", (-.21, .045, .085), (-.25, -.60, .55), 24)


def right_arm(pose, hand, shaft=UP, fingers=RIGHT_FINGERS):
    pose.arm("R", hand, (-.46, .04, 1.16), fingers, shaft)
    pose.grip("R", .85)


def left_arm(pose, hand, fingers=LEFT_FINGERS, axis=UP, grip=.65):
    pose.arm("L", hand, (.50, .04, 1.15), fingers, axis)
    pose.grip("L", grip)


def follow_tail(pose, t, yaw=0, pitch=0):
    for index, name in enumerate(TAIL):
        lagged = max(0, t - index * .04)
        weight = math.sin(math.pi * lagged) ** 2 * math.sin(math.pi * t)
        pose.rotate(name, x=pitch * weight * (.6 + .2 * index), z=yaw * weight * (.55 + .17 * index))


def gada(pose, t):
    # Coil behind the shoulder, strike into the front, continue across the body.
    trunk = curve(t, (0, (-.035, 0, 0)), (.11, (-.079, -8, -28)),
                  (.26, (-.089, 16, 23)), (.40, (-.073, 18, 39)), (.62, (-.048, 7, 12)), (1, (-.035, 0, 0)))
    torso(pose, *trunk, roll=4 * math.sin(math.pi * t))
    feet(pose)
    hand = curve(t, (0, RIGHT_READY), (.11, (-.41, .014, 1.52)),
                 (.26, (-.18, -.47, 1.17)), (.40, (.08, -.42, 1.16)), (.62, (-.26, -.40, 1.23)), (1, RIGHT_READY))
    shaft = curve(t, (0, UP), (.11, (-.43, .25, .88)), (.26, (.24, -.94, .23)),
                  (.40, (.92, -.39, .12)), (.53, (.32, -.67, .69)), (.70, (-.43, -.16, .89)), (1, UP))
    fingers = curve(t, (0, RIGHT_FINGERS), (.11, (.05, -.51, .62)),
                    (.26, (.11, -.18, .95)), (.40, (.06, -.55, .68)), (1, RIGHT_FINGERS))
    right_arm(pose, hand, shaft, fingers)
    offhand = curve(t, (0, LEFT_READY), (.11, (.25, -.21, 1.31)),
                    (.26, (.37, -.15, 1.22)), (.40, (.36, .025, 1.14)), (1, LEFT_READY))
    left_arm(pose, offhand)
    follow_tail(pose, t, yaw=-14, pitch=-6)


def ward(pose, t):
    # Gather at the sternum, then open the left palm toward the shield fan.
    trunk = curve(t, (0, (-.035, 0, 0)), (.24, (-.073, 7, -9)),
                  (.50, (-.059, -7, -16)), (.69, (-.055, -4, -13)), (1, (-.035, 0, 0)))
    torso(pose, *trunk)
    feet(pose)
    right = curve(t, (0, RIGHT_READY), (.32, (-.41, -.08, 1.25)), (.62, (-.42, -.012, 1.32)), (1, RIGHT_READY))
    shaft = curve(t, (0, UP), (.26, (-.43, .04, .91)), (.68, (-.44, .05, .89)), (1, UP))
    right_arm(pose, right, shaft)
    left = curve(t, (0, LEFT_READY), (.24, (.17, -.34, 1.31)),
                 (.50, (.30, -.54, 1.57)), (.69, (.36, -.51, 1.59)), (1, LEFT_READY))
    fingers = curve(t, (0, LEFT_FINGERS), (.24, (.14, -.57, .65)),
                    (.50, (-.04, -.14, .99)), (.69, (.08, -.19, .96)), (1, LEFT_FINGERS))
    axis = curve(t, (0, UP), (.31, (1, 0, .32)), (.70, (1, 0, 0)), (1, UP))
    grip = curve(t, (0, .65), (.27, .27), (.50, .015), (.70, .02), (1, .65))
    left_arm(pose, left, fingers, axis, grip)
    follow_tail(pose, t, yaw=9, pitch=5)


def vault(pose, t):
    # Plant, push, fold the leading knee, unfold to contact and absorb the fall.
    # CharacterBody3D owns the actual travelling arc.
    trunk = curve(t, (0, (-.035, 0, 0)), (.044, (-.183, 27, -10)),
                  (.08, (-.069, 17, -6)), (.39, (-.054, 30, 13)), (.72, (-.141, 20, 8)),
                  (.81, (-.158, 21, 6)), (1, (-.035, 0, 0)))
    torso(pose, *trunk)
    stance_left = (.21, -.075, .085)
    stance_right = (-.21, .045, .085)
    left = curve(t, (0, stance_left), (.08, stance_left), (.31, (.26, -.24, .27)),
                 (.49, (.23, -.26, .23)), (.72, stance_left), (1, stance_left))
    right = curve(t, (0, stance_right), (.08, stance_right), (.29, (-.19, .21, .23)),
                  (.48, (-.22, .16, .27)), (.72, stance_right), (1, stance_right))
    toes = curve(t, (0, 24), (.08, 24), (.34, 46), (.72, 24), (1, 24))
    pose.leg("L", left, (.25, -.60, .55), toes)
    pose.leg("R", right, (-.25, -.60, .55), toes)
    hand = curve(t, (0, RIGHT_READY), (.044, (-.36, .045, 1.06)), (.17, (-.48, -.17, 1.14)),
                 (.35, (-.44, -.15, 1.17)), (.72, (-.34, -.18, 1.11)), (1, RIGHT_READY))
    shaft = curve(t, (0, UP), (.08, (-.32, .31, .83)), (.17, (-.56, .02, .83)), (.36, (-.38, .11, .90)),
                  (.72, (-.23, .17, .91)), (1, UP))
    fingers = curve(t, (0, RIGHT_FINGERS), (.25, (.02, -.72, .64)), (.72, RIGHT_FINGERS), (1, RIGHT_FINGERS))
    right_arm(pose, hand, shaft, fingers)
    reach = curve(t, (0, LEFT_READY), (.045, (.33, .07, 1.05)), (.32, (.26, -.54, 1.39)),
                  (.53, (.30, -.45, 1.28)), (.72, (.41, -.29, 1.13)), (1, LEFT_READY))
    left_arm(pose, reach)
    follow_tail(pose, t, yaw=-11, pitch=-6)


def sweep(pose, t):
    # Four delayed tail links carry a rearward whip after planted upper-body torque.
    trunk = curve(t, (0, (-.035, 0, 0)), (.32, (-.147, 9, -34)), (.50, (-.131, 12, 29)),
                  (.66, (-.086, 9, 39)), (.83, (-.058, 3, 13)), (1, (-.035, 0, 0)))
    torso(pose, *trunk, roll=-5 * math.sin(math.pi * t))
    feet(pose)
    right = curve(t, (0, RIGHT_READY), (.31, (-.37, -.11, 1.27)),
                  (.52, (-.32, -.34, 1.30)), (.69, (-.33, -.23, 1.26)), (1, RIGHT_READY))
    right_arm(pose, right)
    left = curve(t, (0, LEFT_READY), (.32, (.22, -.32, 1.25)),
                 (.50, (.37, .025, 1.31)), (.66, (.49, .015, 1.39)), (1, LEFT_READY))
    left_arm(pose, left, grip=curve(t, (0, .65), (.33, .23), (.68, .15), (1, .65)))
    for index, name in enumerate(TAIL):
        delay = index * .029
        yaw = curve(t, (0, 0), (.28 + delay, -24 - 4 * index), (.50 + delay, 37 + 4 * index),
                    (.69 + delay, 16 + 3 * index), (1, 0))
        lift = curve(t, (0, 0), (.31 + delay, -2 - index), (.54 + delay, -11 - 3 * index),
                     (.81 + delay, -6), (1, 0))
        pose.rotate(name, x=lift, z=yaw)


def pulse(pose, t):
    # Deep gather, rise into the release, and drop to the delayed impact beat.
    trunk = curve(t, (0, (-.035, 0, 0)), (.33, (-.176, 17, -11)), (.55, (-.027, -12, 6)),
                  (.68, (-.064, 0, 7)), (.78, (-.219, 31, 2)), (.86, (-.174, 20, 1)), (1, (-.035, 0, 0)))
    torso(pose, *trunk)
    feet(pose)
    right = curve(t, (0, RIGHT_READY), (.34, (-.39, -.10, 1.32)), (.55, (-.31, -.23, 1.86)),
                  (.68, (-.27, -.34, 1.55)), (.78, (-.35, -.40, .91)), (.90, (-.31, -.31, 1.03)), (1, RIGHT_READY))
    shaft = curve(t, (0, UP), (.34, (-.28, .14, .93)), (.55, (-.39, .20, .89)),
                  (.68, (-.20, -.54, .81)), (.78, (-.32, -.86, -.11)), (.90, (-.32, -.28, .75)), (1, UP))
    fingers = curve(t, (0, RIGHT_FINGERS), (.55, (.05, -.66, .62)), (.78, (.14, -.05, .99)), (1, RIGHT_FINGERS))
    right_arm(pose, right, shaft, fingers)
    left = curve(t, (0, LEFT_READY), (.33, (.22, -.30, 1.17)), (.55, (.32, -.39, 1.78)),
                 (.68, (.46, -.26, 1.52)), (.78, (.33, -.33, .89)), (.90, (.30, -.27, .99)), (1, LEFT_READY))
    left_arm(pose, left, grip=curve(t, (0, .65), (.55, .04), (.78, .78), (1, .65)))
    for index, name in enumerate(TAIL):
        delay = index * .018
        angle = curve(t, (0, 0), (.33 + delay, -10 - 2 * index), (.57 + delay, -21 - 3 * index),
                      (.79 + delay, -8 - 2 * index), (1, 0))
        pose.rotate(name, x=angle, z=.34 * angle)


MOVES = {
    "fire": (gada, None, (.11, .40, .62)),
    "cast2": (ward, None, (.24, .69)),
    "cast1": (vault, .72, (.044, .31, .49, .81)),
    "tail_sweep": (sweep, None, (.32, .66, .83)),
    "mountain_pulse": (pulse, .78, (.33, .68, .86)),
}


def bake_action(rig, clip, phases, poses, start, end, release, impact):
    rotation_bones = sorted(set().union(*(p.rot for p in poses)))
    position_bones = sorted(set().union(*(p.loc for p in poses)))
    if "root" in rotation_bones or "root" in position_bones:
        raise ValueError("Trial actions must leave root motion to the actor.")
    action = bpy.data.actions.new(f"TrialMotion_{clip}")
    action.use_fake_user = True
    action["hanuman_release_phase"] = release
    if impact is not None:
        action["hanuman_impact_phase"] = impact
    rig.animation_data.action = action
    previous = {}
    for phase, pose in zip(phases, poses):
        frame = start + phase * (end - start)
        for name in rotation_bones:
            bone = rig.pose.bones[name]
            bone.rotation_mode = "QUATERNION"
            q = pose.rot.get(name, Quaternion((1, 0, 0, 0))).copy()
            if name in previous and q.dot(previous[name]) < 0:
                q.negate()
            previous[name] = q
            bone.rotation_quaternion = q
            bone.keyframe_insert("rotation_quaternion", frame=frame, group=name)
        for name in position_bones:
            bone = rig.pose.bones[name]
            bone.location = pose.loc.get(name, Vector())
            bone.keyframe_insert("location", frame=frame, group=name)
    for channel in action.fcurves:
        for key in channel.keyframe_points:
            key.interpolation = "LINEAR"
    return rotation_bones, position_bones


def sample_action(rig, phases, frames, rotation_bones, position_bones):
    scene = bpy.context.scene
    start, end = frames
    rotations = {name: [] for name in rotation_bones}
    positions = {name: [] for name in position_bones}
    for phase in phases:
        frame = start + phase * (end - start)
        scene.frame_set(int(frame), subframe=frame - int(frame))
        bpy.context.view_layer.update()
        for name in sorted(rotations.keys() | positions.keys()):
            bone = rig.pose.bones[name]
            local = bone.parent.matrix.inverted() @ bone.matrix
            position, rotation, _ = local.decompose()
            if name in rotations:
                rows = rotations[name]
                q = (rotation.x, rotation.y, rotation.z, rotation.w)
                if rows and sum(a * b for a, b in zip(rows[-1], q)) < 0:
                    q = tuple(-x for x in q)
                rows.append(q)
            if name in positions:
                positions[name].append(tuple(position))
    return rotations, positions


def prepare_actions(rig, filename):
    scene = bpy.context.scene
    definitions = json.loads(DEFINITION.read_text())["abilities"]
    releases = {ability["motion"]: ability["motion_phase"] for ability in definitions}
    for track in rig.animation_data.nla_tracks:
        track.mute = True
    rig.animation_data.action = None
    rig.data.pose_position = "POSE"
    output = {}
    for clip, (author, impact, dramatic_beats) in MOVES.items():
        start, end = bpy.data.actions[clip].frame_range
        release = releases[clip]
        phases = set(dramatic_beats) | {release, *(index / 24 for index in range(25))}
        if impact is not None:
            phases.add(impact)
        phases = sorted(phases)
        poses = []
        for phase in phases:
            pose = _sample(rig, "mace", "idle", 0)
            if 0 < phase < 1:
                author(pose, phase)
            poses.append(pose)
        bones = bake_action(rig, clip, phases, poses, start, end, release, impact)
        rotations, positions = sample_action(rig, phases, (start, end), *bones)
        output[clip] = {"release": release, "impact": impact, "source_frames": [start, end],
                        "phases": phases, "rotation": rotations, "position": positions}
    rig.animation_data.action = bpy.data.actions["idle"]
    scene.frame_set(1)
    filename.write_text(json.dumps({"source_sha256": SOURCE_SHA256, "clips": output}, separators=(",", ":")) + "\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tracks", type=Path, required=True)
    parser.add_argument("--blend", type=Path)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    source = Path(bpy.data.filepath)
    if sha256(source.read_bytes()).hexdigest() != SOURCE_SHA256:
        raise ValueError("Open the pinned Hanuman R5 Blender donor.")
    if args.blend is not None and args.blend.resolve() == source.resolve():
        raise ValueError("Choose a separate output for the editable actions.")
    args.tracks.parent.mkdir(parents=True, exist_ok=True)
    prepare_actions(bpy.context.scene.objects["YugaHeroRig"], args.tracks)
    if args.blend is not None:
        args.blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=str(args.blend.resolve()), compress=True)


if __name__ == "__main__":
    main()
