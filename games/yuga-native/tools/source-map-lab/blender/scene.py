"""Open both source-map GLBs in Blender and render matched geometry/material studies.

    blender -b --factory-startup -t 2 --python-exit-code 1 --python scene.py -- \
      --baseline dust2-baseline.glb --variant dust2-jade.glb --overview de_dust2.txt \
      --objectives objectives.json --output ./views

Both GLBs are kept as inputs. Source X/Y/Z become Blender X/Y/Z at 0.0254 m/unit.
The supplied radar transform and actual site brush bounds register the cameras.
"""

import argparse
import contextlib
import csv
import hashlib
import json
import math
import re
import shutil
import struct
import sys
import tempfile
from pathlib import Path

import bpy
from mathutils import Vector


UNIT = 0.0254
EYE_HEIGHT = 1.60
META = "yugaLabSourceIndex"
GROUND = "yugaGround"
VIEWS = ("overview", "site-a", "site-b")


def parse():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ("baseline", "variant", "overview", "objectives", "output"):
        parser.add_argument("--" + key, required=True, type=Path)
    parser.add_argument("--resolution", type=int, default=960, help="horizontal pixels")
    parser.add_argument(
        "--samples", type=int, default=8, help="Cycles CPU samples per pixel"
    )
    parser.add_argument(
        "--nav",
        type=Path,
        help="Optional matched Source NAV area CSV with all four elevation corners",
    )
    parser.add_argument(
        "--entities",
        type=Path,
        help="BSP entity-lump JSON containing light_environment",
    )
    parser.add_argument("--radar-pixels", type=int, default=1024)
    outputs = parser.add_mutually_exclusive_group()
    outputs.add_argument(
        "--preview-only",
        action="store_true",
        help="render camera and material checks without packing a production .blend",
    )
    outputs.add_argument(
        "--skip-images",
        action="store_true",
        help="save the scene and camera registration only",
    )
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1 :])
    if args.samples <= 0 or args.resolution < 8 or args.radar_pixels <= 0:
        parser.error(
            "Samples and radar size must be positive, and resolution at least 8 pixels"
        )
    return args


def read_glb(path):
    with path.open("rb") as src:
        magic, version, size = struct.unpack("<4sII", src.read(12))
        length, chunk = struct.unpack("<I4s", src.read(8))
        if (
            magic != b"glTF"
            or version != 2
            or chunk != b"JSON"
            or size != path.stat().st_size
        ):
            raise ValueError(f"Invalid glTF 2.0 binary: {path}")
        data = json.loads(src.read(length))
        offset = src.tell()
        size, kind = struct.unpack("<I4s", src.read(8))
        if kind != b"BIN\0" or offset + 8 + size != path.stat().st_size:
            raise ValueError(f"Expected one embedded glTF buffer: {path}")
        return data, offset, size


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def changed_ground(base, variant):
    a, b = base["materials"], variant["materials"]
    if len(a) != len(b):
        raise ValueError("Material tables differ in length")
    changed = set()
    for index, (left, right) in enumerate(zip(a, b)):
        if left == right:
            continue
        pl = left.get("pbrMetallicRoughness", {})
        pr = right.get("pbrMetallicRoughness", {})
        restored = {
            **right,
            "pbrMetallicRoughness": {
                **pr,
                "baseColorFactor": pl.get("baseColorFactor", [1, 1, 1, 1]),
            },
        }
        original = {
            **left,
            "pbrMetallicRoughness": {
                **pl,
                "baseColorFactor": pl.get("baseColorFactor", [1, 1, 1, 1]),
            },
        }
        if restored != original or not (
            left.get("extras", {}).get(GROUND)
            or left.get("name", "").endswith(" / ground")
        ):
            raise ValueError(
                f"Non-ground or non-colour change at material {index}: {left.get('name')}"
            )
        changed.add(index)
    if not changed:
        raise ValueError("No ground material differs between inputs")
    return changed


def annotated_file(source, doc, offset, length, output):
    """Carry stable glTF indices across Blender's truncation and deduplication of names."""
    doc = {**doc}
    for group in ("nodes", "meshes", "materials"):
        doc[group] = [
            {**v, "extras": {**v.get("extras", {}), META: i}}
            for i, v in enumerate(doc.get(group, []))
        ]
    text = json.dumps(doc, ensure_ascii=False, separators=(",", ":")).encode()
    text += b" " * ((-len(text)) % 4)
    with output.open("wb") as dest, source.open("rb") as src:
        dest.write(
            struct.pack(
                "<4s4I",
                b"glTF",
                2,
                12 + 8 + len(text) + 8 + length,
                len(text),
                0x4E4F534A,
            )
        )
        dest.write(text)
        src.seek(offset)
        shutil.copyfileobj(src, dest, 2 * 1024 * 1024)


def import_scene(source, document, offset, length, scratch):
    tmp = scratch / (source.stem + "-indexed.glb")
    annotated_file(source, document, offset, length, tmp)
    try:
        status = bpy.ops.import_scene.gltf(filepath=str(tmp), import_pack_images=True)
        if "FINISHED" not in status:
            raise RuntimeError(f"Blender glTF import failed: {source}")
    finally:
        tmp.unlink(missing_ok=True)


def materials_of(obj):
    return [slot.material for slot in obj.material_slots]


def material_palette(base, variant, changed):
    """Import both exact glTF material graphs with one shared geometry/image buffer.

    A disposable mesh pairs each reference material with its edited equivalent.
    Reusing the source primitive preserves vertex colours, skin and UV semantics.
    """
    doc = {
        **base,
        "meshes": list(base["meshes"]),
        "nodes": list(base["nodes"]),
        "materials": list(base["materials"]),
        "scenes": [dict(scene) for scene in base["scenes"]],
    }
    active = doc.get("scene", 0)
    scene = doc["scenes"][active]
    scene["nodes"] = list(scene["nodes"])
    variant_ids = {}
    for index in sorted(changed):
        variant_ids[index] = len(doc["materials"])
        doc["materials"].append(
            {
                **variant["materials"][index],
                "name": variant["materials"][index].get("name", str(index)) + " / jade",
            }
        )
    representatives = {}
    for mesh in base["meshes"]:
        for prim in mesh["primitives"]:
            index = prim.get("material")
            if index in changed:
                # Blender creates a separate material graph when COLOR_0 is present.
                representatives.setdefault(
                    (index, "COLOR_0" in prim["attributes"]), prim
                )
    unused = changed.difference(index for index, _ in representatives)
    if unused:
        raise ValueError(f"Edited ground material has no source faces: {unused}")
    for (index, colored), primitive in representatives.items():
        name = f"Material swatch {index} {int(colored)}"
        mi = len(doc["meshes"])
        doc["meshes"].append(
            {
                "name": name,
                "extras": {"yugaLabPalette": index},
                "primitives": [
                    primitive,
                    {**primitive, "material": variant_ids[index]},
                ],
            }
        )
        scene["nodes"].append(len(doc["nodes"]))
        doc["nodes"].append({"name": name, "mesh": mi})
    return doc, variant_ids


def map_variants(reference, altered, variant_ids):
    materials = {}
    for obj in list(reference.objects):
        if obj.type != "MESH" or "yugaLabPalette" not in obj.data:
            continue
        mesh = obj.data
        index = mesh["yugaLabPalette"]
        pairs = {m[META]: m for m in materials_of(obj) if m}
        if set(pairs) != {index, variant_ids[index]}:
            raise ValueError(f"Invalid imported material pair on {obj.name}")
        materials[pairs[index]] = pairs[variant_ids[index]]
        bpy.data.objects.remove(obj, do_unlink=True)
        if not mesh.users:
            bpy.data.meshes.remove(mesh)
    clones = {}
    changed_count = 0
    for instance, original in enumerate(reference.objects):
        original["yugaLabInstanceId"] = instance
        clone = original.copy()
        altered.collection.objects.link(clone)
        clones[original] = clone
        if clone.type == "MESH":
            for slot in clone.material_slots:
                replacement = materials.get(slot.material)
                if replacement:
                    slot.link = "OBJECT"
                    slot.material = replacement
                    changed_count += 1
    # Link parents within this scene and keep their original local transform.
    for source, clone in clones.items():
        if source.parent:
            clone.parent = clones[source.parent]
    if not changed_count:
        raise ValueError("No visible scene object received an edited material")
    for source, replacement in materials.items():
        source.pass_index = replacement.pass_index = 1
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    return sum(obj.type == "MESH" for obj in clones), changed_count


def same_payload(args, base, edit, bo, eo, bl, el):
    if (
        bl != el
        or set(base) != set(edit)
        or any(base[k] != edit[k] for k in base if k != "materials")
    ):
        raise ValueError(
            "GLBs must differ only in the declared ground material factors"
        )
    with args.baseline.open("rb") as src, args.variant.open("rb") as dst:
        src.seek(bo + 8)
        dst.seek(eo + 8)
        while True:
            block = src.read(4 * 1024 * 1024)
            if block != dst.read(len(block)):
                raise ValueError(
                    "Embedded geometry, images or other binary data differ"
                )
            if not block:
                break


def load_radar(path, pixels):
    values = dict(re.findall(r'"([^"]+)"\s*"([^"]+)"', path.read_text()))
    left = float(values["pos_x"])
    top = float(values["pos_y"])
    width = float(values["scale"]) * pixels
    return dict(
        left=left,
        top=top,
        size=width,
        site_uv={
            k: [float(values[f"bomb{k}_x"]), float(values[f"bomb{k}_y"])] for k in "AB"
        },
    )


def resolve_sites(path, radar):
    raw = json.loads(path.read_text())
    if not isinstance(raw, list) or len(raw) != 2:
        raise ValueError("Expected two registered site brush bounds")

    def mid(obj):
        return Vector([(a + b) / 2 for a, b in zip(obj["min"], obj["max"])])

    pos = {
        k: Vector((radar["left"] + u * radar["size"], radar["top"] - v * radar["size"]))
        for k, (u, v) in radar["site_uv"].items()
    }
    if (mid(raw[0]).xy - pos["A"]).length > (mid(raw[1]).xy - pos["A"]).length:
        raw = list(reversed(raw))
    return dict(zip("AB", raw))


class NavFloor:
    """Match a point in metres to a Source area and its true bilinear floor."""

    def __init__(self, path):
        self.areas = []
        if path:
            with path.open() as stream:
                for row in csv.DictReader(stream):
                    corners = [
                        float(row[k]) * UNIT
                        for k in (
                            "northWestX",
                            "northWestY",
                            "southEastX",
                            "southEastY",
                            "northWestZ",
                            "northEastZ",
                            "southWestZ",
                            "southEastZ",
                        )
                    ]
                    self.areas.append(
                        (
                            corners,
                            {"area_id": int(row["areaId"]), "callout": row["areaName"]},
                        )
                    )

    def match(self, point):
        options = []
        for (x0, y0, x1, y1, nw, ne, sw, se), record in self.areas:
            if x0 <= point.x <= x1 and y0 <= point.y <= y1 and x1 > x0 and y1 > y0:
                u = (point.x - x0) / (x1 - x0)
                v = (point.y - y0) / (y1 - y0)
                z = (1 - v) * ((1 - u) * nw + u * ne) + v * ((1 - u) * sw + u * se)
                options.append((abs(point.z - z), record, z))
        if not options:
            return None
        gap, record, z = min(options, key=lambda v: v[0])
        return (
            {**record, "nav_z_m": round(z, 5), "foot_to_nav_m": round(gap, 5)}
            if gap < 0.38
            else None
        )


def choose_camera(scene, site, letter, nav):
    """Use ray-cast ground and wall clearance around the real trigger centre."""
    deps = bpy.context.evaluated_depsgraph_get()
    low = Vector(site["min"]) * UNIT
    high = Vector(site["max"]) * UNIT
    anchor = (low + high) * 0.5
    anchor.z = low.z + 0.95

    # Avoid starting directly on a crate or on a ceiling. Candidates can land
    # within one body height of the registered site floor to follow nearby steps.
    def floor(x, y):
        ray = scene.ray_cast(
            deps, Vector((x, y, low.z + 2.00)), Vector((0, 0, -1)), distance=4.15
        )
        if not ray[0] or abs(ray[2].z) < 0.68:
            return None
        return ray[1]

    floor_anchor = floor(anchor.x, anchor.y)
    if floor_anchor is not None:
        anchor.z = floor_anchor.z + 0.9
    best = None
    for radius in (4.5, 6.5, 9.0, 12.0):
        for k in range(36):
            theta = (k * math.tau / 36) + math.radians(4)
            x = anchor.x + math.cos(theta) * radius
            y = anchor.y + math.sin(theta) * radius
            floor_point = floor(x, y)
            if floor_point is None or abs(floor_point.z - low.z) > 1.75:
                continue
            if nav.areas and nav.match(floor_point) is None:
                continue
            eye = floor_point + Vector((0, 0, EYE_HEIGHT))
            # Eye clearance in front and to each side plus foot-to-head clearance.
            overhead = scene.ray_cast(
                deps,
                floor_point + Vector((0, 0, 0.06)),
                Vector((0, 0, 1)),
                distance=EYE_HEIGHT + 0.21,
            )
            if overhead[0]:
                continue
            if any(
                scene.ray_cast(
                    deps,
                    eye,
                    Vector((math.cos(i * math.pi / 2), math.sin(i * math.pi / 2), 0)),
                    distance=0.42,
                )[0]
                for i in range(4)
            ):
                continue
            aim = anchor - eye
            if scene.ray_cast(
                deps, eye, aim.normalized(), distance=max(0.1, aim.length - 0.35)
            )[0]:
                continue
            right = Vector((aim.y, -aim.x, 0)).normalized()
            spread = 0
            depths = []
            for offset in (-0.7, -0.4, -0.15, 0.15, 0.4, 0.7):
                for elevation in (-0.11, 0.09, 0.29):
                    look = (
                        aim.normalized() + right * offset + Vector((0, 0, elevation))
                    ).normalized()
                    hit = scene.ray_cast(deps, eye, look, distance=45)
                    depths.append(min(21, (hit[1] - eye).length) if hit[0] else 21)
                    if hit[0] and (hit[1] - eye).length > 4:
                        spread += 1
            # Prefer open floor, useful background beyond the site and a clear
            # ground foreground. Bias only breaks equivalent candidate bearings.
            grounded = 0
            for offset in (-0.48, -0.18, 0.18, 0.48):
                look = (
                    aim.normalized() + right * offset + Vector((0, 0, -0.42))
                ).normalized()
                hit = scene.ray_cast(deps, eye, look, distance=22)
                if hit[0] and abs(hit[2].z) > 0.62:
                    grounded += 1
            score = (
                spread * 0.14
                + sum(depths) / len(depths) * 0.11
                + grounded * 0.65
                - abs(radius - 8) * 0.06
            )
            if best is None or score > best[0]:
                best = (score, eye, anchor.copy(), floor_point.copy())
    if not best:
        raise RuntimeError(f"Could not find a supported camera around site {letter}")
    return best[1:]


def camera(scene, name, at, look, lens=24, ortho=0):
    data = bpy.data.cameras.new(name)
    obj = bpy.data.objects.new(name, data)
    scene.collection.objects.link(obj)
    obj.location = at
    if ortho:
        # x points right and source world +y points to the top of the sheet.
        obj.rotation_euler = (0, 0, 0)
        data.type = "ORTHO"
        data.ortho_scale = ortho
    else:
        obj.rotation_euler = (look - at).to_track_quat("-Z", "Y").to_euler()
        data.type = "PERSP"
        data.lens = lens
        data.sensor_width = 36
    data.clip_start = 0.025
    data.clip_end = 1300.0
    return obj


def read_daylight(path):
    if not path:
        return None
    entities = json.loads(path.read_text())
    lights = [e for e in entities if e.get("classname") == "light_environment"]
    if len(lights) != 1:
        raise ValueError("Expected one map light_environment")
    light = lights[0]
    angles = [float(value) for value in light["angles"].split()]

    def color(key):
        values = [float(value) for value in light.get(key + "HDR", "").split()]
        if len(values) != 4 or min(values[:3]) < 0:
            values = [float(value) for value in light[key].split()]
        if len(values) != 4:
            raise ValueError(f"Expected an RGB and intensity in {key}")
        return values

    return dict(
        hammer_id=light.get("hammerid"),
        yaw_deg=angles[1],
        pitch_deg=float(light.get("pitch", angles[0])),
        spread_deg=float(light.get("SunSpreadAngle", 0)),
        sunlight=color("_light"),
        ambient=color("_ambient"),
    )


def srgb(channel):
    channel /= 255
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def stage(ref, edit, radar, sites, nav, daylight, width, samples):
    bpy.context.window.scene = ref
    world = bpy.data.worlds.new("Dust II • shared ambient sky")
    world.use_nodes = True
    bgcolor = world.node_tree.nodes.get("Background")
    bgcolor.inputs["Color"].default_value = (0.59, 0.71, 0.86, 1)
    bgcolor.inputs["Strength"].default_value = 0.75
    sun_data = bpy.data.lights.new("Dry daylight", "SUN")
    sun_data.energy = 2.3
    sun_data.angle = math.radians(9)
    sun_data.color = (1, 0.91, 0.79)
    sun = bpy.data.objects.new("Dust II • shared sun", sun_data)
    sun.rotation_euler = (math.radians(25), math.radians(-26), math.radians(-38))
    if daylight:
        yaw, pitch = [math.radians(daylight[k]) for k in ("yaw_deg", "pitch_deg")]
        rays = Vector(
            (
                math.cos(yaw) * math.cos(pitch),
                math.sin(yaw) * math.cos(pitch),
                math.sin(pitch),
            )
        )
        sun.rotation_euler = rays.to_track_quat("-Z", "Y").to_euler()
        sunlight, ambient = daylight["sunlight"], daylight["ambient"]
        sun_data.color = [srgb(v) for v in sunlight[:3]]
        sun_data.energy = sunlight[3] / 255
        sun_data.angle = math.radians(max(0.53, daylight["spread_deg"]))
        bgcolor.inputs["Color"].default_value = [*(srgb(v) for v in ambient[:3]), 1]
        bgcolor.inputs["Strength"].default_value = ambient[3] / 255
    ref.collection.objects.link(sun)
    edit.collection.objects.link(sun)
    mid = Vector(
        (
            (radar["left"] + radar["size"] / 2) * UNIT,
            (radar["top"] - radar["size"] / 2) * UNIT,
            0,
        )
    )
    distance = radar["size"] * UNIT
    # Slightly expand the registered square so landmarks at the edge remain in shot.
    overhead = camera(
        ref, "00 • Radar extent", mid + Vector((0, 0, 180)), mid, ortho=distance * 1.04
    )
    shots = {"overview": (overhead, mid, None)}
    for letter, source in sites.items():
        eye, look, foot = choose_camera(ref, source, letter, nav)
        shots["site-" + letter.lower()] = (
            camera(ref, letter + " • Site at player height", eye, look, lens=24),
            look,
            foot,
        )
    for cam, _, _ in shots.values():
        edit.collection.objects.link(cam)
    for scene in (ref, edit):
        scene.world = world
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = samples
        scene.cycles.use_denoising = False
        scene.cycles.use_adaptive_sampling = False
        scene.cycles.seed = 427
        scene.cycles.max_bounces = 2
        scene.cycles.diffuse_bounces = 0
        scene.cycles.glossy_bounces = 0
        scene.cycles.transmission_bounces = 0
        scene.cycles.transparent_max_bounces = 4
        scene.render.use_persistent_data = False
        scene.render.image_settings.file_format = "PNG"
        scene.render.image_settings.color_mode = "RGB"
        scene.render.image_settings.color_depth = "8"
        scene.render.resolution_percentage = 100
        scene.render.resolution_x = width
        scene.render.resolution_y = width
        scene.render.film_transparent = False
        scene.view_settings.view_transform = "AgX"
        scene.render.image_settings.compression = 25
        scene.frame_start = 1
        scene.frame_end = 3
        for i, (key, (cam, _, _)) in enumerate(shots.items(), 1):
            mark = scene.timeline_markers.new(key, frame=i)
            mark.camera = cam
        scene.frame_set(1)
        scene.camera = overhead
        scene.view_layers[0].use_pass_material_index = True
    return shots


def mask_output(scene, temp_root):
    scene.use_nodes = True
    tree = scene.node_tree
    tree.nodes.clear()
    source = tree.nodes.new("CompositorNodeRLayers")
    source.scene = scene
    out = tree.nodes.new("CompositorNodeComposite")
    tree.links.new(source.outputs["Image"], out.inputs["Image"])
    mask = tree.nodes.new("CompositorNodeIDMask")
    mask.index = 1
    mask.use_antialiasing = True
    tree.links.new(source.outputs["IndexMA"], mask.inputs["ID value"])
    mask_file = tree.nodes.new("CompositorNodeOutputFile")
    mask_file.base_path = str(temp_root)
    mask_file.format.file_format = "PNG"
    mask_file.format.color_mode = "BW"
    mask_file.format.color_depth = "8"
    tree.links.new(mask.outputs["Alpha"], mask_file.inputs[0])
    return mask_file


def vec(v):
    return [round(float(x), 6) for x in v]


def run(args):
    args.output.mkdir(parents=True, exist_ok=True)
    inputs = {
        key: digest(path)
        for key, path in (
            ("baseline", args.baseline),
            ("jade", args.variant),
            ("overview", args.overview),
            ("objectives", args.objectives),
            ("nav_csv", args.nav),
            ("entities", args.entities),
        )
        if path
    }
    base, bo, bl = read_glb(args.baseline)
    edit, eo, el = read_glb(args.variant)
    same_payload(args, base, edit, bo, eo, bl, el)
    changed = changed_ground(base, edit)
    radar = load_radar(args.overview, args.radar_pixels)
    sites = resolve_sites(args.objectives, radar)
    nav = NavFloor(args.nav)
    daylight = read_daylight(args.entities)
    print(
        f"Ground-only difference in {len(changed)} imported source materials",
        flush=True,
    )
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ref = bpy.context.scene
    ref.name = "01 • Reference"
    ref.use_fake_user = True
    with tempfile.TemporaryDirectory(prefix="dust2-blender-") as tmp:
        scratch = Path(tmp)
        document, variant_ids = material_palette(base, edit, changed)
        import_scene(args.baseline, document, bo, bl, scratch)
        altered = bpy.data.scenes.new("02 • Ground recolour")
        altered.use_fake_user = True
        count, overrides = map_variants(ref, altered, variant_ids)
        print(
            f"Paired {count} source mesh objects; preparing matched viewpoints",
            flush=True,
        )
        shots = stage(
            ref, altered, radar, sites, nav, daylight, args.resolution, args.samples
        )
        bpy.context.window.scene = altered
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == "VIEW_3D":
                    area.spaces.active.region_3d.view_perspective = "CAMERA"
                    area.spaces.active.overlay.show_overlays = False
                    area.spaces.active.shading.color_type = "MATERIAL"
                    if screen.name == "Layout":
                        area.spaces.active.shading.type = "MATERIAL"
        instructions = bpy.data.texts.new("Start here")
        instructions.write(
            "DUST II / GROUND STUDY\n\nSelect 01 • Reference or 02 • Ground recolour in the scene dropdown. Both use the same mesh datablocks, cameras and lights. Timeline marks 1, 2 and 3 select the registered map overview and eye-height views of the two objective sites.\n\nAt the overview the radar square is north-up. A detached three-dimensional skybox and off-map backdrop in the source remain placed in world space. The finished reference/recolour comparison images use identical CPU lighting and geometry.\n"
        )
        bpy.context.preferences.filepaths.save_version = 0
        filename = args.output / "dust2-ground-study.blend"
        if not args.preview_only:
            with contextlib.suppress(RuntimeError):
                bpy.ops.file.pack_all()
            bpy.ops.wm.save_as_mainfile(filepath=str(filename), compress=True)
        register = {}
        for key, (cam, target, foot) in shots.items():
            register[key] = dict(
                eye_m=vec(cam.location),
                target_m=vec(target),
                blender_xyz="source xyz * 0.0254",
                camera=cam.data.type,
                lens_mm=cam.data.lens if key != "overview" else None,
                ortho_span_m=cam.data.ortho_scale if key == "overview" else None,
                foot_m=vec(foot) if foot is not None else None,
                nav_support=nav.match(foot) if foot is not None else None,
            )
        if not args.skip_images:
            file_node = mask_output(ref, scratch)
            for label, scene in (("baseline", ref), ("jade", altered)):
                bpy.context.window.scene = scene
                for i, (key, (cam, _, _)) in enumerate(shots.items(), 1):
                    scene.frame_set(i)
                    scene.camera = cam
                    scene.render.resolution_x = args.resolution
                    scene.render.resolution_y = (
                        args.resolution
                        if key == "overview"
                        else round(args.resolution * 9 / 16)
                    )
                    file_node.file_slots[0].path = key + "-mask-"
                    out = args.output / f"{key}-{label}.png"
                    scene.render.filepath = str(out)
                    bpy.ops.render.render(scene=scene.name, write_still=True)
                    if label == "baseline":
                        mask = next(scratch.glob(f"{key}-mask-*.png"))
                        mask.replace(args.output / f"{key}-ground-mask.png")
                    print("Rendered", out, flush=True)
        report = dict(
            blender_version=bpy.app.version_string,
            inputs=inputs,
            resolution_x=args.resolution,
            samples=args.samples,
            renderer="Cycles CPU, shared sun/ambient, no diffuse or glossy indirect bounces",
            state_switch="Blender Scene dropdown",
            unique_glb_meshes=len(base["meshes"]),
            paired_mesh_objects=count,
            object_ground_slots=overrides,
            ground_material_indices=sorted(changed),
            overview_source=radar,
            light_environment_source=daylight,
            sites_source=sites,
            cameras=register,
            blend=filename.name if not args.preview_only else None,
            blend_sha256=digest(filename) if not args.preview_only else None,
        )
        (args.output / "cameras-and-render.json").write_text(
            json.dumps(report, indent=2) + "\n"
        )
        print(
            f"Finished {args.output} with {len(changed)} changed ground materials and {len(shots)} matched cameras",
            flush=True,
        )


if __name__ == "__main__":
    run(parse())
