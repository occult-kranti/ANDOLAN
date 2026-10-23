"""Replay retained R1 GLBs plus the normalized-joints witness after one correction."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(project, scratch, output):
    assert not output.exists(), "fresh report required"
    tool = project / "tools/hero-family-reuse/intake.py"
    manifest_path = project / "docs/research/hero-family-reuse-oct23/rama-family-manifest.json"
    before = {"intake": digest(tool), "manifest": digest(manifest_path)}
    spec = importlib.util.spec_from_file_location("independent_recheck", tool)
    intake = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(intake)
    manifest = json.loads(manifest_path.read_text())
    previous = json.loads((scratch / "r1/counterexamples.json").read_text())
    requests = {"accepted-canonical": {"source": project / intake.DONOR},
                "unknown-socket": {"sockets": ["mace_grip"]},
                "unknown-motion": {"motions": ["mace_slam"]},
                "weapon": {"weapon": "mace"},
                "extra-anatomy-declared": {"extra_anatomy": True},
                "finished-claim": {"finished": True},
                "wrong-source-sha": {"source": project / intake.DONOR, "expected_source_sha": "0" * 64}}
    cases = copy.deepcopy(previous["cases"])
    normalized = scratch / "normalized-joints.glb"
    cases.append({"name": "mesh-normalized-joints", "expected": "reject", "fixture_path": str(normalized), "fixture_sha256": digest(normalized)})
    outcomes = []
    for case in cases:
        selected_manifest = manifest
        if "fixture_path" in case:
            path = Path(case["fixture_path"])
            assert digest(path) == case["fixture_sha256"], "original fixture drift"
            arguments = {"source": path, "expected_source_sha": digest(path)}
        elif case["name"] == "source-pin-drift":
            selected_manifest = copy.deepcopy(manifest)
            selected_manifest["source_pins"][0]["sha256"] = "0" * 64
            arguments = {}
        else:
            arguments = requests[case["name"]]
        try:
            verdict = intake.compatible(selected_manifest, "arjuna", **arguments)
            exception = None
        except Exception as exc:
            verdict = {"ok": False, "errors": []}
            exception = type(exc).__name__ + ": " + str(exc)
        expected_ok = case["expected"] == "accept-authoring-only"
        outcomes.append({"name": case["name"], "expected": case["expected"],
                         "fixture_path": case.get("fixture_path"), "fixture_sha256": case.get("fixture_sha256"),
                         "verdict": verdict, "exception": exception,
                         "passed": verdict["ok"] == expected_ok and exception is None})
    after = {"intake": digest(tool), "manifest": digest(manifest_path)}
    pins = [{**p, "actual_sha256": digest(project / p["path"])} for p in manifest["source_pins"]]
    report = {"schema_version": 1, "scope": "Independent single correction-pass replay of actual retained malformed GLBs and authoring-only requests.",
              "source_before": before, "source_after": after, "source_stable": before == after,
              "script_sha256": digest(__file__), "case_count": len(outcomes), "passed_case_count": sum(c["passed"] for c in outcomes),
              "pins": pins, "all_19_source_pins_match": len(pins) == 19 and all(p["actual_sha256"] == p["sha256"] for p in pins),
              "cases": outcomes, "passed": before == after and all(c["passed"] for c in outcomes)}
    output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"passed": report["passed"], "passed_cases": report["passed_case_count"], "cases": report["case_count"], "source_stable": report["source_stable"], "report": str(output)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--project", type=Path, required=True)
    parser.add_argument("--scratch", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    main(args.project.resolve(), args.scratch.resolve(), args.output.resolve())
