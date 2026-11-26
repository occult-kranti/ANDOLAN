"""Small, shared Blender geometry and PBR palette for Mandala's editable environment."""

from functools import lru_cache
from math import cos, pi, sin, tau
import bpy
import bmesh
from mathutils import Vector

# Hex values are display sRGB. Metal fraction and roughness are linear.
PALETTE = {
    "sandstone": ("BE815C", 0.03, 0.79),
    "limestone": ("E1C6A0", 0.02, 0.72),
    "granite": ("797A72", 0.07, 0.70),
    "basalt": ("414949", 0.05, 0.76),
    "terracotta": ("AD573A", 0.02, 0.78),
    "bronze": ("93643D", 0.60, 0.38),
    "brass": ("D6A753", 0.70, 0.31),
    "patina": ("478477", 0.46, 0.52),
    "timber": ("644630", 0.01, 0.80),
    "indigo": ("344D6A", 0.0, 0.88),
    "saffron": ("D18B3D", 0.0, 0.84),
    "madder": ("A0473B", 0.0, 0.85),
    "linen": ("E8D7AE", 0.0, 0.86),
    "leaf": ("486747", 0.0, 0.70),
    "reed": ("82935A", 0.0, 0.66),
    "water": ("478A88", 0.23, 0.27),
    "teal": ("336B6D", 0.04, 0.61),
    "ink": ("263638", 0.08, 0.68),
    "ember": ("FF9550", 0.08, 0.35),
}


def linear(hex_value):
    nums = [int(hex_value[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    return tuple(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in nums) + (1.0,)


@lru_cache(None)
def mat(key):
    if isinstance(key, bpy.types.Material):
        return key
    if key in PALETTE:
        tone, metal, rough = PALETTE[key]
    else:
        tone = key.lstrip("#")
        if len(tone) != 6:
            raise ValueError(f"Unknown material {key!r}")
        metal, rough = 0.0, 0.68
    material = bpy.data.materials.new("Mandala / " + key)
    material.diffuse_color = rgba = linear(tone)
    material.use_nodes = True
    shader = material.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = rgba
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = rough
    if key == "ember":
        shader.inputs["Emission Color"].default_value = rgba
        shader.inputs["Emission Strength"].default_value = 1.1
    return material


def mesh_data(name, verts, faces, key):
    data = bpy.data.meshes.new(name)
    data.from_pydata(list(verts), [], list(faces))
    data.update()
    data.materials.append(mat(key))
    return data


def instance(name, data, loc=(0.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = loc
    return obj


def mesh(name, vertices, faces, mat):
    return instance(name, mesh_data(name, vertices, faces, mat))


@lru_cache(None)
def box_data(size, key, bevel):
    hx, hy, hz = (n / 2 for n in size)
    verts = [(x * hx, y * hy, z * hz) for z in (-1, 1) for x, y in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    data = mesh_data("Course", verts, faces, key)
    if bevel:
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.bevel(
            bm,
            geom=list(bm.edges),
            offset=min(bevel, min(size) * 0.2),
            segments=2,
            affect="EDGES",
            profile=0.5,
        )
        bm.to_mesh(data)
        bm.free()
    return data


def box(name, loc, size, mat, bevel=0):
    return instance(name, box_data(tuple(round(float(x), 6) for x in size), mat, bevel), loc)


@lru_cache(None)
def round_data(vertices, key):
    if vertices < 3:
        raise ValueError("A cylinder needs at least three sides")
    ring = [(cos(i * tau / vertices), sin(i * tau / vertices)) for i in range(vertices)]
    verts = [(x, y, z) for z in (-0.5, 0.5) for x, y in ring]
    faces = [list(reversed(range(vertices))), list(range(vertices, 2 * vertices))]
    faces += [(i, (i + 1) % vertices, (i + 1) % vertices + vertices, i + vertices) for i in range(vertices)]
    data = mesh_data("Turned shaft", verts, faces, key)
    for face in list(data.polygons)[2:]:
        face.use_smooth = vertices >= 12
    return data


def cyl(name, loc, radius, depth, mat, vertices=16, rotation=None):
    obj = instance(name, round_data(vertices, mat), loc)
    obj.scale = (radius, radius, depth)
    if rotation is not None:
        obj.rotation_euler = rotation
    return obj


@lru_cache(None)
def sphere_data(key):
    lat, lon = 8, 14
    verts = [(0, 0, -1)]
    for j in range(1, lat):
        y = pi * j / lat - pi / 2
        verts += [(cos(y) * cos(tau * i / lon), cos(y) * sin(tau * i / lon), sin(y)) for i in range(lon)]
    top = len(verts)
    verts.append((0, 0, 1))
    faces = [(0, 1 + (i + 1) % lon, 1 + i) for i in range(lon)]
    for j in range(lat - 2):
        a = 1 + j * lon
        for i in range(lon):
            k = (i + 1) % lon
            faces.append((a + i, a + k, a + lon + k, a + lon + i))
    faces += [(top, top - lon + i, top - lon + (i + 1) % lon) for i in range(lon)]
    data = mesh_data("Hand-formed oval", verts, faces, key)
    for face in data.polygons:
        face.use_smooth = True
    return data


def ellipsoid(name, loc, radii, mat):
    obj = instance(name, sphere_data(mat), loc)
    obj.scale = radii
    return obj


def beam(name, p0, p1, radius, mat, vertices=10):
    v0, v1 = Vector(p0), Vector(p1)
    direction = v1 - v0
    obj = cyl(name, (v0 + v1) * 0.5, radius, direction.length, mat, vertices)
    if direction.length_squared:
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return obj
