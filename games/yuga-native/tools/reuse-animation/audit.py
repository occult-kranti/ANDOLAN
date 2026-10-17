#!/usr/bin/env python3
"""Offline key-reduction proposal; writes fresh external JSON, never a game asset.

Hemisphere alignment and RDP selection adapted from ValveResourceFormat, MIT.
See NOTICE.md. Extraction, admission, dense comparison and reporting are YUGA code.
"""
from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
from pathlib import Path

UPSTREAM_COMMIT = "b94b74c5417eceaf0f7ec1ad5bed5ec0bccc32e1"
UPSTREAM_PATH = "ValveResourceFormat/IO/Gltf/GltfModelExporter.Anim.cs"


def norm(value):
    return math.sqrt(sum(x * x for x in value))


def normalize(value):
    length = norm(value)
    if not math.isfinite(length) or length < 1e-12:
        raise ValueError("Non-finite or zero quaternion")
    return tuple(x / length for x in value)


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def lerp(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def align_hemispheres(values):
    result = [normalize(v) for v in values]
    for index in range(1, len(result)):
        if dot(result[index - 1], result[index]) < 0:
            result[index] = tuple(-x for x in result[index])
    return result


def nlerp(a, b, amount):
    if dot(a, b) < 0:
        b = tuple(-x for x in b)
    return normalize(lerp(a, b, amount))


def slerp(a, b, amount):
    cosine = dot(a, b)
    if cosine < 0:
        b = tuple(-x for x in b)
        cosine = -cosine
    cosine = min(1.0, max(-1.0, cosine))
    if cosine > 0.999999:
        return nlerp(a, b, amount)
    angle = math.acos(cosine)
    denominator = math.sin(angle)
    first = math.sin((1 - amount) * angle) / denominator
    last = math.sin(amount * angle) / denominator
    return normalize(tuple(first * x + last * y for x, y in zip(a, b)))


def angular_error(a, b):
    a, b = normalize(a), normalize(b)
    if dot(a, b) < 0:
        b = tuple(-x for x in b)
    # Stable for tiny angles where acos(dot) loses precision.
    return 4 * math.atan2(norm(tuple(x-y for x, y in zip(a, b))),
                         norm(tuple(x+y for x, y in zip(a, b))))


def position_error(a, b):
    return norm(tuple(x-y for x, y in zip(a, b)))


def rotation_interpolation_error(a, b, amount, actual):
    return max(angular_error(slerp(a, b, amount), actual),
               angular_error(nlerp(a, b, amount), actual))


def reduce_keys(times, values, tolerance, error):
    """VRF RDP adaptation; YUGA deliberately retains both existing endpoints."""
    if not values:
        raise ValueError("Empty channel")
    keep = {0, len(values) - 1}
    segments = [(0, len(values) - 1)]
    while segments:
        start, end = segments.pop()
        if end <= start + 1:
            continue
        duration = times[end] - times[start]
        if duration <= 0:
            raise ValueError("Non-increasing key times")
        worst, worst_error = None, tolerance
        for index in range(start + 1, end):
            amount = (times[index] - times[start]) / duration
            current = error(values[start], values[end], amount, values[index])
            if current > worst_error:
                worst, worst_error = index, current
        if worst is not None:
            keep.add(worst)
            segments.extend([(start, worst), (worst, end)])
    return sorted(keep)


def sample(times, values, time, interpolation):
    if time <= times[0]:
        return values[0]
    if time >= times[-1]:
        return values[-1]
    index = bisect.bisect_right(times, time) - 1
    amount = (time - times[index]) / (times[index+1] - times[index])
    return interpolation(values[index], values[index+1], amount)


def admit_track(track, length):
    if track["kind"] not in {"rotation", "position"}:
        raise ValueError("Only rotation/position channels are supported")
    if track["interpolation"] != 1 or not track["enabled"]:
        raise ValueError("Only enabled linear channels are supported")
    times, values, transitions = track["times"], track["values"], track["transitions"]
    if not times or len(times) != len(values) or len(times) != len(transitions):
        raise ValueError("Mismatched or empty channel arrays")
    if any(not math.isfinite(x) for x in times) or any(a >= b for a,b in zip(times,times[1:])):
        raise ValueError("Key times must be finite and strictly increasing")
    if times[0] < 0 or times[-1] > length + 1e-6:
        raise ValueError("Key lies outside clip duration")
    if any(x != 1 for x in transitions):
        raise ValueError("Nonlinear key transitions need a different adapter")
    width = 4 if track["kind"] == "rotation" else 3
    if any(len(v) != width or any(not math.isfinite(x) for x in v) for v in values):
        raise ValueError("Invalid channel dimensions or non-finite values")
    if track["kind"] == "rotation" and any(abs(norm(v)-1) > 1e-4 for v in values):
        raise ValueError("Quaternion exceeds admitted normalization drift")
    # Complete endpoint coverage or a constant single-key channel makes the
    # loop seam explicit; partial loop spans are intentionally not guessed.
    if len(times) > 1 and (abs(times[0]) > 1e-7 or abs(times[-1]-length) > 1e-6):
        raise ValueError("Multi-key channels must cover both clip endpoints")


def audit_track(track, length, rotation_tolerance, position_tolerance, subdivisions):
    admit_track(track, length)
    rotation = track["kind"] == "rotation"
    times = track["times"]
    values = align_hemispheres(track["values"]) if rotation else track["values"]
    tolerance = rotation_tolerance if rotation else position_tolerance
    error = rotation_interpolation_error if rotation else lambda a,b,t,v: position_error(lerp(a,b,t),v)
    # A conservative half-budget leaves room for inter-key interpolation.
    kept = reduce_keys(times, values, tolerance * 0.5, error)
    probes = {0.0, length}
    for index in range(len(times)-1):
        for part in range(subdivisions+1):
            probes.add(times[index] + (times[index+1]-times[index]) * part / subdivisions)
    probes.update(times)
    initial_key_count = len(kept)
    # Key-only tests can miss NLERP curvature between two original keys, even
    # when every original sampled quaternion lies on an exact SLERP arc.
    # Restore both source neighbors of the worst dense probe until it passes.
    while True:
        candidate_times = [times[i] for i in kept]
        candidate_values = [values[i] for i in kept]
        maximum_slerp = maximum_nlerp = worst_error = 0.0
        worst_time = None
        for time in sorted(probes):
            first = slerp if rotation else lerp
            distance = angular_error if rotation else position_error
            expected = sample(times, values, time, first)
            proposed = sample(candidate_times, candidate_values, time, first)
            first_error = distance(expected, proposed)
            maximum_slerp = max(maximum_slerp, first_error)
            second_error = 0.0
            if rotation:
                expected = sample(times, values, time, nlerp)
                proposed = sample(candidate_times, candidate_values, time, nlerp)
                second_error = angular_error(expected, proposed)
                maximum_nlerp = max(maximum_nlerp, second_error)
            current_error = max(first_error, second_error)
            if current_error > worst_error:
                worst_error, worst_time = current_error, time
        if worst_error <= tolerance + 1e-12:
            break
        interval = max(0, min(len(times)-2, bisect.bisect_right(times, worst_time)-1))
        refined = sorted(set(kept) | {interval,interval+1})
        if refined == kept:
            raise ValueError("Dense refinement could not reduce an observed error")
        kept = refined
    distance = angular_error if rotation else position_error
    source_seam = distance(values[0], values[-1])
    candidate_seam = distance(candidate_values[0], candidate_values[-1])
    passed = max(maximum_slerp, maximum_nlerp) <= tolerance + 1e-12
    proposal = {key: value for key,value in track.items() if key not in {"times","values","transitions"}}
    proposal.update(times=candidate_times, values=candidate_values, transitions=[1.0]*len(kept))
    receipt = {"index": track["index"], "path": track["path"], "kind":track["kind"],
               "input_keys":len(times), "proposed_keys":len(kept), "probes":len(probes),
               "keys_restored_by_dense_checks":len(kept)-initial_key_count,
               "max_slerp_or_position_error":maximum_slerp,
               "max_nlerp_error":maximum_nlerp, "error_unit":"radians" if rotation else "meters",
               "source_endpoint_seam":source_seam, "candidate_endpoint_seam":candidate_seam,
               "endpoint_indices_retained":kept[0] == 0 and kept[-1] == len(times)-1,
               "passed_sampled_tolerance":passed}
    return proposal, receipt


def audit(data, rotation_tolerance, position_tolerance, subdivisions):
    if data.get("schema") != 1 or not data.get("clips"):
        raise ValueError("Unsupported/empty extraction")
    if any(not math.isfinite(x) or x <= 0 for x in (rotation_tolerance,position_tolerance)):
        raise ValueError("Tolerances must be finite and positive")
    if not 2 <= subdivisions <= 64:
        raise ValueError("Subdivisions must be between 2 and 64")
    candidates, receipts = [], []
    names = set()
    for clip in data["clips"]:
        if clip["name"] in names or not math.isfinite(clip["length"]) or clip["length"] <= 0:
            raise ValueError("Duplicate clip or invalid duration")
        names.add(clip["name"])
        if clip["loop_mode"] not in {0,1}:
            raise ValueError("Only non-looping or linear-loop clips supported")
        proposed, results = [], []
        for track in clip["tracks"]:
            candidate, result = audit_track(track, clip["length"], rotation_tolerance, position_tolerance, subdivisions)
            proposed.append(candidate); results.append(result)
        candidates.append({**clip,"tracks":proposed})
        receipts.append({"name":clip["name"],"length":clip["length"],"loop_mode":clip["loop_mode"],"tracks":results})
    rows = [track for clip in receipts for track in clip["tracks"]]
    before = sum(row["input_keys"] for row in rows)
    after = sum(row["proposed_keys"] for row in rows)
    report = {"schema":1,"input_sha256":data["input_sha256"],"engine":data.get("engine"),
              "upstream_commit":UPSTREAM_COMMIT,"upstream_path":UPSTREAM_PATH,
              "clips":receipts,"clip_count":len(receipts),"track_count":len(rows),
              "input_keys":before,"proposed_keys":after,"reduction_fraction":1-after/before,
              "rotation_tolerance_radians":rotation_tolerance,"position_tolerance_m":position_tolerance,
              "subdivisions_per_source_interval":subdivisions,
              "probe_count":sum(row["probes"] for row in rows),
              "passed_sampled_tolerance":all(row["passed_sampled_tolerance"] for row in rows),
              "scope":"Offline numerical JSON proposal; finite probes, not continuous proof, Godot candidate playback, contact, event, visual or performance acceptance.",
              "runtime_asset_changed":False}
    return {"schema":1,"source_sha256":data["input_sha256"],"clips":candidates,"runtime_ready":False}, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True,help="JSON from export-library.gd")
    parser.add_argument("--output",type=Path,required=True,help="New directory outside repository")
    parser.add_argument("--rotation-degrees",type=float,default=0.01)
    parser.add_argument("--position-m",type=float,default=1e-5)
    parser.add_argument("--subdivisions",type=int,default=8)
    args = parser.parse_args()
    output = args.output.resolve()
    repository = Path(__file__).resolve().parents[4]
    if output == repository or repository in output.parents or output.exists():
        parser.error("Output must be a fresh directory outside the repository")
    raw = args.input.read_bytes()
    candidate, report = audit(json.loads(raw), math.radians(args.rotation_degrees),args.position_m,args.subdivisions)
    report["extraction_sha256"] = hashlib.sha256(raw).hexdigest()
    report["audit_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    output.mkdir(parents=True,exist_ok=False)
    for name, value in [("candidate.json",candidate),("audit.json",report)]:
        with (output/name).open("x") as file:
            json.dump(value,file,indent=2,allow_nan=False);file.write("\n")
    print(json.dumps({key:report[key] for key in ["clip_count","track_count","input_keys","proposed_keys","reduction_fraction","probe_count","passed_sampled_tolerance","runtime_asset_changed"]}))
    return 0 if report["passed_sampled_tolerance"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
