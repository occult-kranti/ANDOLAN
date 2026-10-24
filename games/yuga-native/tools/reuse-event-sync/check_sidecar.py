#!/usr/bin/env python3
"""Counterexamples are mutations of the retained real capture, not mock success."""
import argparse
import copy
import json
from pathlib import Path

from inspect_sidecar import inspect, read_trace


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--trace", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    trace, file_hash, raw_hash = read_trace(args.trace)
    checks = []

    def check(name, condition, details=None):
        checks.append({"name": name, "passed": bool(condition), "details": details})

    for hz in (30, 60, 120):
        result = inspect(trace, hz)
        check(f"actual receiver/socket capture passes at inspection {hz} Hz", result["accepted"], result["findings"])
        check(f"{hz} Hz keeps every selected source ordinal once", all(
            p["each_ordinal_once"] for t in result["timelines"] for p in t["playback"]))
    base = copy.deepcopy(trace)
    base["timelines"] = [base["timelines"][0]]

    def reject(name, mutate, code, missing_assertion=None):
        modified = copy.deepcopy(base)
        mutate(modified)
        result = inspect(modified)
        found = [finding["code"] for finding in result["findings"]]
        check(name, not result["accepted"] and code in found and
              (missing_assertion(result) if missing_assertion else True), found)

    def row(data):
        return data["timelines"][0]["events"][2]

    reject("missing effect ack stays null and fails", lambda d: row(d).pop("effect"), "EFFECT_ACK_MISSING",
           lambda r: r["timelines"][0]["observations"][2]["effect"] is None)
    reject("missing audio ack stays null and fails", lambda d: row(d).pop("audio"), "AUDIO_ACK_MISSING",
           lambda r: r["timelines"][0]["observations"][2]["audio"] is None)
    reject("missing muzzle is never substituted with identity", lambda d: row(d)["sockets_before_motion_event"].pop("arrow_muzzle"), "SOCKET_MISSING",
           lambda r: "arrow_muzzle" not in r["timelines"][0]["observations"][2]["sockets_before_motion_event"])
    reject("missing socket sample remains null", lambda d: row(d).pop("sockets_after_motion_event"), "SOCKET_SAMPLE_MISSING",
           lambda r: r["timelines"][0]["observations"][2]["sockets_after_motion_event"] is None)
    reject("nonfinite socket rejected", lambda d: row(d)["sockets_before_motion_event"]["bow_grip"]["position"].__setitem__(0, float("inf")), "SOCKET_NONFINITE_OR_MALFORMED")
    reject("duplicate actual event rejected", lambda d: d["timelines"][0]["events"].insert(3, copy.deepcopy(row(d))), "DUPLICATE_EVENT_IDENTITY")
    reject("removed actual event produces visible sequence gap", lambda d: d["timelines"][0]["events"].pop(2), "MISSING_EVENT_SEQUENCE")
    reject("missing generation boundary rejected", lambda d: d["timelines"][0]["events"].pop(0), "GENERATION_FIRST_EVENT_MISSING")
    reject("effect ack from different event rejected", lambda d: row(d)["effect"]["event_identity"].__setitem__(1, 9999), "EFFECT_ACK_IDENTITY_MISMATCH")
    reject("audio stale receiver generation rejected", lambda d: row(d)["audio"].__setitem__("generation", -1), "AUDIO_ACK_IDENTITY_MISMATCH")
    reject("receiver false acknowledgement preserved", lambda d: row(d)["audio"]["return"].__setitem__("ok", False), "AUDIO_REJECTED")
    reject("effect unincremented state rejected", lambda d: row(d)["effect"].__setitem__("accepted_counter_after", row(d)["effect"]["accepted_counter_before"]), "EFFECT_COUNTER_MISMATCH")
    reject("event reversed clock rejected", lambda d: row(d)["event"].__setitem__("time_s", -1), "EVENT_CLOCK_REVERSED_OR_INVALID")
    reject("event bool identity rejected", lambda d: row(d)["event"].__setitem__("event_seq", True), "IDENTITY_INVALID")
    reject("socket from different event rejected", lambda d: row(d)["socket_observed_for"].__setitem__(1, 9999), "SOCKET_IDENTITY_MISMATCH")
    reject("missing continuous samples rejected", lambda d: d["timelines"][0].__setitem__("frames", []), "FRAME_CLOCK_INVALID_OR_MISSING")
    reject("mutated canonical pin rejected", lambda d: d["source_after"].__setitem__(next(iter(d["source_after"])), "changed"), "SOURCE_CHANGED_OR_UNPINNED")
    reject("capture failed check cannot be hidden", lambda d: d["checks"][0].__setitem__("passed", False), "CAPTURE_CHECK_FAILED_OR_MISSING")
    reject("shifted whole frame timeline rejected", lambda d: [f.__setitem__("capture_clock_s", f["capture_clock_s"]+10) for f in d["timelines"][0]["frames"]], "FRAME_COVERAGE_BOUNDS_MISMATCH")
    reject("removed middle frame rejected", lambda d: d["timelines"][0]["frames"].pop(10), "FRAME_CADENCE_GAP_OR_MISMATCH")
    reject("unrequested source cadence rejected", lambda d: d["timelines"][0].__setitem__("presentation_hz", 1), "SOURCE_PRESENTATION_CADENCE_INVALID")
    reject("event capture clock drift rejected", lambda d: row(d).__setitem__("capture_clock_s", 0), "CAPTURE_AND_OWNER_CLOCK_MISMATCH")
    reject("malformed motion produces finding instead of exception", lambda d: d["timelines"][0]["frames"][0].__setitem__("motion", None), "FRAME_PRESENTATION_STATE_MISSING_OR_MALFORMED")
    reject("malformed effects produces finding instead of exception", lambda d: d["timelines"][0]["frames"][0].__setitem__("effects", None), "FRAME_PRESENTATION_STATE_MISSING_OR_MALFORMED")

    for source_hz in (30, 60, 120):
        for mutation, expected in (("drop_frame", "FRAME_CADENCE_GAP_OR_MISMATCH"),
                                   ("shift_frames", "FRAME_COVERAGE_BOUNDS_MISMATCH"),
                                   ("drift_event_clock", "CAPTURE_AND_OWNER_CLOCK_MISMATCH")):
            modified = copy.deepcopy(trace)
            selected = next(t for t in modified["timelines"] if t["presentation_hz"] == source_hz and t["label"] == "kodanda")
            modified["timelines"] = [selected]
            if mutation == "drop_frame":
                selected["frames"].pop(10)
            elif mutation == "shift_frames":
                for frame in selected["frames"]:
                    frame["capture_clock_s"] += 10
            else:
                selected["events"][2]["capture_clock_s"] = 0
            result = inspect(modified, source_hz)
            check(f"{source_hz} Hz rejects {mutation}", not result["accepted"] and
                  any(f["code"] == expected for f in result["findings"]))

    reset_trace = copy.deepcopy(trace)
    reset_trace["timelines"] = [copy.deepcopy(trace["timelines"][3])]
    events = reset_trace["timelines"][0]["events"]
    first_generation = events[0]["event"]["generation"]
    first_new = next(i for i, r in enumerate(events) if r["event"]["generation"] != first_generation)
    events.insert(first_new + 1, copy.deepcopy(events[2]))
    result = inspect(reset_trace)
    check("stale actual pre-reset record rejected after boundary", any(f["code"] == "STALE_EVENT_IDENTITY" for f in result["findings"]))
    check("actual capture covers all requested presentation cadences", {t["presentation_hz"] for t in trace["timelines"]} == {30, 60, 120})
    check("actual capture covers cancellation and reset for every cadence", all(
        sum(t["presentation_hz"] == hz and t["label"] == label for t in trace["timelines"]) == 1
        for hz in (30, 60, 120) for label in ("kodanda", "dawn_volley", "cancel_windup", "reset_windup_then_recast", "cancel_released_volley")))
    check("actual receiver duplicate/stale negatives all passed", len(trace["negative_receipts"]) == 9 and all(r["passed"] for r in trace["negative_receipts"]))
    result = {"schema": 1, "trace_file_sha256": file_hash, "trace_json_sha256": raw_hash,
              "checks": checks, "passed": all(c["passed"] for c in checks)}
    with args.output.open("x") as output:
        json.dump(result, output, indent=2, allow_nan=False)
        output.write("\n")
    print(json.dumps({"passed": sum(c["passed"] for c in checks), "total": len(checks)}))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
