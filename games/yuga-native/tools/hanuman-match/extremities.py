"""Fit weighted keratin plates and digit detail to Hanuman's existing anatomy."""

from __future__ import annotations

import math

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def digit_groups(rig):
    for side in ("L", "R"):
        sign = 1 if side == "L" else -1
        palm_out = rig.data.bones[f"wrist.{side}"].matrix_local.to_3x3().col[2].copy() * sign
        thumb_out = Vector((-sign, -.32, 1)).normalized()
        for kind, outward in (("finger", palm_out), ("toe", Vector((0, 0, 1)))):
            for digit in range(1, 6):
                parent = f"{kind}{digit}-"
                chain = [b for b in rig.data.bones if b.name.startswith(parent) and b.name.endswith(f".{side}")]
                chain.sort(key=lambda b: b.name)
                direction = thumb_out if kind == "finger" and digit == 1 else outward
                yield kind, side, digit, chain, direction


def smooth_step(start, end, value):
    t = min(1.0, max(0.0, (value - start) / (end - start)))
    return t * t * (3 - 2 * t)


def joint_detail(body, groups):
    """Shape a shallow dorsal knuckle and crease on the actual skinned mesh."""
    data = body.data
    weights = {g.index: g.name for g in body.vertex_groups}
    joints = {
        bone.name: (bone.head_local.copy(), (bone.tail_local - bone.head_local).normalized(), outward, kind)
        for kind, _, _, chain, outward in groups
        for bone in chain[1:]
    }
    pigment_delta = {}
    changed = 0
    for vertex in data.vertices:
        if abs(vertex.co.x) < .56 and vertex.co.z >= .086:
            continue
        normal = vertex.normal.copy()
        for influence in vertex.groups:
            joint = joints.get(weights[influence.group])
            if joint is None or influence.weight < .15:
                continue
            pivot, axis, outward, kind = joint
            # Keep the palm and the support plane between the soles unmodified.
            if kind == "toe" and vertex.co.z <= .014:
                continue
            along = (vertex.co - pivot).dot(axis)
            dorsal = smooth_step(.10, .88, normal.dot(outward))
            dorsal *= influence.weight
            if dorsal == 0:
                continue
            width = .012 if kind == "finger" else .009
            rise = math.exp(-((along + .0025) / width) ** 2)
            crease = math.exp(-((along - .002) / (width * .29)) ** 2)
            vertex.co += normal * dorsal * (.0019 * rise - .0009 * crease)
            pigment_delta[vertex.index] = pigment_delta.get(vertex.index, 0.0) + dorsal * crease
            changed += 1
    if pigment := data.color_attributes.get("Pigment"):
        for loop in data.loops:
            if pigment_delta.get(loop.vertex_index, 0) > .005:
                color = pigment.data[loop.index].color
                factor = 1 - min(.18, pigment_delta[loop.vertex_index] * .16)
                pigment.data[loop.index].color = (*[component * factor for component in color[:3]], color[3])
    data.update()
    return len(pigment_delta), changed


class PlateFit:
    def __init__(self, body):
        mesh = body.data
        mesh.calc_loop_triangles()
        self.points = [vertex.co.copy() for vertex in mesh.vertices]
        self.triangles = [tuple(triangle.vertices) for triangle in mesh.loop_triangles]
        self.tree = BVHTree.FromPolygons(self.points, self.triangles, all_triangles=True)
        self.group_names = {g.index: g.name for g in body.vertex_groups}
        self.weights = [
            {self.group_names[g.group]: g.weight for g in v.groups}
            for v in mesh.vertices
        ]

    def skin(self, point, outward, names):
        spot, normal, triangle, _ = self.tree.ray_cast(point + outward * .045, -outward, .075)
        if triangle is None or normal.dot(outward) < .22:
            return None
        ids = self.triangles[triangle]
        a, b, c = [self.points[i] for i in ids]
        u, v, p = b - a, c - a, spot - a
        uv, uu, vv = u.dot(v), u.length_squared, v.length_squared
        denom = uu * vv - uv * uv
        if denom < 1e-18:
            return None
        frac_b = (p.dot(u) * vv - p.dot(v) * uv) / denom
        frac_c = (p.dot(v) * uu - p.dot(u) * uv) / denom
        frac_a = 1 - frac_b - frac_c
        weights = {}
        for vertex, factor in zip(ids, (frac_a, frac_b, frac_c)):
            for name, value in self.weights[vertex].items():
                weights[name] = weights.get(name, 0.0) + max(0.0, factor) * value
        if sum(weights.get(name, 0) for name in names) < .45:
            return None
        strongest = sorted(weights.items(), key=lambda item: -item[1])[:4]
        strongest = [(name, value) for name, value in strongest if value > 1e-5]
        total = sum(value for _, value in strongest)
        return spot, normal, [(name, value / total) for name, value in strongest]


def plate_samples(kind, digit, chain, outward, fit):
    tip = chain[-1]
    axis = (tip.tail_local - tip.head_local).normalized()
    length = tip.length
    outward = (outward - axis * outward.dot(axis)).normalized()
    across = outward.cross(axis).normalized()
    long_radius = min(.0095, length * (.29 if kind == "finger" else .36))
    width_radius = min(.0115, length * (.38 if digit == 1 else .25))
    names = {bone.name for bone in chain}
    sectors = 16
    perimeter = [(0.0, 0.0, 0.0)]
    for ring in (.37, .70, 1.0):
        for index in range(sectors):
            angle = math.tau * index / sectors
            u, v = math.cos(angle), math.sin(angle)
            perimeter.append((math.copysign(abs(u) ** .82, u) * ring,
                              math.copysign(abs(v) ** .84, v) * ring, ring))

    # Move the plate into the real dorsal surface before reducing the outline.
    for fraction in (.55, .46, .64, .38):
        centerline = tip.head_local.lerp(tip.tail_local, fraction)
        for scale in (1.0, .84, .70):
            surface = [
                fit.skin(centerline + axis * (u * long_radius * scale)
                         + across * (v * width_radius * scale), outward, names)
                for u, v, _ in perimeter
            ]
            if all(sample is not None for sample in surface):
                return surface, perimeter, sectors
    raise ValueError(f"No dorsal {kind} plate fit for {tip.name}")


def amber_keratin():
    material = bpy.data.materials.new("Hanuman | amber keratin and cuticle")
    material.diffuse_color = (.25, .10, .065, 1)
    material.use_nodes = True
    tree = material.node_tree
    shader = tree.nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .46
    shader.inputs["Coat Weight"].default_value = .12
    shader.inputs["Coat Roughness"].default_value = .41
    shader.inputs["Subsurface Weight"].default_value = .07
    shader.inputs["Subsurface Radius"].default_value = (.055, .032, .02)
    shader.inputs["Subsurface Scale"].default_value = .014
    color = tree.nodes.new("ShaderNodeVertexColor")
    color.layer_name = "Keratin tone"
    tree.links.new(color.outputs["Color"], shader.inputs["Base Color"])
    return material


def make_plate(collection, rig, kind, side, digit, material, fitted):
    samples, perimeter, sectors = fitted
    positions, colors = [], []
    for (position, normal, _), (along, _, radial) in zip(samples, perimeter):
        edge = smooth_step(.81, 1.0, radial)
        rise = (.00070 + .00047 * (1 - radial * radial) - edge * .00062)
        free_edge = smooth_step(.39, .98, along) * smooth_step(.44, .95, radial)
        root = smooth_step(-.16, -.91, along)
        positions.append(position + normal * rise)
        tone = (.255, .112, .081)
        colors.append((tone[0] + .082 * free_edge - .064 * root,
                       tone[1] + .059 * free_edge - .038 * root,
                       tone[2] + .045 * free_edge - .031 * root, 1))

    faces = [(0, 1 + i, 1 + (i + 1) % sectors) for i in range(sectors)]
    for base in (1, 1 + sectors):
        for i in range(sectors):
            inner, nxt = base + i, base + (i + 1) % sectors
            faces.append((inner, inner + sectors, nxt + sectors, nxt))

    mesh = bpy.data.meshes.new(f"Hanuman | {side} {kind} {digit} dorsal plate")
    mesh.from_pydata(positions, [], faces)
    mesh.update()
    pigment = mesh.color_attributes.new(name="Keratin tone", type="FLOAT_COLOR", domain="POINT")
    for vertex, value in zip(pigment.data, colors):
        vertex.color = value
    mesh.materials.append(material)
    for face in mesh.polygons:
        face.use_smooth = True

    obj = bpy.data.objects.new(mesh.name, mesh)
    collection.objects.link(obj)
    obj.parent = rig
    groups = {}
    for vertex, (_, _, weights) in enumerate(samples):
        for name, weight in weights:
            if name not in groups:
                groups[name] = obj.vertex_groups.new(name=name)
            groups[name].add([vertex], weight, "REPLACE")
    modifier = obj.modifiers.new("Digit and toe skin binding", "ARMATURE")
    modifier.object = rig
    return obj


def apply(scene, reference_profile):
    """Add individually shaped fingernails and toenails using the donor skin."""
    if not reference_profile.get("extremities", {}).get("enabled", True):
        return {"enabled": False}

    rig = scene.objects.get("YugaHeroRig")
    body = next(o for o in scene.objects if o.name.startswith("Hanuman · contiguous skinned anatomy"))
    if rig.data.pose_position != "REST":
        raise ValueError("Set Hanuman's armature to REST before fitting digit detail")
    groups = list(digit_groups(rig))
    vertices, influences = joint_detail(body, groups)
    fit = PlateFit(body)
    collection = bpy.data.collections.new("Hanuman | hands and feet anatomical detail")
    scene.collection.children.link(collection)
    material = amber_keratin()
    plates = [
        make_plate(collection, rig, kind, side, digit, material, plate_samples(kind, digit, chain, outward, fit))
        for kind, side, digit, chain, outward in groups
    ]
    bpy.context.view_layer.update()
    return {
        "enabled": True,
        "fingernails": sum("finger " in obj.name for obj in plates),
        "toenails": sum("toe " in obj.name for obj in plates),
        "keratin_vertices": sum(len(obj.data.vertices) for obj in plates),
        "shaped_crease_vertices": vertices,
        "shaped_crease_influences": influences,
    }
