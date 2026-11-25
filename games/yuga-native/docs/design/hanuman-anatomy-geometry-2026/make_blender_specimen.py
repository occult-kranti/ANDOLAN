"""Create an editable, deliberately schematic half-surface for mirror/shape-key practice.

Run: blender -b --factory-startup --python-exit-code 1 -P make_blender_specimen.py -- OUTPUT.blend
This is an original teaching mesh, not Hanuman or a game-ready asset.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


def gauss(x: float, z: float, cx: float, cz: float, sx: float, sz: float) -> float:
    return math.exp(-((x - cx) / sx) ** 2 - ((z - cz) / sz) ** 2)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def main():
    if "--" not in sys.argv or not sys.argv[sys.argv.index("--") + 1 :]:
        raise SystemExit("Provide a destination .blend path after --")
    output = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene["read_me"] = "Teaching surface only: mirrored half-mesh with an editable bounded cheek shape key. Not Hanuman."
    scene["coordinate_space"] = "Blender Z up, front toward -Y, local symmetry across X=0"

    columns, rows = 25, 29
    vertices, polygons = [], []
    for row in range(rows):
        z = 1.79 + .13 * row / (rows - 1)
        for col in range(columns):
            x = .14 * col / (columns - 1)
            depth = (.142 + .041 * gauss(x, z, 0, 1.825, .055, .032)
                     + .020 * gauss(x, z, .045, 1.906, .036, .018)
                     - .013 * gauss(x, z, .045, 1.885, .026, .015))
            vertices.append((x, -depth, z))
    for row in range(rows - 1):
        for col in range(columns - 1):
            i = row * columns + col
            polygons.append((i, i + 1, i + columns + 1, i + columns))
    mesh = bpy.data.meshes.new("Schematic half-surface grid")
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    obj = bpy.data.objects.new("STUDY ONLY · editable half-surface", mesh)
    scene.collection.objects.link(obj)
    obj["scope"] = "725 vertices on positive X; Mirror makes a paired display. No skin, eyes, jaw or topology correspondence."
    obj.shape_key_add(name="Basis")
    key = obj.shape_key_add(name="Cheek relief · up to 8 mm")
    for index, (x, y, z) in enumerate(vertices):
        key.data[index].co.y = y - .008 * gauss(x, z, .065, 1.835, .035, .022)
    key.value = .65
    mirror = obj.modifiers.new("Practice · local X bilateral mirror", "MIRROR")
    mirror.use_axis[0] = True
    mirror.use_clip = True
    mirror.use_mirror_merge = True
    mirror.merge_threshold = .0001
    material = bpy.data.materials.new("Clay · teaching specimen")
    material.diffuse_color = (.42, .21, .14, 1)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.42, .21, .14, 1)
    shader.inputs["Roughness"].default_value = .68
    mesh.materials.append(material)

    # Mark the symmetry plane with a single editable curve behind the study surface.
    curve = bpy.data.curves.new("Centerline · x = 0", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = .0006
    line = curve.splines.new("POLY")
    line.points.add(1)
    line.points[0].co = (0, -.205, 1.775, 1)
    line.points[1].co = (0, -.205, 1.935, 1)
    marker = bpy.data.objects.new("GUIDE · local X = 0", curve)
    scene.collection.objects.link(marker)
    guide_mat = bpy.data.materials.new("Guide · mint")
    guide_mat.diffuse_color = (.14, .8, .72, 1)
    curve.materials.append(guide_mat)

    camera_data = bpy.data.cameras.new("Specimen orthographic front")
    camera = bpy.data.objects.new("Specimen orthographic front", camera_data)
    scene.collection.objects.link(camera)
    camera.location = (0, -.7, 1.855)
    aim(camera, (0, -.15, 1.855))
    camera_data.type, camera_data.ortho_scale = "ORTHO", .34
    scene.camera = camera
    light_data = bpy.data.lights.new("Broad key", "AREA")
    light_data.energy, light_data.size = 6, .35
    light = bpy.data.objects.new("Broad key", light_data)
    scene.collection.objects.link(light)
    light.location = (-.3, -.55, 2.2)
    aim(light, (0, -.15, 1.855))
    scene.world.use_nodes = True
    scene.world.node_tree.nodes["Background"].inputs["Strength"].default_value = .12
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
    scene.render.resolution_x, scene.render.resolution_y = 1000, 750
    scene.render.resolution_percentage = 100
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))
    print("WROTE", output, "vertices", len(mesh.vertices), "quads", len(mesh.polygons))


if __name__ == "__main__":
    main()
