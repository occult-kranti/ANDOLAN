"""Measure objective time budgets and whether a single Sena disk can span distinct doors."""
import argparse
from collections import defaultdict, deque
import hashlib
from itertools import combinations
import json
from math import dist, inf, isfinite
from pathlib import Path
import sys

from audit import DRY, HERE, MAPS, WALK_MPS, audit_geometry, network, require, shortest
from ritual_rules import rule_constants

RUST = HERE.parents[4] / "yuga-rust"
RULES = rule_constants()
QUENCH_S = RULES["quench"] / RULES["hz"]
BURN_S = RULES["burn"] / RULES["hz"]
IGNITE_S = RULES["kindle"] / RULES["hz"]
TICK_S = 1 / RULES["hz"]
ROLES = {"atk", "def", "a", "b"}


def approach_point(room, outward):
    """First crossing of the room perimeter when tracing an entry away from its centre."""
    low, high = zip(*[(c - w / 2, c + w / 2) for c, w in zip(room["xz"], room["size"])])
    for p, q in zip(outward, outward[1:]):
        if all(l <= v <= h for v, l, h in zip(q, low, high)):
            continue
        fractions = []
        for start, end, lower, upper in zip(p, q, low, high):
            if end < lower or end > upper:
                boundary = lower if end < lower else upper
                fractions.append((boundary - start) / (end - start))
        t = min(fractions)
        return tuple(start + t * (end - start) for start, end in zip(p, q))
    raise ValueError("Entry never leaves the objective room")


def independent_entries(graph, start, blocked, entrances):
    """Can two room-disjoint paths reach the specified last doors before entering the site?"""
    # Split each room into an entry and an exit, joined by a one-player capacity.
    # The start admits both paths. Each selected door accepts one path at the sink.
    capacity = defaultdict(dict)
    sink = ("sink", "")
    source = ("in", start)

    def arc(a, b, limit):
        capacity[a][b] = limit
        capacity[b].setdefault(a, 0)

    for key, neighbours in graph.items():
        if key in blocked:
            continue
        arc(("in", key), ("out", key), 2 if key == start else 1)
        for neighbour, _, _ in neighbours:
            if neighbour not in blocked:
                arc(("out", key), ("in", neighbour), 1)
    for key in entrances:
        arc(("out", key), sink, 1)

    for _ in range(2):
        parent = {source: None}
        pending = deque([source])
        while pending and sink not in parent:
            node = pending.popleft()
            for neighbour, available in capacity[node].items():
                if available and neighbour not in parent:
                    parent[neighbour] = node
                    pending.append(neighbour)
        if sink not in parent:
            return False
        node = sink
        while node != source:
            previous = parent[node]
            capacity[previous][node] -= 1
            capacity[node][previous] += 1
            node = previous
    return True


def entry_pair(plan, dry, links, side, goal, diameter):
    entry_points = {}
    for link in links:
        if link.kind not in DRY or goal not in (link.start, link.end):
            continue
        other = link.end if goal == link.start else link.start
        points = link.points if goal == link.start else link.points[::-1]
        entry_points[other] = approach_point(plan["nodes"][goal], points)
    blocked = ROLES - {side}
    eligible = []
    for left, right in combinations(sorted(entry_points.keys() - blocked), 2):
        if independent_entries(dry, side, blocked, (left, right)):
            gap = dist(entry_points[left], entry_points[right])
            eligible.append((gap, left, right))
    require(eligible, f"{plan['id']} {side}–{goal} needs two independently reachable dry mouths")
    gap, left, right = max(eligible)
    return {"rooms":[left, right],
            "thresholds_xz_m":[[round(v, 3) for v in entry_points[key]] for key in (left, right)],
            "distance_m":round(gap, 3), "beyond_one_disk":gap > diameter + 1e-7}


def read_map(plan, diameter):
    links, _ = audit_geometry(plan)
    dry = network([link for link in links if link.kind in DRY])
    all_routes = network(links)
    retake, _, _ = shortest(dry, "a", "b", {"atk", "def"})
    any_retake, _, _ = shortest(all_routes, "a", "b", {"atk", "def"})
    via_mid_closed, _, _ = shortest(dry, "a", "b", {"atk", "def", "mid"})
    require(isfinite(retake) and isfinite(any_retake), "Detached sites")
    margin = BURN_S - QUENCH_S - retake
    result = {"id":plan["id"], "title":plan["title"],
              "retake_dry_s":round(retake, 3), "retake_any_s":round(any_retake, 3),
              "retake_margin_s":round(margin, 3),
              "retake_after_late_interrupt_s":round(margin - (QUENCH_S - TICK_S), 3),
              "retake_mid_closed_s":round(via_mid_closed, 3) if via_mid_closed < inf else None,
              "sites":{}}
    for goal in ("a", "b"):
        site = {"label":plan["nodes"][goal]["label"]}
        arrivals = []
        for side, label in (("atk", "attack"), ("def", "defend")):
            t, _, _ = shortest(dry, side, goal, ROLES - {side, goal})
            require(isfinite(t), "Unreachable objective")
            arrivals.append(t)
            site[label + "_dry_s"] = round(t, 3)
            site[label + "_doors"] = entry_pair(plan, dry, links, side, goal, diameter)
        site["defender_lead_s"] = round(arrivals[0] - arrivals[1], 3)
        result["sites"][goal] = site
    return result


def snapshot():
    kit = RUST / "assets/vanara-sena.json"
    radius = json.loads(kit.read_text())["geometry"]["radius_m"]
    rows = []
    for key in MAPS:
        source = HERE / "maps" / (key + ".json")
        raw = source.read_bytes()
        row = read_map(json.loads(raw), radius * 2)
        row["layout_sha256"] = hashlib.sha256(raw).hexdigest()
        rows.append(row)
    return {"schema":1, "basis":"Authored map centreline and site footprint, uninterrupted full-speed travel",
            "walk_mps":WALK_MPS, "ignite_s":IGNITE_S, "quench_s":QUENCH_S, "burn_s":BURN_S,
            "sena_diameter_m":2 * radius, "maps":rows}


def report(data):
    lines = ["# Ember Rite balance measurements", "",
             "Use these figures to decide where to test a split push, late rotation or interrupted quench. "
             "All distances and times come from the authored floorplans. The runner walks at 5 m/s. "
             "The model counts the bent routes, grades, shallow-water allowance and authored fold time. "
             "Opponent decisions, camera peeks and combat delays need human matches. "
             "[Travel model and full routes](measurements.md) · [Hero decisions](../HERO_BALANCE.md)", "",
             "## Time to change sites", "",
             "At the instant of ignition a defender at the other site centre has 40 s. The dry margin is "
             "40 s less dry travel and a successful 3.5 s quench. The last column also deducts one interrupted "
             "quench that lasted 3.45 s, one simulation tick short of completion. Both cases assume immediate "
             "movement, a centre placement, and no extra channel delay. A negative value is a missed deadline. "
             "The closed-mid column removes the room and both spawns. A dash means that this closure severs the dry connection.", "",
             "| Map | Dry A–B | All links | Dry, mid closed | Dry margin | After one late interrupt |",
             "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for row in data["maps"]:
        closed = row["retake_mid_closed_s"]
        closed_text = "—" if closed is None else f"{closed:.1f} s"
        lines.append(f"| {row['title']} | {row['retake_dry_s']:.1f} s | {row['retake_any_s']:.1f} s | "
                     f"{closed_text} | {row['retake_margin_s']:.1f} s | {row['retake_after_late_interrupt_s']:.1f} s |")
    lines += ["", "## Time to set up and space to enter", "",
              "Defender lead equals attacker arrival minus defender arrival at the same site. A positive lead gives "
              "the defender time to set up. For each side, the door column gives the widest pair of threshold points "
              "that two players can reach by dry routes sharing only their spawn and the final objective. The other "
              "spawn and site are closed. Each threshold is where its last centreline enters the rectangular site room. "
              "The search splits each room into an entry and exit with capacity one and sends one unit of flow to each candidate door.", "",
              f"Hanuman’s single Sena field is {data['sena_diameter_m']:g} m across. A separation greater than that "
              "diameter proves a stationary disk cannot cover both threshold centres simultaneously. A smaller separation "
              "only means it might fit. Range, solid walls and the caster’s placement still matter. This test says nothing "
              "about other abilities, standing inside the site, or whether two players clear the corners at the same time.", "",
              "| Map / site | Attack | Defend | Defender lead | Attacker doors | Defender doors |",
              "| --- | ---: | ---: | ---: | --- | --- |"]
    for row in data["maps"]:
        for site in row["sites"].values():
            doors = []
            for side in ("attack", "defend"):
                pair = site[side + "_doors"]
                verdict = "separate" if pair["beyond_one_disk"] else "within diameter"
                doors.append(f"{pair['distance_m']:.1f} m · {verdict}")
            lines.append(f"| {row['title']} / {site['label']} | {site['attack_dry_s']:.1f} s | "
                         f"{site['defend_dry_s']:.1f} s | {site['defender_lead_s']:+.1f} s | {doors[0]} | {doors[1]} |")
    lines += ["","The JSON lists the rooms, exact X/Z thresholds, map content hashes and full comparison precision. "
              "Recompute both files with `python3 balance.py` in this directory, or use `--check` to detect stale output. "
              "[Machine-readable measurements](balance.json) · [Sena’s runtime radius](../../../../../yuga-rust/assets/vanara-sena.json) "
              "· [Round timing and tick order](../../../../../yuga-rust/src/ritual.rs)", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    data = snapshot()
    outputs = {"balance.json":json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n",
               "BALANCE_MATH.md":report(data)}
    for name, content in outputs.items():
        path = HERE / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                sys.exit(f"Outdated {name}. Regenerate with balance.py.")
        else:
            path.write_text(content)
    print("Checked four retake windows and sixteen independent entrance pairs.")


if __name__ == "__main__":
    main()
