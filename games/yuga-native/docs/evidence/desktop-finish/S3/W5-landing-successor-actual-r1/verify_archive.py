#!/usr/bin/env python3
"""Verify both new takes and their retained baseline from repository files only."""
import gzip
import hashlib
import json
from pathlib import Path


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    root = Path(__file__).resolve().parent
    rows = []
    for case in ("landing120", "full"):
        comparison = json.loads((root / (case + "-archive-comparison.json")).read_text())
        for role in ("baseline", "candidate"):
            path = root.parent / "W5-actual-motion-r1" / case / "candidate" if role == "baseline" else root / case
            archive = json.loads((path / "archive.json").read_text())
            compressed = (path / archive["capture"]["path"]).read_bytes()
            raw = gzip.decompress(compressed)
            capture = json.loads(raw)
            run = json.loads((path / "run.json").read_text())
            identity = all(sha((path / name).read_bytes()) == pin["sha256"] and (path / name).stat().st_size == pin["bytes"] for name, pin in archive["originals"].items())
            identity &= sha(compressed) == archive["capture"]["gzip_sha256"] and len(compressed) == archive["capture"]["gzip_bytes"]
            identity &= sha(raw) == archive["capture"]["raw_sha256"] == run["report_sha256"] and len(raw) == archive["capture"]["raw_bytes"]
            identity &= comparison["inputs"][role]["capture_raw_sha256"] == sha(raw)
            identity &= comparison["inputs"][role]["capture_file_sha256"] == sha(compressed)
            identity &= comparison["inputs"][role]["run_sha256"] == sha((path / "run.json").read_bytes())
            identity &= all(sha((path / "originals" / shot["file"]).read_bytes()) == shot["sha256"] for shot in capture["shots"])
            identity &= sha((path / "normal-speed.mp4").read_bytes()) == archive["video"]["sha256"]
            rows.append({"case": case, "role": role, "passed": bool(identity), "original_pngs": len(capture["shots"]), "raw_capture_sha256": sha(raw), "complete": capture["complete"] and run["complete"], "native_gates": len(capture["checks"]), "native_gates_passed": all(x["passed"] for x in capture["checks"]), "matched_control_predicates": len(comparison["checks"]), "matched_controls_passed": comparison["passed"]})
    result = {"passed": all(r["passed"] and r["complete"] and r["native_gates_passed"] and r["matched_controls_passed"] for r in rows), "runs": rows, "new_original_pngs": 160, "reused_original_pngs": 160, "scope": "Portable byte identity and completed receipt audit. The same42 control predicates per case are replayed, not counted as new independent tests. No rerender or image-quality scoring."}
    print(json.dumps(result, indent=2))
    raise SystemExit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
