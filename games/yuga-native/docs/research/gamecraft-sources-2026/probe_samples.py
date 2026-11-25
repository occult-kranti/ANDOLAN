"""Inspect two pinned glTF sample assets in Blender.

blender -b -t 1 --factory-startup --python-exit-code 1 -P probe_samples.py
"""

import hashlib
import json
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parent
SAMPLES = ROOT / "samples"
EXPECTED = {
    "fox/Fox.glb": "d97044e701822bac5a62696459b27d7b375aada5de8574ed4362edbba94771f7",
    "animated-morph-cube/AnimatedMorphCube.glb": "214ee56160a50dbf22543a1d66dbf860986e87f0efac3d89feac1359d0e6aeab",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_sample(name):
    source = SAMPLES / name
    if digest(source) != EXPECTED[name]:
        raise ValueError(f"Sample differs from the pinned input: {name}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    return source


def sample_frames(action, count=13):
    start, end = action.frame_range
    return [start + (end - start) * step / (count - 1) for step in range(count)]


def set_frame(value):
    frame = int(value)
    bpy.context.scene.frame_set(frame, subframe=value - frame)
    bpy.context.view_layer.update()


def inspect_fox():
    source = import_sample("fox/Fox.glb")
    rigs = [item for item in bpy.context.scene.objects if item.type == "ARMATURE"]
    if len(rigs) != 1 or len(rigs[0].pose.bones) != 24:
        raise ValueError("Expected one 24-joint fox skeleton")
    rig = rigs[0]
    rig.animation_data.use_nla = False
    actions = {item.name: item for item in bpy.data.actions}
    clips = {}
    for name in ("Survey", "Walk", "Run"):
        action = actions[name + "_root"]
        rig.animation_data.action = action
        offsets = {joint: [] for joint in ("b_LeftFoot02_018", "b_RightFoot02_022", "b_Tail03_014")}
        for frame in sample_frames(action):
            set_frame(frame)
            hip = rig.matrix_world @ rig.pose.bones["b_Hip_01"].head
            for joint in offsets:
                offsets[joint].append((rig.matrix_world @ rig.pose.bones[joint].head) - hip)
        displacement = {
            joint: round(max((point - values[0]).length for point in values), 5)
            for joint, values in offsets.items()
        }
        if max(displacement.values()) < 0.01:
            raise ValueError(f"No sampled skeleton motion in {name}")
        clips[name] = {
            "frame_range": [round(float(value), 4) for value in action.frame_range],
            "samples": 13,
            "max_joint_displacement_from_hip_in_imported_units": displacement,
        }
    return {"file": source.name, "sha256": digest(source), "joints": 24, "clips": clips}


def inspect_morph():
    source = import_sample("animated-morph-cube/AnimatedMorphCube.glb")
    meshes = [item for item in bpy.context.scene.objects if item.type == "MESH"]
    if len(meshes) != 1 or not meshes[0].data.shape_keys:
        raise ValueError("Expected one morph-target mesh")
    keys = meshes[0].data.shape_keys
    names = [item.name for item in keys.key_blocks]
    if names != ["Basis", "thin", "angle"]:
        raise ValueError(f"Unexpected shape keys: {names}")
    action = bpy.data.actions["Square_AnimatedMorphCube"]
    keys.animation_data.use_nla = False
    keys.animation_data.action = action
    weights = []
    for frame in sample_frames(action):
        set_frame(frame)
        weights.append({name: round(float(keys.key_blocks[name].value), 5) for name in names[1:]})
    ranges = {
        name: [min(sample[name] for sample in weights), max(sample[name] for sample in weights)]
        for name in names[1:]
    }
    if not all(high - low > 0.05 for low, high in ranges.values()):
        raise ValueError(f"Shape targets did not animate: {ranges}")
    return {
        "file": source.name,
        "sha256": digest(source),
        "shape_keys": names,
        "clip": action.name,
        "samples": len(weights),
        "sampled_weight_ranges": ranges,
    }


def main():
    result = {
        "blender": bpy.app.version_string,
        "source_commit": "e124e8d8d7330a5372bc2b4d00d39a4a9d7997ea",
        "fox": inspect_fox(),
        "morph_cube": inspect_morph(),
        "scope": "Imported samples and sampled animation inside Blender. No game integration or retargeting is asserted.",
    }
    (ROOT / "sample-results.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
