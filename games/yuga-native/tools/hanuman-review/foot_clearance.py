#!/usr/bin/env python3
"""Measure raw GLB skinned sole heights before game collision, in metres.

Samples the bound vertices of both feet through each exported animation. The
result is a geometric screen for hover/piercing. Native ground and Blender
stage offsets belong to their respective scenes.
"""

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

import numpy as np

from audit_glb import Payload, require, scene_nodes


def transform(node):
    if "matrix" in node:
        return np.array(node["matrix"], dtype=float).reshape(4, 4).T
    rotation = np.array(node.get("rotation", [0, 0, 0, 1]))
    x, y, z, w = rotation / np.linalg.norm(rotation)
    result = np.eye(4)
    result[:3, :3] = (
        (1 - 2*y*y - 2*z*z, 2*x*y - 2*w*z, 2*x*z + 2*w*y),
        (2*x*y + 2*w*z, 1 - 2*x*x - 2*z*z, 2*y*z - 2*w*x),
        (2*x*z - 2*w*y, 2*y*z + 2*w*x, 1 - 2*x*x - 2*y*y),
    )
    result[:3, :3] *= np.array(node.get("scale", [1, 1, 1]))
    result[:3, 3] = node.get("translation", [0, 0, 0])
    return result


def sample(track, when):
    key, times, values, interpolation = track
    right = bisect.bisect_right(times, when)
    if right == 0:
        return values[0]
    left = right - 1
    if right == len(times) or interpolation == "STEP":
        return values[left]
    frac = (when - times[left]) / (times[right] - times[left])
    a, b = values[left], values[right]
    if key == "rotation":
        cosine = float(np.dot(a, b))
        if cosine < 0.0:
            b, cosine = -b, -cosine
        if cosine < .9995:
            theta = math.acos(cosine)
            return (math.sin((1-frac)*theta)*a + math.sin(frac*theta)*b) / math.sin(theta)
    return (1-frac)*a + frac*b


def measure(asset, count):
    payload = Payload(asset)
    doc = payload.document
    roots, visible = scene_nodes(doc)
    nodes, skins = doc["nodes"], doc["skins"]
    require(len(skins) == 1, "expected one hero skin")
    skin = skins[0]
    names = [nodes[i]["name"] for i in skin["joints"]]
    bind_inverse = np.array(payload.accessor(skin["inverseBindMatrices"])).reshape(-1, 4, 4).transpose(0, 2, 1)
    foot_indices = {
        side: [i for i, name in enumerate(names) if name.endswith("." + side) and name.startswith(("foot.", "toe"))]
        for side in ("L", "R")
    }
    per_side = {side: [] for side in foot_indices}
    for i in sorted(visible):
        node = nodes[i]
        if node.get("skin") != 0 or "mesh" not in node:
            continue
        for primitive in doc["meshes"][node["mesh"]]["primitives"]:
            attrs = primitive["attributes"]
            joints = np.array(payload.accessor(attrs["JOINTS_0"]))
            weights = np.array(payload.accessor(attrs["WEIGHTS_0"]))
            points = np.c_[np.array(payload.accessor(attrs["POSITION"])), np.ones(len(joints))]
            for side, indices in foot_indices.items():
                membership = (np.isin(joints, indices) * weights).sum(axis=1)
                selected = (membership >= .6) & (points[:, 1] <= .12)
                per_side[side].append((joints[selected], weights[selected], points[selected]))
    require(all(per_side.values()), "no foot samples")
    feet = {side: tuple(np.concatenate(fields) for fields in zip(*pieces)) for side, pieces in per_side.items()}
    require(all(len(points) for _, _, points in feet.values()), "empty foot sample")

    static = [transform(node) for node in nodes]

    def heights(tracks, when):
        globals_ = {}
        pending = [(index, np.eye(4)) for index in roots]
        while pending:
            index, parent = pending.pop()
            local = static[index]
            if index in tracks:
                changed = {track[0]: sample(track, when) for track in tracks[index]}
                local = transform({**nodes[index], **changed})
            matrix = parent @ local
            globals_[index] = matrix
            pending.extend((child, matrix) for child in nodes[index].get("children", []))
        skin_world = np.array([globals_[i] for i in skin["joints"]]) @ bind_inverse
        return {
            side: float(np.einsum("nkm,nm,nk->n", skin_world[joints, 1], points, weights).min())
            for side, (joints, weights, points) in feet.items()
        }

    result = {"sha256": hashlib.sha256(asset).hexdigest(), "rest_y_m": heights({}, 0),
              "sampled_points": {side: len(points) for side, (_, _, points) in feet.items()}, "clips": {}}
    for animation in doc.get("animations", []):
        tracks = {}
        last_time = 0.0
        for channel in animation["channels"]:
            destination = channel["target"]
            node, path = destination["node"], destination["path"]
            if path not in {"translation", "rotation", "scale"}:
                continue
            sampler = animation["samplers"][channel["sampler"]]
            interpolation = sampler.get("interpolation", "LINEAR")
            require(interpolation in {"LINEAR", "STEP"}, f"unsupported interpolation {interpolation}")
            times = [row[0] for row in payload.accessor(sampler["input"])]
            values = np.array(payload.accessor(sampler["output"]))
            tracks.setdefault(node, []).append((path, times, values, interpolation))
            last_time = max(last_time, times[-1])
        rows = [{"time_s": float(t), **heights(tracks, t)} for t in np.linspace(0, last_time, count)]
        lowest = [min(row["L"], row["R"]) for row in rows]
        result["clips"][animation["name"]] = {"lowest_sole_y_m": [min(lowest), max(lowest)], "samples": rows}
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("asset", type=Path)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--samples", type=int, default=25, choices=range(2, 121), metavar="N")
    args = parser.parse_args()
    if args.report.exists():
        parser.error("report destination already exists")
    result = measure(args.asset.read_bytes(), args.samples)
    with args.report.open("x") as stream:
        json.dump(result, stream, indent=2, allow_nan=False)
        stream.write("\n")


if __name__ == "__main__":
    main()
