#!/usr/bin/env python3
"""Join observed Rama receivers/sockets without inventing absent acknowledgements.

Playback grouping reuses the already-qualified MIT Source 2 Viewer adaptation.
This tool is offline inspection; it never dispatches gameplay or audio events.
"""
from __future__ import annotations

import argparse
import bisect
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys

NATIVE = Path(__file__).resolve().parents[2]
PRIOR = NATIVE / "docs/research/reuse-next-ten/reuse-advisor-world/experiment"
sys.path.insert(0, str(PRIOR))
from inspect_trace import inspect as inspect_event_windows  # noqa: E402

SOCKETS = ("bow_grip", "draw_hand", "string_nock", "arrow_muzzle")
MAX_SAFE_INTEGER = 2**53 - 1


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def integer(value, minimum=0):
    return finite_number(value) and minimum <= value <= MAX_SAFE_INTEGER and int(value) == value


def vector(value):
    return isinstance(value, list) and len(value) == 3 and all(finite_number(v) for v in value)


def transform(value):
    return (isinstance(value, dict) and vector(value.get("position")) and
            isinstance(value.get("basis"), list) and len(value["basis"]) == 3 and
            all(vector(axis) for axis in value["basis"]))


def read_trace(path: Path):
    raw = path.read_bytes()
    data = gzip.decompress(raw) if path.suffix == ".gz" else raw
    return json.loads(data), hashlib.sha256(raw).hexdigest(), hashlib.sha256(data).hexdigest()


def inspect(trace: dict, display_hz: int = 60) -> dict:
    """Return explicit findings and original observation rows; never repair them."""
    if display_hz not in (30, 60, 120):
        raise ValueError("display_hz must be 30, 60 or 120")
    if not isinstance(trace, dict) or type(trace.get("schema")) is not int or trace["schema"] != 1:
        raise ValueError("schema 1 capture required")
    timelines = trace.get("timelines")
    if not isinstance(timelines, list) or not timelines or len(timelines) > 30:
        raise ValueError("capture requires 1..30 timelines")
    findings, summaries = [], []

    def issue(code, timeline, ordinal=None, detail=None):
        findings.append({"code": code, "timeline": timeline, "record_ordinal": ordinal,
                         "detail": detail})

    capture_checks = trace.get("checks")
    if (not isinstance(capture_checks, list) or not capture_checks or
            not all(isinstance(c, dict) and c.get("passed") is True for c in capture_checks)):
        issue("CAPTURE_CHECK_FAILED_OR_MISSING", None)
    if trace.get("source_pins") != trace.get("source_after") or not trace.get("source_pins"):
        issue("SOURCE_CHANGED_OR_UNPINNED", None)
    if trace.get("simulation_hz") != 20:
        issue("OWNER_RATE_MISMATCH", None)

    for timeline_index, timeline in enumerate(timelines):
        if not isinstance(timeline, dict):
            raise ValueError("timeline must be an object")
        records, frames = timeline.get("events"), timeline.get("frames")
        if not isinstance(records, list) or not 1 <= len(records) <= 4096:
            raise ValueError("timeline requires 1..4096 records")
        if not isinstance(frames, list) or len(frames) > 3000:
            raise ValueError("timeline frame bound exceeded")
        previous_generation, watermark, previous_time = -1, -1, -1.0
        seen = set()
        groups, observations = [], []
        frame_times = [frame.get("capture_clock_s") if isinstance(frame, dict) else None for frame in frames]
        frames_valid = (bool(frame_times) and all(finite_number(t) for t in frame_times) and
                        frame_times == sorted(frame_times) and len(set(frame_times)) == len(frame_times))
        if not frames_valid:
            issue("FRAME_CLOCK_INVALID_OR_MISSING", timeline_index)
        for frame_ordinal, frame in enumerate(frames):
            if not isinstance(frame, dict):
                issue("FRAME_INVALID", timeline_index, detail=frame_ordinal)
                continue
            sockets = frame.get("sockets", {})
            if not isinstance(sockets, dict) or not all(transform(sockets.get(name)) for name in SOCKETS):
                issue("FRAME_SOCKET_MISSING_OR_NONFINITE", timeline_index, detail=frame_ordinal)
            if frame.get("motion", {}).get("finite") is not True or frame.get("effects", {}).get("finite") is not True:
                issue("FRAME_PRESENTATION_NONFINITE", timeline_index, detail=frame_ordinal)

        for ordinal, record in enumerate(records):
            if not isinstance(record, dict) or not isinstance(record.get("event"), dict):
                issue("EVENT_MISSING", timeline_index, ordinal)
                continue
            event = record["event"]
            generation, seq = event.get("generation"), event.get("event_seq")
            if not integer(generation) or not integer(seq, 1):
                issue("IDENTITY_INVALID", timeline_index, ordinal)
                continue
            key = (int(generation), int(seq))
            expected = list(key)
            if record.get("identity") != expected:
                issue("RECORD_IDENTITY_MISMATCH", timeline_index, ordinal)
            if key in seen:
                issue("DUPLICATE_EVENT_IDENTITY", timeline_index, ordinal)
            seen.add(key)
            if generation < previous_generation or generation == previous_generation and seq <= watermark:
                issue("STALE_EVENT_IDENTITY", timeline_index, ordinal)
            if generation == previous_generation and seq > watermark + 1:
                issue("MISSING_EVENT_SEQUENCE", timeline_index, ordinal,
                      {"expected": watermark + 1, "observed": seq})
            if generation != previous_generation:
                if event.get("kind") not in ("reset", "begin"):
                    issue("GENERATION_WITHOUT_BOUNDARY", timeline_index, ordinal)
                if seq != 1:
                    issue("GENERATION_FIRST_EVENT_MISSING", timeline_index, ordinal)
                groups.append({"generation": generation, "records": [], "valid_clock": True})
                previous_time = -1.0
            previous_generation, watermark = generation, seq
            event_time = event.get("time_s")
            if not finite_number(event_time) or event_time < 0 or event_time < previous_time:
                issue("EVENT_CLOCK_REVERSED_OR_INVALID", timeline_index, ordinal)
                groups[-1]["valid_clock"] = False
            else:
                previous_time = event_time
            groups[-1]["records"].append((ordinal, record))

            for phase in ("sockets_before_motion_event", "sockets_after_motion_event"):
                sockets = record.get(phase)
                if not isinstance(sockets, dict):
                    issue("SOCKET_SAMPLE_MISSING", timeline_index, ordinal, phase)
                    continue
                for socket in SOCKETS:
                    if socket not in sockets:
                        issue("SOCKET_MISSING", timeline_index, ordinal, {"phase": phase, "socket": socket})
                    elif not transform(sockets[socket]):
                        issue("SOCKET_NONFINITE_OR_MALFORMED", timeline_index, ordinal, {"phase": phase, "socket": socket})
            if record.get("socket_observed_for") != expected:
                issue("SOCKET_IDENTITY_MISMATCH", timeline_index, ordinal)

            effect = record.get("effect")
            if not isinstance(effect, dict):
                issue("EFFECT_ACK_MISSING", timeline_index, ordinal)
            else:
                if effect.get("event_identity") != expected or effect.get("generation") != generation or effect.get("last_event_seq") != seq:
                    issue("EFFECT_ACK_IDENTITY_MISMATCH", timeline_index, ordinal)
                if effect.get("acknowledged") is not True:
                    issue("EFFECT_REJECTED", timeline_index, ordinal)
                before, after = effect.get("accepted_counter_before"), effect.get("accepted_counter_after")
                if not integer(before) or not integer(after) or after != before + 1:
                    issue("EFFECT_COUNTER_MISMATCH", timeline_index, ordinal)

            audio = record.get("audio")
            if not isinstance(audio, dict):
                issue("AUDIO_ACK_MISSING", timeline_index, ordinal)
            else:
                if audio.get("event_identity") != expected or audio.get("generation") != generation or audio.get("last_event_seq") != seq:
                    issue("AUDIO_ACK_IDENTITY_MISMATCH", timeline_index, ordinal)
                if not isinstance(audio.get("return"), dict) or audio["return"].get("ok") is not True:
                    issue("AUDIO_REJECTED", timeline_index, ordinal)
                for counter in ("played_delta", "suppressed_delta", "dropped_delta"):
                    if not integer(audio.get(counter)):
                        issue("AUDIO_COUNTER_INVALID", timeline_index, ordinal, counter)

            sample_index, sample_delay = None, None
            capture_time = record.get("capture_clock_s")
            if not finite_number(capture_time) or capture_time < 0:
                issue("CAPTURE_CLOCK_INVALID", timeline_index, ordinal)
            elif frames_valid:
                found = bisect.bisect_left(frame_times, capture_time)
                if found < len(frames):
                    sample_index, sample_delay = found, frame_times[found] - capture_time
                else:
                    issue("NEXT_PRESENTATION_SAMPLE_MISSING", timeline_index, ordinal)
            observations.append({"source_record_ordinal": ordinal, "identity": expected,
                                 "kind": event.get("kind"), "ability_id": event.get("ability_id"),
                                 "time_s": event_time, "projectile_index": event.get("projectile_index"),
                                 "contact_reason": event.get("reason"),
                                 "effect": effect, "audio": audio,
                                 "sockets_before_motion_event": record.get("sockets_before_motion_event"),
                                 "sockets_after_motion_event": record.get("sockets_after_motion_event"),
                                 "first_presentation_sample_at_or_after": sample_index,
                                 "presentation_sample_delay_s": sample_delay})

        playback = []
        for group in groups:
            # Keep lifecycle/contact plus tick events that actually selected a
            # voice. Ordinary tick payloads remain in the original trace.
            selected = [(i, r) for i, r in group["records"] if r["event"].get("kind") != "tick" or
                        isinstance(r.get("audio"), dict) and r["audio"].get("played_delta", 0) > 0]
            events = [{**record["event"], "source_record_ordinal": ordinal} for ordinal, record in selected]
            if len(events) < 2 or not group["valid_clock"]:
                issue("PLAYBACK_SEGMENT_INCOMPLETE", timeline_index, detail=group["generation"])
                continue
            try:
                view = inspect_event_windows({"ability": timeline.get("label"), "events": events}, [1/display_hz])
                if not view["each_ordinal_once"]:
                    issue("PLAYBACK_ORDINAL_LOSS", timeline_index, detail=group["generation"])
                playback.append({"generation": group["generation"], **view})
            except (ValueError, KeyError, TypeError) as error:
                issue("PLAYBACK_SEGMENT_INVALID", timeline_index, detail=str(error))

        summaries.append({"label": timeline.get("label"), "source_presentation_hz": timeline.get("presentation_hz"),
                          "source_simulation_hz": timeline.get("simulation_hz"), "event_count": len(records),
                          "frame_count": len(frames), "observations": observations, "playback": playback})
    return {"schema": 1, "accepted": not findings, "scope": "Offline observed receiver/socket joins; no dispatch, rendering or listening",
            "display_hz": display_hz, "source_pins": trace.get("source_pins"),
            "event_sampler": str(PRIOR.relative_to(NATIVE) / "event_window.py"),
            "event_sampler_sha256": hashlib.sha256((PRIOR / "event_window.py").read_bytes()).hexdigest(),
            "findings": findings, "timelines": summaries}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--hz", type=int, choices=(30, 60, 120), default=60)
    args = parser.parse_args()
    trace, file_hash, data_hash = read_trace(args.trace)
    result = inspect(trace, args.hz)
    result.update(trace_file_sha256=file_hash, trace_json_sha256=data_hash)
    with args.output.open("x") as destination:
        json.dump(result, destination, separators=(",", ":"), allow_nan=False)
        destination.write("\n")
    print(json.dumps({"accepted": result["accepted"], "findings": len(result["findings"]),
                      "timelines": len(result["timelines"]), "hz": args.hz}))
    raise SystemExit(0 if result["accepted"] else 1)


if __name__ == "__main__":
    main()
