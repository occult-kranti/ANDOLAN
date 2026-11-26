"""Project the registered Blender studies into the rehearsal's walking-height band."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "massing"))
from architecture import Architecture, world_xy


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def convex_hull(points):
    points = sorted(set(points))
    if len(points) < 3:
        return []

    def chain(sequence):
        edge = []
        for p in sequence:
            while len(edge) >= 2 and cross(edge[-2], edge[-1], p) <= 1e-9:
                edge.pop()
            edge.append(p)
        return edge[:-1]

    return chain(points) + chain(reversed(points))


def walking_outline(part, low=.025, high=1.7):
    # Intersect each convex masonry part with the body's vertical interval.
    points = [(x, y) for x, y, z in part.vertices if low <= z <= high]
    for face in part.faces:
        for i, index in enumerate(face):
            x1, y1, z1 = part.vertices[index]
            x2, y2, z2 = part.vertices[face[i - 1]]
            for height in (low, high):
                if min(z1, z2) < height < max(z1, z2):
                    t = (height - z1) / (z2 - z1)
                    points.append((x1 + t * (x2 - x1), y1 + t * (y2 - y1)))
    return convex_hull(points)


def area(polygon):
    return abs(sum(cross((0, 0), a, polygon[i - 1]) for i, a in enumerate(polygon))) / 2


def contained(small, large):
    return all(cross(large[i-1], end, point) >= -1e-8
               for point in small for i, end in enumerate(large))


def project_building(data):
    study = Architecture(data)

    def registered(polygon):
        return [[round(v, 4) for v in world_xy(*p, study.node, study.bearing)] for p in polygon]

    def rectangle(width, depth):
        return registered([(-width/2, -depth/2), (width/2, -depth/2),
                           (width/2, depth/2), (-width/2, depth/2)])

    solids, water = [], []
    for part in study.parts:
        if part.material == "Water":
            outline = convex_hull([(x, y) for x, y, _ in part.vertices])
            water.append({"label": part.name, "ring": registered(outline)})
        else:
            outline = walking_outline(part)
            if len(outline) >= 3 and area(outline) > 1e-8:
                solids.append((part.name, outline))

    # Keep individual gallery columns and well posts; their smaller nested courses
    # need only the outer collision polygon in plan view.
    hulls = []
    for part_name, polygon in sorted(solids, key=lambda item: -area(item[1])):
        if not any(contained(polygon, outer) for _, outer in hulls):
            hulls.append((part_name, polygon))
    return {"outline": rectangle(study.w, study.d), "passage": rectangle(study.opening, study.d),
            "solids": [{"label": name, "ring": registered(ring)} for name, ring in hulls], "water": water}
