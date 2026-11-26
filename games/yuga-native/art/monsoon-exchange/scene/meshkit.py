"""Meter-space geometry, grouped by editable building or surveyed element."""

import math
import bpy
from mathutils import Vector
from surfaces import SURFACES

MATERIALS = {}
SCALES = {}
COLL = {}
TWO_PI = math.tau


def materials(texture_dir):
    from artlib import (
        linear,
    )  # The same color transform as the original Mandala models.

    solids = {
        "sand": ("dfc495", 0.02, 0.83),
        "cream": ("eed8af", 0.03, 0.75),
        "basalt": ("415457", 0.10, 0.75),
        "umber": ("795446", 0.03, 0.78),
        "wood": ("694735", 0.03, 0.75),
        "ink": ("233b40", 0.05, 0.70),
        "gold": ("dbac62", 0.56, 0.34),
        "patina": ("5b9587", 0.42, 0.49),
        "ivory": ("f2d7a1", 0.04, 0.72),
        "glaze": ("219494", 0.27, 0.28),
        "leaf": ("507956", 0.03, 0.75),
        "leaf-light": ("789452", 0.02, 0.81),
        "leaf-dark": ("345c45", 0.02, 0.77),
        "reed": ("97a45c", 0.03, 0.82),
        "signal": ("eeab49", 0.22, 0.31),
        "ferric": ("91664a", 0.40, 0.54),
        "clay": ("bc7951", 0.02, 0.81),
        "paper": ("ece0c5", 0.01, 0.89),
    }
    for key in [*solids, *SURFACES]:
        rgb, metal, rough = solids.get(key, ("ffffff", 0.05, 0.78))
        if key in SURFACES:
            rgb, family, scale = SURFACES[key]
            metal, rough = {
                "water": (0.30, 0.2),
                "metal": (0.49, 0.45),
                "roof": (0.09, 0.61),
                "textile": (0.01, 0.91),
            }.get(family, (0.02, 0.78))
            SCALES[key] = scale
        m = bpy.data.materials.new("Exchange · " + key)
        m.diffuse_color = linear(rgb)
        m.use_nodes = True
        nt = m.node_tree
        sh = nt.nodes.get("Principled BSDF")
        sh.inputs["Base Color"].default_value = linear(rgb)
        sh.inputs["Metallic"].default_value = metal
        sh.inputs["Roughness"].default_value = rough
        if key in SURFACES:
            img = bpy.data.images.load(str(texture_dir / (key + ".png")))
            img.name = "Exchange / " + key
            img.pack()
            # Relative filename stays meaningful to editors extracting the packed art.
            img.filepath_raw = "//textures/" + key + ".png"
            tex = nt.nodes.new("ShaderNodeTexImage")
            tex.image = img
            tex.extension = "REPEAT"
            nt.links.new(tex.outputs["Color"], sh.inputs["Base Color"])
        if key == "signal":
            sh.inputs["Emission Color"].default_value = linear("e28030")
            sh.inputs["Emission Strength"].default_value = 0.28
        elif key == "water":
            # Subsurface blue-green bounce remains visible below the shaded terraces.
            sh.inputs["Emission Color"].default_value = linear("358f91")
            sh.inputs["Emission Strength"].default_value = 0.19
        MATERIALS[key] = m


def groups(scene, names):
    for name in names:
        coll = bpy.data.collections.new(name)
        scene.collection.children.link(coll)
        COLL[name] = coll


def obj(name, mesh, group, role, element, **kwargs):
    o = bpy.data.objects.new(name, mesh)
    COLL[group].objects.link(o)
    o["role"] = role
    o["element"] = element
    for k, v in kwargs.items():
        o[k] = v
    return o


class Batch:
    """A local frame, e.g. U along the facade and V to its exterior or interior."""

    def __init__(self, origin=(0, 0, 0), u=(1, 0), v=None):
        self.origin = Vector(origin)
        self.u = Vector((*u, 0)).normalized()
        self.v = (
            Vector((-self.u.y, self.u.x, 0))
            if v is None
            else Vector((*v, 0)).normalized()
        )
        self.verts = []
        self.faces = []
        self.slots = []
        self.smooth = []
        self.reverse = self.u.x * self.v.y - self.u.y * self.v.x < 0

    def point(self, p):
        return (
            self.origin.x + self.u.x * p[0] + self.v.x * p[1],
            self.origin.y + self.u.y * p[0] + self.v.y * p[1],
            self.origin.z + p[2],
        )

    def solid(self, verts, faces, mat, smooth=False):
        n = len(self.verts)
        self.verts.extend(self.point(a) for a in verts)
        for f in faces:
            self.faces.append(
                tuple(n + i for i in (reversed(f) if self.reverse else f))
            )
            self.slots.append(mat)
            self.smooth.append(smooth)

    def box(self, x, y, z, w, d, h, mat):
        if min(w, d, h) <= 0:
            return
        v = [
            (x + i * w / 2, y + j * d / 2, z + k * h)
            for k in (0, 1)
            for i, j in ((-1, -1), (1, -1), (1, 1), (-1, 1))
        ]
        self.solid(
            v,
            [
                (3, 2, 1, 0),
                (4, 5, 6, 7),
                (0, 1, 5, 4),
                (1, 2, 6, 5),
                (2, 3, 7, 6),
                (3, 0, 4, 7),
            ],
            mat,
        )

    def section(self, points, y, d, mat):
        # CCW X/Z profile, viewed from the front (negative local Y).
        n = len(points)
        verts = [(x, yy, z) for yy in (y, y + d) for x, z in points]
        faces = [tuple(range(n)), tuple(range(2 * n - 1, n - 1, -1))] + [
            ((i + 1) % n, i, i + n, (i + 1) % n + n) for i in range(n)
        ]
        self.solid(verts, faces, mat)

    def lathe(self, x, y, z, profile, mat, n=16, flute=0, turn=0, smooth=True):
        vs = []
        fs = []
        for r, h in profile:
            for i in range(n):
                a = TWO_PI * i / n + turn
                rad = max(0.0005, r) * (1 + flute * (i % 2))
                vs.append((x + rad * math.cos(a), y + rad * math.sin(a), z + h))
        count = len(profile)
        fs.extend(
            (i * n + j, i * n + (j + 1) % n, (i + 1) * n + (j + 1) % n, (i + 1) * n + j)
            for i in range(count - 1)
            for j in range(n)
        )
        fs.extend((tuple(reversed(range(n))), tuple(range((count - 1) * n, count * n))))
        self.solid(vs, fs, mat, smooth)

    def beam(self, a, b, r, mat, n=6):
        a, b = Vector(a), Vector(b)
        t = (b - a).normalized()
        ref = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
        side = t.cross(ref).normalized()
        up = t.cross(side).normalized()
        vs = []
        for p in (a, b):
            for i in range(n):
                angle = TWO_PI * i / n
                vs.append(p + r * (side * math.cos(angle) + up * math.sin(angle)))
        self.solid(
            vs,
            [(i, (i + 1) % n, (i + 1) % n + n, i + n) for i in range(n)]
            + [tuple(reversed(range(n))), tuple(range(n, 2 * n))],
            mat,
            True,
        )

    def arc(self, xc, y, h, w, depth, rise, band, mat):
        """Carved pointed arch ribbon with small cusps, open below the spring line."""
        n = 24
        line = []
        for i in range(n + 1):
            k = (i / n) * 2 - 1
            shape = (1 - abs(k)) ** 0.59 + 0.05 * math.sin(
                4 * math.pi * (1 - abs(k))
            ) ** 2
            line.append((xc + k * w / 2, h + rise * shape))
        for i in range(n):
            x1, z1 = line[i]
            x2, z2 = line[i + 1]
            self.section(
                [(x1, z1), (x2, z2), (x2, z2 + band), (x1, z1 + band)], y, depth, mat
            )
        return line

    def finish(self, name, group, role, element, **kwargs):
        if not self.faces:
            return None
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.verts, [], self.faces)
        mesh.update()
        mats = {k: i for i, k in enumerate(dict.fromkeys(self.slots))}
        for key in mats:
            mesh.materials.append(MATERIALS[key])
        uv = mesh.uv_layers.new(name="Metre projection")
        coords = [0.0] * (len(mesh.loops) * 2)
        for poly, material, smooth in zip(mesh.polygons, self.slots, self.smooth):
            poly.material_index = mats[material]
            poly.use_smooth = smooth
            scale = SCALES.get(material, 3)
            normal = poly.normal
            for vi, li in zip(poly.vertices, poly.loop_indices):
                x, y, z = self.verts[vi]
                a, b = (
                    (x, y)
                    if abs(normal.z) > 0.62
                    else ((-normal.y * x + normal.x * y), z)
                )
                coords[li * 2] = a / scale
                coords[li * 2 + 1] = b / scale
        uv.data.foreach_set("uv", coords)
        return obj(name, mesh, group, role, element, **kwargs)


def blockprint(path):
    """Use the original project painting as a real, exportable base-color swatch."""
    m = bpy.data.materials.new("Exchange · Indigo loom block print")
    m.diffuse_color = (0.062, 0.17, 0.19, 1)
    m.use_nodes = True
    img = bpy.data.images.load(str(path))
    img.name = "Monsoon Exchange / Indigo loom block print"
    img.pack()
    img.filepath_raw = "//../concepts/indigo-cloth.png"
    node = m.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    node.extension = "REPEAT"
    sh = m.node_tree.nodes.get("Principled BSDF")
    sh.inputs["Roughness"].default_value = 0.93
    m.node_tree.links.new(node.outputs["Color"], sh.inputs["Base Color"])
    MATERIALS["exchange-print"] = m
    SCALES["exchange-print"] = 1.75
