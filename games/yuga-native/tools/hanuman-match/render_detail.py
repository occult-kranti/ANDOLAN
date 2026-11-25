"""Render a reference-camera region or an alternate view of a packed Hanuman scene."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--view", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--profile", type=Path, default=Path(__file__).with_name("reference-profile.json"))
    parser.add_argument("--samples", type=int, default=48)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])

    scene = bpy.context.scene
    profile = json.loads(args.profile.read_text())
    render = scene.render
    camera = scene.camera
    review = profile["review_views"]
    if args.view == "alternate":
        target = Vector(review["alternate_target"])
        orbit = Matrix.Rotation(math.radians(review["alternate_yaw_degrees"]), 3, "Z")
        camera.location = target + orbit @ (camera.location - target)
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.shift_y = 0
        camera.data.lens = review["alternate_lens_mm"]
        render.resolution_x = review["alternate_width"]
        render.resolution_y = render.resolution_x * 3 // 4
    else:
        if args.view not in review["regions"]:
            raise ValueError(f"Unknown view {args.view!r}; use alternate or {', '.join(review['regions'])}")
        left, top, right, bottom = review["regions"][args.view]
        render.resolution_x = review["crop_full_width"]
        render.resolution_y = render.resolution_x * 3 // 4
        render.use_border = True
        render.use_crop_to_border = True
        render.border_min_x = left
        render.border_max_x = right
        render.border_min_y = 1 - bottom
        render.border_max_y = 1 - top
    scene.cycles.samples = args.samples
    args.output.parent.mkdir(parents=True, exist_ok=True)
    render.filepath = str(args.output.resolve())
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
