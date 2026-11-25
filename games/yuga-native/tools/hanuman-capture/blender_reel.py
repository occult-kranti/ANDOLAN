"""Render the saved Hanuman rig and authored clips using a shot list.

Run inside Blender against the packed hanuman.blend. The reel stages the
original in-place clips on their studio plinth and includes no simulated hits.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
STORYBOARD = Path(__file__).with_name("storyboard.json")
PROFILE = ROOT / "assets/design/hanuman-ability-kit.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def plan_shots(storyboard, profile, selected):
    actions = bpy.data.actions
    rules = {value["id"]: value for value in profile["abilities"]}
    fps = int(storyboard["fps"])
    if not 8 <= fps <= 30:
        raise ValueError("The shot sample rate must be 8 to 30 fps")
    clock = 0
    for shot in storyboard["shots"]:
        if selected and shot["id"] != selected:
            continue
        rule = rules.get(shot.get("ability"), {})
        name = rule.get("motion", shot.get("motion"))
        clip = actions.get(name)
        count = round(float(shot["duration_s"]) * fps)
        if not clip or not 2 <= count <= fps * 4:
            raise ValueError(f"Missing action or invalid duration for {shot['id']}")
        start, end = map(float, clip.frame_range)
        yield {**shot, "clip": name, "first_frame": clock, "frame_count": count,
               "source_range": [start, end], "motion_cue_ratio": rule.get("motion_phase")}
        clock += count


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--output", type=Path, required=True)
    cli.add_argument("--shot", help="Render only this shot from the same storyboard")
    cli.add_argument("--one-frame", action="store_true", help="Render a single midpoint from each shot")
    args = cli.parse_args(sys.argv[sys.argv.index("--") + 1:])
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    storyboard = json.loads(STORYBOARD.read_text())
    profile = json.loads(PROFILE.read_text())
    shots = list(plan_shots(storyboard, profile, args.shot))
    if not shots:
        raise ValueError("No storyboard shot matches the selection")
    scene = bpy.context.scene
    rigs = [obj for obj in scene.objects if obj.type == "ARMATURE"]
    if len(rigs) != 1 or scene.camera is None:
        raise ValueError("Expected the packed Hanuman studio with one armature and a camera")
    rig = rigs[0]
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = int(storyboard["samples"])
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.use_persistent_data = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.resolution_x = int(storyboard["width"])
    scene.render.resolution_y = int(storyboard["height"])
    scene.render.resolution_percentage = 100
    scene.render.fps = int(storyboard["fps"])
    receipt = {
        "complete": False, "blender": bpy.app.version_string,
        "blend_sha256": digest(Path(bpy.data.filepath)),
        "storyboard_sha256": digest(STORYBOARD), "profile_sha256": digest(PROFILE),
        "script_sha256": digest(Path(__file__)), "fps": scene.render.fps,
        "size": [scene.render.resolution_x, scene.render.resolution_y], "samples": scene.cycles.samples,
        "shots": shots, "frames": [], "midpoints_only": args.one_frame,
        "scope": "Blender software renders of authored in-place action clips",
    }
    def save_receipt():
        (output / "render.json").write_text(json.dumps(receipt, indent=2) + "\n")

    save_receipt()
    for shot in shots:
        rig.animation_data.action = bpy.data.actions[shot["clip"]]
        indices = [shot["frame_count"] // 2] if args.one_frame else range(shot["frame_count"])
        for index in indices:
            t = index / (shot["frame_count"] - 1)
            angle = math.radians((1 - t) * shot["camera_from_deg"] + t * shot["camera_to_deg"])
            scene.camera.location = (math.sin(angle) * 7.5, -math.cos(angle) * 7.5, 2.42)
            scene.camera.rotation_euler = (Vector((0, 0, shot.get("target_z", 1.17))) - scene.camera.location).to_track_quat("-Z", "Y").to_euler()
            scene.camera.data.ortho_scale = float(shot["scale"])
            first, last = shot["source_range"]
            frame = first + t * (last - first)
            scene.frame_set(math.floor(frame), subframe=frame % 1.0)
            number = shot["first_frame"] + index
            artifact = output / f"frame-{number:05}.png"
            scene.render.filepath = str(artifact)
            bpy.ops.render.render(write_still=True)
            receipt["frames"].append({"frame": number, "shot": shot["id"], "clip_frame": frame,
                                      "file": artifact.name, "sha256": digest(artifact)})
            save_receipt()
    receipt["complete"] = True
    save_receipt()


if __name__ == "__main__":
    main()
