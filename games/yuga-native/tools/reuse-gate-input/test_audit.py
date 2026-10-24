#!/usr/bin/env python3
"""Negative controls for the source-bound route acceptance oracle."""
import copy
import json
import run


def row(frame, z, y=0, grounded=True):
    return {"active": True, "paused": False, "overview": False, "physics_frame": frame,
            "position": [-40, y, z], "grounded": grounded, "gate_ray": {"clear": True}, "input": {"forward": True}}


def main():
    examples = [row(i + 1, -64 + i * .1) for i in range(191)]
    examples += [row(len(examples) + i + 1, -45 - i * .1) for i in range(191)]
    checks = []
    checks.append({"name": "consecutive grounded bidirectional samples", "passed": run.audit_route(examples)["passed"]})
    checks.append({"name": "empty trace refused", "passed": not run.audit_route([])["passed"]})
    checks.append({"name": "one complete direction refused", "passed": not run.audit_route(examples[:191])["passed"]})
    teleported = [row(1, -64), row(2, -45), row(3, -64)]
    checks.append({"name": "teleport both ways refused", "passed": not run.audit_route(teleported)["passed"]})
    gaps = copy.deepcopy(examples)
    for entry in gaps:
        entry["physics_frame"] *= 10
    checks.append({"name": "missing physics at crossings refused", "passed": not run.audit_route(gaps)["passed"]})
    airborne = copy.deepcopy(examples)
    for entry in airborne:
        entry["grounded"] = False
    checks.append({"name": "airborne shortcut refused", "passed": not run.audit_route(airborne)["passed"]})
    off_lane = copy.deepcopy(examples)
    for entry in off_lane:
        entry["position"][0] = -46
    checks.append({"name": "walking around gate refused", "passed": not run.audit_route(off_lane)["passed"]})
    paused = copy.deepcopy(examples)
    for entry in paused:
        entry["paused"] = True
    checks.append({"name": "paused staged trace refused", "passed": not run.audit_route(paused)["passed"]})
    print(json.dumps({"checks": checks, "passed": all(check["passed"] for check in checks)}, indent=2))
    return 0 if all(check["passed"] for check in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
