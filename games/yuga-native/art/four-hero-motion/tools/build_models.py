"""Build the two new art-study GLBs from the project's licensed anatomy and costume tools.

blender -b -t 1 --python-exit-code 1 -P tools/build_models.py -- shiva krishna
"""

import argparse
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

PACK = Path(__file__).resolve().parents[1]
ART = PACK.parents[2] / "yuga" / "art"
sys.path.insert(0, str(ART / "pipeline"))
sys.path.insert(0, str(Path(__file__).parent))
from anatomy import build_anatomy
from build_heroes import material
from geometry import Sculpt, costume, face_and_hair
from preview_actions import author

TAU = math.tau
CONFIG = {
    "shiva": dict(
        height=1.92,
        width=1.11,
        face_width=1.045,
        skin=(0.18, 0.287, 0.37),
        cloth=(0.055, 0.050, 0.085),
        silk=(0.52, 0.225, 0.067),
        gem=(0.27, 0.51, 0.59),
        hair="knot",
    ),
    "krishna": dict(
        height=1.79,
        width=0.966,
        face_width=0.96,
        skin=(0.047, 0.155, 0.325),
        cloth=(0.023, 0.22, 0.24),
        silk=(0.89, 0.51, 0.046),
        gem=(0.018, 0.48, 0.54),
        hair="long",
    ),
}


def fabric(name, color, ink):
    mat = material(name, color, rough=0.69)
    yy, xx = np.mgrid[:256, :256]
    u, v = xx / 256.0, yy / 256.0
    diamond = abs(abs(u - 0.5) + 0.83 * abs(v - 0.5) - 0.337) < 0.007
    ellipse = ((u - 0.5) / 0.113) ** 2 + ((v - 0.5) / 0.177) ** 2
    pattern = diamond | (abs(ellipse - 1.0) < 0.09)
    weave = 0.89 + 0.045 * np.cos(xx * math.pi) + 0.045 * np.cos(yy * math.pi / 2)
    rgb = np.where(pattern[:, :, None], ink, color) * weave[:, :, None]
    rgba = np.concatenate([rgb, np.ones((256, 256, 1))], axis=2).astype(np.float32)
    img = bpy.data.images.new(name + " • woven repeat", width=256, height=256)
    img.pixels.foreach_set(rgba.ravel())
    img.pack()
    tree = mat.node_tree
    coord = tree.nodes.new("ShaderNodeTexCoord")
    tex = tree.nodes.new("ShaderNodeTexImage")
    tex.image = img
    tree.links.new(
        tex.outputs["Color"], tree.nodes["Principled BSDF"].inputs["Base Color"]
    )
    # Tiling is baked into mesh UVs to preserve the texture scale in glTF readers.
    tree.links.new(coord.outputs["UV"], tex.inputs["Vector"])
    return mat


def palette(c):
    mats = {
        "skin": material("Living mineral blue", c["skin"], rough=0.52),
        "cloth": fabric("Figured shoulder silk", c["cloth"], (0.53, 0.30, 0.081)),
        "ivory": fabric("Handwoven lower garment", c["silk"], (0.74, 0.51, 0.20)),
        "gold": material(
            "Brushed bell metal", (0.65, 0.32, 0.062), metal=0.78, rough=0.30
        ),
        "silver": material(
            "Worked moon silver", (0.69, 0.76, 0.78), metal=0.60, rough=0.26
        ),
        "gem": material("Polished inlay", c["gem"], metal=0.29, rough=0.18),
        "hair": material("Indigo black hair", (0.015, 0.012, 0.021), rough=0.51),
        "locks": material("Warm lock ridges", (0.042, 0.024, 0.028), rough=0.56),
        "eyes": material("Warm sclera", (0.76, 0.69, 0.57), rough=0.24),
        "iris": material("Dark amber iris", (0.12, 0.062, 0.023), rough=0.23),
        "lips": material("Muted lip vermilion", (0.23, 0.087, 0.083), rough=0.48),
        "ash": material("Sandalwood and ash", (0.84, 0.76, 0.56), rough=0.8),
        "wood": material("Burnished wood", (0.21, 0.077, 0.022), rough=0.45),
        "bead": material("Rudraksha seed", (0.16, 0.052, 0.021), rough=0.72),
        "quill": material(
            "Peacock viridian", (0.023, 0.34, 0.23), metal=0.28, rough=0.27
        ),
        "cobalt": material(
            "Peacock ocellus", (0.017, 0.082, 0.364), metal=0.43, rough=0.21
        ),
    }
    return mats


def face_paint(s, c, m, hero):
    h = c["height"]

    def on_face(x, z):
        hit, pos, _, _ = s.body.ray_cast(Vector((x, -1, z)), Vector((0, 1, 0)))
        return (x, pos.y - 0.0025 if hit else -0.15, z)

    if hero == "shiva":
        for row in range(3):
            s.tube(
                "Tripundra ash line",
                [
                    on_face(
                        (j / 16 - 0.5) * 0.067,
                        h * 0.947 + row * 0.008 + 0.002 * math.sin(j * math.pi / 16),
                    )
                    for j in range(17)
                ],
                0.0024,
                m["ash"],
                "head",
            )
        s.ellipsoid(
            "Forehead copper bindu",
            on_face(0, h * 0.957),
            (0.004, 0.0028, 0.009),
            m["lips"],
            "head",
        )
    else:
        for sign in (-1, 1):
            s.tube(
                "Vaishnava tilaka",
                [
                    on_face(
                        sign * (0.003 + 0.008 * (j / 12) ** 0.75),
                        h * 0.941 + 0.041 * j / 12,
                    )
                    for j in range(13)
                ],
                0.0021,
                m["ash"],
                "head",
            )


def palm(s, side):
    bone = s.rig.data.bones["wrist." + side]
    basis = bone.matrix_local.to_3x3()
    offset = 0.025 if side == "R" else -0.025

    def point(ax, forward, radial):
        return bone.head_local + basis @ Vector((ax, 0.105 + forward, offset + radial))

    return point


def drum(s, p, m, bone):
    z = 0.48

    # The drum crosses the trident shaft. Narrow waist, two broad membranes.
    def shell(u, v):
        rad = 0.023 + 0.035 * abs(2 * v - 1) ** 0.8
        return p(
            z + rad * math.cos(TAU * u), 0.111 * (v - 0.5), rad * math.sin(TAU * u)
        )

    s.cloth(
        "Damaru • hourglass body",
        shell,
        m["wood"],
        rows=12,
        columns=32,
        wrap=True,
        bone=bone,
    )
    for side in (0, 1):
        s.tube(
            "Damaru • hide lacing ring",
            [shell(j / 32, side) for j in range(33)],
            0.004,
            m["ash"],
            bone,
        )
        s.mesh(
            "Damaru • goatskin membrane",
            [p(z, 0.111 * (side - 0.5), 0)] + [shell(j / 32, side) for j in range(32)],
            [(0, 1 + j, 1 + (j + 1) % 32) for j in range(32)],
            m["ash"],
            bone,
        )
    for j in range(10):
        s.tube(
            "Damaru • cross lacing",
            [shell(j / 10, 0), shell((j + 0.5) / 10, 0.5), shell((j + 1) / 10, 1)],
            0.0016,
            m["ash"],
            bone,
        )
    s.tube(
        "Damaru • bead cord",
        [p(z, -0.014, 0.008), p(z - 0.065, -0.03, 0.032), p(z - 0.103, -0.034, 0.021)],
        0.0025,
        m["lips"],
        bone,
    )
    s.ellipsoid(
        "Damaru • striker",
        p(z - 0.103, -0.034, 0.021),
        (0.009,) * 3,
        m["bead"],
        bone,
        10,
        8,
    )


def shiva_details(s, c, m):
    h = c["height"]
    # Coiled jata with distinct changes in diameter and a narrow silver crescent.
    for j in range(13):
        a = TAU * j / 13
        pts = []
        for i in range(33):
            t = i / 32
            r = 0.043 + 0.045 * math.sin(math.pi * t) ** 0.7
            pts.append(
                (
                    r * math.cos(a + 5 * t),
                    0.014 + r * math.sin(a + 5 * t),
                    h * 0.995 + 0.127 * t,
                )
            )
        s.tube(
            "Jata • ascending lock",
            pts,
            0.012,
            m["hair" if j % 3 else "locks"],
            "head",
            sides=8,
            taper=lambda t: 1 - 0.5 * t,
        )
    for j in range(10):
        a = math.pi * j / 9
        s.tube(
            "Jata • shoulder lock",
            [
                (
                    0.086 * math.cos(a) + 0.017 * math.sin(9 * t + a),
                    0.033 + 0.082 * math.sin(a) + 0.06 * t,
                    h * 0.977 - 0.34 * t + 0.009 * math.sin(14 * t + a),
                )
                for t in [i / 30 for i in range(31)]
            ],
            0.014,
            m["hair" if j % 2 else "locks"],
            "head",
            taper=lambda t: 1 - 0.8 * t,
        )
    pts = [
        (
            0.071 + 0.046 * math.cos(math.pi * 0.87 + math.pi * 1.17 * j / 40),
            -0.066,
            h * 1.047 + 0.055 * math.sin(math.pi * 0.87 + math.pi * 1.17 * j / 40),
        )
        for j in range(41)
    ]
    s.tube(
        "Chandra • silver crescent",
        pts,
        0.013,
        m["silver"],
        "head",
        sides=12,
        taper=lambda t: 0.02 + 0.98 * math.sin(math.pi * t) ** 0.67,
    )
    for k in range(2):
        for j in range(33 + 6 * k):
            a = TAU * j / (33 + 6 * k)
            x = (0.11 + 0.033 * k) * math.cos(a)
            y = 0.005 + (0.136 + 0.049 * k) * math.sin(a)
            z = h * 0.827 - (0.095 + k * 0.073) * max(0, -math.sin(a)) ** 1.75
            s.ellipsoid(
                "Rudraksha • fluted bead",
                (x, y, z),
                (0.0105, 0.0115, 0.0125),
                m["bead"],
                "spine01",
                12,
                8,
                ridge=0.115,
            )
    p = palm(s, "R")
    bone = "wrist.R"
    s.tube(
        "Trishula • tapering staff",
        [p(z, 0, 0) for z in (-0.80, -0.55, 0, 0.45, 0.62)],
        0.017,
        m["wood"],
        bone,
        sides=14,
        taper=lambda t: 0.75 + 0.25 * t,
    )
    for z in (-0.76, -0.22, -0.16, 0.22, 0.38, 0.55, 0.585):
        s.tube(
            "Trishula • ferrule",
            [
                p(z, 0.0185 * math.cos(TAU * i / 32), 0.0185 * math.sin(TAU * i / 32))
                for i in range(33)
            ],
            0.0037,
            m["gold"],
            bone,
        )
    for side in (-1, 0, 1):
        pts = []
        for j in range(29):
            t = j / 28
            spread = side * (0.103 * math.sin(t * math.pi * 0.74) ** 0.9)
            pts.append(p(0.58 + t * (0.34 if side == 0 else 0.28), 0, spread))
        s.tube(
            (
                "Trishula • forged central blade"
                if side == 0
                else "Trishula • recurved tine"
            ),
            pts,
            0.021,
            m["silver"],
            bone,
            sides=8,
            taper=lambda t: 0.035 + math.sin((t + 0.20) * math.pi / 1.20) ** 0.8,
        )
    drum(s, p, m, bone)


def disk(s, p, m):
    n = 96

    def edge(radius, j):
        a = TAU * j / n
        return p(0.124 + radius * math.cos(a), 0.026, radius * math.sin(a))

    rows = []
    for radius, offset in (
        (0.096, -0.005),
        (0.110, -0.012),
        (0.139, 0),
        (0.110, 0.012),
        (0.096, 0.005),
    ):
        for j in range(n):
            a = TAU * j / n
            r = radius + (0.010 if radius == 0.139 and j % 4 == 0 else 0)
            rows.append(p(0.124 + r * math.cos(a), 0.026 + offset, r * math.sin(a)))
    s.mesh(
        "Sudarshana • beveled solar disc",
        rows,
        [
            (
                i * n + j,
                i * n + (j + 1) % n,
                ((i + 1) % 5) * n + (j + 1) % n,
                ((i + 1) % 5) * n + j,
            )
            for i in range(5)
            for j in range(n)
        ],
        m["gold"],
        "chakra",
    )
    s.tube(
        "Sudarshana • lapis rim",
        [edge(0.105, j) for j in range(n + 1)],
        0.003,
        m["cobalt"],
        "chakra",
        sides=8,
    )


def krishna_details(s, c, m):
    h = c["height"]

    # A single feather with a curved rachis, individual barbs and an inset ocellus.
    def quill(t):
        return Vector(
            (
                0.046 + 0.116 * t + 0.018 * t * t,
                -0.038 + 0.036 * t,
                h * 0.994 + 0.254 * t,
            )
        )

    s.tube(
        "Mayura • feather rachis",
        [quill(i / 32) for i in range(33)],
        0.003,
        m["gold"],
        "head",
        taper=lambda t: 1 - 0.8 * t,
    )
    for i in range(1, 34):
        t = i / 36.0
        wid = 0.041 * math.sin(math.pi * t) ** 0.72 * (0.6 + 0.55 * t)
        for side in (-1, 1):
            base = quill(t)
            end = base + Vector((side * wid, -0.001, 0.026 + 0.01 * t))
            s.tube(
                "Mayura • iridescent barb",
                [base, base.lerp(end, 0.55) + Vector((0, -0.002, 0.006)), end],
                0.0028,
                m["quill" if i % 5 else "gold"],
                "head",
                sides=5,
                taper=lambda u: 1 - 0.78 * u,
            )
    eye = quill(0.72)
    for size, dy, key in (
        (1.0, 0, "gold"),
        (0.80, -0.003, "quill"),
        (0.52, -0.006, "cobalt"),
    ):
        s.ellipsoid(
            "Mayura • feather eye",
            eye + Vector((0, dy, 0)),
            (0.029 * size, 0.004, 0.037 * size),
            m[key],
            "head",
            24,
            12,
        )
    for j in range(17):
        t = j / 16
        x = 0.118 * math.cos(math.pi * t)
        s.ellipsoid(
            "Vanamala • jasmine blossom",
            (
                x,
                -0.139 - 0.054 * math.sin(math.pi * t),
                h * 0.815 - 0.105 * math.sin(math.pi * t),
            ),
            (0.012, 0.009, 0.015),
            m["ash"],
            "spine01",
            10,
            8,
            ridge=0.13,
        )
    p = palm(s, "L")
    s.tube(
        "Bansuri • bamboo body",
        [p(-0.312, 0, 0), p(0.142, 0, 0)],
        0.012,
        m["wood"],
        "bansuri",
        sides=18,
    )
    for x in (-0.302, -0.284, -0.141, 0.120, 0.135):
        s.tube(
            "Bansuri • binding",
            [
                p(x, 0.0125 * math.cos(TAU * j / 24), 0.0125 * math.sin(TAU * j / 24))
                for j in range(25)
            ],
            0.0022,
            m["gold"],
            "bansuri",
            sides=6,
        )
    for x in (-0.248, -0.195, -0.155, -0.118, -0.078, -0.038, 0.01, 0.061):
        s.ellipsoid(
            "Bansuri • tone hole",
            p(x, -0.0115, 0),
            (0.0038, 0.0038, 0.0038),
            m["hair"],
            "bansuri",
            12,
            8,
        )
    disk(s, palm(s, "R"), m)


def add_sockets(rig):
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    for name, side in (("bansuri", "L"), ("chakra", "R")):
        wrist = rig.data.edit_bones["wrist." + side]
        bone = rig.data.edit_bones.new(name)
        bone.head = wrist.head.copy()
        bone.tail = wrist.tail.copy()
        bone.roll = wrist.roll
        bone.parent = wrist
    bpy.ops.object.mode_set(mode="OBJECT")


def join(objects, name):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    bpy.ops.object.join()
    body = objects[0]
    body.name = name
    for mod in list(body.modifiers)[1:]:
        body.modifiers.remove(mod)
    return body


def build(hero, output_dir):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    c = dict(
        CONFIG[hero], id=hero, sex="male", crown=0.02 if hero == "krishna" else 0.0
    )
    body, rig, weights, tree = build_anatomy(
        ART / "sources/makehuman", "male", c["height"], c["width"], c["face_width"]
    )
    rig.name = hero.title() + " • Preview Rig"
    if hero == "krishna":
        add_sockets(rig)
    m = palette(c)
    body.data.materials.append(m["skin"])
    body.data.materials.append(m["ivory"])
    for face in body.data.polygons:
        if c["height"] * 0.07 < face.center.z < c["height"] * 0.545:
            face.material_index = 1
    sculpt = Sculpt(rig, body, weights, tree)
    costume(sculpt, c["height"], c, m)
    face_and_hair(sculpt, c["height"], c, m)
    remove = [
        "Tailored woven bodice",
        "Repousse shoulder",
        "Shoulder engraved",
        "Forehead tilaka",
        "Gold chest chain",
    ]
    if hero == "shiva":
        remove += [
            "Layered silk mantle",
            "Mantle ",
            "Folded diagonal",
            "Sash woven",
            "Lotus diadem",
            "Crown faceted",
            "Collar torc",
        ]
    for obj in list(sculpt.objects):
        if any(obj.name.startswith(prefix) for prefix in remove):
            sculpt.objects.remove(obj)
            bpy.data.objects.remove(obj, do_unlink=True)
    face_paint(sculpt, c, m, hero)
    if hero == "shiva":
        shiva_details(sculpt, c, m)
    else:
        krishna_details(sculpt, c, m)
    props = [
        o
        for o in sculpt.objects
        if o.name.startswith(("Trishula", "Damaru", "Bansuri", "Sudarshana"))
    ]
    surfaces = join(
        [o for o in sculpt.objects if o not in props],
        hero.title() + " • body and regalia",
    )
    join(props, hero.title() + " • signature instruments")
    actions = author(rig, hero)
    rig.animation_data.action = actions["idle"]
    bpy.context.scene.frame_set(1)
    # glTF receives one exported material per source, with embedded woven color maps.
    for mat in (m["cloth"], m["ivory"]):
        for mesh in (surfaces.data,):
            layer = mesh.uv_layers.active
            if layer:
                for face in mesh.polygons:
                    if mesh.materials[face.material_index] == mat:
                        for li in face.loop_indices:
                            layer.data[li].uv *= 4.0
    out = output_dir / (hero + ".glb")
    bpy.ops.export_scene.gltf(
        filepath=str(out),
        export_format="GLB",
        export_animations=True,
        export_animation_mode="ACTIONS",
        export_force_sampling=True,
        export_frame_range=False,
        export_skins=True,
        export_yup=True,
    )
    print(
        f"Built {out} with {len(rig.data.bones)} joints and {len(actions)} actions",
        flush=True,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("heroes", nargs="*", help="shiva or krishna")
    parser.add_argument("--output", type=Path, default=PACK / "models")
    args = parser.parse_args(
        sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    )
    args.output.mkdir(parents=True, exist_ok=True)
    for identity in args.heroes or CONFIG:
        if identity not in CONFIG:
            parser.error(f"Unknown hero {identity}")
        build(identity, args.output)
