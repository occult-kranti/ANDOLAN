"""Render repeatable views of a Hanuman GLB with the existing YUGA Cycles studio.

Example (run from repository root):
  blender -b -t 2 --python-exit-code 1 -P \
    games/yuga-native/art/hanuman-visual-qa-2026/render_views.py -- \
    --model games/yuga-native/art/hanuman-hero-finish/models/hanuman-enhanced.glb \
    --output /tmp/hanuman-baseline

The same script, camera gates, source action phases, lights, color management,
samples, and dimensions must be used for each model to make a matched review.
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy

HERE = Path(__file__).resolve().parent
ART = HERE.parent
sys.path.insert(0, str(ART / "hanuman-hero-finish/render"))
from studio import camera_at, describe, init, select_pose, snap  # noqa: E402


VIEWS = (
    # name, action, normalized phase, azimuth, elevation, center XYZ, width metres
    ("face-front", "idle", .18, 0, 3.5, (0, -.084, 1.81), .62),
    ("face-three-quarter", "idle", .18, -26, 3.5, (0, -.084, 1.81), .62),
    ("face-profile", "idle", .18, 90, 3.5, (0, -.084, 1.81), .62),
    ("figure-front", "idle", .18, 0, 2, (.09, 0, 1.075), 1.83),
    ("head-rear", "idle", .18, 180, 3.5, (0, -.04, 1.78), .76),
    ("arm-front", "idle", .18, 0, 2, (.38, -.15, 1.37), .72),
)


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=12)
    parser.add_argument("--threads", type=int, default=2)
    parser.add_argument("--width", type=int, default=480)
    parser.add_argument("--height", type=int, default=622)
    parser.add_argument("--views", nargs="+", choices=[v[0] for v in VIEWS])
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    if min(args.samples, args.threads, args.width, args.height) < 1:
        parser.error("samples, threads, width and height must be positive")
    model = args.model.resolve(strict=True)
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene, rig, camera, lights = init(model, args.threads, args.samples, False)
    notes = []
    for name, action, phase, az, el, center, width in VIEWS:
        if args.views and name not in args.views:
            continue
        select_pose(rig, action, phase)
        camera_at(camera, lights, az, el, center, width)
        path = output / (name + ".png")
        print("YUGA_VIEW", name, "rendering", flush=True)
        snap(scene, path, (args.width, args.height))
        notes.append({
            "name": name,
            "image": path.name,
            "sha256": digest(path),
            "azimuth_degrees": az,
            "elevation_degrees": el,
            "center_world_m": center,
            **describe(scene, rig, camera, action, phase),
        })
        print("YUGA_VIEW", name, "complete", flush=True)
    receipt = {
        "scope": "Blender skinned-mesh stills; not an in-game render, motion acceptance or GPU benchmark",
        "source": str(model),
        "source_sha256": digest(model),
        "blender": bpy.app.version_string,
        "renderer": "Cycles CPU",
        "samples": args.samples,
        "denoising_requested": scene.cycles.use_denoising,
        "resolution": [args.width, args.height],
        "color_transform": scene.view_settings.view_transform,
        "look": scene.view_settings.look,
        "seed": scene.cycles.seed,
        "lights": [{"name": obj.name, "watts": obj.data.energy, "color": list(obj.data.color),
                    "diameter": obj.data.size} for obj, _ in lights],
        "views": notes,
    }
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("YUGA_RENDER_RECEIPT", output / "receipt.json", flush=True)


if __name__ == "__main__":
    main()
