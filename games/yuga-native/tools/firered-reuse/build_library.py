"""Build the editable YUGA world library, Blender catalogs and rendered previews."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import uuid

import bpy
from mathutils import Euler, Vector

NATIVE = Path(__file__).resolve().parents[2]
LIBRARY = NATIVE / "art/reuse-library"
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(LIBRARY / "symbols"))
from foundations import build_foundations
from symbols import build_symbols

GROUPS = ("Architecture", "Nature", "Foundations", "Symbols")
CATALOGS = {g: str(uuid.uuid5(uuid.NAMESPACE_URL, f"https://github.com/occult-kranti/ANDOLAN/YUGA/{g}")) for g in GROUPS}
# Y-up game dimensions become X width, Y depth and Z height in Blender.
def game_scale(node, props):
    matches = [p for p in props if p.get("preset") == node and "scale" in p]
    if not matches:
        return (1., 1., 1.)
    x, y, z = matches[0]["scale"]
    return (x, z, y)


def digest(path):
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def add_donors(group, records, props):
    name = group.lower()
    donor = NATIVE / "assets/world" / (name + ".glb")
    original = json.loads((NATIVE / "art/world" / (name + "-manifest.json")).read_text())
    sha = digest(donor)
    if sha != original["asset_sha256"]:
        raise ValueError(f"Unexpected {name} donor identity")
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(donor))
    objects = {o.name: o for o in set(bpy.data.objects) - before}
    expected = {p["node"] for p in original["presets"]}
    if set(objects) != expected:
        raise ValueError(f"{name} import differs from its source manifest")
    for preset in original["presets"]:
        node = preset["node"]
        obj = objects[node]
        col = bpy.data.collections.new(node.replace("_", " ").title())
        for parent in list(obj.users_collection):
            parent.objects.unlink(obj)
        col.objects.link(obj)
        records.append((col, {"id": node, "category": group, "source_node": node,
                             "source": str(donor.relative_to(NATIVE)), "source_sha256": sha,
                             "display_scale_xyz": game_scale(node, props)}))


def build_index():
    props = json.loads((NATIVE / "assets/world/confluence-map.json").read_text())["props"]
    records = []
    add_donors("Architecture", records, props)
    add_donors("Nature", records, props)
    for ident, col in build_foundations().items():
        records.append((col, {"id": ident, "category": "Foundations", "source": "tools/firered-reuse/foundations.py",
                              "display_scale_xyz": (1., 1., 1.)}))
    font = json.loads((LIBRARY / "symbols/manifest.json").read_text())["source_font"]
    for ident, col in build_symbols().items():
        records.append((col, {"id": ident, "category": "Symbols", "source": "art/reuse-library/symbols/" + font["file"],
                              "source_sha256": font["sha256"], "codepoint": col["source_codepoint"],
                              "display_scale_xyz": (1., 1., 1.)}))
    for col, row in records:
        col.asset_mark()
        col["yuga_id"] = row["id"]
        col["yuga_category"] = row["category"]
        col.asset_data.catalog_id = CATALOGS[row["category"]]
        col.asset_data.author = "YUGA"
        col.asset_data.description = {
            "Architecture": "Original Confluence architecture. Scale the instance to its intended footprint.",
            "Nature": "Original Confluence nature or lighting prop. Place by its base anchor.",
            "Symbols": "Editable sign mesh from DejaVu Sans Bold. Local front faces -Y; illustrated in bronze.",
            "Foundations": "Editable stock form corresponding to a primitive used by the FireRed Rust renderer."
        }[row["category"]]
        col.asset_data.tags.new(row["category"])
        col.asset_data.tags.new("YUGA")
    return records


def instance(collection, parent):
    inst = bpy.data.objects.new(collection.name, None)
    inst.instance_type = "COLLECTION"
    inst.instance_collection = collection
    inst.empty_display_size = .18
    parent.objects.link(inst)
    return inst


def fitted(collection, scale):
    corners = [o.matrix_world @ Vector(v) for o in collection.all_objects if o.type == 'MESH' for v in o.bound_box]
    if not corners:
        raise ValueError(f"{collection.name} has no bounds")
    transformed = [tuple(v[i] * scale[i] for i in range(3)) for v in corners]
    low = Vector([min(v[i] for v in transformed) for i in range(3)])
    high = Vector([max(v[i] for v in transformed) for i in range(3)])
    factor = 1.0 / max(high - low)
    return Vector(scale) * factor, (low + high) * .5 * factor


def setup_camera(scene):
    def point(obj, target):
        obj.rotation_euler = (target - obj.location).to_track_quat("-Z", "Y").to_euler()
    target = Vector((0., 0., 0.))
    for label, xyz, energy, color in [
        ("Key", (-2.8, -3.6, 4.8), 385., (1., .89, .75)),
        ("Fill", (3.2, -1.7, 2.0), 185., (.76, .86, 1.)),
        ("Rim", (1.1, 2.4, 3.1), 300., (1., .89, .71)),
    ]:
        lamp = bpy.data.lights.new(label, 'AREA')
        lamp.energy, lamp.color, lamp.shape, lamp.size = energy, color, 'DISK', 3.2
        obj = bpy.data.objects.new(label, lamp)
        scene.collection.objects.link(obj)
        obj.location = xyz
        point(obj, target)
    data = bpy.data.cameras.new("Preview camera")
    data.type = "ORTHO"
    camera = bpy.data.objects.new("Preview camera", data)
    scene.collection.objects.link(camera)
    scene.camera = camera
    scene.world = bpy.data.worlds.new("Preview light")
    scene.world.color = (.20, .20, .20)
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 12
    scene.cycles.use_denoising = False
    scene.render.film_transparent = True
    scene.render.resolution_x = scene.render.resolution_y = 208
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGBA'
    return camera


def render_previews(records, thumb_dir):
    thumb_dir.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes.new("Asset preview studio")
    camera = setup_camera(scene)
    for col, row in records:
        ident = row["id"]
        inst = instance(col, scene.collection)
        inst.scale, center = fitted(col, row["display_scale_xyz"])
        inst.location = -center
        camera.location = (0.6, -5.5, 1.0) if row["category"] == "Symbols" else (3.3, -5.2, 3.15)
        camera.rotation_euler = (-camera.location).to_track_quat("-Z", "Y").to_euler()
        camera.data.ortho_scale = 1.62 if row["category"] == "Architecture" else 1.49
        path = thumb_dir / (ident + ".png")
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        with bpy.context.temp_override(id=col):
            bpy.ops.ed.lib_id_load_custom_preview(filepath=str(path))
        if col.preview is None or not col.preview.image_size[0]:
            raise RuntimeError(f"No asset preview for {ident}")
        bpy.data.objects.remove(inst, do_unlink=True)
    for obj in list(scene.collection.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.scenes.remove(scene)


def layout(records):
    scene = bpy.context.scene
    scene.name = "YUGA asset shelf"
    y = 0.
    for group in GROUPS:
        gallery = bpy.data.collections.new(group + " · linked display")
        scene.collection.children.link(gallery)
        assets = [(col, row) for col, row in records if row["category"] == group]
        for i,(col,row) in enumerate(assets):
            obj = instance(col, gallery)
            scale, center = fitted(col, row["display_scale_xyz"])
            obj.scale = scale
            obj.location = Vector(((i % 8 - 3.5)*1.7, y - (i//8)*1.8, .55)) - center
        y -= math.ceil(len(assets) / 8) * 1.8 + 1.0
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'VIEW_3D':
                sp = area.spaces.active
                sp.overlay.show_floor = False
                sp.overlay.show_extras = False
                sp.shading.color_type = 'MATERIAL'
                sp.region_3d.view_rotation = Euler((math.radians(43), 0, 0)).to_quaternion()
                sp.region_3d.view_perspective = 'ORTHO'
                sp.region_3d.view_location = (0, (y + 1.)*.5 + .5, .5)
                sp.region_3d.view_distance = 19.0
    bpy.ops.object.select_all(action='DESELECT')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--thumbnails", type=Path, required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = args.output_dir.resolve()
    out.mkdir(exist_ok=True, parents=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    records = build_index()
    if len({r["id"] for _,r in records}) != len(records):
        raise ValueError("Duplicate asset identifiers")
    bpy.context.view_layer.update()
    render_previews(records, args.thumbnails.resolve())
    layout(records)
    bpy.ops.file.pack_all()
    bpy.data.orphans_purge(do_recursive=True)
    bpy.context.preferences.filepaths.save_version = 0
    dst = out / "yuga-world-elements.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(dst), compress=True)
    catalog = {"schema": 1, "library": dst.name, "blender": bpy.app.version_string,
               "library_sha256": digest(dst), "assets": [row for _,row in records]}
    (out/"catalog.json").write_text(json.dumps(catalog, indent=2)+"\n")
    (out/"blender_assets.cats.txt").write_text("VERSION 1\n"+"".join(
        f"{CATALOGS[group]}:{group}:{group}\n" for group in GROUPS))
    print(f"Exported {len(records)} marked collections to {dst}")


if __name__ == "__main__":
    main()
