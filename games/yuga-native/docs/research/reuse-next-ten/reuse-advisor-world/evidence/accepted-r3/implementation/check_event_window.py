#!/usr/bin/env python3
"""Inspect captured original Rama events; save a fresh bounded JSON receipt."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path

from event_window import sampled_indices
from inspect_trace import inspect


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit("output exists; preserve the prior result")
    trace = json.loads(args.trace.read_text())
    checks = []

    def check(name, ok, **evidence):
        checks.append(dict(name=name, passed=bool(ok), evidence=evidence))

    check("actual source fixture accepted", bool(trace["checks"]) and all(x["passed"] for x in trace["checks"]))
    check("all five actual Rama abilities present", [x["ability"] for x in trace["timelines"]] ==
          ["kodanda", "piercing_dawn", "measured_step", "guardian_circle", "dawn_volley"])
    source_root = Path(__file__).resolve().parents[1]
    sources = json.loads((source_root / "sources.json").read_text())["fetched_files"]
    check("all retained upstream source/license hashes match acquisition pins", bool(sources) and all(
        hashlib.sha256((source_root / source["retained_path"]).read_bytes()).hexdigest() == source["sha256"]
        for source in sources), files=len(sources))
    for timeline in trace["timelines"]:
        events = timeline["events"]
        origin = events[0]["time_s"]
        times = [event["time_s"] - origin for event in events]
        duration = times[-1]
        cycles = [time / duration for time in times]
        expected = list(range(len(events)))
        schedules = {f"{hz}Hz": [1/hz] for hz in [30, 60, 120]}
        schedules["mixed_hitch"] = [1/60, .19, 1/120, .037]
        for label, schedule in schedules.items():
            report = inspect(timeline, schedule)
            seen = report["observed_ordinals"]
            check(timeline["ability"]+" "+label+" retains every actual ordinal once",
                  seen == expected, observed=seen, expected=expected)
        # Repetition is an offline display experiment, not repeated gameplay.
        for hz in [30, 60, 120]:
            cursor = 0.0
            counts = [0] * len(events)
            for _step in range(5000):
                end = min(duration * 3, cursor + 1 / hz)
                for index in sampled_indices(cycles, duration, cursor, end):
                    counts[index] += 1
                cursor = end
                if cursor >= duration * 3:
                    break
            check(timeline["ability"]+f" {hz}Hz three display loops retain each actual ordinal three times",
                  counts == [3] * len(events), counts=counts)
        check(timeline["ability"]+" multi-loop hitch coalesces actual ordinals",
              sampled_indices(cycles, duration, 0, duration * 3.2) == expected)
    # These fixtures are original synthetic values, not upstream game fixtures.
    check("zero-duration clip emits nothing", sampled_indices([0.0], 0, 0, 1) == [])
    check("paused playhead emits nothing", sampled_indices([.25], 1, .25, .25) == [])
    check("paused terminal playhead emits nothing",
          sampled_indices([0, .25, 1], 1, 1, 1, finished=True) == [])
    check("restart emits nothing", sampled_indices([.25], 1, .8, .2) == [])
    check("start and equal-time attachment events preserve order",
          sampled_indices([0, 0, .5], 1, 0, .1) == [0, 1])
    check("half-open adjacent window excludes upper boundary",
          sampled_indices([.25, .5], 1, .25, .5) == [0])
    check("loop wrap catches end and start once",
          sampled_indices([0, .5, .9], 1, .8, 1.1) == [0, 2])
    check("exact non-binary loop endpoint does not refire beginning",
          sampled_indices([0, 1], .4, 1.19, 3 * .4) == [1])
    check("real advance beyond loop endpoint retains beginning",
          sampled_indices([0, 1], .4, 3 * .4, 3 * .4 + 1e-10) == [0])
    check("exact nonloop endpoint is retained",
          sampled_indices([.8, 1], 1, .8, 1, finished=True) == [0, 1])
    check("long hitch is explicitly coalesced once per authored event",
          sampled_indices([0, .5], 1, 0, 3.2) == [0, 1])
    for label, cycles, duration, before, after, finished in [
        ("NaN duration", [0], math.nan, 0, 1, False),
        ("infinite event", [math.inf], 1, 0, 1, False),
        ("boolean clock", [0], 1, False, 1, False),
        ("negative clock", [0], 1, -1, 1, False),
        ("offclip event", [1.1], 1, 0, 1, False),
        ("malformed finish flag", [0], 1, 0, 1, 1),
        ("premature finish flag", [0, 1], 1, 0, .5, True),
        ("late finish flag", [0, 1], 1, .5, 2, True),
        ("normalized clock overflow", [0], 1e-308, 0, 1e308, False),
    ]:
        rejected = False
        try:
            sampled_indices(cycles, duration, before, after, finished=finished)
        except ValueError:
            rejected = True
        check(label+" rejected before sampling", rejected)
    for label in ["duplicate event identity", "reversed trace chronology", "zero schedule step"]:
        changed = copy.deepcopy(trace["timelines"][0])
        schedule = [1/60]
        if label == "duplicate event identity":
            changed["events"][1]["event_seq"] = changed["events"][0]["event_seq"]
        elif label == "reversed trace chronology":
            changed["events"].reverse()
        else:
            schedule = [0]
        rejected = False
        try:
            inspect(changed, schedule)
        except ValueError:
            rejected = True
        check(label+" rejected by inspector", rejected)
    # A deliberately incorrect closed-window reference double-fires a boundary.
    closed_seen = [i for i, c in enumerate([0, .5, 1]) if 0 <= c <= .5]
    closed_seen += [i for i, c in enumerate([0, .5, 1]) if .5 <= c <= 1]
    check("closed-window corruption negative detected", closed_seen != [0, 1, 2])
    result = {"schema": 1, "scope": "Offline inspection only; not gameplay/audio scheduling, not a rendered animation pass",
              "trace_sha256": hashlib.sha256(args.trace.read_bytes()).hexdigest(),
              "implementation_sha256": {name: hashlib.sha256(Path(__file__).with_name(name).read_bytes()).hexdigest()
                                        for name in ["event_window.py", "inspect_trace.py", "check_event_window.py"]},
              "checks": checks, "passed": sum(c["passed"] for c in checks),
              "total": len(checks)}
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps({k: result[k] for k in ["passed", "total", "trace_sha256"]}))
    raise SystemExit(0 if result["passed"] == result["total"] else 1)


if __name__ == "__main__":
    main()
