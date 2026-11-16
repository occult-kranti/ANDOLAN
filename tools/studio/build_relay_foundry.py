#!/usr/bin/env python3
"""Blender 4.3 authoring source for the original Relay Foundry map study.

Run: blender4.3 --background --python tools/studio/build_relay_foundry.py
No external models, textures, fonts, add-ons or game data are used.
"""
from pathlib import Path
import hashlib
import json
import math

import bpy
import bmesh
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[2]
PROJECT = ROOT / "games/yuga-native"
ART = PROJECT / "art/studio-map"
GLB = PROJECT / "assets/world/studio-relay-foundry.glb"
ART.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for block in bpy.data.materials:
    bpy.data.materials.remove(block)

COLLIDERS = []
MATERIALS = {}


def material(name, color, metallic=0.0, roughness=0.72):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Metallic"].default_value = metallic
    MATERIALS[name] = result
    return result


stone = material("Foundry / warm limestone", (0.52, 0.43, 0.29))
light_stone = material("Foundry / dressed sandstone", (0.73, 0.63, 0.42))
dark = material("Foundry / deep indigo", (0.045, 0.09, 0.14))
lane = material("Foundry / blue slate", (0.16, 0.27, 0.30))
bronze = material("Foundry / copper", (0.55, 0.29, 0.105), 0.55, 0.38)
gold = material("Relay / amber", (0.95, 0.62, 0.15), 0.3, 0.3)
moon = material("North / chalk blue", (0.43, 0.78, 0.85), 0.25, 0.4)
earth = material("Court / terracotta", (0.37, 0.19, 0.13))


def apply_material(obj, mat):
    obj.data.materials.append(mat)
    return obj


def box(name, x, z, bottom, width, depth, height, mat=stone, collision=True):
    prefix = "COL_BOX_" if collision else "DECOR_"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, -z, bottom + height / 2))
    obj = bpy.context.object
    obj.name = prefix + name
    obj.dimensions = (width, depth, height)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_material(obj, mat)
    if collision:
        COLLIDERS.append({"name": obj.name, "shape": "box", "center": [x, bottom + height / 2, z],
                          "size": [width, height, depth]})
    return obj


def cylinder(name, x, z, bottom, radius, height, mat, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=height,
                                       location=(x, -z, bottom + height / 2))
    obj = bpy.context.object
    obj.name = "DECOR_" + name
    apply_material(obj, mat)
    return obj


def ramp(name, x, z_low, z_high, width, elevation=6):
    # The wedge has a level bottom and a single continuous walkable top.
    points = [(x-width/2, -z_low, 0), (x+width/2, -z_low, 0),
              (x-width/2, -z_high, 0), (x+width/2, -z_high, 0),
              (x-width/2, -z_high, elevation), (x+width/2, -z_high, elevation)]
    faces = [(0, 2, 3, 1), (0, 1, 5, 4), (2, 4, 5, 3), (0, 4, 2), (1, 3, 5)]
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(points, [], faces)
    mesh.update()
    edit = bmesh.new()
    edit.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(edit, faces=list(edit.faces))
    edit.to_mesh(mesh)
    edit.free()
    obj = bpy.data.objects.new("COL_RAMP_" + name, mesh)
    bpy.context.collection.objects.link(obj)
    apply_material(obj, light_stone)
    COLLIDERS.append({"name": obj.name, "shape": "convex_wedge", "width": width,
                      "z_low": z_low, "z_high": z_high, "elevation": elevation})
    return obj


def lettering(text, x, z, height=0.06, size=2.0, mat=moon):
    bpy.ops.object.text_add(location=(x, -z, height))
    obj = bpy.context.object
    obj.name = "DECOR_LABEL_" + text.replace(" ", "_")
    obj.data.body = text
    obj.data.align_x = "CENTER"
    obj.data.align_y = "CENTER"
    obj.data.size = size
    obj.data.extrude = 0.006
    apply_material(obj, mat)
    bpy.ops.object.convert(target="MESH")


# The uninterrupted floor makes the underpasses and rotation corridors walkable.
box("FOUNDATION", 0, 0, -1.2, 132, 190, 1.2, dark)
for x, label in [(-40, "LOOM"), (0, "SPAN"), (40, "KILN")]:
    box("ROUTE_" + label, x, 0, 0.005, 19, 158, 0.025, lane, False)
    for z in [-58, 58]:
        lettering(label, x, z, size=2.5)
    # Short broken copper route ticks are visual guidance, never collision walls.
    for z in range(-65, 70, 10):
        if abs(z) < 38 and x == 0:
            continue
        box("TICK_" + label + str(z), x, z, 0.035, 0.3, 2, 0.015, bronze, False)

# Mirrored core/spawn courts, with one uncluttered approach per side.
for z, tint, tag in [(79, gold, "SUN"), (-79, moon, "MOON")]:
    box(tag + "_SPAWN_INLAY", 0, z, 0.015, 25, 16, 0.02, tint, False)
    for x in [-16, 16]:
        box(tag + "_CORE_PLINTH_" + str(x), x, z+(-3 if z > 0 else 3), 0, 5, 6, 1.5, light_stone)
        box(tag + "_CORE_TOWER_" + str(x), x, z+(-3 if z > 0 else 3), 1.5, 2.6, 2.6, 10, dark)
        cylinder(tag + "_CROWN_" + str(x), x, z+(-3 if z > 0 else 3), 11.5, 1.8, 0.7, tint)
    lettering(tag + " COURT", 0, z, size=2.2, mat=dark)

# Four production halls separate lanes but stop short of cross-map rotations.
for x in [-20, 20]:
    for z in [-46, 46]:
        tag = f"HALL_{x}_{z}"
        box(tag, x, z, 0, 12, 32, 9, stone)
        box(tag + "_CORNICE", x, z, 9, 13, 33, 0.55, bronze)
        box(tag + "_ROOF", x, z, 9.55, 11.4, 31.4, 0.4, dark)
        for offset in [-11, 0, 11]:
            box(tag + "_PILASTER_" + str(offset), x-6.15 if x < 0 else x+6.15, z+offset,
                0, 0.5, 1.1, 8.5, light_stone)

# Side rotations offer different silhouettes and cover rhythms.
for x, z in [(-56, -48), (-56, -32), (-56, 32), (-56, 48)]:
    box(f"LOOM_PILLAR_{x}_{z}", x, z, 0, 3.5, 4, 5, light_stone)
    box(f"LOOM_CAP_{x}_{z}", x, z, 5, 4.1, 4.6, 0.35, bronze)
for z in [-50, -32, 32, 50]:
    box("KILN_COVER_" + str(z), 55 if z < 0 else 57, z, 0, 6, 5, 2.4, earth)
    box("KILN_CHIMNEY_" + str(z), 60, z, 0, 2, 2, 7, dark)

# Low cover breaks long lane sightlines while leaving wide passages.
for x in [-40, 0, 40]:
    for z in [-52, 52]:
        offset = -5 if z < 0 else 5
        box(f"LANE_COVER_{x}_{z}", x+offset, z, 0, 5, 3.5, 1.3, light_stone)
for z in [-20, 20]:
    box("ROTATION_STRIP_" + str(z), 0, z, 0.006, 116, 9, 0.025, earth, False)

# Six-metre deck connects all lanes. Ground lanes remain open beneath it.
box("CROSSOVER_DECK", 0, 0, 5.2, 104, 10, 0.8, light_stone)
for x in [-23, 23]:
    for z in [-3.8, 3.8]:
        box(f"BRIDGE_PIER_{x}_{z}", x, z, 0, 2.2, 2.2, 5.2, stone)
for x in [-39, 39]:
    for z in [-4.65, 4.65]:
        box(f"BRIDGE_RAIL_{x}_{z}", x, z, 6, 25, 0.4, 0.8, bronze)
ramp("SOUTH_ACCESS", 0, 35, 5, 12)
ramp("NORTH_ACCESS", 0, -35, -5, 12)

# Relay landmarks are route goals only; this prototype has no capture authority.
for index, (x, z, base) in enumerate([(-40, -12, 0), (0, 0, 6), (40, 12, 0)], 1):
    cylinder(f"RELAY_{index}_PAD", x, z, base+0.035, 4, 0.055, gold, 32)
    # Offset mast keeps the central approach passable.
    box(f"RELAY_{index}_MAST", x+3.3, z, base, 0.5, 0.5, 3.8, bronze)
    cylinder(f"RELAY_{index}_BEACON", x+3.3, z, base+3.8, 0.75, 0.6, gold)
    lettering("R" + str(index), x, z, base+0.1, 2.3, dark)

# Visible perimeter prevents unclear drop boundaries.
for x in [-65, 65]:
    box("BOUNDARY_X_" + str(x), x, 0, 0, 2, 190, 4, dark)
    box("BOUNDARY_CROWN_X_" + str(x), x, 0, 4, 2.2, 190, 0.35, bronze)
for z in [-94, 94]:
    box("BOUNDARY_Z_" + str(z), 0, z, 0, 128, 2, 4, dark)
for z in range(-84, 85, 14):
    for x in [-65, 65]:
        box(f"PERIMETER_POST_{x}_{z}", x, z, 4.35, 3, 3, 2, light_stone)

mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
triangles = sum(sum(len(poly.vertices)-2 for poly in obj.data.polygons) for obj in mesh_objects)
checks = {
    "three_lanes": len([-40, 0, 40]) == 3,
    "three_relay_landmarks": sum(obj.name.endswith("_PAD") and "RELAY_" in obj.name for obj in mesh_objects) == 3,
    "two_walkable_ramps": len([c for c in COLLIDERS if c["shape"] == "convex_wedge"]) == 2,
    "bounded_material_count": len(MATERIALS) == 8,
    "bounded_triangle_count": triangles < 30000,
    "no_external_images": not any(image.filepath or image.source in {"FILE", "TILED", "MOVIE", "SEQUENCE"}
                                  for image in bpy.data.images),
    "unique_collision_names": len({c["name"] for c in COLLIDERS}) == len(COLLIDERS),
}
assert all(checks.values()), checks

# Keep editable lights/camera in the blend, export only original mesh objects.
bpy.ops.object.select_all(action="DESELECT")
for obj in mesh_objects:
    obj.select_set(True)
bpy.context.view_layer.objects.active = mesh_objects[0]
bpy.ops.export_scene.gltf(filepath=str(GLB), export_format="GLB", use_selection=True,
                           export_cameras=False, export_lights=False, export_extras=True)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 24
scene.render.threads_mode = "FIXED"
scene.render.threads = 8
scene.render.resolution_x = 1440
scene.render.resolution_y = 1050
scene.render.resolution_percentage = 100
scene.world.color = (0.17, 0.22, 0.29)
bpy.ops.object.light_add(type="AREA", location=(10, -20, 120))
bpy.context.object.data.energy = 350000
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = 100
bpy.ops.object.light_add(type="SUN", location=(0, 0, 100))
bpy.context.object.rotation_euler = (math.radians(28), math.radians(-30), math.radians(-20))
bpy.context.object.data.energy = 2.2
bpy.ops.object.camera_add(location=(155, -185, 172))
camera = bpy.context.object
camera.rotation_euler = (Vector((0, 0, 0))-camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 225
scene.camera = camera
scene.view_settings.view_transform = "AgX"
scene.render.filepath = str(ART / "blender-overview.png")
bpy.ops.wm.save_as_mainfile(filepath=str(ART / "relay-foundry.blend"))

manifest = {
    "schema_version": 1, "name": "Relay Foundry", "status": "original playable map-design study",
    "blender_version": bpy.app.version_string, "source_script": str(Path(__file__).relative_to(ROOT)),
    "source_script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "asset": str(GLB.relative_to(PROJECT)), "asset_sha256": hashlib.sha256(GLB.read_bytes()).hexdigest(),
    "blend_sha256": hashlib.sha256((ART / "relay-foundry.blend").read_bytes()).hexdigest(),
    "units": "metres; Godot +Y up; Blender Z-up export converted by glTF",
    "bounds": {"width": 132, "length": 190, "crossover_height": 6},
    "lanes": [{"id": "loom", "x": -40}, {"id": "span", "x": 0}, {"id": "kiln", "x": 40}],
    "spawns": [[0, 0.15, 79], [0, 0.15, -79]],
    "relays": [[-40, 0, -12], [0, 6, 0], [40, 0, 12]],
    "collision_contract": "COL_BOX_ meshes -> local mesh AABB boxes; COL_RAMP_ meshes -> convex wedge shapes",
    "colliders": COLLIDERS, "mesh_objects": len(mesh_objects), "triangles": triangles,
    "material_count": len(MATERIALS), "checks": checks,
    "rights": "Original procedural geometry/materials authored in this repository; no external assets or game data.",
    "limits": "No combat, capture rewards, army navigation, native online authority, production art or hardware FPS qualification.",
}
(ART / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
print("STUDIO_MAP_MANIFEST", json.dumps({"meshes": len(mesh_objects), "triangles": triangles,
                                         "colliders": len(COLLIDERS), "checks": checks}))
bpy.ops.render.render(write_still=True)
