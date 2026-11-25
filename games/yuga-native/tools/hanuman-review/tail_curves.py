#!/usr/bin/env python3
"""Audit the exported tail chain and independently compare its take curves."""

import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
from pathlib import Path

from audit_glb import Payload, item, require, scene_nodes


def angle(a, b):
    n1 = math.sqrt(sum(v * v for v in a))
    n2 = math.sqrt(sum(v * v for v in b))
    dot = sum(x * y for x, y in zip(a, b, strict=True)) / (n1 * n2)
    return math.degrees(2.0 * math.acos(min(1.0, abs(dot))))


def audit(raw):
    payload = Payload(raw)
    doc = payload.document
    _, visible = scene_nodes(doc)
    nodes = doc["nodes"]
    require(len(doc["skins"]) == 1, "one skinned rig expected")
    joint_index = doc["skins"][0]["joints"]
    joint_name = [item(nodes, index)["name"] for index in joint_index]
    all_parents = {child: i for i in visible for child in nodes[i].get("children", [])}
    chain_names = sorted(name for name in joint_name if name.startswith("tail_") and name.removeprefix("tail_").isdigit())
    expected = [f"tail_{i:02}" for i in range(1, len(chain_names) + 1)]
    require(chain_names == expected and len(expected) >= 2, "expected consecutive tail bone names")
    chain_nodes = [joint_index[joint_name.index(name)] for name in chain_names]
    chain_parent_names = [nodes[all_parents[index]]["name"] for index in chain_nodes]
    require(chain_parent_names[0] == "spine05" and chain_parent_names[1:] == chain_names[:-1], "incorrect tail hierarchy")
    tip = next((i for i in visible if nodes[i].get("name") == "tail_tip"), None)
    require(tip is not None and all_parents[tip] == chain_nodes[-1], "tail tip is not on terminal joint")

    vertices = Counter()
    max_weight = Counter()
    blends = Counter()
    for i in visible:
        node = nodes[i]
        if node.get("skin") != 0 or "mesh" not in node:
            continue
        for primitive in item(doc["meshes"], node["mesh"])["primitives"]:
            attrs = primitive["attributes"]
            for indices, weights in zip(payload.accessor(attrs["JOINTS_0"]), payload.accessor(attrs["WEIGHTS_0"]), strict=True):
                members = set()
                for j, w in zip(indices, weights, strict=True):
                    name = item(joint_name, j)
                    if w <= .001 or name not in chain_names:
                        continue
                    vertices[name] += 1
                    max_weight[name] = max(max_weight[name], w)
                    members.add(name)
                for a, b in itertools.combinations(sorted(members), 2):
                    require(chain_names.index(b) - chain_names.index(a) == 1, "nonadjacent tail bone blending")
                    blends[f"{a}/{b}"] += 1
    require(all(vertices[name] > 0 and max_weight[name] > .75 for name in chain_names), "unweighted or effectively inactive tail joint")
    require(len(blends) == len(chain_names) - 1, "a tail seam has no shared weights")

    motions = {}
    root_motion = {}
    all_curves = {}
    for take in doc["animations"]:
        take_name = take["name"]
        curves = {}
        rows = {}
        root_travel = 0.0
        for channel in take["channels"]:
            target = channel["target"]
            name = nodes[target["node"]].get("name", "")
            path = target["path"]
            if name not in chain_names and not (name == "root" and path == "translation"):
                continue
            sampler = item(take["samplers"], channel["sampler"])
            times = [x[0] for x in payload.accessor(sampler["input"])]
            values = payload.accessor(sampler["output"])
            require(len(times) == len(values) and all(a < b for a, b in zip(times, times[1:])), "unexpected baked animation format")
            if name == "root":
                root_travel = max(root_travel, max(math.dist(v, values[0]) for v in values))
                continue
            curves[f"{name}/{path}"] = [times, values, sampler.get("interpolation", "LINEAR")]
            if path == "rotation":
                require(all(abs(math.sqrt(sum(q * q for q in value)) - 1.0) < .001 for value in values), "non-unit tail quaternion")
                rows[name] = {
                    "keys": len(times),
                    "start_relative_max_deg": max(angle(values[0], v) for v in values),
                    "largest_key_step_deg": max(angle(a, b) for a, b in zip(values, values[1:])),
                    "loop_end_delta_deg": angle(values[0], values[-1]),
                }
        require(set(rows) == set(chain_names), "one take lacks a tail rotation track")
        require(all(v['start_relative_max_deg'] > .1 for v in rows.values()), "inert joint curve")
        motions[take_name] = rows
        root_motion[take_name] = root_travel
        all_curves[take_name] = curves
    require(motions and all(travel < 1e-6 for travel in root_motion.values()), "unexpected root motion")
    curve_sha = hashlib.sha256(json.dumps(all_curves, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return {
        "sha256": hashlib.sha256(raw).hexdigest(), "tail_curve_sha256": curve_sha,
        "joints": chain_names, "parents": chain_parent_names, "tip_parent": chain_names[-1],
        "weighted_vertices": dict(vertices), "largest_weights": dict(max_weight), "adjacent_blend_vertices": dict(blends),
        "animations": motions, "root_travel_m": root_motion,
        "scope": "Exported local curves and skin groups. Secondary response and rendered appearance are separate."
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--compare", type=Path)
    args = parser.parse_args()
    result = audit(args.asset.read_bytes())
    if args.compare:
        reference = audit(args.compare.read_bytes())
        result["comparison"] = {
            "asset_sha256": reference["sha256"],
            "tail_curves_exact": result["tail_curve_sha256"] == reference["tail_curve_sha256"],
            "weights_counts_equal": reference["weighted_vertices"] == result["weighted_vertices"],
        }
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: result[k] for k in ("sha256", "joints", "weighted_vertices", "adjacent_blend_vertices")}))


if __name__ == "__main__":
    main()
