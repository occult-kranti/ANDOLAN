"""Render authored animation landmarks on Hanuman's packed temple court model."""
from __future__ import annotations

import argparse
from hashlib import file_digest
import json
import math
from pathlib import Path
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Matrix, Vector


NATIVE = Path(__file__).resolve().parents[2]
KIT = NATIVE / "assets/design/hanuman-ability-kit.json"
# Angle around the court and the pose to inspect alongside the release.
# Ground travel and combat effects are supplied by the playable trial.
STUDIES = {
    "vajra_gada": (-11, .12, .53, "Follow-through"),
    "vajra_kavacha": (11, .24, .72, "Ward held"),
    "maruti_udayana": (34, .035, .72, "Landing pose"),
    "lanka_dahan": (26, .30, .70, "Tail follow-through"),
    "mountain_pulse": (-26, .33, .78, "Impact"),
}


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def gada_bounds(scene, camera):
    graph = bpy.context.evaluated_depsgraph_get()
    points = []
    for part in scene.objects:
        if part.type == "MESH" and not part.hide_render and "gada" in part.name.lower():
            posed = part.evaluated_get(graph)
            points.extend(world_to_camera_view(scene, camera, posed.matrix_world @ v.co)
                          for v in posed.data.vertices)
    if not points or min(point.z for point in points) <= camera.data.clip_start:
        raise ValueError("The visible gada should be in front of the studio camera.")
    x = [point.x for point in points]
    y = [point.y for point in points]
    margin = min(min(x), min(y), 1-max(x), 1-max(y))
    if margin < .05:
        raise ValueError(f"Keep at least 5% frame padding around the complete gada. Got {margin:.3f}.")
    return {"x": [min(x), max(x)], "y": [min(y), max(y)], "edge_margin": margin}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--actions", type=Path, required=True, help="Blender donor with the five authored TrialMotion actions")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--width", type=int, default=480)
    p.add_argument("--samples", type=int, default=20)
    p.add_argument("--shot", choices=STUDIES, help="Inspect one ability in a new output directory")
    args = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    if args.width < 160 or args.width % 4 or args.samples < 1:
        p.error("Choose a width divisible by four and positive samples")
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    scene = bpy.context.scene
    rig = scene.objects["YugaHeroRig"]
    rules = json.loads(KIT.read_text())["abilities"]
    selected = [rule for rule in rules if not args.shot or rule["id"] == args.shot]
    names = [f"TrialMotion_{rule['motion']}" for rule in selected]
    with bpy.data.libraries.load(str(args.actions.resolve()), link=False) as (source, dest):
        if set(names) - set(source.actions):
            raise ValueError("The input must contain the authored Hanuman ability actions")
        dest.actions = names
    rig.animation_data.use_nla = False
    rig.animation_data.action = None
    # Keep the full weapon swing in frame during the follow-through.
    studio_direction = Vector((.10, -1, .07)).normalized()
    camera = scene.camera
    camera.data.shift_y = 0
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = 6.73
    camera.data.dof.aperture_fstop = 3.5
    scene.render.resolution_x = args.width
    scene.render.resolution_y = args.width * 3//4
    scene.render.resolution_percentage = 100
    scene.render.use_border = False
    scene.render.use_persistent_data = True
    scene.cycles.samples = args.samples
    records = []
    for rule in selected:
        ability = rule["id"]
        angle, anticipate, finish, finish_label = STUDIES[ability]
        rig.animation_data.action = None
        for bone in rig.pose.bones:
            bone.matrix_basis = Matrix.Identity(4)
        action = bpy.data.actions["TrialMotion_"+rule["motion"]]
        release = float(action["hanuman_release_phase"])
        if abs(release - rule["motion_phase"]) > 1e-5:
            raise ValueError(f"{ability} release differs from the kit")
        if "hanuman_impact_phase" in action:
            finish = float(action["hanuman_impact_phase"])
        rig.animation_data.action = action
        start,end = action.frame_range
        direction = Matrix.Rotation(math.radians(angle), 3, 'Z') @ studio_direction
        overhead = ability == "mountain_pulse"
        center = Vector((.025, 0, 1.445 if overhead else 1.15))
        camera.data.lens = 55 if overhead else 70
        camera.location = center + direction * 6.80
        camera.rotation_euler = (center-camera.location).to_track_quat('-Z','Y').to_euler()
        for index, (label,phase) in enumerate((("Anticipation",anticipate),("Release",release),(finish_label,finish))):
            frame = start + (end-start)*phase
            scene.frame_set(math.floor(frame), subframe=frame % 1)
            bounds = gada_bounds(scene, camera) if overhead else None
            path = out / f"{ability}-{index+1}.png"
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            records.append({"id":ability,"name":rule["label"],"action":action.name,"phase":label,
                            "normalized_time":phase,"source_frame":frame,"camera_yaw_degrees":angle,
                            "camera_lens_mm":camera.data.lens,"camera_target_m":list(center),
                            "gada_frame_bounds":bounds,
                            "file":path.name,"sha256":digest(path)})
    receipt = {"studio_scene_sha256":digest(Path(bpy.data.filepath)), "actions_scene_sha256":digest(args.actions),
               "kit_sha256":digest(KIT),"script_sha256":digest(Path(__file__)),
               "samples":args.samples,"image_size":[scene.render.resolution_x,scene.render.resolution_y],
               "blender":bpy.app.version_string,"frames":records}
    (out/"studio-poses.json").write_text(json.dumps(receipt,indent=2)+"\n")


if __name__ == "__main__":
    main()
