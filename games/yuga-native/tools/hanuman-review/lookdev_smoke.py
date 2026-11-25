"""Independently reopen the look-development scene and check packed inputs.

Invoke Blender headlessly on the editable look-development .blend, with
--disable-autoexec and --python-exit-code. This reads datablocks only.
"""

import hashlib
import json
from pathlib import Path
import sys

import bpy


def digest(data):
    return hashlib.sha256(data).hexdigest()


def connected_images(socket):
    images = set()
    pending = [link.from_node for link in socket.links]
    seen = set()
    while pending:
        node = pending.pop()
        if node in seen:
            continue
        seen.add(node)
        if node.type == "TEX_IMAGE" and node.image:
            images.add(node.image)
        pending.extend(link.from_node for value in node.inputs for link in value.links)
    return images


def main():
    manifest, output = map(Path, sys.argv[sys.argv.index("--") + 1:])
    receipt = json.loads(manifest.read_text())
    actual = digest(Path(bpy.data.filepath).read_bytes())
    assert actual == receipt["blend_sha256"], "wrong look development file"
    source = bpy.data.scenes[receipt["source_scene"]]
    stage = bpy.data.scenes[receipt["lookdev_scene"]]
    assert source.camera.data != stage.camera.data and source.world != stage.world
    shared = 0
    for obj in source.objects:
        clone = stage.objects.get("LookDev - " + obj.name)
        assert clone and clone != obj, f"missing isolated presentation clone: {obj.name}"
        if obj.type in {"MESH", "ARMATURE"}:
            assert clone.data == obj.data, f"geometry changed: {obj.name}"
            shared += 1
    assert shared == receipt["mesh_and_rig_data_shared"]

    reference, = [obj for obj in stage.objects if obj.name.startswith("Reference board - ")]
    assert reference.hide_render and all(group.hide_render for group in reference.users_collection)
    assert digest(reference.data.packed_file.data) == receipt["reference_sha256"]
    assert len(bpy.data.libraries) == 0

    cloth = receipt["cloth_texture"]
    initial = bpy.data.materials["Drapery · red madder dyed weave"]
    revised = bpy.data.materials[cloth["material"]]
    initial_nodes = initial.node_tree.nodes
    revised_nodes = revised.node_tree.nodes
    branch_shader = revised_nodes.get("Principled BSDF")
    original_shader = initial_nodes.get("Principled BSDF")
    actual_swatch = revised_nodes[cloth["base_color_node"]].image
    assert actual_swatch in connected_images(branch_shader.inputs["Base Color"])
    assert actual_swatch not in connected_images(original_shader.inputs["Base Color"])
    assert digest(actual_swatch.packed_file.data) == cloth["sha256"]
    normal_images = connected_images(branch_shader.inputs["Normal"])
    assert normal_images == connected_images(original_shader.inputs["Normal"])
    assert {image.name for image in normal_images} == {cloth["existing_normal_image"]}
    assert len(bpy.data.actions) == receipt["shared_action_count"]
    render_path = manifest.parent / receipt["render"]["file"]
    assert digest(render_path.read_bytes()) == receipt["render"]["sha256"]
    report = {
        "blend_sha256": actual, "scene_count": len(bpy.data.scenes),
        "shared_geometry_or_armature_objects": shared, "shared_actions": len(bpy.data.actions),
        "lookdev_render_sha256": receipt["render"]["sha256"],
        "packed_reference_and_cloth_verified": True, "reference_hidden_in_render": True,
        "branch_cloth_albedo_is_active": True, "source_cloth_and_normals_unchanged": True,
        "scope": "Read-only data and rendered artifact identity. Separate editable studio scene with shared authored geometry.",
    }
    with output.open("x") as stream:
        json.dump(report, stream, indent=2)
        stream.write("\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
