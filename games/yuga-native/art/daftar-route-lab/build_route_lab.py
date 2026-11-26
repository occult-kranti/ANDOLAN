"""Build an original portable Yuga scale/route prototype with Blender's CPU renderer.

Run in a separate background Blender process. No downloaded assets, scripts,
textures, engine installation or gameplay integration are required.
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import time

import bpy
from mathutils import Vector


NAME = "daftar-route-lab"
PINNED_ANDOLAN = "9e59880f31452ce0df8d326cd4f1291b700dc228"
PALETTE = {"indigo": "0c1222", "slate": "172039", "ivory": "f6eddc", "gold": "e2bb70"}
ROUTES = {
    "central": [(0, -23), (0, 23)],
    "west_flank": [(0, -23), (-16, -19), (-16, 19), (0, 23)],
    "east_flank": [(0, -23), (16, -19), (16, 19), (0, 23)],
}
EXPORT_OBJECTS = []
OBSTACLES = []


def linear(hex_color):
    rgb = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
                 for value in rgb) + (1.0,)


def material(name, color, metallic=0.0, roughness=0.7):
    result = bpy.data.materials.new(name)
    result.diffuse_color = linear(color)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = linear(color)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    return result


def finish(obj, name, mat, role, export=True):
    obj.name = name
    obj.data.materials.append(mat)
    obj["daftar_role"] = role
    obj["prototype_only"] = True
    if export:
        EXPORT_OBJECTS.append(obj)
    return obj


def box(name, location, dimensions, mat, role="solid", bevel=0.0, export=True):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("Small original edge bevel", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return finish(obj, name, mat, role, export)


def cylinder(name, location, radius, depth, mat, role="marker", vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location)
    return finish(bpy.context.object, name, mat, role)


def strip(name, start, end, width, mat, height=0.015):
    dx, dy = end[0] - start[0], end[1] - start[1]
    obj = box(name, ((start[0] + end[0]) / 2, (start[1] + end[1]) / 2, height),
              (math.hypot(dx, dy), width, 0.018), mat, "route_visual")
    obj.rotation_euler.z = math.atan2(dy, dx)
    return obj


def ring(name, inner, outer, mat, start=0.0, end=math.tau, segments=64):
    verts, faces = [], []
    for index in range(segments + 1):
        angle = start + (end - start) * index / segments
        for radius in (inner, outer):
            verts.append((math.cos(angle) * radius, math.sin(angle) * radius, 0.08))
    for index in range(segments):
        faces.append((2 * index, 2 * index + 1, 2 * index + 3, 2 * index + 2))
    mesh = bpy.data.meshes.new(name + "Geometry")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    return finish(obj, name, mat, "objective_visual")


def text_label(name, label, location, size, mat):
    data = bpy.data.curves.new(name + "Text", "FONT")
    data.body = label
    data.size = size
    data.space_character = 1.15
    data.extrude = 0.001
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    obj.data.materials.append(mat)
    obj["daftar_role"] = "preview_annotation_only"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def distance_to_obstacle(point, obstacle):
    dx = max(abs(point[0] - obstacle["east"]) - obstacle["width"] / 2, 0)
    dy = max(abs(point[1] - obstacle["north"]) - obstacle["depth"] / 2, 0)
    return math.hypot(dx, dy)


def validate_layout(spawns):
    nearest = min(distance_to_obstacle((0, 0), obstacle) for obstacle in OBSTACLES)
    assert nearest >= 4.5, "The central clearance radius intersects solid geometry."
    for spawn in spawns:
        assert min(distance_to_obstacle((spawn["east"], spawn["north"]), obstacle)
                   for obstacle in OBSTACLES) >= 0.35, "A spawn marker intersects an obstacle."
    route_results = {}
    for name, vertices in ROUTES.items():
        length = 0.0
        minimum = math.inf
        for start, end in zip(vertices, vertices[1:]):
            segment_length = math.dist(start, end)
            length += segment_length
            steps = max(1, math.ceil(segment_length / 0.25))
            for step in range(steps + 1):
                t = step / steps
                point = tuple(a + (b - a) * t for a, b in zip(start, end))
                minimum = min(minimum, *(distance_to_obstacle(point, obstacle) for obstacle in OBSTACLES))
        assert minimum >= 3.0, "The sampled 6 m route corridor intersects an obstacle."
        route_results[name] = {
            "plan_vertices_east_north_m": vertices,
            "length_m": round(length, 6),
            "idealized_seconds_at_5_mps": round(length / 5, 6),
            "sampled_minimum_obstacle_distance_m": round(minimum, 6),
        }
    return {"passed": True, "objective_nearest_obstacle_m": round(nearest, 6),
            "route_sampling_step_max_m": 0.25, "routes": route_results,
            "limitation": "Analytic box footprint and sampled route checks; not a physics, navmesh or gameplay test."}


def main():
    if not bpy.app.background:
        raise RuntimeError("Run this generator in a separate background Blender process.")
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--samples", type=int, default=32)
    args = parser.parse_args(argv)
    if not 4 <= args.samples <= 64:
        raise ValueError("Use 4 to 64 CPU samples.")
    output = args.output_dir.resolve()
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = args.samples
    # The installed 4.3.2 build has no OpenImageDenoise; keep the CPU recipe portable.
    scene.cycles.use_denoising = False
    scene.cycles.time_limit = 60.0
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.resolution_x = 1024
    scene.render.resolution_y = 832
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = "//route-lab-preview.png"
    ivory = material("Yuga ivory floor", PALETTE["ivory"], roughness=0.83)
    slate = material("Yuga slate structure", PALETTE["slate"], roughness=0.68)
    gold = material("Worked gold route inlay", PALETTE["gold"], metallic=0.55, roughness=0.4)
    indigo = material("Yuga indigo backdrop", PALETTE["indigo"], roughness=0.9)
    route_mat = material("Route chalk", "d5cebd", roughness=0.9)
    north_mat = material("North team scale marker", "6589b2", roughness=0.65)

    box("Ground_48x56m", (0, 0, -0.2), (48, 56, 0.4), ivory, "walkable_floor", bevel=0.12)
    box("PreviewBackdrop", (0, 0, -0.55), (200, 200, 0.2), indigo, export=False)
    for name, cx, cy, width, depth in (
        ("Boundary_West", -23.5, 0, 0.5, 55), ("Boundary_East", 23.5, 0, 0.5, 55),
        ("Boundary_South", 0, -27.5, 47.5, 0.5), ("Boundary_North", 0, 27.5, 47.5, 0.5),
    ):
        box(name, (cx, cy, 0.5), (width, depth, 1.0), slate, bevel=0.06)
        OBSTACLES.append({"id": name, "east": cx, "north": cy, "width": width, "depth": depth, "height": 1.0})
    surface_index = 0
    for route_id, points in ROUTES.items():
        for i, (a, b) in enumerate(zip(points, points[1:])):
            # Distinct millimetre offsets prevent coincident faces at junctions.
            strip(f"Route_{route_id}_{i}", a, b, 6.0, route_mat, height=0.015 + surface_index * 0.003)
            surface_index += 1
            strip(f"Inlay_{route_id}_{i}", a, b, 0.10, gold, height=0.055)
    for north in (-4.5, 4.5):
        strip(f"Crosslink_{north}", (-16, north), (16, north), 4.5, route_mat,
              height=0.015 + surface_index * 0.003)
        surface_index += 1

    for east in (-8.5, 8.5):
        for north in (-11.0, 11.0):
            label = f"Block_{'W' if east < 0 else 'E'}{'S' if north < 0 else 'N'}"
            box(label, (east, north, 1.6), (7, 8, 3.2), slate, bevel=0.14)
            box(label + "_Cap", (east, north, 3.24), (7, 8, 0.12), gold, "visual_trim", bevel=0.04)
            box(label + "_Roof", (east, north, 3.33), (6.6, 7.6, 0.08), slate, "visual_trim", bevel=0.03)
            OBSTACLES.append({"id": label, "east": east, "north": north, "width": 7, "depth": 8, "height": 3.37})
    for east in (-20.0, 20.0):
        for north in (-4.0, 4.0):
            label = f"Cover_{east}_{north}"
            box(label, (east, north, 0.625), (2.0, 3.0, 1.25), slate, bevel=0.08)
            OBSTACLES.append({"id": label, "east": east, "north": north, "width": 2.0, "depth": 3.0, "height": 1.25})

    cylinder("Objective_Disk_3mRadius", (0, 0, 0.05), 2.68, 0.04, slate, "objective_visual", vertices=64)
    ring("Objective_Ring_3mRadius", 2.68, 3.0, gold)
    for sector in range(12):
        angle = sector * math.tau / 12
        ring(f"Clearance_4_5mRadius_{sector:02}", 4.46, 4.5, gold, angle, angle + math.tau / 24, 8)
    spawns = []
    for team, north, mat in (("south", -23.0, gold), ("north", 23.0, north_mat)):
        box(f"SpawnPad_{team}", (0, north, 0.06), (15.0, 6.0, 0.12), slate, "spawn_pad", bevel=0.08)
        for index, east in enumerate((-6.0, -3.0, 0.0, 3.0, 6.0), start=1):
            identifier = f"spawn_{team}_{index:02}"
            marker = cylinder(identifier, (east, north, 0.85), 0.25, 1.4, mat, "spawn_visual_only")
            marker["spawn_id"] = identifier
            bpy.ops.mesh.primitive_uv_sphere_add(segments=12, ring_count=8, radius=0.2,
                                                location=(east, north, 1.75))
            finish(bpy.context.object, identifier + "_Head", mat, "spawn_visual_only")
            spawns.append({"id": identifier, "team": team, "east": east, "north": north,
                           "ground_height_m": 0.12, "facing_north": team == "south"})

    text_label("PreviewTitle", "DAFTAR  /  ROUTE LAB", (-23, -33, -0.35), 1.6, ivory)
    text_label("PreviewSubtitle", "YUGA SCALE STUDY   /   ORIGINAL PROTOTYPE 01", (-23, -35.2, -0.35), 0.65, gold)
    text_label("NorthLabel", "N", (-0.5, 25.4, 0.13), 1.4, gold)
    scene.world = bpy.data.worlds.new("Original studio environment")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = linear("a1b5cc")
    background.inputs["Strength"].default_value = 0.4
    sun_data = bpy.data.lights.new("RouteLabSun", "SUN")
    sun_data.energy = 2.3
    sun_data.angle = 0.18
    sun = bpy.data.objects.new("RouteLabSun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.rotation_euler = (math.radians(22), math.radians(-28), math.radians(-35))
    area_data = bpy.data.lights.new("RouteLabSoftFill", "AREA")
    area_data.energy = 3500
    area_data.shape = "DISK"
    area_data.size = 30
    area = bpy.data.objects.new("RouteLabSoftFill", area_data)
    bpy.context.collection.objects.link(area)
    area.location = (12, -18, 28)
    area.rotation_euler = (Vector((0, 0, 0)) - area.location).to_track_quat("-Z", "Y").to_euler()
    camera_data = bpy.data.cameras.new("RouteLabPreviewCamera")
    camera = bpy.data.objects.new("RouteLabPreviewCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    camera_data.type = "ORTHO"
    camera_data.ortho_scale = 85
    target = Vector((0, -3, 0))
    camera.location = (58, -72, 92)
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = camera

    validation = validate_layout(spawns)
    vertices = sum(len(obj.data.vertices) for obj in EXPORT_OBJECTS if obj.type == "MESH")
    assert len(EXPORT_OBJECTS) < 500 and vertices < 100000, "Prototype complexity exceeded its bound."
    blend_path = output / (NAME + ".blend")
    glb_path = output / (NAME + ".glb")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in EXPORT_OBJECTS:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = EXPORT_OBJECTS[0]
    bpy.ops.export_scene.gltf(filepath=str(glb_path), export_format="GLB", use_selection=True,
                              export_apply=True, export_extras=True, export_animations=False,
                              export_cameras=False, export_lights=False, export_yup=True,
                              export_draco_mesh_compression_enable=False)
    data = glb_path.read_bytes()
    assert struct.unpack_from("<4sII", data) == (b"glTF", 2, len(data)), "Invalid GLB header."
    json_size, chunk_type = struct.unpack_from("<II", data, 12)
    assert chunk_type == 0x4E4F534A
    gltf = json.loads(data[20:20 + json_size])
    assert not any(row.get("uri") for key in ("buffers", "images") for row in gltf.get(key, []))
    started = time.monotonic()
    bpy.ops.render.render(write_still=True)
    elapsed = round(time.monotonic() - started, 6)
    manifest = {
        "schema_version": 1, "id": NAME, "title": "Daftar Route Lab", "status": "original_blockout_prototype",
        "authored_map_replacement": False, "gameplay_integration_verified": False, "unreal_executed": False,
        "source_repository": "occult-kranti/ANDOLAN", "conventions_commit": PINNED_ANDOLAN,
        "geometry_source": "Original procedural Blender primitives; no downloaded assets or textures.",
        "dimensions_m": {"east_west": 48, "north_south": 56}, "nominal_route_width_m": 6.0,
        "axes": {"plan": "+X east, +Z north", "blender": "+X east, +Y north, +Z up",
                 "gltf": "+X east, +Y up, -Z north"},
        "objective": {"east": 0, "north": 0, "disk_radius_m": 3.0, "clearance_radius_from_centre_m": 4.5},
        "spawns": spawns, "obstacles": OBSTACLES, "layout_validation": validation,
        "travel_time_note": "Idealized distances at 5 m/s; no movement controller, combat, water or balance simulation.",
        "palette": PALETTE, "blender_version": bpy.app.version_string,
        "geometry": {"export_objects": len(EXPORT_OBJECTS), "source_mesh_vertices": vertices,
                     "gltf_nodes": len(gltf.get("nodes", [])), "gltf_meshes": len(gltf.get("meshes", []))},
        "render": {"engine": "CYCLES", "device": "CPU", "threads": 2, "samples": args.samples,
                   "denoising": False, "resolution": [1024, 832], "time_limit_seconds": 60,
                   "actual_render_seconds": elapsed},
        "recipe_sha256": sha256(Path(__file__).resolve()),
        "files": {p.name: {"bytes": p.stat().st_size, "sha256": sha256(p)} for p in
                  (blend_path, glb_path, output / "route-lab-preview.png")},
        "next_gates": ["GLB reimport and unit check", "Host-engine collision/navigation/controller setup",
                       "Human route review and playtest", "Unreal import/render acceptance if that engine is selected"],
    }
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("DAFTAR_ROUTE_LAB=" + json.dumps({"blender": bpy.app.version_string,
          "layout_passed": validation["passed"], "export_objects": len(EXPORT_OBJECTS),
          "source_vertices": vertices, "render_seconds": elapsed, "device": "CPU"}))


if __name__ == "__main__":
    main()
