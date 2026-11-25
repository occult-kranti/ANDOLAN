"""Render four production character turnarounds using Blender Cycles on two CPU threads.

Run from any directory with Blender 4.3 and Pillow:
    OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=2 blender -b -t 2 --python-exit-code 1 -P blender_stills.py
Append "-- shiva" (or other hero IDs) to render selected sheets only.
"""
import hashlib
import json
import math
import os
import sys
import tempfile
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont

PACK = Path(__file__).resolve().parents[1]
NATIVE = PACK.parents[1]
REPO = NATIVE.parents[1]
PANEL_SIZE = (448, 624)
SAMPLES = 32
# The downloadable meshes also drive the animated study films.
HEROES = {
    "shiva": (PACK / "models/shiva.glb", "cast3", 15 / 42, "Tandava Downbeat", "Raised-knee anticipation"),
    "krishna": (PACK / "models/krishna.glb", "cast3", 30 / 48, "Govardhan Canopy", "Left-hand lift"),
    "rama": (PACK / "models/rama.glb", "volley_draw", .76, "Dawn Volley", "Draw"),
    "hanuman": (PACK / "models/hanuman.glb", "mountain_pulse", .52, "Mountain Pulse", "Enhanced native action"),
}
VIEWS = (
    ("Front", 0, 2, False),
    ("Left profile", 90, 2, False),
    ("Rear", 180, 2, False),
    ("Action", -30, 4, True),
)


def sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def load_model(source):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(source))
    rig, = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
    # glTF creates a hidden 2-metre Icosphere to visualize bones. It is absent from the render.
    meshes = [o for o in bpy.context.scene.objects if o.type in {"MESH", "CURVE"}
              and not o.hide_render and o.visible_get() and any(not c.hide_render for c in o.users_collection)]
    return rig, meshes


def select_pose(rig, name, phase):
    data = rig.animation_data_create()
    for track in data.nla_tracks:
        track.mute = True
    action = bpy.data.actions.get(name)
    if action is None:
        action, = [a for a in bpy.data.actions if a.name.startswith(name + "_")]
    data.action = action
    start, end = action.frame_range
    frame = float(start + (end - start) * phase)
    bpy.context.scene.frame_set(math.floor(frame), subframe=frame % 1)
    bpy.context.view_layer.update()
    return dict(action=action.name, frame=round(frame, 4), phase=round(phase, 4))


def coordinate_cloud(meshes):
    """Use every evaluated vertex, including the skinned bow, tail, trident or chakra."""
    graph = bpy.context.evaluated_depsgraph_get()
    coords = []
    for source in meshes:
        obj = source.evaluated_get(graph)
        mesh = obj.to_mesh()
        try:
            if len(mesh.vertices):
                values = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
                mesh.vertices.foreach_get("co", values)
                matrix = np.array(obj.matrix_world)
                coords.append(values.reshape(-1, 3) @ matrix[:3, :3].T + matrix[:3, 3])
        finally:
            obj.to_mesh_clear()
    return np.concatenate(coords)


def studio(floor):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = SAMPLES
    scene.cycles.use_denoising = bool(getattr(bpy.app.build_options, "openimagedenoise", False))
    scene.cycles.max_bounces = 4
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 2
    scene.render.use_persistent_data = True
    scene.render.resolution_x, scene.render.resolution_y = PANEL_SIZE
    scene.render.resolution_percentage = 100
    scene.render.film_transparent = False
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.use_compositing = False
    scene.render.use_sequencer = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.exposure = 0
    scene.view_settings.gamma = 1
    scene.world = bpy.data.worlds.new("Neutral studio fill")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (.21, .23, .27, 1)
    bg.inputs[1].default_value = .45

    bpy.ops.mesh.primitive_plane_add(size=700, location=(0, 0, floor - .008))
    mat = bpy.data.materials.new("Slate matte studio floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (.067, .080, .097, 1)
    bsdf.inputs["Roughness"].default_value = .83
    bpy.context.object.data.materials.append(mat)
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.data.type = "ORTHO"
    camera.data.clip_end = 600.0
    scene.camera = camera
    lights = []
    for name, power, size, color in [
        ("Warm key", 240, 3.0, (1., .85, .70)),
        ("Cool fill", 115, 2.8, (.74, .86, 1.)),
        ("Edge", 305, 2.1, (1., .90, .77)),
    ]:
        lamp = bpy.data.lights.new(name, "AREA")
        lamp.energy, lamp.shape, lamp.size, lamp.color = power, "DISK", size, color
        obj = bpy.data.objects.new(name, lamp)
        scene.collection.objects.link(obj)
        lights.append(obj)
    return camera, lights


def plan_camera(points, az, elevation):
    a, e = math.radians(az), math.radians(elevation)
    back = Vector((math.sin(a) * math.cos(e), -math.cos(a) * math.cos(e), math.sin(e)))
    rot = (-back).to_track_quat("-Z", "Y")
    right, up = rot @ Vector((1, 0, 0)), rot @ Vector((0, 1, 0))
    xy = points @ np.array([right, up]).T
    low, high = xy.min(axis=0), xy.max(axis=0)
    middle = (high + low) * .5
    center = right * middle[0] + up * middle[1]
    w, h = high - low
    fit = max(h / .91, w / (PANEL_SIZE[0] / PANEL_SIZE[1] * .90))
    return center, back, right, rot, float(fit), xy


def shadow_lights(lights, back, right):
    horizontal = Vector((back.x, back.y, 0)).normalized()
    for light, side, depth, height in zip(lights, (-2.4, 2.5, 1.15), (2.35, 1.45, -2.3), (3.7, 2.4, 3.3)):
        light.location = horizontal * depth + right * side + Vector((0, 0, height))
        aim(light, (0, 0, 1.10))


def typeface(size, bold=False):
    base = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(base, size)
    except OSError:
        return ImageFont.load_default()


def sheet(name, title, action_label, files, output):
    width, height = PANEL_SIZE
    pad, gap, header, footer = 18, 4, 56, 36
    board = Image.new("RGB", (width*4 + gap*3 + pad*2, height + header + footer), "#141a20")
    draw = ImageDraw.Draw(board)
    draw.text((pad, 8), name.title(), font=typeface(32, True), fill="#f2e9da")
    sub = "BLENDER   /   MESH AND MATERIAL STUDY"
    draw.text((board.width - pad, 21), sub, font=typeface(14), fill="#b0bfca", anchor="ra")
    for index, ((label, _, _, active), file) in enumerate(zip(VIEWS, files)):
        left = pad + index*(width + gap)
        with Image.open(file) as img:
            board.paste(img.convert("RGB"), (left, header))
        draw.text((left + 6, height + header + 7), title + "  /  " + action_label if active else label,
                  font=typeface(15, active), fill="#e5ded2")
    board.save(output, "WEBP", quality=94, method=5)
    return list(board.size)


def render(name, folder):
    source, action, phase, title, subtitle = HEROES[name]
    rig, meshes = load_model(source)
    idle_note = select_pose(rig, "idle", .08)
    idle = coordinate_cloud(meshes)
    action_note = select_pose(rig, action, phase)
    active = coordinate_cloud(meshes)
    extent_delta = np.linalg.norm(active-idle, axis=1)
    if float(extent_delta.max()) < .035:
        raise ValueError(f"{name} has no measurable action deformation")
    cam, lights = studio(float(min(idle[:, 2].min(), active[:, 2].min())))
    jobs = [plan_camera(active if act else idle, az, el) for _, az, el, act in VIEWS]
    common_scale = max(job[4] for job in jobs[:3])
    paths, views = [], []
    for (label, az, el, act), (center, back, right, rotation, fit, xy) in zip(VIEWS, jobs):
        select_pose(rig, action if act else "idle", phase if act else .08)
        cam.location = center + back * 7
        cam.rotation_euler = rotation.to_euler()
        cam.data.ortho_scale = max(common_scale, fit) if act else common_scale
        shadow_lights(lights, back, right)
        # Bounds in the final camera gate form an independent framing check.
        bounds = xy.max(axis=0) - xy.min(axis=0)
        occupied = bounds / [cam.data.ortho_scale * PANEL_SIZE[0] / PANEL_SIZE[1], cam.data.ortho_scale]
        if any(value > .911 for value in occupied):
            raise ValueError(f"Camera crops the {name} {label} pose")
        path = folder / f"{name}-{label}.png"
        bpy.context.scene.render.filepath = str(path)
        print("STILL", name, label, flush=True)
        bpy.ops.render.render(write_still=True)
        paths.append(path)
        views.append(dict(view=label, azimuth=az, elevation=el, pose=action_note if act else idle_note,
                          bounds_fraction_xy=[round(float(v), 4) for v in occupied]))
    out = PACK / "media/stills" / f"{name}.webp"
    out.parent.mkdir(parents=True, exist_ok=True)
    dimensions = sheet(name, title, subtitle, paths, out)
    return dict(hero=name, source=str(source.relative_to(REPO)), source_sha256=sha(source),
                output=str(out.relative_to(PACK)), sha256=sha(out), size=dimensions,
                evaluated_vertices=len(idle), visible_geometry_objects=len(meshes),
                maximum_action_vertex_displacement_m=round(float(extent_delta.max()), 5), views=views)


def main():
    selected = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else list(HEROES)
    if not selected or any(hero not in HEROES for hero in selected):
        raise SystemExit("Hero selection must use hanuman, rama, shiva or krishna")
    evidence = PACK / "evidence/blender-stills.json"
    evidence.parent.mkdir(exist_ok=True)
    existing = json.loads(evidence.read_text())["heroes"] if evidence.exists() else {}
    with tempfile.TemporaryDirectory(prefix="yuga-blender-stills-") as folder:
        for hero in selected:
            existing[hero] = render(hero, Path(folder))
            record = dict(blender=bpy.app.version_string, renderer="Cycles CPU", threads=2,
                          samples=SAMPLES, panel_size=PANEL_SIZE, heroes=existing)
            tmp = evidence.with_suffix(".tmp")
            tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
            os.replace(tmp, evidence)


if __name__ == "__main__":
    main()
