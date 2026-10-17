#!/usr/bin/env python3
"""Counterexamples for the production ledger gate, using a temporary repository."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile

TOOL = Path(__file__).resolve().parents[1] / "tools/check-roadmap.py"
spec = importlib.util.spec_from_file_location("roadmap", TOOL)
roadmap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(roadmap)


def main():
    checks = []
    with tempfile.TemporaryDirectory(prefix="yuga-roadmap-cases-") as folder:
        root = Path(folder)
        (root / "proof.json").write_text('{"passed":true}\n')
        fixture = {
            "schema_version": 1,
            "status_values": sorted(roadmap.STATUSES),
            "milestones": [{"id": "M1", "title": "Gate", "status": "planned",
                "owner": "integration", "depends_on": [], "completion_rule": "Actual proof reviewed",
                "task_ids": ["T1", "T2"]}],
            "tasks": [{"id": ident, "milestone": "M1", "title": ident, "owner": "QA",
                "status": "planned", "priority": "P0", "depends_on": deps,
                "deliverables": ["planned: artifact"], "acceptance": ["Actual result inspected"],
                "evidence": [], "next_action": "Run the experiment"}
                for ident, deps in [("T1", []), ("T2", ["T1"])]],
            "next_packets": ["T1"],
        }

        def check(name, candidate, required_error=None):
            errors, _ = roadmap.validate(candidate, root)
            passed = not errors if required_error is None else any(required_error in x for x in errors)
            checks.append({"name": name, "passed": passed, "errors": errors})

        check("valid dependency ledger", fixture)
        changed = copy.deepcopy(fixture)
        changed["tasks"][0].update(status="complete", evidence=[{"path": "proof.json", "scope": "Controlled fixture only", "sha256": hashlib.sha256((root / "proof.json").read_bytes()).hexdigest()}])
        changed["next_packets"] = ["T2"]
        check("hashed completion unlocks dependent packet", changed)
        changed = copy.deepcopy(fixture)
        changed["next_packets"] = ["T2"]
        check("ready queue rejects unmet prerequisite", changed, "prerequisite T1 incomplete")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["status"] = "blocked"
        check("ready queue rejects blocked packet", changed, "next packet blocked")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0].update(status="complete", evidence=[{"path": "proof.json", "scope": "Fixture"}])
        changed["next_packets"] = ["T2"]
        check("completion requires pinned evidence", changed, "complete evidence needs SHA-256")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["depends_on"] = ["T2"]
        check("cycle fails", changed, "dependency cycle")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["status"] = "complete"
        check("completion without evidence fails", changed, "complete without evidence")
        changed = copy.deepcopy(fixture)
        changed["tasks"][1].update(status="complete", evidence=[{"path": "proof.json", "scope": "Fixture only"}])
        check("completion before prerequisite fails", changed, "complete before dependency")
        changed = copy.deepcopy(fixture)
        changed["milestones"][0]["status"] = "complete"
        check("parent cannot precede children", changed, "complete before all tasks")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["evidence"] = [{"path": "../outside.json", "scope": "Invalid"}]
        check("outside evidence fails", changed, "must stay inside repository")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["evidence"] = [{"path": "proof.json", "scope": "Fixture", "sha256": "0" * 64}]
        check("stale evidence hash fails", changed, "hash mismatch")
        changed = copy.deepcopy(fixture)
        changed["tasks"][0]["evidence"] = [{"path": "missing.json", "scope": "Missing"}]
        check("missing evidence fails", changed, "evidence file missing")
    report = {"passed": all(x["passed"] for x in checks), "scope": "Controlled graph and evidence counterexamples only", "checks": checks}
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
