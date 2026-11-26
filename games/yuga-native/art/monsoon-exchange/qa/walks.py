"""Spatial checks over measured triangle queries, independent of the map construction code."""

from collections import deque
from math import ceil, cos, dist, floor, hypot, pi, sin

from mesh_io import need


DOWN = (0, 0, -1)
UP = (0, 0, 1)
GRID = 0.75


def surface(scene, x, y, z):
    """Closest supported height around the intended storey, refusing steep faces."""
    for dx, dy in ((0.0, 0.0), (0.0003, 0.0002), (-0.0002, -0.0003)):
        hit = scene.floor.ray((x + dx, y + dy, z + 0.45), DOWN, 0.9)
        if hit and hit[1].z >= 0.76:
            return hit[0].z
    return None


def clearance(scene, x, y, z, rules, *, slack=0.003):
    radius, height = rules["clearance_radius_m"], rules["standing_height_m"]
    # Three points on the vertical axis of a standing capsule. Adjacent centres are
    # 0.25 m apart for the common rig. A near-boundary case gets a finer resample.
    tree = scene.obstacles.tree
    span = height - 2 * radius
    distances = []
    for f in (0, 0.5, 1):
        _, _, idx, d = tree.find_nearest((x, y, z + radius + f * span), radius + 0.20)
        if idx is not None:
            distances.append(d)
    if not distances or min(distances) >= radius + span / 4:
        return True
    if min(distances) < radius - slack:
        return False
    for k in range(1, 20):
        if (
            tree.find_nearest((x, y, z + radius + k / 20 * span), radius - slack)[2]
            is not None
        ):
            return False
    return True


def supported(scene, p, rules, tolerance=0.18):
    actual = surface(scene, *p)
    return (
        actual is not None
        and abs(actual - p[2]) <= tolerance
        and clearance(scene, *p[:2], actual, rules)
    )


def probes(scene, data):
    rules = data["rules"]
    widths = {}
    tracks = {}
    raw = []
    for link in data["links"]:
        max_error, samples, stance = 0, 0, 0
        points = link["points"]
        for seg, (a, b) in enumerate(zip(points, points[1:])):
            dx, dy, dz = (b[k] - a[k] for k in range(3))
            length = hypot(dx, dy)
            need(length > 0, f"Zero-length plan segment in {link['id']}")
            count = max(1, ceil(length / 0.4))
            for i in range(count + 1):
                t = i / count
                x, y = a[0] + t * dx, a[1] + t * dy
                # Each turn occupies a level square one full corridor width across.
                # The remaining distance carries the rise; a straight slope through
                # the centre of a level turn would predict a different floor.
                turn_before = seg > 0 and ((points[seg - 1][0] != a[0]) != (dx != 0))
                turn_after = seg + 2 < len(points) and (
                    (points[seg + 2][0] != b[0]) != (dx != 0)
                )
                start = link["width"] / 2 if turn_before else 0.0
                stop = length - (link["width"] / 2 if turn_after else 0.0)
                z = a[2] + dz * max(
                    0.0, min(1.0, (length * t - start) / (stop - start))
                )
                for offset in (
                    -rules["clearance_radius_m"],
                    0.0,
                    rules["clearance_radius_m"],
                ):
                    px, py = x - offset * dy / length, y + offset * dx / length
                    actual = surface(scene, px, py, z)
                    need(
                        actual is not None,
                        f"{link['id']} unsupported {px:.3f},{py:.3f},{z:.3f}",
                    )
                    err = abs(actual - z)
                    need(
                        err <= 0.15,
                        f"{link['id']} plan/mesh height error {err:.3f} m at {px:.2f},{py:.2f}",
                    )
                    max_error = max(max_error, err)
                    samples += 1
                    raw.append(actual)
                    if offset == 0:
                        need(
                            clearance(scene, x, y, actual, rules),
                            f"{link['id']} standing body hits obstacle at {x:.2f},{y:.2f},{z:.2f}",
                        )
                        stance += 1
        tracks[link["id"]] = {
            "foot_rays": samples,
            "standing_capsules": stance,
            "max_height_delta_m": round(max_error, 4),
        }
    for entry in data["entries"]:
        x, y, z = entry["center"]
        nx, ny = entry["normal"]
        side = entry["width"] / 2 - rules["clearance_radius_m"] - 0.06
        passed = 0
        for along in (-0.8, -0.25, 0, 0.25, 0.8):
            for across in (-side, 0.0, side):
                p = (x + nx * along - ny * across, y + ny * along + nx * across, z)
                need(
                    supported(scene, p, rules, 0.26),
                    f"{entry['id']} obstructed lip at {p}",
                )
                passed += 1
        widths[entry["id"]] = {
            "sampled_usable_span_m": round(2 * side, 3),
            "standing_positions": passed,
        }
    return tracks, widths, raw


def blockers(scene, data):
    covers = {c["id"]: c for c in data["covers"]}
    screens = {}
    for entry in data["entries"]:
        ex, ey, _ = entry["center"]
        nx, ny = entry["normal"]
        ox, oy = ex - 3 * nx, ey - 3 * ny
        floor = scene.floor.ray((ox, oy, 40.0), DOWN, 80.0)
        need(
            floor and clearance(scene, ox, oy, floor[0].z, data["rules"]),
            f"Blocked observer at {entry['id']}",
        )
        eye = (ox, oy, floor[0].z + data["rules"]["standing_eye_m"])
        witnesses = []
        need(
            len(set(entry["covers"])) == 2,
            f"{entry['id']} needs two distinct cover objects",
        )
        for cid in entry["covers"]:
            c = covers[cid]
            cx, cy = c["center"]
            wx, wy, height = c["size"]
            # Put the hip centre a full clearance radius beyond the far corner of
            # the box along the sightline, then search a small arc for legal feet.
            vx, vy = cx - eye[0], cy - eye[1]
            length = hypot(vx, vy)
            vx /= length
            vy /= length
            far = min(
                wx / (2 * abs(vx)) if vx else 1e6, wy / (2 * abs(vy)) if vy else 1e6
            )
            found = None
            for extra in (0.95, 1.15, 1.5, 1.95, 2.4):
                for sideways in (0.0, -0.25, 0.25, -0.5, 0.5):
                    x = cx + vx * (far + extra) - vy * sideways
                    y = cy + vy * (far + extra) + vx * sideways
                    if not supported(scene, (x, y, c["z"]), data["rules"]):
                        continue
                    hit_ids = []
                    # Feet, belly, both shoulders and head top; check the actual
                    # named cover blocks every line from this one external eye.
                    for across, h in (
                        (0.0, 0.18),
                        (0.0, 0.9),
                        (-0.4, 1.4),
                        (0.4, 1.4),
                        (0.0, 1.79),
                    ):
                        p = (x - vy * across, y + vx * across, c["z"] + h)
                        distance = dist(p, eye)
                        direction = tuple((p[i] - eye[i]) / distance for i in range(3))
                        hit = scene.obstacles.ray(eye, direction, distance)
                        hit_ids.append(hit[2] if hit else None)
                    if all(key == cid for key in hit_ids):
                        found = [round(x, 3), round(y, 3), c["z"]]
                        break
                if found is not None:
                    break
            need(
                found is not None,
                f"{entry['id']}: no legal five-ray shelter behind {cid} from {eye}",
            )
            witnesses.append({"cover": cid, "standing_center": found})
        screens[entry["id"]] = {
            "observer": [round(i, 3) for i in eye],
            "shelters": witnesses,
        }
    return screens


def printed_pins(scene, data, pins):
    """Test the actual illustrated standing point against visible cover geometry."""
    observed = {}
    entries = {e["id"]: e for e in data["entries"]}
    rules = data["rules"]
    for pin in pins:
        entry, cid = entries[pin["entry"]], pin["cover"]
        need(
            cid in entry["covers"] and cid not in observed,
            "Wrong or duplicate printed shelter",
        )
        x, y, z = pin["feet"]
        ex, ey, _ = entry["center"]
        nx, ny = entry["normal"]
        ox, oy, declared_eye = pin["observer_eye"]
        floor_hit = scene.floor.ray((ox, oy, 40.0), DOWN, 80.0)
        need(
            floor_hit and supported(scene, (x, y, z), rules),
            "Missing actual standing floor at printed sightline",
        )
        oz = floor_hit[0].z + rules["standing_eye_m"]
        need(
            abs(oz - declared_eye) < 0.002
            and clearance(scene, ox, oy, floor_hit[0].z, rules),
            "Observer eye does not line up with actual floor",
        )
        eye = (ox, oy, oz)
        rays = 0
        for k in range(8):
            px = x + rules["clearance_radius_m"] * cos(k * pi / 4)
            py = y + rules["clearance_radius_m"] * sin(k * pi / 4)
            # Ensure that the line traverses the declared aperture, including its edges.
            dx, dy = px - ox, py - oy
            den = dx * nx + dy * ny
            t = ((ex - ox) * nx + (ey - oy) * ny) / den if den else 0
            lateral = (ox + t * dx - ex) * (-ny) + (oy + t * dy - ey) * nx
            need(
                0 < t < 1 and abs(lateral) < entry["width"] / 2,
                f"Shelter {cid} ray misses its mapped gate",
            )
            for h in (0.12, 0.95, rules["standing_height_m"]):
                dv = (dx, dy, z + h - oz)
                length = dist(dv, (0, 0, 0))
                hit = scene.obstacles.ray(eye, tuple(c / length for c in dv), length)
                need(
                    hit and hit[2] == cid,
                    f"Printed shelter {cid} exposes its {k * 45}° edge at height {h:g} m on the modeled cover",
                )
                rays += 1
        observed[cid] = rays
    need(
        set(observed) == {c for e in entries.values() for c in e["covers"]},
        "Incomplete site-shelter registry",
    )
    return {
        "shelters": len(observed),
        "standing_silhouette_rays": sum(observed.values()),
        "rays_per_shelter": observed,
    }


def objective_ring(scene, data):
    result = {}
    for obj in data["objectives"]:
        x, y, z = obj["center"]
        radius = obj["radius"]
        rules = data["rules"]
        need(radius == rules["kindle_radius_m"], f"{obj['id']} radius mismatch")
        for r in (0.0, rules["quench_reach_m"], radius - 0.05):
            for i in range(24 if r else 1):
                a = 2 * pi * i / 24
                need(
                    supported(scene, (x + cos(a) * r, y + sin(a) * r, z), rules),
                    f"{obj['id']} blocked at r{r} heading {i * 15}°",
                )
        result[obj["room"]] = {
            "center": obj["center"],
            "radii_m": [0.0, rules["quench_reach_m"], radius - 0.05],
            "standing_positions": 49,
        }
    return result


class WalkGrid:
    """Four-neighbour metre-space floor graph from actual triangles and the standing body."""

    def __init__(self, scene, data):
        self.scene = scene
        self.data = data
        xmin, ymin, xmax, ymax = data["bounds"]
        self.cells = {}
        for i in range(ceil(xmin / GRID), floor(xmax / GRID) + 1):
            for j in range(ceil(ymin / GRID), floor(ymax / GRID) + 1):
                x, y = i * GRID, j * GRID
                hit = scene.floor.ray((x, y, 50), DOWN, 100.0)
                if not hit or hit[1].z < 0.76:
                    continue
                z = hit[0].z
                if clearance(scene, x, y, z, data["rules"]):
                    self.cells[i, j] = z
        self.edges = {idx: [] for idx in self.cells}
        for idx, z in self.cells.items():
            i, j = idx
            for nbr in ((i + 1, j), (i, j + 1)):
                if nbr not in self.cells:
                    continue
                nz = self.cells[nbr]
                if abs(nz - z) / GRID > 0.44:
                    continue
                px, py = (i + nbr[0]) * GRID * 0.5, (j + nbr[1]) * GRID * 0.5
                if not supported(scene, (px, py, (z + nz) / 2), data["rules"], 0.1):
                    continue
                self.edges[idx].append(nbr)
                self.edges[nbr].append(idx)

    def closest(self, p):
        a, b, z = p
        i, j = round(a / GRID), round(b / GRID)
        cells = [
            (x, y)
            for x in range(i - 2, i + 3)
            for y in range(j - 2, j + 3)
            if (x, y) in self.cells
        ]
        need(cells, f"No walkable grid cell by {p}")
        result = min(
            cells, key=lambda v: dist(p, (v[0] * GRID, v[1] * GRID, self.cells[v]))
        )
        need(
            dist(p, (result[0] * GRID, result[1] * GRID, self.cells[result])) <= 0.85,
            f"Survey marker unreachable by standing capsule {p}",
        )
        return result

    def closed_gates(self, entries):
        # Mask only a thin band at the physical threshold to close a declared door.
        blocked = set()
        for e in entries:
            x, y, _ = e["center"]
            nx, ny = e["normal"]
            for i, j in self.cells:
                dx, dy = i * GRID - x, j * GRID - y
                if (
                    abs(dx * nx + dy * ny) <= GRID * 0.58
                    and abs(-dx * ny + dy * nx) < e["width"] / 2 + 0.20
                ):
                    blocked.add((i, j))
        return blocked

    def wet(self):
        cells = set()
        for water in self.data["water"]:
            x, y = water["center"]
            w, d = water["size"]
            r = self.data["rules"]["clearance_radius_m"]
            cells.update(
                (i, j)
                for i, j in self.cells
                if abs(i * GRID - x) <= w / 2 + r and abs(j * GRID - y) <= d / 2 + r
            )
        return cells

    def flood(self, start, blocked):
        need(start not in blocked, "Blocked graph origin")
        depth = {start: 0}
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in self.edges[u]:
                if v in blocked or v in depth:
                    continue
                depth[v] = depth[u] + 1
                queue.append(v)
        return depth

    def gates(self):
        data = self.data
        starts = {
            spawn["id"]: self.closest(spawn["center"]) for spawn in data["spawns"]
        }
        goals = {
            site["room"]: self.closest(site["center"]) for site in data["objectives"]
        }
        wet = self.wet()
        seen = {}
        gates = {e["id"]: self.closed_gates([e]) for e in data["entries"]}
        for sid, origin in starts.items():
            base = self.flood(origin, set())
            dry = self.flood(origin, wet)
            need(
                all(g in dry for g in goals.values()),
                f"No wholly dry route from {sid} to both sites",
            )
            need(
                all(any(p in base for p in cells) for cells in gates.values()),
                "Door lip unreachable on native grid",
            )
            seen[sid] = {}
            for site, goal in goals.items():
                doors = [e["id"] for e in data["entries"] if e["site"] == site]
                all_closed = set.union(*(gates[e] for e in doors))
                none = self.flood(origin, all_closed)
                need(
                    goal not in none,
                    f"{site} stays accessible from {sid} with every surveyed door shut; undeclared opening",
                )
                alternatives = {}
                for door in doors:
                    closed = set.union(set(), *(gates[e] for e in doors if e != door))
                    reachable = self.flood(origin, closed)
                    need(
                        goal in reachable,
                        f"{sid} cannot reach {site} using {door} as the sole open threshold",
                    )
                    alternatives[door] = round(reachable[goal] * GRID, 2)
                seen[sid][site] = {
                    "open_grid_length_m": round(base[goal] * GRID, 2),
                    "dry_grid_length_m": round(dry[goal] * GRID, 2),
                    "sole_open_gate_grid_lengths_m": alternatives,
                    "reachable_when_all_site_gates_closed": False,
                }
        return {
            "grid_step_m": GRID,
            "standing_cells": len(self.cells),
            "accepted_orthogonal_edges": sum(map(len, self.edges.values())) // 2,
            "wet_or_edge_cells_removed_for_dry_routes": len(wet),
            "routes": seen,
        }
