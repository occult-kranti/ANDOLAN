"""Project native Source info_overlays onto their actual clipped and displaced surfaces."""

import struct
from functools import lru_cache

import numpy as np
from srctools.bsp import BSP_LUMPS

from source_world import INCH, axes, unit_rows


def cross2(a, b):
    return a[0] * b[1] - a[1] * b[0]


def clip_polygon(vertices, triangle):
    """Clip the polygon (local xy + attributes) against a convex oriented triangle."""
    sign = 1 if cross2(triangle[1] - triangle[0], triangle[2] - triangle[0]) > 0 else -1
    for i, corner in enumerate(triangle):
        edge = triangle[(i + 1) % 3] - corner
        output = []
        if not vertices:
            return []
        prev = vertices[-1]
        prev_distance = sign * cross2(edge, prev[:2] - corner)
        for current in vertices:
            distance = sign * cross2(edge, current[:2] - corner)
            if (distance < -1.0e-7) != (prev_distance < -1.0e-7):
                weight = prev_distance / (prev_distance - distance)
                output.append(prev + weight * (current - prev))
            if distance >= -1.0e-7:
                output.append(current)
            prev, prev_distance = current, distance
        vertices = output
    return vertices


def overlay_mesh(record, surface):
    identity, texinfo, flags = struct.unpack_from("<ihH", record)
    count = flags & 0x3FFF
    if count > 64:
        raise ValueError(f"BSP overlay {identity} references {count} faces")
    faces = struct.unpack_from(f"<{count}i", record, 8)
    a = np.asarray(struct.unpack_from("<22f", record, 264))
    u0, u1, v0, v1 = a[:4]
    handles = a[4:16].reshape(4, 3)
    org = a[16:19]
    axis_u = handles[:3, 2]
    normal = a[19:22]
    axis_v = np.cross(normal, axis_u)
    if handles[3, 2] > 0.5:
        axis_v = -axis_v
    corners = handles[:, :2]
    tex_coords = np.array([[u0, v0], [u0, v1], [u1, v1], [u1, v0]])
    halves = []
    for order in [[0, 1, 2], [0, 2, 3]]:
        tri = corners[order]
        square = tex_coords[order]
        den = cross2(tri[1] - tri[0], tri[2] - tri[0])
        if abs(den) > 1.0e-8:
            coefficients = np.linalg.solve(np.column_stack((tri, np.ones(3))), square)
            halves.append((tri, coefficients))
    extent_min, extent_max = corners.min(axis=0), corners.max(axis=0)
    positions = []
    normals = []
    uv = []
    indices = []
    for face in faces:
        points, orig_normals, _, triangles, _ = surface(face)
        xy = (points - org) @ np.array([axis_u, axis_v]).T
        attributes = np.column_stack([xy, points, orig_normals])
        tri_xy = xy[triangles]
        feasible = np.all(tri_xy.max(axis=1) >= extent_min - 1.0e-7, axis=1) & np.all(
            tri_xy.min(axis=1) <= extent_max + 1.0e-7, axis=1
        )
        for original in triangles[feasible]:
            input_poly = attributes[original]
            for cut, coefficients in halves:
                poly = clip_polygon(list(input_poly), cut)
                if len(poly) < 3:
                    continue
                pp = np.array(poly)
                fan = np.array([[0, t, t + 1] for t in range(1, len(pp) - 1)])
                inside = pp[fan, :2]
                u = inside[:, 1] - inside[:, 0]
                v = inside[:, 2] - inside[:, 0]
                fan = fan[np.abs(u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]) > 1.0e-6]
                if not len(fan):
                    continue
                offset = len(positions)
                local_normals = unit_rows(pp[:, 5:8])
                positions.extend(
                    pp[:, 2:5] + local_normals * (0.08 + 0.035 * (flags >> 14))
                )
                normals.extend(local_normals)
                uv.extend(np.column_stack((pp[:, :2], np.ones(len(pp)))) @ coefficients)
                indices.extend(fan + offset)
    return (
        identity,
        texinfo,
        faces,
        flags >> 14,
        tuple(np.asarray(v) for v in (positions, normals, uv, indices)),
    )


def add_overlays(scene, world, report):
    raw = world.bsp.lumps[BSP_LUMPS(45)].data
    if len(raw) % 352:
        raise ValueError("Unsupported legacy Source overlay record size")
    surface = lru_cache(maxsize=256)(world.surface)
    nodes = []
    empty = []
    total_triangles = 0
    for offset in range(0, len(raw), 352):
        ident, ti, faces, order, (pp, norm, uv, indices) = overlay_mesh(
            raw[offset : offset + 352], surface
        )
        if not len(indices):
            empty.append(ident)
            continue
        material = world.materials[world.texdata[world.texinfo[ti]["texture"]]["name"]]
        slot = scene.material(material)
        name = f"Overlay {ident}: {material.rsplit('/', 1)[-1]}"
        extras = {
            "sourceOverlayId": ident,
            "sourceOverlayFaces": faces,
            "sourceRenderOrder": order,
        }
        p = scene.primitive(axes(pp) * INCH, axes(norm), uv, indices, slot, extras)
        nodes.append(scene.node(name=name, mesh=scene.mesh(name, [p]), extras=extras))
        total_triangles += len(indices)
    scene.root("Projected surface markings", nodes)
    report.update(
        sourceOverlays=len(raw) // 352,
        renderedOverlays=len(nodes),
        overlayTriangles=total_triangles,
        overlaysWithoutVisibleArea=empty,
    )
