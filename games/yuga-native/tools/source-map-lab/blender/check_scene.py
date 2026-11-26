"""Verify a reopened ground-study .blend and write a small repeatable audit.

blender -b dust2-ground-study.blend --python-exit-code 1 --python check_scene.py -- --output reopened.json
"""

import argparse
import json
import sys
from pathlib import Path

import bpy

INSTANCE = "yugaLabInstanceId"


def world_matrices(scene):
    # On reopening, Blender lazily evaluates only the saved active scene.
    with bpy.context.temp_override(scene=scene, view_layer=scene.view_layers[0]):
        graph = bpy.context.evaluated_depsgraph_get()
        graph.update()
        return {
            obj[INSTANCE]: obj.evaluated_get(graph).matrix_world.copy()
            for obj in scene.objects
            if INSTANCE in obj
        }


def verify():
    original = bpy.data.scenes["01 • Reference"]
    recolour = bpy.data.scenes["02 • Ground recolour"]
    before = {o[INSTANCE]: o for o in original.objects if INSTANCE in o}
    after = {o[INSTANCE]: o for o in recolour.objects if INSTANCE in o}
    if before.keys() != after.keys() or not before:
        raise ValueError("Saved scene source instances disagree")
    original_matrices = world_matrices(original)
    recolour_matrices = world_matrices(recolour)
    changed = 0
    mesh_ids = set()
    for key, a in before.items():
        b = after[key]
        if a.type != b.type or any(
            abs(original_matrices[key][i][j] - recolour_matrices[key][i][j]) > 1e-6
            for i in range(4)
            for j in range(4)
        ):
            raise ValueError(f"Saved instance changed placement: {a.name}")
        if a.type != "MESH":
            continue
        if a.data != b.data:
            raise ValueError(f"States do not share source mesh: {a.name}")
        mesh_ids.add(a.data["yugaLabSourceIndex"])
        if len(a.material_slots) != len(b.material_slots):
            raise ValueError(f"Saved instance material slot count differs: {a.name}")
        for left, right in zip(a.material_slots, b.material_slots):
            if left.material != right.material:
                if (
                    right.link != "OBJECT"
                    or left.material.pass_index != 1
                    or right.material.pass_index != 1
                ):
                    raise ValueError(f"Unexpected unmarked material change on {a.name}")
                changed += 1
    transforms = {}
    for marker in original.timeline_markers:
        other = recolour.timeline_markers.get(marker.name)
        if not other or other.camera != marker.camera or other.frame != marker.frame:
            raise ValueError(f"Camera or timeline marker differs: {marker.name}")
        transforms[marker.name] = marker.frame
    if transforms != {"overview": 1, "site-a": 2, "site-b": 3}:
        raise ValueError(f"Missing registered views: {transforms}")
    packed = [i for i in bpy.data.images if i.source == "FILE" and i.users > 0]
    missing = [i.name for i in packed if not i.packed_file]
    if missing:
        raise ValueError(f"External images remain unpacked: {missing}")
    lights = {obj for obj in original.objects if obj.type == "LIGHT"}
    if (
        original.world != recolour.world
        or not lights
        or lights != {obj for obj in recolour.objects if obj.type == "LIGHT"}
        or not changed
    ):
        raise ValueError("Study lacks matching lights or a material change")
    return {
        "blender": bpy.app.version_string,
        "instances_matching_transform": len(before),
        "mesh_instances_sharing_geometry": sum(
            o.type == "MESH" for o in before.values()
        ),
        "source_meshes": len(mesh_ids),
        "changed_object_ground_slots": changed,
        "packed_file_images": len(packed),
        "matched_cameras": transforms,
        "shared_lights": sorted(light.name for light in lights),
        "source_blend": Path(bpy.data.filepath).name,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    data = verify()
    text = json.dumps(data, indent=2) + "\n"
    if args.output:
        args.output.write_text(text)
    print(text)
