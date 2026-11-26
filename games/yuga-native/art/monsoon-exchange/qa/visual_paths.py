"""Shoot movement-height rays through the entire visible scene, including decoration."""

from collections import Counter
from math import ceil, hypot

import bpy
from mathutils import Vector

from mesh_io import need
from walks import surface


def first_visible(scene, deps, start, finish):
    d = finish - start
    length = d.length
    if length < 0.0001:
        return None
    d /= length
    # Markers on a plan may be visible without belonging to the modeled building.
    while length > 0.0001:
        hit, point, normal, face, obj, matrix = scene.ray_cast(
            deps, start, d, distance=length
        )
        if not hit:
            return None
        role = obj.get("role", "unclassified")
        if not obj.hide_render and role not in {"marker", "guide", "collision"}:
            return obj.name
        length -= (point - start).length + 0.001
        start = point + 0.001 * d
    return None


def visible_corridors(collision, data):
    scene = bpy.context.scene
    deps = bpy.context.evaluated_depsgraph_get()
    hits = Counter()
    first = {}
    tested = 0
    for link in data["links"]:
        for a, b in zip(link["points"], link["points"][1:]):
            dx, dy = b[0] - a[0], b[1] - a[1]
            run = hypot(dx, dy)
            n = ceil(run / 0.40)
            previous = {}
            for i in range(n + 1):
                t = i / n
                x = a[0] + dx * t
                y = a[1] + dy * t
                # First use the surface at the authored centre. At a level turning
                # square a linear estimate may be >0.45 m from the developed floor.
                floor_hit = collision.floor.ray((x, y, 40), (0, 0, -1), 80)
                need(
                    floor_hit is not None,
                    f"Missing floor under visual probe {link['id']}",
                )
                z = floor_hit[0].z
                for across in (-0.4, 0.0, 0.4):
                    px = x - across * dy / run
                    py = y + across * dx / run
                    ground = surface(collision, px, py, z)
                    need(ground is not None, f"Unsupported shoulder track {link['id']}")
                    for height in (0.42, 0.95, data["rules"]["standing_eye_m"]):
                        k = across, height
                        q = Vector((px, py, ground + height))
                        if k in previous:
                            objname = first_visible(scene, deps, previous[k], q)
                            tested += 1
                            if objname:
                                key = link["id"] + "/" + objname
                                hits[key] += 1
                                first.setdefault(key, tuple(round(v, 2) for v in q))
                        previous[k] = q
    need(
        not hits,
        "Visible geometry crossing a walk at knee, torso or eye height: "
        + str([(key, count, first[key]) for key, count in hits.most_common(20)]),
    )
    return {
        "connectors": len(data["links"]),
        "eye_height_m": data["rules"]["standing_eye_m"],
        "checks_at_m": [0.42, 0.95, data["rules"]["standing_eye_m"]],
        "lateral_offsets_m": [-0.4, 0.0, 0.4],
        "ray_segments": tested,
        "visible_crossings": 0,
    }
