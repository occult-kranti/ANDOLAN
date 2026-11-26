"""Reopen the generated Blender scene and reimport its GLB to check portable geometry."""

import hashlib
import json
import math
from pathlib import Path
import struct

import bpy
from mathutils import Vector


def main():
    if not bpy.app.background:
        raise RuntimeError("Run this verification in a separate background Blender process.")
    root = Path(__file__).resolve().parent
    manifest = json.loads((root / "manifest.json").read_text())
    for name, expected in manifest["files"].items():
        data = (root / name).read_bytes()
        assert len(data) == expected["bytes"]
        assert hashlib.sha256(data).hexdigest() == expected["sha256"], name
    bpy.ops.wm.open_mainfile(filepath=str(root / "daftar-route-lab.blend"), load_ui=False, use_scripts=False)
    assert bpy.context.scene.render.engine == "CYCLES"
    assert bpy.context.scene.cycles.device == "CPU"
    assert not bpy.data.libraries and not bpy.data.images
    assert all(font.filepath in ("", "<builtin>") or font.packed_file for font in bpy.data.fonts)
    original_objects = len(bpy.data.objects)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(root / "daftar-route-lab.glb"))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    assert len(meshes) == manifest["geometry"]["export_objects"]
    assert not bpy.data.cameras and not bpy.data.lights
    points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    assert all(math.isfinite(component) for point in points for component in point)
    minimum = [min(point[axis] for point in points) for axis in range(3)]
    maximum = [max(point[axis] for point in points) for axis in range(3)]
    dimensions = [maximum[axis] - minimum[axis] for axis in range(3)]
    assert abs(dimensions[0] - 48) < 0.02 and abs(dimensions[1] - 56) < 0.02
    assert abs(minimum[2] + 0.4) < 0.02 and abs(maximum[2] - 3.37) < 0.02
    for expected in manifest["spawns"]:
        matches = [obj for obj in meshes if obj.get("spawn_id") == expected["id"]]
        assert len(matches) == 1
        position = matches[0].matrix_world.translation
        assert abs(position.x - expected["east"]) < 0.001
        assert abs(position.y - expected["north"]) < 0.001
    vertices = sum(len(obj.data.vertices) for obj in meshes)
    assert 0 < vertices < 100000
    assert all(math.isfinite(value) for obj in meshes for vertex in obj.data.vertices for value in vertex.co)
    png = (root / "route-lab-preview.png").read_bytes()
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    assert struct.unpack_from(">II", png, 16) == (1024, 832)
    receipt = {
        "schema_version": 1, "status": "portable_geometry_verified", "blender_version": bpy.app.version_string,
        "source_blend_objects": original_objects, "reimported_glb_mesh_objects": len(meshes),
        "reimported_vertices": vertices, "reimported_blender_bounds_min_m": [round(x, 6) for x in minimum],
        "reimported_blender_bounds_max_m": [round(x, 6) for x in maximum],
        "reimported_dimensions_m": [round(x, 6) for x in dimensions],
        "spawn_markers_position_verified": len(manifest["spawns"]), "external_resources": False,
        "preview_png_dimensions": [1024, 832], "cpu_scene_verified": True,
        "manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
        "gameplay_integration_verified": False, "physics_collision_verified": False,
        "unreal_executed": False, "gpu_tested": False,
    }
    (root / "geometry-acceptance.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print("DAFTAR_ROUTE_LAB_VERIFIED=" + json.dumps(receipt))


if __name__ == "__main__":
    main()
