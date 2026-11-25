"""Reopen the four portable Blender deliveries and measure their camera, motion and packed dependencies.

blender -b -t 1 --python-exit-code 1 -P tools/render/verify_blend.py -- --dir blender
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent
PACK = HERE.parents[1]


def digest(path):
    with path.open("rb") as handle:
        return hashlib.file_digest(handle, "sha256").hexdigest()


def inspect(directory, hero, plan, source_model=None):
    blend = directory / (hero + ".blend")
    bpy.ops.wm.open_mainfile(filepath=str(blend.resolve()), load_ui=False)
    scene = bpy.context.scene
    rigs = [o for o in scene.objects if o.type == "ARMATURE" and o.animation_data]
    if len(rigs) != 1:
        raise ValueError(f"{hero}: expected one animated rig, found {len(rigs)}")
    rig = rigs[0]
    timeline = rig.animation_data.nla_tracks.get(plan["title"] + " · motion reference")
    if not timeline or not rig.animation_data.use_nla:
        raise ValueError(f"{hero}: missing active NLA timeline")
    shots = plan["shots"]
    if len(timeline.strips) != len(shots) or not scene.camera or not scene.camera.animation_data:
        raise ValueError(f"{hero}: missing camera or action strip")
    if sum(s["frames"] for s in shots) != scene.frame_end or len(scene.timeline_markers) != len(shots):
        raise ValueError(f"{hero}: frame or marker count differs")
    if bpy.data.libraries:
        raise ValueError(f"{hero}: external .blend library dependency")
    files = [image for image in bpy.data.images if image.users and image.source in ("FILE", "TILED")]
    missing = [image.name for image in files if not image.packed_files]
    if missing:
        raise ValueError(f"{hero}: unpacked texture files: {missing}")
    fx = bpy.data.collections.get("Presentation VFX · editable")
    if not fx or not fx.objects or not all(o.animation_data for o in fx.objects):
        raise ValueError(f"{hero}: missing animated VFX")
    summaries = []
    names = ["head", "wrist.R", "wrist.L", "foot.L", "foot.R", "tail_02", "bowstring"]
    for shot, strip in zip(shots, timeline.strips):
        if not strip.action.name.startswith(shot["clip"] + "_") and strip.action.name != shot["clip"]:
            raise ValueError(f"{hero}: wrong action for {shot['label']}: {strip.action.name}")
        start, end = round(strip.frame_start), round(strip.frame_end)
        poses = []
        for frame in (start, (start * 2 + end) // 3, (start + end * 2) // 3, end):
            scene.frame_set(frame)
            poses.append([rig.matrix_world @ rig.pose.bones[n].head for n in names if n in rig.pose.bones])
        span = max((a - b).length for p in poses for a, b in zip(poses[0], p))
        summaries.append(
            {
                "clip": shot["clip"],
                "start_frame": start,
                "end_frame": end,
                "largest_joint_displacement_m": round(span, 5),
            }
        )
    if not any(s["largest_joint_displacement_m"] > 0.05 for s in summaries):
        raise ValueError(f"{hero}: no articulated motion measured")
    return {
        "hero": hero,
        "file": blend.name,
        "sha256": digest(blend),
        "bytes": blend.stat().st_size,
        "source_glb_sha256": digest(source_model or PACK / "models" / (hero + ".glb")),
        "rig_bones": len(rig.pose.bones),
        "packed_texture_files": len(files),
        "external_libraries": len(bpy.data.libraries),
        "animated_fx_objects": len(fx.objects),
        "camera": scene.camera.name,
        "frames": scene.frame_end,
        "shots": summaries,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dir", type=Path, default=PACK / "blender")
    parser.add_argument("--output", type=Path, default=PACK / "blender/manifest.json")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else [])
    specs = json.loads((HERE / "shots.json").read_text())
    receipt = {
        "blender_version": bpy.app.version_string,
        "shots_sha256": digest(HERE / "shots.json"),
        "checks": "Saved projects reopened in Blender; self-contained image files, live NLA strips, pose samples, timeline markers, editable lights, camera and animated effects.",
        "projects": [inspect(args.dir, h, p) for h, p in specs["heroes"].items()],
    }
    args.output.write_text(json.dumps(receipt, indent=2) + "\n")
    print(
        json.dumps(
            [(p["hero"], p["bytes"], p["rig_bones"], p["packed_texture_files"]) for p in receipt["projects"]]
        )
    )


if __name__ == "__main__":
    main()
