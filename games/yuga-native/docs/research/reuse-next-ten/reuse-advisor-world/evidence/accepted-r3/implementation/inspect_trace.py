#!/usr/bin/env python3
"""Create an offline playback-window report from the owned Godot event fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

from event_window import sampled_indices


def inspect(timeline: dict, schedule: list[float]) -> dict:
    """Resample recorded events; the simulation is never advanced here."""
    if not schedule or any(type(dt) not in (int, float) or
                           not math.isfinite(dt) or dt <= 0 for dt in schedule):
        raise ValueError("schedule requires positive finite steps")
    events = timeline["events"]
    if len(events) < 2:
        raise ValueError("a trace needs begin and terminal events")
    times = [event["time_s"] for event in events]
    if any(type(t) not in (int, float) or not math.isfinite(t) for t in times):
        raise ValueError("trace timestamps must be finite numbers")
    if times != sorted(times) or times[0] < 0 or times[-1] <= times[0]:
        raise ValueError("trace chronology must advance monotonically")
    identities = [(e["generation"], e["event_seq"]) for e in events]
    if len(set(identities)) != len(events):
        raise ValueError("trace contains duplicate event identities")
    origin = times[0]
    duration = times[-1] - origin
    cycles = [(time - origin) / duration for time in times]
    cursor = 0.0
    seen = []
    windows = []
    while cursor < duration:
        if len(windows) >= 5000:
            raise ValueError("inspection exceeds 5000-window bound")
        end = min(duration, cursor + schedule[len(windows) % len(schedule)])
        if end <= cursor:
            raise ValueError("schedule does not advance the playhead")
        ordinals = sampled_indices(cycles, duration, cursor, end,
                                   finished=end == duration)
        windows.append({"previous_s": cursor, "current_s": end,
                        "finished": end == duration, "ordinals": ordinals})
        seen.extend(ordinals)
        cursor = end
    return {"ability": timeline["ability"], "source_origin_s": origin,
            "duration_s": duration, "schedule_s": schedule,
            "event_count": len(events), "windows": windows,
            "observed_ordinals": seen,
            "each_ordinal_once": seen == list(range(len(events))),
            "event_table": [{"ordinal": i, **event} for i, event in enumerate(events)]}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--hz", type=int, choices=(30, 60, 120), default=60)
    parser.add_argument("--mixed-hitch", action="store_true",
                        help="repeat 1/hz, 190 ms, 1/120 s, 37 ms display steps")
    args = parser.parse_args()
    trace = json.loads(args.trace.read_text())
    if not trace.get("checks") or not all(c["passed"] for c in trace["checks"]):
        raise SystemExit("source capture failed its checks")
    schedule = [1 / args.hz, .19, 1 / 120, .037] if args.mixed_hitch else [1 / args.hz]
    reports = [inspect(timeline, schedule) for timeline in trace["timelines"]]
    result = {"schema": 1, "scope": "Offline inspection; 20 Hz source simulation is unchanged",
              "trace_sha256": hashlib.sha256(args.trace.read_bytes()).hexdigest(),
              "policy": "source order; half-open windows; closed final endpoint; multi-loop hitches coalesce",
              "timelines": reports}
    with args.output.open("x") as output:
        output.write(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"abilities": len(reports), "events": sum(r["event_count"] for r in reports),
                      "all_retained_once": all(r["each_ordinal_once"] for r in reports)}))
    raise SystemExit(0 if all(r["each_ordinal_once"] for r in reports) else 1)


if __name__ == "__main__":
    main()
