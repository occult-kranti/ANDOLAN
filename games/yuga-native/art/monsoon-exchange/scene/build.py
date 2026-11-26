"""Build Monsoon Exchange from the registered survey, original Blender kit and generated cloth.

blender -b -t 3 --python-exit-code 1 --python build.py [-- --output /tmp/rebuild]
"""

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile
import bpy
import _cycles
from mathutils import Vector

HERE = Path(__file__).resolve().parent
DISTRICT = HERE.parent
PLAN = DISTRICT / "plan"
STUDIO = DISTRICT.parent / "mandala-map-studio"
MODELS = STUDIO / "models"
sys.path[:0] = [str(HERE), str(STUDIO / "src")]
from meshkit import Batch, COLL, MATERIALS, blockprint, groups, materials, obj
from architecture import course, ring
from district import (
    boundaries,
    city,
    central_gate,
    corridor_chapters,
    landmark_cistern,
    landmark_sun,
    north_archive,
)
from surfaces import paint

FLOOR = "01 · Walkable survey"
WALL = "02 · Perimeter walls"
COVER = "03 · Cover"
ARCH = "04 · Landmark architecture"
TOWN = "05 · Urban fabric"
DETAIL = "06 · Inlays and objects"
BASE = "07 · District foundation"
GUIDES = "08 · Gameplay volumes (hidden)"
CAMERA = "09 · Registered cameras"
STAGE = "10 · Studio lighting"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def read(p):
    return json.loads(p.read_bytes())


def floorwork(geom, sur):
    tones = {
        "clay": "buff",
        "chalk": "buff",
        "jade": "jade",
        "basalt": "slate",
        "sunstone": "sunstone",
    }
    for row in geom["floors"]:
        vs = row["vertices"]
        owner = row["owner"]
        p = Batch()
        p.solid(vs, [(0, 1, 2, 3)], tones[row["material"]])
        p.finish(
            "Floor." + row["id"],
            FLOOR,
            "floor",
            owner,
            patch_id=row["id"],
            surface_id=row["material"],
        )
        s = Batch()
        n = len(vs)
        below = [(x, y, -3.10) for x, y, z in vs]
        s.solid(
            below + vs,
            [(i, (i + 1) % n, n + (i + 1) % n, n + i) for i in range(n)],
            "brick-dark",
        )
        s.finish("Foundation." + row["id"], BASE, "art", owner)
    bounds = sur["bounds"]
    r = next(v for v in sur["rooms"] if v["id"] == "b")
    west = r["center"][0] - r["size"][0] / 2
    cy = r["center"][1]
    x0, y0, x1, y1 = bounds
    x0 -= 12
    x1 += 8
    y0 -= 3
    y1 += 6
    p = Batch()
    p.box((x0 + x1) / 2, (y0 + y1) / 2, -6.55, x1 - x0, y1 - y0, 0.9, "basalt")

    def fill(ax, ay, bx, by):
        p.box((ax + bx) / 2, (ay + by) / 2, -5.66, bx - ax, by - ay, 3.52, "brick-dark")
        p.solid(
            [(ax, ay, -2.135), (bx, ay, -2.135), (bx, by, -2.135), (ax, by, -2.135)],
            [(0, 1, 2, 3)],
            "earth",
        )

    # Leave an actual bowl in the ground for the external stepwell.
    fill(west - 0.05, y0, x1, y1)
    fill(x0, y0, west - 0.05, cy - 11.6)
    fill(x0, cy + 11.6, west - 0.05, y1)
    p.finish(
        "Terrain · cutaway and stepped basin excavation", BASE, "background", "terrain"
    )
    for room in sur["rooms"]:
        u, v = room["center"]
        w, d = room["size"]
        z = room["z"]
        p = Batch((u, v, z + 0.012))
        clr = (
            "gold"
            if room["id"] == "a"
            else "patina"
            if room["id"] in ("b", "dyers", "sluice")
            else "sand"
        )
        cut = 0.56
        for s in (-1, 1):
            p.box(0, s * (d / 2 - cut), 0, w - 2 * cut, 0.075, 0.012, clr)
            p.box(s * (w / 2 - cut), 0, 0, 0.075, d - 2 * cut, 0.012, clr)
        p.finish("Paving register · " + room["name"], DETAIL, "marker", room["id"])
    for site in sur["objectives"]:
        x, y, z = site["center"]
        r = site["radius"]
        p = Batch((x, y, z + 0.020))
        tone = "gold" if site["room"] == "a" else "patina"
        p.lathe(
            0,
            0,
            0,
            [(r, 0.003), (r, 0.009)],
            "jade" if site["room"] == "a" else "slate",
            64,
            0,
            0,
            False,
        )
        for radius, width, m in (
            (r - 0.06, 0.10, "cream"),
            (r - 0.26, 0.06, tone),
            (r * 0.67, 0.05, tone),
            (r * 0.25, 0.085, "ivory"),
        ):
            ring(p, 0, 0, 0.018, radius, width, m, 64)
        for i in range(12):
            a = math.tau * i / 12
            v0 = lambda rr, angle: (rr * math.cos(angle), rr * math.sin(angle), 0.021)
            p.solid(
                [
                    v0(0.96, a),
                    v0(r * 0.61, a + 0.095),
                    v0(r * 0.79, a),
                    v0(r * 0.61, a - 0.095),
                ],
                [(0, 3, 2, 1)],
                tone,
            )
        p.finish(
            "Ritual disc · " + site["id"],
            DETAIL,
            "marker",
            site["room"],
            site_id=site["id"],
            radius_m=r,
        )
    for water in sur["water"]:
        x, y = water["center"]
        w, d = water["size"]
        z = water["z"] + water["depth"]
        p = Batch((x, y, z))
        p.box(0, 0, -0.028, w, d, 0.028, "water")
        for i in range(5):
            p.box(0, (-0.38 + 0.19 * i) * d, 0.002, w * 0.83, 0.030, 0.012, "patina")
        p.finish(
            "Surface." + water["id"],
            DETAIL,
            "water",
            water["room"],
            water_id=water["id"],
            depth_m=water["depth"],
        )


class Kit:
    def __init__(self):
        self.catalog = read(MODELS / "index.json")["models"]
        self.masters = {}
        self.uses = []

    def master(self, name):
        if name in self.masters:
            return self.masters[name]
        record = self.catalog[name]
        src = MODELS / record["file"]
        assert sha(src) == record["sha256"]
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(src), loglevel=0)
        fresh = set(bpy.data.objects) - before
        bpy.context.view_layer.update()
        vs = []
        fs = []
        indices = []
        smooth = []
        mats = []
        for o in sorted(fresh, key=lambda ob: ob.name):
            if o.type != "MESH":
                continue
            base = len(vs)
            data = o.data
            vs.extend(tuple(o.matrix_world @ v.co) for v in data.vertices)
            for face in data.polygons:
                mat = data.materials[face.material_index]
                if mat not in mats:
                    mats.append(mat)
                fs.append(tuple(i + base for i in face.vertices))
                indices.append(mats.index(mat))
                smooth.append(face.use_smooth)
        out = bpy.data.meshes.new("Mandala kit · " + name)
        out.from_pydata(vs, [], fs)
        out.update()
        for m in mats:
            out.materials.append(m)
        for f, mi, sm in zip(out.polygons, indices, smooth):
            f.material_index = mi
            f.use_smooth = sm
        for o in fresh:
            bpy.data.objects.remove(o, do_unlink=True)
        dims = [max(v[i] for v in vs) - min(v[i] for v in vs) for i in range(3)]
        center = [
            (max(v[i] for v in vs) + min(v[i] for v in vs)) * 0.5 for i in range(2)
        ] + [min(v[2] for v in vs)]
        for v in out.vertices:
            v.co -= Vector(center)
        self.masters[name] = (out, dims)
        return self.masters[name]

    def place(self, asset, ident, center, group, role, element, size=None, rotation=0):
        mesh, dims = self.master(asset)
        o = obj(ident, mesh, group, role, element, source_asset=asset)
        o.location = center
        o.rotation_euler.z = rotation
        if size:
            o.scale = tuple(size[i] / dims[i] for i in range(3))
        record = self.catalog[asset]
        self.uses.append(
            {
                "placement_id": ident,
                "element": element,
                "asset": asset,
                "source": "../../mandala-map-studio/models/" + record["file"],
                "source_sha256": record["sha256"],
                "center_base_m": list(center),
                "rotation_z_radians": rotation,
                "scale_xyz": [round(v, 5) for v in o.scale],
            }
        )
        return o


COVER_KIT = {
    "brass": "bell-screen",
    "scale": "weigh-counter",
    "plinth": "stone-lectern",
    "press": "dye-cabinet",
    "canopy": "bell-screen",
    "measure": "weigh-counter",
    "cask": "dye-cabinet",
    "slip": "stone-lectern",
    "spool": "dye-cabinet",
    "shelf": "bank-parapet",
    "stack": "dye-cabinet",
    "drum": "sluice-gearbox",
    "spout": "sluice-gearbox",
    "slab": "bank-parapet",
    "weave": "bell-screen",
    "spindle": "weigh-counter",
    "wheel": "sluice-gearbox",
    "bales": "dye-cabinet",
    "jar": "sluice-gearbox",
    "vault": "stone-lectern",
}


def markers_and_kit(sur, kit):
    for c in sur["covers"]:
        x, y = c["center"]
        w, d, h = c["size"]
        z = c["z"]
        ident = c["id"]
        source = "cover-" + COVER_KIT[ident.rsplit("-", 1)[-1]]
        # Keep the body proportions of reused low counters. A full-height masonry plinth carries them.
        mesh, dimensions = kit.master(source)
        rotate = math.pi / 2 if (dimensions[0] > dimensions[1]) != (w > d) else 0
        bw, bd = (d, w) if rotate else (w, d)
        asset_h = min(
            h - 0.25, dimensions[2] * min(bw / dimensions[0], bd / dimensions[1]) * 1.23
        )
        pedestal = h - asset_h
        p = Batch((x, y, z))
        p.box(
            0,
            0,
            0,
            w,
            d,
            pedestal,
            "brick-dark" if c["room"] in ("a", "copper", "toll") else "basalt",
        )
        p.box(
            0,
            0,
            pedestal * 0.70,
            w * 0.995,
            d * 0.995,
            min(0.10, pedestal * 0.22),
            "sand",
        )
        p.finish("Plinth." + ident, COVER, "cover", c["room"], cover_id=ident)
        o = kit.place(
            source,
            "Furnishing." + ident,
            (x, y, z + pedestal),
            COVER,
            "cover",
            c["room"],
            (bw * 0.985, bd * 0.985, asset_h),
            rotate,
        )
        o["cover_id"] = ident
        o["collider_center_xyz_m"] = [x, y, z + h / 2]
        o["collider_size_m"] = [w, d, h]
        p = Batch((x, y, z))
        p.box(0, 0, 0, w, d, h, "signal")
        proxy = p.finish("COL." + ident, GUIDES, "collision", c["room"], cover_id=ident)
        proxy.display_type = "WIRE"
    for spawn in sur["spawns"]:
        for i, pt in enumerate(spawn["pads"]):
            p = Batch(pt)
            ring(p, 0, 0, 0.028, 0.34, 0.040, "cream", 28)
            p.finish(
                f"Spawn sign.{spawn['id']}.{i + 1}", DETAIL, "marker", spawn["room"]
            )
            o = obj(
                f"SPAWN.{spawn['id']}.{i + 1}",
                None,
                GUIDES,
                "spawn",
                spawn["room"],
                seat=i + 1,
            )
            o.location = pt
            o.empty_display_size = 0.60
    for site in sur["objectives"]:
        x, y, z = site["center"]
        p = Batch((x, y, z))
        p.lathe(0, 0, 0, [(site["radius"], 0), (site["radius"], 0.35)], "signal", 48)
        vol = p.finish(
            "TRIGGER." + site["id"],
            GUIDES,
            "trigger",
            site["room"],
            radius_m=site["radius"],
        )
        vol.display_type = "WIRE"
    # Display original ritual pieces and trade instruments on exterior workbenches.
    for asset, ident, room, center, turn in [
        (
            "artifact-weighbeam",
            "District scale beam",
            "scales",
            (7.9, -27, 0),
            math.pi / 2,
        ),
        (
            "artifact-bell-comb",
            "Indigo gallery bell rack",
            "b",
            (-52.0, 30.7, -1.05),
            math.pi / 2,
        ),
        (
            "rite-ember-vessel",
            "Caravan porter’s ember pot",
            "atk",
            (-7, -56.74, 1.03),
            0,
        ),
        ("rite-water-ewer", "Archive keeper’s ewer", "def", (7, 57.78, 2.24), 0),
    ]:
        if asset.startswith("rite"):
            xp, yp, zp = center
            p = Batch((xp, yp, zp - 1.03))
            course(p, 0, 0, 0, 1.0, 1.14, 1.03, "sand")
            p.finish(ident + " · table", DETAIL, "art", room)
        kit.place(asset, ident, center, DETAIL, "art", room, rotation=turn)
    p = Batch()
    p.lathe(
        0,
        0,
        0,
        [(0.13, 0), (0.16, 0.60), (0.25, 1), (0.21, 1.43), (0.13, 1.53)],
        "paper",
        12,
    )
    p.lathe(
        0, 0, 0, [(0.13, 1.53), (0.15, 1.66), (0.09, 1.79), (0.001, 1.8)], "gold", 16
    )
    guide = p.finish("SCALE · 1.80 m standing figure", GUIDES, "scale", "atk")
    guide.location = (3, -49, 0)
    guide["height_m"] = 1.8
    COLL[GUIDES].hide_render = True
    COLL[GUIDES].hide_viewport = True


def stage(sc):
    def light(name, kind, energy, angle, pos):
        data = bpy.data.lights.new(name, kind)
        o = obj(name, data, STAGE, "studio", "lighting")
        o.location = pos
        data.energy = energy
        if kind == "SUN":
            data.angle = angle
            data.color = (1, 0.844, 0.665)
        o.rotation_euler = (-Vector(pos)).to_track_quat("-Z", "Y").to_euler()
        return o

    light("Late monsoon sun", "SUN", 3.75, 0.105, (-48, -74, 96))
    sc.world = bpy.data.worlds.new("High cloud · dry afternoon")
    world = sc.world
    world.use_nodes = True
    node = world.node_tree.nodes.get("Background")
    node.inputs["Color"].default_value = (0.59, 0.72, 0.87, 1)
    node.inputs["Strength"].default_value = 0.56
    # Keep the calibrated diffuse fill while giving the player-view sky a
    # directional horizon and broken high cloud in the camera plane.
    nodes, links = world.node_tree.nodes, world.node_tree.links
    sky = nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_disc = False
    sky.sun_elevation = math.radians(27)
    sky.sun_rotation = math.radians(226)
    sky.air_density = 1.3
    sky.dust_density = 0.95
    coord = nodes.new("ShaderNodeTexCoord")
    cloud = nodes.new("ShaderNodeTexNoise")
    cloud.inputs["Scale"].default_value = 4.4
    cloud.inputs["Detail"].default_value = 4.2
    cloud.inputs["Roughness"].default_value = 0.64
    links.new(coord.outputs["Generated"], cloud.inputs["Vector"])
    edge = nodes.new("ShaderNodeValToRGB")
    edge.color_ramp.elements[0].position = 0.45
    edge.color_ramp.elements[1].position = 0.70
    edge.color_ramp.elements[1].color = (0.60, 0.60, 0.60, 1)
    links.new(cloud.outputs["Fac"], edge.inputs["Fac"])
    tint = nodes.new("ShaderNodeMixRGB")
    tint.inputs[2].default_value = (2.0, 2.12, 2.25, 1)
    links.new(edge.outputs["Color"], tint.inputs[0])
    links.new(sky.outputs["Color"], tint.inputs[1])
    camera_bg = nodes.new("ShaderNodeBackground")
    camera_bg.inputs["Strength"].default_value = 0.68
    links.new(tint.outputs[0], camera_bg.inputs["Color"])
    visible = nodes.new("ShaderNodeLightPath")
    combine = nodes.new("ShaderNodeMixShader")
    links.new(visible.outputs["Is Camera Ray"], combine.inputs[0])
    links.new(node.outputs[0], combine.inputs[1])
    links.new(camera_bg.outputs[0], combine.inputs[2])
    links.new(combine.outputs[0], nodes.get("World Output").inputs["Surface"])
    # Only the studio floor extends beyond the editable city, to catch a soft silhouette.
    p = Batch()
    p.box(0, 0, -6.75, 2200, 2200, 0.12, "paper")
    p.finish("Studio ground, excluded from GLB", STAGE, "studio", "photography")
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    sc.cycles.samples = 12
    sc.cycles.use_denoising = bool(_cycles.with_openimagedenoise)
    sc.cycles.max_bounces = 4
    sc.cycles.diffuse_bounces = 2
    sc.cycles.glossy_bounces = 2
    sc.cycles.transparent_max_bounces = 2
    sc.render.threads_mode = "FIXED"
    sc.render.threads = 3
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "AgX - Medium High Contrast"
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.film_transparent = False


def cameras(sc, rooms):
    a, b, mid = (rooms[k] for k in ("a", "b", "mid"))
    ax, ay = a["center"]
    bx, by = b["center"]
    mx, my = mid["center"]
    cameras = {
        "overview": {
            "position": [-71, -140, 120],
            "target": [0, 0, 0.80],
            "ortho_scale_m": 180,
        },
        "sun-court": {
            "position": [ax - 5.5, ay - 2.0, a["z"] + 1.60],
            "target": [ax + 16.7, ay + 2.6, a["z"] + 2.77],
            "lens_mm": 26,
        },
        "indigo-cistern": {
            "position": [bx - 13.75, by - 3.2, b["z"] + 1.60],
            "target": [bx - 22.8, by + 2.15, b["z"] - 1.0],
            "lens_mm": 19,
        },
        "weavers-gate": {
            "position": [mx + 1.3, my - 19.4, 1.60],
            "target": [mx + 1.85, my - 4.75, 4.48],
            "lens_mm": 21,
        },
        "north-up": {
            "position": [0, 0, 155],
            "target": [0, 0, 0],
            "ortho_scale_m": 153,
        },
    }
    for key, v in cameras.items():
        name = "CAM." + key
        data = bpy.data.cameras.new(name)
        o = obj(name, data, CAMERA, "camera", key)
        o.location = v["position"]
        o.rotation_euler = (
            (Vector(v["target"]) - o.location).to_track_quat("-Z", "Y").to_euler()
            if key != "north-up"
            else (0, 0, 0)
        )
        if "ortho_scale_m" in v:
            data.type = "ORTHO"
            data.ortho_scale = v["ortho_scale_m"]
        else:
            data.lens = v["lens_mm"]
        data.clip_start = 0.08
        data.clip_end = 600
        sc.timeline_markers.new(key, frame=len(sc.timeline_markers) + 1).camera = o
    sc.camera = bpy.data.objects["CAM.overview"]
    return cameras


def build(output):
    sur = read(PLAN / "survey.json")
    geom = read(PLAN / "geometry.json")
    rooms = {r["id"]: r for r in sur["rooms"]}
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.name = "Monsoon Exchange"
    sc.unit_settings.system = "METRIC"
    sc.unit_settings.scale_length = 1.0
    sc["gameplay"] = "Ember Rite environment study"
    groups(sc, [FLOOR, WALL, COVER, ARCH, TOWN, DETAIL, BASE, GUIDES, CAMERA, STAGE])
    bpy.context.preferences.filepaths.save_version = 0
    with tempfile.TemporaryDirectory() as temp:
        paint(Path(temp))
        materials(Path(temp))
        blockprint(DISTRICT / "concepts/indigo-cloth.png")
    floorwork(geom, sur)
    boundaries(geom, rooms)
    landmark_sun(rooms["a"])
    landmark_cistern(rooms["b"])
    central_gate(rooms)
    north_archive(rooms["def"])
    corridor_chapters(rooms)
    lots = city(geom, rooms)
    kit = Kit()
    markers_and_kit(sur, kit)
    stage(sc)
    cams = cameras(sc, rooms)
    sc.frame_set(1)
    sc.render.resolution_x = 1320
    sc.render.resolution_y = 1040
    for scr in bpy.data.screens:
        for ar in scr.areas:
            if ar.type == "VIEW_3D":
                ar.spaces.active.region_3d.view_distance = 102
                ar.spaces.active.region_3d.view_location = (0, 0, 0)
                ar.spaces.active.region_3d.view_perspective = "CAMERA"
                ar.spaces.active.shading.color_type = "MATERIAL"
                ar.spaces.active.overlay.show_overlays = False
    # Remove temporary source import datablocks; packed texture resources remain referenced.
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    blend = output / "monsoon-exchange.blend"
    glb = output / "monsoon-exchange.glb"
    bpy.ops.object.select_all(action="DESELECT")
    bpy.context.view_layer.objects.active = None
    bpy.ops.wm.save_as_mainfile(filepath=str(blend), compress=True)
    visible = [
        o
        for o in sc.objects
        if o.users_collection
        and o.users_collection[0] not in (COLL[GUIDES], COLL[STAGE])
    ]
    for o in visible:
        o.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=str(glb),
        export_format="GLB",
        use_selection=True,
        export_extras=True,
        export_cameras=True,
        export_lights=False,
        export_animations=False,
        export_yup=True,
        export_texcoords=True,
        export_materials="EXPORT",
        export_image_format="AUTO",
        export_attributes=False,
    )
    printmat = MATERIALS["exchange-print"]
    textiles = []
    for o in visible:
        if o.type == "MESH" and printmat in list(o.data.materials):
            idx = list(o.data.materials).index(printmat)
            polys = [f for f in o.data.polygons if f.material_index == idx]
            uv = o.data.uv_layers.active
            coords = [uv.data[i].uv[:] for f in polys for i in f.loop_indices]
            textiles.append(
                {
                    "object": o.name,
                    "element": o["element"],
                    "polygons": len(polys),
                    "uv_bounds": [
                        [round(min(x[k] for x in coords), 4) for k in (0, 1)],
                        [round(max(x[k] for x in coords), 4) for k in (0, 1)],
                    ],
                }
            )
    assert len(textiles) >= 3
    report = {
        "id": sur["id"],
        "blender_version": bpy.app.version_string,
        "coordinates": "Blender east/north/up metres; glTF east/up/south metres",
        "survey_sha256": sha(PLAN / "survey.json"),
        "geometry_sha256": sha(PLAN / "geometry.json"),
        "floors": len(geom["floors"]),
        "wall_segments": len(geom["walls"]),
        "covered_objects": len(sur["covers"]),
        "residual_city_blocks": lots,
        "site_radius_m": sur["rules"]["kindle_radius_m"],
        "team_pads": sum(len(s["pads"]) for s in sur["spawns"]),
        "cameras": cams,
        "original_kit_placements": kit.uses,
        "cloth": {
            "source": "../concepts/indigo-cloth.png",
            "sha256": sha(DISTRICT / "concepts/indigo-cloth.png"),
            "repeat_m": 1.75,
            "placements": textiles,
        },
        "packed_images": sorted(im.name for im in bpy.data.images if im.packed_file),
        "export_objects_by_role": dict(Counter(o.get("role") for o in visible)),
        "files": {
            f.name: {"bytes": f.stat().st_size, "sha256": sha(f)} for f in (blend, glb)
        },
    }
    (output / "scene-register.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    )
    print("EXCHANGE BUILT", json.dumps(report["files"]), flush=True)


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--output", type=Path, default=HERE)
    args = cli.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    build(args.output.resolve())
