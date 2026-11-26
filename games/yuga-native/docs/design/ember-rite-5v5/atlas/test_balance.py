"""Cross-check measured doors with exhaustive simple paths on these small district graphs."""
import json
from collections import defaultdict
from itertools import combinations
from math import dist
import unittest

from audit import DRY, HERE, MAPS
from balance import snapshot


def entrance(room, waypoints):
    """Walk outwards until the line intersects an actual side of the rectangular room."""
    x, z = room["xz"]
    w, d = (size / 2 for size in room["size"])
    for (ax, az), (bx, bz) in zip(waypoints, waypoints[1:]):
        if abs(bx - x) <= w and abs(bz - z) <= d:
            continue
        hits = []
        if bx != ax:
            for wall in (x - w, x + w):
                t = (wall - ax) / (bx - ax)
                height = az + (bz - az) * t
                if 0 <= t <= 1 and z - d <= height <= z + d:
                    hits.append((t, (wall, height)))
        if bz != az:
            for wall in (z - d, z + d):
                t = (wall - az) / (bz - az)
                across = ax + (bx - ax) * t
                if 0 <= t <= 1 and x - w <= across <= x + w:
                    hits.append((t, (across, wall)))
        return min(hits)[1]
    raise AssertionError("No exit found in the drawing")


def exhaustive_gap(plan, spawn, site):
    adj = defaultdict(list)
    door = {}
    for e in plan["links"]:
        if e["kind"] not in DRY:
            continue
        a, b = e["from"], e["to"]
        adj[a].append(b)
        adj[b].append(a)
        if site in (a, b):
            points = [plan["nodes"][a]["xz"], *e.get("via", []), plan["nodes"][b]["xz"]]
            other = b if site == a else a
            door[other] = entrance(plan["nodes"][site], points if site == a else points[::-1])
    forbidden = {"atk", "def", "a", "b"} - {spawn, site}
    paths = []

    def visit(route):
        if route[-1] == site:
            paths.append((route[-2], set(route[1:-1])))
            return
        for next_room in adj[route[-1]]:
            if next_room not in route and next_room not in forbidden:
                visit([*route, next_room])

    visit([spawn])
    return max(dist(door[a], door[b]) for (a, rooms_a), (b, rooms_b) in combinations(paths, 2)
               if a != b and rooms_a.isdisjoint(rooms_b))


class DoorChecks(unittest.TestCase):
    def test_thresholds_and_alternate_paths(self):
        output = snapshot()
        for key, measured in zip(MAPS, output["maps"], strict=True):
            plan = json.loads((HERE / "maps" / (key + ".json")).read_text())
            for side, label in (("atk", "attack"), ("def", "defend")):
                for site in ("a", "b"):
                    with self.subTest(district=key, side=side, site=site):
                        distance = exhaustive_gap(plan, side, site)
                        reported = measured["sites"][site][label + "_doors"]
                        self.assertAlmostEqual(distance, reported["distance_m"], places=3)
                        self.assertEqual(distance > output["sena_diameter_m"], reported["beyond_one_disk"])

    def test_every_district_has_dry_retake_with_mid_and_spawns_closed(self):
        output = snapshot()
        for measured in output["maps"]:
            with self.subTest(district=measured["id"]):
                closed = measured["retake_mid_closed_s"]
                self.assertIsNotNone(closed)
                self.assertGreater(output["burn_s"] - output["quench_s"], closed)


if __name__ == "__main__":
    unittest.main()
