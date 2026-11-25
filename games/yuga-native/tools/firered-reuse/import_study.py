"""Build and verify an editable Blender study library from a captured Y-up mesh inventory.

blender -b -t 3 --python-exit-code 1 -P import_study.py -- --manifest shapes.json --output-dir study
blender -b --python-exit-code 1 -P import_study.py -- --manifest shapes.json --output-dir study --verify
"""

import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import uuid

import bpy
from mathutils import Vector
from PIL import Image, ImageDraw, ImageFont


LIBRARY = "rust-fallback-study.blend"
OVERVIEW = "rust-fallback-overview.png"
PREVIEW_PX = 216


# The source uses a right-handed, Y-up world. Blender uses right-handed Z-up.
def blender_point(vertex):
    x, y, z = vertex
    if not all(math.isfinite(value) for value in (x, y, z)):
        raise ValueError("Non-finite vertex in source inventory")
    return Vector((x, -z, y))


def hash_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def display_name(slug):
    return slug.replace("_", " ").replace("-", " ").capitalize()


def catalog_id(category):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, "yuga/blender/rust-fallback-study/" + category))


def make_materials(palette):
    materials = {}
    for name, rgb in palette.items():
        if len(rgb) != 3 or any(not 0 <= channel <= 255 for channel in rgb):
            raise ValueError(f"Invalid sRGB palette entry {name}")
        material = bpy.data.materials.new(name)
        channels = [v / 255 for v in rgb]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        material.diffuse_color = (*linear, 1)
        material.use_nodes = True
        bsdf = material.node_tree.nodes.get("Principled BSDF")
        bsdf.inputs["Base Color"].default_value = (*linear, 1)
        bsdf.inputs["Roughness"].default_value = .76
        materials[name] = material
    return materials


def bounds(points):
    first, *rest = points
    low, high = first.copy(), first.copy()
    for point in rest:
        for axis in range(3):
            low[axis] = min(low[axis], point[axis])
            high[axis] = max(high[axis], point[axis])
    return low, high


def normalized_axis(value, low, high):
    # Snapping an extremum keeps translated and narrow source blocks on one
    # canonical mesh even when their Bevy f32 endpoints round differently.
    if low == high:
        return 0.0
    if value == low:
        return -.5
    if value == high:
        return .5
    return round((value - low) / (high - low) - .5, 7)


def make_part(part, collection, index, materials, mesh_cache):
    vertices = [blender_point(v) for v in part["vertices"]]
    faces = tuple(tuple(face) for face in part["faces"])
    if not vertices or not faces or any(len(face) < 3 or min(face) < 0 or max(face) >= len(vertices) for face in faces):
        raise ValueError(f"Invalid topology in {collection.name} part {index}")
    low, high = bounds(vertices)
    center = (low + high) * .5
    # Keep each part transform editable; identical topology can share one mesh.
    scale = tuple((high[i] - low[i]) or 1.0 for i in range(3))
    local = tuple(tuple(normalized_axis(v[i], low[i], high[i]) for i in range(3)) for v in vertices)
    # Bevy UV_0 uses the top-left texture convention. Blender UV space is
    # bottom-left. Include UVs in the data-block key to preserve atlas seams.
    source_uv = part.get("uv0_by_vertex")
    uvs = None
    if source_uv is not None:
        if len(source_uv) != len(vertices) or any(len(uv) != 2 or not all(map(math.isfinite, uv)) for uv in source_uv):
            raise ValueError(f"Invalid UV_0 in {collection.name} part {index}")
        uvs = tuple((u, 1 - v) for u, v in source_uv)
    key = local, faces, uvs
    if key not in mesh_cache:
        mesh = bpy.data.meshes.new(part["kind"])
        mesh.from_pydata(local, [], faces)
        mesh.update()
        if mesh.validate():
            raise ValueError(f"Blender repaired source topology in {collection.name} part {index}")
        if uvs is not None:
            layer = mesh.uv_layers.new(name="UVMap")
            for loop in mesh.loops:
                layer.uv[loop.index].vector = uvs[loop.vertex_index]
        mesh.materials.append(materials[part["material"]])
        mesh_cache[key] = mesh
    obj = bpy.data.objects.new(f"{collection.name} {index + 1:02} {part['kind']}", mesh_cache[key])
    collection.objects.link(obj)
    obj.location = center
    obj.scale = scale
    obj.material_slots[0].link = 'OBJECT'
    obj.material_slots[0].material = materials[part["material"]]
    obj.hide_render = obj.hide_viewport = part["hidden"]
    obj["source_part"] = index
    return vertices


def add_lighting(scene, studio):
    scene.world = bpy.data.worlds.new("Study ambient")
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (.72, .79, .87, 1.0)
    background.inputs["Strength"].default_value = .45
    for name, direction, power, color in [
        ("Sun", (-5, -7, 11), 2.8, (1.0, .94, .82)),
        ("Fill", (6, 1, 5), .95, (.74, .86, 1.0)),
    ]:
        light = bpy.data.lights.new(name, 'SUN')
        light.energy, light.angle, light.color = power, math.radians(12), color
        obj = bpy.data.objects.new(name, light)
        obj.rotation_euler = (-Vector(direction)).to_track_quat('-Z', 'Y').to_euler()
        studio.objects.link(obj)
        obj.hide_select = True


def stage(scene, assets):
    studio = bpy.data.collections.new("Preview lighting")
    gallery = bpy.data.collections.new("Preview instances")
    scene.collection.children.link(studio)
    scene.collection.children.link(gallery)
    scene.render.engine = 'CYCLES'
    scene.cycles.device = 'CPU'
    scene.cycles.samples = 16
    scene.cycles.use_denoising = False
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    scene.view_settings.view_transform = 'AgX'
    add_lighting(scene, studio)
    cam = bpy.data.cameras.new("Study camera")
    cam.type = 'ORTHO'
    obj = bpy.data.objects.new(cam.name, cam)
    studio.objects.link(obj)
    normal = Vector((5, -8, 5.2)).normalized()
    rotation = (-normal).to_track_quat('-Z', 'Y')
    right = rotation @ Vector((1, 0, 0))
    up = rotation @ Vector((0, 1, 0))
    obj.rotation_euler = rotation.to_euler()
    obj.location = normal * 35
    scene.camera = obj
    side = math.ceil(math.sqrt(len(assets)))
    tile = 3.0
    cam.ortho_scale = tile * side
    scene.render.resolution_x = scene.render.resolution_y = side * PREVIEW_PX
    scene.render.resolution_percentage = 100
    for i, (_, collection, points) in enumerate(assets):
        extents = [(min(axis.dot(v) for v in points), max(axis.dot(v) for v in points)) for axis in (right, up, normal)]
        center = sum((axis * ((lo + hi) * .5) for axis, (lo, hi) in zip((right, up, normal), extents)), Vector((0, 0, 0)))
        factor = tile * .82 / max(hi - lo for lo, hi in extents[:2])
        x = tile * (i % side + .5 - side / 2)
        y = tile * (side / 2 - i // side - .5)
        inst = bpy.data.objects.new(collection.name, None)
        gallery.objects.link(inst)
        inst.instance_type = 'COLLECTION'
        inst.instance_collection = collection
        inst.scale = (factor,) * 3
        inst.location = right * x + up * y - center * factor
        inst.empty_display_size = .12
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                space = area.spaces.active
                space.region_3d.view_perspective = 'CAMERA'
                space.overlay.show_overlays = False
                space.shading.color_type = 'MATERIAL'
    return side


def label_font(size):
    try:
        return ImageFont.truetype("DejaVuSans.ttf", size)
    except OSError:
        return ImageFont.load_default(size=size)


def paint_previews(scene, assets, side, destination):
    groups = {}
    for i, (entry, _, _) in enumerate(assets):
        groups.setdefault(entry["category"], []).append(i)
    columns = min(5, side)
    cell_w, cell_h, gap = 224, 223, 12
    width = 48 + columns * (cell_w + gap) - gap
    height = 94 + sum(50 + math.ceil(len(group) / columns) * (cell_h + gap) for group in groups.values())
    sheet = Image.new("RGB", (width, height), "#f4f0e8")
    draw = ImageDraw.Draw(sheet)
    draw.text((24, 16), "Rust fallback mesh library", font=label_font(34), fill="#242e31")
    draw.text((26, 62), f"{len(assets)} collection assets   /   source units retained in Blender", font=label_font(15), fill="#47595b")
    with tempfile.TemporaryDirectory() as tmp:
        atlas = Path(tmp) / "atlas.png"
        scene.render.filepath = str(atlas)
        bpy.ops.render.render(write_still=True)
        raw = Image.open(atlas).convert("RGBA")
        top = 82
        for category, indices in groups.items():
            draw.text((24, top + 8), display_name(category), font=label_font(23), fill="#374c4e")
            top += 47
            for offset, i in enumerate(indices):
                entry, collection, _ = assets[i]
                left = (i % side) * PREVIEW_PX
                y = (i // side) * PREVIEW_PX
                icon = raw.crop((left, y, left + PREVIEW_PX, y + PREVIEW_PX))
                if icon.getchannel("A").getextrema()[1] == 0:
                    raise ValueError(f"Empty rendered preview: {entry['id']}")
                preview = Path(tmp) / f"preview-{i}.png"
                icon.save(preview)
                with bpy.context.temp_override(id=collection):
                    result = bpy.ops.ed.lib_id_load_custom_preview(filepath=str(preview))
                if result != {'FINISHED'}:
                    raise ValueError(f"Could not embed preview for {entry['id']}")
                x = 24 + (offset % columns) * (cell_w + gap)
                y = top + (offset // columns) * (cell_h + gap)
                draw.rectangle((x, y, x + cell_w - 1, y + cell_h - 1), fill="#e5e6df")
                icon.thumbnail((cell_w - 8, cell_h - 35), Image.Resampling.LANCZOS)
                sheet.paste(icon, (x + (cell_w - icon.width) // 2, y + 1), icon)
                title = display_name(entry["id"])
                font = label_font(16)
                if draw.textlength(title, font=font) > cell_w-16:
                    font = label_font(13)
                draw.text((x + 9, y + cell_h - 27), title, font=font, fill="#253238")
            top += math.ceil(len(indices) / columns) * (cell_h + gap)
        sheet.save(destination / OVERVIEW, optimize=True)
    scene.render.filepath = "//library-gallery.png"


def build(data, output):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    materials = make_materials(data["materials"])
    meshes = {}
    assets = []
    categories = set()
    for entry in sorted(data["elements"], key=lambda e: (e["category"], e["id"])):
        col = bpy.data.collections.new(entry["id"])
        col.asset_mark()
        cat = entry["category"]
        col.asset_data.catalog_id = catalog_id(cat)
        col.asset_data.tags.new(cat)
        col.asset_data.description = f"Source study from {entry['source_function']}. Coordinates are in tile units."
        col["element_id"] = entry["id"]
        col["source_function"] = entry["source_function"]
        col["category"] = cat
        visible = []
        for i, part in enumerate(entry["parts"]):
            points = make_part(part, col, i, materials, meshes)
            if not part["hidden"]:
                visible.extend(points)
        if not visible:
            raise ValueError(f"No visible mesh in {entry['id']}")
        categories.add(cat)
        assets.append((entry, col, visible))
    if not assets or len({entry["id"] for entry, _, _ in assets}) != len(assets):
        raise ValueError("Expected at least one element and unique element IDs")
    catfile = output / "blender_assets.cats.txt"
    catfile.write_text("VERSION 1\n\n" + "".join(
        f"{catalog_id(cat)}:Rust fallback/{cat}:{cat}\n" for cat in sorted(categories)
    ))
    side = stage(scene, assets)
    paint_previews(scene, assets, side, output)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(output / LIBRARY), compress=True)


def verify(data, manifest, output):
    bpy.ops.wm.open_mainfile(filepath=str(output / LIBRARY))
    scene = bpy.context.scene
    by_id = {c["element_id"]: c for c in bpy.data.collections if "element_id" in c}
    if set(by_id) != {entry["id"] for entry in data["elements"]}:
        raise ValueError("Reopened asset inventory differs from capture")
    preserved = []
    hidden = 0
    total = 0
    triangles = 0
    max_error = 0
    uv_parts = 0
    uv_loops = 0
    max_uv_error = 0.0
    for entry in data["elements"]:
        col = by_id[entry["id"]]
        parts = {int(obj["source_part"]): obj for obj in col.objects}
        preview = col.preview_ensure()
        if (len(parts) != len(entry["parts"]) or not col.asset_data or col.asset_data.catalog_id != catalog_id(entry["category"])
                or min(preview.image_size) <= 0):
            raise ValueError(f"Lost collection structure, catalog or preview: {entry['id']}")
        for i, source in enumerate(entry["parts"]):
            obj = parts[i]
            if (obj.hide_render != source["hidden"] or obj.hide_viewport != source["hidden"]
                    or obj.material_slots[0].material.name != source["material"]):
                raise ValueError(f"Visibility/material mismatch in {obj.name}")
            actual_faces = [list(poly.vertices) for poly in obj.data.polygons]
            if actual_faces != source["faces"] or len(obj.data.vertices) != len(source["vertices"]):
                raise ValueError(f"Topology differs in {obj.name}")
            expected_uv = source.get("uv0_by_vertex")
            layer = obj.data.uv_layers.active
            if (expected_uv is None) != (layer is None):
                raise ValueError(f"UV_0 presence differs in {obj.name}")
            if expected_uv is not None:
                for loop in obj.data.loops:
                    u, v = layer.uv[loop.index].vector
                    ref_u, ref_v = expected_uv[loop.vertex_index]
                    uv_error = max(abs(u - ref_u), abs(1 - v - ref_v))
                    if not math.isfinite(uv_error) or uv_error > 0.000001:
                        raise ValueError(f"UV mismatch after reopen in {obj.name}")
                    max_uv_error = max(uv_error, max_uv_error)
                    uv_loops += 1
                uv_parts += 1
            actual = obj.matrix_local
            errors = [(actual @ vert.co - blender_point(ref)).length for vert, ref in zip(obj.data.vertices, source["vertices"])]
            error = max(errors)
            if not math.isfinite(error) or error > 0.00005:
                raise ValueError(f"Coordinate mismatch {error} in {obj.name}")
            max_error = max(error, max_error)
            triangles += sum(len(poly.vertices) - 2 for poly in obj.data.polygons)
            hidden += int(obj.hide_render)
            total += 1
        preserved.append(entry["id"])
    gallery_instances = sum(obj.instance_type == 'COLLECTION' for obj in scene.objects)
    if gallery_instances != len(preserved):
        raise ValueError("Gallery instance count mismatch")
    report = {
        "blender": bpy.app.version_string, "source_manifest_sha256": hash_file(manifest),
        "library_sha256": hash_file(output / LIBRARY), "overview_sha256": hash_file(output / OVERVIEW),
        "elements": sorted(preserved), "asset_collections": len(preserved), "embedded_previews": len(preserved),
        "gallery_instances": gallery_instances, "parts": total, "unique_meshes": len(bpy.data.meshes),
        "hidden_parts": hidden, "triangles_including_hidden_instances": triangles,
        "max_source_vertex_error_tile_units": max_error,
        "parts_with_source_uv0": uv_parts, "source_uv_face_corners_checked": uv_loops, "max_source_uv_error": max_uv_error,
        "checked": ["all transformed vertices", "face order and winding", "UV_0 presence and per-corner coordinates", "material slots", "source visibility",
                    "relative parts", "asset mark", "catalog ID", "embedded preview dimensions", "gallery instance count"]
    }
    # Exercise the artist's normal Append > Collection entry in a blank file.
    bpy.ops.wm.read_factory_settings(use_empty=True)
    with bpy.data.libraries.load(str(output / LIBRARY), link=False, assets_only=True) as (available, selected):
        if set(available.collections) != set(preserved):
            raise ValueError("Append menu does not expose exactly the recorded elements")
        selected.collections = sorted(preserved)
    for col in selected.collections:
        bpy.context.scene.collection.children.link(col)
    if len(bpy.context.scene.objects) != total:
        raise ValueError("Appended collections lost or duplicated a mesh part")
    if any(obj.library or obj.data.library for obj in bpy.context.scene.objects):
        raise ValueError("Appended collection did not become locally editable")
    report["appended_collections_in_fresh_file"] = len(selected.collections)
    report["checked"].append("all collections append as local editable meshes")
    (output / "blender-verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print("VERIFIED", json.dumps({k: report[k] for k in ["asset_collections", "parts", "unique_meshes", "max_source_vertex_error_tile_units"]}))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--verify", action="store_true", help="Reopen the written .blend and compare each part")
    a = p.parse_args(sys.argv[sys.argv.index("--") + 1:])
    manifest, output = a.manifest.resolve(), a.output_dir.resolve()
    data = json.loads(manifest.read_text())
    if data.get("schema_version") != 1 or data.get("axes") != "Bevy Y-up":
        raise ValueError("Unsupported coordinate system or capture schema")
    output.mkdir(exist_ok=True, parents=True)
    if not a.verify:
        build(data, output)
    verify(data, manifest, output)


if __name__ == "__main__":
    main()
