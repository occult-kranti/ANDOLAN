#!/usr/bin/env python3
"""Compare fresh scene/modifier traces without hiding acquisition contact cost."""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    checks, summaries, inputs, storage = [], [], {}, {}

    def check(name, passed, detail=None):
        checks.append(dict(name=name, passed=bool(passed), detail=detail or {}))

    for hz in (30, 60, 120):
        names = [f"baseline-{hz}{'' if hz == 60 else '-r2'}.json", f"candidate-{hz}-r3.json"]
        traces = []
        for name in names:
            path = args.evidence / name
            stored = path if path.is_file() else path.with_suffix(path.suffix+".gz")
            payload = stored.read_bytes()
            raw = gzip.decompress(payload) if stored.suffix == ".gz" else payload
            inputs[name] = hashlib.sha256(raw).hexdigest()
            storage[name] = dict(path=stored.name, sha256=hashlib.sha256(payload).hexdigest(), bytes=len(payload), uncompressed_bytes=len(raw))
            traces.append(json.loads(raw))
        baseline, candidate = traces
        a, b = baseline["rows"], candidate["rows"]
        aligned = len(a) == len(b) and all(x["label"] == y["label"] and x["physics_frame"] == y["physics_frame"] for x, y in zip(a, b))
        identical_inputs = all(value == candidate["source_sha256"].get(key) for key, value in baseline["source_sha256"].items() if key != "res://scripts/rama_motion.gd")
        check(f"{hz}Hz same native sequence inputs and lifecycle assertions", aligned and identical_inputs and all(t["passed"] and t["count"] == 15 for t in traces))
        if not aligned:
            continue
        same_authority = all(all(x[k] == y[k] for k in ("root", "velocity", "kit", "army_elapsed")) and all(x["motion"][k] == y["motion"][k] for k in ("phase", "stage", "action_elapsed", "release_count", "cancel_count")) for x, y in zip(a, b))
        check(f"{hz}Hz exact root velocity authority events and presentation clocks", same_authority and baseline["events"] == candidate["events"])
        penetration_delta = min(y["soles"][side]["minimum_m"] - min(0, x["soles"][side]["minimum_m"]) for x, y in zip(a, b) for side in ("L", "R"))
        check(f"{hz}Hz no new or deeper sole penetration", penetration_delta >= -0.000001, dict(minimum_margin_m=penetration_delta))
        entry_labels = ("create_title", "return_from_fullbody_recovery", "return_after_cancel")
        ordinary_difference = max(math.dist(p["p"], q["p"]) for x, y in zip(a, b) if x["label"] not in entry_labels for p, q in zip(x["poses"], y["poses"]))
        ordinary_rotation_difference = max(min(math.dist(p["q"], q["q"]), math.dist(p["q"], [-v for v in q["q"]])) for x, y in zip(a, b) if x["label"] not in entry_labels for p, q in zip(x["poses"], y["poses"]))
        check(f"{hz}Hz ordinary reset motion and action poses unchanged", ordinary_difference < 0.000001 and ordinary_rotation_difference < .000001, dict(maximum_joint_difference_m=ordinary_difference, maximum_quaternion_difference=ordinary_rotation_difference))
        phases = {}
        for label in dict.fromkeys(x["label"] for x in a):
            ar, br = ([x for x in trace if x["label"] == label] for trace in (a, b))
            metrics = []
            for rr in (ar, br):
                metrics.append(dict(
                    callbacks=len(rr),
                    idle_entry_eligible_side_samples=2*sum(x["motion"]["locomotion"] == "idle" and x["transition_age"] >= .16 and x["motion"]["stage"] == "none" for x in rr),
                    locked_side_samples=sum(x["motion"]["foot_locks"][s] for x in rr for s in ("L", "R")),
                    actual_floor_side_samples=sum(x["motion"]["foot_locks"][s] and abs(x["soles"][s]["minimum_m"]) <= .005 for x in rr for s in ("L", "R")),
                    minimum_sole_m=min(x["soles"][s]["minimum_m"] for x in rr for s in ("L", "R")),
                    maximum_joint_step_m=max(x["adjacent_rig_origin_step_m"] for x in rr),
                ))
            phases[label] = dict(baseline=metrics[0], candidate=metrics[1])
            if label not in entry_labels:
                continue
            begin = next(i for i, row in enumerate(br) if row["support_age"]["L"] < .12)
            end = next(i for i in range(begin, len(br)) if br[i]["support_age"]["L"] >= .12)
            aw, bw = ar[begin:end+1], br[begin:end+1]
            am, bm = (max(row["adjacent_rig_origin_step_m"] for row in rr) for rr in (aw, bw))
            drift = max(math.dist(row["targets"][s], br[begin]["targets"][s]) for row in bw for s in ("L", "R"))
            ages = [row["support_age"]["L"] for row in bw]
            age_step = max(y-x for x, y in zip(ages, ages[1:]))
            check(f"{hz}Hz {label} acquisition step reduced with fixed anchors", bm < am*.6 and drift < .0000001, dict(baseline_m=am, candidate_m=bm, world_anchor_drift_m=drift))
            check(f"{hz}Hz {label} bounded completion and no pause catch-up", end-begin <= math.ceil(.12*hz)+1 and age_step <= 1/hz+1e-9 and all(0 <= age <= .12 for age in ages), dict(update_count=end-begin, maximum_age_step_s=age_step, effective_duration_s=(end-begin)/hz))
            settled_error = max(abs(x["soles"][s]["minimum_m"]-y["soles"][s]["minimum_m"]) for x, y in zip(ar[end:], br[end:]) for s in ("L", "R"))
            check(f"{hz}Hz {label} settled sole gap returns to baseline", settled_error < .000001, dict(maximum_gap_difference_m=settled_error))
            phases[label]["acquisition"] = dict(first_callback=begin, completed_callback=end, baseline_step_m=am, candidate_step_m=bm, fixed_anchor_drift_m=drift)
        summaries.append(dict(hz=hz, phases=phases))
    result = dict(passed=all(c["passed"] for c in checks), count=len(checks), checks=checks, summaries=summaries, inputs=inputs, storage=storage,
                  scope="Source-bound headless native callback comparison. Locked-anchor counts and actual floor-contact counts are separate. Short initial hovering is extended to smooth admission; ordinary penetration is retained. No rendering, first-draw visibility, C1 continuity, hardware performance or play-feel acceptance.")
    args.report.write_text(json.dumps(result, indent=2)+"\n")
    print(f"{sum(c['passed'] for c in checks)}/{len(checks)}")
    for c in checks:
        if not c["passed"]: print("FAIL", c)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
