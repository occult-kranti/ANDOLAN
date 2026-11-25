"""Assemble a local editable waystation from two adjacent Blender collection libraries.

Place both input libraries under the output folder as YUGA/yuga-world-elements.blend
and Rust/rust-fallback-study.blend. Run in Blender with -- --folder /path/to/kit.
Append --verify to check the saved scene from a second empty folder.
"""
import argparse
from collections import Counter
from hashlib import file_digest
import json
from math import radians
from pathlib import Path
import shutil
import sys
from tempfile import TemporaryDirectory

import bpy
from mathutils import Vector


LIBRARIES = {"Rust": Path("Rust/rust-fallback-study.blend"),
             "YUGA": Path("YUGA/yuga-world-elements.blend")}
SOURCES = {
    "Rust": ["field_lawn_light", "field_path", "field_water_wave", "house", "sign", "fence", "table", "plant"],
    "YUGA": ["Surface tile", "Lanka Watchtower", "Mangrove Roots", "Lotus Cluster", "Reed Cluster",
             "Transit Lantern", "YUGA Symbol arrow-right"],
}


def section(name):
    collection = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(collection)
    return collection


def place(collection, dest, label, xyz, scale=(1, 1, 1), angle=0):
    obj = bpy.data.objects.new(label, None)
    obj.instance_type = "COLLECTION"
    obj.instance_collection = collection
    obj.empty_display_type = "PLAIN_AXES"
    obj.empty_display_size = .2
    obj.location, obj.scale = xyz, scale
    obj.rotation_euler.z = radians(angle)
    dest.objects.link(obj)
    return obj


def light_and_camera(scene):
    world = bpy.data.worlds.new("Late afternoon sky")
    world.use_nodes = True
    background = world.node_tree.nodes["Background"]
    background.inputs["Color"].default_value = (.78, .85, 1., 1.)
    background.inputs["Strength"].default_value = .60
    scene.world = world
    studio = section("Camera and daylight")
    sun = bpy.data.lights.new("Afternoon sun", "SUN")
    sun.energy = 3.1
    sun.angle = radians(10)
    sun.color = (1., .87, .68)
    obj = bpy.data.objects.new(sun.name, sun)
    studio.objects.link(obj)
    obj.rotation_euler = Vector((.44, .62, -1)).to_track_quat("-Z", "Y").to_euler()
    target = Vector((0, .15, 1.15))
    camera = bpy.data.cameras.new("Waystation camera")
    camera.type = "ORTHO"
    camera.ortho_scale = 18
    camera.lens = 48
    eye = bpy.data.objects.new(camera.name, camera)
    studio.objects.link(eye)
    eye.location = target + Vector((11, -18, 11.8))
    eye.rotation_euler = (target - eye.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = eye
    for area in bpy.context.screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_perspective = "CAMERA"
            area.spaces.active.overlay.show_overlays = False
            area.spaces.active.shading.color_type = "MATERIAL"


def build(folder):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    libraries = {}
    for source, path in LIBRARIES.items():
        names = SOURCES[source]
        with bpy.data.libraries.load(str(folder / path), link=True, assets_only=True) as (available, wanted):
            if not set(names) <= set(available.collections):
                raise ValueError(f"Missing collections in {path}: {set(names) - set(available.collections)}")
            wanted.collections = names.copy()
        libraries[source] = {c.name: c for c in wanted.collections}
    rust, yuga = libraries["Rust"], libraries["YUGA"]
    ground = section("Road and riverbank")
    station = section("Waystation")
    waterside = section("Waterside")
    place(yuga["Surface tile"], ground, "Background ground", (0, 0, -.66), (200, 200, 1))
    # One grid of abutting reusable field tiles forms the island and through road.
    for row, y in enumerate((-3.3, -1.1, 1.1, 3.3)):
        for column, x in enumerate((-5.5, -3.3, -1.1, 1.1, 3.3, 5.5)):
            asset = "field_lawn_light"
            if row == 1:
                asset = "field_path"
            if row == 0 and column >= 3:
                asset = "field_water_wave"
            place(rust[asset], ground, f"{asset} · {column+1}-{row+1}", (x, y, 0), (2.2, 2.2, 1.18))
    # The source house front is -Y. Its original fixture anchor is off centre.
    place(rust["house"], station, "Lane house", (-4.94, 3.54, .009))
    place(rust["plant"], station, "House planter", (-3.96, .43, .009), (.66, .66, .66))
    place(rust["table"], station, "Caretaker table", (-1.08, .39, .009), (.72, .72, .74), -12)
    place(yuga["Transit Lantern"], station, "Table lantern", (-.91, .48, .779), (.34, .30, .54))
    place(rust["sign"], station, "Wayfinding board", (-1.83, -2.55, .009), (1.64, 1.64, 1.64), 207)
    place(yuga["YUGA Symbol arrow-right"], station, "Route arrow on board", (-1.762, -2.685, 1.345),
          (.95, .95, .95), 27)
    for x in (-5.38, -3.89):
        place(rust["fence"], station, "Roadside fence", (x, -2.51, .009), (.75, .75, .75))
    place(yuga["Lanka Watchtower"], station, "Gate pavilion", (1.87, 1.65, .009), (3.3, 3.0, 3.98))
    place(yuga["Mangrove Roots"], waterside, "Canopy tree", (5.10, 1.82, .009), (2.9, 3.0, 4.45))
    for x, y, a in ((1.05, -3.7, 17), (3.47, -3.24, -31), (4.89, -3.60, 35)):
        place(yuga["Lotus Cluster"], waterside, "Lotus patch", (x, y, .035), (1.10, .92, .23), a)
    for x, y, a in ((.22, -2.73, -12), (5.82, -2.51, 19)):
        place(yuga["Reed Cluster"], waterside, "Reeds", (x, y, .029), (.56, .52, .89), a)
    light_and_camera(scene)
    scene.render.engine = "CYCLES"
    scene.cycles.device = "CPU"
    scene.cycles.samples = 64
    scene.cycles.use_denoising = False
    scene.render.resolution_x = 1232
    scene.render.resolution_y = 812
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "JPEG"
    scene.render.image_settings.quality = 94
    scene.render.filepath = "//waystation.jpg"
    scene.view_settings.view_transform = "AgX"
    bpy.context.preferences.filepaths.save_version = 0
    # The first save establishes the root directory; then store ordinary Blender
    # relative links so the folder can be copied, unzipped or moved as a unit.
    output = str(folder / "waystation.blend")
    bpy.ops.wm.save_as_mainfile(filepath=output, compress=True)
    for library in bpy.data.libraries:
        library.filepath = bpy.path.relpath(library.filepath)
    bpy.ops.wm.save_as_mainfile(filepath=output, compress=True)
    bpy.ops.render.render(write_still=True)


def digest(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def verify(folder):
    with TemporaryDirectory(prefix="yuga-waystation-reopen-") as tmp:
        root = Path(tmp)
        for path in [Path("waystation.blend"), *LIBRARIES.values()]:
            (root / path).parent.mkdir(exist_ok=True)
            shutil.copyfile(folder / path, root / path)
        bpy.ops.wm.open_mainfile(filepath=str(root / "waystation.blend"), load_ui=False)
        expected = {"//" + p.as_posix() for p in LIBRARIES.values()}
        if {lib.filepath for lib in bpy.data.libraries} != expected:
            raise ValueError("Library links are missing or not relative")
        if any(lib.is_missing for lib in bpy.data.libraries) or any(not m.library for m in bpy.data.meshes):
            raise ValueError("Unresolved library or unexpected local mesh")
        scene = bpy.context.scene
        placements = Counter()
        graph = bpy.context.evaluated_depsgraph_get()
        actual = Counter(i.parent.original.name for i in graph.object_instances if i.is_instance and i.object.type == "MESH")
        for o in scene.objects:
            c = o.instance_collection
            if c:
                if c.is_missing or not c.asset_data or actual[o.name] == 0:
                    raise ValueError("Missing instance geometry: " + o.name)
                placements[(Path(c.library.filepath).parent.name, c.name)] += 1
        for library, names in SOURCES.items():
            if set(names) != {name for key,name in placements if key == library}:
                raise ValueError(f"Source collection coverage differs for {library}")
        report = {"blender": bpy.app.version_string, "blend_sha256": digest(folder / "waystation.blend"),
                  "render_sha256": digest(folder / "waystation.jpg"),
                  "source_libraries": {p.as_posix(): digest(folder / p) for p in LIBRARIES.values()},
                  "sources": [{"library": lib, "asset": asset, "placements": n}
                              for (lib, asset), n in sorted(placements.items())],
                  "placements": sum(placements.values()), "distinct_source_collections": len(placements),
                  "evaluated_mesh_instances": sum(actual.values()), "all_links_verified_after_relocation": True}
        (folder / "waystation-verification.json").write_text(json.dumps(report, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, required=True)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    (verify if args.verify else build)(args.folder.resolve())
