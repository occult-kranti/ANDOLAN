"""Measure the Ember Rite design drawings. Run with --check to verify the report."""

import argparse
from collections import defaultdict
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import combinations
import json
from math import dist, hypot, inf, isclose, isfinite
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
MAPS = ("mandala", "lanka", "ayodhya", "kurukshetra")
DRY = {"walk", "ramp"}
WALK_MPS = 5.0
WATER_FACTOR = 0.85
SITE_RADIUS = 3.0
REACH = 1.5
EPS = 1e-7


def require(ok, message):
    if not ok:
        raise ValueError(message)


def numbers(values, count, field):
    require(isinstance(values, (list, tuple)) and len(values) == count, f"{field}: expected {count} numbers")
    require(all(type(v) in (int, float) and isfinite(v) for v in values), f"{field}: non-finite or non-numeric")
    return tuple(values)


def nonempty(value):
    return isinstance(value, str) and bool(value.strip())


def rectangle(obj, field):
    (x, z) = numbers(obj["xz"], 2, field + " position")
    (w, d) = numbers(obj["size"], 2, field + " size")
    require(min(w, d) > 0, f"{field}: empty footprint")
    return (x - w / 2, z - d / 2, x + w / 2, z + d / 2)


def rect_distance(point, box):
    x, z = point
    left, bottom, right, top = box
    return hypot(max(left - x, 0, x - right), max(bottom - z, 0, z - top))


def segment_distance(point, a, b):
    x, z = point
    ax, az = a
    dx, dz = b[0] - ax, b[1] - az
    t = min(1, max(0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz)))
    return hypot(x - ax - t * dx, z - az - t * dz)


def hits_rect(a, b, box):
    # Clip a closed segment to both coordinate slabs; tangency counts as contact.
    enter, leave = 0.0, 1.0
    for start, stop, low, high in zip(a, b, box[:2], box[2:]):
        if start == stop:
            if not low <= start <= high:
                return False
            continue
        t0, t1 = sorted(((low - start) / (stop - start), (high - start) / (stop - start)))
        enter, leave = max(enter, t0), min(leave, t1)
        if enter > leave:
            return False
    return True


@dataclass
class Link:
    start: str
    end: str
    kind: str
    points: list
    width: float
    time: float

    def segments(self):
        return zip(self.points, self.points[1:])


def read_links(plan, bounds):
    nodes = plan["nodes"]
    links = []
    for item in plan["links"]:
        start, end, kind = item["from"], item["to"], item["kind"]
        ref = f"{start}–{end}"
        require(start in nodes and end in nodes and start != end, ref + ": invalid endpoints")
        require(kind in DRY | {"water", "fold"}, ref + ": unknown link kind")
        (width,) = numbers([item["width"]], 1, ref + " width")
        require(width > 0, ref + ": width must be positive")
        points = [nodes[start]["xz"], *item.get("via", []), nodes[end]["xz"]]
        points = [numbers(p, 2, ref + " waypoint") for p in points]
        for x, z in points:
            margin = 0 if kind == "fold" else width / 2
            require(bounds[0] <= x - margin and bounds[1] <= z - margin and
                    x + margin <= bounds[2] and z + margin <= bounds[3], ref + ": corridor outside bounds")
        lengths = [dist(a, b) for a, b in zip(points, points[1:])]
        require(min(lengths) > 0, ref + ": coincident waypoints")
        rise = nodes[end]["y"] - nodes[start]["y"]
        require(kind != "walk" or isclose(rise, 0, abs_tol=EPS), ref + ": walk changes elevation")
        if kind == "fold":
            (time,) = numbers([item["seconds"]], 1, ref + " transition")
            require(isclose(time, 1.5, abs_tol=EPS), ref + ": expected 1.5 s transition")
            turns = item.get("quarter_turns")
            require(type(turns) is int and abs(turns) == 1 and nonempty(item.get("cue")),
                    ref + ": a folded threshold needs a signed quarter-turn and a local cue")
        else:
            require("seconds" not in item, ref + ": traversable links derive time from geometry")
            speed = WALK_MPS * (WATER_FACTOR if kind == "water" else 1)
            time = hypot(sum(lengths), rise) / speed
        links.append(Link(start, end, kind, points, width, time))
    return links


def audit_geometry(plan):
    nodes = plan["nodes"]
    require({"atk", "def", "a", "b", "mid"} <= nodes.keys(), "missing spawn, site or mid")
    bounds = numbers(plan["bounds"], 4, "bounds")
    require(bounds[0] < bounds[2] and bounds[1] < bounds[3], "bounds inverted")
    rooms = []
    for key, node in nodes.items():
        require(nonempty(node["label"]), key + ": empty room label")
        numbers([node["y"]], 1, key + " elevation")
        room = rectangle(node, key)
        require(rect_distance(room[:2], bounds) == rect_distance(room[2:], bounds) == 0, key + ": room outside bounds")
        rooms.append(room)
    require(len({n["label"].casefold() for n in nodes.values()}) == len(nodes), "duplicate room label")
    architecture = plan["architecture"]
    require(architecture.get("node") in nodes.keys() - {"a", "b", "atk", "def"} and
            all(nonempty(architecture.get(key)) for key in ("name", "play", "source_id")),
            "architectural study needs a non-objective host room, a source and a game function")
    (bearing,) = numbers([architecture["axis_deg"]], 1, "architectural bearing")
    require(0 <= bearing < 360, "architectural bearing must be clockwise from north")
    clear_radius = SITE_RADIUS + REACH
    for key in ("a", "b"):
        require(min(nodes[key]["size"]) >= 2 * clear_radius, key + ": edge within objective apron")
    require(dist(nodes["a"]["xz"], nodes["b"]["xz"]) > 2 * clear_radius, "site aprons overlap")

    links = read_links(plan, bounds)
    floors = [link for link in links if link.kind != "fold"]

    def on_floor(point):
        return (any(rect_distance(point, room) <= EPS for room in rooms) or
                any(segment_distance(point, a, b) <= link.width / 2 + EPS
                    for link in floors for a, b in link.segments()))

    covers = []
    errors = []
    for obj in plan["cover"]:
        name = obj["label"]
        box = rectangle(obj, name)
        (height,) = numbers([obj["height"]], 1, name + " height")
        require(height > 0, name + ": cover height must be positive")
        covers.append((name, box))
        x0, z0, x1, z1 = box
        if not all(on_floor((x, z)) for x in (x0, (x0 + x1)/2, x1) for z in (z0, (z0 + z1)/2, z1)):
            errors.append(f"{name}: footprint samples off authored floor")
        for key in ("a", "b"):
            if rect_distance(nodes[key]["xz"], box) < clear_radius - EPS:
                errors.append(f"{name}: inside site {key.upper()} apron")
        for link in floors:
            if any(hits_rect(a, b, box) for a, b in link.segments()):
                errors.append(f"{name}: overlaps {link.start}–{link.end} centreline in plan")
    for obj in plan["artifacts"]:
        require(nonempty(obj["label"]) and nonempty(obj["cue"]) and obj["node"] in nodes, "artifact lacks room or cue")
    for probe in plan["sightlines"]:
        require(nonempty(probe["label"]) and probe["from"] != probe["to"], "empty or zero-length sightline")
        for end in ("from", "to"):
            point = numbers(probe[end], 2, probe["label"] + " " + end)
            if not on_floor(point) or any(rect_distance(point, box) <= EPS for _, box in covers):
                errors.append(f"{probe['label']}: {end} point outside floor or inside cover")
    section = plan["section"]["route"]
    require(len(section) >= 2 and all(key in nodes for key in section), "invalid section")
    physical_pairs = {frozenset((link.start, link.end)) for link in floors}
    require(all(frozenset(pair) in physical_pairs for pair in zip(section, section[1:])), "section skips floor connection")
    require(len({nodes[key]["y"] for key in section}) > 1, "section omits elevation change")
    if errors:
        raise ValueError("\n  ".join(errors))
    return links, covers


def network(links):
    graph = defaultdict(list)
    for link in links:
        for start, end in ((link.start, link.end), (link.end, link.start)):
            graph[start].append((end, link.time, link.kind))
    return graph


def shortest(graph, start, end, blocked=(), omit_edge=None):
    # Retain the link kinds as well as room IDs so a fold parallel to a walk is visible.
    queue = [(0.0, (start,), ())]
    visited = set(blocked)
    while queue:
        time, path, kinds = heappop(queue)
        here = path[-1]
        if here in visited:
            continue
        visited.add(here)
        if here == end:
            return time, path, kinds
        for there, cost, kind in graph[here]:
            if there not in visited and (omit_edge is None or {here, there} != omit_edge):
                heappush(queue, (time + cost, path + (there,), kinds + (kind,)))
    return inf, (), ()


def check_approaches(graph, start, end, excluded, path):
    # For nonadjacent endpoints, two internally disjoint routes exist iff no one
    # interior node separates the endpoints (vertex form of Menger's theorem).
    # Every separator of size one lies on the already-found route.
    if any(next_node == end for next_node, _, _ in graph[start]):
        time, _, _ = shortest(graph, start, end, excluded, {start, end})
        require(isfinite(time), f"{start}→{end}: only the direct dry opening")
        return
    for key in path[1:-1]:
        time, _, _ = shortest(graph, start, end, excluded | {key})
        require(isfinite(time), f"{start}→{end}: every legal dry approach uses {key}")


def format_route(nodes, path, kinds):
    if not path:
        return "—"
    labels = [nodes[path[0]]["label"]]
    for key, kind in zip(path[1:], kinds):
        marker = f" ({kind})" if kind in {"water", "fold"} else ""
        labels.append(nodes[key]["label"] + marker)
    return " → ".join(labels)


def map_report(path):
    plan = json.loads(path.read_text(encoding="utf-8"))
    require(plan["id"] == path.stem, "filename and map id differ")
    links, covers = audit_geometry(plan)
    nodes = plan["nodes"]
    dry_links = [link for link in links if link.kind in DRY]
    dry = network(dry_links)
    all_routes = network(links)
    for key in nodes:
        require(isfinite(shortest(all_routes, "atk", key)[0]), f"{key}: detached from map")
    report = [f"## {plan['title']}", "",
              f"[Drawing inputs](maps/{plan['id']}.json) · [Encounter notes](maps/{plan['id']}.md)", "",
              f"{len(nodes)} rooms and {len(links)} bidirectional links. Dry corridors span "
              f"{min(link.width for link in dry_links):g}–{max(link.width for link in dry_links):g} m in width. "
              f"Authored floor elevations run from {min(n['y'] for n in nodes.values()):g} "
              f"to {max(n['y'] for n in nodes.values()):g} m.", "",
              "| Run | Dry (s) | All links (s) | Fastest dry callouts |",
              "| --- | ---: | ---: | --- |"]
    runs = [(side, goal) for side in ("atk", "def") for goal in ("a", "b", "mid")] + [("a", "b")]
    roles = {"atk":"Attack", "def":"Defend", "a":"A", "b":"B", "mid":"Mid"}
    differences = []
    alternatives = []
    for start, end in runs:
        excluded = {"atk", "def", "a", "b"} - {start, end}
        dry_time, dry_path, dry_kinds = shortest(dry, start, end, excluded)
        all_time, all_path, all_kinds = shortest(all_routes, start, end, excluded)
        opening = start in {"atk", "def"} and end in {"a", "b"}
        require(isfinite(dry_time), f"{start}→{end}: no legal dry route")
        run = f"{roles[start]} → {roles[end]}"
        if opening:
            check_approaches(dry, start, end, excluded, dry_path)
            remaining = excluded | set(dry_path[1:-1])
            omit_direct = {start, end} if len(dry_path) == 2 else None
            second, path2, kinds2 = shortest(dry, start, end, remaining, omit_direct)
            if isfinite(second):
                alternatives.append(f"| {run} | {second:.1f} | {format_route(nodes, path2, kinds2)} |")
            else:
                alternatives.append(f"| {run} | — | Both independent lines require a different first route. |")
        report.append(f"| {run} | {dry_time:.1f} | {all_time:.1f} | {format_route(nodes, dry_path, dry_kinds)} |")
        if all_time < dry_time - EPS:
            differences.append(f"- {run} via {format_route(nodes, all_path, all_kinds)} saves {dry_time - all_time:.1f} s.")
        if (start, end) == ("a", "b"):
            slack = 40 - 3.5 - dry_time
    report += ["", f"After ignition, a defender starting at the opposite site centre has **{slack:.1f} s** "
               "in the model for reaction, fighting and positioning after reserving the fastest dry rotation "
               "and a 3.5 s quench. The carried vessel can be kindled away from the room centre.", ""]
    report += ["| Opening with the fastest dry line closed | Time (s) | Alternative dry callouts |",
               "| --- | ---: | --- |", *alternatives, ""]
    if differences:
        report += ["Fastest runs that use a special crossing", "", *differences, ""]
    # Measure a ford from one dry bank to another. The floor at the middle
    # of a flooded passage need not be reachable in the dry-only graph.
    crossings = [(link.start, link.end, "fold", link.time) for link in links if link.kind == "fold"]
    water = network([link for link in links if link.kind == "water"])
    shores = set(water).intersection(key for key, edges in dry.items() if edges)
    for left, right in combinations(sorted(shores), 2):
        wet_time, _, _ = shortest(water, left, right, shores - {left, right})
        if isfinite(wet_time):
            crossings.append((left, right, "water", wet_time))
    if crossings:
        report += ["| Optional crossing | Kind | Crossing (s) | Fastest dry detour (s) |",
                   "| --- | --- | ---: | ---: |"]
        for left, right, kind, crossing in crossings:
            blocked = {"atk", "def"} - {left, right}
            time, _, _ = shortest(dry, left, right, blocked)
            require(isfinite(time), f"{left}–{right}: no dry alternative for {kind}")
            report.append(f"| {nodes[left]['label']} ↔ {nodes[right]['label']} | {kind} "
                          f"| {crossing:.1f} | {time:.1f} |")
        report.append("")
    report += ["| Shoulder-camera probe | Length in plan (m) | Fixed cover intersected in plan |",
               "| --- | ---: | --- |"]
    for probe in plan["sightlines"]:
        a, b = probe["from"], probe["to"]
        touched = [name for name, box in covers if hits_rect(a, b, box)]
        report.append(f"| {probe['label']} | {dist(a, b):.1f} | {', '.join(touched) or 'None'} |")
    return report


INTRO = """# Route measurements

A map author can repeat these calculations from the checked-in drawings. Times give centre-to-centre travel along route lines at full walking input. They estimate the time budget for deploying, rotating or faking an approach. First sight of an opponent depends on the camera and cover.

- Dry travel includes walking and ramps at 5 m/s. Hanuman uses this rate in the Rust simulation. Rama advances 0.25 m per 20 Hz tick at full input. [Hanuman movement](../../../../../yuga-rust/src/combat.rs) · [Rama movement](../../../../../yuga-rust/src/rama.rs)
- Distances include every authored bend. Between room centres the model assumes a constant grade over the whole route. On each shallow-water link it applies 85% walk speed for the centre-to-centre distance, assuming a wade at every depth. The drawings show level room floors and dry thresholds. An engine blockout will have shorter sloped and submerged portions. Each fold consumes 1.5 s in either direction. Walking approaches to both mouths still count.
- Each of the four spawn-to-site openings on each map has two internally room-disjoint dry paths even with the other spawn and objective closed. Site rotations exclude both spawns. The Mid rows exclude both sites and the opposing spawn. Spawns denote the attacking and defending roles after each side swap. The alternative opening closes every interior room on the fastest dry path and measures the quickest remaining path.
- The 3 m ignition disk and 1.5 m perimeter apron fit within each site room and clear fixed cover. The 4.5 m radius is a level-design clearance target. The Rust experiment puts the vessel at the actual ignition point and tests 1.5 m quench reach. [Round rules](../ROUND_AND_TECH.md) · [Rust interaction](../../../../../yuga-rust/src/ritual.rs)
- The floor check uses room rectangles and swept corridor widths in plan. It samples cover footprints on a 3 × 3 grid, checks physical route centrelines against solid footprints and checks probe endpoints against floor and cover. Water depth, ceilings, slopes at thresholds, corridor overlap, agent radius, visibility and camera clearance need an engine blockout.

The measurements below assume immediate movement, uninterrupted channels and an empty map. Check the marked probes from both shoulders at ground and elevated eye heights. A clear line in plan may still be hidden by a lintel or floor edge. A low screen intersected in plan may hide the caster's feet while exposing the head. Use screenshots from both ends and check a real ray from eye to target and eye to reticle.

From the repository root run `python3 games/yuga-native/docs/design/ember-rite-5v5/atlas/audit.py --check`. Omit `--check` to write the report after an edit."""


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify existing measurements without writing")
    args = parser.parse_args()
    paths = {path.stem: path for path in (HERE / "maps").glob("*.json")}
    order = [*MAPS, *sorted(paths.keys() - set(MAPS))]
    errors = []
    report = [INTRO]
    for key in order:
        try:
            require(key in paths, "missing map file")
            report.extend(["", *map_report(paths[key])])
        except (OSError, ValueError, KeyError, TypeError) as err:
            errors.append(f"{key}: {err}")
    if errors:
        sys.exit("\n".join(errors))
    content = "\n".join(report) + "\n"
    target = HERE / "measurements.md"
    if args.check:
        if not target.is_file() or target.read_text(encoding="utf-8") != content:
            sys.exit("Route measurements have changed. Run audit.py to regenerate measurements.md.")
    else:
        target.write_text(content, encoding="utf-8")
    print(f"Checked {len(order)} maps, {4 * len(order)} spawn-to-site opening pairs and {len(order)} dry site rotations.")


if __name__ == "__main__":
    main()
