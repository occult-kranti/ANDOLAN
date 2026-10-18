#!/usr/bin/env python3
"""Verify all three central package archives against original execution files."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archives", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), "Preserve earlier receipts."
    cases = []
    checks = {}
    total_originals = 0
    for name in ["native-r1", "relaunch-r1", "staged-r1"]:
        directory = args.archives / name
        receipt = json.loads((directory / "archive-receipt.json").read_text())
        original = Path(receipt["source"])
        files = []
        for filename, expected in receipt["files_sha256"].items():
            source_name = {"godot-output.txt": "godot.log", "xvfb-output.txt": "xvfb.log"}.get(filename, filename)
            actual = sha(directory / filename)
            original_sha = sha(original / source_name)
            files.append({"file": filename, "sha256": actual, "original_file": str(original / source_name), "matches_receipt": actual == expected, "matches_original": actual == original_sha})
        run = json.loads((directory / "run.json").read_text())
        all_shots = run["shots"] + run["automatic_shots"]
        checks[name + ":all_archived_files_match_receipt"] = all(f["matches_receipt"] for f in files)
        checks[name + ":all_archived_files_match_actual_execution"] = all(f["matches_original"] for f in files)
        checks[name + ":all_raw_framebuffer_hashes"] = all(sha(directory / s["file"]) == s["sha256"] for s in all_shots)
        checks[name + ":all_raw_state_sidecars"] = all(json.loads((directory / (Path(s["file"]).stem + ".json")).read_text()) == s for s in all_shots)
        cases.append({"archive": str(directory), "archive_receipt_sha256": sha(directory / "archive-receipt.json"), "manual_originals": len(run["shots"]), "automatic_originals": len(run["automatic_shots"]), "files": files})
        total_originals += len(all_shots)
    result = {"task": "I3-04", "passed": all(checks.values()), "checks": checks, "checker_sha256": sha(Path(__file__)), "raw_originals": total_originals, "archives": cases, "scope": "Exact byte binding only. Does not claim visual inspection of all 57 originals; the scoped per-original review is separate."}
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"passed": result["passed"], "checks": len(checks), "originals": total_originals, "files": sum(len(x["files"]) for x in cases), "failed": [k for k, v in checks.items() if not v]}))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
