"""Route measurements for the Ember Rite floor survey, with body clearance and wet ground."""

import argparse
from collections import defaultdict
from heapq import heappush, heappop
import json
import math

from geometry import HERE, as_json, emit, extent, rounded, surface_z

GRID = 0.5
# Gate sequences restrict these measurements to the entrance being compared.
ITINERARIES = [
    ("a-long", "A · Copper Arcade", ["atk", "toll", "copper", "a"]),
    ("a-short", "A · Ledger Balcony", ["atk", "scales", "mid", "ledger", "a"]),
    ("b-vault", "B · Dyers’ Passage", ["atk", "sail", "dyers", "b"]),
    ("b-sluice", "B · Sluice Walk", ["atk", "scales", "mid", "sluice", "b"]),
    ("a-keep", "A · Archive return", ["def", "a"]),
    ("b-keep", "B · Archive return", ["def", "b"]),
    ("a-witness", "A · Witness Gate", ["def", "well", "a"]),
    ("rotation", "B to A · northern return", ["b", "def", "a"]),
    ("rotation-mid", "B to A · middle switch", ["b", "sluice", "mid", "ledger", "a"]),
]


def box_at(rect):
    x, y = rect["center"][:2]
    w, d = rect["size"][:2]
    return (x - w / 2, y - d / 2, x + w / 2, y + d / 2)


def box_distance(point, box):
    x, y = point
    x0, y0, x1, y1 = box
    return math.hypot(max(0, x0 - x, x - x1), max(0, y0 - y, y - y1))


class SurveyGrid:
    def __init__(self, survey, mesh):
        self.nodes = {}
        self.owners = defaultdict(set)
        self.wet = set()
        self.radius = survey["rules"]["clearance_radius_m"]
        wet = [box_at(o) for o in survey["water"]]
        cover = [box_at(o) for o in survey["covers"]]
        boundary = [
            (
                min(w["a"][0], w["b"][0]),
                min(w["a"][1], w["b"][1]),
                max(w["a"][0], w["b"][0]),
                max(w["a"][1], w["b"][1]),
            )
            for w in mesh["walls"]
        ]
        for floor in mesh["floors"]:
            bounds = extent(floor)
            nearby = [
                r
                for r in cover + boundary
                if r[2] + self.radius >= bounds[0]
                and r[0] - self.radius <= bounds[2]
                and r[3] + self.radius >= bounds[1]
                and r[1] - self.radius <= bounds[3]
            ]
            for i in range(math.ceil(bounds[0] / GRID), math.floor(bounds[2] / GRID) + 1):
                for j in range(math.ceil(bounds[1] / GRID), math.floor(bounds[3] / GRID) + 1):
                    x, y = i * GRID, j * GRID
                    if any(box_distance((x, y), r) < self.radius - 1e-8 for r in nearby):
                        continue
                    self.nodes[i, j] = surface_z(floor, x, y)
                    self.owners[i, j].add(floor["owner"])
                    if any(box_distance((x, y), r) < 1e-8 for r in wet):
                        self.wet.add((i, j))

    def search(self, a, b, allowed, wet_factor, mode="normal"):
        start, goal = tuple(round(q / GRID) for q in a[:2]), tuple(round(q / GRID) for q in b[:2])
        assert start in self.nodes and goal in self.nodes
        open_set = {
            k
            for k, v in self.owners.items()
            if allowed.intersection(v) and (mode != "dry" or k not in self.wet)
        }
        distances = {start: 0}
        previous = {}
        queue = [(0, start)]
        while queue:
            t, node = heappop(queue)
            if node == goal:
                break
            if t != distances[node]:
                continue
            i, j = node
            for di, dj in ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)):
                other = (i + di, j + dj)
                if other not in open_set:
                    continue
                if di and dj and ((i + di, j) not in open_set or (i, j + dj) not in open_set):
                    continue
                distance = math.sqrt(
                    (GRID * di) ** 2 + (GRID * dj) ** 2 + (self.nodes[other] - self.nodes[node]) ** 2
                )
                wet_fraction = ((node in self.wet) + (other in self.wet)) / 2
                new = t + distance * ((1 - wet_fraction) + wet_fraction / wet_factor)
                if new < distances.get(other, math.inf) - 1e-9:
                    distances[other] = new
                    previous[other] = node
                    heappush(queue, (new, other))
        if goal not in distances:
            raise ValueError(f"Unreachable route from {a} to {b}: {allowed}")
        keys = [goal]
        while keys[-1] != start:
            keys.append(previous[keys[-1]])
        keys.reverse()
        points = [[rounded(i * GRID), rounded(j * GRID), rounded(self.nodes[i, j])] for i, j in keys]
        increments = [math.dist(x, y) for x, y in zip(points, points[1:])]
        wet_length = sum(
            ds * ((i in self.wet) + (j in self.wet)) / 2 for ds, i, j in zip(increments, keys, keys[1:])
        )
        short = [points[0]]
        for u, v, w in zip(points, points[1:], points[2:]):
            if any(abs((v[i] - u[i]) - (w[i] - v[i])) > 1e-5 for i in range(3)):
                short.append(v)
        short.append(points[-1])
        return {
            "length_3d_m": round(sum(increments), 2),
            "wet_m": round(wet_length, 2),
            "weighted_m": round(distances[goal], 3),
            "witness": short,
        }


def slab_range(origin, target, intervals):
    near, far = 0.0, 1.0
    for o, t, (lo, hi) in zip(origin, target, intervals):
        d = t - o
        if abs(d) < 1e-9:
            if o < lo or o > hi:
                return None
            continue
        u, v = sorted(((lo - o) / d, (hi - o) / d))
        near = max(near, u)
        far = min(far, v)
        if near > far + 1e-8:
            return None
    return near if 0 < near < 1 else None


def shelter_witnesses(s, mesh, district, field_pins):
    radius = s["rules"]["clearance_radius_m"]
    height = s["rules"]["standing_height_m"]
    eye = s["rules"]["standing_eye_m"]
    covers = {c["id"]: c for c in s["covers"]}
    entry_covers = {cid for entry in s["entries"] for cid in entry["covers"]}
    if unknown := set(field_pins).difference(entry_covers):
        raise ValueError(f"Unregistered cover in measured shelter pins: {sorted(unknown)}")
    volumes = {
        k: ((b[0], b[2]), (b[1], b[3]), (c["z"], c["z"] + c["size"][2]))
        for k, c in covers.items()
        for b in [box_at(c)]
    }
    records = []
    for entry in s["entries"]:
        x, y, z = entry["center"]
        nx, ny = entry["normal"]
        ox, oy = x - 2.5 * nx, y - 2.5 * ny
        patch = next(
            p
            for p in mesh["floors"]
            if p["owner"] == entry["link"] and box_distance((ox, oy), extent(p)) < 1e-6
        )
        observer = (ox, oy, surface_z(patch, ox, oy) + eye)
        eligible = [
            (i * GRID, j * GRID) for (i, j), owners in district.owners.items() if entry["site"] in owners
        ]
        for cid in entry["covers"]:
            c = covers[cid]
            cx, cy = c["center"]
            # Sculpted fittings can narrow at eye height. Preserve the measured position
            # there; letting the prism pick a closer candidate could expose a shoulder.
            field_pin = tuple(field_pins[cid]) if cid in field_pins else None
            nearest = []
            for px, py in eligible:
                if field_pin is not None and (px, py) != field_pin:
                    continue
                dist = box_distance((px, py), box_at(c))
                forward = (px - cx) * (cx - ox) + (py - cy) * (cy - oy)
                if radius - 1e-8 <= dist <= 2.25 and forward > 0:
                    nearest.append((dist, math.hypot(px - ox, py - oy), px, py))
            for _, __, px, py in sorted(nearest):
                samples = [
                    (
                        px + radius * math.cos(k * math.pi / 4),
                        py + radius * math.sin(k * math.pi / 4),
                        z + h,
                    )
                    for k in range(8)
                    for h in (0.12, 0.95, height)
                ]
                hidden = True
                for target in samples:
                    # The witness must be reachable by an eye ray through this exact aperture first.
                    den = (target[0] - ox) * nx + (target[1] - oy) * ny
                    t = ((x - ox) * nx + (y - oy) * ny) / den if den else 0
                    across = abs(
                        (ox + t * (target[0] - ox) - x) * -ny + (oy + t * (target[1] - oy) - y) * nx
                    )
                    if not (0 < t < 1 and across < entry["width"] / 2):
                        hidden = False
                        break
                    hits = [
                        (v, id)
                        for id, box in volumes.items()
                        if (v := slab_range(observer, target, box)) is not None
                    ]
                    if not hits or min(hits)[1] != cid:
                        hidden = False
                        break
                if hidden:
                    records.append(
                        {
                            "entry": entry["id"],
                            "cover": cid,
                            "observer_eye": [rounded(v) for v in observer],
                            "feet": [px, py, z],
                            "occluded_samples": len(samples),
                        }
                    )
                    break
            else:
                raise ValueError(
                    f"No standing 24-ray shelter for {entry['id']} / {cid}, selected {field_pin}"
                )
    return records


def measure(s, mesh, field_pins):
    rooms = {r["id"]: r for r in s["rooms"]}
    connections = {frozenset((r["from"], r["to"])): r["id"] for r in s["links"]}
    district = SurveyGrid(s, mesh)
    routes = []
    for id, name, rooms_on_route in ITINERARIES:
        allowed = set(rooms_on_route) | {
            connections[frozenset(pair)] for pair in zip(rooms_on_route, rooms_on_route[1:])
        }
        start = rooms[rooms_on_route[0]]["center"]
        goal = rooms[rooms_on_route[-1]]["center"]
        r = district.search(start, goal, allowed, s["rules"]["water_speed_factor"])
        routes.append(
            {
                "id": id,
                "name": name,
                "rooms": rooms_on_route,
                "walk_s": round(r["weighted_m"] / s["rules"]["walk_m_s"], 2),
                **r,
            }
        )
    sluice = {"sluice"}
    xs = [(-23.5, "wet"), (-27, "west dry"), (-19.5, "east dry")]
    water_checks = []
    for x, name in xs:
        a = (x, -13)
        b = (x, -1)
        r = district.search(
            a, b, sluice, s["rules"]["water_speed_factor"], mode="dry" if "dry" in name else "normal"
        )
        samples = [(round(x / GRID), j) for j in range(round(a[1] / GRID), round(b[1] / GRID) + 1)]
        assert all(k in district.nodes for k in samples)
        wet_length = sum(
            GRID * ((i in district.wet) + (j in district.wet)) / 2 for i, j in zip(samples, samples[1:])
        )
        length = math.dist(a, b)
        weighted = length - wet_length + wet_length / s["rules"]["water_speed_factor"]
        water_checks.append(
            {
                "strip": name,
                "centres": [a, b],
                "straight_m": length,
                "straight_wet_m": wet_length,
                "straight_walk_s": round(weighted / s["rules"]["walk_m_s"], 2),
                "fastest_unrestricted_m": r["length_3d_m"],
                "fastest_unrestricted_s": round(r["weighted_m"] / s["rules"]["walk_m_s"], 2),
            }
        )
    bounds = [extent(p) for p in mesh["floors"]]
    world = [
        min(b[0] for b in bounds),
        min(b[1] for b in bounds),
        max(b[2] for b in bounds),
        max(b[3] for b in bounds),
    ]
    grades = []
    for patch in mesh["floors"]:
        if patch["kind"] == "ramp":
            p, q, r, t = patch["vertices"]
            dz_x = (q[2] - p[2]) / (q[0] - p[0])
            dz_y = (t[2] - p[2]) / (t[1] - p[1])
            grades.append({"patch": patch["id"], "percent": round(100 * math.hypot(dz_x, dz_y), 2)})
    surface_area = sum((b[2] - b[0]) * (b[3] - b[1]) for b in bounds)
    return {
        "schema": 1,
        "map": s["id"],
        "grid_step_m": GRID,
        "clearance_radius_m": district.radius,
        "walkable_grid_samples": len(district.nodes),
        "floor_bounds_xy": world,
        "horizontal_floor_m2": rounded(surface_area),
        "floors": len(mesh["floors"]),
        "walls": len(mesh["walls"]),
        "seams": mesh["open_flat_or_ramped_seams"],
        "grades": grades,
        "routes": routes,
        "water_lanes": water_checks,
        "shelter_witnesses": shelter_witnesses(s, mesh, district, field_pins),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    s = json.loads((HERE / "survey.json").read_text())
    g = json.loads((HERE / "geometry.json").read_text())
    register = json.loads((HERE / "shelter-pins.json").read_text())
    if register["map"] != s["id"]:
        raise ValueError("Standing shelter register belongs to another district")
    result = measure(s, g, register["standing_feet_xy_m"])
    emit(HERE / "metrics.json", as_json(result).encode(), args.check)
    for r in result["routes"]:
        print(f"{r['name']:28} {r['length_3d_m']:6.2f} m   {r['walk_s']:5.2f} s")
    print(result["water_lanes"])
    print("Walkable centre samples", result["walkable_grid_samples"])
    print("Steepest", max(result["grades"], key=lambda r: r["percent"]))


if __name__ == "__main__":
    main()
