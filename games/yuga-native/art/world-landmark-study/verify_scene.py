"""Reopen a packed landmark scene and inspect assets, geometry and foot contact."""
import hashlib
import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).resolve().parent


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def triangles(mesh):
    return sum(len(p.vertices) - 2 for p in mesh.polygons)


def floor_contact(rig, slabs, graph, side):
    actor = rig.evaluated_get(graph)
    mesh = actor.to_mesh()
    try:
        points = [actor.matrix_world @ vertex.co for vertex in mesh.vertices]
        relevant = [point for point in points if (point.x < -.6) == (side == "left")]
        low = min(relevant, key=lambda point: point.z)
    finally:
        actor.to_mesh_clear()
    hits = []
    for slab in slabs:
        evaluated = slab.evaluated_get(graph)
        inverse = evaluated.matrix_world.inverted()
        origin = inverse @ (low + Vector((0, 0, .1)))
        direction = (inverse.to_3x3() @ Vector((0, 0, -1))).normalized()
        hit, local, _normal, _index = evaluated.ray_cast(origin, direction, distance=.25)
        if hit:
            surface = evaluated.matrix_world @ local
            hits.append((abs(low.z - surface.z), low.z - surface.z, slab.name))
    if not hits:
        raise RuntimeError(f"No ghat tile below {side} foot")
    _, clearance, surface = min(hits)
    if abs(clearance) > .004:
        raise RuntimeError(f"{side} foot is {clearance:.5f} m from {surface}")
    return {
        "lowest_vertex_xyz_m": [round(c, 5) for c in low],
        "surface": surface,
        "vertical_clearance_m": round(clearance, 5),
    }


def main():
    scene_path = HERE / "landmark.blend"
    bpy.ops.wm.open_mainfile(filepath=str(scene_path), load_ui=False)
    scene = bpy.context.scene
    graph = bpy.context.evaluated_depsgraph_get()
    objects = list(scene.objects)
    rocks = [o for o in objects if o.type == "MESH" and o.name.startswith("Rock face · ")]
    if len(rocks) != 16 or len({o.data.as_pointer() for o in rocks}) != 1:
        raise RuntimeError("Expected 16 placements sharing one Poly Haven rock mesh")
    if triangles(rocks[0].data) != 20174:
        raise RuntimeError("Unexpected Poly Haven rock topology")
    images = [im for im in bpy.data.images if im.users and im.source in ("FILE", "TILED")]
    unpacked = [im.name for im in images if not im.packed_files]
    if unpacked or bpy.data.libraries:
        raise RuntimeError(f"External inputs in scene: images={unpacked}, libraries={len(bpy.data.libraries)}")
    actor = scene.objects.get("Hanuman skinned hero")
    helper = scene.objects.get("Icosphere")
    rigs = [o for o in scene.objects if o.type == "ARMATURE"]
    if not actor or not actor.visible_shadow or not helper or not helper.hide_render:
        raise RuntimeError("Actor and shadow or hidden import helper invalid")
    if len(rigs) != 1 or len(rigs[0].pose.bones) != 167:
        raise RuntimeError("Character rig differs from reviewed model")
    slabs = [o for o in objects if o.type == "MESH" and o.name.startswith("Causeway slab ")]
    contacts = {side: floor_contact(actor, slabs, graph, side) for side in ("left", "right")}
    triangle_count = sum(triangles(o.data) for o in objects if o.type == "MESH" and not o.hide_render)
    result = {
        "scene_sha256": sha(scene_path),
        "image_sha256": sha(HERE / "landmark.png"),
        "raw_image_sha256": sha(HERE / "landmark-raw.png"),
        "script_sha256": sha(HERE / "build.py"),
        "blender": bpy.app.version_string,
        "render": {
            "engine": scene.render.engine,
            "device": scene.cycles.device,
            "samples": scene.cycles.samples,
            "resolution": [scene.render.resolution_x, scene.render.resolution_y],
            "camera": scene.camera.name,
            "lens_mm": scene.camera.data.lens,
            "location_m": [round(x, 4) for x in scene.camera.location],
        },
        "meshes": {
            "visible_objects": sum(o.type == "MESH" and not o.hide_render for o in objects),
            "raw_triangles_with_instances": triangle_count,
            "poly_haven_rock_placements": len(rocks),
            "triangles_per_rock": triangles(rocks[0].data),
            "rock_meshes_shared": len({o.data.as_pointer() for o in rocks}),
        },
        "images": {"packed_file_count": len(images), "unpacked": unpacked},
        "external_libraries": len(bpy.data.libraries),
        "hero_joints": len(rigs[0].pose.bones),
        "hero_shadow_visible": actor.visible_shadow,
        "hidden_bone_helper": helper.hide_render,
        "foot_contact": contacts,
        "scope": "Editable still composition; no game collision, traversal or GPU performance is asserted.",
    }
    (HERE / "verification.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
