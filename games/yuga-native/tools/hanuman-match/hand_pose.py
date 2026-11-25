"""Pose the belt-side fist on Hanuman's existing articulated hand."""

from __future__ import annotations

import math

import bpy
from mathutils import Euler, Matrix, Vector


DEFAULT_CURL = (
    (39, 52, 35),
    (42, 57, 38),
    (45, 58, 37),
    (44, 53, 33),
)
DEFAULT_THUMB = (
    (-14, 8, -10),
    (11, 7, -20),
    (6, 1, -18),
)
DEFAULT_TRAVEL = (-.91, .13, -.28)
DEFAULT_DORSAL = (.02, -.99, .16)


def frame(forward, dorsal):
    along = Vector(forward).normalized()
    across = along.cross(Vector(dorsal).normalized())
    if across.length <= 1e-6:
        raise ValueError("Hand travel and dorsal directions must define a plane")
    across.normalize()
    normal = across.cross(along)
    return Matrix((across, along, normal)).transposed()


def digits(bones, digit):
    return [bones[f"finger{digit}-{segment}.L"] for segment in (1, 2, 3)]


def aim_palm(rig, travel, dorsal):
    wrist = rig.pose.bones["wrist.L"]
    rest = wrist.bone
    metacarpal_axis = rig.data.bones["finger3-1.L"].head_local - rest.head_local
    source = frame(metacarpal_axis, rest.matrix_local.to_3x3().col[2])
    target = frame(travel, dorsal)
    orientation = target @ source.transposed() @ rest.matrix_local.to_3x3()
    pose = orientation.to_4x4()
    pose.translation = wrist.head
    wrist.matrix = pose


def local_rotation(bone, xyz_degrees):
    rotation = Euler(tuple(math.radians(angle) for angle in xyz_degrees), "XYZ")
    bone.matrix_basis = rotation.to_matrix().to_4x4()


def apply(rig, profile):
    """Adjust the left palm, finger curl and thumb opposition in the still pose."""
    config = profile.get("hip_hand", {})
    if not config.get("enabled", True):
        return {"enabled": False}

    fingers = config.get("finger_curl_degrees", DEFAULT_CURL)
    thumb = config.get("thumb_euler_degrees", DEFAULT_THUMB)
    if len(fingers) != 4 or any(len(curls) != 3 for curls in fingers):
        raise ValueError("Set three curl angles for each of four fingers")
    if len(thumb) != 3 or any(len(rotation) != 3 for rotation in thumb):
        raise ValueError("Set three local rotation axes for each thumb segment")
    travel = config.get("travel", DEFAULT_TRAVEL)
    dorsal = config.get("dorsal", DEFAULT_DORSAL)
    aim_palm(rig, travel, dorsal)
    for digit, curls in enumerate(fingers, start=2):
        for bone, curl in zip(digits(rig.pose.bones, digit), curls):
            local_rotation(bone, (0, 0, -curl))
    for bone, rotation in zip(digits(rig.pose.bones, 1), thumb):
        local_rotation(bone, rotation)

    bpy.context.view_layer.update()
    return {
        "enabled": True,
        "wrist_m": list(rig.pose.bones["wrist.L"].head),
        "middle_knuckle_m": list(rig.pose.bones["finger3-1.L"].head),
        "travel": list(travel),
        "dorsal": list(dorsal),
        "finger_curl_degrees": list(fingers),
        "thumb_euler_degrees": list(thumb),
    }
